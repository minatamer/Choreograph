"""Bind visitor tokens to their app and persist finite CRM request admission."""
from alembic import op

revision = '0008'
down_revision = '0007'


def upgrade():
    op.execute('''
    ALTER TABLE crm_connections ADD COLUMN app_id varchar(80) NOT NULL DEFAULT 'choreograph-local-simulation';
    ALTER TABLE crm_connections ADD COLUMN destination jsonb NOT NULL DEFAULT '{}';
    ALTER TABLE crm_connections ADD COLUMN destination_options jsonb NOT NULL DEFAULT '[]';
    UPDATE crm_connections SET app_id='legacy-unverified',state='needs_attention',export_consent=false WHERE provider<>'fake';
    ALTER TABLE oauth_states ADD COLUMN provider varchar(24) NOT NULL DEFAULT 'fake';
    ALTER TABLE oauth_states ADD COLUMN app_id varchar(80) NOT NULL DEFAULT 'choreograph-local-simulation';
    CREATE TABLE crm_http_grants(id varchar(80) PRIMARY KEY,app_id varchar(80) NOT NULL,
      spec_hash varchar(64) NOT NULL,requests bigint NOT NULL DEFAULT 0 CHECK(requests>=0));
    CREATE TABLE crm_http_calls(id uuid PRIMARY KEY,grant_id varchar(80) NOT NULL REFERENCES crm_http_grants(id),
      scope_key varchar(36) NOT NULL,created_at timestamptz NOT NULL);
    CREATE INDEX ix_crm_http_calls_grant_id ON crm_http_calls(grant_id);
    CREATE INDEX ix_crm_http_calls_scope_key ON crm_http_calls(scope_key);
    CREATE FUNCTION guard_crm_app_identity() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
      IF NEW.app_id<>OLD.app_id OR NEW.provider<>OLD.provider OR NEW.account_id<>OLD.account_id THEN
        RAISE EXCEPTION 'CRM_IDENTITY_IMMUTABLE' USING ERRCODE='23514'; END IF;
      IF NEW.destination IS DISTINCT FROM OLD.destination AND NEW.generation<=OLD.generation THEN
        RAISE EXCEPTION 'CRM_DESTINATION_GENERATION_REQUIRED' USING ERRCODE='23514'; END IF;
      RETURN NEW; END $$;
    CREATE TRIGGER crm_app_identity_immutable BEFORE UPDATE ON crm_connections
      FOR EACH ROW EXECUTE FUNCTION guard_crm_app_identity();
    ''')


def downgrade():
    # Rolling back a live destination/app fence could expose tokens to the wrong
    # transport. An operator must finish/retire those connections first.
    from sqlalchemy import text
    if op.get_bind().scalar(text("SELECT EXISTS(SELECT 1 FROM crm_connections WHERE provider<>'fake' AND encrypted_tokens IS NOT NULL)")):
        raise RuntimeError('LIVE_CRM_DOWNGRADE_FORBIDDEN')
    op.execute('''
    DROP TRIGGER crm_app_identity_immutable ON crm_connections;
    DROP FUNCTION guard_crm_app_identity();
    DROP TABLE crm_http_calls,crm_http_grants;
    ALTER TABLE oauth_states DROP COLUMN app_id,DROP COLUMN provider;
    ALTER TABLE crm_connections DROP COLUMN app_id,DROP COLUMN destination,DROP COLUMN destination_options;
    ''')
