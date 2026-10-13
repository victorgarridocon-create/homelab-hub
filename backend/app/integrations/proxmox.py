"""Read nodes, VMs and LXC containers from the Proxmox VE API using an API token."""
import re
from urllib.parse import quote

from . import IntegrationError, http_get_json

GIB = 1024 ** 3
_MAC_RE = re.compile(r"([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})")
_LXC_IP_RE = re.compile(r"(?:^|,)ip=(\d+\.\d+\.\d+\.\d+)")

OS_NAMES = {
    "l26": "Linux", "l24": "Linux 2.4", "win11": "Windows 11", "win10": "Windows 10",
    "win8": "Windows 8", "win7": "Windows 7", "w2k22": "Windows Server 2022",
    "w2k19": "Windows Server 2019", "w2k16": "Windows Server 2016", "other": "Other",
    "solaris": "Solaris",
}


class ProxmoxClient:
    def __init__(self, url, token_id, token_secret, verify_ssl=True):
        url = (url or "").strip().rstrip("/")
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        if not re.search(r":\d+$", url.split("//", 1)[1]):
            url += ":8006"
        if not token_id or not token_secret:
            raise IntegrationError("Token ID and secret are required.")
        self.base = url + "/api2/json"
        self.headers = {"Authorization": f"PVEAPIToken={token_id.strip()}={token_secret.strip()}"}
        self.verify_ssl = verify_ssl

    def get(self, path):
        return http_get_json(self.base + path, self.headers, self.verify_ssl).get("data")

    def try_get(self, path):
        """Optional data (guest agent, interfaces...): missing is fine."""
        try:
            return self.get(path)
        except IntegrationError:
            return None


def _gb(value):
    return round(value / GIB, 1) if value else None


def _first_ipv4(addresses):
    for addr in addresses:
        ip = addr.split("/")[0]
        if ip and not ip.startswith(("127.", "169.254.")) and ":" not in ip:
            return ip
    return None


def _node_ip(client, node):
    for iface in client.try_get(f"/nodes/{quote(node)}/network") or []:
        address = iface.get("address")
        if address and iface.get("type") in ("bridge", "eth", "bond", "vlan") and not address.startswith("127."):
            return address
    return None


def _qemu_network(client, node, vmid, config):
    ip = mac = None
    agent = client.try_get(f"/nodes/{quote(node)}/qemu/{vmid}/agent/network-get-interfaces")
    for iface in (agent or {}).get("result", []) if isinstance(agent, dict) else []:
        if iface.get("name") == "lo":
            continue
        ip = ip or _first_ipv4(
            a.get("ip-address", "") for a in iface.get("ip-addresses", []) if a.get("ip-address-type") == "ipv4"
        )
        mac = mac or iface.get("hardware-address")
    if not mac:
        match = _MAC_RE.search(config.get("net0", ""))
        mac = match.group(1) if match else None
    return ip, mac


def _lxc_network(client, node, vmid, config):
    ip = None
    for iface in client.try_get(f"/nodes/{quote(node)}/lxc/{vmid}/interfaces") or []:
        if iface.get("name") != "lo":
            ip = ip or _first_ipv4([iface.get("inet", "")])
    net0 = config.get("net0", "")
    if not ip:
        match = _LXC_IP_RE.search(net0)
        ip = match.group(1) if match else None
    mac = re.search(r"hwaddr=([0-9A-Fa-f:]{17})", net0)
    return ip, (mac.group(1) if mac else None)


def fetch_inventory(client):
    """Return {"hosts": [...], "guests": [...]} in Homelab Hub field names."""
    nodes = client.get("/nodes") or []
    hosts, guests = [], []
    for n in nodes:
        node = n["node"]
        status = client.try_get(f"/nodes/{quote(node)}/status") or {}
        cpuinfo = status.get("cpuinfo", {})
        hosts.append({
            "key": f"node:{node}",
            "name": node,
            "hostname": node,
            "ip_address": _node_ip(client, node),
            "cpu": cpuinfo.get("model"),
            "cpu_cores": cpuinfo.get("cpus") or n.get("maxcpu"),
            "ram_gb": _gb(status.get("memory", {}).get("total") or n.get("maxmem")),
            "os": f"Proxmox VE {status['pveversion'].split('/')[1]}" if "/" in status.get("pveversion", "") else "Proxmox VE",
            "online": n.get("status") == "online",
        })
        if n.get("status") != "online":
            continue

        for kind in ("qemu", "lxc"):
            for g in client.try_get(f"/nodes/{quote(node)}/{kind}") or []:
                vmid = g["vmid"]
                if g.get("template"):
                    continue
                config = client.try_get(f"/nodes/{quote(node)}/{kind}/{vmid}/config") or {}
                if kind == "qemu":
                    ip, mac = _qemu_network(client, node, vmid, config)
                    os_name = OS_NAMES.get(config.get("ostype"), config.get("ostype"))
                else:
                    ip, mac = _lxc_network(client, node, vmid, config)
                    os_name = (config.get("ostype") or "").capitalize() or "Linux"
                name = g.get("name") or config.get("hostname") or f"{kind}-{vmid}"
                guests.append({
                    "key": f"{kind}:{vmid}",
                    "node": node,
                    "vmid": vmid,
                    "kind": kind,
                    "name": name,
                    "hostname": config.get("hostname") or name,
                    "ip_address": ip,
                    "mac_address": mac,
                    "cpu_cores": g.get("cpus") or g.get("maxcpu") or config.get("cores"),
                    "ram_gb": _gb(g.get("maxmem")),
                    "disk_gb": _gb(g.get("maxdisk")),
                    "os": os_name,
                    "status": g.get("status"),
                })
    guests.sort(key=lambda g: (g["node"], g["vmid"]))
    return {"hosts": hosts, "guests": guests}
