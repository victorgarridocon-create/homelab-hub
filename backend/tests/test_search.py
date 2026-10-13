from .conftest import create


def search(client, q):
    return client.get(f"/inventory/search?q={q}").get_json()["data"]


def test_search_matches_any_text_field(client):
    create(client, "hardware", name="server", ip_address="10.0.0.5", mac_address="aa:bb:cc:dd:ee:ff")
    create(client, "misc", name="switch", notes="Located in rack 42", tags="network")

    by_ip = search(client, "10.0.0.5")
    assert [(r["_type"], r["match_field"]) for r in by_ip] == [("hardware", "ip_address")]
    assert search(client, "dd:ee")[0]["name"] == "server"
    assert search(client, "rack 42")[0]["match_field"] == "notes"
    assert search(client, "network")[0]["name"] == "switch"


def test_search_includes_shares_and_documents(client):
    storage = create(client, "storage", name="tank")
    create(client, "shares", name="media", storage_id=storage["id"], share_type="NFS")
    client.post("/api/docs", json={"title": "Runbook", "content": "restart the media server"})

    types = {r["_type"] for r in search(client, "media")}
    assert types == {"shares", "documents"}
    share = next(r for r in search(client, "media") if r["_type"] == "shares")
    assert share["storage_id"] == storage["id"]


def test_exact_name_ranks_first(client):
    create(client, "apps", name="plex-backup")
    create(client, "apps", name="plex")
    assert search(client, "plex")[0]["name"] == "plex"


def test_empty_query(client):
    assert search(client, "") == []
