# Telegram + Gemini Bot

A Telegram bot that answers messages with Google Gemini. It sends easy questions to a light model and hard ones to a stronger model, falls back to the other model if one fails, and shows a "Thinking..." message while it works.

## Setup

1. Create a bot with @BotFather in Telegram and copy the token.
2. Create a Gemini API key in Google AI Studio.
3. Install the packages:

       pip install -r requirements.txt

4. Copy .env.example to .env and put your real keys in it.
5. Run the bot:

       python bot.py

## Notes

- Never commit your .env file. It is listed in .gitignore.
- Only one copy of the bot can run per Telegram token.

## License

MIT. See the LICENSE file.
