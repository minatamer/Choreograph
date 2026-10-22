"""Keep private document manifests scoped even through direct database writes."""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().exec_driver_sql("""
    CREATE FUNCTION guard_document_manifest() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE version_owner uuid; version_slot text; version_state text;
    BEGIN
      SELECT owner_id, slot, state INTO version_owner, version_slot, version_state
        FROM document_versions WHERE id = NEW.version_id FOR SHARE;
      IF NOT FOUND OR (version_owner IS NOT NULL AND version_owner <> NEW.workspace_id)
        OR version_slot <> NEW.slot OR version_state <> 'ready' THEN
        RAISE EXCEPTION 'DOCUMENT_SCOPE_INVALID' USING ERRCODE = '23503';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER document_manifest_scope BEFORE INSERT OR UPDATE ON document_manifest
      FOR EACH ROW EXECUTE FUNCTION guard_document_manifest();
    CREATE FUNCTION guard_document_identity() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF NEW.owner_id IS DISTINCT FROM OLD.owner_id OR NEW.slot <> OLD.slot OR
         (NEW.state <> 'ready' AND EXISTS (SELECT 1 FROM document_manifest WHERE version_id = OLD.id)) THEN
        RAISE EXCEPTION 'DOCUMENT_IDENTITY_IMMUTABLE' USING ERRCODE = '23514';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER document_identity BEFORE UPDATE ON document_versions
      FOR EACH ROW EXECUTE FUNCTION guard_document_identity();
    """)


def downgrade():
    op.execute('DROP TRIGGER document_identity ON document_versions')
    op.execute('DROP TRIGGER document_manifest_scope ON document_manifest')
    op.execute('DROP FUNCTION guard_document_identity()')
    op.execute('DROP FUNCTION guard_document_manifest()')
