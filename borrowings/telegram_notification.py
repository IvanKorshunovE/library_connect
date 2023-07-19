import os

import requests
from dotenv import load_dotenv

load_dotenv()


def send_to_telegram(message=None):

    api_token = os.getenv("API_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    api_url = (
        f"https://api.telegram.org/bot{api_token}/sendMessage"
    )

    try:
        requests.post(api_url, json={'chat_id': chat_id, 'text': message})
    except Exception as e:
        return e
