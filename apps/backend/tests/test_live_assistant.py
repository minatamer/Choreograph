"""Exact live SDK/composition path with injected HTTP and isolated PostgreSQL only."""
import json
import re
from dataclasses import replace
from datetime import datetime, timedelta
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from test_ai_config import live_values
from test_requests import NOW, command

from choreograph import assistant, knowledge, service
from choreograph.ai_admission import AttemptScope
from choreograph.ai_config import parse_live_ai
from choreograph.api import create_app
from choreograph.assistant_context import turn_context
from choreograph.composition import compose_ai
from choreograph.errors import DomainError
from choreograph.models import AIAttempt, Enquiry, Reservation
from choreograph.persistence import Session, repo_rows
from choreograph.providers import GroundedOutput, Interpretation, parse_envelope, strict_schema
from choreograph.sessions import create_workspace


def intent(kind,**values):
    return dict(intent=kind,service=None,bedrooms=None,oven=None,requested_date=None,
                requested_time=None,guide_question=None,period=None,**values)


def envelope(value):
    return {'id':'resp_injected','object':'response','created_at':0,'status':'completed',
        'output':[{'id':'msg_injected','type':'message','role':'assistant','status':'completed',
                   'content':[{'type':'output_text','text':json.dumps(value),'annotations':[]}]}],
        'usage':{'input_tokens':10,'output_tokens':20,'total_tokens':30}}


@pytest.mark.parametrize('changes',[{'bedrooms':True},{'bedrooms':'2'},{'bedrooms':0},
    {'oven':'false'},{'guide_question':'x'*1201},{'requested_date':'2026-02-30'},
    {'requested_date':'2026-10-24T10:00:00+03:00'},{'requested_time':'25:00'},
    {'requested_time':'10:00:30'},{'period':'evening'},{'intent':'run_sql'},{'intent':'guide'}])
def test_live_interpretation_rejects_invalid_values(changes):
    with pytest.raises(DomainError) as error:
        parse_envelope(envelope({**intent('schedule'),**changes}),Interpretation)
    assert error.value.code=='ASSISTANT_FORMAT'


@pytest.mark.parametrize('broken',[None,{},[None],
    [{'type':'function_call','name':'reserve_booking','arguments':'{}'}],
    [{'type':'message','role':'user','content':[]}],
    [{'type':'message','status':'incomplete','content':[]}],
    [{'type':'message','content':[None]}]])
def test_live_envelope_rejects_unexpected_tools_roles_and_malformed_parts(broken):
    with pytest.raises(DomainError) as error:
        parse_envelope({**envelope(intent('greeting')),'output':broken},Interpretation)
    assert error.value.code=='ASSISTANT_FORMAT'


def test_strict_schema_requires_nullable_fields_and_evidence_status_is_consistent():
    for schema in [Interpretation,GroundedOutput]:
        value=strict_schema(schema)
        def check(node):
            if isinstance(node,dict):
                assert 'default' not in node
                if node.get('type')=='object':
                    assert set(node['required'])==set(node['properties'])
                    assert node['additionalProperties'] is False
                for child in node.values():check(child)
            elif isinstance(node,list):
                for child in node:check(child)
        check(value)
    for value in [{'status':'supported','claims':[]},
        {'status':'insufficient','claims':[{'passage_id':'id','excerpt':'A genuine but unrelated quote.'}]}]:
        with pytest.raises(DomainError):parse_envelope(envelope(value),GroundedOutput)


