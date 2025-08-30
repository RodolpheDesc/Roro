import os
import yfinance as yf
import telegram
import openai
import schedule
import time

# === CONFIG ===
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
OPENAI_KEY = os.environ.get("OPENAI_KEY")

bot = telegram.Bot(token=TELEGRAM_TOKEN)
openai.api_key = OPENAI_KEY

print(os.environ.get("OPENAI_KEY"))

def get_market_data():
    """Récupère les 10 dernières bougies horaires de l'or"""
    data = yf.download("XAUUSD=X", period="1d", interval="1h")
    last_data = data.tail(10)
    return last_data.to_string()

def ai_analysis(market_data):
    """Demande à GPT une analyse et une recommandation"""
    prompt = f"""
    Voici les 10 dernières bougies de l'or (XAU/USD) :
    {market_data}
    
    Donne une recommandation de trading (Achat, Vente ou Attente), 
    avec une courte justification en 2-3 phrases maximum.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4",   # ou "gpt-3.5-turbo" si tu veux moins cher
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    
    return response["choices"][0]["message"]["content"]

def job():
    """Exécute une analyse et envoie sur Telegram"""
    try:
        market_data = get_market_data()
        analysis = ai_analysis(market_data)
        bot.send_message(chat_id=CHAT_ID, text=analysis)
        print("Signal envoyé ✔️")
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    # Envoie un signal toutes les 2 heures
    schedule.every(2).hours.do(job)
    print("Bot démarré ✅")
    job()  # Lancer immédiatement une première analyse

    while True:
        schedule.run_pending()
        time.sleep(60)
