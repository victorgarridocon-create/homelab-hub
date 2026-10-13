from .base import db, BaseMixin


class Misc(BaseMixin, db.Model):
    __tablename__ = "misc"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    category = db.Column(db.Text)
    hostname = db.Column(db.Text)
    description = db.Column(db.Text)
    ip_address = db.Column(db.Text)
    properties = db.Column(db.Text)  # JSON blob for arbitrary key-value pairs
    icon = db.Column(db.Text)
    notes = db.Column(db.Text)
    tags = db.Column(db.Text)  # Comma-separated
    renewal_date = db.Column(db.Text)  # ISO date: domain/certificate/licence renewal
