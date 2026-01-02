from crypto.bruteforce import brute_force_caesar

def test_bruteforce_candidate_count():
    text = "Uifsf jt b tfdsfu"
    results = brute_force_caesar(text)
    assert len(results) == 25