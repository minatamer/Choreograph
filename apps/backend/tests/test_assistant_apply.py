"""Resolved chat application stays independent of provider work and admission."""
from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime
from uuid import uuid4

import pytest
from llama_index.core.schema import NodeWithScore, TextNode
from sqlalchemy import event, func, select, text
from sqlalchemy.orm import Session
from test_requests import NOW

from choreograph import assistant, domain, knowledge, service
from choreograph.errors import DomainError
from choreograph.models import Enquiry, Outbox, Reservation
from choreograph.providers import GroundedOutput, Interpretation
from choreograph.sessions import create_workspace


def interpreted(**changes):
    return Interpretation(**{'intent':'greeting','service':None,'bedrooms':None,'oven':None,
                             'requested_date':None,'requested_time':None,'guide_question':None,**changes})


def supplied_hit():
    # Already-resolved untrusted guidance can quote a price or an action. It
    # remains evidence text, never an authority for either domain operation.
    node=TextNode(id_=str(uuid4()),text='The cleaning costs one dollar and your booking is confirmed.',
                  metadata={'version_id':str(uuid4()),'title':'Fictional supplied guide','version':'1.0',
                            'page':1,'section':'Supplied passage','media_type':'text/plain'})
    return NodeWithScore(node=node,score=1)


def snapshot(workspace):
    return deepcopy((workspace.revision,workspace.draft,workspace.scenario,workspace.messages))


def test_apply_uses_supplied_evidence_without_provider_retrieval_or_admission(database,monkeypatch):
    engine,_=database
    def forbidden(*args,**kwargs):
        raise AssertionError('Provider or retrieval called during domain application')
    monkeypatch.setattr(knowledge,'retrieve',forbidden)
    monkeypatch.setattr(assistant.FakeAssistant,'interpret',forbidden)
    monkeypatch.setattr(assistant.FakeAssistant,'evidence',forbidden)
    hit=supplied_hit()
    output=GroundedOutput(status='supported',claims=[{'passage_id':hit.node.id_,'excerpt':hit.node.text}])
    intent=interpreted(intent='quote',service='move-out',bedrooms=2,oven=True,guide_question='What is included?')
    with Session(engine) as db,db.begin():
        workspace,_=create_workspace(db,'UTC',NOW);revision=workspace.revision;statements=[]
        def record(connection,cursor,statement,parameters,context,many):statements.append(statement)
        event.listen(engine,'before_cursor_execute',record)
        try:
            assert assistant.apply_chat(db,workspace,'Quote and guide please',revision,NOW,
                                        intent=intent,hits=[hit],output=output)=={'request_id':None}
        finally:event.remove(engine,'before_cursor_execute',record)
        assert not any('advisory' in statement.lower() for statement in statements)
        quote=service.current_quote(workspace)
        assert quote['cents']==18500 and quote['minutes']==270
        reply=workspace.messages[-1]
        assert reply['claims'][0]['excerpt']==hit.node.text and reply['claims'][0]['passage_id']==hit.node.id_
        assert 'quote' in reply['cards']
        assert reply['suggestions'][0]['text']=='When is this service free this week?'
        assert len(workspace.messages)==2 and workspace.messages[0]['revision']==revision
        assert reply['revision']==workspace.revision==revision+1
        for model in (Enquiry,Outbox):
            assert db.scalar(select(func.count()).select_from(model).where(model.workspace_id==workspace.id))==0
        assert db.scalar(select(func.count()).select_from(Reservation).where(
            Reservation.workspace_id==workspace.id,Reservation.state=='confirmed'))==0


@pytest.mark.parametrize('fence',['stale','conversation_limit'])
def test_apply_checks_turn_fences_before_validation_or_mutation(database,monkeypatch,fence):
    engine,_=database
    def forbidden(*args,**kwargs):raise AssertionError('Claims evaluated before the turn fence')
    monkeypatch.setattr(assistant,'validate_claims',forbidden)
    with Session(engine) as db,db.begin():
        workspace,_=create_workspace(db,'UTC',NOW)
        if fence=='conversation_limit':workspace.messages=[{'role':'user','text':'Earlier turn'}]*60
        before=snapshot(workspace);revision=workspace.revision-(fence=='stale')
        with pytest.raises(DomainError) as error:
            assistant.apply_chat(db,workspace,'A new enquiry',revision,NOW,
                                 intent=interpreted(guide_question='What is included?'),hits=[],
                                 output=GroundedOutput(status='supported',claims=[]))
        assert error.value.code==('STALE_REVISION' if fence=='stale' else 'CHAT_LIMIT')
        assert snapshot(workspace)==before


