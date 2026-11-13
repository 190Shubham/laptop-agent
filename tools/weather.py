import json
import urllib.parse
import urllib.request

# Used when you don't say a city. Change this to your own city.
DEFAULT_CITY = "Bengaluru"

CODES = {
    0: "clear sky", 1: "mostly clear", 2: "partly cloudy", 3: "cloudy",
    45: "foggy", 48: "foggy", 51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain", 71: "light snow", 73: "snow",
    75: "heavy snow", 80: "rain showers", 81: "rain showers", 82: "heavy rain showers",
    95: "a thunderstorm", 96: "a thunderstorm with hail", 99: "a thunderstorm with hail",
}
NOT_CITIES = ("today", "tomorrow", "now", "tonight", "outside", "here", "right now")


def _get(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def get_weather(city: str = "") -> str:
    """Tell the current weather and today's high and low for a city.
    Leave the city empty to use the default city."""
    city = (city or "").strip()
    if city.lower() in NOT_CITIES:
        city = ""
    city = city or DEFAULT_CITY
    try:
        geo = _get("https://geocoding-api.open-meteo.com/v1/search?count=1&name="
                   + urllib.parse.quote(city))
        results = geo.get("results") or []
        if not results:
            return f"I could not find a place called {city}."
        place = results[0]
        data = _get(
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={place['latitude']}&longitude={place['longitude']}"
            "&current=temperature_2m,apparent_temperature,weather_code"
            "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
            "&timezone=auto&forecast_days=1")
        current, day = data["current"], data["daily"]
        sky = CODES.get(current["weather_code"], "unclear weather")
        text = (f"In {place['name']} it is {current['temperature_2m']:.0f} degrees, {sky}. "
                f"Today's high is {day['temperature_2m_max'][0]:.0f} "
                f"and the low is {day['temperature_2m_min'][0]:.0f}.")
        rain = (day.get("precipitation_probability_max") or [None])[0]
        if rain is not None:
            text += f" The chance of rain is {rain} percent."
        return text
    except Exception:
        return "I could not get the weather right now. Please check your internet."