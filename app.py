import streamlit as st

# Header personnalisé
st.set_page_config(page_title="Dashboard Investissements", layout="wide")

st.title("Dashboard de Suivi d’Investissements et d'aide à la prise de décision")
st.subheader("Projet de Fin d’Études")
# Affichage du logo Cy Tech
st.image("uploads/cy-tech-logo.png", width=200)

st.markdown("""
**Collaborateurs :** Adam Da Eira, Leo Hu, Mathis Jousset, Mohamed-Amin Lamrini  

### Abstract

Ce projet de fin d’études vise à développer une **plateforme de suivi des investissements** permettant à tout investisseur particulier ou débutant de **centraliser etvisualiser facilement son portefeuille**, d’analyser sa répartition et de faciliter la **prise de décision éclairée**.

Grâce à l’intégration sécurisée de l’API Binance et à la récupération en temps réel des cours via CoinGecko, ce tableau de bord interactif propose :
- une **connexion sécurisée à l'API Binance avec chiffrement des clés**,
- un **tableau de synthèse** des cryptomonnaies possédées et leurs valeurs en USD associées,
- un **camembert interactif** représentant la répartition du portefeuille,
- une **base modulaire** pour intégrer des alertes, des indicateurs techniques ou de l’analyse de performance future.
            
Nous avons également développé une **section d’analyse technique** pour chaque cryptomonnaie, permettant :
- de récupérer les données de prix en by-passant l’API Yahoo Finance en utilisant un user-agent personnalisé,
- de visualiser les tendances et les signaux d’achat/vente en plusieurs timeframes.
- de recenser les actualités pertinentes et d’analyser le sentiment du marché via l’API NewsAPI et un modèle de **sentiment analysis**.

Ce projet reflète notre volonté d’allier **technique, sécurité et accessibilité** au service de l'investissement.

""")