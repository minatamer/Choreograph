"""One independently selected CRM provider/client per process."""
from datetime import UTC, datetime

from .hubspot import CRMFailure, FakeHubSpot, HubSpotTransport


class DisabledCRM:
    provider='disabled'
    app_id='disabled'
    capacity=0
    def close(self):pass
    def authorization_url(self,state):raise CRMFailure('CRM_NOT_CONFIGURED')


def compose_crm(settings, engine, *, client=None, clock=None):
    if settings.crm_provider=='fake':return FakeHubSpot(engine)
    if settings.crm_provider=='disabled':return DisabledCRM()
    config=settings.live_crm
    if settings.crm_provider!='hubspot' or not config or settings.testing:
        raise ValueError('CRM_CONFIGURATION_INVALID')
    if config.allowance.expires_at is not None and config.allowance.expires_at<=(clock or (lambda:datetime.now(UTC)))():
        raise ValueError('CRM_ALLOWANCE_EXPIRED')
    provider=HubSpotTransport(config.transport,authorized=True,client=client,engine=engine,
                              allowance=config.allowance,clock=clock)
    provider.requires_admission=True
    return provider
