from crypto.caesar import encrypt
from crypto.bruteforce import brute_force_caesar
from crypto.scoring import extract_features, load_wordlist, load_ngrams
from crypto.frequency import decrypt_with_frequency
import joblib

# --- Charger le modèle ML ---
res = joblib.load('tools/caesar_model.joblib')
clf = res['model']
scaler = res['scaler']

# --- Charger les ressources NLP ---
resources = {
    "stopwords": load_wordlist("data/stopwords_en.txt"),
    "vocab": load_wordlist("data/words_en.txt"),
    "bigrams": load_ngrams("data/sample_plain.txt", 2),
    "trigrams": load_ngrams("data/sample_plain.txt", 3),
}

# --- Exemple de plaintext et chiffrement ---
plaintext = "This is a secret message for testing the pipeline"
key = 7
ciphertext = encrypt(plaintext, key)

print("Ciphertext:", ciphertext)

# --- Analyse fréquentielle ---
freq_plain, freq_key = decrypt_with_frequency(ciphertext)
print("\nFrequency Analysis:")
print("Predicted key:", freq_key)
print("Decrypted text:", freq_plain)

# --- Pipeline ML ---
candidates = brute_force_caesar(ciphertext)
scores = []

for k, cand in candidates:
    feats = extract_features(cand, resources)
    prob = clf.predict_proba([scaler.transform([feats])[0]])[0][1]
    scores.append((k, cand, prob))

# tri par score décroissant
scores.sort(key=lambda x: x[2], reverse=True)

print("\nTop 5 candidates ML:")
for i, (k, cand, prob) in enumerate(scores[:5], 1):
    print(f"[{i}] key={k}, score={prob:.2f} -> {cand}")
