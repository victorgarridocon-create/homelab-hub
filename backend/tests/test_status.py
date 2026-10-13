from app.utils import monitor

from .conftest import create


def test_targets_skip_items_without_address_and_bad_hosts(client, app):
    create(client, "hardware", name="no-ip")
    create(client, "hardware", name="evil", hostname="-f")
    hw = create(client, "hardware", name="ok", ip_address="10.0.0.2")
    create(client, "apps", name="web", ip_address="10.0.0.2", port=8443, https=True)
    create(client, "apps", name="noport", hostname="svc.lan")

    from app.models import AppService, Hardware, Misc, VM
    with app.app_context():
        targets = monitor.build_targets(Hardware.query.all(), VM.query.all(), AppService.query.all(), Misc.query.all())
    by_key = {t["key"]: t for t in targets}
    assert set(by_key) == {f"hardware-{hw['id']}", "apps-1", "apps-2"}
    assert by_key["apps-1"]["url"] == "https://10.0.0.2:8443/"
    assert by_key["apps-2"]["method"] == "ping"


def fake_checks(monkeypatch, status="up"):
    calls = []

    def fake_check(target, timeout):
        calls.append(target["key"])
        return target["key"], {"status": status, "latency_ms": 1, "method": "ping",
                               "target": target["host"], "checked_at": "now"}

    monkeypatch.setattr(monitor, "check_target", fake_check)
    return calls


def test_status_endpoint_reuses_results(client, monkeypatch):
    calls = fake_checks(monkeypatch)
    create(client, "hardware", name="a", ip_address="10.0.0.2")

    body = client.get("/api/status").get_json()
    assert body["up"] == 1 and body["data"]["hardware-1"]["status"] == "up"
    client.get("/api/status")
    assert calls == ["hardware-1"]  # nothing changed: previous results reused
    client.get("/api/status?refresh=1")
    assert calls == ["hardware-1", "hardware-1"]


def test_deleted_items_disappear_from_results(client, monkeypatch):
    fake_checks(monkeypatch)
    hw = create(client, "hardware", name="a", ip_address="10.0.0.2")
    assert client.get("/api/status").get_json()["data"]
    client.delete(f"/api/hardware/{hw['id']}")
    assert client.get("/api/status").get_json()["data"] == {}


def test_background_mode_answers_immediately(app, monkeypatch):
    """Without STATUS_SYNC the endpoint must not wait for slow checks."""
    import threading
    import time

    started = threading.Event()
    release = threading.Event()

    def slow_check(target, timeout):
        started.set()
        release.wait(5)
        return target["key"], {"status": "down", "latency_ms": None, "method": "ping",
                               "target": target["host"], "checked_at": "now"}

    monkeypatch.setattr(monitor, "check_target", slow_check)
    monkeypatch.setattr(monitor, "_thread", None)
    app.config["STATUS_SYNC"] = False
    c = app.test_client()
    c.post("/api/auth/login", json={"username": "admin", "password": "secret"})
    create(c, "hardware", name="slow", ip_address="10.0.0.3")

    t0 = time.time()
    body = c.get("/api/status").get_json()
    assert time.time() - t0 < 1
    assert body["checking"] is True and body["data"] == {}
    assert started.wait(2)
    release.set()
    for _ in range(50):
        body = c.get("/api/status").get_json()
        if body["data"]:
            break
        time.sleep(0.05)
    assert body["data"]["hardware-1"]["status"] == "down"


def test_http_check_counts_error_responses_as_up(monkeypatch):
    import urllib.error

    def raise_401(*a, **kw):
        raise urllib.error.HTTPError("http://x", 401, "Unauthorized", {}, None)

    monkeypatch.setattr(monitor.urllib.request, "urlopen", raise_401)
    assert monitor._http("http://x/", 1) is True


def test_valid_host():
    assert monitor.valid_host("192.168.1.10")
    assert monitor.valid_host("nas.lan")
    assert not monitor.valid_host("-c 100")
    assert not monitor.valid_host("a b")
    assert not monitor.valid_host("")


def test_status_rechecks_when_items_change(client, monkeypatch):
    calls = fake_checks(monkeypatch, status="down")
    assert client.get("/api/status").get_json()["data"] == {}
    hw = create(client, "hardware", name="new", ip_address="10.0.0.9")
    # A new target appeared: it is checked without waiting for the next interval
    assert f"hardware-{hw['id']}" in client.get("/api/status").get_json()["data"]
    assert calls == [f"hardware-{hw['id']}"]
