def test_list_root(client):
    r = client.get("/memory/list")
    assert r.status_code == 200
    items = r.json()["items"]
    names = [i["name"] for i in items]
    assert "test.md" in names


def test_get_file(client):
    r = client.get("/memory/get?path=test.md")
    assert r.status_code == 200
    assert "Hello world" in r.json()["content"]


def test_get_missing(client):
    r = client.get("/memory/get?path=nonexistent.md")
    assert r.status_code == 404


def test_search(client):
    r = client.get("/memory/search?q=Hello")
    assert r.status_code == 200
    assert r.json()["count"] >= 1


def test_search_no_results(client):
    r = client.get("/memory/search?q=xyznonexistent")
    assert r.status_code == 200
    assert r.json()["count"] == 0


def test_write_new(client):
    r = client.post("/memory/write", json={"path": "new_doc.md", "content": "# New\n\nContent"})
    assert r.status_code == 200
    assert r.json()["written"] is True


def test_write_conflict(client):
    client.post("/memory/write", json={"path": "conflict.md", "content": "first"})
    r = client.post("/memory/write", json={"path": "conflict.md", "content": "second"})
    assert r.status_code == 409


def test_write_overwrite(client):
    client.post("/memory/write", json={"path": "overwrite.md", "content": "first"})
    r = client.post("/memory/write", json={"path": "overwrite.md", "content": "second", "overwrite": True})
    assert r.status_code == 200


def test_append(client):
    r = client.post("/memory/append", json={"path": "log.md", "content": "Entry 1"})
    assert r.status_code == 200
    assert r.json()["appended"] is True


def test_timeline(client):
    r = client.get("/memory/timeline?project=test_project")
    assert r.status_code == 200
    assert r.json()["count"] >= 1


def test_invoke_list(client):
    r = client.post("/invoke", json={"action": "list", "path": ""})
    assert r.status_code == 200


def test_invoke_search(client):
    r = client.post("/invoke", json={"action": "search", "query": "Hello"})
    assert r.status_code == 200


def test_invoke_unknown(client):
    r = client.post("/invoke", json={"action": "unknown_action"})
    assert r.status_code == 400
