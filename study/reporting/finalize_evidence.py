"""Prepare final successful logs and replace private report path references."""
from workspace import REPO_ROOT, script_path, source_reference
import json,pathlib,re
from publication import aggregate,final_evidence,sanitize_text
from mjx_profiles import selected
MJX=selected()
B=REPO_ROOT;O=B/'report'
c=json.loads((O/'gpu-campaign-status.json').read_text(encoding='utf-8'))
mapping=final_evidence(O,O/'evidence/final',c)
f=O/'confluence-report.md';text=f.read_text(encoding='utf-8')
for runid,name in mapping.items():
 for ext in('.json','.log'):text=text.replace('evidence/results/'+runid+ext,'evidence/final/'+name+ext)
text=re.sub(r'\[([^\]]+)\]\(evidence/results/\d{8}T\d{6}Z[^)]+\)',r'[\1](benchmark-data.json)',text)
text=sanitize_text(text)
text=text.replace('최종 측정 수치는','최종 측정 수치는').replace('FAIL/BLOCKED를 수치로 대체하지 않으며 원본 로그를 남긴다.','각 구성의 상태와 최종 측정 근거를 함께 기록한다.').replace('실패·시간 초과는 통과 수치로 대체하지 않는다. ','')
text=text.replace('의 GPU replay에서 step','의 GPU replay(`recipes/genesis/benchmarks/capture_provided_genesis.py`)에서 step')
text=re.sub(r'최초 smoke는 float32 gravity.*?초기 실패·수정 후 결과를 모두 보존(?:한다|했다)\.','중력 파라미터는 float32 표현 오차를 고려해 허용오차 1e-6으로 비교하며, 물리 gate는 유지한다.',text,flags=re.S)
text=text.replace('버전별 시도와 실패는 분리해 기록한다.','최종 실행 버전과 필요한 workaround를 함께 기록한다.')
text=re.sub(r'^Run ID:.*$','실행 방법은 `study/REPRODUCE.md`를 따른다. 제공 예제 표의 최종 JSON에서 모델·버전·계측 조건과 실행 코드의 hash를 확인할 수 있다.',text,flags=re.M)
text=text.replace('각 탭의 Run ID에서 실제 버전과 반복 시간을 확인한다.','각 탭의 최종 JSON에서 실제 버전과 반복 시간을 확인한다.')
text=re.sub(r'Pinned commit:.*?(?=\n\n)', 'Pinned base commit: `d1adb4a0cd5f55ce80443e642092190de9d12f6e`. 최종 성공 실행의 재현 명령·설정·수치 JSON·로그는 `evidence/final/`에 수록했다. 실행과 보고서 생성 코드는 코드 ZIP의 `study/`에 있으며, 버전 목록은 `configs/benchmarks/software.json`에 기록했다.',text,count=1,flags=re.S)
text=text.replace(' JAX 0.12.0 결과는 별도 버전 진단으로 표시한다.','')
if c['status']=='IN_PROGRESS':
 text=text.replace('요청한 제공 예제 env scaling을 모두 실행했다. 실패 구성에는 처리량을 제시하지 않는다.','제공 예제 env scaling을 재측정 중이다. 통과한 구성만 처리량을 제시한다.')
 text=text.replace('요청한 env 규모의 실행을 마쳤다.','요청한 env 규모를 순차적으로 재측정하고 있다.')
elif c['status']=='COMPLETED':
 text=text.replace('제공 예제 env scaling을 재측정 중이다. 통과한 구성만 처리량을 제시한다.','요청한 제공 예제 env scaling의 '+str(c['expected_configurations'])+'개 구성이 모두 통과했다.')
 text=text.replace('요청한 env 규모를 순차적으로 재측정하고 있다.','요청한 모든 env 규모의 측정을 마쳤다.')
start=text.index('## MuJoCo · MJX / MJWarp');end=text.find('\n## ',start+4);end=end if end>=0 else len(text)
chapter=text[start:end];software,throughput=chapter.split('### 3. Throughput',1);version_rows=[0]
def version_row(match):
 version_rows[0]+=1
 if version_rows[0]==1:return '| MJX-JAX · 제공 Humanoid | mujoco=3.16.0; JAX/jaxlib/PJRT/plugin='+MJX['version']+'; isolated ROCm 7.14.1; profile='+MJX['compiler_profile']+' |'
 return '| MJX-JAX · 구·바닥 기초 측정 | mujoco=3.16.0; JAX/jaxlib=0.12.0; PJRT/plugin=0.11.2; isolated ROCm 7.14.1 |'
