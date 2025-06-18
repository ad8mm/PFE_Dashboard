import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from Ajout.technical_section import afficher_indicateurs
from Ajout.indicators import TechnicalAnalyzer
from News_analyzer.news_analyzer import NewsSentimentAnalyzer

# Fonction de récupération OHLC depuis Yahoo Finance
def fetch_yahoo_crypto_ohlc(ticker, range_="1y", interval="1d"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={range_}&interval={interval}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    
    if r.status_code != 200:
        st.error(f"Erreur HTTP {r.status_code} pour {ticker}")
        return None
    
    data = r.json()
    try:
        timestamps = data["chart"]["result"][0]["timestamp"]
        ohlc = data["chart"]["result"][0]["indicators"]["quote"][0]
        df = pd.DataFrame(ohlc, index=pd.to_datetime(timestamps, unit="s"))
        df.dropna(inplace=True)
        return df
    except Exception as e:
        st.error(f"Erreur de parsing : {e}")
        return None

# Mapping nom → ticker
name_to_ticker = {
    "bitcoin": "BTC-USD", "btc": "BTC-USD",
    "ethereum": "ETH-USD", "eth": "ETH-USD",
    "solana": "SOL-USD", "sol": "SOL-USD",
    "ripple": "XRP-USD", "xrp": "XRP-USD",
    "tether": "USDT-USD", "usdt": "USDT-USD",
    "binance coin": "BNB-USD", "bnb": "BNB-USD",
    "usd coin": "USDC-USD", "usdc": "USDC-USD",
    "dogecoin": "DOGE-USD", "doge": "DOGE-USD",
    "cardano": "ADA-USD", "ada": "ADA-USD",
    "avalanche": "AVAX-USD", "avax": "AVAX-USD"
}

st.title("🪙 Suivi des Cryptomonnaies")

# Liste de base
default_tickers = ["BTC-USD", "ETH-USD", "SOL-USD"]

# Barre de recherche
user_input = st.text_input("🔍 Ajouter une crypto", placeholder="ex: XRP, Bitcoin...").lower().strip()
new_ticker = name_to_ticker.get(user_input)

if new_ticker and new_ticker not in default_tickers:
    default_tickers.append(new_ticker)

# Sélection d'une crypto
selected_ticker = st.selectbox("📌 Sélectionnez une cryptomonnaie :", default_tickers)

# Timeframes disponibles
tf_map = {
    "M15": ("7d", "15m"),
    "H1": ("14d", "60m"),
    "H4": ("1mo", "1h"),
    "D1": ("1y", "1d")
}
timeframe = st.selectbox("⏱️ Choisir la timeframe :", list(tf_map.keys()), index=3)
period, interval = tf_map[timeframe]

# Récupération des données
df_chart = fetch_yahoo_crypto_ohlc(selected_ticker, range_=period, interval=interval)

if df_chart is None or df_chart.empty:
    st.error(f"❌ Données indisponibles pour {selected_ticker} à cette granularité.")
else:
    fig = go.Figure(data=[go.Candlestick(
        x=df_chart.index,
        open=df_chart["open"],
        high=df_chart["high"],
        low=df_chart["low"],
        close=df_chart["close"]
    )])
    fig.update_layout(
        title=f"Graphique Bougie - {selected_ticker} ({interval})",
        xaxis_title="Date",
        yaxis_title="Prix (USD)",
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig, use_container_width=True)

# Analyse technique
st.markdown("---")
st.subheader(f"📊 Analyse Technique - {selected_ticker}")
afficher_indicateurs(selected_ticker, period, interval)

# Analyse de sentiment
st.markdown("---")
st.subheader(f"💬 Analyse de sentiment - {selected_ticker}")
with st.expander("📰 Actualités & Sentiment", expanded=True):
    api_key = "e30e3507bcf14b97a836b42f10718586"
    news_analyzer = NewsSentimentAnalyzer(api_key=api_key)

    search_term = selected_ticker.split("-")[0]
    news_df = news_analyzer.analyze_sentiment(
        news_analyzer.get_news(search_term, page_size=100)
    )

    st.subheader("🧭 Sentiment du marché")
    st.markdown(news_analyzer.compute_market_sentiment(news_df))
    news_analyzer.display_news(news_df.to_dict(orient="records"))
