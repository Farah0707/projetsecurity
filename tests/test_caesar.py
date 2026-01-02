import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from crypto.caesar import encrypt, decrypt


#test de cas simples
def test_simple_shift():
    assert encrypt("abc", 3) == "def"
    assert decrypt("def", 3) == "abc"


#test de ponctuation
def test_punctuation_unchanged():
    text = "Hello, world! 123."
    encrypted = encrypt(text, 5)
    assert encrypted == "Mjqqt, btwqi! 123."
    assert decrypt(encrypted, 5) == text


#test majuscule/miniscule
def test_upper_and_lower_case():
    text = "AbC xYz"
    encrypted = encrypt(text, 2)
    assert encrypted == "CdE zAb"
    assert decrypt(encrypted, 2) == text
    


#test d'accent
def test_accents_and_unicode_preserved():
    text = "Sécurité 🔐 café"
    encrypted = encrypt(text, 4)
    assert encrypted == "Wégyvmxé 🔐 gejé"
    assert decrypt(encrypted, 4) == text


#test de chaine vide
def test_empty_string():
    assert encrypt("", 10) == ""
    assert decrypt("", 10) == ""


