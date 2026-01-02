# crypto/scoring.py

import math
from collections import Counter
from typing import Dict, List
import re


# ---------- Utils chargement ----------

def load_wordlist(path: str) -> set:
    with open(path, encoding="utf-8") as f:
        return set(w.strip().lower() for w in f if w.strip())


def load_ngrams(path: str, n: int) -> Dict[str, float]:
    """
    Calcule les log-fréquences de n-grams à partir d'un texte propre.
    """
    with open(path, encoding="utf-8") as f:
        text = f.read().lower()

    grams = Counter(text[i:i+n] for i in range(len(text) - n + 1))
    total = sum(grams.values())

    return {
        g: math.log(c / total)
        for g, c in grams.items()
    }


# ---------- Features ----------

def stopwords_count(text: str, stopwords: set) -> int:
    """Count stopwords in text with better word extraction."""
    if not stopwords:
        return 0
    words = re.findall(r'\b[a-z\u0080-\uFFFF]+\b', text.lower())
    return sum(1 for w in words if w in stopwords)


def valid_word_ratio(text: str, vocabulary: set) -> float:
    """Calculate the ratio of valid words, with better word extraction."""
    if not vocabulary:
        return 0.0
    
    # Extract words more intelligently - remove punctuation but keep word boundaries
    # This handles cases like "hello,world" or "don't" better
    # Split on whitespace and punctuation, but keep sequences of letters
    words = re.findall(r'\b[a-z\u0080-\uFFFF]+\b', text.lower())
    
    if not words:
        return 0.0
    
    # Check each word against vocabulary
    valid = sum(1 for w in words if w in vocabulary)
    
    # Return ratio
    ratio = valid / len(words)
    
    # Bonus: if all words are valid, give a small boost
    if ratio == 1.0 and len(words) > 0:
        return min(1.0, ratio + 0.05)
    
    return ratio


def ngram_likelihood(text: str, ngrams: Dict[str, float], n: int) -> float:
    score = 0.0
    text = text.lower()
    for i in range(len(text) - n + 1):
        g = text[i:i+n]
        score += ngrams.get(g, -15.0)  # pénalité si inconnu
    return score


def character_entropy(text: str) -> float:
    counts = Counter(text)
    total = sum(counts.values())

    entropy = 0.0
    for c in counts.values():
        p = c / total
        entropy -= p * math.log2(p)

    return entropy


# ---------- Letter frequency / chi-squared ----------
ENGLISH_LETTER_FREQ = {
    'a': 0.08167, 'b': 0.01492, 'c': 0.02782, 'd': 0.04253, 'e': 0.12702,
    'f': 0.02228, 'g': 0.02015, 'h': 0.06094, 'i': 0.06966, 'j': 0.00153,
    'k': 0.00772, 'l': 0.04025, 'm': 0.02406, 'n': 0.06749, 'o': 0.07507,
    'p': 0.01929, 'q': 0.00095, 'r': 0.05987, 's': 0.06327, 't': 0.09056,
    'u': 0.02758, 'v': 0.00978, 'w': 0.02360, 'x': 0.00150, 'y': 0.01974,
    'z': 0.00074
}


FRENCH_LETTER_FREQ = {
    'a': 0.07636, 'b': 0.00901, 'c': 0.03260, 'd': 0.03669, 'e': 0.14715,
    'f': 0.01066, 'g': 0.00866, 'h': 0.00737, 'i': 0.07529, 'j': 0.00613,
    'k': 0.00049, 'l': 0.05456, 'm': 0.02968, 'n': 0.07110, 'o': 0.05796,
    'p': 0.02521, 'q': 0.01362, 'r': 0.06693, 's': 0.07948, 't': 0.07244,
    'u': 0.06311, 'v': 0.01629, 'w': 0.00074, 'x': 0.00427, 'y': 0.00128,
    'z': 0.00326
}


