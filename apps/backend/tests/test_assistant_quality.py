"""Meaningful expected-source retrieval and explicit lifecycle checks, no live credentials."""
import json
from datetime import datetime
from uuid import uuid4

import pytest
from test_assistant import send, setup_pack
from test_booking import book
from test_customer_booking import confirm, ready
from test_requests import NOW, begin, command

from choreograph import assistant, knowledge
from choreograph.models import Reservation, Workspace
from choreograph.persistence import Session, repo_first
from choreograph.sessions import create_workspace


def same_time(a,b):return datetime.fromisoformat(a)==datetime.fromisoformat(b)


def test_expected_source_page_and_passage_recall_and_answer_support(database):
    setup_pack(database)
    cases=json.loads((knowledge.PACK/'evaluation.json').read_text())
    cases.append({'question':'What cleaning supplies and equipment do you bring?','slot':'service','page':2,'contains':'Juniper brings'})
    with Session(database[0]) as db,db.begin():
        workspace,_=create_workspace(db,'UTC',NOW);knowledge.attach_samples(db,workspace)
        failures=[]
        for case in cases:
            hits=knowledge.retrieve(db,workspace,case['question'])
            expected=[hit for hit in hits if hit.node.metadata['slot']==case['slot'] and
                      hit.node.metadata['page']==case['page'] and case['contains'] in hit.node.text]
            claims=assistant.validate_claims(assistant.FakeAssistant().evidence(case['question'],hits),hits)
            selected=[claim for claim in claims if claim.page==case['page'] and
                      case['contains'] in claim.excerpt and any(str(claim.passage_id)==hit.node.id_ for hit in expected)]
            if not expected or not selected:failures.append({'question':case['question'],'recall':bool(expected),'answer':bool(selected),
                'hits':[(hit.node.metadata['slot'],hit.node.metadata['section']) for hit in hits],
                'claims':[(claim.title,claim.section) for claim in claims]})
        if failures:pytest.fail(json.dumps(failures,indent=2))


@pytest.mark.parametrize('question',['What is your parking charge?','How much insurance coverage do you carry?',
    'What payment cards do you accept?','Do you offer student discounts?'])
def test_absent_business_policy_is_not_invented_or_a_draft_edit(database,question):
    setup_pack(database);client,headers,state=begin(database)
    try:
        state=command(client,headers,state,{'service':'regular','bedrooms':2}).json()['state']
        original=state['draft'];state=send(client,headers,state,question)
        reply=state['messages'][-1]
        assert not reply['claims'] and 'enough support' in reply['text']
        assert state['draft']==original and state['requests']==[]
    finally:client.close()


def test_fake_chat_management_preserves_changes_until_review_and_appends_actual_receipts(database):
    setup_pack(database);client,headers,state=ready(database)
    try:
        state=confirm(client,headers,state).json()['state'];record=state['requests'][0]
        state=send(client,headers,state,'I’d like to reschedule my appointment.')
        assert state['messages'][-1]['cards']==['manage'] and state['requests'][0]['booking']==record['booking']
        week=client.get(f"/v1/requests/{record['id']}/availability",headers=headers).json()
        candidate=next(slot['start'] for day in week['days'] for slot in day['slots'] if not same_time(slot['start'],record['preferred_at']))
        state=book(client,headers,state,record['id'],'reschedule',{'preferred_at':candidate}).json()['state']
        assert same_time(state['draft']['preferred_at'],candidate) and state['messages'][-1]['cards']==['booking']
        assert 'moved' in state['messages'][-1]['text']
        state=send(client,headers,state,'Cancel my appointment, please.')
        assert state['messages'][-1]['cards']==['manage'] and state['requests'][0]['status']=='confirmed'
        key=str(uuid4());before=state
        result=book(client,headers,state,record['id'],'cancel',key=key).json();state=result['state']
        assert result['receipt']['action']=='cancelled' and state['draft']['preferred_at'] is None
        assert state['messages'][-1]['cards']==['booking'] and 'cancelled' in state['messages'][-1]['text']
        replay=book(client,headers,before,record['id'],'cancel',key=key).json()
        assert replay['replayed'] and replay['state']['messages']==state['messages']
        week=client.get(f"/v1/requests/{record['id']}/availability",headers=headers).json()
        assert any(same_time(slot['start'],candidate) for day in week['days'] for slot in day['slots'])
        state=send(client,headers,state,'Is my booking confirmed?')
        assert 'cancelled' in state['messages'][-1]['text']
        with Session(database[0]) as db:
            reservation=repo_first(db, Reservation, filters={'enquiry_id': record['id']})
            assert reservation.state=='cancelled'
    finally:client.close()


def test_cancelling_an_older_booking_preserves_a_separately_edited_draft(database):
    client,headers,state=ready(database)
    try:
        state=confirm(client,headers,state).json()['state'];record=state['requests'][0]
        state=command(client,headers,state,{'service':'regular','bedrooms':1}).json()['state']
        separate=state['draft'];state=book(client,headers,state,record['id'],'cancel').json()['state']
        assert state['draft']==separate
        with Session(database[0]) as db:assert db.get(Workspace,state['workspace_id']).active
    finally:client.close()
