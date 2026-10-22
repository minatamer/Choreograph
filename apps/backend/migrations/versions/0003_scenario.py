from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE workspaces ADD COLUMN scenario jsonb NOT NULL DEFAULT '{}'::jsonb")


def downgrade():
    op.execute('ALTER TABLE workspaces DROP COLUMN scenario')
