import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # Store your key in .env or environment
MODEL_NAME = "qwen/qwq-32b:free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def send_to_deepseek(user_message: str, mode="init"):
    if mode == "init":
        prompt = f"""
You are a smart grocery assistant. Greet the user and ask for their delivery address before anything else.
Wait for the user's response and do NOT assume what they want to buy yet. If there are no items in the user's message do not assume any.
"""
    elif mode == "parse_items":
        prompt = f"""
Extract shopping items from this message:

"{user_message}"

Respond ONLY in valid JSON:

[
  {{
    "product": "product name",
    "quantity": number,
    "unit": "optional unit like kg, pack, dozen"
  }}
]
"""
    else:
        raise ValueError("Unknown mode")


    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a helpful shopping assistant."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        print("❌ DeepSeek API error:", response.text)
        return []

    try:
        content = response.json()["choices"][0]["message"]["content"]
        if mode == "parse_items":
            return json.loads(content)
        return content

    except Exception as e:
        print("⚠️ Failed to parse DeepSeek response:", e)
        print("🔎 Raw model response:", response.text)
        return [] if mode == "parse_items" else ""

