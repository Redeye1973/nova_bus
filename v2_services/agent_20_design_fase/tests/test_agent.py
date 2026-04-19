import base64
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["agent"] == "20_design_fase"


def test_palette_create() -> None:
    response = client.post(
        "/palette/create",
        json={"theme": "space_noir", "faction_count": 6, "restrictions": {}},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["master_palette"]) == 32
    assert "faction_0" in data["faction_palettes"]


def test_palette_validate() -> None:
    response = client.post(
        "/palette/validate",
        json={
            "palette": ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF"],
            "faction_names": ["harkon", "helios", "marshal", "ghost", "phantom"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "valid" in body


def test_silhouette_check() -> None:
    img = Image.new("RGBA", (100, 100))
    for i in range(100):
        img.putpixel((i, i), (255, 0, 0, 255))
    buf = BytesIO()
    img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    response = client.post(
        "/silhouette/check",
        json={"image_base64": img_b64, "target_sizes": [32, 64]},
    )
    assert response.status_code == 200
    assert "size_results" in response.json()
