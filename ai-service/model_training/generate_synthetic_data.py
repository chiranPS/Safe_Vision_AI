import pandas as pd
# pyrefly: ignore [missing-import]
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()

# Configuration
NUM_RECORDS = 15000
START_DATE = datetime(2020, 1, 1)
END_DATE = datetime(2024, 12, 31)

DISTRICTS = [
    "Ampara", "Anuradhapura", "Badulla", "Batticaloa", "Colombo", 
    "Galle", "Gampaha", "Hambantota", "Jaffna", "Kalutara", 
    "Kandy", "Kegalle", "Kilinochchi", "Kurunegala", "Mannar", 
    "Matale", "Matara", "Moneragala", "Mullaitivu", "Nuwara Eliya", 
    "Polonnaruwa", "Puttalam", "Ratnapura", "Trincomalee", "Vavuniya"
]

CATEGORIES = [
    "Family Dispute", "Land/Property Dispute", "Theft/Burglary", 
    "Assault", "Traffic", "Social Conflict", "Drug Offenses", 
    "Fraud", "Child Abuse", "Missing Persons"
]

CATEGORY_WEIGHTS = [0.25, 0.15, 0.15, 0.10, 0.10, 0.08, 0.05, 0.05, 0.04, 0.03]

def get_priority(category):
    if category in ["Assault", "Child Abuse", "Missing Persons"]:
        return "High"
    elif category in ["Theft/Burglary", "Drug Offenses", "Fraud"]:
        return "Medium"
    else:
        return random.choices(["Medium", "Low"], weights=[0.4, 0.6])[0]

# --- UNIFIED PARTS OF SPEECH ---
SUBJECTS = [
    "husband", "wife", "child", "son", "daughter", "father", "neighbor", "uncle", "cousin", 
    "driver", "scammer", "thief", "addict", "police", "thug", "boys", "people", "suspect", "stranger"
]

VERBS = [
    "hit", "beat", "assaulted", "struck", "stabbed", "shouted", "argued", "scolded", "harassed",
    "stole", "robbed", "took", "snatched", "broke", "scammed", "deceived", "cheated", "promised",
    "collided", "scraped", "crashed", "fled", "disappeared", "went missing", "wandered away", "abused"
]

OBJECTS = [
    "money", "cash", "gold chain", "wallet", "laptop", "phone", "fence", "land boundary", 
    "coconut tree", "property deeds", "common path", "vehicle", "bus", "three-wheeler", "motorcycle", 
    "drugs", "kudu heroin", "kasippu liquor", "ice crystal meth", "house lock", "shop door", "water motor pump"
]

LOCATIONS_REASONS = [
    "near the road junction", "inside the house", "in the empty land plot", "near the school premises", 
    "by the river bank", "during the night shift", "at the local bazaar", "on the main highway", 
    "from the tuition class", "over land property arguments", "demanding cash for alcohol", 
    "under the influence of liquor", "after a heated verbal fight", "due to an old family grudge", 
    "without any legal permission", "trying to overtake from the left side", "after a minor road scrap"
]

CONSEQUENCES = [
    "causing bleeding head injuries", "and was admitted to base hospital ward 3", 
    "making the complainant very scared", "causing a huge public disturbance", 
    "police patrol must check this area", "now missing and phone is switched off", 
    "the children are crying and terrified", "neighbors heard loud screaming and crying", 
    "fled the scene immediately on a bike", "demanding Rs. {amount} to settle the issue",
    "causing severe damage worth Rs. {amount}", "pleased help me to do justice"
]

