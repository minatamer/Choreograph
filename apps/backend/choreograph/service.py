"""Workspace-scoped application commands shared by UI and assistant adapters."""
import hashlib
import json
from datetime import date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from . import domain
from .errors import DomainError
from .models import (
    Activity,
    Catalogue,
    Connection,
    Enquiry,
    Idempotency,
    Outbox,
    Reservation,
    Staff,
    Workspace,
)


def ensure_seeded(db, workspace: Workspace, now: datetime):
    _seed_working_calendar(db, workspace, now)
    _seed_calendar_history(db, workspace, now)


def _seed_working_calendar(db, workspace: Workspace, now: datetime):
    if workspace.seeded:
        return
    if db.scalar(select(func.count()).select_from(Reservation).where(Reservation.workspace_id == workspace.id)):
        # An already exposed calendar can never be rearranged to force a script.
        workspace.seeded = True
        return
    today = now.astimezone(ZoneInfo(workspace.timezone)).date()
    busy_day = domain.working_day_after(today)
    alternative = domain.working_day_after(busy_day)
    workspace.scenario = {"busy_date": busy_day.isoformat(), "alternative_date": alternative.isoformat(),
                          "week_start": domain.week_start(busy_day).isoformat()}
    db.execute(insert(Catalogue).values(id='juniper-v1', version=1, rules={
        'rates': domain.RATES, 'staff': list(domain.STAFF_IDS), 'hours': [9,18], 'days': [0,1,2,3,4,5],
        'currency': 'USD', 'oven_cents': 2500, 'oven_minutes': 30}).on_conflict_do_nothing())
    for staff_id, name in [('ada', 'Ada'), ('noah', 'Noah')]:
        db.add(Staff(workspace_id=workspace.id, id=staff_id, name=name))
    db.flush()
    for offset in range(30):
        day = today + timedelta(days=offset)
        if day.weekday() == 6 or day == alternative:
            continue
        intervals = [('ada', 9, 18), ('noah', 9, 18)] if day == busy_day else (
            [('ada',9,12),('noah',14,16)] if offset % 3 == 0 else [('ada',13,15)] if offset % 3 == 1 else [])
        for staff, start_hour, end_hour in intervals:
            start = domain.local_to_utc(datetime.combine(day,time(start_hour)),workspace.timezone)
            end = domain.local_to_utc(datetime.combine(day,time(end_hour)),workspace.timezone)
            db.add(Reservation(workspace_id=workspace.id, staff_id=staff, starts_at=start, ends_at=end,
                               state='blocked', label='Existing appointment'))
    workspace.seeded = True
    db.flush()


def _seed_calendar_history(db, workspace: Workspace, now: datetime):
    """Add examples once, including to guests whose working calendar is already exposed.

    Callers hold the workspace lock. Never move a blocker or infer that a real
    booking completed; these are separate historical Juniper appointments.
    """
    if db.scalar(select(Activity.id).where(Activity.workspace_id==workspace.id,
                                         Activity.kind=='calendar_examples_v1').limit(1)):
        return
    today=now.astimezone(ZoneInfo(workspace.timezone)).date()
    completed=0
    for offset in range(1,15):
        day=today-timedelta(days=offset)
        if day.weekday()==6:
            continue
        start=domain.local_to_utc(datetime.combine(day,time(9)),workspace.timezone)
        end=domain.local_to_utc(datetime.combine(day,time(11)),workspace.timezone)
        for staff in (('ada','noah') if completed==0 else ('noah','ada')):
            occupied=db.scalar(select(Reservation.id).where(Reservation.workspace_id==workspace.id,
                Reservation.staff_id==staff,Reservation.state!='cancelled',
                Reservation.starts_at<end,Reservation.ends_at>start).limit(1))
            if occupied:
                continue
            db.add(Reservation(workspace_id=workspace.id,staff_id=staff,starts_at=start,ends_at=end,
                               state='completed',label='Home clean'))
            db.flush()
            completed+=1
            break
        if completed==2:
            break
    week=domain.week_start(today)
    for offset,staff,hour,label in [(1,'noah',13,'Deep clean'),(3,'ada',15,'Home clean')]:
        day=week+timedelta(days=offset)
        db.add(Reservation(workspace_id=workspace.id,staff_id=staff,
            starts_at=domain.local_to_utc(datetime.combine(day,time(hour)),workspace.timezone),
            ends_at=domain.local_to_utc(datetime.combine(day,time(hour+2)),workspace.timezone),
            state='cancelled',label=label))
    db.add(Activity(workspace_id=workspace.id,kind='calendar_examples_v1',created_at=now,reference='juniper-v1'))
    workspace.revision+=1
    db.flush()


