"""Offline release rendering and bounded, explicitly requested control-plane reads.

This tool never provisions, deploys, writes IAM, sends tasks or reads secret bytes.
Generated commands/REST requests are review artifacts for a later authorized run.
"""
import argparse
import base64
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path

from .readiness import ROOT

TEMPLATES=('cloud-run.example.yaml','iam.example.json','worker-pool.example.json')
OBJECT_TEMPLATES=('cloud-run.object.example.yaml','iam.object.example.json','scheduler.object.example.json')
DERIVED={'REPLACE_THROWAWAY_SETTINGS_ONLY_32_PLUS_CHARACTERS':'settings-only-'+'x'*40,
         'REPLACE_THROWAWAY_SETTINGS_ONLY_BASE64URL_32_BYTES':base64.urlsafe_b64encode(bytes(32)).decode()}


def required_fields(storage='objects'):
    if storage not in {'objects','postgres'}:raise ValueError('CLOUD_STORAGE_MODE_INVALID')
    source='\n'.join((ROOT/'infra'/name).read_text() for name in (OBJECT_TEMPLATES if storage=='objects' else TEMPLATES))
    if storage=='objects':source+=' REPLACE_PREPARE_KNOWLEDGE_JOB_NAME'
    if storage=='postgres':source+=json.dumps(json.loads((ROOT/'infra/cloud-tasks.example.json').read_text())['queue'])
    return sorted(set(re.findall(r'REPLACE_[A-Z0-9_]+',source))-DERIVED.keys())


def validate(values,storage='objects'):
    required=required_fields(storage)
    if set(values)!=set(required):raise ValueError('CLOUD_INPUT_FIELDS_INVALID')
    for key,value in values.items():
        if not isinstance(value,str) or not 1<=len(value)<=180 or 'REPLACE_' in value:raise ValueError('CLOUD_INPUT_INVALID')
        pattern=r'[a-z][a-z0-9-]{0,61}[a-z0-9]'
        if key=='REPLACE_PROJECT_ID':pattern=r'[a-z][a-z0-9-]{4,28}[a-z0-9]'
        elif key=='REPLACE_PROJECT_NUMBER' or 'PINNED_' in key:pattern=r'[1-9][0-9]{0,19}'
        elif key=='REPLACE_REGION':pattern=r'[a-z]+-[a-z]+[0-9]{1,2}'
        elif key.endswith('_IMAGE_DIGEST'):pattern=r'[a-f0-9]{64}'
        elif key=='REPLACE_QA_TESTERS_GROUP':pattern=r'[a-zA-Z0-9._+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        elif key.endswith('_SA'):pattern=r'[a-z][a-z0-9-]{4,28}[a-z0-9]'
        elif key.endswith('_SECRET_NAME'):pattern=r'[a-zA-Z0-9_-]{1,100}'
        elif key.endswith('_SERVICE_ORIGIN'):pattern=r'[a-z0-9](?:[a-z0-9.-]{0,120}[a-z0-9])?'
        if not re.fullmatch(pattern,value):raise ValueError('CLOUD_INPUT_INVALID')
    identities=[value for key,value in values.items() if key.endswith('_SA')]
    if len(set(identities))!=len(identities):raise ValueError('CLOUD_IDENTITIES_MUST_DIFFER')
    names=[value for key,value in values.items() if key.endswith('_SERVICE_NAME') or key.endswith('_JOB_NAME')]
    if len(set(names))!=len(names):raise ValueError('CLOUD_SERVICES_MUST_DIFFER')
    origins=[value for key,value in values.items() if key.endswith('_SERVICE_ORIGIN')]
    if len(set(origins))!=3 or any('..' in host for host in origins):raise ValueError('CLOUD_ORIGINS_MUST_DIFFER')
    return {**values,**DERIVED}


def substitute(source,values):
    return re.sub(r'REPLACE_[A-Z0-9_]+',lambda match:values[match[0]],source)