def live_runtime(database,response,*,embedding_model='operator-embedding-model'):
    engine,base=database
    values=live_values()
    for name in ['REQUESTS','INPUT_TOKENS','OUTPUT_TOKENS','VECTORS','COST_MICROS',
                 'WORKSPACE_REQUESTS','WORKSPACE_INPUT_TOKENS','WORKSPACE_OUTPUT_TOKENS',
                 'WORKSPACE_VECTORS','WORKSPACE_COST_MICROS']:
        values['CHOREOGRAPH_AI_'+name]='1000000'
    values.update(CHOREOGRAPH_AI_GRANT_ID='injected-'+str(uuid4()),CHOREOGRAPH_AI_EMBEDDING_DIMENSIONS='64',
                  CHOREOGRAPH_AI_EMBEDDING_MODEL=embedding_model)
    settings=replace(base,testing=False,profile='live',live_ai=parse_live_ai(values),crm_provider='disabled')
    embeddings=[];vectorizer=knowledge.FakeEmbedding()
    def embed(request):
        body=json.loads(request.content);embeddings.append(body)
        return httpx.Response(200,json={'object':'list','model':body['model'],
            'data':[{'object':'embedding','index':index,'embedding':vectorizer.get_text_embedding(text)}
                    for index,text in enumerate(body['input'])],
            'usage':{'prompt_tokens':1,'total_tokens':1}})
    runtime=compose_ai(settings,engine,response_transport=httpx.MockTransport(response),
        embedding_transport=httpx.MockTransport(embed),clock=lambda:NOW)
    return settings,runtime,embeddings


def test_live_composition_policy_history_preferences_review_booking_and_status(database):
    requests=[]
    def respond(request):
        body=json.loads(request.content);data=json.loads(body['input']);requests.append((body,data))
        assert str(request.url)=='https://api.openai.com/v1/responses'
        assert body['store'] is False and body['text']['format']['strict'] is True
        if body['text']['format']['name']=='GroundedOutput':
            hit=next(hit for hit in data['passages'] if 'separate safe room' in hit['text'])
            excerpt=next(sentence for sentence in re.split(r'(?<=[.!?])\s+',hit['text']) if 'separate safe room' in sentence)
            value={'status':'supported','claims':[{'passage_id':hit['id'],'excerpt':excerpt}]}
        else:
            question=data['enquiry']
            if question=='Hello':value=intent('greeting')
            elif question=='A regular clean for one bedroom. What should I do with my pets?':
                value={**intent('quote'),'service':'regular','bedrooms':1,'guide_question':'What should I do with my pets?'}
            elif question=='What about dogs?':
                assert any('pets?' in turn['text'] for turn in data['context']['recent_turns'])
                assert data['draft']['service']=='regular'
                value={**intent('guide'),'guide_question':'What should I do with my dogs during cleaning?'}
            elif question=='What morning appointments are available?':value={**intent('schedule'),'period':'morning'}
            elif question=='Book it':value=intent('review')
            elif question=='Is it booked?':
                assert data['context']['bookings'][0]['status'] in {'confirmed','cancelled'}
                value=intent('booking')
            elif question in {'Move my appointment','Cancel my appointment'}:value=intent('manage')
            else:
                assert question=='Thank you';value=intent('thanks')
        return httpx.Response(200,json=envelope(value))
    settings,runtime,embeddings=live_runtime(database,respond)
    engine,_=database;client=None
    try:
        operator=runtime.for_scope(AttemptScope(None,0,str(uuid4())))
        knowledge.prepare_pack(engine,NOW,spec=runtime.spec,embedder=operator.embedder,tokenizer=operator.tokenizer)
        prepared=len(embeddings)
        class InjectedVerification:
            def verify(self,proof,action,binding):return proof=='injected-human-proof'
        client=TestClient(create_app(settings,engine,lambda:NOW,ai_runtime=runtime,verification_provider=InjectedVerification()))
        headers={'origin':settings.origin,'x-choreograph-bridge':settings.bridge_secret,
                 'x-turnstile-token':'injected-human-proof','idempotency-key':str(uuid4())}
        state=client.post('/v1/session',headers=headers,json={'timezone':'Asia/Kathmandu'}).json()
        headers['x-csrf-token']=state['csrf'];assert len(state['documents'])==6
        assert len(embeddings)==prepared and requests==[]  # visits never pay to re-index/answer
        def send(question):
            nonlocal state
            result=command(client,headers,state,{'text':question},'/v1/chat',method='post')
            assert result.status_code==200,result.text
            state=result.json()['state'];return state['messages'][-1]
        send('Hello');reply=send('A regular clean for one bedroom. What should I do with my pets?')
        assert state['quote']['cents']==6000 and state['quote']['minutes']==90
        assert reply['claims'] and not state['requests']
        for claim in reply['claims']:
            detail=client.get('/v1/documents/'+claim['version_id'],headers=headers).json()
            assert any(row['id']==claim['passage_id'] and row['page']==claim['page'] and
                       claim['excerpt'] in row['content'] for row in detail['passages'])
        assert send('What about dogs?')['claims']
        assert send('What morning appointments are available?')['requested_period']=='morning'
        week=client.get('/v1/availability',headers=headers).json()
        slot=next(slot for day in week['days'] for slot in day['slots'])
        state=command(client,headers,state,{'preferred_at':slot['start']}).json()['state']
        assert send('Book it')['cards']==['review'] and state['requests']==[]
        result=command(client,headers,state,{'accept_quote':True},'/v1/bookings',method='post')
        assert result.status_code==200,result.text
        state=result.json()['state'];record=state['requests'][0]
        assert record['status']=='confirmed' and record['booking']['starts_at']==slot['start']
        assert send('Is it booked?')['request_id']==record['id']
        assert send('Move my appointment')['cards']==['manage']
        assert state['requests'][0]['booking']==record['booking']
        assert 'welcome' in send('Thank you')['text']
        alternatives=client.get(f"/v1/requests/{record['id']}/availability",headers=headers).json()
        candidate=next(option['start'] for day in alternatives['days'] for option in day['slots']
                       if datetime.fromisoformat(option['start'])!=datetime.fromisoformat(record['preferred_at']))
        changed=command(client,headers,state,{'request_revision':record['revision'],'confirm':True,'preferred_at':candidate},
                        f"/v1/requests/{record['id']}/reschedule",method='post')
        assert changed.status_code==200,changed.text
        state=changed.json()['state'];record=state['requests'][0]
        assert datetime.fromisoformat(state['draft']['preferred_at'])==datetime.fromisoformat(candidate)
        assert 'moved' in state['messages'][-1]['text']
        assert send('Cancel my appointment')['cards']==['manage'] and state['requests'][0]['status']=='confirmed'
        cancelled=command(client,headers,state,{'request_revision':record['revision'],'confirm':True},
                          f"/v1/requests/{record['id']}/cancel",method='post')
        assert cancelled.status_code==200,cancelled.text
        state=cancelled.json()['state'];assert state['draft']['preferred_at'] is None
        assert state['messages'][-1]['cards']==['booking'] and 'cancelled' in state['messages'][-1]['text']
        assert 'cancelled' in send('Is it booked?')['text']
        with Session(engine) as db:
            assert len(repo_rows(db, Reservation, filters={'workspace_id': state['workspace_id'], 'state': 'cancelled'}, predicate=lambda candidate: candidate.enquiry_id is not None))==1
            attempts=list(repo_rows(db, AIAttempt, filters={'grant_id': settings.live_ai.grant.grant_id}))
            assert len(attempts)==len(requests)+len(embeddings)
            assert all(row.state=='completed' for row in attempts)
        assert runtime.assistant.context=={}  # no cross-visitor mutable history
        assert len(embeddings)==prepared+2  # only the two policy questions embedded
    finally:
        if client:client.close()
        runtime.close()


