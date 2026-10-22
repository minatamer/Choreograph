"""Local operator-only aggregates. No public endpoint or account/token details."""
import json

from sqlalchemy import func, select

from .models import Connection, Installation, OAuthState, Outbox


def summary(db,app_id='choreograph-local-simulation'):
    return {'installations':dict(db.execute(select(Installation.state,func.count()).where(
                Installation.app_id==app_id).group_by(Installation.state)).all()),
            'oauth_outcomes':dict(db.execute(select(OAuthState.outcome,func.count()).where(
                OAuthState.app_id==app_id).group_by(OAuthState.outcome)).all()),
            'work':dict(db.execute(select(Outbox.state,func.count()).join(Connection,
                (Connection.workspace_id==Outbox.workspace_id)&(Connection.id==Outbox.connection_id)).where(
                Connection.app_id==app_id).group_by(Outbox.state)).all())}


if __name__=='__main__':
    from sqlalchemy.orm import Session

    from .db import build_engine
    from .settings import load_local
    settings=load_local();engine=build_engine(settings)
    try:
        app_id=settings.live_crm.transport.app_id if settings.live_crm else ('disabled' if settings.crm_provider=='disabled' else 'choreograph-local-simulation')
        with Session(engine) as db:print(json.dumps(summary(db,app_id)))
    finally:engine.dispose()
