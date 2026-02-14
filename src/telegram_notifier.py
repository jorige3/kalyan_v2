import os
import logging
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def send_telegram_message(message: str) -> bool:
    """
    Sends a message to a Telegram chat.

    Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from environment variables.
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    logging.debug(f"DEBUG: Retrieved bot_token: {bot_token is not None}, chat_id: {chat_id}")

    if not bot_token or not chat_id:
        logging.warning("Telegram bot token or chat ID not found in environment variables. Skipping Telegram notification.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "MarkdownV2"
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        logging.info("Telegram message sent successfully.")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send Telegram message: {e}")
        return False

def escape_markdown_v2_chars(text: str) -> str:
    """
    Escapes characters that have special meaning in Telegram's MarkdownV2.
    """
    # List of characters to escape: _ * [ ] ( ) ~ ` > # + - = | { } . ! \
    # The backslash '\' itself must be escaped first.
    escape_chars = r"\_*[]()~`>#+-=|{}.!\\"
    
    # Escape the backslash first, then other characters.
    # Note: Telegram's MarkdownV2 requires a backslash to be escaped with another backslash.
    escaped_text = text.replace('\\', '\\\\')
    for char in escape_chars:
        if char in escaped_text: # Only replace if the character is present
            escaped_text = escaped_text.replace(char, f"\\{char}")
    return escaped_text

if __name__ == "__main__":
    # Example usage (for testing purposes)
    test_message = "This is a *test message* from the Kalyan v2 project. Please ensure your Telegram bot token and chat ID are correctly set in your .env file."
    send_telegram_message(test_message)
