"""Current GPU-only campaign matrix; never infer completion from an old baseline."""
import datetime,json,pathlib,re,shutil
from mjx_profiles import selected
MJX=selected()
B=pathlib.Path(__file__).resolve().parents[1];O=B/'report';E=O/'evidence/results';records=[]
for f in E.glob('*.json'):
 try:r=json.loads(f.read_text(encoding='utf-8'))
 except Exception:continue
 if isinstance(r,dict)and r.get('gpu_requested')and 'run_id'in r:records.append((f.stat().st_mtime_ns,r))
records.sort(key=lambda p:p[0]);latest={r['case']:r for _,r in records}
specs=[
 ('mujoco','MJWarp supplied Humanoid','humanoid',[2048,4096,8192,16384,32768,65536],False),
 ('mujoco','MJX-JAX '+MJX['version']+' supplied Humanoid',MJX['case_prefix'],[2048,4096,8192,16384,32768,65536],False),
 ('genesis','supplied Franka','provided-franka',[1,16,64,256,1024,2048,4096,8192,16384,32768,65536],False),
 ('genesis','supplied SPH + rigid coupling','provided-genesis-sph',[1,2,4,8],False),
 ('chrono','supplied SPH DamBreak','provided-chrono-fsi',[1,2,4,8],True),
 ('chrono','supplied DEM repose initial transient','provided-chrono-dem',[1,2,4,8],True),
 ('incflo','supplied cavity','provided-incflo',[1,2,4,8],True),
 ('nekrs','supplied TGV, consecutive windows','provided-nekrs-windows',[1,2,4,8],False),
 ('fluidlab','supplied MixingEnv','provided-fluidlab',[1,2,4,8],False),
 ('instinct','supplied LIBERO spatial task 0','provided-instinct-libero',[1,2,4,8,16,32],False),
 ('taichi','supplied MPM88','provided-taichi',[1,2,4,8,16],False),
 ('gsplat','supplied garden camera batch (renderer)','provided-garden',[1,2,4,8,16,32],False)]
def qualification(r,gated=False,timed=True):
 if not r or r.get('status')!='PASS':return False
 xs=r.get('results',[])
 if r.get('case','').startswith(MJX['case_prefix'])and any(x.get('jax')!=MJX['version']or x.get('compiler_profile')!=MJX['compiler_profile']or x.get('xla_flags','')!=MJX['xla_flags']for x in xs):return False
 return bool(xs)and all(x.get('physics_valid')and x.get('backend_observed')in('hip','rocm','amdgpu')and(not gated or x.get('validation_barrier'))and(not timed or(x.get('repeats')==5 and len(x.get('synchronized_rollout_s',[]))==5))for x in xs)
campaigns=[];counts=dict(PASS=0,FAIL=0,BLOCKED=0,PENDING=0,REMEASUREMENT_PENDING=0)
for engine,model,prefix,envs,gated in specs:
 points=[]
 for n in envs:
  case=f'{prefix}-envs-{n}';r=latest.get(case)
  if qualification(r,gated):state='PASS'
  elif prefix==MJX['case_prefix']and r:state='REMEASUREMENT_PENDING'
  elif r and r['status']in('FAIL','BLOCKED'):state=r['status']
  elif r:state='REMEASUREMENT_PENDING'
  else:state='PENDING'
  counts[state]+=1;points.append(dict(envs=n,status=state,run_id=r['run_id']if r else None,case=case))
 smoke=latest.get(prefix+'-smoke');campaigns.append(dict(engine=engine,model=model,expected_envs=envs,smoke_status='PASS'if qualification(smoke,gated,timed=False)else('PENDING_REMEASUREMENT'if smoke else'PENDING'),smoke_run_id=smoke['run_id']if smoke else None,points=points))
