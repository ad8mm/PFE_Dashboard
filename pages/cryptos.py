import streamlit as st
import plotly.graph_objects as go
import yfinance as yf
from data.utils.data_loader import load_prices
from Ajout.technical_section import afficher_indicateurs
from Ajout.indicators import TechnicalAnalyzer
from News_analyzer.news_analyzer import NewsSentimentAnalyzer

st.title("🪙 Suivi des Cryptomonnaies")

tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD']
selection = st.sidebar.multiselect("Sélectionnez des cryptos :", tickers, default=tickers[:2])

tf_map = {
    "M15": ("7d", "15m"),
    "H1": ("7d", "60m"),
    "H4": ("1mo", "1h"),
    "D1": ("1y", "1d")
}
timeframe = st.selectbox("⏱️ Choisir la timeframe :", list(tf_map.keys()), index=3)
period, interval = tf_map[timeframe]

analyzer = TechnicalAnalyzer()

if selection:
    st.markdown(f"### 📈 Graphique Bougie - {selection[0]} ({timeframe})")

    # On limite à 1 crypto pour le graphe bougie
    main_ticker = selection[0]
    df_chart = analyzer.get_data(main_ticker, period=period, interval=interval)

    if df_chart is not None and {'Open', 'High', 'Low', 'Close'}.issubset(df_chart.columns):
        fig = go.Figure(data=[
            go.Candlestick(
                x=df_chart.index,
                open=df_chart['Open'],
                high=df_chart['High'],
                low=df_chart['Low'],
                close=df_chart['Close'],
                name=main_ticker
            )
        ])
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Prix (USD)",
            title=f"Graphique Bougies - {main_ticker} ({interval})",
            xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Données OHLC non disponibles pour ce ticker ou cette granularité.")


    st.markdown("---")
    for ticker in selection:
        st.subheader(f"📊 Analyse Technique - {ticker}")
        afficher_indicateurs(ticker, period, interval)

    st.markdown("---")
    with st.expander("Afficher l'analyse de sentiment", expanded=True):
        st.subheader(f"📰 Dernières actualités sur {ticker}")

        # 🔑 Clé API NewsAPI
        api_key = "e30e3507bcf14b97a836b42f10718586"
        analyzer = NewsSentimentAnalyzer(api_key=api_key)

        # Récupération et analyse des actualités
        search_term = ticker.replace("-USD", "")  # Exemple : "BTC" → meilleur pour une requête API
        if search_term == "BTC":
            search_term = "Bitcoin"
        elif search_term == "ETH":
            search_term = "Ethereum"
        elif search_term == "SOL":
            search_term = "Solana"
        # Tu peux ajouter d'autres mappings ici

        news_df = analyzer.analyze_sentiment(analyzer.get_news(search_term, page_size=100))


        # Sentiment global du marché
        sentiment_global = analyzer.compute_market_sentiment(news_df)
        st.subheader(f"🧭 Analyse de sentiment du marché sur {ticker}")
        st.markdown(sentiment_global)

        # Résumé synthétique
        # resume = analyzer.summarize_articles(news_df)
        # st.markdown(resume)
        
        # Détails des actualités
        analyzer.display_news(news_df.to_dict(orient="records"))


else:
    st.info("Veuillez sélectionner au moins une cryptomonnaie.")
