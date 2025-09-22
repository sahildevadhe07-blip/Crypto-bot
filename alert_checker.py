import os
import requests
import sqlite3
import logging
import time

from telegram import Bot
from db import get_db_connection, get_all_active_alerts, deactivate_alert # Import DB functions

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"

# Initialize the Bot outside the function to avoid recreating on each run
if TELEGRAM_BOT_TOKEN:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
else:
    logger.error("TELEGRAM_BOT_TOKEN not set for alert_checker.py. Alerts cannot be sent.")
    bot = None # Handle case where token is missing

def get_current_prices_for_symbols(symbols):
    """Fetches current prices for a list of symbols from CoinGecko."""
    if not symbols:
        return {}
    try:
        ids = ",".join(s.lower() for s in symbols)
        response = requests.get(f"{COINGECKO_API_BASE}/simple/price?ids={ids}&vs_currencies=usd")
        response.raise_for_status()
        data = response.json()
        return {k.upper(): v['usd'] for k, v in data.items()}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching prices for alert check: {e}")
        return {}

def check_and_send_alerts():
    """Checks all active alerts and sends notifications if triggered."""
    if not bot:
        logger.error("Bot is not initialized. Cannot send alerts.")
        return

    alerts = get_all_active_alerts()
    if not alerts:
        logger.info("No active alerts to check.")
        return

    # Get unique symbols to fetch prices efficiently
    unique_symbols = list(set(alert['symbol'] for alert in alerts))
    current_prices = get_current_prices_for_symbols(unique_symbols)

    if not current_prices:
        logger.warning("Could not fetch any current prices for active alerts.")
        return

    triggered_alerts = []

    for alert in alerts:
        symbol = alert['symbol'].upper()
        target_price = alert['target_price']
        alert_id = alert['id']
        chat_id = alert['chat_id']

        if symbol in current_prices:
            current_price = current_prices[symbol]
            # Simple logic: Trigger if current price meets or exceeds target price
            # You might want more complex logic (e.g., target below price, target above price)
            if current_price >= target_price:
                message = (f"🚨 Price Alert for {symbol}! 🚨\n"
                           f"Your target: ${target_price:,.2f}\n"
                           f"Current price: ${current_price:,.2f}")
                try:
                    bot.send_message(chat_id=chat_id, text=message)
                    triggered_alerts.append(alert_id)
                    logger.info(f"Alert {alert_id} triggered for {symbol} (Target: {target_price}, Current: {current_price})")
                except Exception as e:
                    logger.error(f"Failed to send alert {alert_id} to chat {chat_id}: {e}")
            else:
                logger.info(f"Alert {alert_id} for {symbol}: Not triggered (Current: {current_price}, Target: {target_price})")
        else:
            logger.warning(f"Could not get current price for {symbol} (Alert ID: {alert_id}). Skipping.")

    # Deactivate all triggered alerts
    for alert_id in triggered_alerts:
        deactivate_alert(alert_id)
    if triggered_alerts:
        logger.info(f"Deactivated {len(triggered_alerts)} triggered alerts.")

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set. Exiting alert checker.")
        exit(1)
    
    # Ensure DB is initialized before checking alerts (important for first run)
    from db import init_db
    init_db()
    
    check_and_send_alerts()
    logger.info("Alert checker run completed.")