pending=counts['PENDING']+counts['REMEASUREMENT_PENDING'];smoke_pending=any(c['smoke_status']!='PASS'for c in campaigns);status='IN_PROGRESS'if pending or smoke_pending else('COMPLETED_WITH_LIMITATIONS'if counts['FAIL']+counts['BLOCKED']else'COMPLETED')
data=dict(updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status=status,scope='MI355X GPU physics: 8 engines; GSplat separate GPU rendering adjunct; CPU for GPU sanity references only',expected_configurations=sum(counts.values()),counts=counts,campaigns=campaigns,notes=['Five samples per accepted configuration; nekRS samples are consecutive trajectory windows, not independent resets.','Native Chrono/incflo timings require a global validation/finalization release barrier. Prior native timings remain raw provisional evidence.','A FAIL or BLOCKED point is a recorded outcome, never a throughput value.'])
(O/'gpu-campaign-status.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
audit=O/'evidence/measurement-audit.json';archive=B/'_workspace/gpu-scope-revision';archive.mkdir(parents=True,exist_ok=True)
if audit.exists()and not(archive/'prior-measurement-audit.json').exists():shutil.copy2(audit,archive/'prior-measurement-audit.json')
baseline=json.loads((O/'benchmark-data.json').read_text(encoding='utf-8'));assert all(x.get('backend_observed')!='cpu'for x in baseline)
audit.write_text(json.dumps(dict(**data,baseline_gpu_configurations=len(baseline),baseline_samples_each=5,physics_accuracy_scope='Scene-specific finite-state/conservation/contact/parity checks; no blanket G2/application certification'),ensure_ascii=False,indent=2),encoding='utf-8')
(O/'evidence/gpu-smoke-coverage.json').write_text(json.dumps([dict(engine=c['engine'],model=c['model'],status=c['smoke_status'],run_id=c['smoke_run_id'])for c in campaigns],ensure_ascii=False,indent=2),encoding='utf-8')
f=B/'study/plan.json';p=json.loads(f.read_text(encoding='utf-8'));p['state']=data['scope']+'; '+status
p['method']=['CPU는 같은 장면의 초기 GPU 결과를 확인하는 sanity check에만 사용한다. CPU 처리량은 측정 결과와 집계에서 제외한다.'if x.startswith('CPU')else x for x in p['method']]
for e in p['engines']:
 own=[c for c in campaigns if c['engine']==e['id']];passed=sum(point['status']=='PASS'for c in own for point in c['points']);expected=sum(len(c['points'])for c in own);e['baseline_performance_configurations']=e['measured_configurations'];e.pop('primary_performance_configurations',None);e['provided_configurations_passed']=passed;e['provided_configurations_expected']=expected;e['status']=f'GPU · provided {passed}/{expected} PASS'+(' · in progress'if any(point['status']in('PENDING','REMEASUREMENT_PENDING')for c in own for point in c['points'])else'')
 for state in ('FAIL','BLOCKED'):
  n=sum(point['status']==state for c in own for point in c['points'])
  if n:e['status']+=f' · {n} {state}'
p['method']=[('CPU는 같은 GPU 장면의 sanity check에만 사용하며 CPU 처리량은 집계하지 않는다.'if'CPU 기준값'in x else x)for x in p['method']];f.write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
f=O/'confluence-report.md';s=f.read_text(encoding='utf-8');title='## 시험 범위와 완료 상태';start=s.index(title);end=s.find('\n## ',start+len(title));body=[title,'','MI355X GPU에서 물리 계산을 수행하는 8개 엔진을 평가한다. GSplat은 별도 GPU 렌더링 보조 항목이다. CPU는 GPU 결과의 sanity check에만 사용하고 CPU 성능은 포함하지 않는다.','','제공 예제의 현재 진행 상태는 아래와 같다. 기존 기초 측정의 PASS와 추가 scaling 완료 여부를 구분한다.','','| Simulator | 제공 예제 측정 PASS | 현재 상태 |','|---|---:|---|']
for e in p['engines']:body.append(f"| {e['title']} | {e['provided_configurations_passed']}/{e['provided_configurations_expected']} | {e['status']} |")
body+=['','[전체 env별 상태](gpu-campaign-status.json) · [GPU smoke 근거](evidence/gpu-smoke-coverage.json). FAIL/BLOCKED는 수치로 대체하지 않으며 원본 로그를 남긴다.',''];s=s[:start]+'\n'.join(body)+s[end if end>=0 else len(s):];s=s.replace('[측정 자료](benchmark-data.json)','[GPU 기초 측정 자료](benchmark-data.json) · [제공 예제 측정 자료](env-scaling-data.json)');f.write_text(s,encoding='utf-8')
print(json.dumps(dict(status=status,expected=data['expected_configurations'],counts=counts)))

# Show missing/failed requested points next to the successful throughput table.
# Success alone must not suggest that every requested env size has passed.
s=re.sub(r'<!-- GPU-CAMPAIGN-OUTCOMES -->.*?<!-- /GPU-CAMPAIGN-OUTCOMES -->\s*','',s,flags=re.S)
parts=re.split(r'^## (.+)\s*$',s,flags=re.M);out=[parts[0]]
for title,content in zip(parts[1::2],parts[2::2]):
 e=next((e for e in p['engines']if e['title']==title),None)
 own=[c for c in campaigns if e and c['engine']==e['id']]
 if any(point['status']!='PASS'for c in own for point in c['points']):
  block=['<!-- GPU-CAMPAIGN-OUTCOMES -->','#### 요청 규모별 실행 상태','','| 모델 / 경로 | PASS envs | FAIL / BLOCKED envs | 대기·재측정 envs |','|---|---|---|---|']
  for c in own:
   passed=', '.join(str(q['envs'])for q in c['points']if q['status']=='PASS')or'—'
   failed=', '.join(f"{q['envs']} [{q['status']}](evidence/results/{q['run_id']}.log)"for q in c['points']if q['status']in('FAIL','BLOCKED'))or'—'
   waiting=', '.join(str(q['envs'])for q in c['points']if q['status']in('PENDING','REMEASUREMENT_PENDING'))or'—'
   block.append(f"| {c['model']} | {passed} | {failed} | {waiting} |")
  block+=['','FAIL/BLOCKED 구성의 처리량은 제시하지 않는다. 상태 링크에서 원본 오류 로그를 확인할 수 있다.','<!-- /GPU-CAMPAIGN-OUTCOMES -->','']
  content=content.replace('### 3. Throughput\n','### 3. Throughput\n\n'+'\n'.join(block),1)
 out+=['## '+title,content]
f.write_text('\n'.join(out),encoding='utf-8')
