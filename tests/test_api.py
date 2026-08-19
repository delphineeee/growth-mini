import asyncio

import httpx

from app.main import app


def request(method: str, path: str, **kwargs) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def test_main_flow_endpoints():
    health = request("GET", "/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    matrix = request("GET", "/api/matrix", params={"role_family": "application"})
    assert matrix.status_code == 200
    assert matrix.json()["summary"]["jd_count"] > 0
    assert matrix.json()["matrix"]

    priority = request(
        "POST",
        "/api/priorities",
        json={"role_family": "application", "evidence": []},
    )
    assert priority.status_code == 200
    top_skill = priority.json()["priorities"][0]["skill"]

    sprint = request(
        "POST",
        "/api/sprint",
        json={"skill": top_skill, "daily_minutes": 90},
    )
    assert sprint.status_code == 200
    assert len(sprint.json()["days"]) == 7


def test_invalid_filters_and_time_are_rejected():
    assert request("GET", "/api/matrix", params={"role_family": "unknown"}).status_code == 422
    assert request("POST", "/api/sprint", json={"skill": "Python", "daily_minutes": 5}).status_code == 422
