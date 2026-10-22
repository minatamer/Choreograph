import json
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from test_requests import NOW, begin, command

from choreograph import assistant, knowledge
from choreograph.api import create_app
from choreograph.errors import DomainError
from choreograph.providers import GroundedOutput, Interpretation, OpenAITransport, parse_envelope


def setup_pack(database):
    with Session(database[0]) as db,db.begin():knowledge.prepare_samples(db,NOW)


def send(c,h,s,text):
    result=command(c,h,s,{'text':text},'/v1/chat',method='post')
    assert result.status_code==200,result.text
    return result.json()['state']


def test_guided_busy_sources_context_correction_and_booking_authority(database):
    setup_pack(database);c,h,s=begin(database,'Africa/Cairo')
    try:
        s=send(c,h,s,f"I’m moving out of my two-bedroom apartment on {s['scenario']['busy_date']} at 09:00. Does that include carpet shampooing? I have two cats. Can you do the oven too?")
        assert s['quote']['cents']==18500 and s['quote']['minutes']==270
        reply=s['messages'][-1]
        assert 'occupied' in reply['text'] and 'week' in reply['cards'] and not s['requests']
        assert any('Carpet shampooing' in p['excerpt'] and p['page']==2 for p in reply['claims'])
        assert any('separate safe room' in p['excerpt'] and p['page']==1 for p in reply['claims'])
        for claim in reply['claims']:
            detail=c.get(f"/v1/documents/{claim['version_id']}",headers=h).json()
            passage=next(p for p in detail['passages'] if p['id']==claim['passage_id'])
            assert claim['excerpt'] in passage['content']
        s=send(c,h,s,'What cleaning supplies and equipment do you bring?')
        assert s['quote']['cents']==18500 and s['draft']['service']=='move-out'
        assert any('Juniper brings' in p['excerpt'] for p in s['messages'][-1]['claims'])
        s=send(c,h,s,'When is this service free this week?')
        assert 'week' in s['messages'][-1]['cards']
        week=c.get('/v1/availability?week='+s['scenario']['week_start'],headers=h).json()
        slot=next(d['slots'][0]['start'] for d in week['days'] if d['date']==s['scenario']['alternative_date'])
        s=command(c,h,s,{'preferred_at':slot}).json()['state']
        s=send(c,h,s,'Remove the oven.')
        assert s['quote']['cents']==16000 and not s['draft']['oven'] and s['draft']['preferred_at'] is None
        s=send(c,h,s,'Can you confirm my booking?')
        assert not s['requests'] and 'review' in s['messages'][-1]['text']
        assert c.get('/v1/session',headers=h).json()['messages']==s['messages']
    finally:c.close()


def test_open_week_and_incomplete_request_keep_local_date(database):
    setup_pack(database);c,h,s=begin(database,'Asia/Kathmandu')
    try:
        s=send(c,h,s,'I’d like a regular clean for my one-bedroom apartment. When is it free this week?')
        assert s['quote']['cents']==6000 and 'week' in s['messages'][-1]['cards']
        assert 'occupied' not in s['messages'][-1]['text']
        s=send(c,h,s,'Can you help me clean my place next Friday?')
        date=s['scenario']['requested_date'];assert date
        s=send(c,h,s,'Make that a deep clean instead.')
        assert s['draft']['service']=='deep' and s['scenario']['requested_date']==date
    finally:c.close()
    c,h,s=begin(database,'Pacific/Auckland')
    try:
        s=send(c,h,s,'I need a clean tomorrow.')
        assert s['quote'] is None and 'clarify' in s['messages'][-1]['cards']
        date=s['scenario']['requested_date']
        s=send(c,h,s,'Regular cleaning please.')
        assert s['quote'] is None
        s=send(c,h,s,'Two bedrooms, please.')
        assert s['quote']['cents']==8000 and s['messages'][-1]['requested_date']==date
    finally:c.close()


