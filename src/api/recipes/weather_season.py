"""
Weather + Season detector for Recipe Maker AI
Input: city, state, date
Output: current weather data + Indian season + regional context for recipe selection

APIs used:
  - Open-Meteo Geocoding: https://geocoding-api.open-meteo.com (no key needed)
  - Open-Meteo Weather:   https://api.open-meteo.com (no key needed)
"""
from datetime import date
from dataclasses import dataclass
from typing import Optional
import httpx


@dataclass
class WeatherData:
    city: str
    state: str
    latitude: float
    longitude: float
    temperature_c: float
    feels_like_c: float
    humidity_pct: float
    precipitation_mm: float
    wind_kmh: float
    weather_code: int
    weather_description: str
    season: str
    season_hindi: str
    region_type: str
    recipe_context: dict


WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}

INDIA_REGIONS = {
    "north": [
        "delhi", "uttar pradesh", "haryana", "punjab", "himachal pradesh",
        "uttarakhand", "jammu and kashmir", "ladakh", "chandigarh",
    ],
    "south": [
        "kerala", "tamil nadu", "karnataka", "andhra pradesh", "telangana",
        "puducherry", "lakshadweep",
    ],
    "east": [
        "west bengal", "odisha", "jharkhand", "bihar",
    ],
    "northeast": [
        "assam", "meghalaya", "manipur", "mizoram", "nagaland", "tripura",
        "arunachal pradesh", "sikkim",
    ],
    "west": [
        "maharashtra", "gujarat", "rajasthan", "goa", "dadra and nagar haveli",
        "daman and diu",
    ],
    "central": [
        "madhya pradesh", "chhattisgarh",
    ],
}


def _get_region(state: str) -> str:
    s = state.lower().strip()
    for region, states in INDIA_REGIONS.items():
        if any(s in st or st in s for st in states):
            return region
    return "central"


def _get_indian_season(month: int, region: str, temp_c: float, precip_mm: float) -> tuple[str, str]:
    """
    Returns (season_english, season_hindi)
    Indian seasons vary by region:
    - North: Summer(Mar-Jun), Monsoon(Jul-Sep), Autumn(Oct-Nov), Winter(Dec-Feb)
    - South: Summer(Feb-May), SW Monsoon(Jun-Sep), NE Monsoon(Oct-Dec), Mild Winter(Jan-Feb)
    - Northeast: Pre-monsoon(Mar-May), Heavy Monsoon(Jun-Oct), Dry(Nov-Feb)
    - Rajasthan/West: Extreme Summer(Apr-Jun), Monsoon(Jul-Sep), Pleasant(Oct-Feb)
    """
    if region == "northeast":
        if month in (12, 1, 2):
            return "Winter", "शीतकाल"
        elif month in (3, 4, 5):
            return "Pre-monsoon", "पूर्व-मानसून"
        elif month in (6, 7, 8, 9, 10):
            return "Monsoon", "मानसून"
        else:
            return "Post-monsoon", "मानसूनोत्तर"

    if region == "south":
        if month in (1, 2):
            return "Mild Winter", "शीतकाल"
        elif month in (3, 4, 5):
            return "Summer", "ग्रीष्मकाल"
        elif month in (6, 7, 8, 9):
            return "Southwest Monsoon", "दक्षिण-पश्चिम मानसून"
        elif month in (10, 11):
            return "Northeast Monsoon", "उत्तर-पूर्व मानसून"
        else:
            return "Mild Winter", "शीतकाल"

    # North, Central, East, West
    if month in (12, 1, 2):
        return "Winter", "शीतकाल"
    elif month == 3:
        return "Spring", "वसंत"
    elif month in (4, 5, 6):
        return "Summer", "ग्रीष्मकाल"
    elif month in (7, 8, 9):
        return "Monsoon", "मानसून"
    else:
        return "Autumn", "शरद"


