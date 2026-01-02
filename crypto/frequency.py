from collections import Counter
from crypto.caesar import decrypt

def letter_frequency(text: str, alphabet_only=True):
    """
    Compte la fréquence de chaque lettre dans un texte.
    Params:
        text (str)
        alphabet_only (bool) : ignore les caractères non alphabétiques
    Returns:
        dict : {lettre: fréquence_rel}
    """
    text = text.upper()
    if alphabet_only:
        text = ''.join(c for c in text if c.isalpha())

    total = len(text)
    counts = Counter(text)
    freqs = {c: counts[c] / total for c in counts} if total > 0 else {}
    return freqs

def best_key_by_frequency(ciphertext: str, language='EN'):
    """
    Propose une clé candidate en utilisant l'analyse fréquentielle.
    EN : suppose que 'E' est la lettre la plus fréquente
    FR : suppose que 'E' est la lettre la plus fréquente (adaptable)
    """
    freqs = letter_frequency(ciphertext)
    if not freqs:
        return 0  # chaîne vide ou pas de lettres

    # lettre la plus fréquente dans le texte chiffré
    Lmax = max(freqs, key=freqs.get)

    # lettre de référence selon langue
    ref_letter = 'E' if language.upper() in ['EN', 'FR'] else 'E'

    # clé candidate : décalage pour que Lmax devienne ref_letter
    k = (ord(Lmax) - ord(ref_letter)) % 26
    return k

def decrypt_with_frequency(ciphertext: str, language='EN'):
    """
    Retourne le texte déchiffré avec la clé proposée par analyse fréquentielle
    """
    k = best_key_by_frequency(ciphertext, language)
    return decrypt(ciphertext, k), k
