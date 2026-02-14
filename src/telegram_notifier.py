import html  # Added
import json
import logging
import os

import requests

# Configure logging
# Set level to DEBUG temporarily to see all messages, will revert to INFO later
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def send_telegram_message(message: str) -> bool:
    """
    Sends a message to a Telegram chat.

    Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from environment variables.
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    # Mask bot_token for logging
    masked_bot_token = bot_token[:5] + "..." + bot_token[-5:] if bot_token and len(bot_token) > 10 else bot_token
    logging.debug(f"DEBUG: Using bot_token: {masked_bot_token}, chat_id: {chat_id}")

    if not bot_token or not chat_id:
        logging.warning("Telegram bot token or chat ID not found in environment variables. Skipping Telegram notification.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    logging.debug(f"DEBUG: Telegram API URL: {url}")
    logging.debug(f"DEBUG: Telegram API Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        logging.info("Telegram message sent successfully.")
        return True
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"Failed to send Telegram message: HTTP error occurred: {http_err} - Response: {response.text}")
        return False
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Failed to send Telegram message: Request error occurred: {req_err}")
        return False

def escape_html_chars(text: str) -> str:
    """
    Escapes characters that have special meaning in Telegram's HTML parse mode.
    """
    # Use html.escape from Python's standard library for robust HTML escaping.
    return html.escape(text, quote=True)

if __name__ == "__main__":
    # Example usage (for testing purposes) with HTML
    test_message_html = (
        "This is a <b>test message</b> from the Kalyan v2 project.\n"
        "Please ensure your Telegram bot token and chat ID are correctly set in your .env file.\n"
        "Here's some <i>italic text</i> and <code>code example</code>."
        "And a <a href='https://example.com'>link</a> with some & characters."
    )
    # Since the message already contains HTML tags, we should only escape the dynamic content,
    # or ensure the test message itself is properly formed HTML.
    # For a simple test, we will assume the above string is well-formed.
    send_telegram_message(test_message_html)
