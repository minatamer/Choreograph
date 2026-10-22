CREATE EXTENSION IF NOT EXISTS vector;

CREATE EXTENSION IF NOT EXISTS btree_gist;


CREATE TABLE catalogue (
	id VARCHAR(40) NOT NULL, 
	version INTEGER NOT NULL, 
	rules JSONB NOT NULL, 
	PRIMARY KEY (id)
)

;


CREATE TABLE crm_installations (
	app_id VARCHAR(80) NOT NULL, 
	account_id VARCHAR(80) NOT NULL, 
	state VARCHAR(24) NOT NULL, 
	checked_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (app_id, account_id)
)

;


CREATE TABLE workspaces (
	id UUID NOT NULL, 
	session_hash VARCHAR(64) NOT NULL, 
	timezone VARCHAR(80) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	active BOOLEAN NOT NULL, 
	generation INTEGER NOT NULL, 
	revision INTEGER NOT NULL, 
	seeded BOOLEAN NOT NULL, 
	draft JSONB NOT NULL, 
	messages JSONB NOT NULL, 
	crm_mode VARCHAR(24) NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (expires_at > created_at), 
	CHECK (generation > 0), 
	UNIQUE (session_hash)
)

;

CREATE INDEX ix_workspaces_expires_at ON workspaces (expires_at);


CREATE TABLE activity (
	workspace_id UUID NOT NULL, 
	id UUID NOT NULL, 
	kind VARCHAR(40) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	reference VARCHAR(64) NOT NULL, 
	PRIMARY KEY (workspace_id, id), 
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE
)

;


CREATE TABLE crm_connections (
	workspace_id UUID NOT NULL, 
	id UUID NOT NULL, 
	account_id VARCHAR(80) NOT NULL, 
	generation INTEGER NOT NULL, 
	state VARCHAR(24) NOT NULL, 
	provider VARCHAR(24) NOT NULL, 
	encrypted_tokens BYTEA, 
	export_consent BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (workspace_id, id), 
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE
)

;


