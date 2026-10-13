"""Importers that read inventory from external systems (Proxmox VE, Docker)."""
import http.client
import json
import socket
import ssl
import urllib.error
import urllib.request


class IntegrationError(Exception):
    """Raised with a user-facing message when an external system can't be read."""


def http_get_json(url, headers=None, verify_ssl=True, timeout=10):
    ctx = None
    if url.startswith("https://"):
        ctx = ssl.create_default_context()
        if not verify_ssl:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as res:
            return json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise IntegrationError(f"Access denied ({e.code}). Check the credentials and permissions.")
        raise IntegrationError(f"HTTP {e.code} from {url}")
    except urllib.error.URLError as e:
        reason = e.reason
        if isinstance(reason, ssl.SSLCertVerificationError):
            raise IntegrationError("Invalid SSL certificate. Disable certificate verification for self-signed certificates.")
        raise IntegrationError(f"Could not connect: {reason}")
    except (OSError, ValueError) as e:
        raise IntegrationError(f"Could not connect: {e}")


class _UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path, timeout=10):
        super().__init__("localhost", timeout=timeout)
        self.socket_path = socket_path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.socket_path)


def unix_get_json(socket_path, path, timeout=10):
    try:
        conn = _UnixHTTPConnection(socket_path, timeout=timeout)
        conn.request("GET", path, headers={"Host": "docker"})
        res = conn.getresponse()
        body = res.read().decode()
        conn.close()
    except FileNotFoundError:
        raise IntegrationError(f"Socket not found: {socket_path}. Mount it in docker-compose.yml.")
    except PermissionError:
        raise IntegrationError(f"Permission denied on {socket_path}.")
    except OSError as e:
        raise IntegrationError(f"Could not connect to {socket_path}: {e}")
    if res.status >= 400:
        raise IntegrationError(f"HTTP {res.status} from the Docker API")
    return json.loads(body)


def merge_tags(existing, *new_tags):
    tags = [t.strip() for t in (existing or "").split(",") if t.strip()]
    for tag in new_tags:
        if tag and tag.lower() not in (t.lower() for t in tags):
            tags.append(tag)
    return ", ".join(tags)
