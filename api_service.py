import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Допоміжна функція для отримання внутрішніх ID аеропортів
def get_airport_ids(airport_code):
    api_key = os.getenv("RAPIDAPI_KEY")
    url = "https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchAirport"
    querystring = {"query": airport_code}
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "sky-scrapper.p.rapidapi.com"
    }
    
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    
    if data.get("status") and data.get("data"):
        first_result = data["data"][0]
        # Дістаємо потрібні значення з глибини словника
        flight_params = first_result.get("navigation", {}).get("relevantFlightParams", {})
        return flight_params.get("skyId"), flight_params.get("entityId")
    
    return None, None

def search_flights(origin, destination, date):
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        return "API ключ не знайдено"

    # Крок 1. Дістаємо внутрішні коди (entityId) для обох міст
    origin_sky, origin_entity = get_airport_ids(origin)
    dest_sky, dest_entity = get_airport_ids(destination)

    if not origin_entity or not dest_entity:
        return f"Не вдалося знайти внутрішні коди для аеропортів {origin} або {destination}."

    # Крок 2. Шукаємо квитки з правильними параметрами
    url = "https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchFlights"
    querystring = {
        "originSkyId": origin_sky,
        "destinationSkyId": dest_sky,
        "originEntityId": origin_entity,
        "destinationEntityId": dest_entity,
        "date": date,
        "cabinClass": "economy",
        "adults": "1"
    }
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "sky-scrapper.p.rapidapi.com"
    }
    
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    
    # Крок 3. Красиво обробляємо відповідь сервера
    if data.get("status") and "data" in data:
        itineraries = data["data"].get("itineraries", [])
        
        if not itineraries:
            return f"✈️ На жаль, рейсів {origin} -> {destination} на обрану дату не знайдено. Спробуй змінити день."
            
        # Якщо рейси є, беремо перші 3 найдешевші
        results = ["Знайдені авіаквитки:"]
        for flight in itineraries[:3]:
            price = flight.get("price", {}).get("formatted", "Немає ціни")
            legs = flight.get("legs", [])
            if legs:
                airline = legs[0].get("carriers", {}).get("marketing", [{}])[0].get("name", "Невідома а/к")
                dep_time = legs[0].get("departure", "")[-8:-3] # беремо лише час (години:хвилини)
                arr_time = legs[0].get("arrival", "")[-8:-3]
                
                results.append(f"• {airline}: {dep_time} - {arr_time} | {price}")
                
        return "\n".join(results)
        
    return "Сталася помилка при обробці даних від сервера."

def check_city_exists(city_name):
    """Перевіряє чи існує місто через Open-Meteo та повертає його правильну назву"""
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&language=uk&count=1"
    try:
        response = requests.get(url, timeout=3).json()
        if "results" in response:
            return response["results"][0].get("name", city_name)
        return False
    except Exception:
        return False