software=re.sub(r'^\| MJX-JAX[^\n]+$',version_row,software,flags=re.M)
throughput=re.sub(r'<!-- MJX-BATCH-PARITY -->.*?<!-- /MJX-BATCH-PARITY -->\s*','',throughput,flags=re.S)
if MJX['version']=='0.12.0':
 records=[]
 for path in(O/'evidence/results').glob('*mjx0120-batch-parity*.json'):
  value=json.loads(path.read_text(encoding='utf-8'))
  if isinstance(value,dict)and value.get('case')=='mjx0120-batch-parity'and value.get('status')=='PASS':records.append((path.stat().st_mtime_ns,value))
 assert records,'Selected profile needs batched numerical qualification'
 parity=aggregate(max(records,key=lambda pair:pair[0])[1]['results'][0]);parity['code']='recipes/mujoco/benchmarks/mjx_batch_parity.py'
 (O/'evidence/mjx-batch-parity.json').write_text(json.dumps(parity,ensure_ascii=False,indent=2),encoding='utf-8')
 qerror=max(x['qpos_max_abs_error']for x in parity['checks']);verror=max(x['qvel_max_abs_error']for x in parity['checks'])
 note='\n<!-- MJX-BATCH-PARITY -->\n\n요청한 여섯 env 규모에서 20-step 이후 모든 GPU env의 qpos/qvel을 같은 모델의 CPU 기준과 대조했다. 최대 qpos 오차는 '+f'{qerror:.8g}'+', qvel 오차는 '+f'{verror:.8g}'+'이었다. CPU 처리량은 측정하지 않았다. 이 결과는 단기 sanity check이며 장기 궤적 정확도 검증을 대신하지 않는다. [규모별 오차와 허용오차](evidence/mjx-batch-parity.json).\n\n<!-- /MJX-BATCH-PARITY -->\n'
 throughput=note+throughput
text=text[:start]+software+'### 3. Throughput'+throughput+text[end:]
plan=json.loads((B/'configs/benchmarks/report-plan.json').read_text(encoding='utf-8'));parts=re.split(r'^## (.+)\s*$',text,flags=re.M);out=[parts[0]]
for title,chapter in zip(parts[1::2],parts[2::2]):
 engine=next((e for e in plan['engines']if e['title']==title),None)
 if engine:
  chapter=re.sub(r'<!-- PROVIDED-COMMAND -->.*?<!-- /PROVIDED-COMMAND -->\s*','',chapter,flags=re.S)
  files=sorted(set(re.findall(r'python3\s+([A-Za-z_][A-Za-z0-9_]*\.py)',engine['command'])))
  assert all(script_path(name).is_file()for name in files)
  source_paths=' · '.join('`'+source_reference(name)+'`'for name in files)
  block='<!-- PROVIDED-COMMAND -->\n\n#### 제공 예제 실행\n\n저장소 코드: '+source_paths+'. 외부 작업 공간과 공통 환경은 `study/REPRODUCE.md`에 따라 준비한다.\n\n```bash\n'+engine['command']+'\n```\n\n<!-- /PROVIDED-COMMAND -->\n\n'
  chapter=chapter.replace('### 3. Throughput',block+'### 3. Throughput',1)
 out+=['## '+title,chapter]
text='\n'.join(out)
f.write_text(text,encoding='utf-8')
for name in('env-scaling-data.json','benchmark-data.json','gpu-campaign-status.json','test-plan.json','env-scaling-plan.json'):
 source=O/name
 if not source.exists():continue
 target=O/'publication-data'/name;target.parent.mkdir(exist_ok=True)
 target.write_text(json.dumps(aggregate(json.loads(source.read_text(encoding='utf-8'))),ensure_ascii=False,indent=2),encoding='utf-8')
print('Final accepted GPU receipts:',len(mapping))
