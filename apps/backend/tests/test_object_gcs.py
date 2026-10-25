"""No Google account/network: exercise the exact conditional GCS request contract."""
import base64
import copy
from urllib.parse import unquote

import pytest

from choreograph.errors import DomainError
from choreograph.object_store import FileObjects, GCSObjects, ObjectEngine

POLICY={'iamConfiguration':{'publicAccessPrevention':'enforced','uniformBucketLevelAccess':{'enabled':True}}}


class Reply:
    def __init__(self,status=200,data=None,content=b''):
        self.status_code=status;self.data=data;self.content=content
    def json(self):return self.data


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
