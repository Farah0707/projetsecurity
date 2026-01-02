from crypto.bruteforce import brute_force_caesar
from crypto.scoring import load_wordlist, valid_word_ratio, heuristic_score

vocab = load_wordlist('data/words_fr.txt')
print('Loaded', len(vocab), 'French words')
