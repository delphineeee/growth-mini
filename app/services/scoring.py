from __future__ import annotations


GAP_WEIGHT = {"verified": 0.0, "claimed": 0.55, "none": 1.0}


def rank_priorities(matrix: list[dict], evidence: list[dict]) -> list[dict]:
    evidence_by_skill = {item["skill"]: item for item in evidence}
    ranked = []
    for row in matrix:
        item = evidence_by_skill.get(row["skill"], {"status": "none", "title": "", "url": "", "note": ""})
        status = item.get("status", "none")
        gap_weight = GAP_WEIGHT.get(status, 1.0)
        priority = round(row["role_weight"] * gap_weight * 100, 1)
        ranked.append({
            **row,
            "evidence_status": status,
            "evidence_title": item.get("title", ""),
            "evidence_url": item.get("url", ""),
            "gap_weight": gap_weight,
            "priority": priority,
            "formula": f"{row['role_weight']:.3f} × {gap_weight:.2f} × 100 = {priority:.1f}",
        })
    return sorted(ranked, key=lambda item: (-item["priority"], -item["role_weight"], item["skill"]))
