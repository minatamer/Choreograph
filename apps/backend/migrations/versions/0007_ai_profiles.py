"""Preserve fake vectors while adding immutable profiles and durable AI admission."""
import hashlib
import json

from alembic import op
from sqlalchemy import text

revision = '0007'
down_revision = '0006'


def identity(model, chunker):
    values = dict(provider='fake', model=model, dimensions=64, chunker=chunker, tokenizer='whitespace-v1')
    return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(',', ':')).encode()).hexdigest(), values


def upgrade():
    connection = op.get_bind()
    connection.exec_driver_sql('''
    CREATE TABLE embedding_profiles (id varchar(64) PRIMARY KEY, provider varchar(16) NOT NULL,
      model varchar(100) NOT NULL, dimensions integer NOT NULL CHECK(dimensions BETWEEN 1 AND 3072),
      chunker varchar(100) NOT NULL, tokenizer varchar(100) NOT NULL CHECK(provider IN ('fake','openai')));
    ALTER TABLE workspaces ADD COLUMN embedding_profile_id varchar(64) REFERENCES embedding_profiles(id);
    ALTER TABLE document_versions ADD COLUMN embedding_profile_id varchar(64) REFERENCES embedding_profiles(id);
    ALTER TABLE knowledge_chunks ALTER COLUMN embedding TYPE vector;
    ALTER TABLE document_versions ALTER COLUMN embedding_model TYPE varchar(100);
    ALTER TABLE document_versions ALTER COLUMN chunker_version TYPE varchar(100);
    ''')
    profiles = list(connection.execute(text('SELECT DISTINCT embedding_model,chunker_version FROM document_versions')))
    profiles.append(('fake-hash-64-v2', 'llama-token-section-v3'))
    profiles.append(('legacy-mixed-fake64', 'legacy-mixed'))
    for model, chunker in profiles:
        key, values = identity(model, chunker)
        connection.execute(text('INSERT INTO embedding_profiles VALUES (:id,:provider,:model,:dimensions,:chunker,:tokenizer) '
                                'ON CONFLICT DO NOTHING'), dict(id=key, **values))
        connection.execute(text('UPDATE document_versions SET embedding_profile_id=:id '
                                'WHERE embedding_model=:model AND chunker_version=:chunker'),
                           dict(id=key, model=model, chunker=chunker))
    default, _ = identity('fake-hash-64-v2', 'llama-token-section-v3')
    mixed, _ = identity('legacy-mixed-fake64', 'legacy-mixed')
    connection.execute(text('''UPDATE workspaces w SET embedding_profile_id=COALESCE(
      (SELECT CASE WHEN count(DISTINCT d.embedding_profile_id)=1 THEN min(d.embedding_profile_id)
                   WHEN count(DISTINCT d.embedding_profile_id)>1 THEN :mixed END
       FROM document_manifest m JOIN document_versions d ON d.id=m.version_id WHERE m.workspace_id=w.id),:default)'''),
                       dict(mixed=mixed, default=default))
    connection.exec_driver_sql(f'''
    ALTER TABLE workspaces ALTER COLUMN embedding_profile_id SET NOT NULL;
    ALTER TABLE workspaces ALTER COLUMN embedding_profile_id SET DEFAULT '{default}';
    ALTER TABLE document_versions ALTER COLUMN embedding_profile_id SET NOT NULL;
    ALTER TABLE document_versions ALTER COLUMN embedding_profile_id SET DEFAULT '{default}';
    DROP INDEX sample_document_identity;
    CREATE UNIQUE INDEX sample_document_identity ON document_versions(slot,sha256,embedding_profile_id) WHERE owner_id IS NULL;
    CREATE TABLE ai_grants (id varchar(80) PRIMARY KEY, spec_hash varchar(64) NOT NULL, spec jsonb NOT NULL,
      expires_at timestamptz NOT NULL, blocked boolean NOT NULL DEFAULT false,
      requests bigint NOT NULL DEFAULT 0, input_tokens bigint NOT NULL DEFAULT 0,
      output_tokens bigint NOT NULL DEFAULT 0, vectors bigint NOT NULL DEFAULT 0, cost_micros bigint NOT NULL DEFAULT 0);
    CREATE TABLE ai_attempts (id uuid PRIMARY KEY, grant_id varchar(80) NOT NULL REFERENCES ai_grants(id),
      workspace_id uuid REFERENCES workspaces(id) ON DELETE CASCADE, scope_key varchar(40) NOT NULL,
      generation integer NOT NULL, command_key varchar(36) NOT NULL, phase varchar(24) NOT NULL,
      batch integer NOT NULL, model varchar(100) NOT NULL, state varchar(16) NOT NULL,
      lease_until timestamptz NOT NULL, lease_token uuid NOT NULL, input_tokens bigint NOT NULL,
      output_tokens bigint NOT NULL, vectors bigint NOT NULL, cost_micros bigint NOT NULL,
      actual_input_tokens bigint, actual_output_tokens bigint, reference varchar(100),
      UNIQUE(scope_key,generation,command_key,phase,batch));
    CREATE INDEX ix_ai_attempts_lease_until ON ai_attempts(lease_until);
    CREATE TABLE ai_interactions (id uuid PRIMARY KEY, workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
      generation integer NOT NULL, revision integer NOT NULL, command_key varchar(36) NOT NULL,
      request_hash varchar(64) NOT NULL, operation varchar(16) NOT NULL, profile_id varchar(64) NOT NULL,
      manifest_ids jsonb NOT NULL, state varchar(16) NOT NULL, lease_until timestamptz NOT NULL,
      UNIQUE(workspace_id,generation,command_key));
    CREATE INDEX ix_ai_interactions_workspace_id ON ai_interactions(workspace_id);
    CREATE INDEX ix_ai_interactions_lease_until ON ai_interactions(lease_until);
    CREATE FUNCTION guard_embedding_profile() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
      RAISE EXCEPTION 'EMBEDDING_PROFILE_IMMUTABLE' USING ERRCODE='23514'; END $$;
    CREATE TRIGGER embedding_profile_immutable BEFORE UPDATE ON embedding_profiles
      FOR EACH ROW EXECUTE FUNCTION guard_embedding_profile();
    CREATE FUNCTION guard_workspace_profile() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
      IF NEW.embedding_profile_id IS DISTINCT FROM OLD.embedding_profile_id THEN
        RAISE EXCEPTION 'EMBEDDING_PROFILE_IMMUTABLE' USING ERRCODE='23514'; END IF; RETURN NEW; END $$;
    CREATE TRIGGER workspace_profile_immutable BEFORE UPDATE ON workspaces
      FOR EACH ROW EXECUTE FUNCTION guard_workspace_profile();
    CREATE FUNCTION guard_chunk_profile() RETURNS trigger LANGUAGE plpgsql AS $$ DECLARE dimensions integer; BEGIN
      SELECT p.dimensions INTO dimensions FROM document_versions d JOIN embedding_profiles p
        ON p.id=d.embedding_profile_id WHERE d.id=NEW.version_id;
      IF dimensions IS NULL OR vector_dims(NEW.embedding)<>dimensions THEN
        RAISE EXCEPTION 'EMBEDDING_DIMENSIONS_INVALID' USING ERRCODE='23514'; END IF; RETURN NEW; END $$;
    CREATE TRIGGER chunk_profile_scope BEFORE INSERT OR UPDATE ON knowledge_chunks
      FOR EACH ROW EXECUTE FUNCTION guard_chunk_profile();
    CREATE OR REPLACE FUNCTION guard_document_manifest() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE d record; w record; BEGIN
      SELECT v.*,p.provider,p.dimensions INTO d FROM document_versions v JOIN embedding_profiles p
        ON p.id=v.embedding_profile_id WHERE v.id=NEW.version_id FOR SHARE OF v;
      SELECT s.*,p.model INTO w FROM workspaces s JOIN embedding_profiles p ON p.id=s.embedding_profile_id
        WHERE s.id=NEW.workspace_id;
      IF d.id IS NULL OR w.id IS NULL OR (d.owner_id IS NOT NULL AND d.owner_id<>NEW.workspace_id)
        OR d.slot<>NEW.slot OR d.state<>'ready'
        OR (d.embedding_profile_id<>w.embedding_profile_id AND NOT
            (w.model='legacy-mixed-fake64' AND d.provider='fake' AND d.dimensions=64)) THEN
        RAISE EXCEPTION 'DOCUMENT_SCOPE_INVALID' USING ERRCODE='23503'; END IF; RETURN NEW; END $$;
    CREATE OR REPLACE FUNCTION guard_document_identity() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
      IF NEW.owner_id IS DISTINCT FROM OLD.owner_id OR NEW.slot<>OLD.slot
        OR NEW.embedding_profile_id<>OLD.embedding_profile_id OR NEW.embedding_model<>OLD.embedding_model
        OR NEW.chunker_version<>OLD.chunker_version
        OR (OLD.state='ready' AND (NEW.source IS DISTINCT FROM OLD.source OR NEW.sha256<>OLD.sha256
            OR NEW.title<>OLD.title OR NEW.version<>OLD.version OR NEW.media_type<>OLD.media_type
            OR NEW.page_count<>OLD.page_count OR NEW.generation<>OLD.generation))
        OR (NEW.state<>'ready' AND EXISTS(SELECT 1 FROM document_manifest WHERE version_id=OLD.id)) THEN
        RAISE EXCEPTION 'DOCUMENT_IDENTITY_IMMUTABLE' USING ERRCODE='23514'; END IF; RETURN NEW; END $$;
    ''')


