"""Small server-owned conversational context; no source bytes, contacts or secrets."""
import json

from sqlalchemy import select

from .models import Enquiry


def turn_context(db,workspace):
    history=[];size=0
    for message in reversed(workspace.messages[-8:]):
        if message.get('role') not in {'user','assistant'}:continue
        row={'role':message['role'],'text':str(message.get('text',''))[:600],
             'source_topics':list(dict.fromkeys(str(claim.get('title',''))[:100]
                 for claim in message.get('claims',[])))[:3]}
        amount=len(json.dumps(row,ensure_ascii=True))
        if size+amount>8000:break
        history.append(row);size+=amount
    records=list(db.scalars(select(Enquiry).where(Enquiry.workspace_id==workspace.id)
                           .order_by(Enquiry.created_at.desc(),Enquiry.quote['revision'].as_integer().desc(),Enquiry.id.desc()).limit(3)))
    return {'recent_turns':list(reversed(history)),
            'pending_date':workspace.scenario.get('requested_date'),
            'pending_time':workspace.scenario.get('requested_time'),
            'bookings':[{'status':row.status,'preferred_at':row.preferred_at.isoformat()} for row in records],
            'capabilities':['current_document_guidance','exact_catalogue_quote','availability',
                            'draft_preference','explicit_booking_review','booking_status','business_management']}


def bind_context(provider,context):
    # Injected minimal providers keep their existing four-argument protocol.
    # The live adapter returns a per-command copy, never mutates the runtime.
    return provider.with_context(context) if hasattr(provider,'with_context') else provider
