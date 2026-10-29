"""Publish supplied-example measurements separately from the earlier baseline."""
import csv,json,pathlib,re,statistics,sys,tempfile
from mjx_profiles import selected
MJX=selected()
B=pathlib.Path(__file__).resolve().parents[1];O=B/'report'
sys.path.insert(0,str(pathlib.Path(tempfile.gettempdir())/'robotics-study-plot-deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
rows=[]
for f in (O/'evidence/results').glob('*.json'):
 try:r=json.loads(f.read_text(encoding='utf-8'))
 except Exception:continue
 if not isinstance(r,dict)or not(r.get('case','').startswith('provided-')or r.get('case','').startswith('humanoid-envs-'))or 'run_id'not in r or r.get('engine')in('gazebo','pybullet','drake','sofa','urlab'):continue
 if r.get('case','').startswith('provided-mjx')and not r['case'].startswith(MJX['case_prefix']):continue
 if r.get('case','').startswith(MJX['case_prefix'])and any(x.get('jax')!=MJX['version']or x.get('compiler_profile')!=MJX['compiler_profile']or x.get('xla_flags','')!=MJX['xla_flags']for x in r.get('results',[])):continue
 if r.get('status')!='PASS'or not r.get('gpu_requested'):continue
 for x in r.get('results',[]):
  ts=x.get('synchronized_rollout_s',[])
  if x.get('repeats')!=5 or len(ts)!=5 or not x.get('physics_valid')or x.get('backend_observed')not in('hip','rocm','amdgpu'):continue
  if r['engine']in('chrono','incflo')and not x.get('validation_barrier'):continue # Provisional native timings were superseded by globally isolated validation.
  meta=x.get('scene_metadata',{});model=meta.get('model',x.get('scene',x.get('implementation','')))
  if r['engine']=='mujoco'and x.get('jax'):model+=' · JAX '+x['jax']
  if r['engine']=='chrono'and 'DEM repose'in x.get('implementation',''):
   x['env_advance_calls_per_s']=x['env_step_per_s'];x['native_fixed_dt']=2.5e-6;x['nominal_native_substeps_per_advance']=400
   x['derived_metric_note']='AdvanceSimulation(0.001s) calls, not single fixed physics substeps; fixed dt from pinned repose.json'
  if r['engine']=='instinct'and x.get('scene','').startswith('LIBERO spatial'):
   x['control_frequency_hz']=20;x['physics_substeps_per_control_step']=round(1/(20*x['physics_dt']));x['rtf_per_env']=x['steps']/(20*x['median_s'])
   x['derived_metric_note']='control frequency from pinned LIBERO default (no override); physics substep count from provided backend round(1/(control_freq*physics_dt))'
  if r['engine']=='incflo':
   x['simulation_time_per_rollout']=x['checks'][-1][0]['simulation_time'];x['rtf_per_env']=x['simulation_time_per_rollout']/x['median_s']
  metric=next((k for k in ('env_advance_calls_per_s','env_step_per_s','frames_per_s','env_rollouts_per_s')if k in x),None)
  if not metric:continue
  rows.append(dict(engine=r['engine'],case=r['case'],run_id=r['run_id'],utc=r['utc'],model=model,envs=x['envs'],metric=metric,throughput=x[metric],rtf_per_env=x.get('rtf_per_env'),median_s=statistics.median(ts),min_s=min(ts),max_s=max(ts),repeats=5,status=r['status'],measurement=x))
latest={}
for row in sorted(rows,key=lambda a:a['utc']):latest[(row['engine'],row['model'],row['envs'])]=row
rows=sorted(latest.values(),key=lambda a:(a['engine'],a['model'],a['envs']))
data=dict(status='IN_PROGRESS',constraint='Provided upstream examples/models only. Preserve physics; execution and measurement adapters documented per record.',measurements=rows,publication_scope='Latest accepted GPU configurations only. Campaign status separately tracks unfinished or unsuccessful requested points; diagnostic history remains private.')
(O/'env-scaling-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
keys=['engine','model','envs','metric','throughput','rtf_per_env','median_s','min_s','max_s','repeats','status','run_id']
with (O/'env-scaling-data.csv').open('w',encoding='utf-8-sig',newline='')as f:
 w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(rows)
groups={}
for row in rows:groups.setdefault((row['engine'],row['model']),[]).append(row)
summaries=[]
for i,((engine,model),items)in enumerate(groups.items()):
 image=f'provided-scaling-{engine}-{i}.png';fig,ax=plt.subplots(figsize=(7.5,4.1));ax.errorbar([a['envs']for a in items],[a['throughput']for a in items],yerr=[[max(0,a['throughput']-a['throughput']*a['median_s']/a['max_s'])for a in items],[max(0,a['throughput']*a['median_s']/a['min_s']-a['throughput'])for a in items]],marker='o',capsize=3,label='Median; range of 5 measured samples');ax.set_xscale('log',base=2);ax.set_xlabel('Independent environments / cameras');ax.set_ylabel(items[0]['metric']);ax.set_title(engine+' — supplied example');ax.grid(True,alpha=.25);ax.set_title(engine+' | '+model,fontsize=10);ax.legend(fontsize=8);fig.tight_layout();fig.savefig(O/'images'/image,dpi=160);plt.close(fig)
 summaries.append((engine,model,items,image))
title='## 제공 예제 envs scaling 추가 시험'
body=[title,'','추가 시험 진행 중이다. MI355X GPU에서 계산하는 제공 예제와 모델만 성능 평가에 포함한다. 모델·재료·해상도·중력·solver 등 물리 설정을 유지하며 headless 처리, backend 선택, env 복제, reset, 동기화와 계측을 추가한다. 호환성 수정과 측정 구간 변경은 원자료에 기록한다.','','아래 결과는 기존 GPU 기초 측정과 분리한 추가 시험이다. 각 행은 같은 모델·같은 env 수에서 5회 측정한 중앙값이다. GPU native batch와 독립 GPU 프로세스 복제를 구분한다. GSplat은 보조 GPU 렌더링 항목이며 env는 카메라 수다. CPU-only 성능은 포함하지 않으며, CPU는 GPU 결과의 sanity check에만 사용한다.','']
details={};software={};plots={}
body+=['| 엔진 | 제공 모델 / 작업 | 통과한 envs | PASS / 계획 |','|---|---|---|---:|']
for engine,model,items,image in summaries:
 expected={'mujoco':6,'instinct':6,'genesis':4 if'SPH'in model else 11,'chrono':4,'incflo':4,'nekrs':4,'fluidlab':4,'taichi':5,'gsplat':6}[engine]
 body.append('| ['+engine+'](#'+engine+') | '+model+' | '+', '.join(str(a['envs'])for a in items)+' | '+str(len(items))+' / '+str(expected)+' |')
 block=['#### 제공 예제 · '+model,'','| envs | 처리량 | 단위 | RTF/env | 중앙값 (s) | 최소–최대 (s) | 실행 | 근거 |','|---:|---:|---|---:|---:|---:|---|---|']
 for a in items:
  unit={'env_step_per_s':'env-steps/s','frames_per_s':'camera-frames/s','env_advance_calls_per_s':'env-advance-calls/s (1 ms)'}[a['metric']];rtf='—'if a['rtf_per_env']is None else f"{a['rtf_per_env']:.4g}"
  block.append(f"| {a['envs']} | {a['throughput']:,.3f} | {unit} | {rtf} | {a['median_s']:.6f} | {a['min_s']:.6f}–{a['max_s']:.6f} | {a['status']} | [JSON](evidence/results/{a['run_id']}.json) |")
 peak=max(items,key=lambda a:a['throughput']);first=items[0]
 if len(items)>1:
  unit={'env_step_per_s':'env-steps/s','frames_per_s':'camera-frames/s','env_advance_calls_per_s':'env-advance-calls/s (1 ms)'}[peak['metric']]
  block+=['',f"측정한 규모 중 aggregate 처리량의 최댓값은 {peak['envs']:,} envs에서 {peak['throughput']:,.3f} {unit}다. {first['envs']:,} envs 대비 처리량은 {peak['throughput']/first['throughput']:.2f}배이며, 환경 수는 {peak['envs']/first['envs']:.2f}배다. 같은 모델·실행 방식의 측정 구간 안에서 해석한다.",'']
 else:block+=['','이 버전은 한 규모의 통과 결과만 있으므로 scaling 추세를 판단하지 않는다.','']
 x=items[-1]['measurement'];meta=x.get('scene_metadata',{});scope=x.get('scope',x.get('execution',''))
 if not scope:scope='; '.join(f'{key}={x[key]}'for key in('graph_mode','steps','repeats','readback_in_timing')if key in x)
 block+=['','측정 범위: '+scope,'']
 fields={k:v for k,v in {**x,**meta}.items()if k in('source','source_commit','source_sha256','model_source','model_sha256','libero_commit','backend_commit','bddl_file','bddl_sha256','asset_sha256','steps','dt','physics_dt','native_fixed_dt','nominal_native_substeps_per_advance','control_frequency_hz','physics_substeps_per_control_step','derived_metric_note','repeat_mode','warmup_steps','substeps','particles','particles_per_env','nodes','grid','gaussians','camera','width','height','mujoco','jax','warp','genesis_version','version','solver_iterations','line_search_iterations','solver_tolerance','controls','changes')}
 fields.update({key:x[key]for key in('compiler_profile','xla_flags')if key in x})
 soft=['<details markdown="1"><summary>제공 예제 재현 정보 · '+model+'</summary>','','```json',json.dumps(fields,ensure_ascii=False,indent=2),'```','','</details>','']
 details.setdefault(engine,[]).extend(block);software.setdefault(engine,[]).extend(soft);plots.setdefault(engine,[]).extend([f'![{engine} supplied-example env scaling](images/{image})',''])
body+=['','실패·시간 초과는 통과 수치로 대체하지 않는다. 전체 실행 이력과 추가 시험 수치는 [env-scaling-data.json](env-scaling-data.json), [CSV](env-scaling-data.csv)에 기록한다.','']
f=O/'confluence-report.md';s=f.read_text(encoding='utf-8');start=s.find(title)
if start>=0:
 end=s.find('\n## ',start+len(title));s=s[:start]+'\n'.join(body)+s[end if end>=0 else len(s):]
else:s+='\n'+'\n'.join(body)
active=json.loads((B/'study/plan.json').read_text(encoding='utf-8'));parts=re.split(r'^## (.+)\s*$',s,flags=re.M);out=[parts[0]]
for section,content in zip(parts[1::2],parts[2::2]):
 engine=next((e['id']for e in active['engines']if e['title']==section),None)
 if engine:
  content=content.replace('#### 기존 GPU 기초 측정\n','').replace('#### 기존 GPU 기초 측정 그래프\n','')
  for tag in('THROUGHPUT','PLOTS'):
   content=re.sub(r'<!-- BASELINE-'+tag+r' -->\s*<details(?: markdown="1")?><summary>[^<]*</summary>\s*(.*?)\s*</details>\s*<!-- /BASELINE-'+tag+r' -->',lambda m:m[1],content,flags=re.S)
  for tag in('SOFTWARE','THROUGHPUT','PLOTS'):content=re.sub(r'<!-- PROVIDED-'+tag+r' -->.*?<!-- /PROVIDED-'+tag+r' -->\s*','',content,flags=re.S)
  if engine:
   soft='<!-- PROVIDED-SOFTWARE -->\n'+'\n'.join(software.get(engine,[]))+'\n<!-- /PROVIDED-SOFTWARE -->\n\n';through='<!-- PROVIDED-THROUGHPUT -->\n'+'\n'.join(details.get(engine,['제공 예제의 GPU 측정 결과를 확인 중이다. 완료 전에는 처리량을 제시하지 않는다.']))+'\n<!-- /PROVIDED-THROUGHPUT -->\n\n';figs='<!-- PROVIDED-PLOTS -->\n'+'\n'.join(plots.get(engine,[]))+'\n<!-- /PROVIDED-PLOTS -->\n\n'
   before,rest=content.split('### 3. Throughput',1);baseline,plotbody=rest.split('### 4. Throughput plot',1);captures=''
   match=re.search(r'<!-- PROVIDED-CAPTURES -->.*?<!-- /PROVIDED-CAPTURES -->',plotbody,flags=re.S)
   if match:captures=match[0];plotbody=plotbody.replace(captures,'')
   if engine=='mujoco':
    match=re.search(r'#### 실제 실행 화면.*?(?=\n!\[[^\n]*throughput\]\(images/mujoco-|\Z)',plotbody,flags=re.S)
    if match:captures+='\n'+match[0];plotbody=plotbody[:match.start()]+plotbody[match.end():]
   wrap=lambda tag,text:'<!-- BASELINE-'+tag+' -->\n<details markdown="1"><summary>기존 GPU 기초 측정 · 참고</summary>\n\n'+text.strip()+'\n\n</details>\n<!-- /BASELINE-'+tag+' -->\n'
   content=before+soft+'### 3. Throughput\n\n'+through+wrap('THROUGHPUT',baseline)+'\n### 4. Throughput plot\n\n'+figs+captures+'\n'+wrap('PLOTS',plotbody)
 out+=['## '+section,content]
s='\n'.join(out);f.write_text(s,encoding='utf-8')
planfile=B/'study/env-scaling-plan.json';plan=json.loads(planfile.read_text(encoding='utf-8'))
for case in plan['cases']:
 matches=[v for (engine,model),v in groups.items() if engine==case['engine'] and (case['engine']!='genesis' or ('SPH' in model)==('sph_rigid' in case['example']))]
 if matches:case['status']='Measured: '+ '; '.join('envs '+','.join(str(a['envs'])for a in v) for v in matches)+'; provided-example measurements in env-scaling-data.json'
 else:case['status']='PENDING: no accepted provided-example measurement under current validation requirements'
planfile.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8');(O/'env-scaling-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
print('Provided example configurations:',len(rows),'models:',len(groups))
