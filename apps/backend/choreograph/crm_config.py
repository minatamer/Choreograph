"""Independent, explicit visitor OAuth configuration. No account is a fallback."""
import ipaddress
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from urllib.parse import urlsplit

from .crm_admission import CRMAllowance, ManualCRMAllowance
from .hubspot import HubSpotConfig


@dataclass(frozen=True)
class LiveCRMConfig:
    transport: HubSpotConfig = field(repr=False)
    allowance: CRMAllowance | ManualCRMAllowance


def parse_live_crm(values, origin, *, now=None, manual_grant_id=None):
    app_id=values.get('CHOREOGRAPH_HUBSPOT_APP_ID','')
    client=values.get('CHOREOGRAPH_HUBSPOT_CLIENT_ID','')
    secret=values.get('CHOREOGRAPH_HUBSPOT_CLIENT_SECRET','')
    callback=values.get('CHOREOGRAPH_HUBSPOT_REDIRECT_URI','')
    parsed=urlsplit(origin)
    try:
        valid_origin=bool(parsed.hostname and not (parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password)
                          and (parsed.port is None or 1<=parsed.port<=65535))
    except ValueError:valid_origin=False
    try:
        ipaddress.ip_address(parsed.hostname or '')
        domain=False
    except ValueError:domain=True
    if (not re.fullmatch(r'[0-9]{1,30}',app_id) or not re.fullmatch(r'[A-Za-z0-9-]{1,100}',client) or
            not 1<=len(secret)<=512 or any(char.isspace() for char in secret) or
            callback!=origin+'/auth/hubspot/callback' or not valid_origin or not domain or
            (parsed.scheme!='https' and origin!='http://localhost:45860')):
        raise ValueError('CRM_CONFIGURATION_INVALID')
    distribution=values.get('CHOREOGRAPH_HUBSPOT_DISTRIBUTION','')
    maximum={'private':10,'marketplace_unlisted':25}.get(distribution,0)
    def number(name,cap):
        raw=values.get(name,'')
        if not re.fullmatch(r'[1-9][0-9]{0,6}',raw) or not 1<=int(raw)<=cap:raise ValueError('CRM_CONFIGURATION_INVALID')
        return int(raw)
    capacity=number('CHOREOGRAPH_HUBSPOT_CAPACITY',maximum)
    schema=values.get('CHOREOGRAPH_HUBSPOT_SCHEMA_SETUP_ALLOWED','false')
    if schema not in {'true','false'}:raise ValueError('CRM_CONFIGURATION_INVALID')
    grant=manual_grant_id if manual_grant_id is not None else values.get('CHOREOGRAPH_CRM_GRANT_ID','')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,79}',grant):raise ValueError('CRM_CONFIGURATION_INVALID')
    if manual_grant_id is not None:
        allowance=ManualCRMAllowance(grant,app_id)
    else:
        try:
            expiry=datetime.fromisoformat(values.get('CHOREOGRAPH_CRM_EXPIRES_AT','').replace('Z','+00:00'))
            if expiry.tzinfo is None or expiry<=(now or datetime.now(UTC)):raise ValueError()
        except (ValueError,TypeError):raise ValueError('CRM_ALLOWANCE_INVALID') from None
        allowance=CRMAllowance(grant,app_id,expiry,number('CHOREOGRAPH_CRM_REQUESTS',1_000_000),
                               number('CHOREOGRAPH_CRM_WORKSPACE_REQUESTS',1_000_000))
    return LiveCRMConfig(HubSpotConfig(app_id,client,secret,callback,schema_setup_allowed=schema=='true',
                                      capacity=capacity,distribution=distribution),allowance)
