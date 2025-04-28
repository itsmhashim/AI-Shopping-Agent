import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # Store your key in .env or environment
MODEL_NAME = "google/gemini-2.5-pro-exp-03-25:free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

def send_to_gemini(product_name, product_options, user_message):
    prompt = f"""
You are a smart shopping assistant helping users select the best product.

The user is interested in: "{product_name}"
User message: "{user_message}"

Here are the top 3 product options:
1. {product_options[0]}
2. {product_options[1]}
3. {product_options[2]}

Please recommend the best option. If multiple are equally good, ask the user to clarify.
Respond in a short, conversational format.
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "You are a smart shopping assistant that helps users choose the best product from a list."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        print("❌ Gemini error:", response.text)
        return None

    try:
        return response.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print("⚠️ Failed to parse Gemini response:", e)
        print("🔍 Raw response:", response.json())  # <-- ADD THIS LINE
        return None
