import requests
import spacy
from spacy.matcher import PhraseMatcher
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.svm import SVC

def fetch_api_data():
    url = "http://localhost:5000/api/result"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch data")
        return None

# Load spaCy model
nlp = spacy.load("en_core_web_sm")
matcher = PhraseMatcher(nlp.vocab)

SYMPTOM_KEYWORDS = [
    "bleeding", "fracture", "wound", "limping", "shivering", 
    "vomiting", "injury", "burn", "pus", "weakness", "cough", "blood"
]
patterns = [nlp(text) for text in SYMPTOM_KEYWORDS]
matcher.add("SYMPTOMS", patterns)

def extract_entities(text):
    doc = nlp(text)
    symptoms = []
    location = None

    matches = matcher(doc)
    for match_id, start, end in matches:
        symptoms.append(doc[start:end].text)
    
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"]:
            location = ent.text
    
    return {"symptoms": list(set(symptoms)), "location": location}

# Train SVM classifier
X_train = [
    "profuse bleeding, unconscious",  
    "broken leg, limping",  
    "shivering, minor wound",  
    "healthy, walking normally",  
]
y_train = ["HIGH", "MEDIUM", "MEDIUM", "LOW"]

vectorizer = CountVectorizer()
X_train_vectors = vectorizer.fit_transform(X_train)
clf = SVC(kernel="linear")
clf.fit(X_train_vectors, y_train)

def predict_urgency(text):
    X_test_vector = vectorizer.transform([text])
    return clf.predict(X_test_vector)[0]

def generate_whatsapp_report(data, entities, urgency):
    case_id = f"SH-20250308-{str(data['case_id']).zfill(5)}"
    image_url = f"[View Reported Case]({data['image_path']})"
    
    symptoms_text = ", ".join(entities["symptoms"]) if entities["symptoms"] else "No visible injury"
    location_text = entities["location"] if entities["location"] else "(Location not provided)"

    report = f"""
📢 *Urgent Stray Animal Assistance Required!*

🆔 *Case ID:* {case_id}
📍 *Location:* {location_text}
🖼 *Image:* {image_url}
🔍 *Detection:* {data['prediction']} ({symptoms_text})
⚠ *Urgency Level:* {urgency} (Review needed)

🚀 *Action Required:* Please review the case and initiate rescue intervention.
📞 *Contact Person (If Available):* Sanket Suryawanshi (+91XXXXXXXXXX)

🔗 [Update Case Status Here](NGO Dashboard)

This message was auto-generated by *Stray Help* – A Technology-Driven Platform for Stray Animal Welfare.
    """
    return report.strip()

# Main execution
data = fetch_api_data()
if data:
    entities = extract_entities(data['user_input'])
    urgency = predict_urgency(data['user_input'])
    final_report = generate_whatsapp_report(data, entities, urgency)
    print(final_report)
