import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

def main():
    print("="*60)
    print(" LOADING MODELS AND EVALUATION DATA ")
    print("="*60)
    
    # Load dataset
    df = pd.read_csv("synthetic_complaints_sl.csv")
    X = df['Description'].values
    y = df['Category'].values
    
    # Load Label Encoder and Vectorizer
    le = joblib.load('label_encoder_category.joblib')
    tfidf = joblib.load('tfidf_vectorizer.joblib')
    
    y_encoded = le.transform(y)
    
    # Stratified split matching nlp_pipeline_ml.py
    _, X_test, _, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    
    # Transform test features
    X_test_vec = tfidf.transform(X_test)
    
    # List of models to evaluate
    models = {
        "NAIVE BAYES CLASSIFIER": "nb_category_model.joblib",
        "RANDOM FOREST CLASSIFIER": "rf_category_model.joblib",
        "XGBOOST CLASSIFIER": "xgb_category_model.joblib"
    }
    
    for model_name, model_file in models.items():
        print("\n" + "="*60)
        print(f" {model_name} EVALUATION ")
        print("="*60)
        
        try:
            model = joblib.load(model_file)
            y_pred = model.predict(X_test_vec)
            
            # Print full scikit-learn classification report
            print(classification_report(y_test, y_pred, target_names=le.classes_, digits=4))
        except Exception as e:
            print(f"Error evaluating {model_name}: {e}")

if __name__ == "__main__":
    main()
