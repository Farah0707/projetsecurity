from crypto.scoring import heuristic_score

def test_scoring_positive_for_cleartext():
    text = "This is a secret message"
    score = heuristic_score(text, lang="en")
    assert score > 0