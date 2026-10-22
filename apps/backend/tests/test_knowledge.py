import base64
import io
import json
import re
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from pypdf import PdfWriter
from pypdf.actions import JavaScript
from sqlalchemy import event, func, select
from sqlalchemy.orm import Session

from choreograph import knowledge
from choreograph.api import create_app
from choreograph.errors import DomainError
from choreograph.models import Chunk, DocumentVersion, Manifest
from choreograph.sessions import create_workspace, retire

NOW=datetime(2026,10,22,8,tzinfo=UTC)


def test_pack_provenance_and_bounded_parser():
    manifest=json.loads((knowledge.PACK/'manifest.json').read_text())
    assert len([x for x in manifest if x['file'].endswith('.pdf')])==6
    for item in manifest:
        pages=knowledge.parse((knowledge.PACK/item['file']).read_bytes(),'pdf' if item['file'].endswith('.pdf') else 'text')
        assert max(p['page'] for p in pages)==item['pages']
    coverage=knowledge.parse((knowledge.PACK/'service-guide.pdf').read_bytes(),'pdf')
    assert 'Carpet shampooing' in coverage[1]['text']
    assert 'separate safe room' in knowledge.parse((knowledge.PACK/'preparation-guide.pdf').read_bytes(),'pdf')[0]['text']
    writer=PdfWriter(clone_from=io.BytesIO((knowledge.PACK/'preparation-guide.pdf').read_bytes()))
    control=io.BytesIO();writer.write(control)
    assert knowledge.parse(control.getvalue(),'pdf')[0]['text']
    writer.add_open_action(JavaScript('alert("no")'));stream=io.BytesIO();writer.write(stream)
    for data,kind in [(stream.getvalue(),'pdf'),(b'not a pdf','pdf'),(b'\xff'*200,'text'),(b'<script>alert(1)</script>'+b'a'*50,'text'),(b'a'*32_001,'text')]:
        with pytest.raises(DomainError):knowledge.parse(data,kind)
    with pytest.raises(DomainError):knowledge.parse(b'x'*2_097_153,'text')


def test_actual_pgvector_retrieval_and_manifest_scope(database):
    engine,_=database
    with Session(engine) as db,db.begin():
        knowledge.prepare_samples(db,NOW)
        count=db.scalar(select(func.count()).select_from(Chunk))
        knowledge.prepare_samples(db,NOW)
        assert db.scalar(select(func.count()).select_from(Chunk))==count
        a,_=create_workspace(db,'Africa/Cairo',NOW);b,_=create_workspace(db,'Asia/Kathmandu',NOW)
        knowledge.attach_samples(db,a);knowledge.attach_samples(db,b)
        evaluation=json.loads((knowledge.PACK/'evaluation.json').read_text())
        for case in evaluation:
            hits=knowledge.retrieve(db,a,case['question'])
            assert len(hits)<=4
            assert any(h.node.metadata['slot']==case['slot'] and h.node.metadata['page']==case['page'] and case['contains'] in h.node.text for h in hits),case['question']
        original=db.get(Manifest,(a.id,'preparation')).version_id
        result=knowledge.replace(db,a,'preparation',(knowledge.PACK/'preparation-guide-v2.pdf').read_bytes(),'pdf',NOW)
        assert result['ready']
        replacement=db.get(Manifest,(a.id,'preparation')).version_id
        assert replacement!=original
        assert 'outside the home' in next(h.node.text for h in knowledge.retrieve(db,a,'What do I do with my pets?') if h.node.metadata['slot']=='preparation')
        assert all(h.node.metadata['version_id']!=str(replacement) for h in knowledge.retrieve(db,b,'What do I do with my pets?'))
        with pytest.raises(DomainError):knowledge.source(db,b,replacement)
        with pytest.raises(DomainError):knowledge.source(db,a,original)
        failed=knowledge.replace(db,a,'preparation',b'%PDF-garbage','pdf',NOW)
        assert not failed['ready'] and db.get(Manifest,(a.id,'preparation')).version_id==replacement
        assert a.ingestion_attempts==2
        knowledge.replace(db,a,'preparation',b'not a pdf','pdf',NOW)
        with pytest.raises(DomainError):knowledge.replace(db,a,'preparation',b'any','text',NOW)
        retire(a);knowledge.purge_private(db,a);db.flush()
        assert db.get(DocumentVersion,replacement) is None
        assert db.scalar(select(func.count()).select_from(Chunk).where(Chunk.version_id==replacement))==0
        assert len(knowledge.documents(db,b))==6


