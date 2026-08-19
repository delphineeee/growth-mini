from app.services.sprint import build_report, generate_sprint


def test_sprint_has_seven_verifiable_days():
    sprint = generate_sprint("RAG/知识库", 90)
    assert len(sprint["days"]) == 7
    assert sprint["estimated_total_minutes"] > 0
    assert all(day["acceptance"] for day in sprint["days"])


def test_report_calculates_completion_and_time_error():
    report = build_report(700, [
        {
            "day": day,
            "completed": day <= 6,
            "actual_minutes": 100,
            "artifact_url": "https://example.com" if day == 6 else "",
            "note": "今天的学习记录" if day == 1 else "",
            "blocker": "参数校验" if day == 2 else "",
            "next_step": "补充测试" if day == 2 else "",
        }
        for day in range(1, 8)
    ])
    assert report["completed_days"] == 6
    assert report["completion_rate"] == 85.7
    assert report["estimation_error_percent"] == 0
    assert report["recorded_days"] == 7
    assert report["note_count"] == 1
    assert report["checkins"][1]["blocker"] == "参数校验"
