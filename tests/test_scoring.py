from app.services.scoring import rank_priorities


def test_verified_evidence_removes_gap_priority():
    matrix = [{"skill": "RAG", "role_weight": 0.8, "jd_count": 8}]
    ranked = rank_priorities(matrix, [{"skill": "RAG", "status": "verified", "title": "demo", "url": "x"}])
    assert ranked[0]["priority"] == 0


def test_claimed_evidence_is_between_none_and_verified():
    matrix = [{"skill": "RAG", "role_weight": 0.8, "jd_count": 8}]
    none_score = rank_priorities(matrix, [])[0]["priority"]
    claimed_score = rank_priorities(matrix, [{"skill": "RAG", "status": "claimed"}])[0]["priority"]
    assert 0 < claimed_score < none_score