def test_unprepared_live_pack_stops_before_any_provider_request(database):
    def denied(request):raise AssertionError('Missing pack must not consume a paid request')
    settings,runtime,embeddings=live_runtime(database,denied,embedding_model='unprepared-'+str(uuid4()))
    class InjectedVerification:
        def verify(self,*args):return True
    client=TestClient(create_app(settings,database[0],lambda:NOW,ai_runtime=runtime,verification_provider=InjectedVerification()))
    try:
        headers={'origin':settings.origin,'x-choreograph-bridge':settings.bridge_secret,
                 'x-turnstile-token':'injected-human-proof','idempotency-key':str(uuid4())}
        result=client.post('/v1/session',headers=headers,json={'timezone':'UTC'})
        assert result.status_code==503 and result.json()['code']=='KNOWLEDGE_NOT_READY'
        assert embeddings==[]
    finally:client.close();runtime.close()


def test_context_is_bounded_and_does_not_send_source_claims_contacts_or_ids(database):
    with Session(database[0]) as db,db.begin():
        workspace,_=create_workspace(db,'UTC',NOW)
        workspace.messages=[{'role':'user','text':'🧹'*1200,'claims':[], 'secret':'never serialize'}]*20
        context=turn_context(db,workspace);encoded=json.dumps(context)
        assert len(context['recent_turns'])<8 and len(encoded)<9000
        assert 'secret' not in encoded and 'workspace_id' not in encoded and 'csrf' not in encoded


