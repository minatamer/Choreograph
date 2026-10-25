"""Local operator-only aggregates. No public endpoint or account/token details."""
import json

from .models import Connection, Installation, OAuthState, Outbox


def summary(db,app_id='choreograph-local-simulation'):
    from collections import Counter

    from .persistence import repo_rows
    connections={(row.workspace_id,row.id) for row in repo_rows(db,Connection,filters={'app_id':app_id})}
    return {'installations':dict(Counter(row.state for row in repo_rows(db,Installation,filters={'app_id':app_id}))),
            'oauth_outcomes':dict(Counter(row.outcome for row in repo_rows(db,OAuthState,filters={'app_id':app_id}))),
            'work':dict(Counter(row.state for row in repo_rows(db,Outbox,
                predicate=lambda row:(row.workspace_id,row.connection_id) in connections)))}


if __name__=='__main__':
    from .db import build_engine
    from .persistence import Session
    from .settings import load_local
    settings=load_local();engine=build_engine(settings)
    try:
        app_id=settings.live_crm.transport.app_id if settings.live_crm else ('disabled' if settings.crm_provider=='disabled' else 'choreograph-local-simulation')
        with Session(engine) as db:print(json.dumps(summary(db,app_id)))
    finally:engine.dispose()
