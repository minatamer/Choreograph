"""No Google account/network: exercise the exact conditional GCS request contract."""
import base64
import copy
import io
import json
from urllib.parse import unquote

import pytest

from choreograph.errors import DomainError
from choreograph.object_store import FileObjects, GCSObjects, ObjectEngine

POLICY={'iamConfiguration':{'publicAccessPrevention':'enforced','uniformBucketLevelAccess':{'enabled':True}}}


class Reply:
    def __init__(self,status=200,data=None,content=b'',headers=None):
        self.status_code=status;self.headers=headers or {};self.closed=False
        body=json.dumps(data).encode() if data is not None else content
        class Raw(io.BytesIO):
            def read1(self,amount,**_kwargs):return super().read1(amount)
        self.raw=Raw(body)
    def close(self):self.closed=True;self.raw.close()
    @property
    def content(self):raise AssertionError('Eager response materialization is forbidden')


class Storage:
    def __init__(self,policy=None):
        self.policy=copy.deepcopy(POLICY if policy is None else policy)
        self.objects={};self.calls=[];self.closed=False;self.status=None
    def get(self,url,**kwargs):
        self.calls.append(('GET',url,kwargs))
        if '/o/' not in url:return Reply(data=self.policy)
        name=unquote(url.split('/o/')[1]);item=self.objects.get(name)
        if not item:return Reply(404)
        generation,data=item
        if kwargs.get('params',{}).get('alt')=='media':
            assert kwargs['params']['generation']==str(generation)
            return Reply(content=data)
        return Reply(data={'generation':str(generation),'size':str(len(data))})
    def post(self,url,**kwargs):
        self.calls.append(('POST',url,kwargs))
        if self.status:return Reply(self.status)
        params=kwargs['params'];name=params['name'];expected=int(params['ifGenerationMatch'])
        actual=self.objects.get(name,(0,b''))[0]
        if expected!=actual:return Reply(412)
        self.objects[name]=(actual+1,kwargs['data'])
        return Reply(data={'generation':str(actual+1)})
    def close(self):self.closed=True


@pytest.mark.parametrize('bad',[
    {},{'iamConfiguration':{'publicAccessPrevention':'inherited','uniformBucketLevelAccess':{'enabled':True}}},
    {**POLICY,'versioning':{'enabled':True}},
    {**POLICY,'softDeletePolicy':{'retentionDurationSeconds':'604800'}},
    {**POLICY,'retentionPolicy':{'retentionPeriod':'86400'}},
])
def test_bucket_policy_fails_closed_before_any_object_write(bad):
    session=Storage(bad)
    with pytest.raises(ValueError,match='PRIVATE_STORAGE_POLICY_REQUIRED'):
        GCSObjects('test-private-bucket',session=session)
    assert session.closed and all(method=='GET' for method,_,_ in session.calls)


def test_generation_pinned_reads_and_conditional_writes_are_encrypted():
    session=Storage();store=GCSObjects('test-private-bucket',session=session)
    key=base64.urlsafe_b64encode(bytes(32)).decode();engine=ObjectEngine(store,key)
    engine.save({'example':[]},'0')
    assert b'example' not in session.objects['state/v1'][1]
    records,generation=engine.load();assert records['example']==[]
    engine.save({'example':[{'value':'safe server state'}]},generation)
    with pytest.raises(DomainError,match='WRITE_RETRY'):engine.save({},generation)
    assert engine.load()[0]['example']==[{'value':'safe server state'}]
    writes=[kwargs for method,_,kwargs in session.calls if method=='POST']
    assert all('ifGenerationMatch' in item['params'] and item['allow_redirects'] is False for item in writes)
    assert all(url.startswith('https://storage.googleapis.com/') for _,url,_ in session.calls)


def test_corruption_never_becomes_an_empty_successful_store():
    session=Storage();store=GCSObjects('test-private-bucket',session=session)
    key=base64.urlsafe_b64encode(bytes(32)).decode();engine=ObjectEngine(store,key)
    session.objects['state/v1']=(1,b'corrupted')
    with pytest.raises(DomainError,match='STORAGE_UNAVAILABLE'):engine.load()
    assert not any(method=='POST' for method,_,_ in session.calls)