def test_date_only_and_time_only_preferences_do_not_reuse_a_wrong_slot(database):
    with Session(database[0]) as db,db.begin():
        workspace,_=create_workspace(db,'Asia/Kathmandu',NOW);service.ensure_seeded(db,workspace,NOW)
        service.update_draft(db,workspace,{'service':'regular','bedrooms':1},workspace.revision,NOW)
        week=service.week_view(db,workspace,NOW)
        slot=next(slot for day in week['days'] for slot in day['slots'])
        service.update_draft(db,workspace,{'preferred_at':slot['start'].isoformat()},workspace.revision,NOW)
        other_date=(datetime.fromisoformat(workspace.scenario['requested_date'])+timedelta(days=1)).date().isoformat()
        assistant.apply_chat(db,workspace,'Another day',workspace.revision,NOW,
            intent=Interpretation(**{**intent('schedule'),'requested_date':other_date}),hits=[],output=None)
        assert workspace.draft['preferred_at'] is None
        assert workspace.messages[-1]['requested_date']==other_date
        service.update_draft(db,workspace,{'preferred_at':slot['start'].isoformat()},workspace.revision,NOW)
        assistant.apply_chat(db,workspace,'At another time',workspace.revision,NOW,
            intent=Interpretation(**{**intent('schedule'),'requested_time':'14:00'}),hits=[],output=None)
        assert workspace.messages[-1]['requested_date']==workspace.scenario['requested_date']
        if workspace.draft['preferred_at']:
            assert workspace.draft['preferred_at']!=slot['start'].isoformat()
        assert len(repo_rows(db, Enquiry, filters={'workspace_id': workspace.id}))==0


def test_explicit_combined_policy_request_keeps_quote_but_pure_policy_cannot_edit(database):
    provider=assistant.FakeAssistant()
    request=provider.interpret('I need a regular clean for one bedroom. What do I do with my cats?',{},'UTC','2026-10-22')
    assert request.intent=='quote' and request.guide_question
    with Session(database[0]) as db,db.begin():
        workspace,_=create_workspace(db,'UTC',NOW)
        assistant.apply_chat(db,workspace,'Quote and policy',workspace.revision,NOW,intent=request,hits=[],
                             output=GroundedOutput(status='insufficient',claims=[]))
        assert service.current_quote(workspace)['cents']==6000
        unrelated=Interpretation(**{**intent('guide'),'service':'deep','bedrooms':3,
                                    'requested_date':'2026-10-24','guide_question':'What is included in deep cleaning?'})
        assistant.apply_chat(db,workspace,'A policy question',workspace.revision,NOW,intent=unrelated,hits=[],
                             output=GroundedOutput(status='insufficient',claims=[]))
        assert service.current_quote(workspace)['cents']==6000 and not workspace.scenario.get('requested_date')


def test_date_without_time_uses_actual_day_availability_not_an_invented_morning(database):
    from choreograph import domain
    with Session(database[0]) as db,db.begin():
        workspace,_=create_workspace(db,'UTC',NOW);service.ensure_seeded(db,workspace,NOW)
        service.update_draft(db,workspace,{'service':'regular','bedrooms':1},workspace.revision,NOW)
        day=datetime.fromisoformat(workspace.scenario['alternative_date']).date()
        start=domain.local_to_utc(datetime.combine(day,datetime.min.time().replace(hour=9)),'UTC')
        for staff in domain.STAFF_IDS:
            db.add(Reservation(workspace_id=workspace.id,staff_id=staff,starts_at=start,
                ends_at=start+timedelta(hours=3),state='blocked',label='Test morning'))
        db.flush()
        assistant.apply_chat(db,workspace,'This day, please',workspace.revision,NOW,
            intent=Interpretation(**{**intent('schedule'),'requested_date':day.isoformat()}),hits=[],output=None)
        reply=workspace.messages[-1]
        assert 'Choose an available time' in reply['text'] and '09:00' not in reply['text']
        assert workspace.draft.get('preferred_at') is None
