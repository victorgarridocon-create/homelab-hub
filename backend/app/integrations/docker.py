"""Read containers from the Docker Engine API (unix socket or TCP)."""
import re

from . import IntegrationError, http_get_json, unix_get_json

DEFAULT_SOCKET = "/var/run/docker.sock"


def _list_containers(connection, url, socket_path):
    path = "/containers/json?all=1"
    if connection == "tcp":
        url = (url or "").strip().rstrip("/")
        if not re.match(r"^https?://", url):
            raise IntegrationError("The Docker URL must start with http:// or https://")
        return http_get_json(url + path)
    return unix_get_json(socket_path or DEFAULT_SOCKET, path)


def _pick_port(ports):
    """Prefer published web ports, then the lowest published TCP port."""
    published = [p for p in ports or [] if p.get("PublicPort") and p.get("Type", "tcp") == "tcp"]
    if not published:
        return None, False
    web = [p for p in published if p.get("PrivatePort") in (80, 443, 8080, 8443, 3000, 8000, 9000)]
    chosen = min(web or published, key=lambda p: p["PublicPort"])
    https = chosen.get("PrivatePort") in (443, 8443) or chosen["PublicPort"] in (443, 8443)
    return chosen["PublicPort"], https


def fetch_containers(connection="socket", url=None, socket_path=None):
    containers = _list_containers(connection, url, socket_path)
    apps = []
    for c in containers:
        name = (c.get("Names") or ["/" + c.get("Id", "")[:12]])[0].lstrip("/")
        port, https = _pick_port(c.get("Ports"))
        labels = c.get("Labels") or {}
        apps.append({
            "key": f"container:{name}",
            "name": name,
            "description": c.get("Image"),
            "port": port,
            "https": https,
            "status": c.get("State"),
            "compose_project": labels.get("com.docker.compose.project"),
        })
    apps.sort(key=lambda a: a["name"].lower())
    return apps
