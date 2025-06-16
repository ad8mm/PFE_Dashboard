
---

## Prérequis

- Python **3.8+**  
- Virtualenv ou Conda  
- (optionnel) MongoDB pour la persistance  

---

## 1. Installation

1. **Cloner le dépôt**  
    ```bash
    git clone #à compléter
    cd PFE_Dashboard
    ```

2. **Créer un environnement virtuel**  
    ```bash
    python -m venv .venv
    source venv/bin/activate    # Unix/macOS
    venv\Scripts\activate       # Windows
    ```

3. **Installer les dépendances**  
    ```bash
    pip install -r requirements.txt
    ```

---

## 2. Lancer l'app

1. **Commande**
    ```bash
    streamlit run app.py
    ```