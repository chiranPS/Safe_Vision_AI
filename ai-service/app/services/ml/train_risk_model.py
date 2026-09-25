import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

# ── Simulated Data Generation ────────────────────────────────────────────────
def generate_simulated_data(n_samples=500):
    categories = ["Theft", "Assault", "Narcotics", "Traffic", "Domestic Violence", "Suspicious Activity", "Homicide"]
    
    data = []
    for _ in range(n_samples):
        cat = np.random.choice(categories)
        hour = np.random.randint(0, 24)
        loc_freq = np.random.randint(1, 50) # Times this location appeared before
        
        # Base risk calculation for simulation
        risk = 0.1
        
        # Category impact
        if cat == "Homicide": risk += 0.7
        elif cat in ["Assault", "Domestic Violence"]: risk += 0.5
        elif cat == "Narcotics": risk += 0.4
        
        # Time impact (higher risk at night)
        if 22 <= hour or hour <= 4: risk += 0.2
        
        # Location frequency impact
        risk += min(loc_freq / 100, 0.2)
        
        # Noise
        risk += np.random.normal(0, 0.05)
        risk = max(0, min(1, risk))
        
        data.append({
            "category": cat,
            "hour": hour,
            "location_frequency": loc_freq,
            "risk_score": risk
        })
    
    return pd.DataFrame(data)

def train_risk_model():
    print("Starting Risk Prediction Model Training...")
    
    df = generate_simulated_data(1000)
    
    # ── Preprocessing & Pipeline ─────────────────────────────────────────────
    # We treat 'hour' and 'location_frequency' as numerical
    # We treat 'category' as categorical
    
    numeric_features = ["hour", "location_frequency"]
    categorical_features = ["category"]
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )
    
    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(n_estimators=100, random_state=42))
    ])
    
    # ── Train ────────────────────────────────────────────────────────────────
    X = df.drop("risk_score", axis=1)
    y = df["risk_score"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Random Forest Regressor...")
    pipeline.fit(X_train, y_train)
    
    score = pipeline.score(X_test, y_test)
    print(f"Model R^2 Score on test set: {score:.4f}")
    
    # ── Save ─────────────────────────────────────────────────────────────────
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    model_path = os.path.join(assets_dir, "risk_model.joblib")
    joblib.dump(pipeline, model_path)
    
    print(f"Risk model saved to: {model_path}")

if __name__ == "__main__":
    train_risk_model()
