import yfinance as yf
import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model
from data_preparer import prepare_data

def generate_predictions(ticker: str = "AAPL",
                         start_date: str = "2017-01-01",
                         end_date: str = "2024-01-01",
                         model_path: str = "model_lstm.h5",
                         sequence_length: int = 60,
                         output_csv: str = "predictions.csv"):

    # 1. Charger les données
    df = yf.download(ticker, start=start_date, end=end_date)
    df = df[["Close"]].dropna()

    # 2. Préparer les données
    X_train, y_train, X_test, y_test, scaler = prepare_data(df, "Close", sequence_length)

    # 3. Charger le modèle
    model = load_model(model_path)

    # 4. Prédire
    y_pred_scaled = model.predict(X_test)

    # 5. Dé-normaliser
    y_pred = scaler.inverse_transform(y_pred_scaled)
    y_test_real = scaler.inverse_transform(y_test)

    # 6. Récupérer les dates alignées avec les y_test
    aligned_dates = df.index[-len(y_test_real):]

    # 7. Sauver dans un CSV
    result = pd.DataFrame({
        "Date": aligned_dates,
        "Real": y_test_real.flatten(),
        "Predicted": y_pred.flatten()
    })
    result.to_csv(output_csv, index=False)
    print(f"✅ Fichier '{output_csv}' généré avec {len(result)} lignes.")

# Exemple d'utilisation
if __name__ == "__main__":
    generate_predictions()
