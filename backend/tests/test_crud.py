from .conftest import create


def test_hardware_crud_with_tags_and_dates(client):
    hw = create(client, "hardware", name="pve1", tags="rack, prod",
                purchase_date="2024-01-15", warranty_until="2027-01-15")
    assert hw["tags"] == "rack, prod"
    assert hw["warranty_until"] == "2027-01-15"

    res = client.put(f"/api/hardware/{hw['id']}", json={"name": "pve1b"})
    assert res.get_json()["data"]["name"] == "pve1b"

    assert client.delete(f"/api/hardware/{hw['id']}").status_code == 200
    assert client.get("/api/hardware").get_json()["count"] == 0


def test_app_defaults_hostname_from_parent(client):
    hw = create(client, "hardware", name="host", hostname="host.lan")
    app = create(client, "apps", name="grafana", hardware_id=hw["id"], renewal_date="2026-12-01")
    assert app["hostname"] == "host.lan"
    assert app["renewal_date"] == "2026-12-01"


def test_export_import_roundtrip(client):
    hw = create(client, "hardware", name="nas", tags="storage")
    create(client, "vms", name="vm1", hardware_id=hw["id"])
    exported = client.get("/inventory/export").get_json()

    client.post("/api/hardware", json={"name": "temporary"})
    res = client.post("/inventory/import", json=exported)
    assert res.status_code == 200

    names = [h["name"] for h in client.get("/api/hardware").get_json()["data"]]
    assert names == ["nas"]
    assert client.get("/api/hardware").get_json()["data"][0]["tags"] == "storage"


PNG = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="


def test_lists_reference_image_icons_by_url(client):
    hw = create(client, "hardware", name="nas", icon=PNG)
    create(client, "hardware", name="emoji", icon="🖥️")

    listed = {h["name"]: h["icon"] for h in client.get("/api/hardware").get_json()["data"]}
    assert listed["nas"].startswith(f"/api/icons/hardware/{hw['id']}?v=")
    assert listed["emoji"] == "🖥️"
    # The detail (used by the edit form) keeps the full image
    assert client.get(f"/api/hardware/{hw['id']}").get_json()["data"]["icon"] == PNG
    assert client.get("/inventory").get_json()["data"]["hardware"][0]["icon"].startswith("/api/icons/")

    res = client.get(listed["nas"])
    assert res.status_code == 200 and res.mimetype == "image/png"
    assert res.data.startswith(b"\x89PNG")
    assert "immutable" in res.headers["Cache-Control"]
    assert "sandbox" in res.headers["Content-Security-Policy"]


def test_icon_endpoint_errors(client, anon):
    hw = create(client, "hardware", name="no-icon")
    assert client.get(f"/api/icons/hardware/{hw['id']}").status_code == 404
    assert client.get("/api/icons/networks/1").status_code == 404
    assert anon.get(f"/api/icons/hardware/{hw['id']}").status_code == 401


def test_large_json_is_gzipped(client):
    for i in range(30):
        create(client, "hardware", name=f"host-{i}", notes="x" * 100)
    res = client.get("/api/hardware", headers={"Accept-Encoding": "gzip"})
    assert res.headers["Content-Encoding"] == "gzip"
    import gzip
    import json
    assert json.loads(gzip.decompress(res.data))["count"] == 30
    assert "Content-Encoding" not in client.get("/api/hardware").headers


def test_deleting_hardware_removes_its_vms_and_frees_the_rest(client):
    hw = create(client, "hardware", name="pve")
    vm = create(client, "vms", name="docker", hardware_id=hw["id"])
    app_on_vm = create(client, "apps", name="grafana", vm_id=vm["id"])
    app_on_hw = create(client, "apps", name="pihole", hardware_id=hw["id"])
    pool = create(client, "storage", name="tank", hardware_id=hw["id"])

    res = client.delete(f"/api/hardware/{hw['id']}")
    assert res.status_code == 200, res.get_json()

    assert client.get("/api/vms").get_json()["count"] == 0  # VMs can't exist without their host
    apps = {a["name"]: a for a in client.get("/api/apps").get_json()["data"]}
    assert apps["grafana"]["vm_id"] is None and apps["pihole"]["hardware_id"] is None
    assert client.get(f"/api/storage/{pool['id']}").get_json()["data"]["hardware_id"] is None
