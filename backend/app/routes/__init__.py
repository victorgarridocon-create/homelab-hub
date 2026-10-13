from . import apps, documents, hardware, integrations, inventory, ipam, map_routes, misc, networks, shares, status, storage, vms
from flask import Blueprint

def register_blueprints(app):
    from .documents import bp as documents_bp
    from .hardware import bp as hardware_bp
    from .vms import bp as vms_bp
    from .apps import bp as apps_bp
    from .storage import bp as storage_bp
    from .shares import bp as shares_bp
    from .networks import bp as networks_bp
    from .misc import bp as misc_bp
    from .inventory import bp as inventory_bp
    from .map_routes import bp as map_bp
    from .status import bp as status_bp
    from .ipam import bp as ipam_bp
    from .integrations import bp as integrations_bp
    from .icons import bp as icons_bp

    app.register_blueprint(documents_bp)
    app.register_blueprint(hardware_bp)
    app.register_blueprint(vms_bp)
    app.register_blueprint(apps_bp)
    app.register_blueprint(storage_bp)
    app.register_blueprint(shares_bp)
    app.register_blueprint(networks_bp)
    app.register_blueprint(misc_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(map_bp)
    app.register_blueprint(status_bp)
    app.register_blueprint(ipam_bp)
    app.register_blueprint(integrations_bp)
    app.register_blueprint(icons_bp)
