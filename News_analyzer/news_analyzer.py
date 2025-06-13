import requests
from transformers import pipeline
import streamlit as st
import pandas as pd

class NewsSentimentAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://newsapi.org/v2/everything"
        self.sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

    def get_news(self, query: str, language="fr", page_size=10):
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "language": language,
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "apiKey": self.api_key
        }
        response = requests.get(url, params=params)
        data = response.json()

        if data.get("status") != "ok":
            st.error(f"Erreur API News : {data.get('message', 'Inconnue')}")
            return []

        return data["articles"]

    def analyze_sentiment(self, articles):
        analyzed = []
        for article in articles:
            text = f"{article['title']} {article.get('description', '')}"[:512]
            sentiment = self.sentiment_pipeline(text)[0]
            article["sentiment"] = sentiment["label"]
            article["sentiment_score"] = sentiment["score"]
            analyzed.append(article)
        return pd.DataFrame(analyzed)

    def compute_market_sentiment(self, df: pd.DataFrame) -> str:
        if df.empty:
            return "Aucune donnée"

        avg_score = df["sentiment_score"].mean()

        if avg_score >= 0.6:
            return f"🟢 Sentiment global : Positif ({avg_score:.2f})"
        elif avg_score <= 0.4:
            return f"🔴 Sentiment global : Négatif ({avg_score:.2f})"
        else:
            return f"🟡 Sentiment global : Neutre ({avg_score:.2f})"

    def summarize_articles(self, df: pd.DataFrame, max_length=1300) -> str:
        if df.empty:
            return "Pas d'articles disponibles pour générer un résumé."

        texts = [f"{row['title']}. {row.get('description', '')}" for _, row in df.iterrows() if row.get('description')]
        corpus = " ".join(texts)

        try:
            summary_result = self.summarizer(corpus[:3000], max_length=150, min_length=50, do_sample=False)
            if not summary_result or "summary_text" not in summary_result[0]:
                return "Le résumé est vide ou mal formaté."
            summary = summary_result[0]["summary_text"]
            return f"📝 **Résumé des actualités** : {summary}"
        except Exception as e:
            return f"⚠️ Erreur lors de la génération du résumé : {e}"

    def display_news(self, articles):
        for article in articles[:5]:
            st.markdown(f"### [{article['title']}]({article['url']})")
            st.markdown(f"🗓️ *{article['publishedAt']}*")
            if article.get('description'):
                st.write(article['description'])
            sentiment_color = "green" if "POS" in article['sentiment'] else ("red" if "NEG" in article['sentiment'] else "gray")
            st.markdown(f"Sentiment : <span style='color:{sentiment_color}'><strong>{article['sentiment']}</strong> ({article['sentiment_score']:.2f})</span>", unsafe_allow_html=True)
            st.markdown("---")