def clear_calendar_entry(db, workspace, booking_id, revision, now):
    require_revision(workspace,revision)
    reservation=db.get(Reservation,(workspace.id,booking_id),with_for_update=True)
    if reservation is None:
        raise DomainError('APPOINTMENT_UNAVAILABLE','That appointment is unavailable.',404)
    if reservation.state!='cancelled':
        raise DomainError('APPOINTMENT_NOT_CANCELLED','Only cancelled appointments can be removed from the calendar.')
    cleared=db.scalar(select(Activity.id).where(Activity.workspace_id==workspace.id,
        Activity.kind=='calendar_cleared',Activity.reference==str(booking_id)).limit(1))
    if not cleared:
        db.add(Activity(workspace_id=workspace.id,kind='calendar_cleared',created_at=now,reference=str(booking_id)))
        workspace.revision+=1
    return {'request_id':None}


def current_quote(workspace):
    fields = workspace.draft
    if fields.get('service') and fields.get('bedrooms'):
        return domain.quote(fields['service'],fields['bedrooms'],fields.get('oven',False),workspace.revision)
    return None


def busy_records(db, workspace, *, exclude_enquiry=None):
    query=select(Reservation).where(Reservation.workspace_id==workspace.id,Reservation.state!='cancelled')
    if exclude_enquiry is not None:
        query=query.where((Reservation.enquiry_id.is_(None)) | (Reservation.enquiry_id!=exclude_enquiry))
    return [domain.Busy(row.staff_id,row.starts_at,row.ends_at) for row in db.scalars(query)]


def week_view(db, workspace, now, week: date | None = None):
    ensure_seeded(db,workspace,now)
    quote=current_quote(workspace)
    if not quote:
        raise DomainError('SERVICE_REQUIRED','Choose a service and home size to see available times.',422)
    week=week or domain.week_start(now.astimezone(ZoneInfo(workspace.timezone)).date())
    return domain.availability(week,quote['minutes'],workspace.timezone,now,busy_records(db,workspace))


def idempotency_status(db, workspace, key: str | None, operation: str, body: dict):
    """Validate/replay before external work without claiming business success."""
    try:
        if not key or len(key)!=36:
            raise ValueError()
        UUID(key)
    except (ValueError, TypeError):
        raise DomainError('IDEMPOTENCY_REQUIRED','Refresh the action and try again.',422) from None
    fingerprint=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    previous=db.get(Idempotency,(workspace.id,key))
    if previous:
        if previous.operation!=operation or previous.request_hash!=fingerprint:
            raise DomainError('IDEMPOTENCY_MISMATCH','That action key was already used for different details.')
        return fingerprint, {**previous.result,'replayed':True}
    if db.scalar(select(func.count()).select_from(Idempotency).where(Idempotency.workspace_id==workspace.id))>=200:
        raise DomainError('DEMO_LIMIT','This demo has reached its action limit. Start a fresh demo.',429)
    return fingerprint, None


def idempotent(db, workspace, key: str | None, operation: str, body: dict, apply):
    fingerprint, previous = idempotency_status(db, workspace, key, operation, body)
    if previous is not None:
        return previous
    result=apply()
    result['applied_revision']=workspace.revision
    db.add(Idempotency(workspace_id=workspace.id,key=key,operation=operation,request_hash=fingerprint,result=result))
    db.flush()
    return {**result,'replayed':False}


def require_revision(workspace, revision):
    if workspace.revision!=revision:
        raise DomainError('STALE_REVISION','The request changed. Review the current details before continuing.')