CREATE TABLE document_versions (
	id UUID NOT NULL, 
	owner_id UUID, 
	generation INTEGER NOT NULL, 
	slot VARCHAR(50) NOT NULL, 
	title VARCHAR(120) NOT NULL, 
	version VARCHAR(40) NOT NULL, 
	media_type VARCHAR(80) NOT NULL, 
	source BYTEA NOT NULL, 
	sha256 VARCHAR(64) NOT NULL, 
	page_count INTEGER NOT NULL, 
	state VARCHAR(24) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (octet_length(source) <= 2097152), 
	CHECK (page_count BETWEEN 1 AND 10), 
	FOREIGN KEY(owner_id) REFERENCES workspaces (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_document_versions_owner_id ON document_versions (owner_id);


CREATE TABLE enquiries (
	workspace_id UUID NOT NULL, 
	id UUID NOT NULL, 
	revision INTEGER NOT NULL, 
	status VARCHAR(24) NOT NULL, 
	fields JSONB NOT NULL, 
	quote JSONB NOT NULL, 
	preferred_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (workspace_id, id), 
	CHECK (revision > 0), 
	CHECK (status IN ('awaiting_review','confirmed','cancelled','completed')), 
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE
)

;


CREATE TABLE idempotency (
	workspace_id UUID NOT NULL, 
	key VARCHAR(64) NOT NULL, 
	operation VARCHAR(40) NOT NULL, 
	request_hash VARCHAR(64) NOT NULL, 
	result JSONB NOT NULL, 
	PRIMARY KEY (workspace_id, key), 
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE
)

;


CREATE TABLE oauth_states (
	state_hash VARCHAR(64) NOT NULL, 
	workspace_id UUID NOT NULL, 
	generation INTEGER NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	used BOOLEAN NOT NULL, 
	PRIMARY KEY (state_hash), 
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE
)

;


CREATE TABLE staff (
	workspace_id UUID NOT NULL, 
	id VARCHAR(20) NOT NULL, 
	name VARCHAR(40) NOT NULL, 
	PRIMARY KEY (workspace_id, id), 
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE
)

;


CREATE TABLE document_manifest (
	workspace_id UUID NOT NULL, 
	slot VARCHAR(50) NOT NULL, 
	version_id UUID NOT NULL, 
	PRIMARY KEY (workspace_id, slot), 
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE, 
	FOREIGN KEY(version_id) REFERENCES document_versions (id)
)

;


CREATE TABLE external_mappings (
	workspace_id UUID NOT NULL, 
	connection_id UUID NOT NULL, 
	enquiry_id UUID NOT NULL, 
	account_id VARCHAR(80) NOT NULL, 
	revision INTEGER NOT NULL, 
	contact_id VARCHAR(80), 
	deal_id VARCHAR(80), 
	state VARCHAR(24) NOT NULL, 
	verified BOOLEAN NOT NULL, 
	PRIMARY KEY (workspace_id, connection_id, enquiry_id), 
	FOREIGN KEY(workspace_id, connection_id) REFERENCES crm_connections (workspace_id, id) ON DELETE CASCADE, 
	FOREIGN KEY(workspace_id, enquiry_id) REFERENCES enquiries (workspace_id, id) ON DELETE CASCADE
)

;


CREATE TABLE knowledge_chunks (
	id UUID NOT NULL, 
	version_id UUID NOT NULL, 
	page INTEGER NOT NULL, 
	section VARCHAR(180) NOT NULL, 
	content TEXT NOT NULL, 
	embedding VECTOR(64) NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (page BETWEEN 1 AND 10), 
	CHECK (length(content) <= 6000), 
	FOREIGN KEY(version_id) REFERENCES document_versions (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_knowledge_chunks_version_id ON knowledge_chunks (version_id);


CREATE TABLE outbox (
	workspace_id UUID NOT NULL, 
	id UUID NOT NULL, 
	enquiry_id UUID, 
	connection_id UUID, 
	account_id VARCHAR(80), 
	connection_generation INTEGER, 
	workspace_generation INTEGER NOT NULL, 
	revision INTEGER NOT NULL, 
	kind VARCHAR(40) NOT NULL, 
	state VARCHAR(24) NOT NULL, 
	attempts INTEGER NOT NULL, 
	due_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	lease_until TIMESTAMP WITH TIME ZONE, 
	lease_token UUID, 
	code VARCHAR(40), 
	PRIMARY KEY (workspace_id, id), 
	FOREIGN KEY(workspace_id, enquiry_id) REFERENCES enquiries (workspace_id, id) ON DELETE CASCADE, 
	FOREIGN KEY(workspace_id, connection_id) REFERENCES crm_connections (workspace_id, id) ON DELETE CASCADE, 
	UNIQUE (workspace_id, enquiry_id, revision, connection_id, kind), 
	CHECK (attempts BETWEEN 0 AND 5), 
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_outbox_due_at ON outbox (due_at);

CREATE INDEX ix_outbox_state ON outbox (state);


CREATE TABLE reservations (
	workspace_id UUID NOT NULL, 
	id UUID NOT NULL, 
	staff_id VARCHAR(20) NOT NULL, 
	enquiry_id UUID, 
	starts_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	ends_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	period TSTZRANGE GENERATED ALWAYS AS (tstzrange(starts_at, ends_at, '[)')) STORED NOT NULL, 
	state VARCHAR(24) NOT NULL, 
	label VARCHAR(60) NOT NULL, 
	PRIMARY KEY (workspace_id, id), 
	FOREIGN KEY(workspace_id, staff_id) REFERENCES staff (workspace_id, id) ON DELETE CASCADE, 
	FOREIGN KEY(workspace_id, enquiry_id) REFERENCES enquiries (workspace_id, id) ON DELETE CASCADE, 
	UNIQUE (workspace_id, enquiry_id), 
	CHECK (ends_at > starts_at), 
	CHECK (state IN ('confirmed','blocked','completed','cancelled')), 
	CONSTRAINT reservation_no_overlap EXCLUDE USING gist (workspace_id WITH =, staff_id WITH =, period WITH &&) WHERE (state IN ('confirmed','blocked','completed')), 
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_reservations_starts_at ON reservations (starts_at);
