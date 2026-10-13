from app.integrations import merge_tags, proxmox
from app.integrations import docker as docker_api

from .conftest import create

PVE = {
    "/nodes": [{"node": "pve1", "status": "online", "maxcpu": 8, "maxmem": 34359738368}],
    "/nodes/pve1/status": {"cpuinfo": {"model": "Ryzen 7", "cpus": 16},
                           "memory": {"total": 68719476736}, "pveversion": "pve-manager/8.2.4/abc"},
    "/nodes/pve1/network": [{"type": "bridge", "iface": "vmbr0", "address": "192.168.1.10"}],
    "/nodes/pve1/qemu": [{"vmid": 100, "name": "docker", "status": "running", "cpus": 4,
                          "maxmem": 8589934592, "maxdisk": 68719476736},
                         {"vmid": 900, "name": "tpl", "template": 1}],
    "/nodes/pve1/qemu/100/config": {"ostype": "l26", "net0": "virtio=BC:24:11:AA:BB:CC,bridge=vmbr0"},
    "/nodes/pve1/qemu/100/agent/network-get-interfaces": {"result": [
        {"name": "lo", "ip-addresses": [{"ip-address-type": "ipv4", "ip-address": "127.0.0.1"}]},
        {"name": "eth0", "hardware-address": "bc:24:11:aa:bb:cc",
         "ip-addresses": [{"ip-address-type": "ipv4", "ip-address": "192.168.1.50"}]}]},
    "/nodes/pve1/lxc": [{"vmid": 101, "name": "pihole", "status": "stopped", "maxmem": 536870912}],
    "/nodes/pve1/lxc/101/config": {"ostype": "debian", "hostname": "pihole",
                                   "net0": "name=eth0,bridge=vmbr0,hwaddr=BC:24:11:00:00:01,ip=192.168.1.53/24"},
}


def fake_pve_get(self, path):
    if path not in PVE:
        raise proxmox.IntegrationError("404")
    return PVE[path]


def test_proxmox_fetch_inventory(monkeypatch):
    monkeypatch.setattr(proxmox.ProxmoxClient, "get", fake_pve_get)
    client = proxmox.ProxmoxClient("pve.lan", "root@pam!hub", "s3cret")
    assert client.base == "https://pve.lan:8006/api2/json"

    data = proxmox.fetch_inventory(client)
    host = data["hosts"][0]
    assert (host["ip_address"], host["cpu_cores"], host["ram_gb"], host["os"]) == \
        ("192.168.1.10", 16, 64.0, "Proxmox VE 8.2.4")

    vm, ct = data["guests"]  # template skipped
    assert (vm["ip_address"], vm["mac_address"], vm["os"], vm["disk_gb"]) == \
        ("192.168.1.50", "bc:24:11:aa:bb:cc", "Linux", 64.0)
    assert (ct["kind"], ct["ip_address"], ct["mac_address"], ct["os"]) == \
        ("lxc", "192.168.1.53", "BC:24:11:00:00:01", "Debian")


def test_proxmox_preview_and_apply(client, monkeypatch):
    monkeypatch.setattr(proxmox.ProxmoxClient, "get", fake_pve_get)
    existing = create(client, "hardware", name="PVE1", notes="keep me")
    body = {"url": "pve.lan", "token_id": "root@pam!hub", "token_secret": "x"}

    preview = client.post("/api/integrations/proxmox/preview", json=body).get_json()["data"]
    assert preview["hosts"][0]["match_id"] == existing["id"]
    assert all(g["match_id"] is None for g in preview["guests"])

    res = client.post("/api/integrations/proxmox/apply", json=preview).get_json()["data"]
    assert res == {"created": 2, "updated": 1, "skipped": []}

    hw = client.get(f"/api/hardware/{existing['id']}").get_json()["data"]
    assert hw["notes"] == "keep me" and hw["ip_address"] == "192.168.1.10" and hw["tags"] == "proxmox"
    assert {v["name"] for v in hw["vms"]} == {"docker", "pihole"}

    # Re-running updates instead of duplicating
    res = client.post("/api/integrations/proxmox/apply", json=preview).get_json()["data"]
    assert res["created"] == 0 and res["updated"] == 3


def test_proxmox_guest_without_node_is_skipped(client):
    res = client.post("/api/integrations/proxmox/apply",
                      json={"guests": [{"name": "orphan", "node": "ghost"}]}).get_json()["data"]
    assert res["skipped"][0]["name"] == "orphan"


def test_proxmox_error_is_reported(client):
    res = client.post("/api/integrations/proxmox/preview", json={"url": "pve.lan"})
    assert res.status_code == 502 and "required" in res.get_json()["error"]