def update_draft(db, workspace, fields: dict, revision: int, now: datetime):
    require_revision(workspace,revision)
    draft={**workspace.draft,**fields}
    if 'preferred_at' not in fields and any(key in fields and fields[key]!=workspace.draft.get(key) for key in ['service','bedrooms','oven']):
        draft['preferred_at']=None
    if draft.get('service') and draft.get('bedrooms'):
        quote=domain.quote(draft['service'],draft['bedrooms'],draft.get('oven',False),workspace.revision+1)
    else:
        quote=None
    if draft.get('preferred_at'):
        if not quote:
            raise DomainError('SERVICE_REQUIRED','Choose a cleaning before choosing a time.',422)
        start=domain.validate_start(datetime.fromisoformat(draft['preferred_at']),quote['minutes'],workspace.timezone,now)
        if not domain.eligible(start,quote['minutes'],busy_records(db,workspace)):
            raise DomainError('TIME_OCCUPIED','That time is occupied. Choose an available alternative.')
        draft['preferred_at']=start.isoformat()
        workspace.scenario={**workspace.scenario,'requested_date':start.astimezone(ZoneInfo(workspace.timezone)).date().isoformat(),
                            'requested_time':start.astimezone(ZoneInfo(workspace.timezone)).strftime('%H:%M')}
    workspace.draft=draft
    workspace.revision+=1
    return {'request_id':None}


def submit_request(db, workspace, revision: int, now: datetime):
    require_revision(workspace,revision)
    quote=current_quote(workspace)
    if not quote or not workspace.draft.get('preferred_at'):
        raise DomainError('REVIEW_REQUIRED','Choose a cleaning and a time, then review the quote.',422)
    if db.scalar(select(func.count()).select_from(Enquiry).where(Enquiry.workspace_id==workspace.id))>=10:
        raise DomainError('REQUEST_LIMIT','This demo has reached ten requests. Start a fresh demo.',429)
    start=domain.validate_start(datetime.fromisoformat(workspace.draft['preferred_at']),quote['minutes'],workspace.timezone,now)
    if not domain.eligible(start,quote['minutes'],busy_records(db,workspace)):
        raise DomainError('TIME_OCCUPIED','That time became occupied. Choose another time.')
    enquiry=Enquiry(workspace_id=workspace.id,revision=1,status='awaiting_review',fields=dict(workspace.draft),
                    quote=quote,preferred_at=start,created_at=now)
    db.add(enquiry);db.flush()
    workspace.revision+=1
    db.add(Activity(workspace_id=workspace.id,kind='request_submitted',created_at=now,reference=str(enquiry.id)))
    return {'request_id':str(enquiry.id)}


def owned_request(db,workspace,request_id):
    enquiry=db.get(Enquiry,(workspace.id,request_id),with_for_update=True)
    if enquiry is None:
        raise DomainError('REQUEST_UNAVAILABLE','That request is unavailable.',404)
    return enquiry


def queue_crm(db,workspace,enquiry,now):
    if workspace.crm_mode!='connected':
        return 'not_connected'
    connection=db.scalar(select(Connection).where(Connection.workspace_id==workspace.id,Connection.state=='ready').order_by(Connection.created_at.desc()).limit(1))
    if not connection or not connection.export_consent:
        return 'not_shared'
    db.add(Outbox(workspace_id=workspace.id,enquiry_id=enquiry.id,connection_id=connection.id,
                  account_id=connection.account_id,connection_generation=connection.generation,
                  workspace_generation=workspace.generation,revision=enquiry.revision,kind='crm_upsert',
                  state='pending',attempts=0,due_at=now))
    return 'pending'


def booking_receipt(db,workspace,enquiry,reservation,action,now):
    crm_state=queue_crm(db,workspace,enquiry,now) if reservation else ('not_shared' if workspace.crm_mode=='connected' else 'not_connected')
    db.add(Activity(workspace_id=workspace.id,kind='booking_'+action,created_at=now,reference=str(enquiry.id)))
    db.flush()
    return {'request_id':str(enquiry.id),'receipt':{'action':action,'status':'accepted',
            'booking_id':str(reservation.id) if reservation else None,'enquiry_revision':enquiry.revision,'crm_state':crm_state}}


