import pandas as pd
import numpy as np
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
from scipy.signal import argrelextrema

# Simule un prix
dates = pd.date_range(start="2025-06-01", periods=25000, freq='h')
np.random.seed(42)
price = np.cumsum(np.random.randn(25000) * 1.5) + 100
df = pd.DataFrame(data={'Close': price}, index=dates)
df["Open"] = df["Close"].shift(1).bfill()

# Bollinger Bands
bb = BollingerBands(close=df["Close"], window=20, window_dev=2)
df["bb_upper"] = bb.bollinger_hband()
df["bb_lower"] = bb.bollinger_lband()
df["bb_middle"] = bb.bollinger_mavg()

# Conditions de réintégration
df["bulle_sup"] = (df["Open"] > df["bb_upper"]) & (df["Close"] > df["bb_upper"])
df["bulle_inf"] = (df["Open"] < df["bb_lower"]) & (df["Close"] < df["bb_lower"])

df["reintegration_sup"] = (
    (df["bulle_sup"].shift(1)) &
    (df["Open"] < df["bb_upper"]) &
    (df["Close"] < df["bb_upper"])
)

df["reintegration_inf"] = (
    (df["bulle_inf"].shift(1)) &
    (df["Open"] > df["bb_lower"]) &
    (df["Close"] > df["bb_lower"])
)

# Backtest Bollinger
n_future = 30
success_boll, total_boll = 0, 0
for idx in df.index[df["reintegration_sup"] | df["reintegration_inf"]]:
    target = df.loc[idx, "bb_middle"]
    future_prices = df.loc[idx:].iloc[1:n_future+1]["Close"]
    touched = (future_prices - target).abs().min() <= target * 0.005  # ±0.5% de tolérance
    if touched:
        success_boll += 1
    total_boll += 1

# === RSI Divergences ===

# RSI calculation
df["RSI"] = RSIIndicator(close=df["Close"], window=14).rsi()

# Local minima
order = 5
local_min_idx = argrelextrema(df["Close"].values, np.less_equal, order=order)[0]

# Divergences haussières (ta logique)
divergences = []
for i in range(1, len(local_min_idx)):
    prev_idx, curr_idx = local_min_idx[i - 1], local_min_idx[i]
    if curr_idx - prev_idx < 4:
        continue
    if df["Close"].iloc[curr_idx] < df["Close"].iloc[prev_idx] and df["RSI"].iloc[curr_idx] > df["RSI"].iloc[prev_idx]:
        if df["RSI"].iloc[curr_idx] < 40:
            divergences.append((df.index[curr_idx], "RSI_HAUSSIERE", df["Close"].iloc[curr_idx]))

# Backtest divergences RSI
success_rsi, total_rsi = 0, 0
tp_70_hits, sl_50_hits = 0, 0

for date, typ, entry_price in divergences:
    future_rsi = df.loc[date:].iloc[1:30]["RSI"]
    rsi_entry = df.loc[date, "RSI"]

    # Étape 1 : comportement classique
    if any(future_rsi >= 60):
        success_rsi += 1

    # Étape 2 : on active le SL dynamique si RSI dépasse 55
    crossed_55 = np.where(future_rsi >= 55)[0]
    if len(crossed_55) > 0:
        start_idx = crossed_55[0]
        after_55_rsi = future_rsi.iloc[start_idx:]

        if any(after_55_rsi >= 70):
            tp_70_hits += 1
        elif any(after_55_rsi <= 50):
            sl_50_hits += 1

    total_rsi += 1


# Résultats finaux
if total_boll > 0:
    print(f"🎯 Bulle de bollinger : {success_boll}/{total_boll} ont touché bb_middle ({success_boll/total_boll*100:.1f}%)")
else:
    print("Aucune situation de réintégration détectée.")

if total_rsi > 0:
    print(f"🔄 Divergences RSI : {success_rsi}/{total_rsi} ont atteint RSI 60 ({success_rsi/total_rsi*100:.1f}%)")
    print(f"📈 RSI après 55 : {tp_70_hits} ont atteint RSI 70 ✅")
    print(f"📉 RSI après 55 : {sl_50_hits - tp_70_hits} sont retombés sous RSI 50 🛑")

else:
    print("Aucune divergence RSI détectée.")
