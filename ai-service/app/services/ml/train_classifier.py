import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# ── Dataset ──────────────────────────────────────────────────────────────────
# A representative dataset of complaint descriptions and their categories
data = [
    # Theft
    ("My laptop was stolen from my car while I was at the mall.", "Theft"),
    ("Someone picked my pocket on the bus and took my wallet.", "Theft"),
    ("My bicycle was missing from the front porch this morning.", "Theft"),
    ("I noticed my jewelry was gone after the house cleaners left.", "Theft"),
    ("Shop lifter caught stealing electronics from the store.", "Theft"),
    
    # Assault
    ("I was attacked by two men while walking home last night.", "Assault"),
    ("A man punched me in the face during an argument at the bar.", "Assault"),
    ("There was a physical fight and someone was badly injured.", "Assault"),
    ("I saw someone being beaten up in the parking lot.", "Assault"),
    ("Victim was kicked and slapped repeatedly by the suspect.", "Assault"),
    
    # Narcotics
    ("I suspect my neighbors are selling drugs from their apartment.", "Narcotics"),
    ("Found a bag of white powder and syringes in the park.", "Narcotics"),
    ("Observed a suspicious hand-to-hand transaction of pills.", "Narcotics"),
    ("Smell of marijuana coming from the house next door constantly.", "Narcotics"),
    ("Arrested a person for possession of heroin and crystal meth.", "Narcotics"),
    
    # Traffic
    ("Two cars collided at the intersection of Main and 5th.", "Traffic"),
    ("A reckless driver hit my parked car and drove away.", "Traffic"),
    ("Motorcycle accident on the highway causing a major jam.", "Traffic"),
    ("I want to report a drunk driver swerving across lanes.", "Traffic"),
    ("Vehicle hit a pedestrian near the school crossing.", "Traffic"),
    
    # Domestic Violence
    ("I can hear my neighbor screaming and things breaking next door.", "Domestic Violence"),
    ("My husband hit me and threatened to kill me.", "Domestic Violence"),
    ("Report of a domestic disturbance involving a physical dispute.", "Domestic Violence"),
    ("The victim has bruises on her arms from a family member.", "Domestic Violence"),
    ("Restraining order violation: the ex-partner is at the house.", "Domestic Violence"),
    
    # Suspicious Activity
    ("A person in a hoodie has been loitering near the bank for hours.", "Suspicious Activity"),
    ("Saw someone looking into car windows with a flashlight.", "Suspicious Activity"),
    ("Unattended bag left at the train station platform.", "Suspicious Activity"),
    ("Group of individuals taking photos of the power plant fence.", "Suspicious Activity"),
    ("Drone flying very low over private property at night.", "Suspicious Activity"),
]

def train_model():
    print("Starting ML Model Training...")
    
    # Convert to DataFrame
    df = pd.DataFrame(data, columns=['text', 'category'])
    
    # ── Preprocessing ────────────────────────────────────────────────────────
    print("Preprocessing text using TF-IDF...")
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
    X = vectorizer.fit_transform(df['text'])
    y = df['category']
    
    # ── Split Data ───────────────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # ── Train Model ──────────────────────────────────────────────────────────
    print("Training Logistic Regression model...")
    model = LogisticRegression(max_iter=1000, multi_class='multinomial')
    model.fit(X_train, y_train)
    
    # ── Evaluation ───────────────────────────────────────────────────────────
    y_pred = model.predict(X_test)
    print("\nModel Evaluation:")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}")
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # ── Save Model ───────────────────────────────────────────────────────────
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    model_path = os.path.join(assets_dir, "classifier_model.joblib")
    vec_path = os.path.join(assets_dir, "vectorizer.joblib")
    
    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vec_path)
    
    print(f"\nModel saved to: {model_path}")
    print(f"Vectorizer saved to: {vec_path}")

if __name__ == "__main__":
    train_model()
