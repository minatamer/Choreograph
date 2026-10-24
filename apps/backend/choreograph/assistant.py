"""Small interpretation/retrieval/command vocabulary, shared with ordinary controls."""
import re
from datetime import datetime, time, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import select

from . import domain, knowledge, service
from .assistant_context import bind_context, turn_context
from .contracts import ChatMessage, SourceClaim, Suggestion
from .errors import DomainError
from .models import Enquiry
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
        guide_pattern=r'include|carpet|shampoo|pets?|cats?|dogs?|suppl|product|equipment|method|how.*clean|prepar|access|key|fragrance|unscented|allerg|guarantee|deposit|hazard|mould|pest|refund|cancellation|rescheduling|heavy furniture|service area|parking|insurance|insured|discount|payment'
        guidance=bool(re.search(guide_pattern,q))
        period='morning' if 'morning' in q else 'afternoon' if 'afternoon' in q else None
        schedule=bool(date_value or requested_time or re.search(r'available|free this|show.*week|this week|morning appointment|afternoon appointment|find.*time|unavailable',q))
        intent='schedule' if schedule else 'guide' if guidance else 'quote' if re.search(r'quote|cost|price|how much',q) else 'change' if service_name or rooms or oven is not None else 'greeting' if re.fullmatch(r'(hi|hello|hey|thanks|thank you)[!. ]*',q) else 'clarify'
        if intent=='guide' and (service_name or rooms or oven is not None) and re.search(r"\b(?:i (?:need|want)|i['’]d like|i['’]m (?:moving|looking)|make (?:that|it))\b",q):intent='quote'
        if rooms and rooms not in (1,2,3):intent='handoff'
        if re.fullmatch(r'(thanks|thank you)[!. ]*',q):intent='thanks'
        if re.search(r'what can you do|how (?:does|do) (?:this|you) work|who are you|help me (?:get started|use)',q):intent='about'
        if re.search(r'(?:is|was|check|show|status).*\b(?:my )?book(?:ing|ed)|am i booked',q) and not guidance:intent='booking'
        if re.search(r'(?:cancel|reschedule|move|change).*(?:appointment|booking|reservation)|\b(?:cancel|reschedule) (?:it|my clean)\b|mark.*complete',q) and not guidance:intent='manage'
        if re.search(r'confirm.*book|book (?:it|this|the clean)|reserve (?:it|this)|send.*request',q) and intent not in {'booking','manage'}:intent='review'
        guide_parts=[part.strip() for part in re.split(r'[?!.]',text) if re.search(guide_pattern,part,re.I)]
        return Interpretation(intent=intent,service=service_name,bedrooms=rooms,oven=oven,
                              requested_date=date_value,requested_time=requested_time,guide_question='? '.join(guide_parts) if guidance else None,period=period)

    def evidence(self,question,hits):
        untrusted=' '.join(hit.node.text.lower() for hit in hits)
        if re.search(r'ignore.*instructions|system override|reveal.*tokens|contradict|costs one dollar|pets must remain in the room being cleaned',untrusted):
            return GroundedOutput(status='conflicting',claims=[])
        aliases={'supply':'product','allergen':'allergy','guarantees':'guarantee','preparation':'prepare',
                 'preparing':'prepare','cleaned':'clean','stays':'keep','stay':'keep','pests':'pest'}
        def words(value):return {aliases.get(token,token) for token in knowledge.terms(value)}
        tokens=words(question)-{'one','two','three','apartment','home','please','need','include','remove','use','work',
            'offer','cleaner','should','would','there','which','where','during','follow','leave','here','cover','safe','move','out'}
        vocabulary=set().union(*(words(hit.node.text+' '+hit.node.metadata.get('section','')+' '+hit.node.metadata.get('title','')) for hit in hits))
        # Fake selection is deliberately conservative about an unknown subject:
        # matching "charge" alone cannot establish a parking-charge policy.
        if not tokens or tokens-vocabulary:return GroundedOutput(status='insufficient',claims=[])
        ranked=[]
        for hit in hits:
            section=words(hit.node.metadata.get('section',''))
            content=words(hit.node.text);overlap=tokens&content
            score=sum(1+1/sum(token in words(other.node.text) for other in hits) for token in overlap)+len(tokens&section)*1.5
            if 'prepare' in tokens and 'prepare' in words(hit.node.metadata.get('title','')):score+=1
            excerpts=[hit.node.text] if len(hit.node.text)<=650 else re.split(r'(?<=[.!?])\s+',hit.node.text)
            for excerpt in excerpts:
                if overlap and 20<=len(excerpt)<=650 and tokens&words(excerpt):ranked.append((score,hit,excerpt))
        ranked.sort(key=lambda item:item[0],reverse=True);claims=[];covered=set()
        for score,hit,excerpt in ranked:
            overlap=tokens&words(excerpt)
            if claims and not overlap-covered and score<ranked[0][0]*.6:continue
            covered.update(overlap);claims.append(EvidenceQuote(passage_id=hit.node.id_,excerpt=excerpt))
            if len(claims)==3:break
        return GroundedOutput(status='supported' if claims else 'insufficient',claims=claims)


