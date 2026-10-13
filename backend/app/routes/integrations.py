"""Preview and import inventory from Proxmox VE, VMware ESXi/vCenter and Docker.

Flow: POST .../preview reads the external system and marks each item as new or matching an
existing record; POST .../apply receives the items the user selected and creates/updates them.
Credentials are only used for the request and never stored.
"""
from flask import Blueprint, jsonify, request

from ..integrations import IntegrationError, merge_tags
from ..integrations import docker as docker_api
from ..integrations import esxi
from ..integrations import proxmox
from ..models import AppService, Hardware, VM, db

bp = Blueprint("integrations", __name__, url_prefix="/api/integrations")

HARDWARE_FIELDS = ("hostname", "ip_address", "cpu", "cpu_cores", "ram_gb", "os", "make", "model", "serial_number")
VM_FIELDS = ("hostname", "ip_address", "mac_address", "cpu_cores", "ram_gb", "disk_gb", "os")
APP_FIELDS = ("description", "port", "https")


@bp.errorhandler(IntegrationError)
def _integration_error(e):
    return jsonify(error=str(e)), 502


def _find_hardware(name):
    name = (name or "").lower()
    return next(
        (h for h in Hardware.query.all() if (h.name or "").lower() == name or (h.hostname or "").lower() == name),
        None,
    )


def _find_vm(name, hardware_id):
    if hardware_id is None:
        return None
    name = (name or "").lower()
    return next((v for v in VM.query.filter_by(hardware_id=hardware_id).all() if (v.name or "").lower() == name), None)


def _find_app(name, hardware_id, vm_id):
    name = (name or "").lower()
    query = AppService.query.filter_by(hardware_id=hardware_id, vm_id=vm_id)
    return next((a for a in query.all() if (a.name or "").lower() == name), None)


def _apply_fields(record, data, fields):
    """Copy non-empty values only, so data the user entered by hand is never blanked."""
    for field in fields:
        value = data.get(field)
        if value not in (None, ""):
            setattr(record, field, value)


# ---- Proxmox ----

def _proxmox_client(body):
    return proxmox.ProxmoxClient(
        body.get("url"), body.get("token_id"), body.get("token_secret"), bool(body.get("verify_ssl", True))
    )


@bp.route("/proxmox/preview", methods=["POST"])
def proxmox_preview():
    body = request.get_json(silent=True) or {}
    data = proxmox.fetch_inventory(_proxmox_client(body))
    return jsonify(data=_mark_matches(data))


def _apply_hosts_and_guests(body, source_tag, guest_tag=lambda guest: None):
    """Create/update hardware from body["hosts"] and VMs from body["guests"] (matched by name)."""
    created = updated = 0
    skipped = []

    node_hw = {}
    for host in body.get("hosts", []):
        hw = _find_hardware(host.get("name"))
        if hw is None:
            hw = Hardware(name=host["name"])
            db.session.add(hw)
            created += 1
        else:
            updated += 1
        _apply_fields(hw, host, HARDWARE_FIELDS)
        hw.tags = merge_tags(hw.tags, source_tag)
        db.session.flush()
        node_hw[host["name"]] = hw.id

    for guest in body.get("guests", []):
        hw_id = node_hw.get(guest.get("node"))
        if hw_id is None:
            hw = _find_hardware(guest.get("node"))
            hw_id = hw.id if hw else None
        if hw_id is None:
            skipped.append({"name": guest.get("name"), "reason": f"node '{guest.get('node')}' is not in the inventory"})
            continue
        vm = _find_vm(guest.get("name"), hw_id)
        if vm is None:
            vm = VM(name=guest["name"], hardware_id=hw_id)
            db.session.add(vm)
            created += 1
        else:
            updated += 1
        _apply_fields(vm, guest, VM_FIELDS)
        vm.tags = merge_tags(vm.tags, source_tag, guest_tag(guest))
        db.session.flush()

    db.session.commit()
    return jsonify(data={"created": created, "updated": updated, "skipped": skipped})


def _mark_matches(data):
    """Set match_id on each host/guest the inventory already has."""
    node_hw = {}
    for host in data["hosts"]:
        hw = _find_hardware(host["name"])
        host["match_id"] = hw.id if hw else None
        node_hw[host["name"]] = hw.id if hw else None
    for guest in data["guests"]:
        vm = _find_vm(guest["name"], node_hw.get(guest["node"]))
        guest["match_id"] = vm.id if vm else None
    return data


@bp.route("/proxmox/apply", methods=["POST"])
def proxmox_apply():
    return _apply_hosts_and_guests(
        request.get_json(silent=True) or {}, "proxmox",
        lambda guest: "lxc" if guest.get("kind") == "lxc" else None,
    )


# ---- VMware ESXi / vCenter ----

@bp.route("/esxi/preview", methods=["POST"])
def esxi_preview():
    body = request.get_json(silent=True) or {}
    data = esxi.fetch_inventory(
        body.get("host"), body.get("username"), body.get("password"), bool(body.get("verify_ssl", True))
    )
    return jsonify(data=_mark_matches(data))


@bp.route("/esxi/apply", methods=["POST"])
def esxi_apply():
    return _apply_hosts_and_guests(request.get_json(silent=True) or {}, "esxi")


# ---- Docker ----

def _parent(body):
    """Resolve the hardware/VM the containers run on."""
    parent_type, parent_id = body.get("parent_type"), body.get("parent_id")
    try:
        parent_id = int(parent_id)
    except (TypeError, ValueError):
        raise IntegrationError("Select the equipment or VM where the containers run.")
    model = {"hardware": Hardware, "vm": VM}.get(parent_type)
    parent = db.session.get(model, parent_id) if model else None
    if parent is None:
        raise IntegrationError("The selected parent does not exist.")
    return parent, (parent_id if parent_type == "hardware" else None), (parent_id if parent_type == "vm" else None)


@bp.route("/docker/preview", methods=["POST"])
def docker_preview():
    body = request.get_json(silent=True) or {}
    containers = docker_api.fetch_containers(body.get("connection", "socket"), body.get("url"), body.get("socket_path"))
    hw_id = vm_id = None
    if body.get("parent_id"):
        _, hw_id, vm_id = _parent(body)
    for c in containers:
        app = _find_app(c["name"], hw_id, vm_id) if (hw_id or vm_id) else None
        c["match_id"] = app.id if app else None
    return jsonify(data={"containers": containers})


@bp.route("/docker/apply", methods=["POST"])
def docker_apply():
    body = request.get_json(silent=True) or {}
    parent, hw_id, vm_id = _parent(body)
    created = updated = 0
    for c in body.get("containers", []):
        app = _find_app(c.get("name"), hw_id, vm_id)
        if app is None:
            app = AppService(name=c["name"], hardware_id=hw_id, vm_id=vm_id)
            db.session.add(app)
            created += 1
        else:
            updated += 1
        _apply_fields(app, c, APP_FIELDS)
        if not app.hostname and parent.hostname:
            app.hostname = parent.hostname
        if not app.ip_address and parent.ip_address:
            app.ip_address = parent.ip_address
        app.tags = merge_tags(app.tags, "docker", c.get("compose_project"))
    db.session.commit()
    return jsonify(data={"created": created, "updated": updated, "skipped": []})
