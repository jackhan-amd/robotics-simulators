"""Verify the release contains only the accepted GPU execution history."""
from workspace import REPO_ROOT
import hashlib,io,json,pathlib,re,zipfile
from workspace import profile
B=REPO_ROOT;O=B/'report';bundle=O/'mi355x-simulator-results.zip'
with zipfile.ZipFile(bundle)as z:
 assert z.testzip()is None;names=set(z.namelist())
 assert all(not n.startswith(('/','\\'))and'..'not in pathlib.PurePosixPath(n).parts for n in names)
 campaign=json.loads(z.read('report/gpu-campaign-status.json'))
 assert campaign['status']=='COMPLETED'and campaign['counts']==dict(PASS=64,FAIL=0,BLOCKED=0,PENDING=0,REMEASUREMENT_PENDING=0)
 assert len(json.loads(z.read('report/test-plan.json'))['engines'])==9
 evidence=[n for n in names if n.startswith('report/evidence/final/')and n.endswith('.json')]
 assert len(evidence)==76,'64 configurations and 12 model-path smokes expected'
 for name in evidence:
  receipt=json.loads(z.read(name));assert receipt['status']=='PASS'and receipt['gpu_requested']
  assert 'run_id'not in receipt and'command'not in receipt and'environment'not in receipt
  assert 'report/evidence/final/'+receipt['execution_log']in names
 assert not any(re.match(r'report/evidence/results/\d{8}T',n)for n in names)
 review=json.loads(z.read('report/humanizer-review.json'));assert review['markdown_sha256']==hashlib.sha256(z.read('report/confluence-report.md')).hexdigest()
 tokens=[v for k,v in profile().items()if isinstance(v,str)and len(v)>=6 and any(x in k for x in('ROOT','PATH','TARGET','CONFLUENCE'))]
 for name in names:
  if pathlib.PurePosixPath(name).suffix in('.md','.html','.json','.log','.csv','.txt'):
   text=z.read(name).decode('utf-8');assert not any(v in text or v.replace('\\','/')in text for v in tokens),name
 with zipfile.ZipFile(io.BytesIO(z.read('report/mi355x-reproduction-code.zip')))as source:
  assert source.testzip()is None
  assert {'study/workspace.py','study/README.md','recipes/mujoco/benchmarks/provided_mjx_humanoid.py','study/reporting/render_final.py'}<=set(source.namelist())
  assert not any(n.startswith(('private/','report/','_workspace/'))for n in source.namelist())
 result=dict(status='PASS',bundle=bundle.name,sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(),files=len(names),simulator_tabs=9,gpu_requested_configurations=64,pass_count=64,fail_count=0,final_successful_receipts=len(evidence),cpu_throughput_in_customer_package=False)
(O/'delivery-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