def validate_claims(output,hits):
    if output.status!='supported':
        if output.claims:raise DomainError('ANSWER_UNSUPPORTED','The answer could not be matched to its source. Try again.',503)
        return []
    if not 1<=len(output.claims)<=3:raise DomainError('ANSWER_UNSUPPORTED','The documents don’t establish an answer. Ask for a review.',422)
    supplied={hit.node.id_:hit.node for hit in hits};result=[];seen=set()
    for claim in output.claims:
        node=supplied.get(claim.passage_id)
        if not node or not 15<=len(claim.excerpt)<=650 or claim.excerpt not in node.text:
            raise DomainError('ANSWER_UNSUPPORTED','The answer could not be matched to its source. Try again.',503)
        m=node.metadata
        if (node.id_,claim.excerpt) in seen:continue
        seen.add((node.id_,claim.excerpt))
        result.append(SourceClaim(version_id=m['version_id'],passage_id=node.id_,title=m['title'],version=m['version'],
                                  page=m['page'],section=m['section'],media_type=m['media_type'],excerpt=claim.excerpt))
    return result


def _require_turn(workspace,revision):
    service.require_revision(workspace,revision)
    if len(workspace.messages)>=60:raise DomainError('CHAT_LIMIT','This demo has reached its conversation limit. Start a new demo.',429)


def _normalize_intent(workspace,intent):
    intent=intent.model_copy(deep=True);scenario=None
    if intent.intent not in {'quote','change','schedule','review'}:
        intent.service=None;intent.bedrooms=None;intent.oven=None
        intent.requested_date=None;intent.requested_time=None;intent.period=None
    if intent.requested_time and not intent.requested_date and intent.intent=='schedule':
        selected=workspace.draft.get('preferred_at')
        intent.requested_date=(datetime.fromisoformat(selected).astimezone(ZoneInfo(workspace.timezone)).date().isoformat()
                               if selected else workspace.scenario.get('requested_date'))
    if intent.requested_date:
        try:
            datetime.fromisoformat(intent.requested_date)
            scenario={'requested_date':intent.requested_date,'requested_time':intent.requested_time}
        except ValueError:intent.requested_date=None
    elif (intent.service or intent.bedrooms or intent.oven is not None) and not workspace.draft.get('preferred_at') and workspace.scenario.get('requested_date'):
        intent.requested_date=workspace.scenario['requested_date'];intent.requested_time=workspace.scenario.get('requested_time');intent.intent='schedule'
    if intent.bedrooms is not None and intent.bedrooms not in (1,2,3):intent.intent='handoff'
    return intent,scenario


def _clarification(workspace):
    if not workspace.draft.get('service'):return 'Which clean would you like: regular, deep or move-out?'
    if not workspace.draft.get('bedrooms'):return 'How many bedrooms does your home have: one, two or three?'
    return 'Would you like a quote, available times, or help with Juniper’s guides?'


def _latest_request(db,workspace):
    return db.scalar(select(Enquiry).where(Enquiry.workspace_id==workspace.id)
                     .order_by(Enquiry.created_at.desc(),Enquiry.quote['revision'].as_integer().desc(),Enquiry.id.desc()).limit(1))


