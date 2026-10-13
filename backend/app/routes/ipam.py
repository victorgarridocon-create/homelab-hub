"""IP address management: usage per subnet, free addresses and conflicts."""
from collections import defaultdict
from ipaddress import ip_address, ip_network
from itertools import islice

from flask import Blueprint, jsonify, request

from ..models import AppService, Hardware, Misc, Network, Share, VM

bp = Blueprint("ipam", __name__, url_prefix="/api/ipam")

# Hosts own an address: two hosts on one IP is a conflict. Apps and shares usually reuse
# their parent's IP, so they count as "used" but never as a conflict.
HOST_SOURCES = (("hardware", Hardware), ("vms", VM), ("misc", Misc))
SERVICE_SOURCES = (("apps", AppService), ("shares", Share))
FREE_SAMPLE_SIZE = 256
MAX_SCAN = 65536


def _ip_sort_key(entry):
    # IPv4 and IPv6 objects can't be compared directly
    return (entry[0].version, entry[0])


def _ip_attr(item):
    return getattr(item, "ip_address", None) or getattr(item, "ip", None)


def collect_addresses():
    """Return ({ip: [owner, ...]}, [invalid entries])."""
    used = defaultdict(list)
    invalid = []
    for sources, is_host in ((HOST_SOURCES, True), (SERVICE_SOURCES, False)):
        for entity_type, model in sources:
            for item in model.query.all():
                raw = (_ip_attr(item) or "").strip()
                if not raw:
                    continue
                owner = {"type": entity_type, "id": item.id, "name": item.name, "host": is_host}
                if entity_type == "shares":
                    owner["storage_id"] = item.storage_id
                try:
                    used[ip_address(raw)].append(owner)
                except ValueError:
                    invalid.append({"value": raw, "owner": owner})
    return used, invalid


def _network_summary(network, used):
    net = ip_network(network.subnet, strict=False)
    gateway = None
    if network.gateway:
        try:
            gateway = ip_address(network.gateway.strip())
        except ValueError:
            pass

    in_net = {ip: owners for ip, owners in used.items() if ip.version == net.version and ip in net}
    taken = set(in_net)
    if gateway is not None and gateway in net:
        taken.add(gateway)

    usable = net.num_addresses - 2 if net.version == 4 and net.prefixlen < 31 else net.num_addresses
    free_iter = (h for h in islice(net.hosts(), MAX_SCAN) if h not in taken)
    free_sample = [str(h) for h in islice(free_iter, FREE_SAMPLE_SIZE)]

    rows = [{"ip": str(ip), "owners": owners} for ip, owners in in_net.items()]
    if gateway is not None and gateway in net and gateway not in in_net:
        rows.append({"ip": str(gateway), "owners": []})
    rows.sort(key=lambda r: ip_address(r["ip"]))

    used_count = len(taken)
    return {
        "id": network.id,
        "name": network.name,
        "subnet": str(net),
        "vlan_id": network.vlan_id,
        "color": network.color,
        "gateway": str(gateway) if gateway is not None else None,
        "size": usable,
        "used_count": used_count,
        "free_count": max(0, usable - used_count),
        "utilization": round(used_count / usable * 100, 1) if usable else 0,
        "next_free": free_sample[0] if free_sample else None,
        "free_sample": free_sample,
        "addresses": rows,
    }


@bp.route("", methods=["GET"])
def ipam_overview():
    used, invalid = collect_addresses()

    networks, bad_subnets, parsed = [], [], []
    for network in Network.query.order_by(Network.name).all():
        if not network.subnet:
            continue
        try:
            parsed.append(ip_network(network.subnet, strict=False))
            networks.append(_network_summary(network, used))
        except ValueError:
            bad_subnets.append({"id": network.id, "name": network.name, "subnet": network.subnet})

    duplicates = [
        {"ip": str(ip), "owners": owners}
        for ip, owners in sorted(used.items(), key=_ip_sort_key)
        if sum(1 for o in owners if o["host"]) > 1
    ]
    unassigned = [
        {"ip": str(ip), "owners": owners}
        for ip, owners in sorted(used.items(), key=_ip_sort_key)
        if not any(ip.version == n.version and ip in n for n in parsed)
    ]
    return jsonify(data={
        "networks": networks,
        "duplicates": duplicates,
        "unassigned": unassigned,
        "invalid": invalid,
        "invalid_subnets": bad_subnets,
    })


@bp.route("/check", methods=["GET"])
def check_ip():
    """Which hosts already use ?ip= (excluding ?exclude=<type>-<id>)."""
    raw = request.args.get("ip", "").strip()
    exclude = request.args.get("exclude", "")
    try:
        ip = ip_address(raw)
    except ValueError:
        return jsonify(data={"valid": False, "conflicts": []})
    used, _ = collect_addresses()
    conflicts = [o for o in used.get(ip, []) if o["host"] and f"{o['type']}-{o['id']}" != exclude]
    return jsonify(data={"valid": True, "conflicts": conflicts})
