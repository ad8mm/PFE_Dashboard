import os
os.environ["TRANSFORMERS_NO_TF"] = "1"  # Désactive TensorFlow

import requests
from transformers import pipeline
import streamlit as st
import pandas as pd

# Dictionnaire pour améliorer la qualité des requêtes de recherche
TICKER_TO_QUERY = {
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "USDT-USD": "Tether",
    "BNB-USD": "Binance Coin",
    "SOL-USD": "Solana",
    "XRP-USD": "Ripple",
    "USDC-USD": "USD Coin",
    "DOGE-USD": "Dogecoin",
    "ADA-USD": "Cardano",
    "AVAX-USD": "Avalanche"
}

# RELEVANT_KEYWORDS = [
#     "crypto", "bitcoin", "ethereum", "blockchain", "token",
#     "web3", "wallet", "exchange", "coin", "altcoin"
# ]

# RELEVANT_SOURCES = [
#     "coindesk.com", "cointelegraph.com", "decrypt.co", "bitcoin.com",
#     "beincrypto.com", "theblock.co", "blockworks.co", "bitcoinmagazine.com",
#     "coingape.com", "u.today"
# ]

# # Remplacez RELEVANT_SOURCES (liste de domaines) par :
# RELEVANT_DOMAINS = "coindesk.com,cointelegraph.com,decrypt.co,bitcoin.com,beincrypto.com,theblock.co,blockworks.co,bitcoinmagazine.com,coingape.com,u.today"



# def is_relevant_article(article: dict) -> bool:
#     content = f"{article.get('title', '')} {article.get('description', '')}".lower()
#     return sum(kw in content for kw in RELEVANT_KEYWORDS) >= 2


class NewsSentimentAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://newsapi.org/v2/everything"
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            framework="pt"
        )

    def get_news(self, ticker: str, language="fr", page_size=10):
        query = TICKER_TO_QUERY.get(ticker.upper(), ticker)
        # sources_param = ",".join(RELEVANT_SOURCES)
        response = requests.get(
            self.endpoint,
            params={
                "q": query,
                "language": language,
                "sortBy": "publishedAt",
                "pageSize": page_size,
                "apiKey": self.api_key
            }
        )
        data = response.json()
        if data.get("status") != "ok":
            st.error(f"Erreur API News : {data.get('message', 'Inconnue')}")
            return []
        return data["articles"]

    def analyze_sentiment(self, articles):
        results = []
        for article in articles:
            # if not is_relevant_article(article):
            #     continue
            text = f"{article['title']} {article.get('description', '')}"[:512]
            try:
                sentiment = self.sentiment_pipeline(text)[0]
                if sentiment["score"] >= 0.7:
                    article["sentiment"] = "POS"
                elif sentiment["score"] <= 0.3:
                    article["sentiment"] = "NEG"
                else:
                    article["sentiment"] = "NEUTRAL"

                article["sentiment_score"] = sentiment["score"]
            except Exception:
                article["sentiment"] = "NEUTRAL"
                article["sentiment_score"] = 0.5
            results.append(article)
        return pd.DataFrame(results)

    def compute_market_sentiment(self, df: pd.DataFrame) -> str:
        if df.empty:
            return "Aucune donnée"

        avg_score = df["sentiment_score"].mean()
        count_pos = (df["sentiment"] == "POS").sum()
        count_neg = (df["sentiment"] == "NEG").sum()
        count_neu = (df["sentiment"] == "NEUTRAL").sum()
        total = len(df)

        if count_pos / total > 0.5:
            return f"🟢 Sentiment global : Positif ({avg_score:.2f})"
        elif count_neg / total > 0.5:
            return f"🔴 Sentiment global : Négatif ({avg_score:.2f})"
        else:
            return f"🟡 Sentiment global : Mitigé ({avg_score:.2f})"


    def display_news(self, articles):
        for article in articles[:5]:
            st.markdown(f"### [{article['title']}]({article['url']})")
            st.markdown(f"🗓️ *{article['publishedAt']}*")
            if article.get("description"):
                st.write(article["description"])
            color = {"POS": "green", "NEG": "red"}.get(article["sentiment"], "gray")
            st.markdown(
                f"Sentiment : <span style='color:{color}'><strong>{article['sentiment']}</strong> "
                f"({article['sentiment_score']:.2f})</span>",
                unsafe_allow_html=True
            )
            st.markdown("---")
