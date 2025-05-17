from llama_cpp import Llama
import os

MODEL_PATH = os.path.join("models", "mistral-7b-instruct-v0.1.Q4_K_M.gguf")

llm = Llama(model_path=MODEL_PATH, n_ctx=2048, n_gpu_layers=40)

def ask_model(prompt: str) -> str:
    full_prompt = f"""
    [INST]
    Ты — математический помощник. Твоя задача — пошагово разложить решение задачи и для каждого шага дать отдельное арифметическое выражение.

    Пример:
    Вопрос: У студента было 1200 рублей. Он потратил 25% на еду и 300 на книги. Сколько осталось?
    Ответ:
    Шаг 1: 1200 * 0.25
    Шаг 2: 300 + 300
    Шаг 3: 1200 - 600

    Теперь задача:
    {prompt}
    Ответ:
    [/INST]
    """
    result = llm(full_prompt.strip(), max_tokens=500, temperature=0.4)
    return result["choices"][0]["text"].strip()

