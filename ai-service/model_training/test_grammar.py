import joblib

def main():
    print("Loading Models and TF-IDF Vectorizer...\n")
    tfidf = joblib.load('tfidf_vectorizer.joblib')
    xgb_cat = joblib.load('xgb_category_model.joblib')
    nb_cat = joblib.load('nb_category_model.joblib')
    le_cat = joblib.load('label_encoder_category.joblib')
    
    # List of entirely NEW misspellings that the model has NEVER seen in training
    test_complaints = [
        # Should be Theft/Burglary
        "sumone brak my hous window and steal mobile phone.",
        
        # Should be Family Dispute
        "husbnd drink alcohol and fight with waif.",
        
        # Should be Traffic
        "bus drivr speeding and smash my vechicle back.",
        
        # Should be Assault
        "he punch me with iron rod, head cut.",
        
        # Should be Fraud
        "i pay cash for visa but guy disapear."
    ]
    
    print("Testing Grammatically Incorrect Complaints:\n")
    print("-" * 60)
    
    for text in test_complaints:
        # Transform the text using the trained TF-IDF vocabulary
        vec = tfidf.transform([text])
        
        # Predict the category
        pred_xgb = xgb_cat.predict(vec)
        cat_xgb = le_cat.inverse_transform(pred_xgb)[0]
        
        pred_nb = nb_cat.predict(vec)
        cat_nb = le_cat.inverse_transform(pred_nb)[0]
        
        print(f"Messy Text: '{text}'")
        print(f"XGBoost Prediction:     {cat_xgb}")
        print(f"Naive Bayes Prediction: {cat_nb}")
        print("-" * 60)

if __name__ == "__main__":
    main()
