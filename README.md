# Telegram Math Bot

Интеллектуальный Telegram-бот, который умеет:
- Вычислять производные, интегралы, логарифмы
- Упрощать и раскрывать выражения
- Решать уравнения и задачи с помощью GPT и нейросети Mistral

## Установка

```bash
git clone https://github.com/SerGoGryz/telegram-math-bot.git
cd telegram-math-bot
pip install -r requirements.txt
```

## Переменные окружения

Создайте файл `.env`, основываясь на `.env.example`, и укажите там свои токены.

## Запуск

```bash
python bot.py
```

## Особенности

- Поддержка API OpenAI с автоматическим переключением
- Клавиатура с действиями (производные, логарифмы и др.)
