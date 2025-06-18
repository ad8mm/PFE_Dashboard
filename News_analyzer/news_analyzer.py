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
    "AVAX-USD": "Avalanche",
    "AAPL": "Apple",
    "GOOGL": "Google",
    "MSFT": "Microsoft",
    "AMZN": "Amazon",
    "NVDA": "Nvidia",
    "TSLA": "Tesla",
    "META": "Meta Platforms",
    "NFLX": "Netflix",
    "INTC": "Intel",
    "PYPL": "PayPal"
}

RELEVANT_DOMAINS = (
    "coindesk.com,cointelegraph.com,decrypt.co,bitcoin.com,"
    "beincrypto.com,theblock.co,blockworks.co,bitcoinmagazine.com,"
    "coingape.com,u.today"
)

CRYPTO_SOURCES = "coindesk.com,cointelegraph.com,decrypt.co,bitcoinmagazine.com"
STOCK_SOURCES = "bloomberg.com,cnbc.com,reuters.com,finance.yahoo.com"

CRYPTO_TICKERS = {
    "BTC-USD", "ETH-USD", "USDT-USD", "BNB-USD", "SOL-USD",
    "XRP-USD", "USDC-USD", "DOGE-USD", "ADA-USD", "AVAX-USD"
}

BLACKLIST_KEYWORDS = ["photography", "gaming", "travel", "recipe", "nintendo", "iphone"]

def is_blacklisted(article: dict):
    content = f"{article.get('title', '')} {article.get('description', '')}".lower()
    return any(bad in content for bad in BLACKLIST_KEYWORDS)

def is_relevant_article(article: dict, ticker: str, keywords: list[str]) -> bool:
    content = f"{article.get('title', '')} {article.get('description', '')}".lower()
    return any(kw.lower() in content for kw in [ticker.lower()] + [k.lower() for k in keywords])

class NewsSentimentAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://newsapi.org/v2/everything"
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            framework="pt"
        )

    def get_news(self, ticker: str, page_size=15):
        query = TICKER_TO_QUERY.get(ticker.upper(), ticker)
        context = "crypto" if ticker.upper() in CRYPTO_TICKERS else "stock"

        def query_news(language, use_domains=True):
            params = {
                "q": f"{query} {context}",
                "language": language,
                "sortBy": "publishedAt",
                "pageSize": page_size,
                "apiKey": self.api_key
            }
            if use_domains:
                domains = CRYPTO_SOURCES if ticker.upper() in CRYPTO_TICKERS else STOCK_SOURCES
                params["domains"] = domains

            return requests.get(self.endpoint, params=params).json()

        data = query_news(language="fr", use_domains=True)
        if data.get("status") != "ok" or not data.get("articles"):
            data = query_news(language="en", use_domains=False)

        if data.get("status") != "ok":
            st.error(f"Erreur API News : {data.get('message', 'Inconnue')}")
            return []

        return data["articles"]

    def analyze_sentiment(self, articles, ticker):
        keywords = TICKER_TO_QUERY.get(ticker.upper(), ticker).split()
        results = []
        for article in articles:
            if not is_relevant_article(article, ticker, keywords):
                continue

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