def _build_recipe_context(
    season: str,
    region: str,
    temp_c: float,
    humidity_pct: float,
    precip_mm: float,
    weather_code: int,
) -> dict:
    is_raining = precip_mm > 0.5 or weather_code in range(51, 100)
    is_very_hot = temp_c > 35
    is_cold = temp_c < 15
    is_humid = humidity_pct > 70

    cooking_style = []
    avoid = []
    prefer = []
    seasonal_ingredients = []

    if season in ("Summer", "Extreme Summer"):
        prefer = ["cooling", "light", "hydrating"]
        seasonal_ingredients = ["cucumber", "watermelon", "mint", "curd", "raw mango", "kokum", "sattu"]
        cooking_style = ["uncooked", "cold", "lightly sauteed"]
        avoid = ["heavy fried", "very spicy", "hot soups"]

    elif season in ("Winter", "Mild Winter"):
        prefer = ["warming", "hearty", "spiced"]
        seasonal_ingredients = ["sarson", "methi", "gajar", "matar", "til", "jaggery", "dry fruits", "amla"]
        cooking_style = ["slow cooked", "dum", "tadka heavy"]
        avoid = ["cold salads", "ice-based drinks"]

    elif "Monsoon" in season:
        prefer = ["warming", "comforting", "freshly cooked", "immunity boosting"]
        seasonal_ingredients = ["corn", "jamun", "peach", "litchi", "ginger", "tulsi", "turmeric"]
        cooking_style = ["freshly cooked", "pakora", "soups", "khichdi"]
        avoid = ["raw vegetables", "street food", "leafy greens (contamination risk)"]

    elif season == "Spring":
        prefer = ["light", "festive", "colorful"]
        seasonal_ingredients = ["mango (raw)", "strawberry", "peas", "spring onion", "radish"]
        cooking_style = ["grilled", "stir-fried", "light curries"]
        avoid = []

    elif season in ("Autumn", "Post-monsoon"):
        prefer = ["balanced", "moderate spice", "variety"]
        seasonal_ingredients = ["pomegranate", "papaya", "guava", "sweet potato", "beetroot"]
        cooking_style = ["baked", "roasted", "light curries"]
        avoid = []

    if is_raining:
        prefer.insert(0, "hot snacks")
        seasonal_ingredients.insert(0, "pakora ingredients")
        cooking_style.insert(0, "deep fried (monsoon special)")

    return {
        "prefer_cooking_styles": cooking_style,
        "prefer_food_types": prefer,
        "seasonal_ingredients": seasonal_ingredients,
        "avoid": avoid,
        "is_raining_now": is_raining,
        "is_very_hot": is_very_hot,
        "is_cold": is_cold,
        "is_humid": is_humid,
        "region": region,
    }


def get_weather_and_season(
    city: str,
    state: str,
    query_date: Optional[date] = None,
) -> WeatherData:
    if query_date is None:
        query_date = date.today()

    # Step 1: Geocoding — city → lat/lon
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    with httpx.Client(timeout=10) as client:
        geo_resp = client.get(geo_url, params={
            "name": city,
            "count": 5,
            "language": "en",
            "format": "json",
            "countryCode": "IN",
        })
    geo_resp.raise_for_status()
    geo_data = geo_resp.json()

    if not geo_data.get("results"):
        raise ValueError(f"City not found: {city}, {state}")

    # Pick result matching state if multiple results returned
    results = geo_data["results"]
    state_lower = state.lower().strip()
    result = next(
        (r for r in results if state_lower in (r.get("admin1", "") or "").lower()),
        results[0],
    )
    lat = result["latitude"]
    lon = result["longitude"]
    resolved_city = result.get("name", city)

    # Step 2: Current weather
    weather_url = "https://api.open-meteo.com/v1/forecast"
    with httpx.Client(timeout=10) as client:
        w_resp = client.get(weather_url, params={
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m",
                "apparent_temperature",
                "relative_humidity_2m",
                "precipitation",
                "wind_speed_10m",
                "weather_code",
            ],
            "timezone": "Asia/Kolkata",
            "forecast_days": 1,
        })
    w_resp.raise_for_status()
    w_data = w_resp.json()["current"]

    temp = w_data["temperature_2m"]
    feels = w_data["apparent_temperature"]
    humidity = w_data["relative_humidity_2m"]
    precip = w_data["precipitation"]
    wind = w_data["wind_speed_10m"]
    code = w_data["weather_code"]
    desc = WEATHER_CODES.get(code, "Unknown")

    region = _get_region(state)
    season, season_hindi = _get_indian_season(query_date.month, region, temp, precip)
    recipe_ctx = _build_recipe_context(season, region, temp, humidity, precip, code)

    return WeatherData(
        city=resolved_city,
        state=state,
        latitude=lat,
        longitude=lon,
        temperature_c=temp,
        feels_like_c=feels,
        humidity_pct=humidity,
        precipitation_mm=precip,
        wind_kmh=wind,
        weather_code=code,
        weather_description=desc,
        season=season,
        season_hindi=season_hindi,
        region_type=region,
        recipe_context=recipe_ctx,
    )


if __name__ == "__main__":
    import json
    from dataclasses import asdict

    tests = [
        ("Mumbai", "Maharashtra"),
        ("Jaipur", "Rajasthan"),
        ("Amritsar", "Punjab"),
        ("Chennai", "Tamil Nadu"),
        ("Guwahati", "Assam"),
    ]

    for city, state in tests:
        try:
            w = get_weather_and_season(city, state)
            print(f"\n{'='*50}")
            print(f"{w.city}, {w.state}  ({w.region_type} India)")
            print(f"Temp: {w.temperature_c}°C  Feels: {w.feels_like_c}°C  Humidity: {w.humidity_pct}%")
            print(f"Precip: {w.precipitation_mm}mm  Wind: {w.wind_kmh} km/h")
            print(f"Weather: {w.weather_description}")
            print(f"Season: {w.season} ({w.season_hindi})")
            print(f"Recipe context:")
            print(f"  Prefer: {w.recipe_context['prefer_food_types']}")
            print(f"  Seasonal ingredients: {w.recipe_context['seasonal_ingredients']}")
            print(f"  Avoid: {w.recipe_context['avoid']}")
            print(f"  Raining: {w.recipe_context['is_raining_now']}")
        except Exception as e:
            print(f"{city}: ERROR — {e}")
