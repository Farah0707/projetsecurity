# crypto/caesar.py

def _shift_char(c: str, k: int) -> str:
    """
    Décale un caractère selon le chiffrement de César.
    Supporte uniquement l'alphabet latin (anglais et français).

    Préconditions :
    - c est une chaîne de longueur 1 (str)
    - c est encodé en Unicode (str Python standard)
    - k est un entier (int)

    Comportement :
    - Si c ∈ [A-Z], applique un décalage circulaire sur l'alphabet latin majuscule
    - Si c ∈ [a-z], applique un décalage circulaire sur l'alphabet latin minuscule
    - Sinon (accents, symboles, emojis, ponctuation), retourne c inchangé

    Postcondition :
    - La casse est conservée
    - Le caractère retourné est toujours une chaîne de longueur 1
    """
    if 'A' <= c <= 'Z':
        base = ord('A')
        return chr((ord(c) - base + k) % 26 + base)

    if 'a' <= c <= 'z':
        base = ord('a')
        return chr((ord(c) - base + k) % 26 + base)

    return c


def encrypt(plaintext: str, k: int) -> str:
    """
    Chiffre un texte en clair à l'aide du chiffrement de César.

    Préconditions :
    - plaintext est une chaîne Unicode (str Python)
    - plaintext peut contenir des caractères ASCII et Unicode
    - k est un entier (positif, négatif ou supérieur à 26)

    Comportement :
    - Applique un décalage de k positions aux lettres latines [A-Z] et [a-z]
    - Les autres caractères (accents, emojis, chiffres, ponctuation) sont inchangés
    - La casse des lettres est conservée

    Postconditions :
    - Le texte retourné a la même longueur que plaintext
    - Le résultat est une chaîne Unicode (str)
    """
    k = k % 26
    return ''.join(_shift_char(c, k) for c in plaintext)


def decrypt(ciphertext: str, k: int) -> str:
    """
    Déchiffre un texte chiffré avec le chiffrement de César.

    Préconditions :
    - ciphertext est une chaîne Unicode (str Python)
    - k est l'entier utilisé lors du chiffrement

    Comportement :
    - Applique le décalage inverse (-k)
    - Fonction inverse exacte de encrypt

    Postconditions :
    - decrypt(encrypt(x, k), k) == x pour tout texte valide x
    """
    return encrypt(ciphertext, -k)
