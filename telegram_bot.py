import os
import requests

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_approval_request(full_name: str, draft_tweet: str, images: list):

    keyboard = {
        "inline_keyboard": [[
            {"text": "Approve", "callback_data": f"approve|{full_name}"},
            {"text": "Reject", "callback_data": f"reject|{full_name}"},
        ]]
    }

    caption = f"{full_name}\n\n{draft_tweet}"

    if images:
        url = f"{TELEGRAM_API_BASE}/sendPhoto"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": images[0],
            "caption": caption[:1024],
            "reply_markup": keyboard,
        }
    else:
        url = f"{TELEGRAM_API_BASE}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": caption,
            "reply_markup": keyboard,
        }

    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def answer_callback_query(callback_query_id: str, text: str):
    """Stops the little loading spinner on the Telegram button after a tap."""
    url = f"{TELEGRAM_API_BASE}/answerCallbackQuery"
    requests.post(url, json={"callback_query_id": callback_query_id, "text": text})


def edit_message_after_decision(chat_id, message_id, original_text: str, decision: str, has_photo: bool):
    """Edits the original message to show the decision was recorded and removes the buttons."""
    status_line = "Approved and posted" if decision == "approved" else "Rejected"
    new_text = f"{original_text}\n\n---\n{status_line}"

    if has_photo:
        url = f"{TELEGRAM_API_BASE}/editMessageCaption"
        payload = {"chat_id": chat_id, "message_id": message_id, "caption": new_text[:1024]}
    else:
        url = f"{TELEGRAM_API_BASE}/editMessageText"
        payload = {"chat_id": chat_id, "message_id": message_id, "text": new_text}

    requests.post(url, json=payload)
