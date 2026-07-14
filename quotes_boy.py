import json
import os
import random

import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

STATE_FILE = "state.json"
QUOTES_FILE = "quotes.json"


def load_json(path, default):
    """Load a JSON file, or return `default` if it doesn't exist yet."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return default


def save_json(path, data):
    """Write `data` to a JSON file, formatted for readability."""
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def get_updates(offset):
    """Ask Telegram for any messages sent to the bot since the last check."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"offset": offset, "timeout": 0}
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()["result"]


def send_message(text):
    """Send `text` to the configured Telegram chat."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)


def pick_quote(quotes, used_texts):
    """Pick a random quote that hasn't been used yet. Reset the pool once all have been shown."""
    available = [q for q in quotes if q["text"] not in used_texts]
    if not available:
        used_texts.clear()
        available = quotes
    quote = random.choice(available)
    used_texts.append(quote["text"])
    return quote


def main():
    state = load_json(STATE_FILE, {"offset": 0, "used_quotes": []})
    quotes = load_json(QUOTES_FILE, [])

    updates = get_updates(state["offset"])

    for update in updates:
        state["offset"] = update["update_id"] + 1  # move past this update so we don't see it again
        message = update.get("message", {})
        text = message.get("text", "").strip()

        if text == "/quote":
            if quotes:
                quote = pick_quote(quotes, state["used_quotes"])
                send_message(f'"{quote["text"]}"\n— {quote["author"]}')
            else:
                send_message("Цитат пока нет в базе.")

    save_json(STATE_FILE, state)


if __name__ == "__main__":
    main()