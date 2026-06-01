import requests

API_KEY = "YOUR_KEY_HERE"

response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={
        "Authorization": f"Bearer API_KEY",
        "Content-Type": "application/json"
    },
    json={
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "user",
                "content": "hello"
            }
        ]
    }
)

print(response.status_code)
print(response.text)