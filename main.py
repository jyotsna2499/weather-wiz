from fastapi import FastAPI, HTTPException
import requests
import json
from dotenv import load_dotenv
import os

app = FastAPI()
load_dotenv()

# Configure your API keys here
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def get_weather_data(city: str):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="City not found")
    return response.json()

def generate_weather_summary(weather_data, promptFromUser):
    # Extract data from weather API response
    temp = weather_data['main']['temp']
    weather_description = weather_data['weather'][0]['description']
    city = weather_data['name']

    # Create a prompt for the LLM
    prompt = f"The weather in {city} is currently {weather_description} with a temperature of {temp}°C. {promptFromUser}"
    
    # Generate response using Mistral API
    url = 'https://openrouter.ai/api/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    body = {
        'model': 'mistralai/mistral-7b-instruct:free',
        'messages': [
            {'role': 'user', 'content': prompt}
        ]
    }
    
    response = requests.post(url, headers=headers, json=body)
    result = response.json()
    
    # Extract and return the summary from the response
    if 'choices' in result and len(result['choices']) > 0:
        return result['choices'][0]['message']['content'].strip()
    
    return "No forecast data available."

@app.get("/forecast/{city}")
async def get_forecast(city: str, prompt: str):
    try:
        weather_data = get_weather_data(city)
        forecast_summary = generate_weather_summary(weather_data, prompt)
        return {"city": city, "forecast": forecast_summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

