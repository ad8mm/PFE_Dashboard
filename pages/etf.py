import streamlit as st
import plotly.graph_objects as go
from utils.data_loader import load_prices

st.title("📦 Suivi des ETF")

tickers = ['SPY', 'VOO', 'QQQ']
selection = st.sidebar.multiselect("Sélectionnez des ETF :", tickers, default=tickers[:2])

if selection:
    data = load_prices(selection)

    fig = go.Figure()
    for ticker in selection:
        fig.add_trace(go.Scatter(x=data.index, y=data[ticker], mode='lines', name=ticker))

    fig.update_layout(title="Historique des Prix ETF", xaxis_title="Date", yaxis_title="Prix (USD)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Veuillez sélectionner au moins un ETF.")