CONTAINERS = [
    {"Names": ["/grafana"], "Image": "grafana/grafana", "State": "running",
     "Ports": [{"PrivatePort": 3000, "PublicPort": 3001, "Type": "tcp"},
               {"PrivatePort": 9999, "PublicPort": 2000, "Type": "tcp"}],
     "Labels": {"com.docker.compose.project": "monitoring"}},
    {"Names": ["/proxy"], "Image": "caddy", "State": "running",
     "Ports": [{"PrivatePort": 443, "PublicPort": 443, "Type": "tcp"}], "Labels": {}},
    {"Names": ["/worker"], "Image": "busybox", "State": "exited", "Ports": [], "Labels": {}},
]


def test_docker_port_detection(monkeypatch):
    monkeypatch.setattr(docker_api, "_list_containers", lambda *a: CONTAINERS)
    apps = {a["name"]: a for a in docker_api.fetch_containers()}
    assert (apps["grafana"]["port"], apps["grafana"]["https"]) == (3001, False)
    assert (apps["proxy"]["port"], apps["proxy"]["https"]) == (443, True)
    assert apps["worker"]["port"] is None


def test_docker_preview_and_apply(client, monkeypatch):
    monkeypatch.setattr(docker_api, "_list_containers", lambda *a: CONTAINERS)
    hw = create(client, "hardware", name="host", hostname="host.lan", ip_address="10.0.0.2")
    parent = {"parent_type": "hardware", "parent_id": hw["id"]}

    preview = client.post("/api/integrations/docker/preview", json=parent).get_json()["data"]
    assert len(preview["containers"]) == 3

    res = client.post("/api/integrations/docker/apply",
                      json={**parent, "containers": preview["containers"][:1]}).get_json()["data"]
    assert res["created"] == 1
    app = client.get("/api/apps").get_json()["data"][0]
    assert (app["hardware_id"], app["ip_address"], app["port"], app["tags"]) == \
        (hw["id"], "10.0.0.2", 3001, "docker, monitoring")

    preview = client.post("/api/integrations/docker/preview", json=parent).get_json()["data"]
    assert preview["containers"][0]["match_id"] == app["id"]


def test_docker_apply_requires_parent(client):
    res = client.post("/api/integrations/docker/apply", json={"containers": []})
    assert res.status_code == 502


def test_merge_tags():
    assert merge_tags("a, B", "b", "c", None) == "a, B, c"
    assert merge_tags(None, "docker") == "docker"


# ---- VMware ESXi / vCenter ----
from types import SimpleNamespace as NS  # noqa: E402

from app.integrations import IntegrationError, esxi  # noqa: E402

GIB = 1024 ** 3


def fake_host():
    """PropertyCollector result for one HostSystem."""
    return {
        "name": "esxi01.lan",
        "runtime.connectionState": "connected",
        "summary.config.name": "esxi01.lan",
        "summary.config.product.fullName": "VMware ESXi 8.0.2 build-22380479",
        "summary.hardware.cpuModel": "Intel Xeon E-2236",
        "summary.hardware.numCpuThreads": 12,
        "summary.hardware.numCpuCores": 6,
        "summary.hardware.memorySize": 64 * GIB,
        "summary.hardware.vendor": "Dell Inc.",
        "summary.hardware.model": "PowerEdge T140",
        "summary.hardware.otherIdentifyingInfo": [],
        "hardware.systemInfo": NS(serialNumber="ABC1234"),
        "config.network.vnic": [NS(spec=NS(ip=NS(ipAddress="192.168.1.20")))],
    }


def fake_vm(name, host_moid="host-1", **overrides):
    props = {
        "name": name,
        "config.template": False,
        "config.instanceUuid": f"uuid-{name}",
        "config.guestFullName": "Ubuntu Linux (64-bit)",
        "config.hardware.numCPU": 4,
        "config.hardware.memoryMB": 8192,
        "config.hardware.device": [
            NS(macAddress="00:50:56:aa:bb:cc"),
            NS(capacityInKB=64 * 1024 * 1024),
            NS(capacityInKB=16 * 1024 * 1024),
            NS(label="CD/DVD"),
        ],
        "guest.ipAddress": "192.168.1.60",
        "guest.hostName": "docker01",
        "guest.guestFullName": "Ubuntu 22.04",
        "guest.net": [],
        "runtime.host": NS(_moId=host_moid) if host_moid else None,
        "runtime.powerState": "poweredOn",
    }
    props.update(overrides)
    return props


