"""Content-free once-only identities for explicitly invoked acceptance tools."""
from alembic import op

revision = '0010'
down_revision = '0009'


def upgrade():
    op.execute('''CREATE TABLE acceptance_runs(id uuid PRIMARY KEY,kind varchar(16) NOT NULL,
      config_hash varchar(64) NOT NULL,state varchar(16) NOT NULL,created_at timestamptz NOT NULL,
      finished_at timestamptz,counts jsonb NOT NULL DEFAULT '{}',workspace_ids jsonb NOT NULL DEFAULT '[]')''')


def downgrade():
    from sqlalchemy import text
    if op.get_bind().scalar(text('SELECT EXISTS(SELECT 1 FROM acceptance_runs)')):
        raise RuntimeError('ACCEPTANCE_RECEIPTS_DOWNGRADE_FORBIDDEN')
    op.execute('DROP TABLE acceptance_runs')
