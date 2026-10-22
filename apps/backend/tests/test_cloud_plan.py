import json
import re
from types import SimpleNamespace

import pytest
import yaml

from choreograph import cloud_plan


def values():
    result={key:'fixture-'+key.removeprefix('REPLACE_').lower().replace('_','-') for key in cloud_plan.required_fields()}
    result.update(REPLACE_PROJECT_ID='fixture-project',REPLACE_PROJECT_NUMBER='123456789012',
        REPLACE_REGION='us-central1',REPLACE_QA_TESTERS_GROUP='qa@example.invalid',
        REPLACE_FRONTEND_IMAGE_DIGEST='a'*64,REPLACE_BACKEND_IMAGE_DIGEST='b'*64)
    for key in result:
        if 'PINNED_' in key:result[key]='7'
    return result


def test_render_is_offline_and_has_private_bootstrap_and_separate_roles():
    files,plan=cloud_plan.render(values())
    assert plan['cloud_changes']==0
    assert not any(re.search(r'REPLACE_[A-Z0-9_]+',source) for source in files.values())
    assert len(plan['commands'])==14
    api=yaml.safe_load(files['fixture-api-service-name.yaml'])
    assert api['metadata']['annotations']['run.googleapis.com/invoker-iam-disabled']=='false'
    initial=yaml.safe_load(files['bootstrap-fixture-api-service-name.yaml'])
    assert initial['spec']['template']['spec']['containers'][0]['args']==['bootstrap']
    assert initial['spec']['template']['spec']['containers'][0]['env']==[]
    worker=json.loads(files['worker-pool.json'])
    assert worker['scaling']['manualInstanceCount']==1
    assert plan['rest_requests'][1]['url'].startswith('https://run.googleapis.com/v2/')
    assert all('allUsers' not in binding['members'] for item in json.loads(files['iam.json'])['resourcePolicyAdditions'] for binding in item['bindings'])


@pytest.mark.parametrize(('key','bad'),[('REPLACE_PROJECT_ID','project; inject'),
    ('REPLACE_PINNED_TOKEN_KEY_SECRET_VERSION','latest'),('REPLACE_BACKEND_IMAGE_DIGEST','mutable:tag'),
    ('REPLACE_WORKER_SERVICE_ORIGIN','host/path'),('REPLACE_REGION','us-central1\ninject')])
def test_unreviewable_substitutions_rejected(key,bad):
    with pytest.raises(ValueError):cloud_plan.render({**values(),key:bad})


def test_preflight_is_finite_read_only_and_does_not_echo_descriptions():
    calls=[]
    def runner(argv,**kwargs):
        calls.append(argv);assert kwargs['timeout']==15
        return SimpleNamespace(returncode=0,stdout='private env contents',stderr='sensitive')
    result=cloud_plan.preflight(values(),runner=runner)
    assert result['reads']==7 and result['writes']==0
    assert all('describe' in argv and '--quiet' in argv for argv in calls)
    assert 'private' not in json.dumps(result) and 'sensitive' not in json.dumps(result)


def test_no_config_cli_is_a_no_network_plan(monkeypatch,capsys):
    monkeypatch.setattr('sys.argv',['cloud_plan'])
    monkeypatch.setattr('subprocess.run',lambda *_args,**_kwargs:pytest.fail('unexpected gcloud'))
    cloud_plan.main()
    assert json.loads(capsys.readouterr().out)['cloud_changes']==0
