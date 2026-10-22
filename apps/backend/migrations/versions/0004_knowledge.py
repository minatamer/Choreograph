"""Record bounded document admission and reproducible embedding provenance."""
from alembic import op

revision='0004'
down_revision='0003'


def upgrade():
    op.execute("ALTER TABLE workspaces ADD COLUMN ingestion_attempts integer NOT NULL DEFAULT 0 CHECK (ingestion_attempts BETWEEN 0 AND 3)")
    op.execute("ALTER TABLE document_versions ADD COLUMN embedding_model varchar(80) NOT NULL DEFAULT 'fake-hash-64-v1'")
    op.execute("ALTER TABLE document_versions ADD COLUMN chunker_version varchar(80) NOT NULL DEFAULT 'llama-token-page-v1'")
    op.execute("CREATE UNIQUE INDEX sample_document_identity ON document_versions(slot,sha256) WHERE owner_id IS NULL")


def downgrade():
    op.execute('DROP INDEX sample_document_identity')
    op.execute('ALTER TABLE document_versions DROP COLUMN chunker_version, DROP COLUMN embedding_model')
    op.execute('ALTER TABLE workspaces DROP COLUMN ingestion_attempts')
