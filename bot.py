from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import os
import requests

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"

# --- Command Handlers ---

def start(update, context):
    """Sends a welcome message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_html(
        f"Hi {user.mention_html()}! I'm your Crypto Tracker bot. "
        "Use /price <symbol> for current prices, /alert <symbol> <target_price> to set an alert, or /news for crypto news."
    )

def help_command(update, context):
    """Sends a help message when the command /help is issued."""
    update.message.reply_text("Here are the commands you can use:\n"
                              "/price <symbol> - Get current price (e.g., /price btc)\n"
                              "/alert <symbol> <target_price> - Set a price alert (e.g., /alert eth 3000)\n"
                              "/myalerts - View your active alerts\n"
                              "/news - Get the latest crypto news\n"
                              "/help - Show this help message")

def get_crypto_price(symbol):
    """Fetches crypto price from CoinGecko API."""
    try:
        # CoinGecko uses 'id' which is often the lowercase name, not symbol.
        # A more robust solution would map symbols to CoinGecko IDs.
        response = requests.get(f"{COINGECKO_API_BASE}/simple/price?ids={symbol.lower()}&vs_currencies=usd")
        response.raise_for_status() # Raise an exception for HTTP errors
        data = response.json()
        if data and symbol.lower() in data:
            return data[symbol.lower()]['usd']
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        return None

def price_command(update, context):
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

# --- Placeholder for Alert and News features ---
# These will require more complex logic and potentially a database.

def set_alert_command(update, context):
    """Placeholder for /alert command."""
    update.message.reply_text("Alert functionality coming soon! This will require a database.")

def my_alerts_command(update, context):
    """Placeholder for /myalerts command."""
    update.message.reply_text("Alert functionality coming soon! This will require a database.")

def crypto_news_command(update, context):
    """Placeholder for /news command."""
    update.message.reply_text("News functionality coming soon! This will require a news API or RSS parsing.")

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    """Start the bot."""
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("price", price_command))
    dp.add_handler(CommandHandler("alert", set_alert_command))
    dp.add_handler(CommandHandler("myalerts", my_alerts_command))
    dp.add_handler(CommandHandler("news", crypto_news_command))


    # log all errors
    dp.add_handler(MessageHandler(Filters.all, error)) # Catch all for errors, though `error` handler above is more specific.

    # Start the Bot
    updater.start_polling() # For local development
    # For Render, you'll need to use webhook
    # updater.start_webhook(listen="0.0.0.0",
    #                       port=int(os.environ.get("PORT", "8080")),
    #                       url_path=TELEGRAM_BOT_TOKEN)
    # updater.bot.set_webhook("YOUR_RENDER_EXTERNAL_URL/" + TELEGRAM_BOT_TOKEN)


    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used only with start_polling().
    updater.idle()

if __name__ == '__main__':
    main()
