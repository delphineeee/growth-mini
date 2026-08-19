from app.services.sprint import build_report, generate_sprint


def test_sprint_has_seven_verifiable_days():
    sprint = generate_sprint("RAG/知识库", 90)
    assert len(sprint["days"]) == 7
    assert sprint["estimated_total_minutes"] > 0
    assert all(day["acceptance"] for day in sprint["days"])


def test_report_calculates_completion_and_time_error():
    report = build_report(700, [
        {"day": day, "completed": day <= 6, "actual_minutes": 100, "artifact_url": "https://example.com" if day == 6 else ""}
        for day in range(1, 8)
    ])
    assert report["completed_days"] == 6
    assert report["completion_rate"] == 85.7
    assert report["estimation_error_percent"] == 0
    assert report["evidence_level"] == "verified"
