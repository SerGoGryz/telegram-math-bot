import openai
import os
from openai import RateLimitError
from typing import Tuple
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI()
PRIMARY = os.getenv("GPT_MODEL_PRIMARY", "gpt-4.1-nano")
SECONDARY = os.getenv("GPT_MODEL_SECONDARY", "gpt-4o")
def ask_gpt(prompt: str) -> Tuple[str, str]:
    try:
        response = client.chat.completions.create(
            model=PRIMARY,
            messages=[
                {"role": "system", "content": "Ты — математический ассистент. Отвечай просто и кратко. Если есть ошибка - напиши про нее в чем она заключается, затем выводи возможное решение. Не используй LaTeX, Markdown, **жирный текст**, кавычки и форматирование. Если есть решение, то делай 2-4 шага с пояснениями. Каждый шаг в формате:\nШаг N: выражение\nИ в конце напиши:\nОтвет: число или фраза."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=5000
        )
        return response.choices[0].message.content.strip(), PRIMARY
    except Exception:
        try:
            response = client.chat.completions.create(
                model=SECONDARY,
                messages=[
                    {"role": "system", "content": "Ты — математический ассистент. Решай пошагово и понятно."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=5000
            )
            return response.choices[0].message.content.strip(), SECONDARY
        except RateLimitError:
            return "[GPT: превышен лимит]", "None"
        except Exception as e:
            return f"[GPT: ошибка — {e}]", "None"
