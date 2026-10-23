"""Small interpretation/retrieval/command vocabulary, shared with ordinary controls."""
import re
from datetime import datetime, time, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from . import domain, knowledge, service
from .contracts import ChatMessage, SourceClaim, Suggestion
from .errors import DomainError
from .providers import EvidenceQuote, GroundedOutput, Interpretation

WEEKDAYS=['monday','tuesday','wednesday','thursday','friday','saturday','sunday']


class FakeAssistant:
    def interpret(self,text,draft,zone,local_date):
        q=text.lower();service_name='move-out' if re.search(r'mov(?:e|ing)[ -]?out',q) else 'deep' if 'deep' in q else 'regular' if 'regular' in q else None
        match=re.search(r'\b(one|two|three|four|[1-9])[ -]?(?:bedrooms?|beds?|br)\b',q)
        rooms=({'one':1,'two':2,'three':3,'four':4}.get(match[1],int(match[1]) if match[1].isdigit() else 0)) if match else None
        oven=(not re.search(r'(?:remove|without|no|skip|don.t need) (?:the |an? )?oven',q)) if 'oven' in q and not re.search(r'prepare|cool|switch|products',q) else None
        date_value=None;today=datetime.fromisoformat(local_date).date()
        exact=re.search(r'\b\d{4}-\d{2}-\d{2}\b',q)
        if exact:date_value=exact[0]
        elif 'tomorrow' in q:date_value=(today+timedelta(days=1)).isoformat()
        else:
            for index,name in enumerate(WEEKDAYS):
                if name in q:
                    offset=(index-today.weekday())%7
                    if 'next '+name in q and offset==0:offset=7
                    date_value=(today+timedelta(days=offset)).isoformat();break
        match_time=re.search(r'(?:\bat\s+)(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b',q)
        requested_time=None
        if match_time:
            hour=int(match_time[1]);minute=int(match_time[2] or 0)
            if match_time[3]=='pm' and hour<12:hour+=12
            if match_time[3]=='am' and hour==12:hour=0
            requested_time=f'{hour:02}:{minute:02}'
        guidance=bool(re.search(r'include|carpet|shampoo|pets?|cats?|dogs?|suppl|product|equipment|method|how.*clean|prepare|access|key|fragrance|unscented|allerg|guarantee|deposit|hazard|mould|pest|refund|cancellation|rescheduling|heavy furniture|service area',q))
        schedule=bool(date_value or re.search(r'available|free this|show.*week|this week|morning appointment|find.*time|unavailable',q))
        intent='schedule' if schedule else 'guide' if guidance else 'quote' if re.search(r'quote|cost|price|how much',q) else 'change' if service_name or rooms or oven is not None else 'greeting' if re.fullmatch(r'(hi|hello|hey|thanks|thank you)[!. ]*',q) else 'clarify'
        if rooms and rooms not in (1,2,3):intent='handoff'
        if re.search(r'confirm.*book|cancel.*book|reschedule.*book|mark.*complete|send.*request',q):intent='handoff'
        guide_parts=[part.strip() for part in re.split(r'[?!.]',text) if re.search(r'include|carpet|shampoo|pets?|cats?|dogs?|suppl|product|equipment|method|how.*clean|prepare|access|key|fragrance|unscented|allerg|guarantee|deposit|hazard|mould|pest|refund|cancellation|rescheduling|heavy furniture|service area',part,re.I)]
        return Interpretation(intent=intent,service=service_name,bedrooms=rooms,oven=oven,
                              requested_date=date_value,requested_time=requested_time,guide_question='? '.join(guide_parts) if guidance else None)

    def evidence(self,question,hits):
        untrusted=' '.join(hit.node.text.lower() for hit in hits)
        if re.search(r'ignore.*instructions|system override|reveal.*tokens|contradict|costs one dollar|pets must remain in the room being cleaned',untrusted):
            return GroundedOutput(status='conflicting',claims=[])
        tokens=set(knowledge.terms(question))-{'one','two','three','apartment','home','please','need','include'};ranked=[]
        for hit in hits:
            sentences=re.split(r'(?<=[.!?])\s+',hit.node.text)
            for sentence in sentences:
                overlap=tokens.intersection(knowledge.terms(sentence));score=len(overlap)
                if hit.node.metadata['section']=='Floors and carpets' and tokens.intersection({'carpet','shampoo'}):score+=.8
                if hit.node.metadata['section']=='Pets' and 'pet' in tokens:score+=1
                if score and 20<=len(sentence)<=650:ranked.append((score,hit,sentence))
        ranked.sort(key=lambda item:item[0],reverse=True);claims=[];used=set();covered=set()
        for _,hit,sentence in ranked:
            if hit.node.id_ in used:continue
            overlap=tokens.intersection(knowledge.terms(sentence))
            if not overlap-covered:continue
            covered.update(overlap);used.add(hit.node.id_);claims.append(EvidenceQuote(passage_id=hit.node.id_,excerpt=sentence))
            if len(claims)==3:break
        return GroundedOutput(status='supported' if claims else 'insufficient',claims=claims)


