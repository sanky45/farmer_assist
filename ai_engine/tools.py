import requests
import os
from langchain.tools import tool
from .disease_detector import DiseaseDetectorService

detector_service = DiseaseDetectorService()
from dotenv import load_dotenv
load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


@tool
def get_weather(city: str) -> str:
    """Get current weather information for a city. Use this when users ask about weather conditions."""

    if not city or not isinstance(city, str):
        return "Please provide a valid city name."
    
    if not WEATHER_API_KEY:
        return "Weather API key not configured. Please set WEATHER_API_KEY environment variable."

    url = (
        f"http://api.openweathermap.org/data/2.5/weather?"
        f"q={city}&appid={WEATHER_API_KEY}&units=metric"
    )

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        data = response.json()

        # Extract weather information safely
        if "main" not in data or "weather" not in data:
            return f"Weather data for {city} is incomplete. Please try another city."

        temperature = data["main"].get("temp", "N/A")
        humidity = data["main"].get("humidity", "N/A")
        description = data["weather"][0].get("description", "Unknown")
        wind_speed = data.get("wind", {}).get("speed", "N/A")

        return (f"Weather for {city}: {temperature}°C, {description}. "
                f"Humidity: {humidity}%, Wind: {wind_speed} m/s")

    except requests.exceptions.Timeout:
        return f"Weather service timeout. Could not fetch data for {city}."
    except requests.exceptions.ConnectionError:
        return "Weather service connection error. Please try again later."
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            return f"City '{city}' not found. Please check the city name."
        return f"Weather service error: {e.response.status_code}"
    except Exception as e:
        return f"Unexpected error fetching weather: {str(e)}"


# Disease detection tool using the service defined in disease_detector.py
@tool
def detect_disease(image_path: str) -> str:
    """Run analysis on an uploaded crop image and return possible disease details.
    The input should be a local filesystem path to the saved image file."""

    if not image_path or not isinstance(image_path, str):
        return "Please provide a valid image path."

    try:
        result = detector_service.detect_disease(image_path)
        return result
    except Exception as e:
        return f"Error running disease detector: {str(e)}"
