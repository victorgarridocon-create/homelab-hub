"""Reachability checks for inventory items (ping for hosts, HTTP for apps)."""
import re
import socket
import ssl
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

# Hostnames/IPs only. Rejecting a leading "-" stops a value being read as a ping option.
_HOST_RE = re.compile(r"^[A-Za-z0-9_.:\[\]%-]+$")
_FALLBACK_TCP_PORTS = (22, 80, 443)



def valid_host(host):
    return bool(host) and not host.startswith("-") and bool(_HOST_RE.match(host)) and len(host) <= 253


def build_targets(hardware, vms, apps, misc):
    """Turn model instances into check targets. Items without an address are skipped."""
    targets = []

    def add_host(entity_type, item):
        host = (item.ip_address or item.hostname or "").strip()
        if valid_host(host):
            targets.append({"key": f"{entity_type}-{item.id}", "host": host, "method": "ping"})

    for item in hardware:
        add_host("hardware", item)
    for item in vms:
        add_host("vms", item)
    for item in misc:
        add_host("misc", item)
    for app in apps:
        host = (app.ip_address or app.hostname or "").strip()
        if not valid_host(host):
            continue
        if app.port:
            scheme = "https" if app.https else "http"
            targets.append({
                "key": f"apps-{app.id}", "host": host, "method": "http",
                "url": f"{scheme}://{host}:{app.port}/",
            })
        else:
            targets.append({"key": f"apps-{app.id}", "host": host, "method": "ping"})
    return targets


def _tcp_probe(host, timeout):
    """Host is reachable if any common port accepts or actively refuses the connection."""
    for port in _FALLBACK_TCP_PORTS:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except ConnectionRefusedError:
            return True
        except OSError:
            continue
    return False


def _ping(host, timeout):
    seconds = str(max(1, int(round(timeout))))
    if sys.platform == "darwin":
        cmd = ["ping", "-c", "1", "-t", seconds, host]
    else:
        cmd = ["ping", "-c", "1", "-W", seconds, host]
    try:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                timeout=timeout + 1)
        return result.returncode == 0, "ping"
    except (FileNotFoundError, PermissionError):
        return _tcp_probe(host, timeout), "tcp"
    except subprocess.TimeoutExpired:
        return False, "ping"


def _http(url, timeout):
    # Homelab services commonly use self-signed certificates: reachability matters, not trust.
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "homelab-hub-monitor"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx):
            return True
    except urllib.error.HTTPError:
        return True  # The server answered (401, 404, 500...): it is up
    except (urllib.error.URLError, OSError, ValueError):
        return False


def check_target(target, timeout):
    start = time.monotonic()
    if target["method"] == "http":
        up, method = _http(target["url"], timeout), "http"
    else:
        up, method = _ping(target["host"], timeout)
    latency = round((time.monotonic() - start) * 1000)
    return target["key"], {
        "status": "up" if up else "down",
        "latency_ms": latency if up else None,
        "method": method,
        "target": target.get("url") or target["host"],
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def run_checks(targets, timeout, check=None):
    if not targets:
        return {}
    check = check or check_target
    # Unreachable hosts wait for the full timeout, so run many checks at once
    with ThreadPoolExecutor(max_workers=min(64, len(targets))) as pool:
        return dict(pool.map(lambda t: check(t, timeout), targets))


# ---- Results store + background checker ----
# Checks can take several seconds (every unreachable host waits for the timeout), so they run in a
# background thread and the API always answers immediately with the latest results.

_state = {"results": {}, "checked_at": 0.0, "signature": None, "running": False}
_lock = threading.Lock()
_wake = threading.Event()
_thread = None


def signature(targets):
    return sorted((t["key"], t["host"], t.get("url")) for t in targets)


def refresh(targets, timeout, check=None):
    """Check targets now (blocking) and store the results."""
    with _lock:
        _state["running"] = True
    try:
        results = run_checks(targets, timeout, check)
    finally:
        with _lock:
            _state["running"] = False
    with _lock:
        _state.update(results=results, checked_at=time.time(), signature=signature(targets))


def snapshot():
    with _lock:
        return dict(_state["results"]), _state["checked_at"], _state["signature"], _state["running"]


def ensure_background(app, targets_factory, interval):
    """Start the checker thread once per process (gunicorn worker)."""
    global _thread
    with _lock:
        if _thread is not None and _thread.is_alive():
            return
        _thread = threading.Thread(
            target=_loop, args=(app, targets_factory, interval), daemon=True, name="status-monitor"
        )
        _thread.start()


def request_refresh():
    """Ask the background thread to check again now (new/edited items, "Refresh" button)."""
    _wake.set()


def _loop(app, targets_factory, interval):
    while True:
        try:
            with app.app_context():
                targets = targets_factory()
            refresh(targets, app.config["STATUS_TIMEOUT_SECONDS"])
        except Exception:
            app.logger.exception("Status check failed")
        _wake.wait(interval)
        _wake.clear()


def reset_cache():
    with _lock:
        _state.update(results={}, checked_at=0.0, signature=None, running=False)
