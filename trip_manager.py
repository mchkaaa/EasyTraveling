import os
import json
from dotenv import load_dotenv
from groq import Groq

# Завантажуємо змінні з .env
load_dotenv()

# Ініціалізуємо клієнта Groq
client = Groq(api_key=os.getenv("LLM_API_KEY"))

def generate_trip_plan(origin, destination, date, flight_data):
    prompt = f"""
    Ти ШІ-помічник для планування подорожей. Склади маршрут.
    Звідки: {origin}
    Куди: {destination}
    Дати: {date}
    Дані про реальні рейси від API: {flight_data}
    
    ВАЖЛИВО: Відповідь ТІЛЬКИ у форматі JSON без жодного іншого тексту.
    
    ПРАВИЛА ДЛЯ РЕЙСІВ (СУВОРО):
    1. РОЗПОДІЛИ отримані рейси між 'cheap', 'medium' та 'expensive' рівномірно. 
    2. ОБМЕЖЕННЯ: У кожній категорії має бути РІВНО 2 рядки (один "✈️ Туди:" і один "✈️ Назад:"). НЕ БІЛЬШЕ! Ніколи не роби довгих списків з 5-10 рейсів в одній колонці.
    3. Якщо API повернув мало рейсів, краще залиш 'expensive' порожнім ([]), але не переповнюй 'medium'.
    4. НІКОЛИ не дублюй рейси.
    
    СТРУКТУРА JSON:
    {{
        "flights": {{
            "cheap": ["✈️ Туди: [Дані API з ціною]", "✈️ Назад: [Дані API з ціною]"],
            "medium": ["✈️ Туди: [Дані API з ціною]", "✈️ Назад: [Дані API з ціною]"],
            "expensive": ["✈️ Туди: [Дані API з ціною]", "✈️ Назад: [Дані API з ціною]"]
        }},
        "places": ["[Локація 1]", "[Локація 2]"],
        "tip": "[Порада]"
    }}
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="qwen/qwen3.8-27b",
            temperature=0.3, # Зменшили температуру для меншої фантазії
            response_format={"type": "json_object"} 
        )
        
        import json
        response_text = chat_completion.choices[0].message.content.strip()
        return json.loads(response_text)
        
    except Exception as e:
        print(f"Помилка сервера Groq: {e}")
        return {
            "flights": {"cheap": [], "medium": [], "expensive": []},
            "places": ["Помилка генерації"],
            "tip": "Спробуйте ще раз."
        }
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="qwen/qwen3.8-27b",
            temperature=0.5,
            response_format={"type": "json_object"} # Гарантує повернення чистого JSON
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        return json.loads(response_text)
        
    except Exception as e:
        print(f"Помилка сервера Groq: {e}")
        return {
            "flights": ["Перевірка рейсів тимчасово призупинена"],
            "places": ["Очікування відновлення зв'язку з сервером"],
            "tip": "Сервер тимчасово перевантажений запитами або сталася помилка. Зачекайте хвилину та спробуйте ще раз."
        }