def test_esxi_build_inventory():
    vms = {
        "vm-1": fake_vm("docker01"),
        # Powered off, no VMware Tools: no guest data
        "vm-2": fake_vm("win11", **{"guest.ipAddress": None, "guest.hostName": None, "guest.guestFullName": None,
                                    "runtime.powerState": "poweredOff"}),
        "vm-3": fake_vm("tpl-ubuntu", **{"config.template": True}),
        "vm-4": fake_vm("orphan", host_moid=None),
    }
    data = esxi.build_inventory({"host-1": fake_host()}, vms)

    h = data["hosts"][0]
    assert (h["name"], h["ip_address"], h["cpu_cores"], h["ram_gb"]) == ("esxi01.lan", "192.168.1.20", 12, 64.0)
    assert (h["make"], h["model"], h["serial_number"]) == ("Dell Inc.", "PowerEdge T140", "ABC1234")
    assert h["os"].startswith("VMware ESXi 8.0.2")

    assert [g["name"] for g in data["guests"]] == ["docker01", "win11"]  # template + orphan skipped
    d, w = data["guests"]
    assert (d["node"], d["vmid"], d["ip_address"], d["mac_address"], d["cpu_cores"], d["ram_gb"], d["disk_gb"],
            d["os"], d["status"]) == \
        ("esxi01.lan", "vm-1", "192.168.1.60", "00:50:56:aa:bb:cc", 4, 8.0, 80.0, "Ubuntu 22.04", "running")
    assert (w["ip_address"], w["hostname"], w["os"], w["status"]) == (None, "win11", "Ubuntu Linux (64-bit)", "stopped")


def test_esxi_missing_extras_still_import():
    # The optional device/NIC read failed: MAC and disk are simply empty
    vm = fake_vm("lite")
    del vm["config.hardware.device"], vm["guest.net"]
    g = esxi.build_inventory({"host-1": fake_host()}, {"vm-1": vm})["guests"][0]
    assert (g["mac_address"], g["disk_gb"], g["ip_address"]) == (None, None, "192.168.1.60")


def test_esxi_ip_falls_back_to_nic_list_and_skips_ipv6():
    vm = fake_vm("x", **{"guest.ipAddress": "fe80::1",
                         "guest.net": [NS(ipAddress=["fe80::1", "169.254.1.1", "10.0.0.7"])]})
    assert esxi.vm_to_dict(vm, "esxi01.lan")["ip_address"] == "10.0.0.7"


def test_esxi_serial_from_identifying_info():
    host = fake_host()
    host["hardware.systemInfo"] = NS(serialNumber=None)
    host["summary.hardware.otherIdentifyingInfo"] = [
        NS(identifierType=NS(key="AssetTag"), identifierValue="nope"),
        NS(identifierType=NS(key="ServiceTag"), identifierValue="SVC99"),
    ]
    assert esxi.host_to_dict(host)["serial_number"] == "SVC99"


def test_esxi_preview_and_apply(client, monkeypatch):
    def fake_retrieve(si, kind, paths):
        if kind == "HostSystem":
            return {"host-1": fake_host()}
        return {"vm-1": fake_vm("docker01")} if paths == esxi.VM_PATHS else {}

    monkeypatch.setattr(esxi, "connect", lambda *a, **kw: object())
    monkeypatch.setattr(esxi, "disconnect", lambda si: None)
    monkeypatch.setattr(esxi, "retrieve", fake_retrieve)
    existing = create(client, "hardware", name="esxi01.lan", notes="rack 2")
    body = {"host": "esxi01.lan", "username": "reader", "password": "x", "verify_ssl": False}

    preview = client.post("/api/integrations/esxi/preview", json=body).get_json()["data"]
    assert preview["hosts"][0]["match_id"] == existing["id"]
    assert preview["guests"][0]["match_id"] is None

    res = client.post("/api/integrations/esxi/apply", json=preview).get_json()["data"]
    assert res == {"created": 1, "updated": 1, "skipped": []}
    hw = client.get(f"/api/hardware/{existing['id']}").get_json()["data"]
    assert (hw["notes"], hw["make"], hw["serial_number"], hw["tags"]) == ("rack 2", "Dell Inc.", "ABC1234", "esxi")
    assert hw["vms"][0]["name"] == "docker01" and hw["vms"][0]["tags"] == "esxi"


def test_esxi_requires_credentials():
    try:
        esxi.connect("esxi.lan", "", "")
    except IntegrationError as e:
        assert "required" in str(e)
    else:
        raise AssertionError("expected IntegrationError")


def test_esxi_connection_error_is_reported(client):
    # Nothing listens on port 1: pyVmomi's connection error becomes a readable 502
    res = client.post("/api/integrations/esxi/preview",
                      json={"host": "127.0.0.1:1", "username": "root", "password": "x", "verify_ssl": False})
    assert res.status_code == 502 and "connect" in res.get_json()["error"].lower()