def booking_command(db,workspace,request_id,action,body,now):
    require_revision(workspace,body.revision)
    enquiry=owned_request(db,workspace,request_id)
    if enquiry.revision!=body.request_revision:
        raise DomainError('STALE_REQUEST','The booking changed. Review its current details.')
    reservation=db.scalar(select(Reservation).where(Reservation.workspace_id==workspace.id,Reservation.enquiry_id==enquiry.id).with_for_update())
    if action in {'approve','reschedule'}:
        expected='awaiting_review' if action=='approve' else 'confirmed'
        if enquiry.status!=expected:
            raise DomainError('STATUS_CHANGED','This request is no longer waiting for that action.')
        verified=domain.quote(enquiry.fields['service'],enquiry.fields['bedrooms'],enquiry.fields.get('oven',False),enquiry.quote['revision'])
        if verified!=enquiry.quote:
            raise DomainError('QUOTE_CHANGED','The saved quote needs a fresh review.')
        proposed=getattr(body,'preferred_at',None)
        if action=='reschedule' and proposed is None:
            raise DomainError('REVIEW_REQUIRED','Choose and review a new time before rescheduling.',422)
        start=domain.validate_start(proposed or enquiry.preferred_at,enquiry.quote['minutes'],workspace.timezone,now)
        candidates=domain.eligible(start,enquiry.quote['minutes'],busy_records(db,workspace,exclude_enquiry=enquiry.id))
        selected=getattr(body,'staff_id',None)
        if (selected and selected not in candidates) or not candidates:
            raise DomainError('TIME_OCCUPIED','That cleaner cannot fit the full appointment. Choose another time or cleaner.')
        staff=selected or (reservation.staff_id if reservation and reservation.staff_id in candidates else candidates[0])
        if action=='reschedule' and reservation and reservation.starts_at==start and reservation.staff_id==staff:
            return {'request_id':str(enquiry.id),'receipt':None}
        if reservation is None:
            reservation=Reservation(workspace_id=workspace.id,enquiry_id=enquiry.id,staff_id=staff,
                                    starts_at=start,ends_at=start+timedelta(minutes=enquiry.quote['minutes']),
                                    state='confirmed',label=domain.NAMES[enquiry.fields['service']])
            db.add(reservation)
        else:
            reservation.starts_at=start;reservation.ends_at=start+timedelta(minutes=enquiry.quote['minutes'])
            reservation.staff_id=staff
        enquiry.preferred_at=start
        enquiry.fields={**enquiry.fields,'preferred_at':start.isoformat()}
        enquiry.status='confirmed'
    elif action=='cancel':
        if enquiry.status not in {'awaiting_review','confirmed'}:
            raise DomainError('STATUS_CHANGED','This request can no longer be cancelled.')
        enquiry.status='cancelled'
        if reservation:reservation.state='cancelled'
    elif action=='complete':
        if enquiry.status!='confirmed' or not reservation:
            raise DomainError('STATUS_CHANGED','Only a confirmed booking can be completed.')
        enquiry.status='completed';reservation.state='completed'
    else:
        raise DomainError('ACTION_UNAVAILABLE','That action is unavailable.',422)
    enquiry.revision+=1;workspace.revision+=1
    return booking_receipt(db,workspace,enquiry,reservation,{'approve':'confirmed','reschedule':'rescheduled','cancel':'cancelled','complete':'completed'}[action],now)


def request_week(db,workspace,enquiry,now,week=None):
    day=week or domain.week_start(enquiry.preferred_at.astimezone(ZoneInfo(workspace.timezone)).date())
    # A past preference does not hide today's actionable alternatives.
    today_week=domain.week_start(now.astimezone(ZoneInfo(workspace.timezone)).date())
    return domain.availability(max(day,today_week),enquiry.quote['minutes'],workspace.timezone,now,
                               busy_records(db,workspace,exclude_enquiry=enquiry.id))
