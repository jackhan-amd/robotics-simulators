"""Create standalone plots and Confluence-ready Markdown from measured results."""
import csv,json,pathlib,statistics,sys,tempfile
sys.path.insert(0,str(pathlib.Path(tempfile.gettempdir())/'robotics-study-plot-deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=pathlib.Path(__file__).resolve().parents[1];O=B/'report';I=O/'images';I.mkdir(exist_ok=True)
rows=[];records=[]
for f in sorted((O/'evidence/results').glob('*.json')):
 try:r=json.loads(f.read_text(encoding='utf-8'))
 except Exception:continue
 if 'engine'not in r:continue
 records.append(r)
 for x in r.get('results',[]):
  if r['engine']=='mujoco' and 'env_step_per_s'in x:
   rows.append(dict(backend=x.get('implementation'),scene=x.get('scene',''),dt=x['dt'],steps=x['steps'],envs=x['envs'],env_steps_per_s=x['env_step_per_s'],step_per_s=x['step_per_s'],rtf_per_env=x['rtf_per_env'],median_s=x['median_s'],compile_s=x['compile_s'],min_s=min(x['synchronized_rollout_s']),max_s=max(x['synchronized_rollout_s']),physics_valid=x['physics_valid'],run_id=r['run_id']))
if rows:
 with (O/'mujoco-throughput.csv').open('w',newline='',encoding='utf-8-sig')as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 for humanoid in [False,True]:
  selected=[x for x in rows if ('Humanoid'in x['backend'])==humanoid]
  if not selected:continue
  fig,ax=plt.subplots(figsize=(10,5),layout='constrained')
  for backend in sorted(set(x['backend']for x in selected)):
   d=sorted([x for x in selected if x['backend']==backend and x['physics_valid']],key=lambda x:x['envs'])
   ax.plot([x['envs']for x in d],[x['env_steps_per_s']/1e6 for x in d],marker='o',label=backend)
  scene='Humanoid (27 DoF, zero control), dt=0.005 s'if humanoid else'Sphere/plane (6 DoF), dt=0.001 s'
  ax.set_xscale('log',base=2);ax.set_xticks([2048,4096,8192,16384,32768,65536],labels=['2048','4096','8192','16384','32768','65536']);ax.set_xlabel('Parallel environments');ax.set_ylabel('Throughput (million env-steps/s)');ax.set_title('MI355X x1 | '+scene+' | FP32');ax.grid(alpha=.25);ax.legend();name='mujoco-humanoid-throughput'if humanoid else'mujoco-throughput';fig.savefig(I/(name+'.png'),dpi=180);fig.savefig(I/(name+'.svg'));plt.close(fig)
plan=json.loads((B/'study/plan.json').read_text(encoding='utf-8'))
md=['# Robotics simulators on MI355X','', '시험 진행 중. 수치가 없는 항목은 측정 대기다. GPU 1개, headless physics를 기준으로 측정한다.','', '## 시험 환경','', '- AMD Instinct MI355X × 1, gfx950, Ubuntu 24.04.5, Python 3.12.3.','- 기본 PyTorch 2.14.0+rocm10.1.0. MJX는 별도 ROCm 7.14.1 환경에서 실행.','- 저장소 커밋: `'+plan['repository_commit']+'`.','- env-step/s = envs × measured steps / synchronized wall time. 5회 중앙값. JIT·warm-up·readback 제외.','']
for e in plan['engines']:
 md+=['## '+e['title'],'','### 1. Simulator 설명','',e['use'],'','### 2. Software','','- Repository: '+e['source'],'- Local integration: `robotics-sim-lab@'+plan['repository_commit']+'`','']
 versions=[]
 for r in records:
  if r['engine']==e['id']:
   for x in r.get('results',[]):
    versions.extend(f'{k}: {x[k]}'for k in ('version','mujoco','jax','warp','genesis_version','quadrants_version','torch','torch_hip')if k in x)
 md+=['- Versions: '+('; '.join(dict.fromkeys(versions))or '설치/실행 후 기록 예정'),'','### 3. Throughput','']
 relevant=[r for r in records if r['engine']==e['id']]
 if e['id']=='mujoco'and rows:
  md+=['장면: 저장소의 단일 sphere–plane 낙하·접촉, dt=0.001 s, FP32. 실제 로봇 전체의 처리량과 구분한다.','','| Backend | envs | env-step/s | time/1000 steps (s) | Physics |','|---|---:|---:|---:|---|']
  md += [f'| {x["backend"]} | {x["envs"]} | {x["env_steps_per_s"]:,.0f} | {x["median_s"]:.4f} | {x["physics_valid"]} |' for x in rows]
 else:
  benchmarks=[x for r in relevant for x in r.get('results',[]) if 'step_per_s'in x]
  md += [f'- {x.get("case", "benchmark")}: {x["step_per_s"]:,.0f} step/s, CPU.'for x in benchmarks]or ['성능 측정 대기.']
 md+=['','Smoke: '+(', '.join(r['case']+'='+r['status']for r in relevant)or '대기'),'','### 4. Throughput plot','']
 if e['id']=='mujoco'and rows:md+=['![MI355X MuJoCo throughput](images/mujoco-throughput.png)','']
 else:md+=['측정 완료 후 그래프 추가.','']
(O/'confluence-report.md').write_text('\n'.join(md),encoding='utf-8')
print('PLOTS',len(rows),'measured sweep points; Markdown ready')
