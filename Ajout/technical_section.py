import streamlit as st
from Ajout.indicators import TechnicalAnalyzer

def afficher_indicateurs(ticker: str, period: str = "1y", interval: str = "1d"):
    st.markdown("## 🔍 Analyse Technique")

    with st.expander("Afficher l'analyse technique", expanded=True):
        analyzer = TechnicalAnalyzer()
        df = analyzer.get_data(ticker, period=period, interval=interval)  # 👈 Ajoute interval ici

        if df is not None:
            df_indic = analyzer.add_indicators(df)

            st.markdown("### 🧠 Interprétation")
            interpretations = analyzer.interpret_indicators(df_indic)
            for k, v in interpretations.items():
                st.markdown(f"- **{k}** : {v}")

            st.markdown("### 📍 Signaux")
            signals = analyzer.generate_signals(df_indic)
            analyzer.display_signals(signals)  # ✅ Utilise la méthode colorée

        else:
            st.warning("⚠️ Impossible de charger les données techniques.")
