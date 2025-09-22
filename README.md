# Crypto Tracker Telegram Bot

A Telegram bot that provides cryptocurrency prices, news, and allows users to set price alerts.

## Features

*   **Real-time Price Tracking:** Get current prices for various cryptocurrencies.
*   **Price Alerts:** Set custom alerts for target prices.
*   **Crypto News:** Fetch the latest news from popular crypto sources.

## Deployment

This bot is designed to be deployed on [Render.com](https://render.com) using its Web Service and Cron Job features.

### Setup

1.  **Clone this repository:**
    `git clone https://github.com/yourusername/crypto-tracker-bot.git`
    `cd crypto-tracker-bot`

2.  **Install dependencies:**
    `pip install -r requirements.txt`

3.  **Get a Telegram Bot Token:**
    *   Talk to `@BotFather` on Telegram.
    *   Use `/newbot` to create a new bot and get your API Token.

4.  **Environment Variables:**
    *   Rename `.env.example` to `.env` (for local testing)
    *   Fill in your `TELEGRAM_BOT_TOKEN`.
    *   `WEBHOOK_URL` will be provided by Render.

### Running Locally (for development)

You can run `bot.py` locally for testing. The `start_polling()` mode will be used if `WEBHOOK_URL` is not set.

```bash
# Create a .env file from .env.example and fill in TELEGRAM_BOT_TOKEN
source .env
python bot.py
