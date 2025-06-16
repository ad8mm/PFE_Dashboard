import os
os.environ["TRANSFORMERS_NO_TF"] = "1"  # Désactive TensorFlow

import requests
from transformers import pipeline
import streamlit as st
import pandas as pd

class NewsSentimentAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://newsapi.org/v2/everything"
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            framework="pt"  # on force PyTorch
        )

    def get_news(self, query: str, language="fr", page_size=10):
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
            text = f"{article['title']} {article.get('description', '')}"[:512]
            try:
                sentiment = self.sentiment_pipeline(text)[0]
                article["sentiment"] = "POS" if sentiment["label"] == "POSITIVE" else "NEG"
                article["sentiment_score"] = sentiment["score"]
            except Exception:
                article["sentiment"] = "NEUTRAL"
                article["sentiment_score"] = 0.5
            results.append(article)
        return pd.DataFrame(results)

    def compute_market_sentiment(self, df: pd.DataFrame) -> str:
        if df.empty:
            return "Aucune donnée"
        avg = df["sentiment_score"].mean()
        if avg >= 0.6:
            return f"🟢 Sentiment global : Positif ({avg:.2f})"
        elif avg <= 0.4:
            return f"🔴 Sentiment global : Négatif ({avg:.2f})"
        else:
            return f"🟡 Sentiment global : Neutre ({avg:.2f})"

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
