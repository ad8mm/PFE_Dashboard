# Trigger redeployment (Python 3.9)
import streamlit as st

# Header personnalisé
st.set_page_config(page_title="Dashboard Investissements", layout="wide")

st.title("Dashboard de Suivi d’Investissements et d'aide à la prise de décision")
st.subheader("Projet de Fin d’Études")
# Affichage du logo Cy Tech
st.image("uploads/cy-tech-logo.png", width=200)

st.markdown("""
**Collaborateurs :** Adam Da Eira, Leo Hu, Mathis Jousset, Mohamed-Amin Lamrini  

## Abstract

Ce projet de fin d’études vise à développer une **plateforme de suivi des investissements** permettant à tout investisseur particulier ou débutant de **centraliser et visualiser facilement son portefeuille**, d’analyser sa répartition et de faciliter la **prise de décision**.\n

##### NB: \n 
Ce projet ne constitue pas un conseil financier et ne doit pas être utilisé pour des transactions réelles. Il est destiné à des fins éducatives et de démonstration uniquement.\n 
L'investissement comporte des risques, et il est important de faire ses propres recherches avant de prendre des décisions financières.\n

-----------------------
### Fonctionnalités principales

#### 1. Suivi des investissements (connexion à l'API Binance)

Grâce à l’intégration sécurisée de l’API Binance et à la récupération en temps réel des cours via CoinGecko, ce tableau de bord interactif propose :
- une **connexion sécurisée à l'API Binance avec chiffrement des clés** (algorithme de FERNET) et requêtes sécurisées (HMAC-256),
- un **tableau de synthèse** des cryptomonnaies possédées et leurs valeurs en USD associées,
- des **graphiques intéractifs** représentant la répartition du portefeuille,
- une **base modulaire** pour intégrer des alertes, des indicateurs techniques ou de l’analyse de performance future.

#### 2. Analyse technique
Nous avons également développé une **section d’analyse technique** pour chaque cryptomonnaie, permettant :
- de récupérer les données de prix en by-passant l’API Yahoo Finance en utilisant un user-agent personnalisé,
- de visualiser les tendances et les signaux d’achat/vente adaptative en fonction de la timeframe.
- de centraliser les indicateurs techniques à analyser (Moyennes Mobiles, RSI, MACD, etc.) et d'en dégager des signaux positifs ou négatifs.
- de recenser les actualités pertinentes et d’analyser le sentiment du marché via l’API NewsAPI et un modèle de **sentiment analysis** NLP BERT fine-tuné.

#### 3. Alertes personnalisées
Enfin, nous avons mis en place une **section d’alertes personnalisées**, permettant:
- d'être averti en cas d'opportunité d'achat ou de vente selon des stratégies définies.
- d'éviter de devoir surveiller constamment les marchés.
- à terme, de pouvoir sélectionner des stratégies de trading automatisées et d'être notifié en conséquence.

-------------- 
### Conclusion
Notre objectif était d'appliquer les concepts et technologies vus cette année.\n
En passant, par la gestion d'API, le traitement de données financières jusqu'à l'automatisation de stratégies,
nous avons cherché à fournir un outil complet et accessible pour les investisseurs, en alliant **technique, sécurité et accessibilité** au service de l'investissement.


""")