# --- CATEGORY-SPECIFIC PROBABILITY WEIGHTS ---
# Any word not specified for a category will default to a weight of 1.0 (baseline overlap)
WEIGHTS_PROFILES = {
    "Family Dispute": {
        "subjects": {"husband": 70, "wife": 70, "father": 40, "son": 40, "daughter": 40, "uncle": 30, "cousin": 25},
        "verbs": {"argued": 60, "shouted": 50, "harassed": 60, "scolded": 50, "hit": 30, "beat": 35},
        "objects": {"money": 40, "cash": 30, "phone": 25, "kasippu liquor": 30, "gold chain": 20},
        "locations_reasons": {"inside the house": 70, "demanding cash for alcohol": 60, "due to an old family grudge": 50, "under the influence of liquor": 40},
        "consequences": {"the children are crying and terrified": 70, "making the complainant very scared": 40, "pleased help me to do justice": 30}
    },
    "Land/Property Dispute": {
        "subjects": {"neighbor": 70, "uncle": 40, "cousin": 40, "suspect": 20},
        "verbs": {"argued": 40, "shouted": 35, "fled": 15, "took": 20, "broke": 20},
        "objects": {"land boundary": 70, "fence": 60, "coconut tree": 50, "property deeds": 65, "common path": 55},
        "locations_reasons": {"over land property arguments": 70, "without any legal permission": 50, "after a heated verbal fight": 35},
        "consequences": {"pleased help me to do justice": 50, "causing a huge public disturbance": 30, "making the complainant very scared": 30}
    },
    "Theft/Burglary": {
        "subjects": {"thief": 70, "robber": 60, "suspect": 40, "stranger": 30, "someone": 30},
        "verbs": {"stole": 70, "robbed": 60, "snatched": 50, "broke": 45, "took": 40, "fled": 35},
        "objects": {"laptop": 60, "gold chain": 60, "cash": 50, "money": 40, "motorcycle": 45, "wallet": 50, "house lock": 40, "shop door": 40, "water motor pump": 35},
        "locations_reasons": {"during the night shift": 70, "from the tuition class": 20, "near the road junction": 25},
        "consequences": {"fled the scene immediately on a bike": 60, "causing severe damage worth Rs. {amount}": 50, "now missing and phone is switched off": 30}
    },
    "Assault": {
        "subjects": {"thug": 50, "neighbor": 40, "suspect": 40, "driver": 25, "brother": 25, "addict": 25},
        "verbs": {"hit": 60, "beat": 60, "assaulted": 70, "struck": 50, "stabbed": 55, "shouted": 20},
        "objects": {"money": 20, "gold chain": 20, "fence": 20, "three-wheeler": 15},
        "locations_reasons": {"after a heated verbal fight": 60, "due to an old family grudge": 40, "after a minor road scrap": 30, "under the influence of liquor": 35},
        "consequences": {"causing bleeding head injuries": 70, "and was admitted to base hospital ward 3": 70, "making the complainant very scared": 40}
    },
    "Traffic": {
        "subjects": {"driver": 70, "bus": 40, "three-wheeler": 45, "motorcycle": 40, "suspect": 20},
        "verbs": {"collided": 70, "scraped": 60, "crashed": 65, "fled": 50, "hit": 40, "struck": 30},
        "objects": {"vehicle": 70, "bus": 60, "three-wheeler": 60, "motorcycle": 50},
        "locations_reasons": {"on the main highway": 70, "trying to overtake from the left side": 65, "after a minor road scrap": 60, "near the road junction": 40},
        "consequences": {"fled the scene immediately on a bike": 50, "causing severe damage worth Rs. {amount}": 70, "pleased help me to do justice": 30}
    },
    "Social Conflict": {
        "subjects": {"boys": 70, "youth": 65, "villagers": 60, "people": 40, "thug": 30},
        "verbs": {"shouted": 40, "argued": 40, "scolded": 40, "broke": 30, "hit": 20},
        "objects": {"kasippu liquor": 30, "three-wheeler": 20, "fence": 15},
        "locations_reasons": {"near the road junction": 60, "in the empty land plot": 45, "under the influence of liquor": 40},
        "consequences": {"causing a huge public disturbance": 70, "neighbors heard loud screaming and crying": 50, "police patrol must check this area": 50}
    },
    "Drug Offenses": {
        "subjects": {"addict": 70, "suspect": 40, "boys": 35, "stranger": 30},
        "verbs": {"stole": 20, "took": 20, "fled": 20, "harassed": 20},
        "objects": {"drugs": 70, "kudu heroin": 75, "kasippu liquor": 60, "ice crystal meth": 70},
        "locations_reasons": {"in the empty land plot": 60, "near the school premises": 60, "by the river bank": 55},
        "consequences": {"police patrol must check this area": 60, "causing a huge public disturbance": 40, "making the complainant very scared": 30}
    },
    "Fraud": {
        "subjects": {"scammer": 70, "suspect": 40, "known person": 30, "uncle": 20},
        "verbs": {"scammed": 70, "deceived": 75, "cheated": 70, "promised": 60, "took": 40},
        "objects": {"money": 60, "cash": 55, "property deeds": 35, "gold chain": 20},
        "locations_reasons": {"over land property arguments": 30, "demanding cash for alcohol": 20},
        "consequences": {"demanding Rs. {amount} to settle the issue": 70, "now missing and phone is switched off": 60, "making the complainant very scared": 40}
    },
    "Child Abuse": {
        "subjects": {"child": 70, "son": 50, "daughter": 50, "step-father": 60, "father": 40},
        "verbs": {"abused": 75, "hit": 40, "beat": 50, "harassed": 35},
        "objects": {"phone": 15, "money": 15, "drugs": 15},
        "locations_reasons": {"inside the house": 60, "near the school premises": 35, "under the influence of liquor": 40},
        "consequences": {"neighbors heard loud screaming and crying": 70, "the children are crying and terrified": 60, "and was admitted to base hospital ward 3": 30}
    },
    "Missing Persons": {
        "subjects": {"son": 50, "daughter": 50, "father": 50, "husband": 40, "child": 45},
        "verbs": {"went missing": 75, "wandered away": 70, "disappeared": 65},
        "objects": {"money": 15, "phone": 20, "motorcycle": 20},
        "locations_reasons": {"from the tuition class": 60, "at the local bazaar": 50, "during the night shift": 35},
        "consequences": {"now missing and phone is switched off": 70, "pleased help me to do justice": 50, "the children are crying and terrified": 20}
    }
}

