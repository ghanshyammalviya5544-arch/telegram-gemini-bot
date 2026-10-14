import os
import asyncio

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]

MODEL_LITE = "gemini-3.1-flash-lite"
MODEL_PRO = "gemini-3.8-flash"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"


def call_gemini(model, prompt):
    headers = {"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    r = requests.post(GEMINI_URL.format(model), headers=headers, json=payload, timeout=60)
    print(f"[{model}] status:", r.status_code)
    data = r.json()
    if r.status_code != 200:
        raise RuntimeError(f"{r.status_code}: {data.get('error', {}).get('message', 'error')}")
    return data["candidates"][0]["content"]["parts"][0]["text"]


def heuristic_check(prompt):
    lower = prompt.lower()
    if any(k in lower for k in ["debug", "refactor", "code architecture", "proof"]) or len(prompt) > 400:
        return MODEL_PRO
    words = lower.split()
    if len(words) <= 4 and words[0] in ("hi", "hello", "hey", "thanks", "ok"):
        return MODEL_LITE
    return None


def llm_classify(prompt):
    routing_prompt = (
        "Classify the following query difficulty as either 'EASY' (casual chit-chat, "
        "simple question, translation) or 'HARD' (math, coding, logical reasoning, "
        "multi-step planning, detailed analysis).\n"
        "Output ONLY the single word EASY or HARD.\n\n"
        f"Query: {prompt}"
    )
    try:
        if "HARD" in call_gemini(MODEL_LITE, routing_prompt).upper():
            return MODEL_PRO
    except Exception:
        pass
    return MODEL_LITE


def execute_with_fallback(primary, prompt):
    fallback = MODEL_LITE if primary == MODEL_PRO else MODEL_PRO
    try:
        return call_gemini(primary, prompt), primary
    except Exception as e:
        print(f"[!] {primary} failed ({e}). Falling back to {fallback}...")
        return call_gemini(fallback, prompt), f"{fallback} (fallback)"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text or ""
    if not user_text.strip():
        await update.message.reply_text("Please send a text message.")
        return

    print(f"Received: {user_text}")
    status = await update.message.reply_text("Thinking...")
    try:
        model = heuristic_check(user_text)
        if not model:
            model = await asyncio.to_thread(llm_classify, user_text)
        reply, used = await asyncio.to_thread(execute_with_fallback, model, user_text)
        final_text = f"{reply}\n\n(Handled by: {used})"
        await status.edit_text(final_text[:4000])
        for i in range(4000, len(final_text), 4000):
            await update.message.reply_text(final_text[i:i + 4000])
        print(f"Reply sent via {used}")
    except Exception as e:
        print("Error occurred:", e)
        await status.edit_text("Sorry, something went wrong.")


if __name__ == "__main__":
    print("Bot is starting...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Polling Telegram... waiting for messages.")
    app.run_polling()
