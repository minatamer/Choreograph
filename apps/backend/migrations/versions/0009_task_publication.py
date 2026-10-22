"""Durable task publication/reconciliation and unattended caller heartbeat."""
from alembic import op

revision = '0009'
down_revision = '0008'


def upgrade():
    op.execute('''
    CREATE TABLE task_publications(workspace_id uuid NOT NULL,event_id uuid NOT NULL,target_hash varchar(64) NOT NULL,
      epoch integer NOT NULL DEFAULT 0 CHECK(epoch BETWEEN 0 AND 120),name varchar(500) NOT NULL,state varchar(24) NOT NULL,
      attempts integer NOT NULL DEFAULT 0 CHECK(attempts BETWEEN 0 AND 120),next_check timestamptz NOT NULL,
      lease_until timestamptz,lease_token uuid,code varchar(40),PRIMARY KEY(workspace_id,event_id),
      FOREIGN KEY(workspace_id,event_id) REFERENCES outbox(workspace_id,id) ON DELETE CASCADE);
    CREATE INDEX ix_task_publications_next_check ON task_publications(next_check);
    CREATE TABLE dispatcher_heartbeats(id varchar(40) PRIMARY KEY,instance uuid NOT NULL,attempted_at timestamptz NOT NULL,
      succeeded_at timestamptz,cycles bigint NOT NULL DEFAULT 0,published bigint NOT NULL DEFAULT 0,code varchar(40));
    ''')


def downgrade():
    from sqlalchemy import text
    if op.get_bind().scalar(text("SELECT EXISTS(SELECT 1 FROM task_publications WHERE state NOT IN ('retired','attention'))")):
        raise RuntimeError('ACTIVE_PUBLICATION_DOWNGRADE_FORBIDDEN')
    op.execute('DROP TABLE task_publications,dispatcher_heartbeats')
