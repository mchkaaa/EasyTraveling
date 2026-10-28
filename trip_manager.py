import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

def generate_trip_plan(origin, destination, date, flight_data):
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        return None

    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        Маршрут: {origin} -> {destination}. Дата: {date}. Квитки: {flight_data}
        
        Поверни ТІЛЬКИ валідний JSON (без форматування ```json). Пиши максимально коротко:
        {{
            "flights": ["Авіакомпанія 1 від €XX", "Авіакомпанія 2 від €XX", "Авіакомпанія 3 від €XX"],
            "places": ["Локація 1", "Локація 2", "Локація 3"],
            "tip": "Коротка порада (до 5 слів)"
        }}
        """
        
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt
        )
        
        # Очищаємо від можливих маркерів тексту та перетворюємо в словник
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(raw_text)
        
    except Exception as e:
        print(f"Помилка ШІ: {e}")
        return None