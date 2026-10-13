"""Read hosts and VMs from VMware ESXi or vCenter through the vSphere SOAP API (pyVmomi).

Standalone ESXi has no REST API, so pyVmomi is the one client that works for both.
Only read-only properties are accessed: a user with the built-in "Read-only" role is enough.
"""
import socket
import ssl

from . import IntegrationError

MIB = 1024 ** 2
GIB = 1024 ** 3


def connect(host, username, password, verify_ssl=True, port=443, timeout=15):
    """Return a pyVmomi ServiceInstance. Caller must call disconnect()."""
    try:
        from pyVim.connect import SmartConnect
        from pyVmomi import vim
    except ImportError:
        raise IntegrationError("pyvmomi is not installed. Rebuild the Docker image.")

    host = (host or "").strip()
    for prefix in ("https://", "http://"):
        if host.startswith(prefix):
            host = host[len(prefix):]
    host = host.split("/")[0]
    if host.count(":") == 1:  # "host:port" (bare IPv6 addresses have several colons)
        host, _, port_text = host.rpartition(":")
        port = int(port_text) if port_text.isdigit() else port
    if not host or not username or not password:
        raise IntegrationError("Host, username and password are required.")

    # Always pass an explicit context: pyVmomi silently skips verification for localhost otherwise
    context = ssl.create_default_context() if verify_ssl else ssl._create_unverified_context()
    try:
        return SmartConnect(
            host=host, user=username, pwd=password, port=port,
            sslContext=context, httpConnectionTimeout=timeout,
        )
    except vim.fault.InvalidLogin:
        raise IntegrationError("Access denied. Check the username and password.")
    except ssl.SSLCertVerificationError:
        raise IntegrationError("Invalid SSL certificate. Disable certificate verification for self-signed certificates.")
    except (OSError, socket.timeout) as e:
        raise IntegrationError(f"Could not connect: {e}")
    except Exception as e:  # pyVmomi raises assorted SOAP/HTTP errors
        raise IntegrationError(f"Could not connect: {getattr(e, 'msg', None) or e}")


def disconnect(service_instance):
    try:
        from pyVim.connect import Disconnect
        Disconnect(service_instance)
    except Exception:
        pass


# Leaf properties fetched with the PropertyCollector. Reading whole objects (vm.runtime...) makes
# pyVmomi deserialize every nested field, and one enum value it doesn't know (newer ESXi than the
# library) breaks the whole read; asking for specific paths avoids that and is one round trip.
HOST_PATHS = [
    "name", "runtime.connectionState", "summary.config.name", "summary.config.product.fullName",
    "summary.hardware.cpuModel", "summary.hardware.numCpuThreads", "summary.hardware.numCpuCores",
    "summary.hardware.memorySize", "summary.hardware.vendor", "summary.hardware.model",
    "summary.hardware.otherIdentifyingInfo", "hardware.systemInfo", "config.network.vnic",
]
VM_PATHS = [
    "name", "config.template", "config.instanceUuid", "config.guestFullName", "config.hardware.numCPU",
    "config.hardware.memoryMB", "guest.ipAddress", "guest.hostName", "guest.guestFullName",
    "runtime.host", "runtime.powerState",
]
# Optional extras (MAC, disks, per-NIC IPs): fetched separately so a failure only loses these fields
VM_EXTRA_PATHS = ["config.hardware.device", "guest.net"]


def retrieve(service_instance, kind, paths):
    """{moId: {path: value}} for every object of a type ("HostSystem" or "VirtualMachine")."""
    from pyVmomi import vim, vmodl

    content = service_instance.RetrieveContent()
    view = content.viewManager.CreateContainerView(content.rootFolder, [getattr(vim, kind)], True)
    try:
        spec = vmodl.query.PropertyCollector.FilterSpec(
            objectSet=[vmodl.query.PropertyCollector.ObjectSpec(
                obj=view, skip=True,
                selectSet=[vmodl.query.PropertyCollector.TraversalSpec(
                    name="traverseView", path="view", skip=False, type=vim.view.ContainerView,
                )],
            )],
            propSet=[vmodl.query.PropertyCollector.PropertySpec(type=getattr(vim, kind), pathSet=paths)],
        )
        collector = content.propertyCollector
        result = collector.RetrievePropertiesEx([spec], vmodl.query.PropertyCollector.RetrieveOptions())
        objects = {}
        while result:
            for obj in result.objects:
                objects[obj.obj._moId] = {prop.name: prop.val for prop in obj.propSet}
            result = collector.ContinueRetrievePropertiesEx(result.token) if result.token else None
        return objects
    finally:
        view.Destroy()


def _get(obj, path, default=None):
    """Safe nested attribute access: properties are often unset (VM off, no VMware Tools...)."""
    for part in path.split("."):
        try:
            obj = getattr(obj, part)
        except Exception:
            return default
        if obj is None:
            return default
    return obj


