import logging
import os
from datetime import datetime
from typing import Any, Dict, List

import requests


class TelegramSender:
    """Handles sending notifications to Telegram."""
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.logger = logging.getLogger(self.__class__.__name__)

    def send_prediction_update(self, predictions: List[Dict[str, Any]], metrics: Dict[str, Any]):
        """Formats and sends a prediction update."""
        if not self.bot_token or not self.chat_id:
            self.logger.warning("Telegram credentials not found. Skipping notification.")
            return

        date_str = datetime.now().strftime('%d-%b-%Y')
        
        message = [
            f"<b>🏆 KALYAN DAILY ANALYSIS - {date_str}</b>",
            f"<i>Historical Confidence (Top 5): {metrics.get('hit_rate_top5', 0)*100:.2f}%</i>",
            "",
            "<b>🔥 TOP 5 JODI PICKS:</b>"
        ]
        
        for i, p in enumerate(predictions[:5], 1):
            message.append(f"{i}. <code>{p['value']}</code> (Score: {p['score']:.4f})")
            
        message.append("")
        message.append("<b>✨ NEXT TOP 5 (TOTAL 10):</b>")
        for i, p in enumerate(predictions[5:10], 6):
            message.append(f"{i}. <code>{p['value']}</code>")
            
        full_message = "\n".join(message)
        self._send(full_message)

    def _send(self, text: str):
        """Internal helper to send the message via API."""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            self.logger.info("Telegram notification sent successfully.")
        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
