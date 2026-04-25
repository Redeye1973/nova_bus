from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_health():
    r = TestClient(app).get("/health")
    assert r.status_code == 200


def test_create_and_advance_job():
    c = TestClient(app)
    r = c.post("/bake/jobs", json={"postcode": "1234AB", "layers": ["BAG"]})
    assert r.status_code == 200
    jid = r.json()["job_id"]
    r2 = c.get(f"/bake/jobs/{jid}")
    assert r2.json()["state"] == "queued"
    r3 = c.post(f"/bake/jobs/{jid}/advance")
    assert r3.json()["state"] == "pdok"


def test_invoke_create():
    c = TestClient(app)
    r = c.post("/invoke", json={"action": "create", "postcode": "9999ZZ", "layers": []})
    assert r.status_code == 200
    assert "job_id" in r.json()


# ---------------------------------------------------------------------------
# NEW: Asset lineage tests
# ---------------------------------------------------------------------------

import main


def _reset_asset_state():
    main.ASSETS.clear()
    main.LINEAGE_EDGES.clear()


def test_register_asset():
    _reset_asset_state()
    c = TestClient(app)
    r = c.post("/assets/register", json={
        "name": "bag_data.gml",
        "asset_type": "gml",
        "source": "pdok",
        "agent_id": "agent_13",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["registered"] is True
    assert "asset_id" in body


def test_register_asset_custom_id():
    _reset_asset_state()
    c = TestClient(app)
    r = c.post("/assets/register", json={
        "asset_id": "custom-123",
        "name": "custom_asset.obj",
    })
    assert r.status_code == 200
    assert r.json()["asset_id"] == "custom-123"


def test_get_asset():
    _reset_asset_state()
    c = TestClient(app)
    aid = c.post("/assets/register", json={"name": "test.glb"}).json()["asset_id"]

    r = c.get(f"/assets/{aid}")
    assert r.status_code == 200
    body = r.json()
    assert body["asset_id"] == aid
    assert body["name"] == "test.glb"
    assert body["parents"] == []
    assert body["children"] == []


def test_get_asset_unknown():
    _reset_asset_state()
    c = TestClient(app)
    r = c.get("/assets/nonexistent-id")
    assert r.status_code == 404


def test_register_with_parent_creates_lineage():
    _reset_asset_state()
    c = TestClient(app)

    parent_id = c.post("/assets/register", json={"name": "raw_data.gml"}).json()["asset_id"]
    child_id = c.post("/assets/register", json={
        "name": "processed.gpkg",
        "parent_assets": [parent_id],
    }).json()["asset_id"]

    parent = c.get(f"/assets/{parent_id}").json()
    assert child_id in parent["children"]
    assert parent["parents"] == []

    child = c.get(f"/assets/{child_id}").json()
    assert parent_id in child["parents"]
    assert child["children"] == []


def test_multi_parent_lineage():
    _reset_asset_state()
    c = TestClient(app)

    p1 = c.post("/assets/register", json={"name": "bag.gml"}).json()["asset_id"]
    p2 = c.post("/assets/register", json={"name": "bgt.gml"}).json()["asset_id"]
    child = c.post("/assets/register", json={
        "name": "merged.gpkg",
        "parent_assets": [p1, p2],
    }).json()["asset_id"]

    child_detail = c.get(f"/assets/{child}").json()
    assert set(child_detail["parents"]) == {p1, p2}

    p1_detail = c.get(f"/assets/{p1}").json()
    assert child in p1_detail["children"]
    p2_detail = c.get(f"/assets/{p2}").json()
    assert child in p2_detail["children"]


# ---------------------------------------------------------------------------
# NEW: GET /assets/{id}/lineage
# ---------------------------------------------------------------------------


def test_asset_lineage_single():
    _reset_asset_state()
    c = TestClient(app)
    aid = c.post("/assets/register", json={"name": "solo.obj"}).json()["asset_id"]

    r = c.get(f"/assets/{aid}/lineage")
    assert r.status_code == 200
    body = r.json()
    assert body["asset_id"] == aid
    assert len(body["lineage"]) == 1
    assert body["lineage"][0]["asset_id"] == aid
    assert body["lineage"][0]["depth"] == 0


def test_asset_lineage_chain():
    _reset_asset_state()
    c = TestClient(app)

    a = c.post("/assets/register", json={"name": "raw.gml"}).json()["asset_id"]
    b = c.post("/assets/register", json={"name": "processed.gpkg", "parent_assets": [a]}).json()["asset_id"]
    final = c.post("/assets/register", json={"name": "baked.glb", "parent_assets": [b]}).json()["asset_id"]

    r = c.get(f"/assets/{final}/lineage")
    assert r.status_code == 200
    lineage = r.json()["lineage"]
    ids_in_lineage = [node["asset_id"] for node in lineage]
    assert final in ids_in_lineage
    assert b in ids_in_lineage
    assert a in ids_in_lineage


def test_asset_lineage_depth_limit():
    _reset_asset_state()
    c = TestClient(app)

    prev = c.post("/assets/register", json={"name": "root"}).json()["asset_id"]
    for i in range(8):
        prev = c.post("/assets/register", json={
            "name": f"level_{i}",
            "parent_assets": [prev],
        }).json()["asset_id"]

    r = c.get(f"/assets/{prev}/lineage", params={"depth": 3})
    lineage = r.json()["lineage"]
    assert len(lineage) <= 4  # depth 3 means 0,1,2,3 = max 4 nodes


def test_asset_lineage_unknown_asset():
    _reset_asset_state()
    c = TestClient(app)
    r = c.get("/assets/does-not-exist/lineage")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# NEW: GET /assets (list)
# ---------------------------------------------------------------------------


def test_list_assets():
    _reset_asset_state()
    c = TestClient(app)

    c.post("/assets/register", json={"name": "a.gml", "job_id": "j1"})
    c.post("/assets/register", json={"name": "b.gpkg", "job_id": "j1"})
    c.post("/assets/register", json={"name": "c.glb", "job_id": "j2"})

    r = c.get("/assets")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 3


def test_list_assets_filter_by_job_id():
    _reset_asset_state()
    c = TestClient(app)

    c.post("/assets/register", json={"name": "a.gml", "job_id": "j1"})
    c.post("/assets/register", json={"name": "b.gpkg", "job_id": "j1"})
    c.post("/assets/register", json={"name": "c.glb", "job_id": "j2"})

    r = c.get("/assets", params={"job_id": "j1"})
    body = r.json()
    assert body["count"] == 2
    assert all(a["job_id"] == "j1" for a in body["assets"])


def test_list_assets_limit():
    _reset_asset_state()
    c = TestClient(app)
    for i in range(10):
        c.post("/assets/register", json={"name": f"asset_{i}.obj"})

    r = c.get("/assets", params={"limit": 3})
    assert len(r.json()["assets"]) == 3


def test_list_assets_empty():
    _reset_asset_state()
    c = TestClient(app)
    r = c.get("/assets")
    assert r.status_code == 200
    assert r.json()["count"] == 0
    assert r.json()["assets"] == []


# ---------------------------------------------------------------------------
# NEW: full lineage integration test
# ---------------------------------------------------------------------------


def test_asset_lineage_full_pipeline():
    _reset_asset_state()
    c = TestClient(app)

    job = c.post("/bake/jobs", json={"postcode": "1234AB", "layers": ["BAG", "BGT"]}).json()
    jid = job["job_id"]

    raw_bag = c.post("/assets/register", json={
        "name": "BAG_1234AB.gml", "asset_type": "gml",
        "source": "pdok", "job_id": jid, "agent_id": "agent_13",
    }).json()["asset_id"]

    raw_bgt = c.post("/assets/register", json={
        "name": "BGT_1234AB.gml", "asset_type": "gml",
        "source": "pdok", "job_id": jid, "agent_id": "agent_13",
    }).json()["asset_id"]

    processed = c.post("/assets/register", json={
        "name": "merged_1234AB.gpkg", "asset_type": "gpkg",
        "job_id": jid, "agent_id": "agent_15",
        "parent_assets": [raw_bag, raw_bgt],
    }).json()["asset_id"]

    baked = c.post("/assets/register", json={
        "name": "1234AB.glb", "asset_type": "glb",
        "job_id": jid, "agent_id": "agent_14",
        "parent_assets": [processed],
        "minio_path": "/output/1234AB.glb",
    }).json()["asset_id"]

    lineage = c.get(f"/assets/{baked}/lineage").json()["lineage"]
    all_ids = {n["asset_id"] for n in lineage}
    assert raw_bag in all_ids
    assert raw_bgt in all_ids
    assert processed in all_ids
    assert baked in all_ids

    baked_detail = c.get(f"/assets/{baked}").json()
    assert processed in baked_detail["parents"]
    assert baked_detail["children"] == []

    processed_detail = c.get(f"/assets/{processed}").json()
    assert set(processed_detail["parents"]) == {raw_bag, raw_bgt}
    assert baked in processed_detail["children"]

    job_assets = c.get("/assets", params={"job_id": jid}).json()
    assert job_assets["count"] == 4