def test_grounded_fixture_answers_and_untrusted_replacement(database):
    setup_pack(database);engine,_=database
    with Session(engine) as db,db.begin():
        from choreograph.sessions import create_workspace
        workspace,_=create_workspace(db,'UTC',NOW);knowledge.attach_samples(db,workspace)
        provider=assistant.FakeAssistant()
        for case in json.loads((knowledge.PACK/'evaluation.json').read_text()):
            hits=knowledge.retrieve(db,workspace,case['question']);answer=provider.evidence(case['question'],hits)
            claims=assistant.validate_claims(answer,hits)
            assert claims and all(claim.excerpt in next(h.node.text for h in hits if h.node.id_==str(claim.passage_id)) for claim in claims)
        for name in ['malicious-guide.txt','conflicting-guide.txt']:
            data=(Path(__file__).parent/'fixtures'/name).read_bytes()
            assert knowledge.replace(db,workspace,'preparation',data,'text',NOW)['ready']
            hits=knowledge.retrieve(db,workspace,'What are the pet preparation instructions?')
            assert provider.evidence('What are the pet preparation instructions?',hits).status=='conflicting'
            assert not workspace.draft and not workspace.messages


def test_provider_envelopes_limits_refusal_and_no_fallback():
    intent={'intent':'greeting','service':None,'bedrooms':None,'oven':None,'requested_date':None,'requested_time':None,'guide_question':None}
    def envelope(value):return {'status':'completed','output':[{'type':'reasoning','summary':[]},{'type':'message','content':[{'type':'output_text','text':json.dumps(value)}]}]}
    assert parse_envelope(envelope(intent),Interpretation).intent=='greeting'
    for payload in [{'status':'incomplete'}, {'status':'completed','output':[{'type':'message','content':[{'type':'refusal'}]}]},envelope({'intent':'run_sql','sql':'drop table'}),envelope({'claims':[]})]:
        with pytest.raises(DomainError):parse_envelope(payload,Interpretation)
    class Reply:
        def model_dump(self,mode):return envelope(intent)
    class Responses:
        def create(self,**kwargs):
            self.kwargs=kwargs;return Reply()
    class Client:responses=Responses()
    transport=OpenAITransport(model='injected-test-only',client=Client(),authorized=True)
    assert transport.interpret('hello',{},'UTC','2026-10-22').intent=='greeting'
    assert Client.responses.kwargs['store'] is False and Client.responses.kwargs['max_output_tokens']==1400
    assert Client.responses.kwargs['text']['format']['strict'] is True
    with pytest.raises(DomainError):OpenAITransport(model='',authorized=True)
    class Broken:
        def create(self,**kwargs):raise RuntimeError('private payload must never escape')
    class BrokenClient:responses=Broken()
    with pytest.raises(DomainError) as error:OpenAITransport(model='injected-test-only',client=BrokenClient(),authorized=True).interpret('hello',{},'UTC','2026-10-22')
    assert error.value.code=='ASSISTANT_UNAVAILABLE' and 'private' not in error.value.message


def test_forged_citation_rolls_back_and_stale_turn_cannot_mutate(database):
    setup_pack(database);engine,settings=database
    class Forged(assistant.FakeAssistant):
        def evidence(self,question,hits):return GroundedOutput(status='supported',claims=[{'passage_id':str(uuid4()),'excerpt':'A fabricated unsupported policy.'}])
    c=TestClient(create_app(settings,engine,lambda:NOW,assistant_provider=Forged()));h={'x-choreograph-bridge':settings.bridge_secret,'origin':settings.origin}
    try:
        s=c.post('/v1/session',headers=h,json={'timezone':'UTC'}).json();h['x-csrf-token']=s['csrf']
        result=command(c,h,s,{'text':'A two-bedroom deep clean. What supplies do you use?'},'/v1/chat',method='post')
        assert result.status_code==503 and result.json()['code']=='ANSWER_UNSUPPORTED'
        current=c.get('/v1/session',headers=h).json();assert current['revision']==s['revision'] and not current['messages'] and current['draft']['service'] is None
        s=command(c,h,s,{'service':'regular'}).json()['state']
        result=command(c,h,{**s,'revision':s['revision']-1},{'text':'Three bedrooms'},'/v1/chat',method='post')
        assert result.status_code==409 and not c.get('/v1/session',headers=h).json()['messages']
    finally:c.close()