def render(values,storage='objects'):
    if storage=='objects':return render_objects(values)
    import yaml
    replacements=validate(values,storage)
    rendered={}
    for name in TEMPLATES:
        rendered[name.replace('.example','')]=substitute((ROOT/'infra'/name).read_text(),replacements)
    resources=list(yaml.safe_load_all(rendered.pop('cloud-run.yaml')))
    for resource in resources:
        name=resource['metadata']['name']
        rendered[name+'.yaml']=yaml.safe_dump(resource,sort_keys=False)
    queue=json.loads(substitute(json.dumps(json.loads((ROOT/'infra/cloud-tasks.example.json').read_text())['queue']),replacements))
    rendered['queue.json']=json.dumps(queue,indent=2)
    # Reserve actual stable URLs with private health-only services. This has no
    # database/provider settings and cannot serve the guest API or accept tasks.
    bootstrap=[]
    for resource in resources[:3]:
        initial=copy.deepcopy(resource);container=initial['spec']['template']['spec']['containers'][0]
        container['image']=resources[1]['spec']['template']['spec']['containers'][0]['image']
        container['command']=['python','-m','choreograph.release'];container['args']=['bootstrap'];container['env']=[]
        container['startupProbe']['httpGet']['path']='/health'
        initial['spec']['template']['metadata']['annotations'].pop('run.googleapis.com/cloudsql-instances',None)
        initial['metadata']['annotations']['run.googleapis.com/description']='Private bootstrap only; application_ready=false'
        rendered['bootstrap-'+initial['metadata']['name']+'.yaml']=yaml.safe_dump(initial,sort_keys=False)
        bootstrap.append(initial['metadata']['name'])
    project=values['REPLACE_PROJECT_ID'];region=values['REPLACE_REGION']
    common=['--project',project,'--region',region]
    commands=[{'stage':'bootstrap','argv':['gcloud','run','services','replace','bootstrap-'+name+'.yaml',*common]} for name in bootstrap]
    commands.extend({'stage':'discover-or-verify-urls','argv':['gcloud','run','services','describe',name,*common,'--format=value(status.url)']} for name in bootstrap)
    commands.extend({'stage':'apply-job-definition','argv':['gcloud','run','jobs','replace',resource['metadata']['name']+'.yaml',*common]} for resource in resources if resource['kind']=='Job')
    for key in ('REPLACE_MIGRATE_JOB_NAME','REPLACE_PREPARE_KNOWLEDGE_JOB_NAME'):
        commands.append({'stage':'explicit-job-execution','argv':['gcloud','run','jobs','execute',values[key],*common,'--wait']})
    commands.extend({'stage':'apply-application-after-migration','argv':['gcloud','run','services','replace',name+'.yaml',*common]} for name in bootstrap)
    # v2 JSON is used directly as a REST request; do not pass a v2 WorkerPool
    # object to gcloud's v1 YAML replace command.
    worker=json.loads(rendered['worker-pool.json'])
    rest=[{'stage':'queue-create','method':'POST','url':f'https://cloudtasks.googleapis.com/v2/projects/{project}/locations/{region}/queues','body_file':'queue.json'},
          {'stage':'dispatcher-create-last','method':'POST','url':f'https://run.googleapis.com/v2/projects/{project}/locations/{region}/workerPools?workerPoolId='+values['REPLACE_DISPATCHER_POOL_NAME'],'body_file':'worker-pool.json'},
          {'stage':'dispatcher-update','method':'PATCH','url':'https://run.googleapis.com/v2/'+worker['name']+'?updateMask=template,scaling','body_file':'worker-pool.json'}]
    return rendered,{'mode':'offline-review-plan','cloud_changes':0,'provider_calls':0,'commands':commands,'rest_requests':rest,
        'prerequisites':['owner-approved project/billing/region, managed PostgreSQL17/pgvector and backup/restore plan',
            'pushed immutable images, separate service accounts, restricted SQL application/migration roles',
            'numeric Secret Manager versions containing only owner-entered values',
            'merge resourcePolicyAdditions into freshly read policies, preserving etags and unrelated bindings',
            'verify discovered stable service URLs equal rendered origins; rerender if different',
            'verify queue overrides, OIDC/IAM negative tests, stopped-dispatcher recovery and native CRM cleanup before release'],
        'scope':'restricted fake-provider cloud QA; real AI/visitor OAuth activation is a separate reviewed configuration change'}


