import os
import asyncio
import yfinance as yf
from telegram import Bot
from openai import AsyncOpenAI
from flask import Flask

# =========================
# Variables d’environnement
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OPENAI_KEY = os.getenv("OPENAI_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
client = AsyncOpenAI(api_key=OPENAI_KEY)

async def notify_startup():
    message = "Bot de trading Gold est maintenant en ligne sur Render !"
    await bot.send_message(chat_id=CHAT_ID, text=message)

# =========================
# Vérification opportunité
# =========================
def check_trading_opportunity(data, threshold=0.7):
    """
    Vérifie si une opportunité intéressante existe.
    threshold : variation minimale en % pour considérer une opportunité
    """
    last_close = data['Close'].iloc[-1]
    prev_close = data['Close'].iloc[-5]  # variation sur 5 bougies (≈ 1h15)
    change = (last_close - prev_close) / prev_close * 100

    if change >= threshold:
        return f"Opportunité Achat (Gold) : prix monté de {change:.2f}%"
    elif change <= -threshold:
        return f"Opportunité Vente (Gold) : prix baissé de {change:.2f}%"
    else:
        return None

# =========================
# Analyse IA pour TP/SL
# =========================
async def ai_analysis(market_data, signal):
    prompt = f"""
    Tu es un expert en trading sur l'or (XAUUSD).
    Voici un signal détecté : {signal}

    Donne une recommandation avec :
    - Un prix d'entrée
    - 3 Take Profit (TP1, TP2, TP3)
    - Un Stop Loss (SL)

    Contrainte : réponds de manière concise et structurée.
    Voici les données récentes du marché :
    {market_data}
    """
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# =========================
# Envoi Telegram
# =========================
async def send_signal(message):
    await bot.send_message(chat_id=CHAT_ID, text=message)

# =========================
# Boucle principale
# =========================
async def job():
    while True:
        data = yf.download("XAUUSD=X", period="1d", interval="15m").tail(20)
        signal = check_trading_opportunity(data)

        if signal:
            analysis = await ai_analysis(data.to_string(), signal)
            message = f"{signal}\n\n Analyse IA :\n{analysis}"
            await send_signal(message)
            print("Signal envoyé ✔️")
        else:
            print("Pas d'opportunité intéressante")

        await asyncio.sleep(60 * 15)  # toutes les 15 minutes

# =========================
# Flask (Render)
# =========================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot de trading Gold en ligne"

# =========================
# Lancer
# =========================
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(notify_startup())
    loop.create_task(job())
    app.run(host="0.0.0.0", port=10000)
