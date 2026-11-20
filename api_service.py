import os
import requests
import re
from dotenv import load_dotenv

load_dotenv()

# --- СУПЕР-ФУНКЦІЯ: Безкоштовний пошук IATA-кодів (Без лімітів і ключів) ---
# --- ОНОВЛЕНА ФУНКЦІЯ: Шукає конкретні аеропорти (FCO, MXP), а не загальні міста ---
def get_location_id(city_name):
    url = "https://autocomplete.travelpayouts.com/places2"
    
    # Крок 1: Спочатку шукаємо конкретний АЕРОПОРТ
    params_airport = {
        "term": city_name,
        "locale": "uk",
        "types[]": "airport"
    }
    try:
        response = requests.get(url, params=params_airport, timeout=5).json()
        if response and len(response) > 0:
            code = response[0].get("code").upper()
            print(f"🌍 Знайдено аеропорт для {city_name}: {code}")
            return code
            
        # Крок 2: Якщо прямого аеропорту немає, беремо код МІСТА як запасний варіант
        params_city = {
            "term": city_name,
            "locale": "uk",
            "types[]": "city"
        }
        response_city = requests.get(url, params=params_city, timeout=5).json()
        if response_city and len(response_city) > 0:
            code = response_city[0].get("code").upper()
            print(f"🌍 Знайдено місто для {city_name}: {code}")
            return code
            
    except Exception as e:
        print(f"Помилка TravelPayouts для {city_name}: {e}")
    return None

def get_one_way_flights(origin_id, dest_id, date, api_key):
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_flights",
        "departure_id": origin_id,     
        "arrival_id": dest_id,         
        "outbound_date": date,
        "type": "2", # ВАЖЛИВО: 2 означає пошук квитка ТІЛЬКИ в один бік
        "currency": "EUR",
        "hl": "uk",
        "api_key": api_key
    }
    try:
        response = requests.get(url, params=params).json()
        flights = response.get("best_flights", []) + response.get("other_flights", [])
        flights.sort(key=lambda x: x.get("price", 999999))
        
        formatted = []
        for f in flights[:5]: # Беремо 5 варіантів
            price = f.get("price", "Немає ціни")
            if f.get("flights"):
                airline = f["flights"][0].get("airline", "Невідома а/к")
                dep = f["flights"][0].get("departure_airport", {}).get("time", "")[-5:]
                arr = f["flights"][0].get("arrival_airport", {}).get("time", "")[-5:]
                formatted.append(f"• {airline}: {dep} - {arr} | {price}€")
        return formatted
    except Exception:
        return []

def search_flights(origin, destination, date):
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return "API ключ SerpApi не знайдено."

    origin_id = get_location_id(origin)
    dest_id = get_location_id(destination)

    if not origin_id or not dest_id:
        return f"Не вдалося знайти аеропорти для {origin} або {destination}."

    try:
        dates = re.findall(r'\d{2}\.\d{2}\.\d{4}', date)
        if len(dates) >= 2:
            outbound_date = f"{dates[0][6:10]}-{dates[0][3:5]}-{dates[0][0:2]}"
            return_date = f"{dates[1][6:10]}-{dates[1][3:5]}-{dates[1][0:2]}"
        else:
            raise ValueError("Немає двох дат")
    except:
        outbound_date, return_date = "2026-12-15", "2026-12-20"

    # Робимо два окремі пошуки!
    outbound_results = get_one_way_flights(origin_id, dest_id, outbound_date, api_key)
    return_results = get_one_way_flights(dest_id, origin_id, return_date, api_key)

    final_text = f"Квитки ({origin} <-> {destination}):\n"
    final_text += "ТУДИ:\n" + ("\n".join(outbound_results) if outbound_results else "Не знайдено") + "\n"
    final_text += "НАЗАД:\n" + ("\n".join(return_results) if return_results else "Не знайдено")
    
    print("========== ДАНІ ВІД GOOGLE FLIGHTS ==========\n" + final_text + "\n=============================================")
    return final_text

def check_city_exists(city_name):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&language=uk&count=1"
    try:
        response = requests.get(url, timeout=3).json()
        if "results" in response:
            return response["results"][0].get("name", city_name)
        return False
    except Exception:
        return False