def render_objects(values):
    """The selected private-object QA topology; no SQL or continuous worker."""
    import yaml

    from .runtime_config import OBJECT_BUCKET
    replacements=validate(values,'objects')
    source=substitute((ROOT/'infra/cloud-run.object.example.yaml').read_text(),replacements)
    resources=list(yaml.safe_load_all(source));rendered={};commands=[]
    project=values['REPLACE_PROJECT_ID'];region=values['REPLACE_REGION'];common=['--project',project,'--region',region]
    for resource in resources:
        name=resource['metadata']['name'];rendered[name+'.yaml']=yaml.safe_dump(resource,sort_keys=False)
        initial=copy.deepcopy(resource);container=initial['spec']['template']['spec']['containers'][0]
        container['image']=resources[1]['spec']['template']['spec']['containers'][0]['image']
        container['command']=['python','-m','choreograph.release'];container['args']=['bootstrap'];container['env']=[]
        container['startupProbe']['httpGet']['path']='/health'
        initial['metadata']['annotations']['run.googleapis.com/description']='Private bootstrap only; application_ready=false'
        rendered['bootstrap-'+name+'.yaml']=yaml.safe_dump(initial,sort_keys=False)
        commands.append({'stage':'bootstrap','argv':['gcloud','run','services','replace','bootstrap-'+name+'.yaml',*common]})
    commands.extend({'stage':'discover-or-verify-urls','argv':['gcloud','run','services','describe',row['metadata']['name'],*common,'--format=value(status.url)']} for row in resources)
    rendered['iam.json']=substitute((ROOT/'infra/iam.object.example.json').read_text(),replacements)
    scheduler=json.loads(substitute((ROOT/'infra/scheduler.object.example.json').read_text(),replacements))
    rendered['scheduler.json']=json.dumps(scheduler,indent=2)
    bucket=copy.deepcopy(json.loads((ROOT/'infra/object-storage.example.json').read_text())['bucket'])
    if bucket['name']!=OBJECT_BUCKET:raise ValueError('OBJECT_BUCKET_IDENTITY_MISMATCH')
    bucket['location']=region;rendered['bucket.json']=json.dumps(bucket,indent=2)
    # An explicit fake-only preparation job establishes all six sources before
    # traffic. A live pack needs separately authorized preparation/promotion.
    api_spec=resources[1]['spec']['template']['spec'];prepare=copy.deepcopy(api_spec['containers'][0])
    prepare['args']=['prepare-knowledge'];prepare.pop('ports',None);prepare.pop('startupProbe',None)
    prepare['env']=[row for row in prepare['env'] if row['name'] in {'DATABASE_ENABLED','FAKE_MODE','PAID_DEMO_ENABLED','CHOREOGRAPH_ORIGIN','CHOREOGRAPH_BRIDGE_SECRET','CHOREOGRAPH_TOKEN_KEY'}]
    job_name=values['REPLACE_PREPARE_KNOWLEDGE_JOB_NAME']
    job={'apiVersion':'run.googleapis.com/v1','kind':'Job','metadata':{'name':job_name,'namespace':values['REPLACE_PROJECT_NUMBER']},
        'spec':{'template':{'spec':{'taskCount':1,'parallelism':1,'template':{'spec':{'serviceAccountName':api_spec['serviceAccountName'],
            'maxRetries':0,'timeoutSeconds':300,'containers':[prepare]}}}}}}
    rendered[job_name+'.yaml']=yaml.safe_dump(job,sort_keys=False)
    commands.extend([{'stage':'apply-fake-preparation-job','argv':['gcloud','run','jobs','replace',job_name+'.yaml',*common]},
                     {'stage':'prepare-fake-sources-after-storage-iam','argv':['gcloud','run','jobs','execute',job_name,*common,'--wait']}])
    commands.extend({'stage':'apply-after-storage-iam-and-corpus-readiness','argv':['gcloud','run','services','replace',row['metadata']['name']+'.yaml',*common]} for row in resources)
    rest=[{'stage':'private-bucket-create','method':'POST','url':f'https://storage.googleapis.com/storage/v1/b?project={project}','body_file':'bucket.json'},
          {'stage':'maintenance-create-last','method':'POST','url':f'https://cloudscheduler.googleapis.com/v1/projects/{project}/locations/{region}/jobs','body_file':'scheduler.json'}]
    return rendered,{'mode':'offline-review-plan','storage':'objects','cloud_changes':0,'provider_calls':0,'commands':commands,'rest_requests':rest,
        'prerequisites':['owner-approved project/region/cost scope and pushed immutable images',
            'fresh private bucket with enforced public-access prevention, uniform IAM and no retained object history',
            'merge exact-resource IAM additions with fresh etags; create custom roles and preserve service-agent permissions',
            'numeric secret versions and distinct frontend/API/worker/maintenance identities',
            'verify stable origins, prepare all six profile-matching sources and pass runtime readiness before traffic',
            'verify hosted storage contention/memory, OIDC negative cases, duplicate/crashed sweeps and browser-closed cleanup',
            'real AI/HubSpot need fresh finite hosted authority, provider secrets and hostname/callback setup'],
        'scope':'restricted fake-provider object-storage QA only; unapplied and not a public/live deployment approval'}