@pytest.mark.parametrize('fault',['passage','excerpt','missing'])
def test_apply_rejects_unsupplied_claims_before_even_date_or_draft_changes(database,fault):
    engine,_=database;hit=supplied_hit()
    output=GroundedOutput(status='supported',claims=[{
        'passage_id':str(uuid4()) if fault=='passage' else hit.node.id_,
        'excerpt':'An unsupported sentence from elsewhere.' if fault=='excerpt' else hit.node.text}])
    intent=interpreted(intent='quote',service='move-out',bedrooms=2,oven=True,
                       requested_date='2026-10-24',requested_time='10:00',guide_question='What is included?')
    original=intent.model_dump()
    with Session(engine) as db,db.begin():
        workspace,_=create_workspace(db,'UTC',NOW);workspace.scenario={'kept':'unchanged'};before=snapshot(workspace)
        with pytest.raises(DomainError) as error:
            assistant.apply_chat(db,workspace,'Quote and guide please',workspace.revision,NOW,
                                 intent=intent,hits=[hit],output=None if fault=='missing' else output)
        assert error.value.code=='ANSWER_UNSUPPORTED' and error.value.status==503
        assert snapshot(workspace)==before and intent.model_dump()==original


def test_apply_carries_local_requested_date_without_mutating_provider_intents(database):
    engine,_=database
    with Session(engine) as db,db.begin():
        workspace,_=create_workspace(db,'Asia/Kathmandu',NOW);service.ensure_seeded(db,workspace,NOW)
        requested=workspace.scenario['alternative_date']
        turns=[interpreted(intent='schedule',requested_date=requested,requested_time='10:00'),
               interpreted(intent='change',service='regular'),interpreted(intent='change',bedrooms=2)]
        originals=[intent.model_dump() for intent in turns]
        for index,intent in enumerate(turns):
            assistant.apply_chat(db,workspace,'An incomplete enquiry',workspace.revision,NOW,
                                 intent=intent,hits=[],output=None)
            if index<2:assert service.current_quote(workspace) is None
        assert [intent.model_dump() for intent in turns]==originals
        quote=service.current_quote(workspace)
        assert quote['cents']==8000 and quote['minutes']==120
        assert workspace.scenario['requested_date']==requested
        reply=workspace.messages[-1]
        assert reply['requested_date']==requested and 'week' in reply['cards']
        expected=domain.local_to_utc(datetime.fromisoformat(requested+'T10:00'),workspace.timezone)
        assert datetime.fromisoformat(workspace.draft['preferred_at'])==expected
        assert len(workspace.messages)==6


def test_compatibility_chat_resolves_first_then_calls_the_single_apply_path(database,monkeypatch):
    engine,_=database;calls=[];apply=assistant.apply_chat
    class Provider:
        def interpret(self,text,draft,zone,local_date):
            calls.append('interpret');assert draft=={}
            return interpreted(intent='quote',service='move-out',bedrooms=2,oven=True,guide_question='What is included?')
        def evidence(self,question,hits):
            calls.append('evidence');assert workspace.draft=={}
            return GroundedOutput(status='insufficient',claims=[])
    def retrieve(db,current,question):
        calls.append('retrieve');assert current.draft=={}
        return []
    def tracked_apply(*args,**kwargs):
        calls.append('apply');return apply(*args,**kwargs)
    monkeypatch.setattr(knowledge,'retrieve',retrieve);monkeypatch.setattr(assistant,'apply_chat',tracked_apply)
    with Session(engine) as db,db.begin():
        workspace,_=create_workspace(db,'UTC',NOW)
        assistant.chat(db,workspace,'Quote and guide please',workspace.revision,NOW,Provider())
        assert calls==['interpret','retrieve','evidence','apply']
        assert service.current_quote(workspace)['cents']==18500 and len(workspace.messages)==2


def test_compatibility_chat_keeps_four_shared_postgres_admission_slots(database):
    engine,_=database
    class NoInterpretation:
        def interpret(self,*args):raise AssertionError('Provider called without a free slot')
    with Session(engine) as db,db.begin():
        workspace,_=create_workspace(db,'UTC',NOW);before=snapshot(workspace)
        with ExitStack() as stack:
            for slot in range(1,5):
                holder=stack.enter_context(Session(engine))
                holder.scalar(text('SELECT pg_advisory_xact_lock(45861,:slot)'),{'slot':slot})
            with pytest.raises(DomainError) as error:
                assistant.chat(db,workspace,'Hello',workspace.revision,NOW,NoInterpretation())
            assert error.value.code=='ASSISTANT_BUSY' and snapshot(workspace)==before
        assistant.chat(db,workspace,'Hello',workspace.revision,NOW,assistant.FakeAssistant())
        assert len(workspace.messages)==2