def sample_with_weights(word_list, category, part):
    """Sample a word from a list using category-specific weights."""
    profile = WEIGHTS_PROFILES[category].get(part, {})
    
    # Generate weights: use profile weight if specified, else 1.0 (baseline overlap)
    weights = [profile.get(word, 1.0) for word in word_list]
    
    return random.choices(word_list, weights=weights)[0]

def generate_complaint_text(category):
    """Generate complaint narrative by sampling parts of speech statistically."""
    subject = sample_with_weights(SUBJECTS, category, "subjects")
    verb = sample_with_weights(VERBS, category, "verbs")
    obj = sample_with_weights(OBJECTS, category, "objects")
    loc_reason = sample_with_weights(LOCATIONS_REASONS, category, "locations_reasons")
    consequence = sample_with_weights(CONSEQUENCES, category, "consequences")
    
    # Fill in randomized amounts in consequences
    consequence = consequence.format(amount=random.randint(15000, 350000))
    
    # Generic structures to compose sentences grammatically
    struct = random.choice([1, 2, 3])
    if struct == 1:
        text = f"complainant states that {subject} {verb} {obj} {loc_reason}. {consequence}."
    elif struct == 2:
        text = f"regarding {obj}, {subject} {verb} {loc_reason} and {consequence}."
    else:
        text = f"{subject} {verb} {obj} {loc_reason}. {consequence}."
        
    return " ".join(text.split()).strip()

