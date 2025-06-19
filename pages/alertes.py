import streamlit as st
import pandas as pd
import numpy as np
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
from scipy.signal import argrelextrema
from technical_indicators.indicators import TechnicalAnalyzer

st.set_page_config(page_title="Alertes Techniques", layout="wide")
st.title("🚨 Alertes Techniques Court Terme")

TICKERS = [
    "BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "BNB-USD", "XRP-USD",
    "ADA-USD", "DOGE-USD", "MATIC-USD", "SHIB-USD", "DOT-USD", "LTC-USD",
    "PEPE-USD", "FLOKI-USD", "ARB-USD", "OP-USD", "SUI-USD", "APT-USD",
    "NEAR-USD", "INJ-USD", "RNDR-USD"
]
TIMEFRAMES = {
    "15min": "15m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d"
}

analyzer = TechnicalAnalyzer()

def detect_bollinger_alerts_tracking(df, lookback=10):
    bb = BollingerBands(close=df["Close"], window=20, window_dev=2)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_middle"] = bb.bollinger_mavg()

    df["open_out_upper"] = df["Open"] > df["bb_upper"]
    df["close_out_upper"] = df["Close"] > df["bb_upper"]
    df["open_out_lower"] = df["Open"] < df["bb_lower"]
    df["close_out_lower"] = df["Close"] < df["bb_lower"]

    df["bulle_haussiere"] = df["open_out_upper"] & df["close_out_upper"]
    df["bulle_baissiere"] = df["open_out_lower"] & df["close_out_lower"]

    alerts = []
    df_recent = df.iloc[-lookback:]

    for i in range(len(df_recent)):
        row = df_recent.iloc[i]
        if row.name > pd.Timestamp.now(tz="Europe/Paris") - pd.Timedelta(hours=6):  # limiter à 6h max
            if row.get("bulle_baissiere", False):
                alerts.append({
                    "Ticker": None,
                    "Timeframe": None,
                    "Date": row.name.strftime("%Y-%m-%d %H:%M"),
                    "Type": "Bollinger Inf",
                    "Statut": "En cours",
                    "Ordre": "Achat",
                    "Objectif (prix)": round(row["bb_middle"], 2)
                })
            elif row.get("bulle_haussiere", False):
                alerts.append({
                    "Ticker": None,
                    "Timeframe": None,
                    "Date": row.name.strftime("%Y-%m-%d %H:%M"),
                    "Type": "Bollinger Sup",
                    "Statut": "En cours",
                    "Ordre": "Vente",
                    "Objectif (prix)": round(row["bb_middle"], 2)
                })

    return alerts


def detect_real_rsi_divergence(df, order=5):
    rsi = RSIIndicator(close=df["Close"], window=14).rsi()
    df["RSI"] = rsi

    local_min_idx = argrelextrema(df["Close"].values, np.less_equal, order=order)[0]
    local_max_idx = argrelextrema(df["Close"].values, np.greater_equal, order=order)[0]

    alerts = []

    for i in range(1, len(local_min_idx)):
        prev_idx, curr_idx = local_min_idx[i - 1], local_min_idx[i]
        if curr_idx - prev_idx < 4:
            continue
        if df["Close"].iloc[curr_idx] < df["Close"].iloc[prev_idx] and df["RSI"].iloc[curr_idx] > df["RSI"].iloc[prev_idx]:
            if df["RSI"].iloc[curr_idx] < 40:
                start_time = df.index[prev_idx].strftime("%Y-%m-%d %H:%M")
                end_time = df.index[curr_idx].strftime("%Y-%m-%d %H:%M")
                alerts.append({
                    "Ticker": None,
                    "Timeframe": None,
                    "Date": f"{start_time} - {end_time}",
                    "Type": "RSI Haussière",
                    "Statut": "En cours",
                    "Ordre": "Achat",
                    "Objectif RSI": 60
                })

    for i in range(1, len(local_max_idx)):
        prev_idx, curr_idx = local_max_idx[i - 1], local_max_idx[i]
        if curr_idx - prev_idx < 4:
            continue
        if df["Close"].iloc[curr_idx] > df["Close"].iloc[prev_idx] and df["RSI"].iloc[curr_idx] < df["RSI"].iloc[prev_idx]:
            if df["RSI"].iloc[curr_idx] > 60:
                start_time = df.index[prev_idx].strftime("%Y-%m-%d %H:%M")
                end_time = df.index[curr_idx].strftime("%Y-%m-%d %H:%M")
                alerts.append({
                    "Ticker": None,
                    "Timeframe": None,
                    "Date": f"{start_time} - {end_time}",
                    "Type": "RSI Baissière",
                    "Statut": "En cours",
                    "Ordre": "Vente",
                    "Objectif RSI": 40
                })

    return alerts

def convert_utc_to_paris(index):
    return pd.to_datetime(index, utc=True).tz_convert("Europe/Paris")

bollinger_alerts_total = []
rsi_alerts_total = []

for ticker in TICKERS:
    for tf_name, tf_code in TIMEFRAMES.items():
        with st.spinner(f"Analyse de {ticker} en {tf_name}..."):
            range_map = {"15m": "1d", "1h": "3d", "4h": "5d", "1d": "7d"}

            try:
                df = analyzer.fetch_yahoo_crypto_ohlc(ticker, range_=range_map[tf_code], interval=tf_code)
                if df is None or df.empty:
                    continue

                df = df.rename(columns=str.capitalize)

                if not isinstance(df.index, pd.DatetimeIndex):
                    continue

                df.index = convert_utc_to_paris(df.index)

                b_alerts = detect_bollinger_alerts_tracking(df)
                for a in b_alerts:
                    a["Ticker"] = ticker
                    a["Timeframe"] = tf_name
                    bollinger_alerts_total.append(a)

                r_alerts = detect_real_rsi_divergence(df)
                for a in r_alerts:
                    a["Ticker"] = ticker
                    a["Timeframe"] = tf_name
                    rsi_alerts_total.append(a)

            except Exception as e:
                st.warning(f"Erreur sur {ticker} ({tf_name}) : {e}")

if bollinger_alerts_total:
    st.subheader("📉 Alertes Bandes de Bollinger")
    df_boll = pd.DataFrame(bollinger_alerts_total)
    df_boll["Sort"] = pd.to_datetime(df_boll["Date"].str[:16], errors='coerce')
    df_boll = df_boll.sort_values("Sort", ascending=False).drop(columns=["Sort"])
    st.dataframe(df_boll, use_container_width=True)

if rsi_alerts_total:
    st.subheader("🔄 Divergences RSI")
    df_rsi = pd.DataFrame(rsi_alerts_total)
    df_rsi["Sort"] = pd.to_datetime(df_rsi["Date"].str[:16], errors='coerce')
    df_rsi = df_rsi.sort_values("Sort", ascending=False).drop(columns=["Sort"])
    st.dataframe(df_rsi, use_container_width=True)

if not bollinger_alerts_total and not rsi_alerts_total:
    st.success("✅ Aucune alerte détectée pour le moment.")