def turn_suggestions(workspace,intent,claims,record=None):
    """Application-owned follow-ups, grounded in this turn rather than model prose."""
    topics={
        'Service Guide':[('Cleaning methods','How do you clean a kitchen?'),('Supplies & equipment','Do I need to provide equipment?')],
        'Preparation Guide':[('Arrange access','How do I arrange access for the cleaner?'),('Prepare the oven','How do I prepare the oven?')],
        'Access and Arrival':[('Get ready for the clean','How should I prepare the apartment?'),('Pets at home','What should I do with my pets?')],
        'Changes and Cancellations':[('If a change fails?','Will a failed reschedule release my old time?'),('Cancellation fee?','Is there a cancellation fee or refund?')],
        'Safety and Exclusions':[('Unscented products','Can I request fragrance-free products?'),('Moving furniture','Can you move heavy furniture?')],
        'Service Questions':[('What’s included?','What’s included in move-out cleaning?'),('Cleaning supplies','What cleaning supplies do you use?')],
    }
    choices=[]
    for claim in claims:choices.extend(topics.get(claim.title,[]))
    if record and record.status=='confirmed':
        choices.extend([('Reschedule my booking','I’d like to reschedule my appointment.'),('Cancel my booking','I’d like to cancel my appointment.')])
    elif not workspace.draft.get('service'):
        choices.extend((name+' clean',f'I’d like a {name.lower()} clean.') for name in ['Regular','Deep','Move-out'])
    elif not workspace.draft.get('bedrooms'):
        choices.extend((f'{count} bedroom'+('s' if count>1 else ''),f'{count} bedroom'+('s' if count>1 else '')+', please.') for count in [1,2,3])
    elif not workspace.draft.get('preferred_at'):
        choices.extend([('Find a time','When is this service free this week?'),('Morning appointments','What morning appointments are available?')])
    elif intent.intent!='review':choices.append(('Review my booking','Book it, please.'))
    seen={message.get('text','').strip().lower() for message in workspace.messages[-8:] if message.get('role')=='user'}
    result=[]
    for label,text in choices:
        if text.lower() in seen:continue
        seen.add(text.lower());result.append(Suggestion(label=label,text=text))
        if len(result)==4:break
    return result


