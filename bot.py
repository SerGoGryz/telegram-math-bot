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
from math_solver import solve_equation, compute_operation

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
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
PROMPTS = {
    "diff":       "Найди производную выражения: ",
    "integrate":  "Вычисли неопределённый интеграл выражения: ",
    "log":        "Вычисли логарифм (если надо, укажи основание) для выражения: ",
    "simplify":   "Упрости выражение: ",
    "expand":     "Раскрой скобки в выражении: ",
    "solve":      "Реши уравнение: ",
    "free":       "Реши или растолкуй: "
}

ALLOWED_CHARS = r"^[0-9a-zA-ZxXeEππ\+\-\*/\^\(\)=\s\.,_:]*$"   # всё, что SymPy обычно «ест»

def log_task(user, query, source, result):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {user} \nЗапрос: {query}\nИсточник: {source}\nРезультат: {result}\n---\n")

def get_main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("Старт"), KeyboardButton("Производная")],
        [KeyboardButton("Интеграл"), KeyboardButton("Логарифм"), KeyboardButton("Упростить")],
        [KeyboardButton("Раскрыть скобки"), KeyboardButton("Решить уравнение")],
        [KeyboardButton("Ручной ввод"), KeyboardButton("Очистить")]
    ], resize_keyboard=True)
async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я вас не понял. Пожалуйста, выберите действие из меню:", reply_markup=get_main_keyboard())
    return OPERATION_CHOICE

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_operation.pop(update.effective_user.id, None)
    await update.message.reply_text("Добро пожаловать! Выбери действие или нажми 'Ручной ввод':", reply_markup=get_main_keyboard())
    return OPERATION_CHOICE
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        "Упростить": "simplify", "Раскрыть скобки": "expand", "Решить уравнение": "solve"
    }
    if text in operations:
        user_operation[update.effective_user.id] = operations[text]
        hint = ""
        if text == "Логарифм":
            hint = "\nПример ввода:\n- 2 8 — логарифм 8 по основанию 2\n- 10 — натуральный логарифм"
        if text == "Решить уравнение":
            hint = "\Пример ввода:\nx^2 + 2*x + 8\nx^2 - 5x + 6"
        await update.message.reply_text(f"Введите выражение или уравнение:{hint}")
        return WAIT_FOR_INPUT
    elif text == "Ручной ввод":
        user_operation.pop(update.effective_user.id, None)
        await update.message.reply_text("Введите математическое выражение или текстовую задачу:")
        return WAIT_FOR_INPUT
    elif text in ["Назад", "Очистить"]:
        user_operation.pop(update.effective_user.id, None)
        await update.message.reply_text("Операция сброшена. Выберите новое действие:", reply_markup=get_main_keyboard())
        return OPERATION_CHOICE
    elif text in ["/start","start","Старт"]:
        user_operation.pop(update.effective_user.id, None)
        await update.message.reply_text("Добро пожаловать! Выбери действие или нажми 'Ручной ввод':", reply_markup=get_main_keyboard())
        return OPERATION_CHOICE
    else:
        await update.message.reply_text("Пожалуйста, выберите действие с клавиатуры.")
        return OPERATION_CHOICE

async def handle_expression(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    text = re.sub(r'e\^([a-zA-Z0-9_()]+)', r'exp(\1)', text)
    uid = update.effective_user.id
    username = update.effective_user.full_name

    if text in ["Назад", "Очистить", "start", "/start"]:
        return await choose_operation(update, context)
    if uid in user_operation:
        op = user_operation.pop(uid)
        clean_text = text.replace("√", "sqrt")          # 1) Меняем знак корня
        result = compute_operation(op, clean_text)      # 2) Пробуем SymPy

        bad = ("Ошибка:" in result or
               result == "Решений нет." or
               re.search(r"invalid|could not parse", result, re.I) or
               not re.match(ALLOWED_CHARS, clean_text))           # 3) «Подозрительный» ответ

        if bad:
            prompt = PROMPTS.get(op, PROMPTS["free"]) + text
            model_reply, model_used = ask_gpt(prompt) if USE_GPT else (ask_model(prompt), "Mistral")
            reply = f"Ответ:\n{model_reply}"
            log_task(username, text, model_used, reply)
            await update.message.reply_text(reply, reply_markup=get_main_keyboard())
            return OPERATION_CHOICE

        # если всё хорошо – обычный путь
        log_task(username, f"Операция {op} с {text}", "SymPy", result)
        await update.message.reply_text(result, reply_markup=get_main_keyboard())
        return OPERATION_CHOICE


    result = solve_equation(text)
    result = result.replace("sqrt", "√").replace("⋅", "*").replace("ⅈ", "i")

    if ("Ошибка:" in result or 
        result == "Решений нет." or
        "invalid syntax" in result or 
        "could not parse" in result):
    
        model_used = "GPT"
        model_reply, model_used = ask_gpt(text) if USE_GPT else (ask_model(text), "Mistral")
        if "Ошибка" in model_reply or "invalid" in model_reply or "invalid syntax" in model_reply or "could not parse" in model_reply:
            model_reply = "Не удалось решить задачу. Попробуйте переформулировать или ввести по-другому."
        result = f"Ответ от модели:\n{model_reply}"
        log_task(username, text, model_used, result)
        await update.message.reply_text(result, reply_markup=get_main_keyboard())
        return OPERATION_CHOICE

    log_task(username, text, "SymPy (авто)", result)
    await update.message.reply_text(result)
    await update.message.reply_text("Выберите следующее действие:", reply_markup=get_main_keyboard())

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог завершён.")
    return ConversationHandler.END

# === Запуск ===
if __name__ == "__main__":
    from telegram.ext import ApplicationBuilder

    app = ApplicationBuilder().token(os.getenv("TOKEN_BOT")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("menu", show_menu)],
        states={
            OPERATION_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_operation)],
            WAIT_FOR_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_expression)],
        },
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("model", model_command))
    # Запуск синхронно — сам делает initialize/start/idle/stop
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 10000)),
        url_path=WEBHOOK_PATH,
        webhook_url=WEBHOOK_URL,
    )
