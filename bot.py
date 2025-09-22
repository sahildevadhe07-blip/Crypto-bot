import os
import logging
import requests
import feedparser
import re # For parsing alert arguments

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from db import init_db, add_alert, get_active_alerts_for_user, deactivate_alert # Import DB functions

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"
PORT = int(os.environ.get('PORT', '8080')) # Render provides PORT env var
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") # This will be your Render app's external URL

# --- Utility Functions ---
def get_crypto_price(symbol):
    """Fetches crypto price from CoinGecko API."""
    try:
        # CoinGecko uses 'id' which is often the lowercase name.
        # We'll assume user inputs a common symbol like 'btc', 'eth'
        # For a production bot, you'd need a more robust mapping or search feature.
        response = requests.get(f"{COINGECKO_API_BASE}/simple/price?ids={symbol.lower()}&vs_currencies=usd")
        response.raise_for_status() # Raise an exception for HTTP errors
        data = response.json()
        if data and symbol.lower() in data:
            return data[symbol.lower()]['usd']
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        return None

def get_crypto_news():
    """Fetches latest crypto news from RSS feeds."""
    news_sources = [
        "https://www.coindesk.com/feed/",
        "https://cointelegraph.com/rss",
        # Add more RSS feeds here
    ]
    all_news = []
    for url in news_sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]: # Get top 3 from each source
                title = entry.title
                link = entry.link
                all_news.append(f"*{title}*\n{link}")
        except Exception as e:
            logger.error(f"Error fetching news from {url}: {e}")
            continue
    return "\n\n".join(all_news[:10]) # Limit total news items

# --- Command Handlers ---

def start(update: Update, context: CallbackContext) -> None:
    """Sends a welcome message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_html(
        f"Hi {user.mention_html()}! I'm your Crypto Tracker bot. "
        "Use /price <symbol> for current prices, /alert <symbol> <target_price> to set an alert, "
        "or /news for crypto news. Use /help for more options."
    )

def help_command(update: Update, context: CallbackContext) -> None:
    """Sends a help message when the command /help is issued."""
    update.message.reply_text(
        "Here are the commands you can use:\n"
        "/price <symbol> - Get current price (e.g., /price btc)\n"
        "/alert <symbol> <target_price> - Set a price alert (e.g., /alert eth 3000)\n"
        "/myalerts - View your active alerts\n"
        "/delete_alert <id> - Delete an alert by its ID (from /myalerts list)\n"
        "/news - Get the latest crypto news\n"
        "/help - Show this help message"
    )

def price_command(update: Update, context: CallbackContext) -> None:
    """Handles the /price command."""
    if not context.args:
        update.message.reply_text("Please specify a cryptocurrency symbol. E.g., /price btc")
        return

    symbol = context.args[0].lower()
    price = get_crypto_price(symbol)

    if price:
        update.message.reply_text(f"The current price of {symbol.upper()} is ${price:,.2f} USD.")
    else:
        update.message.reply_text(f"Could not fetch price for {symbol.upper()}. Please check the symbol.")

def set_alert_command(update: Update, context: CallbackContext) -> None:
    """Sets a price alert for the user."""
    if len(context.args) != 2:
        update.message.reply_text("Usage: /alert <symbol> <target_price> (e.g., /alert eth 3000)")
        return

    symbol = context.args[0].lower()
    try:
        target_price = float(context.args[1])
        if target_price <= 0:
            raise ValueError
    except ValueError:
        update.message.reply_text("Please provide a valid positive number for the target price.")
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    add_alert(chat_id, user_id, symbol, target_price)
    update.message.reply_text(f"Alert set for {symbol.upper()} at ${target_price:,.2f}.")

def my_alerts_command(update: Update, context: CallbackContext) -> None:
    """Displays active alerts for the user."""
    user_id = update.effective_user.id
    alerts = get_active_alerts_for_user(user_id)

    if not alerts:
        update.message.reply_text("You have no active alerts.")
        return

    response = "Your active alerts:\n"
    for alert in alerts:
        response += f"ID: {alert['id']}, {alert['symbol'].upper()} at ${alert['target_price']:,.2f}\n"
    response += "\nTo delete an alert, use /delete_alert <ID>"
    update.message.reply_text(response)

def delete_alert_command(update: Update, context: CallbackContext) -> None:
    """Deletes an alert by ID."""
    if not context.args or not context.args[0].isdigit():
        update.message.reply_text("Usage: /delete_alert <alert_id> (Get ID from /myalerts)")
        return

    alert_id = int(context.args[0])
    # Basic check: ensure the alert belongs to the user trying to delete it
    # A more robust system would fetch the alert and check user_id
    user_id = update.effective_user.id
    alerts = get_active_alerts_for_user(user_id)
    alert_to_delete = next((a for a in alerts if a['id'] == alert_id), None)

    if alert_to_delete:
        deactivate_alert(alert_id)
        update.message.reply_text(f"Alert ID {alert_id} for {alert_to_delete['symbol'].upper()} at ${alert_to_delete['target_price']:,.2f} has been deleted.")
    else:
        update.message.reply_text(f"Alert with ID {alert_id} not found or doesn't belong to you.")


def crypto_news_command(update: Update, context: CallbackContext) -> None:
    """Handles the /news command."""
    update.message.reply_text("Fetching latest crypto news...")
    news = get_crypto_news()
    if news:
        update.message.reply_text(news, parse_mode='Markdown', disable_web_page_preview=True)
    else:
        update.message.reply_text("Could not fetch crypto news at the moment.")

def error(update: Update, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main() -> None:
    """Start the bot."""
    init_db() # Initialize the database when the bot starts

    # Create the Updater and pass it your bot's token.
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("price", price_command))
    dp.add_handler(CommandHandler("alert", set_alert_command))
    dp.add_handler(CommandHandler("myalerts", my_alerts_command))
    dp.add_handler(CommandHandler("delete_alert", delete_alert_command))
    dp.add_handler(CommandHandler("news", crypto_news_command))

    # log all errors
    dp.add_handler(MessageHandler(Filters.all, error))

    # --- Start the Bot with Webhooks for Render ---
    if WEBHOOK_URL:
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TELEGRAM_BOT_TOKEN,
                              webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")
        logger.info(f"Bot started with webhook: {WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")
    else:
        logger.warning("WEBHOOK_URL not set. Running in polling mode (for local testing).")
        updater.start_polling() # Fallback for local testing if WEBHOOK_URL is not set
        updater.idle() # Only call idle if in polling mode

if __name__ == '__main__':
    # Ensure token and webhook URL are set for deployment
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set.")
        exit(1)
    # WEBHOOK_URL is optional for local testing, but required for Render deployment
    # if not WEBHOOK_URL:
    #     logger.error("WEBHOOK_URL environment variable not set. This is required for Render deployment.")
    #     exit(1)

    main()
