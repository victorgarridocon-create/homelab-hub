from flask import Blueprint, Response, abort

from ..models import AppService, Hardware, Misc, Storage, VM, db
from ..utils import icons

bp = Blueprint("icons", __name__, url_prefix="/api/icons")

MODELS = {"hardware": Hardware, "vms": VM, "apps": AppService, "storage": Storage, "misc": Misc}


@bp.route("/<entity_type>/<int:item_id>", methods=["GET"])
def get_icon(entity_type, item_id):
    model = MODELS.get(entity_type) or abort(404)
    item = db.get_or_404(model, item_id)
    decoded = icons.decode(item.icon) or abort(404)
    mimetype, data = decoded
    response = Response(data, mimetype=mimetype)
    # The URL carries ?v=<updated_at>, so it can be cached for good
    response.headers["Cache-Control"] = "private, max-age=31536000, immutable"
    # An uploaded SVG opened directly must not be able to run script
    response.headers["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'; sandbox"
    return response
