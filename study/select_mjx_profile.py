"""Select a final profile only after all requested GPU measurements qualify."""
import argparse,json,pathlib
from mjx_profiles import PROFILES
B=pathlib.Path(__file__).resolve().parents[1];E=B/'report/evidence/results'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('profile',choices=PROFILES);a=p.parse_args();profile=PROFILES[a.profile];records=[]
for path in E.glob('*.json'):
 try:record=json.loads(path.read_text(encoding='utf-8'))
 except Exception:continue
 if isinstance(record,dict)and'run_id'in record:records.append((path.stat().st_mtime_ns,record))
latest={r['case']:r for _,r in sorted(records,key=lambda x:x[0])}
for n in(None,2048,4096,8192,16384,32768,65536):
 case=profile['case_prefix']+('-smoke'if n is None else'-envs-'+str(n));r=latest.get(case)
 assert r and r['status']=='PASS'and r['rc']==0 and r['gpu_requested'],case
 assert r['results'],case
 for x in r['results']:
  assert x['physics_valid']and x['backend_observed']=='rocm'
  assert x['jax']==profile['version']and x['compiler_profile']==profile['compiler_profile']and x.get('xla_flags','')==profile['xla_flags']
  assert x['model_sha256']=='9b29ea10152748e66a0a77f7651efbbb8282fef9621e7cb8d220ca157c41e61a'
  if n is not None:assert x['envs']==n and x['steps']==1000 and x['repeats']==5 and len(x['synchronized_rollout_s'])==5
if a.profile=='jax0120-default':
 r=latest.get('mjx0120-batch-parity');assert r and r['status']=='PASS'and r['gpu_requested']and r['rc']==0,'Batched numerical parity must pass'
 x=r['results'][0];assert x['physics_valid']and x['jax']=='0.12.0'and x['env_counts_tested']==[2048,4096,8192,16384,32768,65536]
 assert all(c['valid']for c in x['checks'])and x['steps']==20
(B/'study/mjx-profile.json').write_text(json.dumps(dict(profile=a.profile),indent=2)+'\n',encoding='utf-8')
print('Selected fully qualified MJX profile:',a.profile)
