"""A persistent fake external CRM for local replay/recovery acceptance."""
from alembic import op

revision='0005'
down_revision='0004'


def upgrade():
    op.execute("ALTER TABLE outbox ADD COLUMN payload jsonb NOT NULL DEFAULT '{}'::jsonb")
    op.execute("ALTER TABLE oauth_states ADD COLUMN outcome varchar(24) NOT NULL DEFAULT 'pending'")
    op.execute('''CREATE TABLE simulated_crm_records (
      account_id varchar(80) NOT NULL,object_type varchar(20) NOT NULL,external_key varchar(64) NOT NULL,
      id varchar(80) NOT NULL UNIQUE,properties jsonb NOT NULL,archived boolean NOT NULL DEFAULT false,
      PRIMARY KEY(account_id,object_type,external_key))''')


def downgrade():
    op.execute('DROP TABLE simulated_crm_records')
    op.execute('ALTER TABLE outbox DROP COLUMN payload')
    op.execute('ALTER TABLE oauth_states DROP COLUMN outcome')
