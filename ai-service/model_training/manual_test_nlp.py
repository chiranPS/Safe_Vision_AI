import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score
import joblib

def main():
    print("--- Manual NLP Evaluation Script ---")
    print("Loading dataset and splitting...")
    
    # Load the same dataset
    df = pd.read_csv("synthetic_complaints_sl.csv")
    X = df['Description'].values
    y_cat = df['Category'].values
    
    # Load the saved LabelEncoder
    le_cat = joblib.load('label_encoder_category.joblib')
    y_cat_encoded = le_cat.transform(y_cat)
    
    # Split the same way as training to get the exact test set
    _, X_test, _, y_test = train_test_split(X, y_cat_encoded, test_size=0.2, random_state=42, stratify=y_cat_encoded)
    
    print(f"Test set size: {len(X_test)} records.\n")
    
    # Load the TF-IDF Vectorizer and transform test data
    tfidf = joblib.load('tfidf_vectorizer.joblib')
    X_test_vec = tfidf.transform(X_test)
    
    # --- Test XGBoost ---
    print("Loading XGBoost Model...")
    xgb = joblib.load('xgb_category_model.joblib')
    
    print("Predicting with XGBoost...")
    y_pred_xgb = xgb.predict(X_test_vec)
    
    xgb_f1 = f1_score(y_test, y_pred_xgb, average='macro')
    xgb_prec = precision_score(y_test, y_pred_xgb, average='macro', zero_division=0)
    xgb_rec = recall_score(y_test, y_pred_xgb, average='macro')
    
    print(f"\n[XGBoost Metrics]")
    print(f"F1-Score  : {xgb_f1:.4f}")
    print(f"Precision : {xgb_prec:.4f}")
    print(f"Recall    : {xgb_rec:.4f}")
    
    # --- Test Random Forest ---
    print("\nLoading Random Forest Model...")
    rf = joblib.load('rf_category_model.joblib')
    
    print("Predicting with Random Forest...")
    y_pred_rf = rf.predict(X_test_vec)
    
    rf_f1 = f1_score(y_test, y_pred_rf, average='macro')
    rf_prec = precision_score(y_test, y_pred_rf, average='macro', zero_division=0)
    rf_rec = recall_score(y_test, y_pred_rf, average='macro')
    
    print(f"\n[Random Forest Metrics]")
    print(f"F1-Score  : {rf_f1:.4f}")
    print(f"Precision : {rf_prec:.4f}")
    print(f"Recall    : {rf_rec:.4f}")
    
    print("\nDetailed Classification Report for Random Forest:")
    print(classification_report(y_test, y_pred_rf, target_names=le_cat.classes_))
    
    # Note: If Naive Bayes got 1.0000, it's because the synthetic data templates 
    # use highly distinct vocabulary for each category without much overlap.

if __name__ == "__main__":
    main()
