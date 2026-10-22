"""Initial scoped schema. DDL is frozen beside this revision, not imported from current models."""
from pathlib import Path

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().exec_driver_sql(Path(__file__).with_suffix('.sql').read_text(encoding='utf-8'))


def downgrade():
    for name in ['external_mappings', 'outbox', 'oauth_states', 'crm_installations', 'crm_connections',
                 'knowledge_chunks', 'document_manifest', 'document_versions', 'activity', 'idempotency',
                 'reservations', 'enquiries', 'staff', 'catalogue', 'workspaces']:
        op.execute(f'DROP TABLE {name}')
