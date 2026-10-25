"""Represent local owner manual AI policy without an invented expiry."""
from alembic import op
from sqlalchemy import text

revision = '0011'
down_revision = '0010'


def upgrade():
    op.alter_column('ai_grants', 'expires_at', nullable=True)


def downgrade():
    if op.get_bind().scalar(text('SELECT EXISTS(SELECT 1 FROM ai_grants WHERE expires_at IS NULL)')):
        raise RuntimeError('MANUAL_AI_POLICY_DOWNGRADE_FORBIDDEN')
    op.alter_column('ai_grants', 'expires_at', nullable=False)
