import requests

API_KEY = "AIzaSyBQYpuW_qoCQcK2d-W6LcMdf-l57KyT5rg"

# Try different models 
models = [
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash", 
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash-8b",
]

results = []
for model in models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
    payload = {"contents": [{"role": "user", "parts": [{"text": "hi"}]}]}
    r = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=30)
    line = f"{model} => Status: {r.status_code} => {r.text[:200]}"
    results.append(line)
    if r.status_code == 200:
        results.append(f"*** SUCCESS: {model} ***")
        break

with open('test_results.txt', 'w', encoding='utf-8') as f:
    f.write('\n\n'.join(results))
print("Done - check test_results.txt")