def apply_chat(db,workspace,text,revision,now,*,intent:Interpretation,hits,output:GroundedOutput|None):
    """Apply a resolved turn; the caller owns external work and source authorization."""
    _require_turn(workspace,revision)
    intent,scenario=_normalize_intent(workspace,intent)
    claims=[]
    if intent.intent!='handoff' and intent.guide_question:
        if output is None:raise DomainError('ANSWER_UNSUPPORTED','The answer could not be matched to its source. Try again.',503)
        claims=validate_claims(output,hits)
    if scenario and intent.intent not in {'handoff','booking','manage','greeting','thanks','about'}:
        workspace.scenario={**workspace.scenario,**scenario}
    cards=[];paragraphs=[];requested_date=None;request_id=None
    if intent.intent=='handoff':
        paragraphs.append('I can help with Juniper’s regular, deep and move-out cleans for one to three bedrooms. For anything outside those options, please ask the coordinator.')
        cards=['services']
    elif intent.intent in {'booking','manage'}:
        record=_latest_request(db,workspace)
        if record:
            request_id=record.id
            if intent.intent=='manage':
                paragraphs.append('You can choose a new time or cancel below. Your booking stays as it is until you confirm a change.' if record.status=='confirmed' else
                    'You can review or cancel this request from the business side. It hasn’t been booked yet.' if record.status=='awaiting_review' else
                    'You can see this booking’s current details from the business side. I can also help you prepare another clean.')
                cards=['manage']
            else:
                paragraphs.append({'confirmed':'Your latest clean is booked. Here are its current details.',
                    'completed':'Your latest booking is marked completed. Here are its details.',
                    'cancelled':'Your latest booking is cancelled.',
                    'awaiting_review':'Your latest request has not been booked yet. You can review it from the business side.',
                    'declined':'Your latest request was declined. I can help you find another time.'}[record.status])
                cards=['booking'] if record.status in {'confirmed','completed','cancelled'} else ['manage']
        else:
            paragraphs.append('You haven’t booked a clean yet. I can help you choose a service and find a time.')
            cards=['services']
    else:
        edits={key:value for key,value in {'service':intent.service,'bedrooms':intent.bedrooms,'oven':intent.oven}.items() if value is not None}
        if edits:service.update_draft(db,workspace,edits,workspace.revision,now)
        if intent.guide_question:
            if output.status=='conflicting':paragraphs.append('I can’t establish that from the current guides. A coordinator can help check it. Your booking hasn’t changed.')
            elif not claims:paragraphs.append('I don’t have enough support in Juniper’s guides to answer that confidently. A coordinator can help check it.')
            else:paragraphs.append('Here’s what Juniper’s guides say:')
        quote=service.current_quote(workspace)
        if intent.intent=='greeting':paragraphs.append('Hi! I’m Juniper’s front desk. I can help with cleaning questions, a quote or finding a time. What can I help you with?');cards=['services']
        elif intent.intent=='thanks':paragraphs.append('You’re welcome! I’m here if you need anything else.')
        elif intent.intent=='about':
            paragraphs.append('I can explain Juniper’s services using its guides, prepare a quote and help you find an appointment. You review the details before booking. You can also check your booking or manage it from Business view.')
            cards=['services']
        elif not quote:
            if intent.intent!='guide':paragraphs.append(_clarification(workspace));cards=['clarify']
        else:
            cards=['quote'] if edits or intent.intent=='quote' else []
            if intent.intent=='schedule':
                cards.append('week')
                if intent.requested_date and workspace.draft.get('preferred_at'):
                    service.update_draft(db,workspace,{'preferred_at':None},workspace.revision,now)
                if intent.requested_date:
                    try:
                        requested_date=datetime.fromisoformat(intent.requested_date).date()
                        busy=service.busy_records(db,workspace)
                        if intent.requested_time:
                            requested_time=time.fromisoformat(intent.requested_time)
                            start=domain.local_to_utc(datetime.combine(requested_date,requested_time),workspace.timezone)
                            domain.validate_start(start,quote['minutes'],workspace.timezone,now)
                            if domain.eligible(start,quote['minutes'],busy):
                                service.update_draft(db,workspace,{'preferred_at':start.isoformat()},workspace.revision,now)
                                paragraphs.append(f'{requested_date.isoformat()} at {requested_time.strftime("%H:%M")} is available for the full clean. Review the quote before booking.')
                            else:paragraphs.append(f'{requested_date.isoformat()} at {requested_time.strftime("%H:%M")} is occupied. Choose a free alternative in the week below.')
                        else:
                            week=domain.availability(domain.week_start(requested_date),quote['minutes'],workspace.timezone,now,busy)
                            day=next(day for day in week['days'] if day['date']==requested_date)
                            slots=[slot for slot in day['slots'] if not intent.period or
                                (slot['start'].astimezone(ZoneInfo(workspace.timezone)).hour<12)==(intent.period=='morning')]
                            paragraphs.append(f'Choose an available {intent.period+" " if intent.period else ""}time on {requested_date.isoformat()}.' if slots else
                                f'No {intent.period+" " if intent.period else ""}appointments fit this clean on {requested_date.isoformat()}. Choose another day below.')
                    except (ValueError,DomainError):
                        paragraphs.append('That time isn’t available in the booking window. Choose a listed time below.')
                elif intent.requested_time:
                    paragraphs.append('What date would you like for that time? You can also choose from the week below.')
                else:paragraphs.append(f'Let’s look for {intent.period+" " if intent.period else ""}appointments that fit the whole clean. Choose a day below.')
            elif intent.intent=='review':
                record=_latest_request(db,workspace)
                if (record and record.status in {'confirmed','completed'} and
                        record.preferred_at.isoformat()==workspace.draft.get('preferred_at') and
                        all(record.fields.get(key)==workspace.draft.get(key) for key in ['service','bedrooms','oven'])):
                    request_id=record.id;cards=['booking'];paragraphs.append('That clean is already booked. Here are its current details.')
                elif workspace.draft.get('preferred_at'):
                    cards=['review'];paragraphs.append('Everything is ready to review below. Check the quote and time, then choose Book this clean to reserve it.')
                else:
                    cards=['quote','week'];paragraphs.append('Let’s choose a time first. Then you can review the details and book your clean.')
            elif intent.intent in {'quote','change'}:
                paragraphs.append(f'The current quote is ${quote["cents"]/100:.2f} for {quote["minutes"]} minutes. Choose a time, then review the details before booking.')
            elif intent.intent=='clarify':paragraphs.append(_clarification(workspace));cards=['services']
    if workspace.revision==revision:workspace.revision+=1
    suggestions=turn_suggestions(workspace,intent,claims,_latest_request(db,workspace))
    message=ChatMessage(id=uuid4(),role='assistant',text='\n\n'.join(paragraphs),claims=claims,cards=cards,suggestions=suggestions,
                        requested_date=requested_date,requested_period=intent.period,request_id=request_id,revision=workspace.revision)
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
    provider=bind_context(provider,turn_context(db,workspace))
    intent=provider.interpret(text,dict(workspace.draft),workspace.timezone,local.date().isoformat())
    normalized,_=_normalize_intent(workspace,intent);hits=[];output=None
    if normalized.intent!='handoff' and normalized.guide_question:
        hits=knowledge.retrieve(db,workspace,normalized.guide_question)
        output=provider.evidence(normalized.guide_question,hits)
    return apply_chat(db,workspace,text,revision,now,intent=intent,hits=hits,output=output)
