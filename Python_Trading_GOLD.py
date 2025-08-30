import os
import asyncio
import threading
import yfinance as yf
import openai
from telegram import Bot
from flask import Flask

# === CONFIG ===
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
OPENAI_KEY = os.environ.get("OPENAI_KEY")
PORT = int(os.environ.get("PORT", 10000))  # Render injecte la variable PORT

bot = Bot(token=TELEGRAM_TOKEN)
openai.api_key = OPENAI_KEY

# === FLASK MINIMAL POUR RENDER ===
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot Telegram en ligne"

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

threading.Thread(target=run_flask).start()

# === FONCTIONS BOT ===
def get_market_data():
    """Récupère les 10 dernières bougies horaires de l'or, avec fallback"""
    try:
        data = yf.download("XAUUSD=X", period="1d", interval="1h")
        if data.empty:
            print("XAUUSD=X vide, fallback sur GC=F")
            data = yf.download("GC=F", period="1d", interval="1h")
        if data.empty:
            print("Pas de données disponibles sur Yahoo Finance")
            return "Données indisponibles"
        return data.tail(10).to_string()
    except Exception as e:
        print(f"Erreur récupération Yahoo Finance: {e}")
        return "Données indisponibles"

async def ai_analysis(market_data: str) -> str:
    """Demande à l'IA une recommandation de trading"""
    prompt = f"""
    Voici les 10 dernières bougies de l'or (XAU/USD) :
    {market_data}

    Donne une recommandation de trading (Achat, Vente ou Attente),
    avec une courte justification en 2-3 phrases maximum.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response["choices"][0]["message"]["content"]

async def send_signal(message: str):
    """Envoie un message sur Telegram"""
    await bot.send_message(chat_id=CHAT_ID, text=message)

async def job():
    """Récupère les données, analyse et envoie sur Telegram"""
    try:
        market_data = get_market_data()
        analysis = await ai_analysis(market_data)
        await send_signal(analysis)
        print("Signal envoyé ✔️")
    except Exception as e:
        print(f"Erreur: {e}")

# === BOUCLE PRINCIPALE ===
async def main_loop():
    """Exécute le job toutes les 2 heures"""
    while True:
        await job()
        await asyncio.sleep(2 * 60 * 60)  # 2 heures en secondes

if __name__ == "__main__":
    asyncio.run(main_loop())