def validate_claims(output,hits):
    if output.status!='supported':return []
    if not 1<=len(output.claims)<=3:raise DomainError('ANSWER_UNSUPPORTED','The documents don’t establish an answer. Ask for a review.',422)
    supplied={hit.node.id_:hit.node for hit in hits};result=[]
    for claim in output.claims:
        node=supplied.get(claim.passage_id)
        if not node or not 15<=len(claim.excerpt)<=650 or claim.excerpt not in node.text:
            raise DomainError('ANSWER_UNSUPPORTED','The answer could not be matched to its source. Try again.',503)
        m=node.metadata
        result.append(SourceClaim(version_id=m['version_id'],passage_id=node.id_,title=m['title'],version=m['version'],
                                  page=m['page'],section=m['section'],media_type=m['media_type'],excerpt=claim.excerpt))
    return result


def _require_turn(workspace,revision):
    service.require_revision(workspace,revision)
    if len(workspace.messages)>=60:raise DomainError('CHAT_LIMIT','This demo has reached its conversation limit. Start a new demo.',429)


def _normalize_intent(workspace,intent):
    intent=intent.model_copy(deep=True);scenario=None
    if intent.requested_date:
        try:
            datetime.fromisoformat(intent.requested_date)
            scenario={'requested_date':intent.requested_date,'requested_time':intent.requested_time}
        except ValueError:intent.requested_date=None
    elif (intent.service or intent.bedrooms or intent.oven is not None) and not workspace.draft.get('preferred_at') and workspace.scenario.get('requested_date'):
        intent.requested_date=workspace.scenario['requested_date'];intent.requested_time=workspace.scenario.get('requested_time');intent.intent='schedule'
    if intent.bedrooms is not None and intent.bedrooms not in (1,2,3):intent.intent='handoff'
    return intent,scenario


