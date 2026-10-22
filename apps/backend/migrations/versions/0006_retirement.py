"""Track completion of private local retirement without losing cleanup references."""
from alembic import op

revision='0006'
down_revision='0005'
def upgrade():op.execute('ALTER TABLE workspaces ADD COLUMN purged_at timestamptz')
def downgrade():op.execute('ALTER TABLE workspaces DROP COLUMN purged_at')