def _host_ip(props):
    for vnic in props.get("config.network.vnic") or []:
        ip = _get(vnic, "spec.ip.ipAddress")
        if ip and ip != "0.0.0.0":
            return ip
    return None


def _host_serial(props):
    serial = _get(props.get("hardware.systemInfo"), "serialNumber")
    if serial:
        return serial
    for info in props.get("summary.hardware.otherIdentifyingInfo") or []:
        if _get(info, "identifierType.key") in ("SerialNumberTag", "ServiceTag", "EnclosureSerialNumberTag"):
            return info.identifierValue
    return None


def _usable_ipv4(ip):
    return bool(ip) and ":" not in ip and not ip.startswith(("127.", "169.254.", "0."))


def _vm_ip(props):
    ip = props.get("guest.ipAddress")
    if _usable_ipv4(ip):
        return ip
    for nic in props.get("guest.net") or []:
        for candidate in _get(nic, "ipAddress", []) or []:
            if _usable_ipv4(candidate):
                return candidate
    return None


def _vm_mac(props):
    for device in props.get("config.hardware.device") or []:
        mac = getattr(device, "macAddress", None)
        if mac:
            return mac
    return None


def _vm_disk_gb(props):
    # Only virtual disks have capacityInKB
    total_kb = sum(getattr(d, "capacityInKB", 0) or 0 for d in props.get("config.hardware.device") or [])
    return round(total_kb * 1024 / GIB, 1) if total_kb else None


def host_to_dict(props):
    name = props.get("name")
    memory = props.get("summary.hardware.memorySize")
    return {
        "key": f"host:{name}",
        "name": name,
        "hostname": props.get("summary.config.name") or name,
        "ip_address": _host_ip(props),
        "cpu": props.get("summary.hardware.cpuModel"),
        "cpu_cores": props.get("summary.hardware.numCpuThreads") or props.get("summary.hardware.numCpuCores"),
        "ram_gb": round(memory / GIB, 1) if memory else None,
        "os": props.get("summary.config.product.fullName"),
        "make": props.get("summary.hardware.vendor"),
        "model": props.get("summary.hardware.model"),
        "serial_number": _host_serial(props),
        "online": props.get("runtime.connectionState") in (None, "connected"),
    }


POWER_STATES = {"poweredOn": "running", "poweredOff": "stopped", "suspended": "suspended"}


def vm_to_dict(props, host_name):
    name = props.get("name")
    memory_mb = props.get("config.hardware.memoryMB")
    power = str(props.get("runtime.powerState") or "")
    return {
        "key": f"vm:{props.get('config.instanceUuid') or name}",
        "node": host_name,
        "vmid": props.get("_moId", ""),
        "kind": "vm",
        "name": name,
        "hostname": props.get("guest.hostName") or name,
        "ip_address": _vm_ip(props),
        "mac_address": _vm_mac(props),
        "cpu_cores": props.get("config.hardware.numCPU"),
        "ram_gb": round(memory_mb * MIB / GIB, 2) if memory_mb else None,
        "disk_gb": _vm_disk_gb(props),
        "os": props.get("guest.guestFullName") or props.get("config.guestFullName"),
        "status": POWER_STATES.get(power, power),
    }


def build_inventory(hosts, vms):
    """hosts/vms: {moId: {path: value}} → the importer's {hosts, guests} shape."""
    host_names = {moid: props.get("name") for moid, props in hosts.items()}
    host_list = [host_to_dict(props) for props in hosts.values()]
    guests = []
    for moid, props in vms.items():
        if props.get("config.template"):
            continue
        host_ref = props.get("runtime.host")
        host_name = host_names.get(getattr(host_ref, "_moId", None))
        if not host_name:
            continue  # orphaned/inaccessible VM
        guests.append(vm_to_dict({**props, "_moId": moid}, host_name))
    host_list.sort(key=lambda h: h["name"] or "")
    guests.sort(key=lambda g: (g["node"], (g["name"] or "").lower()))
    return {"hosts": host_list, "guests": guests}


def fetch_inventory(host, username, password, verify_ssl=True):
    si = connect(host, username, password, verify_ssl)
    try:
        hosts = retrieve(si, "HostSystem", HOST_PATHS)
        vms = retrieve(si, "VirtualMachine", VM_PATHS)
        try:
            for moid, extra in retrieve(si, "VirtualMachine", VM_EXTRA_PATHS).items():
                vms.get(moid, {}).update(extra)
        except Exception:
            pass  # MAC/disk/NIC details unavailable: import the rest
        return build_inventory(hosts, vms)
    except IntegrationError:
        raise
    except Exception as e:
        raise IntegrationError(f"Error reading the inventory: {getattr(e, 'msg', None) or e}")
    finally:
        disconnect(si)