def apply_chat(db,workspace,text,revision,now,*,intent:Interpretation,hits,output:GroundedOutput|None):
    """Apply a resolved turn; the caller owns external work and source authorization."""
    _require_turn(workspace,revision)
    intent,scenario=_normalize_intent(workspace,intent)
    claims=[]
    if intent.intent!='handoff' and intent.guide_question:
        if output is None:raise DomainError('ANSWER_UNSUPPORTED','The answer could not be matched to its source. Try again.',503)
        claims=validate_claims(output,hits)
    if scenario:workspace.scenario={**workspace.scenario,**scenario}
    cards=[];paragraphs=[];requested_date=None
    if intent.intent=='handoff':
        paragraphs.append('That needs a coordinator review. Use the request controls for booking changes; no booking has changed.')
        cards=['services']
    else:
        edits={key:value for key,value in {'service':intent.service,'bedrooms':intent.bedrooms,'oven':intent.oven}.items() if value is not None}
        if edits:service.update_draft(db,workspace,edits,workspace.revision,now)
        if intent.guide_question:
            if output.status=='conflicting':paragraphs.append('The document has conflicting or unrelated instructions. A coordinator needs to review it; your quote and booking rules are unchanged.')
            elif not claims:paragraphs.append('The current documents don’t establish that. Ask for a coordinator review.')
            else:paragraphs.append('From Juniper’s current documents:')
        quote=service.current_quote(workspace)
        if intent.intent=='greeting':paragraphs.append('Hi. Choose a question below, or tell us about the clean you need.');cards=['services']
        elif not quote:
            paragraphs.append('Which cleaning and home size would you like?');cards=['clarify']
        else:
            cards=['quote'] if edits or intent.intent=='quote' else []
            if intent.intent=='schedule':
                cards.append('week')
                if intent.requested_date:
                    try:
                        requested_date=datetime.fromisoformat(intent.requested_date).date()
                        requested_time=time.fromisoformat(intent.requested_time or '09:00')
                        start=domain.local_to_utc(datetime.combine(requested_date,requested_time),workspace.timezone)
                        domain.validate_start(start,quote['minutes'],workspace.timezone,now)
                        if domain.eligible(start,quote['minutes'],service.busy_records(db,workspace)):
                            if intent.requested_time:
                                service.update_draft(db,workspace,{'preferred_at':start.isoformat()},workspace.revision,now)
                                paragraphs.append(f'{requested_date.isoformat()} at {requested_time.strftime("%H:%M")} is available for the full clean. Review the quote before sending your request.')
                            else:paragraphs.append(f'Choose an available time on {requested_date.isoformat()}.')
                        else:
                            paragraphs.append(f'{requested_date.isoformat()} at {requested_time.strftime("%H:%M")} is occupied. Choose a free alternative in the week below.')
                    except (ValueError,DomainError):
                        paragraphs.append('That time isn’t available in the booking window. Choose a listed time below.')
                else:paragraphs.append('These times fit the whole clean. Choose a day to see its available appointments.')
            elif intent.intent in {'quote','change'}:
                paragraphs.append(f'The current quote is ${quote["cents"]/100:.2f} for {quote["minutes"]} minutes. Choose a time, then review it before sending.')
            elif intent.intent=='clarify':paragraphs.append('I can help with cleaning scope, preparation, a quote or a time. Choose a question below.');cards=['services']
    if workspace.revision==revision:workspace.revision+=1
    suggestions=[Suggestion(label='Show this week',text='When is this service free this week?'),Suggestion(label='Cleaning supplies',text='What cleaning supplies and equipment do you bring?'),Suggestion(label='Prepare a quote',text='Show a quote for a two-bedroom move-out with the oven.')]
    message=ChatMessage(id=uuid4(),role='assistant',text='\n\n'.join(paragraphs),claims=claims,cards=cards,suggestions=suggestions,
                        requested_date=requested_date,revision=workspace.revision)
    user=ChatMessage(id=uuid4(),role='user',text=text,revision=revision)
    workspace.messages=[*workspace.messages,user.model_dump(mode='json'),message.model_dump(mode='json')]
    return {'request_id':None}


def chat(db,workspace,text,revision,now,provider):
    """Compatibility orchestration for direct fake-provider callers."""
    _require_turn(workspace,revision)
    # Direct callers retain the original four shared transaction admission slots.
    # API orchestration admits its external work separately, before apply_chat.
    from sqlalchemy import text as sql
    if not any(db.scalar(sql('SELECT pg_try_advisory_xact_lock(45861,:slot)'),{'slot':slot}) for slot in range(1,5)):
        raise DomainError('ASSISTANT_BUSY','The front desk is busy. Try again shortly.',429)
    local=now.astimezone(ZoneInfo(workspace.timezone))
    intent=provider.interpret(text,dict(workspace.draft),workspace.timezone,local.date().isoformat())
    normalized,_=_normalize_intent(workspace,intent);hits=[];output=None
    if normalized.intent!='handoff' and normalized.guide_question:
        hits=knowledge.retrieve(db,workspace,normalized.guide_question)
        output=provider.evidence(normalized.guide_question,hits)
    return apply_chat(db,workspace,text,revision,now,intent=intent,hits=hits,output=output)