def test_metadata_retrieval_and_attachment_omit_source_without_weakening_source_authorization(database):
    engine,_=database
    with Session(engine) as db,db.begin():
        knowledge.prepare_samples(db,NOW)
    selected=[]

    def capture(_connection,_cursor,statement,_parameters,_context,_many):
        if statement.lstrip().upper().startswith('SELECT') and 'document_versions' in statement:
            selected.append(statement)

    def projections():
        return [re.sub(r'\s+',' ',re.split(r'\bFROM\b',statement,maxsplit=1,flags=re.I)[0]).strip().lower()
                for statement in selected]

    event.listen(engine,'before_cursor_execute',capture)
    try:
        with Session(engine) as db,db.begin():
            a,_=create_workspace(db,'Africa/Cairo',NOW);b,_=create_workspace(db,'Asia/Kathmandu',NOW)
            selected.clear()
            knowledge.attach_samples(db,a)
            assert len(selected)==6
            assert all(projection=='select document_versions.id' for projection in projections())
            knowledge.attach_samples(db,b)
            selected.clear()
            metadata=knowledge.documents(db,a)
            assert len(metadata)==6 and len(selected)==1
            assert all('document_versions.source' not in projection for projection in projections())
            selected.clear()
            hits=knowledge.retrieve(db,a,'What do I do with my cats?')
            assert any(hit.node.metadata['slot']=='preparation' and 'separate safe room' in hit.node.text for hit in hits)
            assert len(selected)==1
            assert all('document_versions.source' not in projection for projection in projections())

            original=next(row['id'] for row in metadata if row['slot']=='preparation')
            original_bytes=(knowledge.PACK/'preparation-guide.pdf').read_bytes()
            original_row=knowledge.source(db,a,original)
            assert original_row.source==original_bytes
            replacement_bytes=(knowledge.PACK/'preparation-guide-v2.pdf').read_bytes()
            assert knowledge.replace(db,a,'preparation',replacement_bytes,'pdf',NOW)['ready']
            replacement=next(row['id'] for row in knowledge.documents(db,a) if row['slot']=='preparation')
            assert replacement!=original
            replacement_row=knowledge.source(db,a,replacement)
            assert replacement_row.source==replacement_bytes
            assert knowledge.source(db,b,original).source==original_bytes
            with pytest.raises(DomainError,match='SOURCE_UNAVAILABLE'):
                knowledge.source(db,a,original)
            with pytest.raises(DomainError,match='SOURCE_UNAVAILABLE'):
                knowledge.source(db,b,replacement)
    finally:
        event.remove(engine,'before_cursor_execute',capture)


def test_document_http_authorization_replay_reset(database):
    import asyncio
    engine,settings=database
    with Session(engine) as db,db.begin():knowledge.prepare_samples(db,NOW)
    async def run():
        transport=httpx.ASGITransport(app=create_app(settings,engine,lambda:NOW))
        headers={'x-choreograph-bridge':settings.bridge_secret,'origin':settings.origin}
        async with httpx.AsyncClient(transport=transport,base_url=settings.origin,headers=headers) as client:
            state=(await client.post('/v1/session',json={'timezone':'Africa/Cairo'})).json()
            assert len(state['documents'])==6
            doc=next(d for d in state['documents'] if d['slot']=='service')
            source=await client.get(f"/v1/documents/{doc['id']}/source")
            assert source.status_code==200 and source.content.startswith(b'%PDF')
            detail=(await client.get(f"/v1/documents/{doc['id']}")).json()
            assert any(p['page']==2 and 'Carpet shampooing' in p['content'] for p in detail['passages'])
            request={'generation':state['generation'],'revision':state['revision'],'kind':'pdf',
                     'data':base64.b64encode((knowledge.PACK/'preparation-guide-v2.pdf').read_bytes()).decode()}
            action={'x-csrf-token':state['csrf'],'idempotency-key':str(uuid4())}
            first=await client.post('/v1/documents/preparation/replace',json=request,headers=action)
            assert first.status_code==200,first.text
            assert first.json()['document_notice']['ready']
            replay=await client.post('/v1/documents/preparation/replace',json=request,headers=action)
            assert replay.json()['replayed'] and replay.json()['state']['replacements_left']==2
            current=first.json()['state'];private=next(d for d in current['documents'] if d['private'])
            async with httpx.AsyncClient(transport=transport,base_url=settings.origin,headers=headers) as other:
                await other.post('/v1/session',json={'timezone':'UTC'})
                assert (await other.get(f"/v1/documents/{private['id']}/source")).status_code==404
            reset=await client.post('/v1/reset',json={'timezone':state['timezone'],'generation':state['generation']},headers={'x-csrf-token':state['csrf']})
            assert reset.status_code==200
            assert (await client.get(f"/v1/documents/{private['id']}/source")).status_code==404
    asyncio.run(run())
