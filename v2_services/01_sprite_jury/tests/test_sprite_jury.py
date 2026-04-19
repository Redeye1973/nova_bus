import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_verdict_reject_low_pixel():
    r = client.post("/v1/verdict", json={"pixel_integrity": 3.0, "jury_scores": [9, 9]})
    assert r.status_code == 200
    assert r.json()["verdict"] == "reject"


def test_verdict_accept_all_high():
    r = client.post(
        "/v1/verdict", json={"pixel_integrity": 8.0, "jury_scores": [8, 8.5, 9]}
    )
    assert r.status_code == 200
    assert r.json()["verdict"] == "accept"


def test_pixel_check_png():
    buf = io.BytesIO()
    Image.new("RGBA", (32, 32), (128, 64, 32, 200)).save(buf, format="PNG")
    buf.seek(0)
    r = client.post("/v1/pixel-check", files={"file": ("t.png", buf, "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert "score" in body
    assert body["verdict"] in ("ok", "warning", "broken")
