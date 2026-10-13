"""add tags to inventory items and purchase/warranty/renewal dates

Revision ID: 009_add_tags_and_dates
Revises: 008_add_mac_address
Create Date: 2026-09-23

"""
from alembic import op
import sqlalchemy as sa
from utils.migration_helpers import add_column_if_not_exists


# revision identifiers, used by Alembic.
revision = '009_add_tags_and_dates'
down_revision = '008_add_mac_address'
branch_labels = None
depends_on = None

TAGGED_TABLES = ['hardware', 'vms', 'apps', 'storage', 'networks', 'misc']
DATE_COLUMNS = [
    ('hardware', 'purchase_date'),
    ('hardware', 'warranty_until'),
    ('apps', 'renewal_date'),
    ('misc', 'renewal_date'),
]


def upgrade():
    for table in TAGGED_TABLES:
        add_column_if_not_exists(table, sa.Column('tags', sa.Text(), nullable=True))
    for table, column in DATE_COLUMNS:
        add_column_if_not_exists(table, sa.Column(column, sa.Text(), nullable=True))


def downgrade():
    for table, column in reversed(DATE_COLUMNS):
        op.drop_column(table, column)
    for table in TAGGED_TABLES:
        op.drop_column(table, 'tags')
