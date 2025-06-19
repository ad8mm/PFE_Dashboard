import os
os.environ["TRANSFORMERS_NO_TF"] = "1"  # Désactive TensorFlow

import requests
from transformers import pipeline
import streamlit as st
import pandas as pd
import re


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

POSITIVE_KEYWORDS = {
    "acquired": +0.05,
    "acquires": +0.05,
    "acquisition": +0.05,
    "buy": +0.04,
    "buys": +0.04,
    "tops": +0.04,
    "purchases": +0.04,
    "added": +0.03,
    "adds": +0.03,
    "increased": +0.04,
    "raises": +0.04,
    "boost": +0.05,
    "growth": +0.05,
    "rally": +0.04,
    "surge": +0.05,
    "bullish": +0.06,
    "breakout": +0.04,
    "uptrend": +0.04,
    "adoption": +0.05,
    "partnership": +0.05,
    "collaboration": +0.04,
    "approved": +0.05,
    "approval": +0.05,
    "launch": +0.04,
    "success": +0.05,
    "successful": +0.05,
    "profit": +0.04,
    "record high": +0.06,
    "new high": +0.05,
    "all-time high": +0.06,
    "invest": +0.04,
    "investing": +0.04,
    "support": +0.03,
    "expansion": +0.04,
    "innovation": +0.04,
    "upgrade": +0.03,
    "recovery": +0.03,
    "rebound": +0.04,
    "positive": +0.03,
    "gains": +0.03,
    "beats expectations": +0.05,
    "outperforms": +0.04
}


NEGATIVE_KEYWORDS = {
    "cut": -0.07,
    "cuts": -0.07,
    "sold": -0.05,
    "sell": -0.05,
    "sells": -0.05,
    "selling": -0.05,
    "reduces": -0.05,
    "reduced": -0.05,
    "dropped": -0.06,
    "drop": -0.05,
    "plunge": -0.07,
    "slump": -0.06,
    "bearish": -0.06,
    "falls":-0.06,
    "downtrend": -0.05,
    "crash": -0.08,
    "decline": -0.05,
    "declined": -0.05,
    "loss": -0.05,
    "losses": -0.05,
    "missed expectations": -0.06,
    "underperforms": -0.05,
    "resigned": -0.04,
    "lawsuit": -0.05,
    "hack": -0.06,
    "hacked": -0.06,
    "scam": -0.07,
    "regulatory scrutiny": -0.06,
    "banned": -0.07,
    "ban": -0.06,
    "warning": -0.04,
    "fined": -0.06,
    "penalty": -0.05,
    "collapse": -0.07,
    "down": -0.03,
    "negative": -0.03,
    "shutdown": -0.06,
    "layoff": -0.05,
    "delisted": -0.06,
    "recession": -0.05,
    "withdraw": -0.04,
    "withdrawal": -0.04,
    "rejected": -0.05,
    "failed": -0.06,
    "failure": -0.06,
    "fraud": -0.07,
    "suspension": -0.05,
    "lowers": -0.05,
    "embarassing":-0.05,
    "bad": -0.05,
    "bankruptcy": -0.08,
    "bankrupt": -0.08,
    "halts": -0.05,
    "plummets": -0.07,
    "plummeted": -0.07,
    "plummeting": -0.07,
    "at risk": -0.05,
    "exod": -0.05,
    "exodus": -0.05,
}



def is_blacklisted(article: dict):
    content = f"{article.get('title', '')} {article.get('description', '')}".lower()
    return any(bad in content for bad in BLACKLIST_KEYWORDS)

def is_relevant_article(article: dict, ticker: str, keywords: list[str]) -> bool:
    content = f"{article.get('title', '')} {article.get('description', '')}".lower()
    return any(kw.lower() in content for kw in [ticker.lower()] + [k.lower() for k in keywords])

def adjust_sentiment_score(text: str, original_score: float) -> float:
        score = original_score
        text_lower = text.lower()
        for word, boost in POSITIVE_KEYWORDS.items():
            if word in text_lower:
                score += boost
        for word, penalty in NEGATIVE_KEYWORDS.items():
            if word in text_lower:
                score += penalty
        return max(0.0, min(1.0, score))  # s'assurer que le score reste entre 0 et 1

from typing import Optional

def force_label_from_title(title: str) -> Optional[str]:
    title_lower = title.lower()
    for word in NEGATIVE_KEYWORDS:
        if word in title_lower:
            return "NEG"
    for word in POSITIVE_KEYWORDS:
        if word in title_lower:
            return "POS"
    return None


class NewsSentimentAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://newsapi.org/v2/everything"
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert"
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
            title = article.get("title", "")

            forced_label = force_label_from_title(title)

            if forced_label:
                article["sentiment"] = forced_label
                article["sentiment_score"] = 0.8 if forced_label == "POS" else 0.2
            else:
                try:
                    sentiment = self.sentiment_pipeline(text)[0]
                    adjusted_score = adjust_sentiment_score(text, sentiment["score"])

                    if adjusted_score >= 0.7:
                        label = "POS"
                    elif adjusted_score <= 0.3:
                        label = "NEG"
                    else:
                        label = "NEUTRAL"

                    article["sentiment"] = label
                    article["sentiment_score"] = adjusted_score
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
