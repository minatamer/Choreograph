"""Request-bound queue publication; durable intent survives every failed attempt."""
from contextlib import suppress

from starlette.concurrency import run_in_threadpool


class ImmediatePublication:
    def __init__(self,app,*,engine,transport,clock):
        self.app=app;self.engine=engine;self.transport=transport;self.clock=clock

    async def __call__(self,scope,receive,send):
        async def response(message):
            if (message['type']=='http.response.start' and message['status']<300 and
                    scope.get('method') in {'POST','PUT','PATCH'} and scope.get('path','').startswith('/v1/')):
                from .dispatch import tick
                # A committed booking stays accepted; the maintenance sweep recovers failed publication.
                with suppress(Exception):
                    await run_in_threadpool(tick,self.engine,self.transport,self.clock,limit=1)
            await send(message)
        await self.app(scope,receive,response)