def preflight(values,*,storage='objects',runner=subprocess.run):
    """At most eight gcloud describe reads. No secret access or account login."""
    validate(values,storage);project=values['REPLACE_PROJECT_ID'];region=values['REPLACE_REGION']
    commands=[['projects','describe',project]]
    if storage=='postgres':commands.extend([['tasks','queues','describe',values['REPLACE_QUEUE_NAME'],'--location',region],['sql','instances','describe',values['REPLACE_SQL_INSTANCE']]])
    else:
        from .runtime_config import OBJECT_BUCKET
        commands.append(['storage','buckets','describe','gs://'+OBJECT_BUCKET])
    commands.extend(['run','services','describe',values[key],'--region',region] for key in
        ('REPLACE_FRONTEND_SERVICE_NAME','REPLACE_API_SERVICE_NAME','REPLACE_WORKER_SERVICE_NAME'))
    commands.append(['run','worker-pools','describe',values['REPLACE_DISPATCHER_POOL_NAME'],'--region',region] if storage=='postgres' else
                    ['scheduler','jobs','describe',values['REPLACE_MAINTENANCE_JOB_NAME'],'--location',region])
    checks=[]
    for args in commands:
        result=runner(['gcloud',*args,'--project',project,'--format=json','--quiet'],capture_output=True,text=True,timeout=15,check=False)
        # Retain only a bounded content-free control-plane receipt. Resource
        # descriptions/IAM can contain environment values: never echo stdout.
        checks.append({'resource_kind':args[:2],'readable':result.returncode==0})
    return {'mode':'read-only-cloud-preflight','writes':0,'reads':len(checks),'checks':checks,
            'acceptance':'resource presence only; not deployed IAM/recovery/provider evidence'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--storage',choices=['objects','postgres'],default='objects')
    parser.add_argument('--config',type=Path);parser.add_argument('--output',type=Path)
    parser.add_argument('--execute-preflight',action='store_true')
    args=parser.parse_args()
    try:
        if args.config is None:
            print(json.dumps({'mode':'dry-run','storage':args.storage,'cloud_changes':0,'required_fields':required_fields(args.storage)}));return
        if args.config.stat().st_size>16_384:raise ValueError('CLOUD_INPUT_INVALID')
        values=json.loads(args.config.read_text());files,plan=render(values,args.storage)
        if args.output:
            target=args.output.resolve();runtime=(ROOT/'.runtime').resolve()
            if runtime not in target.parents or target.exists():raise ValueError('FRESH_RUNTIME_OUTPUT_REQUIRED')
            target.mkdir(parents=True)
            for name,source in files.items():(target/name).write_text(source,encoding='utf-8',newline='\n')
            (target/'plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8',newline='\n')
            plan['rendered_files']={name:hashlib.sha256(source.encode()).hexdigest() for name,source in files.items()}
        if args.execute_preflight:print(json.dumps(preflight(values,storage=args.storage)))
        else:print(json.dumps(plan))
    except Exception:  # noqa: BLE001 - no raw gcloud/configuration errors or environment payloads.
        print('{"mode":"cloud-plan","code":"CLOUD_PLAN_FAILED","cloud_changes":0}')
        raise SystemExit(1) from None


if __name__=='__main__':main()
