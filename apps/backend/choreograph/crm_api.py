from fastapi import Depends, Request

from . import crm, service
from .contracts import Command, CRMConsent, CRMFinish, CRMSetup, MutationView, OAuthCallback


def register(app):
    dependency=Depends(app.state.unit_of_work,scope='function')
    def run(action,body,request,db,apply):
        workspace,token=app.state.authorize(request,db,body)
        payload=body.model_dump(mode='json')
        if action=='callback':payload.pop('revision',None)
        result=service.idempotent(db,workspace,request.headers.get('idempotency-key'),'crm-'+action,payload,lambda:apply(workspace))
        return MutationView(state=app.state.full_view(db,workspace,token),**result)
    @app.post('/v1/crm/connect',response_model=MutationView)
    def connect(body:Command,request:Request,db=dependency):
        return run('connect',body,request,db,lambda ws:crm.begin(db,ws,body.revision,app.state.crm,app.state.clock()))
    @app.post('/v1/crm/callback',response_model=MutationView)
    def callback(body:OAuthCallback,request:Request,db=dependency):
        return run('callback',body,request,db,lambda ws:crm.callback(db,ws,body,app.state.crm,app.state.settings.token_key,app.state.clock()))
    @app.post('/v1/crm/consent',response_model=MutationView)
    def consent(body:CRMConsent,request:Request,db=dependency):
        return run('consent',body,request,db,lambda ws:crm.consent(db,ws,body,app.state.crm,now=app.state.clock()))
    @app.post('/v1/crm/setup',response_model=MutationView)
    def setup(body:CRMSetup,request:Request,db=dependency):
        return run('setup',body,request,db,lambda ws:crm.setup_destination(db,ws,body,app.state.crm,
            app.state.settings.token_key,app.state.clock()))
    @app.post('/v1/crm/skip',response_model=MutationView)
    @app.post('/v1/crm/disconnect',response_model=MutationView)
    def skip(body:Command,request:Request,db=dependency):
        return run('skip',body,request,db,lambda ws:crm.detach(db,ws,body.revision))
    @app.post('/v1/crm/finish',response_model=MutationView)
    def finish(body:CRMFinish,request:Request,db=dependency):
        return run('finish',body,request,db,lambda ws:crm.finish(db,ws,body,app.state.clock()))
