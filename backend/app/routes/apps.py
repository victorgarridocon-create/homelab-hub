from ..models import AppService, Hardware, VM, db
from ._crud_factory import create_crud_blueprint


def _set_default_hostname(app_service, data):
    """Set hostname to parent's hostname if not provided."""
    # Only set default if hostname is not provided or is empty
    if not data.get("hostname"):
        if app_service.hardware_id:
            hardware = db.session.get(Hardware, app_service.hardware_id)
            if hardware and hardware.hostname:
                app_service.hostname = hardware.hostname
        elif app_service.vm_id:
            vm = db.session.get(VM, app_service.vm_id)
            if vm and vm.hostname:
                app_service.hostname = vm.hostname


bp = create_crud_blueprint("apps", AppService, before_save=_set_default_hostname)
