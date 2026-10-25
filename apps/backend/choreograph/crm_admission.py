"""Conservative CRM HTTP counts commit before requests and survive rollbacks."""
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from uuid import UUID, uuid4

from .hubspot import CRMFailure
from .models import CRMCall, CRMGrant
from .persistence import Session, advisory, repo_rows, storage_retry


@dataclass(frozen=True)
class CRMAllowance:
    grant_id: str
    app_id: str
    expires_at: datetime
    requests: int
    workspace_requests: int

    def __post_init__(self):
        if (not self.grant_id or len(self.grant_id)>80 or not self.app_id or len(self.app_id)>80 or
                self.expires_at.tzinfo is None or type(self.requests) is not int or
                type(self.workspace_requests) is not int or not 1<=self.workspace_requests<=self.requests<=1_000_000):
            raise ValueError('CRM_ALLOWANCE_INVALID')


@dataclass(frozen=True)
class ManualCRMAllowance:
    """Owner-operated local session; no aggregate request cap or deadline."""
    grant_id: str
    app_id: str

    def __post_init__(self):
        if not self.grant_id or len(self.grant_id)>80 or not self.app_id or len(self.app_id)>80:
            raise ValueError('CRM_ALLOWANCE_INVALID')

    expires_at = None
    requests = None
    workspace_requests = None


class CRMAdmission:
    def __init__(self, engine, allowance, workspace_id, clock):
        self.engine,self.allowance,self.workspace_id,self.clock=engine,allowance,UUID(str(workspace_id)),clock

    @storage_retry
    def reserve(self):
        now=self.clock();spec=asdict(self.allowance);expiry=self.allowance.expires_at
        if isinstance(self.allowance,ManualCRMAllowance):spec['policy']='local_owner_manual'
        else:spec['expires_at']=expiry.isoformat()
        if expiry is not None and now>=expiry:raise CRMFailure('CRM_ALLOWANCE_EXPIRED')
        digest=hashlib.sha256(json.dumps(spec,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        with Session(self.engine) as db,db.begin():
            advisory(db,45868,1)
            if expiry is not None and self.clock()>=expiry:raise CRMFailure('CRM_ALLOWANCE_EXPIRED')
            row=db.get(CRMGrant,self.allowance.grant_id)
            if row and (row.spec_hash!=digest or row.app_id!=self.allowance.app_id):raise CRMFailure('CRM_ALLOWANCE_CHANGED')
            if not row:
                row=CRMGrant(id=self.allowance.grant_id,app_id=self.allowance.app_id,spec_hash=digest,requests=0)
                db.add(row);db.flush()
            if not isinstance(self.allowance,ManualCRMAllowance):
                guest=len(repo_rows(db, CRMCall, filters={'grant_id': row.id, 'scope_key': str(self.workspace_id)}))
                if row.requests>=self.allowance.requests or guest>=self.allowance.workspace_requests:
                    raise CRMFailure('CRM_ALLOWANCE_LIMIT')
            row.requests+=1
            db.add(CRMCall(id=uuid4(),grant_id=row.id,scope_key=str(self.workspace_id),created_at=now))
