from flask import Blueprint, jsonify, request
from ..models import *
from ..models.base import db
import json

from ..utils.icons import icon_url, list_dict

bp = Blueprint('inventory', __name__, url_prefix='/inventory')

ENTITY_MAP = {
    "hardware": Hardware,
    "vms": VM,
    "apps": AppService,
    "storage": Storage,
    "networks": Network,
    "misc": Misc,
}


@bp.route("", methods=["GET"])
def get_all_inventory():
    """Return all inventory items across all types."""
    result = {}
    for entity_type, model in ENTITY_MAP.items():
        result[entity_type] = [list_dict(entity_type, item) for item in model.query.all()]
    return jsonify(data=result)


SEARCH_LIMIT = 50


def _text_columns(model):
    return [c for c in model.__table__.columns if isinstance(c.type, db.Text) and c.name != "icon"]


def _snippet(text, q, width=60):
    """Short excerpt of text around the first match of q."""
    text = " ".join(str(text).split())
    pos = text.lower().find(q.lower())
    if pos < 0:
        return text[:width]
    start = max(0, pos - width // 2)
    end = min(len(text), pos + len(q) + width // 2)
    return ("…" if start else "") + text[start:end] + ("…" if end < len(text) else "")


@bp.route("/search", methods=["GET"])
def search_inventory():
    """Search every text field (name, IPs, hostnames, MACs, tags, notes...) across all types."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify(data=[], count=0)

    pattern = f"%{q}%"
    results = []
    sources = list(ENTITY_MAP.items()) + [("shares", Share), ("documents", Document)]
    for entity_type, model in sources:
        columns = _text_columns(model)
        matches = model.query.filter(db.or_(*[c.ilike(pattern) for c in columns])).limit(SEARCH_LIMIT).all()
        for item in matches:
            field, value = next(
                ((c.name, getattr(item, c.name)) for c in columns
                 if getattr(item, c.name) and q.lower() in str(getattr(item, c.name)).lower()),
                ("name", ""),
            )
            results.append({
                "_type": entity_type,
                "id": item.id,
                "name": getattr(item, "name", None) or getattr(item, "title", ""),
                "icon": icon_url(entity_type, item),
                "storage_id": getattr(item, "storage_id", None),
                "match_field": field,
                "match": _snippet(value, q),
            })

    # Exact name matches first, then prefix matches, then the rest
    ql = q.lower()
    results.sort(key=lambda r: (r["name"].lower() != ql, not r["name"].lower().startswith(ql), r["name"].lower()))
    return jsonify(data=results[:SEARCH_LIMIT], count=len(results))


@bp.route('/export', methods=['GET'])
def export_database():
    """Export all data from the database"""
    try:
        # Define the order of data to export to maintain relationships
        data = {
            'hardware': [h.to_dict() for h in Hardware.query.all()],
            'vms': [vm.to_dict() for vm in VM.query.all()],
            'apps': [app.to_dict() for app in AppService.query.all()],
            'storage': [s.to_dict() for s in Storage.query.all()],
            'networks': [n.to_dict() for n in Network.query.all()],
            'misc': [m.to_dict() for m in Misc.query.all()],
            'documents': [d.to_dict() for d in Document.query.all()]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/import', methods=['POST'])
def import_database():
    """Import data into the database"""
    try:
        import_data = request.get_json()

        # Clear existing data in dependency order
        db.session.query(Share).delete()  # Delete shares before storage
        db.session.query(AppService).delete()
        db.session.query(VM).delete()
        db.session.query(Hardware).delete()
        db.session.query(Storage).delete()
        db.session.query(Network).delete()
        db.session.query(Misc).delete()
        db.session.query(Document).delete()

        # Helper function to remove auto-generated fields
        def clean_item(item):
            item_copy = item.copy()
            # Remove fields that should be auto-generated
            item_copy.pop('id', None)
            item_copy.pop('created_at', None)
            item_copy.pop('updated_at', None)
            # Remove nested relationships (they'll be imported separately)
            item_copy.pop('shares', None)
            return item_copy

        # Import new data in dependency order
        # First, import hardware (no dependencies)
        if 'hardware' in import_data:
            for item in import_data['hardware']:
                hardware = Hardware(**clean_item(item))
                db.session.add(hardware)
        
        db.session.flush()  # Get IDs for hardware

        # Import VMs (depends on hardware)
        if 'vms' in import_data:
            for item in import_data['vms']:
                vm = VM(**clean_item(item))
                db.session.add(vm)
        
        db.session.flush()  # Get IDs for VMs

        # Import apps (depends on hardware and VMs)
        if 'apps' in import_data:
            for item in import_data['apps']:
                app = AppService(**clean_item(item))
                db.session.add(app)

        # Import storage (depends on hardware and VMs)
        storage_entries = []  # Track storage objects with their share data
        if 'storage' in import_data:
            for item in import_data['storage']:
                # Extract shares before cleaning
                shares_data = item.get('shares', [])
                cleaned_item = clean_item(item)
                storage = Storage(**cleaned_item)
                db.session.add(storage)
                storage_entries.append((storage, shares_data))

        db.session.flush()  # Get IDs for storage

        # Now import shares (depends on storage)
        for storage, shares_data in storage_entries:
            if not shares_data:
                continue
            for share_data in shares_data:
                cleaned_share = clean_item(share_data)
                cleaned_share['storage_id'] = storage.id  # Set the correct storage_id
                share = Share(**cleaned_share)
                db.session.add(share)

        # Import networks
        if 'networks' in import_data:
            for item in import_data['networks']:
                network = Network(**clean_item(item))
                db.session.add(network)

        # Import misc
        if 'misc' in import_data:
            for item in import_data['misc']:
                misc = Misc(**clean_item(item))
                db.session.add(misc)

        # Import documents
        if 'documents' in import_data:
            for item in import_data['documents']:
                document = Document(**clean_item(item))
                db.session.add(document)

        db.session.commit()
        return jsonify({'message': 'Database imported successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
