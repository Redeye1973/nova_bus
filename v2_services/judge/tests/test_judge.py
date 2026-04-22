from judge.nova_judge import NovaJudge

j = NovaJudge()


def test_accept():
    r = j.evaluate(
        {"status": "success"},
        ["entrypoint=v1", "dispatch=v2", "agent=foo"],
    )
    assert r["verdict"] == "accept"
    assert r["score"] >= 0.75


def test_reject_localhost():
    r = j.evaluate(
        {"status": "success"},
        ["entrypoint=v1", "dispatch=v2", "localhost:8080"],
    )
    assert r["verdict"] == "reject"


def test_reject_routing():
    r = j.evaluate({"status": "success"}, ["random log"])
    assert r["verdict"] == "reject"


def test_reject_format():
    # Invalid payload plus forbidden override flag (without godot_import) → sub 0.75
    r = j.evaluate(
        {"invalid": "no_status"},
        ["entrypoint=v1", "dispatch=v2", "override=true"],
    )
    assert r["verdict"] == "reject"
