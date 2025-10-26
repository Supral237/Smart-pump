# ============================================
# 🧠 SMART PUMP DETECTOR v1.0
# Auteur : Thierry & GPT
# Fonction : Détecter automatiquement les crypto qui pumpent
# ============================================

import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# ==========================
# 🧩 CHARGER LES VARIABLES ENVIRONNEMENT
# ==========================
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
LUNARCRUSH_API_KEY = os.getenv("LUNARCRUSH_API_KEY")
COINMARKETCAL_API_KEY = os.getenv("COINMARKETCAL_API_KEY")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")

# ==========================
# ⚙️ PARAMÈTRES DU BOT
# ==========================
TARGET_SYMBOLS = ["ASTR", "PEPE", "WIF", "SOL", "TIA"]  # cryptos à surveiller
SLEEP_TIME = 180  # intervalle de vérification (en secondes)
AGGRESSIVE_MODE = False  # True = plus d'alertes (moins strict)

# ==========================
# 🧠 FONCTIONS UTILITAIRES
# ==========================

def log(message: str):
    """Affiche proprement les logs avec l'heure."""
    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {message}")

def send_telegram(message: str):
    """Envoie une alerte sur Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log("❌ Clés Telegram manquantes")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=payload)
    except Exception as e:
        log(f"⚠️ Erreur Telegram: {e}")

# ==========================
# 📈 SIGNALS
# ==========================

def check_volume(symbol: str):
    """Vérifie si le volume 24h est en forte hausse (Binance public API)."""
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}USDT"
        r = requests.get(url, timeout=10)
        data = r.json()
        vol = float(data.get("quoteVolume", 0))
        price_change = float(data.get("priceChangePercent", 0))
        if price_change > 5 or vol > 50000000:
            return True, f"Volume élevé +{price_change:.1f}%"
        return False, ""
    except Exception:
        return False, ""

def check_social_hype(symbol: str):
    """Mesure la hype sociale (LunarCrush)."""
    try:
        url = f"https://lunarcrush.com/api3/coins?symbol={symbol}&data=metrics"
        headers = {"Authorization": f"Bearer {LUNARCRUSH_API_KEY}"}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json().get("data", [])
        if data and data[0].get("social_volume") and data[0]["social_volume"] > 200:
            return True, "Hausse du volume social 🚀"
        return False, ""
    except Exception:
        return False, ""

def check_whale_activity(symbol: str):
    """Vérifie s'il y a de gros transferts récents (Etherscan)."""
    try:
        url = f"https://api.etherscan.io/api?module=account&action=txlist&address=0x0000000000000000000000000000000000000000&page=1&offset=10&sort=desc&apikey={ETHERSCAN_API_KEY}"
        # NOTE: cette adresse est juste un placeholder, à remplacer par un vrai token si tu veux filtrer une adresse spécifique
        # Pour simplifier, on simule le signal ici :
        return False, ""  # Mets True pour tester les alertes
    except Exception:
        return False, ""

def check_events(symbol: str):
    """Détecte les événements à venir sur CoinMarketCal."""
    try:
        url = f"https://developers.coinmarketcal.com/v1/events?coins={symbol.lower()}"
        headers = {"x-api-key": COINMARKETCAL_API_KEY}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json().get("body", [])
        if len(data) > 0:
            return True, f"Annonce à venir ({len(data)} événements)"
        return False, ""
    except Exception:
        return False, ""

# ==========================
# 🧩 LOGIQUE DE DÉTECTION
# ==========================

def analyze_symbol(symbol: str):
    reasons = []
    signals = [
        check_volume(symbol),
        check_social_hype(symbol),
        check_whale_activity(symbol),
        check_events(symbol),
    ]
    for ok, reason in signals:
        if ok:
            reasons.append(reason)

    score = len(reasons)
    threshold = 2 if AGGRESSIVE_MODE else 3

    if score >= threshold:
        alert = (
            f"🚨 <b>ALERTE PUMP DÉTECTÉE</b>\n"
            f"Token : <b>{symbol}</b>\n"
            f"Score : {score}\n"
            f"Raisons : {', '.join(reasons)}\n"
            f"Heure : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        send_telegram(alert)
        log(f"✅ Signal fort pour {symbol} ({', '.join(reasons)})")
    else:
        log(f"Analyse {symbol} : score {score}")

# ==========================
# 🚀 LANCEMENT PRINCIPAL
# ==========================

def main():
    log(f"Smart Pump Detector lancé. Surveillance : {', '.join(TARGET_SYMBOLS)}")
    while True:
        for symbol in TARGET_SYMBOLS:
            try:
                analyze_symbol(symbol)
                time.sleep(5)
            except Exception as e:
                log(f"Erreur {symbol}: {e}")
        log(f"Pause {SLEEP_TIME}s avant la prochaine vérification...")
        time.sleep(SLEEP_TIME)

if __name__ == "__main__":
    main()