def detect_language_alphabet(text: str) -> str:
    """Detect which alphabet is primarily used in the text. Only supports Latin for English and French."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 'latin'
    
    # Only check for Latin alphabet (English and French)
    latin_count = sum(1 for c in letters if 'A' <= c.upper() <= 'Z')
    
    # Always return 'latin' since we only support English and French
    return 'latin'

def get_letter_frequencies_for_alphabet(alphabet: str) -> Dict[str, float]:
    """Get letter frequency distribution for a given alphabet. Only supports Latin (English/French)."""
    # Only support Latin alphabet (English and French)
    # Language-specific frequencies are handled in app.py
    return ENGLISH_LETTER_FREQ

def chi_squared_letter_score(text: str, expected: Dict[str, float] = None) -> float:
    """Compute a normalized score (0..1) where higher means closer to expected letter frequencies.

    Uses the Pearson chi-squared statistic with improved normalization.
    Automatically detects the alphabet if expected frequencies are not provided.
    """
    if expected is None:
        # Auto-detect alphabet and use appropriate frequencies
        alphabet = detect_language_alphabet(text)
        expected = get_letter_frequencies_for_alphabet(alphabet)
    
    # Count only alphabetic characters, normalize to lowercase
    letters = [c.lower() for c in text if c.isalpha()]
    n = len(letters)
    if n == 0:
        return 0.01  # Minimum score instead of 0.0

    counts = Counter(letters)

    chi2 = 0.0
    # Only calculate chi-squared for letters that appear in the text or are common
    all_letters = set(counts.keys()) | set(expected.keys())
    
    for ch in all_letters:
        observed = counts.get(ch, 0)
        exp_freq = expected.get(ch, 0.0)
        if exp_freq > 0:
            expected_count = exp_freq * n
            # Avoid division by zero
            if expected_count > 0.01:
                chi2 += (observed - expected_count) ** 2 / expected_count
            elif observed > 0:
                # Penalize unexpected letters
                chi2 += observed * 10

    # Normalize chi-squared: for n letters, expected chi2 is roughly n
    # Better normalization: use degrees of freedom (number of unique letters - 1)
    degrees_of_freedom = max(len(all_letters) - 1, 1)
    
    # Normalize chi2 by degrees of freedom, then map to 0..1
    # Good texts have chi2/df close to 1, bad texts have much higher
    if degrees_of_freedom > 0:
        normalized_chi2 = chi2 / degrees_of_freedom
    else:
        normalized_chi2 = chi2
    
    # Map to score: chi2/df = 1 -> score = 1, chi2/df = 10 -> score ≈ 0.1
    # Using exponential decay for better discrimination, but ensure minimum score
    # For very high chi2, use a more forgiving formula
    if normalized_chi2 < 1:
        score = 1.0
    elif normalized_chi2 < 50:
        # Use exponential decay but ensure it doesn't go too low
        score = math.exp(-normalized_chi2 / 10.0)
    else:
        # Very high chi2, but still give some score
        score = 1.0 / (1.0 + normalized_chi2 / 100.0)
    
    # Ensure minimum score of 0.01 to avoid rounding to 0.0
    score = max(0.01, min(1.0, score))
    
    return score

def extract_features(text: str, resources: dict):
    return [
        stopwords_count(text, resources["stopwords"]),
        valid_word_ratio(text, resources["vocab"]),
        ngram_likelihood(text, resources["bigrams"], 2),
        ngram_likelihood(text, resources["trigrams"], 3),
        character_entropy(text),
    ]



def heuristic_score(text: str, resources: dict) -> float:
    """Improved heuristic scoring that works better across languages."""
    text = text.lower()
    length = max(len(text), 1)
    words = text.split()
    word_count = len(words)

    vocab = resources.get("vocab", set())
    bigrams = resources.get("bigrams", {})
    trigrams = resources.get("trigrams", {})
    stopwords = resources.get("stopwords", set())

    # 1️⃣ Word-based features (only if vocab is available)
    vr = valid_word_ratio(text, vocab) if vocab else 0.0
    sw = stopwords_count(text, stopwords)
    sw_norm = min(sw / max(word_count, 1), 1.0) if word_count > 0 else 0.0

    # 2️⃣ N-gram likelihood (normalized by length)
    ng_norm = 0.0
    if trigrams and len(text) >= 3:
        ng = ngram_likelihood(text, trigrams, 3)
        # Normalize by number of trigrams, not total length
        num_trigrams = max(len(text) - 2, 1)
        ng_avg = ng / num_trigrams
        # Typical good text: ng_avg around -3 to -5, bad text: -10 or worse
        # Map to 0..1: -3 -> 1.0, -5 -> 0.6, -10 -> 0.1
        if ng_avg > -3:
            ng_norm = 1.0
        elif ng_avg > -10:
            ng_norm = max(0.0, 1.0 + (ng_avg + 3) / 7.0)  # Linear interpolation
        else:
            ng_norm = 0.0
    elif bigrams and len(text) >= 2:
        ng = ngram_likelihood(text, bigrams, 2)
        num_bigrams = max(len(text) - 1, 1)
        ng_avg = ng / num_bigrams
        # Similar mapping for bigrams
        if ng_avg > -2:
            ng_norm = 1.0
        elif ng_avg > -8:
            ng_norm = max(0.0, 1.0 + (ng_avg + 2) / 6.0)
        else:
            ng_norm = 0.0

    # 3️⃣ Letter frequency score (language-agnostic)
    freq_score = chi_squared_letter_score(text)

    # 4️⃣ Entropy score (natural language ≈ 3.5–4.5)
    letters_only = [c for c in text if c.isalpha()]
    if len(letters_only) > 0:
        ent = character_entropy(''.join(letters_only))
        ent_score = max(0.0, 1.0 - abs(ent - 4.0) / 2.0)
    else:
        ent_score = 0.0

    # 5️⃣ Pattern recognition: common letter patterns (English and French)
    pattern_score = 0.0
    text_lower = text.lower()
    
    # Common patterns for English and French (Latin alphabet)
    common_patterns = ['th', 'he', 'in', 'er', 'an', 're', 'ed', 'nd', 'ou', 'to', 'en', 'at', 'it', 'is', 'or', 'ti', 'as', 'of', 'st', 'le', 'de', 'et', 'la', 'un', 'es', 'nt', 'on', 'te']
    
    pattern_count = sum(1 for pattern in common_patterns if pattern in text_lower)
    # Normalize by text length (more patterns in longer text is expected)
    if length > 0:
        pattern_score = min(1.0, pattern_count / max(length / 20, 1))
    else:
        pattern_score = 0.0

    # 6️⃣ Length-aware weighting with improved logic
    is_single_word = word_count == 1
    is_short = length < 30
    
    if is_single_word:
        # For single words, prioritize frequency analysis and vocabulary
        # Frequency is most reliable for single words
        score = (
            0.50 * freq_score +
            0.30 * vr +
            0.15 * pattern_score +
            0.05 * ent_score
        )
    elif is_short:
        # Short texts: balance frequency, vocabulary, and n-grams
        score = (
            0.35 * freq_score +
            0.30 * vr +
            0.20 * ng_norm +
            0.10 * sw_norm +
            0.05 * ent_score
        )
    else:
        # Longer texts: prioritize vocabulary and n-grams (most reliable for long text)
        score = (
            0.40 * vr +
            0.30 * ng_norm +
            0.15 * freq_score +
            0.10 * sw_norm +
            0.05 * ent_score
        )
    
    # Ensure score is in valid range, with minimum of 0.01 to avoid rounding to 0
    score = min(1.0, max(0.01, score))
    return score
