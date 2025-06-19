import yfinance as yf
import requests
import ta
import pandas as pd
import numpy as np
import streamlit as st
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_valid_yahoo_data(data):
    try:
        _ = data["chart"]["result"][0]["timestamp"]
        return True
    except Exception:
        return False


class TechnicalAnalyzer:
    """Classe pour l'analyse technique des actifs financiers"""

    def __init__(self, rsi_overbought: int = 70, rsi_oversold: int = 30,
                 sma_periods: tuple = (20, 50, 200), bollinger_period: int = 20):
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.sma_periods = sma_periods
        self.bollinger_period = bollinger_period

    def fetch_yahoo_crypto_ohlc(self, ticker: str, range_: str = "1y", interval: str = "1d") -> Optional[pd.DataFrame]:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={range_}&interval={interval}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)
        
        if r.status_code != 200:
            return None

        data = r.json()
        if not is_valid_yahoo_data(data):
            return None

        try:
            timestamps = data["chart"]["result"][0]["timestamp"]
            ohlc = data["chart"]["result"][0]["indicators"]["quote"][0]
            df = pd.DataFrame(ohlc, index=pd.to_datetime(timestamps, unit="s", utc=True))
            df.dropna(inplace=True)
            return df
        except Exception:
            return None


    def get_data(self, ticker: str, period: str = "6mo", interval: str = "1d") -> Optional[pd.DataFrame]:
        logger.info(f"Téléchargement des données pour {ticker} via Yahoo avec {period}, intervalle {interval}")
        df = self.fetch_yahoo_crypto_ohlc(ticker, range_=period, interval=interval)
        if df is None or df.empty:
            return None

        min_required = max(self.sma_periods) + 50
        if len(df) < min_required:
            st.warning(f"⚠️ Données insuffisantes pour {ticker} ({len(df)} points). Minimum requis: {min_required}")
            return None

        logger.info(f"Données récupérées avec succès: {len(df)} points")
        return df

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            df_copy = df.copy()
            df_copy['Close'] = df_copy['close']
            df_copy['High'] = df_copy['high']
            df_copy['Low'] = df_copy['low']
            df_copy['Volume'] = df_copy['volume']

            for period in self.sma_periods:
                if len(df_copy) >= period:
                    df_copy[f'SMA{period}'] = df_copy['Close'].rolling(period).mean()

            if len(df_copy) >= self.bollinger_period:
                bb = ta.volatility.BollingerBands(close=df_copy['Close'], window=self.bollinger_period, window_dev=2)
                df_copy['Bollinger_High'] = bb.bollinger_hband()
                df_copy['Bollinger_Low'] = bb.bollinger_lband()
                df_copy['Bollinger_Mid'] = bb.bollinger_mavg()

            if len(df_copy) >= 14:
                df_copy['RSI'] = ta.momentum.RSIIndicator(close=df_copy['Close']).rsi()

            if len(df_copy) >= 26:
                macd = ta.trend.MACD(close=df_copy['Close'])
                df_copy['MACD'] = macd.macd()
                df_copy['MACD_Signal'] = macd.macd_signal()
                df_copy['MACD_Histogram'] = macd.macd_diff()

            if len(df_copy) >= 14:
                stoch = ta.momentum.StochasticOscillator(
                    high=df_copy['High'], low=df_copy['Low'], close=df_copy['Close']
                )
                df_copy['Stoch_K'] = stoch.stoch()
                df_copy['Stoch_D'] = stoch.stoch_signal()

            if len(df_copy) >= 14:
                df_copy['ATR'] = ta.volatility.AverageTrueRange(
                    high=df_copy['High'], low=df_copy['Low'], close=df_copy['Close']
                ).average_true_range()

            if 'Volume' in df_copy.columns and len(df_copy) >= 20:
                df_copy['Volume_SMA20'] = df_copy['Volume'].rolling(20).mean()

            logger.info("Indicateurs techniques calculés avec succès")
            return df_copy
        except Exception as e:
            logger.error(f"Erreur calcul indicateurs: {e}")
            st.error(f"❌ Erreur calcul indicateurs: {str(e)}")
            return df


    def display_signals(self, signals: Dict[str, str]):
        """
        Affiche les signaux avec couleurs (vert pour acheter, rouge pour vendre, bleu pour confirmer)
        """
        for key, value in signals.items():
            color = None
            if 'Acheter' in value:
                color = 'green'
            elif 'Vendre' in value:
                color = 'red'
            elif 'Confirme' in value:
                color = 'blue'
            elif 'Neutre' in value:
                color = 'gray'

            if color:
                st.markdown(f"**{key}** : <span style='color:{color}'>{value}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"**{key}** : {value}", unsafe_allow_html=True)


    def interpret_indicators(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Interprète les indicateurs techniques avec des messages lisibles
        
        Args:
            df: DataFrame avec les indicateurs calculés
            
        Returns:
            Dictionnaire avec les interprétations
        """
        if df.empty:
            return {"Erreur": "Aucune donnée disponible"}
        
        try:
            last = df.iloc[-1]
            interpretations = {}
            
            # RSI
            if 'RSI' in df.columns and pd.notna(last['RSI']):
                rsi = last['RSI']
                if rsi > self.rsi_overbought:
                    interpretations['RSI'] = f"RSI = {rsi:.1f} ➜ Surachat ⚠️ (possible correction)"
                elif rsi < self.rsi_oversold:
                    interpretations['RSI'] = f"RSI = {rsi:.1f} ➜ Survente 📈 (possible rebond)"
                else:
                    interpretations['RSI'] = f"RSI = {rsi:.1f} ➜ Zone neutre 🔄"
            
            # MACD
            if all(col in df.columns for col in ['MACD', 'MACD_Signal']) and \
               pd.notna(last['MACD']) and pd.notna(last['MACD_Signal']):
                macd = last['MACD']
                signal = last['MACD_Signal']
                diff = macd - signal
                
                if diff > 0.01:  # Seuil pour éviter le bruit
                    interpretations['MACD'] = f"MACD = {macd:.3f} > Signal = {signal:.3f} ➜ Tendance haussière ✅"
                elif diff < -0.01:
                    interpretations['MACD'] = f"MACD = {macd:.3f} < Signal = {signal:.3f} ➜ Tendance baissière ❌"
                else:
                    interpretations['MACD'] = f"MACD ≈ Signal ➜ Indécision 🤔"
            
            # Bandes de Bollinger
            if all(col in df.columns for col in ['Bollinger_High', 'Bollinger_Low']) and \
               pd.notna(last['Bollinger_High']) and pd.notna(last['Bollinger_Low']):
                close = last['Close']
                upper = last['Bollinger_High']
                lower = last['Bollinger_Low']
                
                if close > upper:
                    interpretations['Bollinger'] = f"Prix ({close:.2f}) > Bande sup. ➜ Surachat 🔴"
                elif close < lower:
                    interpretations['Bollinger'] = f"Prix ({close:.2f}) < Bande inf. ➜ Survente 🟢"
                else:
                    middle_pos = (close - lower) / (upper - lower) * 100
                    interpretations['Bollinger'] = f"Prix dans les bandes ({middle_pos:.0f}%) ➜ Volatilité normale 🔵"
            
            # Stochastique
            if all(col in df.columns for col in ['Stoch_K', 'Stoch_D']) and \
               pd.notna(last['Stoch_K']) and pd.notna(last['Stoch_D']):
                stoch_k = last['Stoch_K']
                stoch_d = last['Stoch_D']
                
                if stoch_k > 80 and stoch_d > 80:
                    interpretations['Stochastique'] = f"Stoch K={stoch_k:.1f}, D={stoch_d:.1f} ➜ Surachat ⚠️"
                elif stoch_k < 20 and stoch_d < 20:
                    interpretations['Stochastique'] = f"Stoch K={stoch_k:.1f}, D={stoch_d:.1f} ➜ Survente 📈"
                else:
                    interpretations['Stochastique'] = f"Stoch K={stoch_k:.1f}, D={stoch_d:.1f} ➜ Zone neutre 🔄"
            
            # Analyse du volume (si disponible)
            if 'Volume' in df.columns and 'Volume_SMA20' in df.columns and \
               pd.notna(last['Volume']) and pd.notna(last['Volume_SMA20']):
                volume_ratio = last['Volume'] / last['Volume_SMA20']
                if volume_ratio > 1.5:
                    interpretations['Volume'] = f"Volume élevé ({volume_ratio:.1f}x la moyenne) ➜ Fort intérêt 📊"
                elif volume_ratio < 0.5:
                    interpretations['Volume'] = f"Volume faible ({volume_ratio:.1f}x la moyenne) ➜ Peu d'intérêt 📉"
                else:
                    interpretations['Volume'] = f"Volume normal ({volume_ratio:.1f}x la moyenne) ➜ Activité standard 📈"
            
            return interpretations
            
        except Exception as e:
            logger.error(f"Erreur lors de l'interprétation: {e}")
            return {"Erreur": f"Erreur lors de l'interprétation: {str(e)}"}

    def generate_signals(self, df: pd.DataFrame, weights: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Génère des signaux d'achat/vente avec système de pondération
        
        Args:
            df: DataFrame avec les indicateurs
            weights: Poids des différents indicateurs (optionnel)
            
        Returns:
            Dictionnaire avec les signaux et la recommandation globale
        """
        if df.empty:
            return {"Erreur": "Aucune donnée disponible"}
        
        # Poids par défaut
        if weights is None:
            weights = {
                'RSI': 1.0,
                'MACD': 1.2,  # Légèrement plus important
                'Bollinger': 0.8,
                'Stochastique': 0.6,
                'Volume': 0.4
            }
        
        try:
            last = df.iloc[-1]
            signals = {}
            weighted_score = 0
            total_weight = 0
            
            # Signal RSI
            if 'RSI' in df.columns and pd.notna(last['RSI']):
                rsi = last['RSI']
                if rsi > self.rsi_overbought:
                    signals['RSI'] = 'Vendre'
                    weighted_score -= weights['RSI']
                elif rsi < self.rsi_oversold:
                    signals['RSI'] = 'Acheter'
                    weighted_score += weights['RSI']
                else:
                    signals['RSI'] = 'Attendre'
                total_weight += weights['RSI']
            
            # Signal MACD
            if all(col in df.columns for col in ['MACD', 'MACD_Signal']) and \
               pd.notna(last['MACD']) and pd.notna(last['MACD_Signal']):
                macd_diff = last['MACD'] - last['MACD_Signal']
                if macd_diff > 0.01:
                    signals['MACD'] = 'Acheter'
                    weighted_score += weights['MACD']
                elif macd_diff < -0.01:
                    signals['MACD'] = 'Vendre'
                    weighted_score -= weights['MACD']
                else:
                    signals['MACD'] = 'Attendre'
                total_weight += weights['MACD']
            
            # Signal Bollinger
            if all(col in df.columns for col in ['Bollinger_High', 'Bollinger_Low']) and \
               pd.notna(last['Bollinger_High']) and pd.notna(last['Bollinger_Low']):
                price = last['Close']
                if price > last['Bollinger_High']:
                    signals['Bollinger'] = 'Vendre'
                    weighted_score -= weights['Bollinger']
                elif price < last['Bollinger_Low']:
                    signals['Bollinger'] = 'Acheter'
                    weighted_score += weights['Bollinger']
                else:
                    signals['Bollinger'] = 'Attendre'
                total_weight += weights['Bollinger']
            
            # Signal Stochastique
            if all(col in df.columns for col in ['Stoch_K', 'Stoch_D']) and \
               pd.notna(last['Stoch_K']) and pd.notna(last['Stoch_D']):
                stoch_k = last['Stoch_K']
                stoch_d = last['Stoch_D']
                if stoch_k > 80 and stoch_d > 80:
                    signals['Stochastique'] = 'Vendre'
                    weighted_score -= weights['Stochastique']
                elif stoch_k < 20 and stoch_d < 20:
                    signals['Stochastique'] = 'Acheter'
                    weighted_score += weights['Stochastique']
                else:
                    signals['Stochastique'] = 'Attendre'
                total_weight += weights['Stochastique']
            
            # Signal Volume
            if 'Volume' in df.columns and 'Volume_SMA20' in df.columns and \
               pd.notna(last['Volume']) and pd.notna(last['Volume_SMA20']):
                volume_ratio = last['Volume'] / last['Volume_SMA20']
                if volume_ratio > 1.5:
                    # Volume élevé confirme la tendance
                    if weighted_score > 0:
                        weighted_score += weights['Volume'] * 0.5
                    elif weighted_score < 0:
                        weighted_score -= weights['Volume'] * 0.5
                    signals['Volume'] = 'Confirme la tendance'
                else:
                    signals['Volume'] = 'Neutre'
                total_weight += weights['Volume']
            
            # Recommandation globale avec score pondéré
            if total_weight > 0:
                normalized_score = weighted_score / total_weight
                
                if normalized_score > 0.3:
                    recommendation = 'Acheter ✅'
                    confidence = min(abs(normalized_score) * 100, 100)
                elif normalized_score < -0.3:
                    recommendation = 'Vendre ❌'
                    confidence = min(abs(normalized_score) * 100, 100)
                else:
                    recommendation = 'Attendre 🕒'
                    confidence = 100 - min(abs(normalized_score) * 100, 100)
                
                signals['Recommandation'] = recommendation
                signals['Confiance'] = f"{confidence:.0f}%"
                signals['Score'] = f"{normalized_score:.2f}"
            else:
                signals['Recommandation'] = 'Données insuffisantes'
                signals['Confiance'] = '0%'
                signals['Score'] = '0.00'
            
            # Timestamp de l'analyse
            signals['Analyse_le'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return signals
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des signaux: {e}")
            return {"Erreur": f"Erreur lors de la génération des signaux: {str(e)}"}

    def export_analysis(self, df: pd.DataFrame, ticker: str) -> Dict[str, Any]:
        """
        Prépare les données pour l'export (Excel, CSV, etc.)
        
        Args:
            df: DataFrame avec les indicateurs
            ticker: Symbole de l'actif
            
        Returns:
            Dictionnaire avec toutes les données d'analyse
        """
        try:
            analysis = {
                'ticker': ticker,
                'date_analysis': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'data_points': len(df),
                'period_start': df.index[0].strftime("%Y-%m-%d"),
                'period_end': df.index[-1].strftime("%Y-%m-%d"),
                'current_price': df['Close'].iloc[-1],
                'interpretations': self.interpret_indicators(df),
                'signals': self.generate_signals(df),
                'price_change_pct': ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100,
                'volatility': df['Close'].pct_change().std() * 100,
                'volume_avg': df['Volume'].mean() if 'Volume' in df.columns else None
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export: {e}")
            return {"Erreur": f"Erreur lors de l'export: {str(e)}"}


# Fonctions d'utilité pour la compatibilité avec l'ancien code
def get_data(ticker: str, period: str = "6mo", interval: str = "1d") -> Optional[pd.DataFrame]:
    analyzer = TechnicalAnalyzer()
    return analyzer.get_data(ticker, period, interval)

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    analyzer = TechnicalAnalyzer()
    return analyzer.add_indicators(df)

def interpret_indicators(df: pd.DataFrame) -> Dict[str, str]:
    """Fonction wrapper pour compatibilité"""
    analyzer = TechnicalAnalyzer()
    return analyzer.interpret_indicators(df)

def generate_signals(df: pd.DataFrame) -> Dict[str, Any]:
    """Fonction wrapper pour compatibilité"""
    analyzer = TechnicalAnalyzer()
    return analyzer.generate_signals(df)


# # Exemple d'utilisation
# if __name__ == "__main__":
#     # Créer un analyseur avec paramètres personnalisés
#     analyzer = TechnicalAnalyzer(rsi_overbought=75, rsi_oversold=25)
    
#     # Analyser un actif
#     ticker = "AAPL"
#     df = analyzer.get_data(ticker, "6mo")
    
#     if df is not None:
#         df_with_indicators = analyzer.add_indicators(df)
#         interpretations = analyzer.interpret_indicators(df_with_indicators)
#         signals = analyzer.generate_signals(df_with_indicators)
        
#         print(f"Analyse pour {ticker}:")
#         print("\nInterprétations:")
#         for key, value in interpretations.items():
#             print(f"  {key}: {value}")
        
#         print("\nSignaux:")
#         for key, value in signals.items():
#             print(f"  {key}: {value}")