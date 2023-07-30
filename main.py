
import textbase
from textbase.message import Message
from textbase import models
import os
import requests
from typing import List
from datetime import datetime, timedelta

# Load your OpenAI API key
models.OpenAI.api_key = "OPENAI_API_KEY"
# or from environment variable:
# models.OpenAI.api_key = os.getenv("OPENAI_API_KEY")

# Prompt for GPT-3.5 Turbo
SYSTEM_PROMPT = """You are chatting with an AI. Feel free to ask me any questions or talk about any topic you like, and I'll do my best to respond in a natural, conversational manner. Whether it's about science, technology, history, or just casual chit-chat, I'm here to chat with you!

Additionally, I can provide you with the current weather information for any city or town. Just ask me something like 'What's the weather in London?' or 'Tell me the weather forecast for New York.' I'll fetch the latest weather data for you.

If you ever want to end the conversation, simply say 'Goodbye' or 'Exit.' Now, let's have a pleasant chat!
"""


@textbase.chatbot("talking-bot")
def on_message(message_history: List[Message], state: dict = None):
    """Your chatbot logic here
    message_history: List of user messages
    state: A dictionary to store any stateful information

    Return a string with the bot_response or a tuple of (bot_response: str, new_state: dict)
    """

    if state is None or "counter" not in state:
        state = {"counter": 0}
    else:
        state["counter"] += 1

    user_message = message_history[-1].content.strip().lower()

    # Check if the user asks for weather information
    if "weather" in user_message:
        # Check if the user asks for current weather
        if "now" in user_message:
            location = extract_location(user_message)
            if location:
                current_weather = get_current_weather(location)
                if current_weather:
                    return current_weather, state
                else:
                    return f"Sorry, I couldn't fetch the current weather for {location}. Please try again.", state
            else:
                return "Please provide a valid location for weather information.", state

        # Check if the user asks for weather in the past
        days_ago = extract_days_ago(user_message)
        if days_ago is None:
            return "Please specify the number of days you want to know the weather for.", state

        location = extract_location(user_message)
        if location:
            weather_info = get_past_days_weather_info(location, days_ago)
            if weather_info:
                return weather_info, state
            else:
                return f"Sorry, I couldn't fetch weather information for {days_ago} days ago in {location}. Please try again.", state
        else:
            return "Please provide a valid location for weather information.", state

    # Generate GPT-3.5 Turbo response
    bot_response = models.OpenAI.generate(
        system_prompt=SYSTEM_PROMPT,
        message_history=message_history,
        model="gpt-3.5-turbo",
    )

    return bot_response, state


def extract_location(user_message):
    # Extract the location from the user's message
    prefixes = ["weather in", "what's the weather in", "what is the weather in"]
    for prefix in prefixes:
        if prefix in user_message:
            return user_message.replace(prefix, "").strip()
    return None


def extract_days_ago(user_message):
    # Extract the number of days ago from the user's message
    words = user_message.split()
    for i in range(len(words) - 1):
        if words[i] == "days" and words[i + 1].isdigit():
            return int(words[i + 1])
    return None


def get_current_weather(location):
    # Replace 'YOUR_OPENWEATHER_API_KEY' with your actual OpenWeatherMap API key
    api_key = 'YOUR_OPENWEATHER_API_KEY'
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    complete_url = f"{base_url}?q={location}&units=metric&appid={api_key}"

    try:
        response = requests.get(complete_url)
        data = response.json()

        if 'main' in data and 'weather' in data:
            temperature = data['main']['temp']
            weather_description = data['weather'][0]['description']
            return f"Current weather in {location}: {weather_description}. Temperature: {temperature}°C"
        else:
            return None

    except Exception as e:
        print(f"Error fetching current weather data: {e}")
        return None


def get_past_days_weather_info(location, days_ago):
    # Replace 'YOUR_OPENWEATHER_API_KEY' with your actual OpenWeatherMap API key
    api_key = 'YOUR_OPENWEATHER_API_KEY'
    base_url = "http://api.openweathermap.org/data/2.5/onecall/timemachine"
    start_date = (datetime.utcnow() - timedelta(days=days_ago)).timestamp()
    lat, lon = get_coordinates(location)

    if lat is None or lon is None:
        return None

    params = {
        "lat": lat,
        "lon": lon,
        "units": "metric",
        "dt": int(start_date),
        "appid": api_key
    }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        weather_info = []
        if 'hourly' in data:
            for hour in data['hourly']:
                timestamp = hour['dt']
                date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                weather_description = hour['weather'][0]['description']
                temperature = hour['temp']
                humidity = hour['humidity']
                weather_info.append(f"{date}: {weather_description}. Temperature: {temperature}°C, Humidity: {humidity}%")

        return f"Weather in {location} {days_ago} days ago:\n" + "\n".join(weather_info)

    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None


def get_coordinates(location):
    # Replace 'YOUR_OPENWEATHER_API_KEY' with your actual OpenWeatherMap API key
    api_key = 'YOUR_OPENWEATHER_API_KEY'
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    complete_url = f"{base_url}?q={location}&appid={api_key}"

    try:
        response = requests.get(complete_url)
        data = response.json()

        if 'coord' in data:
            return data['coord']['lat'], data['coord']['lon']
    except Exception as e:
        print(f"Error fetching location coordinates: {e}")

    return None, None
