import streamlit as st
import requests
import hmac
import hashlib
import time
import os
from cryptography.fernet import Fernet
import json
import pandas as pd
import plotly.express as px
from pycoingecko import CoinGeckoAPI


def get_prices_in_usdt(assets):
    cg = CoinGeckoAPI()
    ids_map = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "BNB": "binancecoin",
        "SOL": "solana",
        "XRP": "ripple",
        "USDT": "tether",
        "DOGE": "dogecoin",
        "ADA": "cardano",
        "AVAX": "avalanche-2",
        "VET": "vechain",
        "STX": "stacks-2",
        "JASMY": "jasmycoin",
        "NMR": "numeraire",
        "AXS": "axie-infinity",
        "CKB": "nervos-network",
        "CFX": "conflux-token",
        "AR": "arweave",
        "BICO": "biconomy",
        "IMX": "immutable-x",
        "STRK": "starknet",
        "TAO": "bittensor",
        "NOT": "notcoin",
        "RENDER": "render",
        "S": "sonic",
        "ANKR": "ankr"
    }
    filtered = {k: v for k, v in ids_map.items() if k in assets}
    prices = cg.get_price(ids=list(filtered.values()), vs_currencies="usd")
    result = {k: prices.get(v, {}).get("usd", 0) for k, v in filtered.items()}
    # Prix manuels si pas trouvés
    if "STX" in assets and not result.get("STX"):
        result["STX"] = 0.6285
    if "RENDER" in assets and not result.get("RENDER"):
        result["RENDER"] = 3.93

    return result


st.title("📊 Suivi des investissements (Binance)")

# Chargement ou génération d'une clé de chiffrement Fernet
KEY_FILE = "fernet.key"
if not os.path.exists(KEY_FILE):
    with open(KEY_FILE, "wb") as f:
        f.write(Fernet.generate_key())

with open(KEY_FILE, "rb") as f:
    fernet = Fernet(f.read())

# Formulaire pour rentrer les clés API
with st.form("binance_form"):
    api_key = st.text_input("🔐 API Key", type="password")
    api_secret = st.text_input("🔒 API Secret", type="password")
    submitted = st.form_submit_button("Se connecter")

if submitted:
    try:
        # Chiffrement (optionnel, pour stockage temporaire si besoin)
        enc_key = fernet.encrypt(api_key.encode())
        enc_secret = fernet.encrypt(api_secret.encode())

        # Fonction pour interroger l’API REST Binance
        def get_binance_balances(key: str, secret: str):
            timestamp = int(time.time() * 1000)
            query_string = f"timestamp={timestamp}"
            signature = hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

            headers = {"X-MBX-APIKEY": key}
            url = f"https://api.binance.com/api/v3/account?{query_string}&signature={signature}"

            response = requests.get(url, headers=headers)
            return response.json()

        # Appel
        decrypted_key = fernet.decrypt(enc_key).decode()
        decrypted_secret = fernet.decrypt(enc_secret).decode()
        data = get_binance_balances(decrypted_key, decrypted_secret)

        st.success("✅ Connexion réussie !")
        st.subheader("💼 Portefeuille")

        assets = {a['asset']: float(a['free']) for a in data['balances'] if float(a['free']) > 0}
        prices = get_prices_in_usdt(assets)
        converted = {coin: qty * prices.get(coin, 0) for coin, qty in assets.items()}

        df_assets = pd.DataFrame([
            {"Coin": coin, "Quantité": qty, "Valeur ($)": converted[coin]}
            for coin, qty in assets.items()
        ]).sort_values(by="Valeur ($)", ascending=False)

        total_value = df_assets["Valeur ($)"].sum()

        st.metric("💰 Valeur totale du portefeuille ($)", f"{total_value:,.2f} $")
        st.dataframe(df_assets, use_container_width=True)

        fig = px.pie(df_assets, names="Coin", values="Valeur ($)", title="Répartition du portefeuille")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Erreur : {e}")