def test_throttling_retries_only_the_same_conditional_object_write(monkeypatch):
    pauses=[];monkeypatch.setattr('choreograph.object_store.time.sleep',pauses.append)
    session=Storage();store=GCSObjects('test-private-bucket',session=session);session.status=429
    with pytest.raises(DomainError,match='WRITE_RETRY'):store.replace('state/v1',b'encrypted','0')
    writes=[kwargs for method,_,kwargs in session.calls if method=='POST']
    assert len(writes)==4 and pauses==[.4,.8,1.6]
    assert all(item['params']==writes[0]['params'] and item['data']==b'encrypted' for item in writes)


def test_concurrent_file_reads_and_replacements_never_lose_a_cas_update(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    store=FileObjects(tmp_path/'private')
    store.replace('counter',b'0','0')
    def increment(_):
        for _attempt in range(100):
            data,generation=store.read('counter')
            try:
                store.replace('counter',str(int(data)+1).encode(),generation)
                return
            except DomainError as error:
                assert error.code=='WRITE_RETRY'
        pytest.fail('conditional update did not settle')
    with ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(increment,range(40)))
    assert store.read('counter')[0]==b'40'


@pytest.mark.parametrize('headers',[{'content-length':'65537'},{'content-encoding':'gzip'},{'content-length':'private-error'}])
def test_oversized_or_encoded_responses_are_closed_before_reading(headers):
    session=Storage();store=GCSObjects('test-private-bucket',session=session)
    reply=Reply(data={'sensitive':'not public'},headers=headers)
    reply.raw.read1=lambda *_a,**_kw:pytest.fail('Body must not be read')
    session.get=lambda *_a,**_kw:reply
    with pytest.raises(DomainError,match='STORAGE_UNAVAILABLE') as caught:store.read('state/v1')
    assert reply.closed and 'sensitive' not in str(caught.value)


def test_chunked_media_is_bounded_before_materializing_and_late_reads_are_closed(monkeypatch):
    session=Storage();store=GCSObjects('test-private-bucket',session=session)
    monkeypatch.setattr('choreograph.object_store.MAX_BYTES',128)
    metadata=Reply(data={'generation':'1','size':'100'});body=Reply(content=b'x'*129)
    replies=iter([metadata,body]);session.get=lambda *_a,**_kw:next(replies)
    with pytest.raises(DomainError,match='STORAGE_UNAVAILABLE'):store.read('state/v1')
    assert body.closed
    reply=Reply(content=b'{}');session.get=lambda *_a,**_kw:reply
    times=iter([0,0,16]);monkeypatch.setattr('choreograph.object_store.time.monotonic',lambda:next(times))
    with pytest.raises(DomainError,match='STORAGE_UNAVAILABLE'):store.read('state/v1')
    assert reply.closed


def test_lost_upload_ack_never_replays_the_write_and_committed_state_is_recoverable():
    session=Storage();store=GCSObjects('test-private-bucket',session=session)
    engine=ObjectEngine(store,base64.urlsafe_b64encode(bytes(32)).decode())
    post=session.post
    def lost(*args,**kwargs):
        post(*args,**kwargs);raise TimeoutError('sensitive upstream detail')
    session.post=lost
    with pytest.raises(DomainError,match='STORAGE_UNAVAILABLE') as caught:engine.save({'example':[]},'0')
    assert 'sensitive' not in str(caught.value)
    assert len([call for call in session.calls if call[0]=='POST'])==1
    assert engine.load()[0]['example']==[]


def test_requests_raw_read1_path_handles_real_streamed_json_without_eager_content():
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    import requests
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body=json.dumps(POLICY).encode();self.send_response(200)
            self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        def log_message(self,*_args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    class LocalSession:
        def __init__(self):self.client=requests.Session();self.client.trust_env=False
        def get(self,url,**kwargs):
            assert url.startswith('https://storage.googleapis.com/')
            return self.client.get('http://127.0.0.1:'+str(server.server_port),**kwargs)
        def close(self):self.client.close()
    try:
        store=GCSObjects('test-private-bucket',session=LocalSession());store.close()
    finally:server.shutdown();server.server_close();thread.join(timeout=2)
