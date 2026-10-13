from .conftest import create


def test_network_usage_and_free_addresses(client):
    create(client, "networks", name="lan", subnet="192.168.1.0/29", gateway="192.168.1.1")
    hw = create(client, "hardware", name="pve", ip_address="192.168.1.2")
    create(client, "apps", name="web", hardware_id=hw["id"], ip_address="192.168.1.2")

    data = client.get("/api/ipam").get_json()["data"]
    lan = data["networks"][0]
    assert lan["size"] == 6
    assert lan["used_count"] == 2  # gateway + pve (the app shares pve's IP)
    assert lan["free_count"] == 4
    assert lan["next_free"] == "192.168.1.3"
    assert data["duplicates"] == []  # an app on its host's IP is not a conflict


def test_duplicates_unassigned_and_invalid(client):
    create(client, "networks", name="lan", subnet="10.0.0.0/24")
    create(client, "hardware", name="a", ip_address="10.0.0.9")
    create(client, "vms", name="b", ip_address="10.0.0.9",
           hardware_id=create(client, "hardware", name="c")["id"])
    create(client, "misc", name="cam", ip_address="172.16.0.4")
    create(client, "misc", name="bad", ip_address="not-an-ip")

    data = client.get("/api/ipam").get_json()["data"]
    assert [d["ip"] for d in data["duplicates"]] == ["10.0.0.9"]
    assert [u["ip"] for u in data["unassigned"]] == ["172.16.0.4"]
    assert data["invalid"][0]["value"] == "not-an-ip"


def test_check_endpoint_excludes_self(client):
    hw = create(client, "hardware", name="a", ip_address="10.0.0.9")
    res = client.get("/api/ipam/check?ip=10.0.0.9").get_json()["data"]
    assert [c["name"] for c in res["conflicts"]] == ["a"]
    res = client.get(f"/api/ipam/check?ip=10.0.0.9&exclude=hardware-{hw['id']}").get_json()["data"]
    assert res["conflicts"] == []
    assert client.get("/api/ipam/check?ip=nope").get_json()["data"]["valid"] is False


def test_ipv4_and_ipv6_together(client):
    create(client, "hardware", name="v4", ip_address="10.0.0.1")
    create(client, "hardware", name="v6", ip_address="fd00::1")
    assert client.get("/api/ipam").status_code == 200
