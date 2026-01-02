from typing import List, Tuple
from crypto.caesar import decrypt


def excerpt(text: str, length: int = 120) -> str:
    return text[:length]


def brute_force_caesar(ciphertext: str) -> List[Tuple[int, str]]:
    candidates = []

    # include k=0 (no shift) so that already-plain texts are considered
    for k in range(0, 26):
        plaintext = decrypt(ciphertext, k)
        candidates.append((k, plaintext))

    return candidates
