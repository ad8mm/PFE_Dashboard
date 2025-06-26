import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import argrelextrema

def compute_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# --- Données de test ---
np.random.seed(42)
dates = pd.date_range(end=pd.Timestamp.now(), periods=300000, freq='h')
prices = 100 + np.cumsum(np.random.normal(0, 1, len(dates)))
df = pd.DataFrame({'Close': prices}, index=dates)
df['RSI'] = compute_rsi(df['Close'])

# --- Détection des divergences ---
order = 5
local_min_idx = argrelextrema(df["Close"].values, np.less_equal, order=order)[0]
entries, exits, results, returns = [], [], [], []

stats = {
    "tp_rsi70": 0,
    "tp_rsi50": 0,
    "tp_prix": 0,
    "sl": 0,
    "ld_break": 0
}

capital = 100
capital_history = [capital]

for i in range(1, len(local_min_idx)):
    if capital < 10:
        break

    prev_idx, curr_idx = local_min_idx[i - 1], local_min_idx[i]
    if curr_idx - prev_idx < 4:
        continue

    price_prev = df['Close'].iloc[prev_idx]
    price_curr = df['Close'].iloc[curr_idx]
    rsi_prev = df['RSI'].iloc[prev_idx]
    rsi_curr = df['RSI'].iloc[curr_idx]

    if price_curr < price_prev and rsi_curr > rsi_prev and rsi_curr < 40:
        x1, x2 = prev_idx, curr_idx
        y1, y2 = rsi_prev, rsi_curr
        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1

        entry_idx = None
        for j in range(curr_idx + 1, len(df)):
            expected_rsi = slope * j + intercept
            real_rsi = df["RSI"].iloc[j]
            if real_rsi > expected_rsi:
                entry_idx = j
                entry_date = df.index[j]
                price_entry = df["Close"].iloc[j]
                rsi_entry = real_rsi

                points_rsi = 60 - rsi_entry
                prix_par_point_rsi = price_entry / rsi_entry if rsi_entry > 0 else 0
                price_tp = price_entry + points_rsi * prix_par_point_rsi
                sl_range = 0.5 * (price_tp - price_entry)
                r=0.25
                # price_tp = price_entry * (1 + r)      # ex: r = 0.15 (15 %)
                price_sl = price_entry * (1 - r / 2)  # perte max 7.5 % si TP = 15 %
                

                entries.append(entry_date)
                break

        if entry_idx:
            for k in range(entry_idx + 1, len(df)):
                price_k = df["Close"].iloc[k]
                rsi_k = df["RSI"].iloc[k]
                expected_rsi_k = slope * k + intercept
                date_k = df.index[k]

                if price_k <= price_sl:
                    stats['sl'] += 1
                    exits.append(date_k)
                    results.append((price_entry, price_sl))
                    ret = (price_sl - price_entry) / price_entry
                    returns.append(ret)
                    capital += 10 * ret
                    capital_history.append(capital)
                    break
                elif price_k >= price_tp:
                    stats['tp_prix'] += 1
                    exits.append(date_k)
                    results.append((price_entry, price_tp))
                    ret = (price_tp - price_entry) / price_entry
                    returns.append(ret)
                    capital += 10 * ret
                    capital_history.append(capital)
                    break
                elif rsi_k < expected_rsi_k:
                    stats['ld_break'] += 1
                    exits.append(date_k)
                    results.append((price_entry, price_k))
                    ret = (price_k - price_entry) / price_entry
                    returns.append(ret)
                    capital += 10 * ret
                    capital_history.append(capital)
                    break
                elif rsi_k > 55:
                    for l in range(k + 1, len(df)):
                        rsi_l = df["RSI"].iloc[l]
                        price_l = df["Close"].iloc[l]
                        date_l = df.index[l]
                        if rsi_l < 50:
                            stats['tp_rsi50'] += 1
                            exits.append(date_l)
                            results.append((price_entry, price_l))
                            ret = (price_l - price_entry) / price_entry
                            returns.append(ret)
                            capital += 10 * ret
                            capital_history.append(capital)
                            break
                        elif rsi_l >= 70:
                            stats['tp_rsi70'] += 1
                            exits.append(date_l)
                            results.append((price_entry, price_l))
                            ret = (price_l - price_entry) / price_entry
                            returns.append(ret)
                            capital += 10 * ret
                            capital_history.append(capital)
                            break
                    break

# --- Résumé ---
n_trades = len(returns)
avg_return = np.mean(np.array(returns) * 100) if returns else 0
total_return_pct = ((capital - 100) / 100) * 100 if n_trades > 0 else 0
gagnants = stats['tp_rsi70'] + stats['tp_rsi50'] + stats['tp_prix']
perdants = stats['sl'] + stats['ld_break']

print("🔍 Résultats de la stratégie RSI")
print(f"Nombre de trades         : {n_trades}")
print(f"Performance moyenne/trade: {avg_return:.2f} %")
print(f"Performance cumulée      : {total_return_pct:.2f} %")
print(f"Capital final            : {capital:.2f} €")
print(f"✔ TP RSI 70              : {stats['tp_rsi70']}")
print(f"✔ TP RSI 55 → 50         : {stats['tp_rsi50']}")
print(f"✔ TP prix                : {stats['tp_prix']}")
print(f"❌ Stop Loss             : {stats['sl']}")
print(f"❌ Cassure LD            : {stats['ld_break']}")
print(f"Total gagnants           : {gagnants}")
print(f"Total perdants           : {perdants}")
print("💥 Pires trades          :", sorted([round(r * 100, 2) for r in returns])[:10])
# Affichage des 10 meilleurs trades
top_trades = sorted([(i, round(10 * r, 2), round(r * 100, 2)) for i, r in enumerate(returns)], key=lambda x: x[1], reverse=True)[:10]

print("\n🏆 Meilleurs trades :")
print("Trade # | Gain (€) | Rendement (%)")
for i, gain_eur, pct in top_trades:
    print(f"{i:<8} | {gain_eur:<8} | {pct:<13}")


# --- Graphiques ---
plt.figure(figsize=(14, 6))
plt.plot(df.index, df["Close"], label="Prix", alpha=0.6)
for i, entry in enumerate(entries):
    plt.axvline(entry, color='green', linestyle='--', label="Entrée" if i == 0 else "")
for i, exit_ in enumerate(exits):
    plt.axvline(exit_, color='red', linestyle='--', label="Sortie" if i == 0 else "")
plt.title("Stratégie RSI - Entrées/Sorties")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

plt.figure(figsize=(12, 4))
plt.plot(range(len(capital_history)), capital_history, marker='o')
plt.title("Évolution du capital")
plt.xlabel("Trade #")
plt.ylabel("Capital (€)")
plt.grid(True)
plt.tight_layout()
plt.show()
