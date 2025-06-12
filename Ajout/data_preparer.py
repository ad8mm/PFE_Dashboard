import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

def prepare_data(
    df: pd.DataFrame,
    feature_column: str = "Close",
    sequence_length: int = 60,
    split_ratio: float = 0.8,
    shuffle: bool = False,
    random_seed: int = None
):
    """
    Prépare les données pour l'entraînement et le test d'un modèle séquentiel.

    Args:
        df (pd.DataFrame): DataFrame contenant les données historiques.
        feature_column (str): Nom de la colonne à prédire (par défaut 'Close').
        sequence_length (int): Longueur des séquences d'entrée (default: 60).
        split_ratio (float): Proportion des données à utiliser pour l'entraînement.
        shuffle (bool): Si True, les séquences seront mélangées (désactivé pour les modèles séquentiels).
        random_seed (int): Graine pour la reproductibilité si shuffle=True.

    Returns:
        dict: Dictionnaire contenant les données prêtes à l'emploi :
            - "X_train", "y_train", "X_test", "y_test" : np.arrays
            - "scaler" : l'objet MinMaxScaler utilisé pour la normalisation
    """
    
    # Vérification de la colonne cible
    if feature_column not in df.columns:
        raise ValueError(f"La colonne '{feature_column}' n'existe pas dans le DataFrame.")

    data = df[[feature_column]].values
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(data)

    X, y = [], []
    for i in range(sequence_length, len(scaled_data)):
        X.append(scaled_data[i-sequence_length:i])
        y.append(scaled_data[i])

    X = np.array(X)
    y = np.array(y)

    # Optionnel : shuffle
    if shuffle:
        if random_seed is not None:
            np.random.seed(random_seed)
        indices = np.arange(len(X))
        np.random.shuffle(indices)
        X = X[indices]
        y = y[indices]

    # Split
    split_index = int(len(X) * split_ratio)
    X_train, X_test = X[:split_index], X[split_index:]
    y_train, y_test = y[:split_index], y[split_index:]

    return {
        "X_train": X_train,
        "y_train": y_train,
        "X_test": X_test,
        "y_test": y_test,
        "scaler": scaler
    }
