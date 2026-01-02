#!/usr/bin/env python3
"""
Simple Flask app for Caesar cipher cracking
"""
import sys
import math
from pathlib import Path
from flask import Flask, render_template, request, jsonify

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from crypto.bruteforce import brute_force_caesar
from crypto.scoring import (
    load_wordlist, load_ngrams, heuristic_score, valid_word_ratio, 
    chi_squared_letter_score, FRENCH_LETTER_FREQ, ENGLISH_LETTER_FREQ,
    detect_language_alphabet, get_letter_frequencies_for_alphabet
)
import re

app = Flask(__name__, 
            template_folder='.',
            static_folder='static',
            static_url_path='/static')

# Cache resources
CACHE = {}

def get_resources(lang='en'):
    """Get vocabulary and stopwords for language"""
    if lang in CACHE:
        return CACHE[lang]
    
    try:
        vocab = load_wordlist(f"data/words_{lang}.txt")
        stopwords = load_wordlist(f"data/stopwords_{lang}.txt")

        # build simple n-gram models from the sample plain text
        try:
            bigrams = load_ngrams('data/sample_plain.txt', 2)
            trigrams = load_ngrams('data/sample_plain.txt', 3)
        except Exception:
            bigrams = {}
            trigrams = {}

        # augment vocab with words found in the sample plain text to increase
        # chance of matching short/common words not present in the small wordlists
        try:
            with open('data/sample_plain.txt', encoding='utf-8') as sp:
                sample_words = set(w.strip().lower() for w in sp.read().split())
                # keep only alphabetic token-like words
                sample_words = set(w for w in sample_words if any(c.isalpha() for c in w))
                vocab = set(w.lower() for w in vocab) | sample_words
        except Exception:
            pass

        CACHE[lang] = {
            'vocab': vocab,
            'stopwords': stopwords,
            'bigrams': bigrams,
            'trigrams': trigrams
        }
    except Exception as e:
        print(f"Error loading resources for {lang}: {e}")
        CACHE[lang] = {'vocab': set(), 'stopwords': set()}
    
    return CACHE[lang]

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Analyze a Caesar cipher text and find the most likely decryption.
    
    Request: {"cipherText": "...", "lang": "en|fr"}
    Response: {"key": k, "plainText": "...", "score": 0.95, "candidates": [...]}
    """
    try:
        data = request.get_json() or {}
        cipher_text = data.get('cipherText', '').strip()
        lang = data.get('lang', 'en')
        
        if not cipher_text:
            return jsonify({'error': 'Empty cipher text'}), 400
        
        # Accept only English or French, default to 'en' if not recognized
        if lang not in ['en', 'fr']:
            # Auto-detect: if lang is 'auto' or not provided, default to 'en'
            if not lang or lang == 'auto':
                lang = 'en'
            else:
                lang = 'en'
        
        # Get resources (vocab + n-gram models)
        resources = get_resources(lang)
        vocab = resources.get('vocab', set())

        # Detect single-word short inputs (works for any language)
        words = cipher_text.split()
        is_single_word = len(words) == 1 and bool(re.match(r'^[\w\u0080-\uFFFF]+$', cipher_text, re.UNICODE))

        # Auto-detect alphabet from cipher text
        detected_alphabet = detect_language_alphabet(cipher_text)
        
        # Augment vocab with common words for English and French
        COMMON_WORDS = {
            'en': {'the', 'and', 'is', 'to', 'of', 'you', 'hello', 'that', 'in', 'it', 
                   'dog', 'cat', 'this', 'message', 'secret', 'word', 'text', 'code'},
            'fr': {'le', 'la', 'et', 'de', 'un', 'bonjour', 'je', 'tu', 'il', 'elle',
                   'nous', 'vous', 'message', 'secret', 'mot', 'texte', 'code'}
        }
        
        # Get appropriate common words based on language
        common_aug = COMMON_WORDS.get(lang, COMMON_WORDS['en'])
        
        if is_single_word and (not vocab or len(vocab) < 50):
            augmented_vocab = set(w.lower() for w in vocab) | common_aug
        else:
            augmented_vocab = set(w.lower() for w in vocab) | common_aug
        
        # Get appropriate letter frequencies based on language
        if lang == 'fr':
            expected_freq = FRENCH_LETTER_FREQ
        else:
            expected_freq = ENGLISH_LETTER_FREQ
        
        # Brute force all 26 shifts (including 0)
        candidates = []
        for k, plaintext in brute_force_caesar(cipher_text):
            try:
                # Compute raw scores
                h_score = heuristic_score(plaintext, resources)
                word_score = valid_word_ratio(plaintext, augmented_vocab) if augmented_vocab else 0.0

                # Language-aware letter frequency scoring
                freq_score = chi_squared_letter_score(plaintext, expected=expected_freq)
                
                # Debug: Print scores for first candidate to verify they're being calculated
                if k == 0:
                    print(f"DEBUG Key {k} - h_score: {h_score}, word_score: {word_score}, freq_score: {freq_score}")

                # Check if plaintext exactly matches a dictionary entry (case-insensitive)
                plaintext_lower = plaintext.strip().lower()
                is_dict_match = plaintext_lower in augmented_vocab

                # Improved scoring logic - combine all features intelligently
                if is_single_word:
                    if is_dict_match:
                        # Exact dictionary match gets highest score, but still consider frequency
                        # to distinguish between multiple dictionary matches
                        score = 0.95 + (freq_score * 0.05)
                    else:
                        # For non-matches, rely heavily on frequency (most reliable for single words)
                        # and heuristic score
                        score = freq_score * 0.65 + h_score * 0.35
                        # Additional penalty for very low scores
                        if score < 0.2:
                            score *= 0.3
                else:
                    # Multi-word text: combine all scores with smart weighting
                    if word_score > 0.7:
                        # Very high vocabulary match: trust it, but verify with frequency
                        score = word_score * 0.55 + h_score * 0.30 + freq_score * 0.15
                    elif word_score > 0.4:
                        # Good vocabulary match: balanced approach
                        score = word_score * 0.45 + h_score * 0.35 + freq_score * 0.20
                    elif word_score > 0:
                        # Some vocabulary match: still use it but weight frequency more
                        score = word_score * 0.30 + h_score * 0.40 + freq_score * 0.30
                    else:
                        # No vocabulary match: rely on frequency and heuristic
                        # Frequency is more reliable when vocab fails
                        score = freq_score * 0.55 + h_score * 0.45

                # Ensure score is a float and is not NaN or negative
                if math.isnan(score) or math.isinf(score) or score < 0:
                    score = 0.01  # Minimum score instead of 0
                
                # Ensure score is at least 0.01 to avoid rounding issues
                score = max(0.01, score)
                final_score = float(round(score, 4))
                
                # Ensure final_score is never exactly 0.0 (minimum 0.0001 for display)
                if final_score <= 0.0:
                    final_score = 0.0001
                
                # Debug: Print final score for first candidate
                if k == 0:
                    print(f"DEBUG Key {k} - final_score: {final_score}")
                
                candidates.append({
                    'key': k,
                    'plaintext': plaintext,
                    'score': final_score
                })
            except Exception as e:
                print(f"Error scoring shift {k}: {e}")
                import traceback
                traceback.print_exc()
                # Even on error, give a minimal score instead of 0.0
                candidates.append({
                    'key': k,
                    'plaintext': plaintext,
                    'score': 0.0001  # Minimum score instead of 0.0
                })
        
        # Sort by score (highest first), ensuring we have valid candidates
        if not candidates:
            return jsonify({'error': 'No candidates generated'}), 500
        
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Get best result (highest score)
        best = candidates[0]
        
        # Ensure we always return top 5, even if there are fewer candidates
        top_5 = candidates[:5]
        
        # Ensure all scores are floats and never 0.0
        for candidate in top_5:
            if 'score' in candidate:
                score_val = float(candidate['score'])
                if score_val <= 0.0:
                    score_val = 0.0001
                candidate['score'] = score_val
        
        # Debug: Print top 5 scores before sending
        print(f"DEBUG Top 5 scores: {[(c['key'], c['score']) for c in top_5]}")
        
        best_score = float(best['score'])
        if best_score <= 0.0:
            best_score = 0.0001
        
        return jsonify({
            'cipher': cipher_text[:500],
            'key': best['key'],
            'plainText': best['plaintext'][:500],
            'score': best_score,
            'candidates': top_5  # Always return top 5 (or fewer if less than 5 candidates)
        })
    
    except Exception as e:
        print(f"Error in /analyze: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Preload resources
    get_resources('en')
    get_resources('fr')
    print("Resources loaded. Starting Flask app...")
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
