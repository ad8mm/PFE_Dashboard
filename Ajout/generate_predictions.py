import yfinance as yf
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import mean_squared_error
from data_preparer import prepare_data

def generate_predictions(ticker="AAPL",
                         start_date="2017-01-01",
                         end_date="2024-01-01",
                         model_path="model_rf.pkl",
                         sequence_length=60,
                         output_csv="predictions_rf.csv"):

    # 1. Télécharger les données
    df = yf.download(ticker, start=start_date, end=end_date)[["Close"]].dropna()

    # 2. Préparer les données
    result = prepare_data(df, "Close", sequence_length)
    X_test = result["X_test"].reshape(result["X_test"].shape[0], -1)  # flatten
    y_test = result["y_test"]
    scaler = result["scaler"]

    # 3. Charger le modèle
    model = joblib.load(model_path)

    # 4. Prédire
    y_pred_scaled = model.predict(X_test)
    y_pred = scaler.inverse_transform(y_pred_scaled.reshape(-1, 1))
    y_test_real = scaler.inverse_transform(y_test)

    # 5. Sauvegarder le résultat
    aligned_dates = df.index[-len(y_test_real):]
    result_df = pd.DataFrame({
        "Date": aligned_dates,
        "Real": y_test_real.flatten(),
        "Predicted": y_pred.flatten()
    })

    result_df.to_csv(output_csv, index=False)
    rmse = np.sqrt(mean_squared_error(y_test_real, y_pred))
    print(f"✅ Prédictions sauvegardées dans {output_csv} | RMSE: {rmse:.4f}")

    return result_df

# Exemple d'exécution
if __name__ == "__main__":
    generate_predictions()
