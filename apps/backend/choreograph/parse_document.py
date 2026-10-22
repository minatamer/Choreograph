"""Fixed, isolated parser child. No model, HTTP or application configuration."""
import io
import json
import os
import re
import sys

MAX_BYTES=2*1024*1024
MAX_TEXT=32_000


def memory_limit():
    if os.name!='nt':
        import resource
        resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
        resource.setrlimit(resource.RLIMIT_CPU,(5,5))
        return None
    # Attach this child before reading untrusted bytes. Keep its job handle alive.
    import ctypes as c
    from ctypes import wintypes as w
    class Basic(c.Structure):
        _fields_=[('process_time',c.c_int64),('job_time',c.c_int64),('flags',w.DWORD),
                  ('min_working',c.c_size_t),('max_working',c.c_size_t),('active',w.DWORD),
                  ('affinity',c.c_size_t),('priority',w.DWORD),('scheduling',w.DWORD)]
    class IO(c.Structure):
        _fields_=[(name,c.c_uint64) for name in ('read_ops','write_ops','other_ops','read_bytes','write_bytes','other_bytes')]
    class Extended(c.Structure):
        _fields_=[('basic',Basic),('io',IO),('process_memory',c.c_size_t),('job_memory',c.c_size_t),
                  ('peak_process',c.c_size_t),('peak_job',c.c_size_t)]
    kernel=c.WinDLL('kernel32',use_last_error=True)
    kernel.CreateJobObjectW.argtypes=[c.c_void_p,w.LPCWSTR];kernel.CreateJobObjectW.restype=w.HANDLE
    kernel.SetInformationJobObject.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD];kernel.SetInformationJobObject.restype=w.BOOL
    kernel.GetCurrentProcess.restype=w.HANDLE
    kernel.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE];kernel.AssignProcessToJobObject.restype=w.BOOL
    job=kernel.CreateJobObjectW(None,None)
    info=Extended();info.basic.flags=0x100;info.process_memory=256*1024*1024
    if not job or not kernel.SetInformationJobObject(job,9,c.byref(info),c.sizeof(info)) or not kernel.AssignProcessToJobObject(job,kernel.GetCurrentProcess()):
        raise ValueError('PARSER_LIMIT_UNAVAILABLE')
    return job


def extract(data:bytes,kind:str):
    if not data or len(data)>MAX_BYTES:
        raise ValueError('DOCUMENT_TOO_LARGE')
    if kind=='pdf':
        from pypdf import PdfReader
        if not data.startswith(b'%PDF-'):
            raise ValueError('DOCUMENT_FORMAT')
        reader=PdfReader(io.BytesIO(data),strict=True)
        if reader.is_encrypted:
            raise ValueError('DOCUMENT_ENCRYPTED')
        if not 1<=len(reader.pages)<=10:
            raise ValueError('DOCUMENT_PAGES')
        forbidden={'/OpenAction','/AA','/JavaScript','/JS','/Launch','/EmbeddedFiles','/RichMedia','/AcroForm','/XFA'}
        visited=set();budget=10_000
        def walk(value,depth=0):
            nonlocal budget
            budget-=1
            if depth>40 or budget<0:
                raise ValueError('DOCUMENT_COMPLEX')
            if hasattr(value,'idnum'):
                key=(value.idnum,value.generation)
                if key in visited:return
                visited.add(key);value=value.get_object()
            if isinstance(value,dict):
                if forbidden.intersection(str(key) for key in value):raise ValueError('DOCUMENT_ACTIVE')
                for child in value.values():walk(child,depth+1)
            elif isinstance(value,list):
                for child in value:walk(child,depth+1)
        walk(reader.trailer)
        pages=[];size=0
        for number,page in enumerate(reader.pages,1):
            content=page.extract_text() or '';size+=len(content)
            if size>MAX_TEXT:raise ValueError('DOCUMENT_TEXT_LIMIT')
            if len(content.strip())<30:raise ValueError('DOCUMENT_NO_TEXT')
            pages.append({'page':number,'section':f'Page {number}','text':re.sub(r'\s+',' ',content).strip()})
        return pages
    text=data.decode('utf-8',errors='strict')
    if '\x00' in text or len(text)>MAX_TEXT or len(text.strip())<30:
        raise ValueError('DOCUMENT_TEXT_LIMIT')
    if re.search(r'<\s*(?:script|html|iframe|svg)\b',text,re.I):raise ValueError('DOCUMENT_FORMAT')
    pages=[]
    for part in re.split(r'(?m)^## ',text):
        if not part.strip():continue
        lines=part.strip().splitlines();section=lines[0].lstrip('# ').strip()[:180] or 'Text'
        pages.append({'page':1,'section':section,'text':part.strip()})
    if len(pages)>32:raise ValueError('DOCUMENT_COMPLEX')
    return pages


if __name__=='__main__':
    try:
        job=memory_limit()
        result=extract(sys.stdin.buffer.read(MAX_BYTES+1),sys.argv[1])
        print(json.dumps({'pages':result},ensure_ascii=True))
    except Exception:  # noqa: BLE001 - every child-parser failure must return a fixed code without document contents.
        print('{"code":"DOCUMENT_UNREADABLE"}')
        sys.exit(1)
