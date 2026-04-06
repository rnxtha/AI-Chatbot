import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)
api_key = os.environ.get('GEMINI_API_KEY')

print(f"Key loaded: {api_key[:5]}...{api_key[-5:]}" if api_key else "No key found")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
payload = {
    "contents": [{"role": "user", "parts": [{"text": "Hello, this is a test."}]}]
}

try:
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
