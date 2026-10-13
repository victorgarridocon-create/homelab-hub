from .base import db, BaseMixin


class Hardware(BaseMixin, db.Model):
    __tablename__ = "hardware"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    hostname = db.Column(db.Text)
    ip_address = db.Column(db.Text)
    mac_address = db.Column(db.Text)
    cpu = db.Column(db.Text)
    cpu_cores = db.Column(db.Integer)
    ram_gb = db.Column(db.Float)
    os = db.Column(db.Text)
    make = db.Column(db.Text)
    model = db.Column(db.Text)
    serial_number = db.Column(db.Text)
    location = db.Column(db.Text)
    icon = db.Column(db.Text)
    notes = db.Column(db.Text)
    tags = db.Column(db.Text)  # Comma-separated
    purchase_date = db.Column(db.Text)  # ISO date YYYY-MM-DD
    warranty_until = db.Column(db.Text)  # ISO date YYYY-MM-DD

    # VMs can't exist without their host (vms.hardware_id is NOT NULL, ondelete=CASCADE): delete them
    # with it. Apps and storage just lose the link (their FKs are nullable, ondelete=SET NULL).
    vms = db.relationship("VM", backref="hardware", lazy="select", cascade="all, delete-orphan")
    apps = db.relationship("AppService", backref="hardware", lazy="select")
    storage_pools = db.relationship("Storage", backref="hardware", lazy="select")
