from fastapi import FastAPI, Request
import requests, os, logging, asyncio
from dotenv import load_dotenv
from browser.playwright_driver import run
from telegram_bot.state import set_product_selection, set_order_confirmation
from models.deepseek_client import send_to_deepseek

# ──────────────────────────────────────────────────────────────────────────────
# Environment & Logging
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()
BOT_TOKEN   = os.getenv("BOT_TOKEN")
WEBHOOK_URL = "https://d6e6-149-34-244-133.ngrok-free.app/webhook"  # e.g. "https://<your‑ngrok‑domain>.ngrok‑free.app/webhook"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Telegram API Helpers
# ──────────────────────────────────────────────────────────────────────────────
def send_message(chat_id, text):
    return requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

def answer_callback_query(callback_id, text=None):
    return requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
        json={"callback_query_id": callback_id, "text": text}
    )


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI Webhook Endpoint
# ──────────────────────────────────────────────────────────────────────────────
app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    logger.info(f"Received update: {data}")

    if 'message' in data and 'text' in data['message']:
        chat_id = data['message']['chat']['id']
        user_text = data['message']['text']

        logger.info(f"📝 Received message from {chat_id}: {user_text}")

        # Parse with model
        parsed_list = send_to_deepseek(user_text, mode="parse_items")

        if not parsed_list or not isinstance(parsed_list, list):
            send_message(chat_id, "❌ Couldn't understand your shopping list. Please try again.")
            return {"status": "error"}

        send_message(chat_id, "📦 Processing your request...")

        # ✅ Define send_update INSIDE webhook so it can use chat_id
        async def send_update(message=None, photo_url=None, caption=None, reply_markup=None):
            payload = {
                "chat_id": chat_id,
                "text": message,
                "caption": caption,
                "photo": photo_url,
                "reply_markup": reply_markup.to_dict() if reply_markup else None
            }

            if photo_url:
                endpoint = "sendPhoto"
            else:
                endpoint = "sendMessage"

            resp = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/{endpoint}",
                json={k: v for k, v in payload.items() if v is not None}
            )
            logger.info(f"Telegram API response: {resp.text}")

        # 🔁 Run Playwright with this scoped send_update
        asyncio.create_task(run(
            parsed_list=parsed_list,
            send_update=send_update,
            auto_address=True,
            user_id=chat_id
        ))

    elif 'callback_query' in data:
        callback = data['callback_query']
        chat_id = callback['message']['chat']['id']
        user_id = callback['from']['id']
        callback_data = callback['data']
        callback_id = callback['id']

        # Acknowledge the button press
        answer_callback_query(callback_id, f"You selected: {callback_data}")

        # ✅ Critical step: update state
        if callback_data.startswith("select_"):
            # ✅ Keep it as string
            set_product_selection(user_id, callback_data)
            # 🔥 This wakes up the playwright wait
            #send_message(chat_id, f"🛒 Selected product index: {callback_data}")

        elif callback_data in ["confirm_order", "add_more"]:
            set_order_confirmation(user_id, callback_data)
            #send_message(chat_id, f"📥 Got your response: {callback_data.replace('_', ' ').title()}")

    return {"status": "ok"}


# ──────────────────────────────────────────────────────────────────────────────
# Webhook Management (run at startup)
# ──────────────────────────────────────────────────────────────────────────────
def set_webhook():
    resp = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
        json={"url": WEBHOOK_URL, "allowed_updates": ["message", "callback_query"]}
    )
    logger.info("setWebhook: %s", resp.json())

def get_webhook_info():
    resp = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
    logger.info("getWebhookInfo: %s", resp.json())

if __name__ == "__main__":
    import uvicorn
    set_webhook()
    get_webhook_info()
    uvicorn.run(app, host="0.0.0.0", port=5000)
