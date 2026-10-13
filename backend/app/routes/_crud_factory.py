from flask import Blueprint, current_app, jsonify, request

from ..models import db
from ..utils.icons import list_dict


def create_crud_blueprint(name, model_class, url_prefix=None, detail_route=True, before_save=None):
    """Generate a Flask Blueprint with standard CRUD endpoints for a model.

    before_save(item, data) runs after the request data is applied on create and update.
    """
    prefix = url_prefix or f"/api/{name}"
    bp = Blueprint(name, __name__, url_prefix=prefix)

    @bp.route("", methods=["GET"])
    def list_items():
        items = model_class.query.all()
        return jsonify(data=[list_dict(name, item) for item in items], count=len(items))

    if detail_route:
        @bp.route("/<int:item_id>", methods=["GET"])
        def get_item(item_id):
            item = db.get_or_404(model_class, item_id)
            return jsonify(data=item.to_dict())

    @bp.route("", methods=["POST"])
    def create_item():
        data = request.get_json()
        if not data:
            return jsonify(error="Request body required"), 400
        try:
            item = model_class()
            item.update_from_dict(data)
            if before_save:
                before_save(item, data)
            db.session.add(item)
            db.session.commit()
            return jsonify(data=item.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            print(f"Error creating {model_class.__name__}: {str(e)}")
            return jsonify(error=str(e)), 500

    @bp.route("/<int:item_id>", methods=["PUT"])
    def update_item(item_id):
        item = db.get_or_404(model_class, item_id)
        data = request.get_json()
        if not data:
            return jsonify(error="Request body required"), 400
        try:
            item.update_from_dict(data)
            if before_save:
                before_save(item, data)
            db.session.commit()
            return jsonify(data=item.to_dict())
        except Exception as e:
            db.session.rollback()
            print(f"Error updating {model_class.__name__}: {str(e)}")
            return jsonify(error=str(e)), 500

    @bp.route("/<int:item_id>", methods=["DELETE"])
    def delete_item(item_id):
        item = db.get_or_404(model_class, item_id)
        try:
            db.session.delete(item)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Error deleting %s %s", model_class.__name__, item_id)
            return jsonify(error=f"Could not delete: {e.__class__.__name__}"), 409
        return jsonify(message="Deleted"), 200

    return bp