def random_date(start, end):
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def adjust_time_for_category(dt, category):
    hour = dt.hour
    if category in ["Theft/Burglary", "Assault"]:
        hour = random.choice(list(range(18, 24)) + list(range(0, 5)))
    elif category == "Family Dispute":
        hour = random.choice(range(17, 23))
    elif category == "Traffic":
        hour = random.choice([7, 8, 9, 16, 17, 18, 19])
    return dt.replace(hour=hour, minute=random.randint(0, 59))

def messify_text(text):
    """Inject typos, code-mixed Singlish terms, and remove filler words to simulate real officer notes."""
    if random.random() > 0.8:  # 20% clean
        return text
    
    replacements = {
        "complainant": ["complanent", "i", "me", "complainer"],
        "suspect": ["saspaet", "hora", "man", "that guy"],
        "vehicle": ["vechicle", "vehical", "van"],
        "assaulted": ["assulted", "hit", "guti dunna", "beated"],
        "intoxicated": ["drunk", "beela", "alcohol"],
        "stolen": ["steel", "hora gaththa", "robbed"],
        "motorcycle": ["bike", "motor bike", "scooter"],
        "missing": ["misng", "lost", "disapear", "not finding"],
        "hospital": ["hospitl", "ispiritale", "ward"],
        "jewelry": ["jewlery", "gold", "mala"],
        "argument": ["fight", "argment", "shouting"],
        "encroached": ["take", "alluwa"],
        "narcotics": ["kudu", "drugs", "ice"],
        "fraud": ["fake", "cheat", "boruwa"],
        "police": ["polise", "policiya", "oic mahaththaya"]
    }
    
    words = text.split()
    new_words = []
    
    for w in words:
        clean_w = w.strip(".,!?()").lower()
        if clean_w in replacements and random.random() < 0.6:
            new_words.append(random.choice(replacements[clean_w]))
        elif len(clean_w) > 4 and random.random() < 0.12:
            drop_idx = random.randint(1, len(clean_w)-2)
            typo_word = clean_w[:drop_idx] + clean_w[drop_idx+1:]
            new_words.append(typo_word)
        elif clean_w in ['the', 'a', 'an', 'to', 'is', 'was', 'and', 'of', 'in'] and random.random() < 0.45:
            continue
        else:
            new_words.append(w)
            
    if len(new_words) > 5 and random.random() < 0.35:
        idx1 = random.randint(0, len(new_words)-2)
        idx2 = idx1 + 1
        new_words[idx1], new_words[idx2] = new_words[idx2], new_words[idx1]
        
    return " ".join(new_words).lower()

def generate_data():
    print(f"Generating {NUM_RECORDS} synthetic complaint records...")
    data = []
    
    for i in range(NUM_RECORDS):
        complaint_id = f"CMP-{fake.unique.random_int(min=100000, max=999999)}"
        
        category = random.choices(CATEGORIES, weights=CATEGORY_WEIGHTS)[0]
        priority = get_priority(category)
        
        raw_date = random_date(START_DATE, END_DATE)
        incident_datetime = adjust_time_for_category(raw_date, category)
        
        date_str = incident_datetime.strftime("%Y-%m-%d")
        time_str = incident_datetime.strftime("%H:%M:%S")
        day_of_week = incident_datetime.strftime("%A")
        
        district = random.choice(DISTRICTS)
        lat = round(random.uniform(5.9, 9.8), 6)
        lon = round(random.uniform(79.5, 81.8), 6)
        
        description = generate_complaint_text(category)
        description = messify_text(description)
        
        data.append({
            "Complaint_ID": complaint_id,
            "Date": date_str,
            "Time": time_str,
            "Day_of_Week": day_of_week,
            "District": district,
            "Latitude": lat,
            "Longitude": lon,
            "Category": category,
            "Priority": priority,
            "Description": description
        })
        
        if (i+1) % 3000 == 0:
            print(f"Generated {i+1} records...")

    df = pd.DataFrame(data)
    output_path = "synthetic_complaints_sl.csv"
    df.to_csv(output_path, index=False)
    print(f"Successfully saved to {output_path}")

if __name__ == "__main__":
    generate_data()