def downgrade():
    connection = op.get_bind()
    # A rollback cannot truncate paid vectors or collapse parallel sample spaces.
    if connection.scalar(text("SELECT EXISTS(SELECT 1 FROM embedding_profiles p JOIN document_versions d "
                              "ON d.embedding_profile_id=p.id WHERE p.provider<>'fake' OR p.dimensions<>64)")):
        raise RuntimeError('LIVE_VECTOR_DOWNGRADE_FORBIDDEN')
    if connection.scalar(text('SELECT EXISTS(SELECT 1 FROM document_versions WHERE owner_id IS NULL '
                              'GROUP BY slot,sha256 HAVING count(*)>1)')):
        raise RuntimeError('PROFILE_COLLAPSE_DOWNGRADE_FORBIDDEN')
    connection.exec_driver_sql('''
    DROP TABLE ai_interactions,ai_attempts,ai_grants;
    DROP TRIGGER chunk_profile_scope ON knowledge_chunks;
    DROP FUNCTION guard_chunk_profile();
    DROP TRIGGER workspace_profile_immutable ON workspaces;
    DROP FUNCTION guard_workspace_profile();
    DROP TRIGGER embedding_profile_immutable ON embedding_profiles;
    DROP FUNCTION guard_embedding_profile();
    CREATE OR REPLACE FUNCTION guard_document_manifest() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE version_owner uuid; version_slot text; version_state text; BEGIN
      SELECT owner_id,slot,state INTO version_owner,version_slot,version_state FROM document_versions
        WHERE id=NEW.version_id FOR SHARE;
      IF NOT FOUND OR (version_owner IS NOT NULL AND version_owner<>NEW.workspace_id)
        OR version_slot<>NEW.slot OR version_state<>'ready' THEN
        RAISE EXCEPTION 'DOCUMENT_SCOPE_INVALID' USING ERRCODE='23503'; END IF; RETURN NEW; END $$;
    CREATE OR REPLACE FUNCTION guard_document_identity() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
      IF NEW.owner_id IS DISTINCT FROM OLD.owner_id OR NEW.slot<>OLD.slot OR
        (NEW.state<>'ready' AND EXISTS(SELECT 1 FROM document_manifest WHERE version_id=OLD.id)) THEN
        RAISE EXCEPTION 'DOCUMENT_IDENTITY_IMMUTABLE' USING ERRCODE='23514'; END IF; RETURN NEW; END $$;
    DROP INDEX sample_document_identity;
    CREATE UNIQUE INDEX sample_document_identity ON document_versions(slot,sha256) WHERE owner_id IS NULL;
    ALTER TABLE knowledge_chunks ALTER COLUMN embedding TYPE vector(64);
    ALTER TABLE document_versions DROP COLUMN embedding_profile_id;
    ALTER TABLE workspaces DROP COLUMN embedding_profile_id;
    DROP TABLE embedding_profiles;
    ''')
