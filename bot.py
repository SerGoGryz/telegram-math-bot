from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)
import os
from dotenv import load_dotenv
from math_solver import solve_equation, compute_operation
from gpt_solver import ask_gpt
from datetime import datetime
import re

load_dotenv()

# Настройки вебхука
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://{WEBHOOK_HOST}{WEBHOOK_PATH}"

OPERATION_CHOICE, WAIT_FOR_INPUT = range(2)
user_operation = {}
USE_GPT = os.getenv("OPENAI_API_KEY") is not None
LOG_FILE = "log.txt"

def ask_model(prompt: str) -> str:
    return "Локальная модель отключена на хостинге."

def log_task(user, query, source, result):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {user} \nЗапрос: {query}\nИсточник: {source}\nРезультат: {result}\n---\n")

def get_main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("Производная"), KeyboardButton("Интеграл")],
        [KeyboardButton("Логарифм"), KeyboardButton("Упростить"), KeyboardButton("Раскрыть скобки")],
        [KeyboardButton("Ручной ввод"), KeyboardButton("Очистить"), KeyboardButton("Назад")]
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выбери действие или нажми 'Ручной ввод':", reply_markup=get_main_keyboard())
    return OPERATION_CHOICE

async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if USE_GPT:
        from gpt_solver import PRIMARY, SECONDARY
        await update.message.reply_text(f"Сейчас используется GPT API:\n- Основная модель: {PRIMARY}\n- Запасная модель: {SECONDARY}")
    else:
        await update.message.reply_text("Используется локальная модель: Mistral")

async def choose_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    operations = {
        "Производная": "diff", "Интеграл": "integrate", "Логарифм": "log",
        "Упростить": "simplify", "Раскрыть скобки": "expand"
    }
    if text in operations:
        user_operation[update.effective_user.id] = operations[text]
        hint = ""
        if text == "Логарифм":
            hint = "\nПример ввода:\n- 2 8 — логарифм 8 по основанию 2\n- 10 — натуральный логарифм"
        await update.message.reply_text(f"Введите выражение (например: x^2):{hint}")
        return WAIT_FOR_INPUT
    elif text == "Ручной ввод":
        user_operation.pop(update.effective_user.id, None)
        await update.message.reply_text("Введите математическое выражение или текстовую задачу:")
        return WAIT_FOR_INPUT
    elif text in ["Назад", "Очистить"]:
        user_operation.pop(update.effective_user.id, None)
        await update.message.reply_text("Операция сброшена. Выберите новое действие:", reply_markup=get_main_keyboard())
        return OPERATION_CHOICE
    else:
        await update.message.reply_text("Пожалуйста, выберите действие с клавиатуры.")
        return OPERATION_CHOICE

async def handle_expression(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id
    username = update.effective_user.full_name
    result = ""

    if text in ["Назад", "Очистить"]:
        return await choose_operation(update, context)

    if uid in user_operation:
        op = user_operation.pop(uid)
        result = compute_operation(op, text)
        log_task(username, f"Операция {op} с {text}", "SymPy (ручная)", result)
    else:
        result = solve_equation(text)
        if "Ошибка:" in result or result == "Решений нет.":
            model_used = "GPT"
            model_reply, model_used = ask_gpt(text) if USE_GPT else (ask_model(text), "Mistral")
            if model_reply.strip() == "[GPT: превышен лимит]" or model_used == "None":
                model_reply = ask_model(text)
                model_used = "Mistral (fallback)"
            steps = []
            for line in model_reply.splitlines():
                if ":" in line:
                    label, expr = line.split(":", 1)
                    expr = expr.strip()
                    if not re.match(r"^[\d\s\+\-\*/\.\(\)x^]+$", expr):
                        continue
                    calc = solve_equation(expr)
                    steps.append(f"{label.strip()}: {expr} = {calc.replace('Ответ: ', '')}")
            result = "\n".join(steps) if steps else f"Ответ от модели:\n{model_reply}"
            log_task(username, text, model_used, result)
        else:
            log_task(username, text, "SymPy (авто)", result)

    await update.message.reply_text(result)
    await update.message.reply_text("Можешь выбрать новое действие:", reply_markup=get_main_keyboard())
    return OPERATION_CHOICE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог завершён.")
    return ConversationHandler.END

# === Запуск ===
async def main():
    app = ApplicationBuilder().token(os.getenv("TOKEN_BOT")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            OPERATION_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_operation)],
            WAIT_FOR_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_expression)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("model", model_command))

    await app.bot.set_webhook(WEBHOOK_URL)
    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 10000)),
        webhook_path=WEBHOOK_PATH,
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
