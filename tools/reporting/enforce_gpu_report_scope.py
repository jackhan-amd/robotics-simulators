"""Check and maintain the customer's GPU-only reporting scope."""
from workspace import REPO_ROOT
from workspace import expand_runtime, run_root, runtime_path
import json,pathlib,re
from mjx_profiles import selected
B=REPO_ROOT;O=B/'report'
excluded={'pybullet','drake','gazebo','sofa','urlab'}
p=json.loads((B/'configs/benchmarks/report-plan.json').read_text(encoding='utf-8'))
assert not excluded.intersection(e['id']for e in p['engines'])
campaign=json.loads((O/'gpu-campaign-status.json').read_text(encoding='utf-8'))
MJX=selected()
amd=json.loads((B/'configs/benchmarks/amd-solutions.json').read_text(encoding='utf-8'))['engines']
commands={
 'mujoco':'python3 representative_suite.py\nPROVIDED_MJX_ALIGNED=1 python3 provided_mjx_suite.py',
 'instinct':'python3 provided_instinct_suite.py',
 'genesis':'python3 provided_scaling_suite.py\nPROVIDED_ENGINE=genesis-sph python3 provided_replicas_suite.py',
 'chrono':'python3 provided_chrono_suite.py',
 'incflo':'PROVIDED_CFD_ENGINE=incflo python3 provided_cfd_suite.py',
 'nekrs':'PROVIDED_CFD_ENGINE=nekrs PROVIDED_CFD_WINDOWS=1 python3 provided_cfd_suite.py',
 'fluidlab':'PROVIDED_ENGINE=fluidlab python3 provided_replicas_suite.py',
 'taichi':'PROVIDED_ENGINE=taichi python3 provided_replicas_suite.py',
 'gsplat':'python3 provided_gsplat_suite.py'}
commands['mujoco']='python3 representative_suite.py\nPROVIDED_MJX_VERSION='+MJX['version']+' PROVIDED_MJX_COMPILER_PROFILE='+MJX['compiler_profile']+' python3 provided_mjx_suite.py'
for e in p['engines']:
 if e['id']in amd:e['amd_solution']=amd[e['id']]
 own=[c for c in campaign['campaigns']if c['engine']==e['id']]
 e.setdefault('baseline_performance_description',e.get('performance',''))
 e.setdefault('baseline_smoke_description',e.get('smoke',''))
 e['performance']='; '.join(c['model']+'; envs='+','.join(map(str,c['expected_envs']))for c in own)+'; 5 synchronized samples per configuration'
 e['scalability']='Native batch or independent GPU process replicas; see per-model measurement scope'
 e['smoke']='Same supplied scene on MI355X GPU; explicit backend and scene-specific numerical/image checks before performance sweep'
 e['command']='cd ${LAB_ROOT}\nsource ./env.sh\n'+commands[e['id']]
(B/'configs/benchmarks/report-plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
f=O/'confluence-report.md';s=f.read_text(encoding='utf-8')
s='\n'.join(line for line in s.splitlines()if not(line.startswith('- ')and('Schola / URLab'in line or'UnrealRoboticsLab'in line)))+'\n'
s=re.sub(r' URLab/Schola 탭에서는[^\n]*','',s)
s=s.replace('evidence/smoke-coverage.json','evidence/gpu-smoke-coverage.json')
if '[처리량·단위 검산](evidence/throughput-audit.json)'not in s:s=s.replace('[측정 검산](evidence/measurement-audit.json)','[측정 검산](evidence/measurement-audit.json) · [처리량·단위 검산](evidence/throughput-audit.json)')
note='기초 측정 목록과 제공 예제 목록은 MJWarp Humanoid의 6개 실행을 공유하므로 구성 수를 합산하지 않는다.'
s=s.replace(note+' JAX 0.12.0 결과는 별도 버전 진단으로 표시한다.','').replace(note,'')
s=s.replace('재현 절차:',note+'\n\n재현 절차:',1)
s=s.replace('LIBERO·RoboCasa 전체 평가, OSC controller와 ray tracer의 정확도·성능은 이번 물리 시험 범위 밖이다.','LIBERO·RoboCasa의 전체 정책 평가는 수행하지 않았다. 제공 LIBERO 시험의 end-to-end 처리량에는 GPU OSC·ray tracer 경로를 포함하지만, 이들의 개별 정확도나 개별 처리량을 검증한 것은 아니다.')
s=s.replace('FSI-SPH와 DEM의 HIP 장치·커널·유한 상태, CPU multibody 기준','FSI-SPH와 DEM의 HIP 장치·커널·유한 상태')
s=s.replace('이번 MI355X smoke 실행에서 저장한 합성 Gaussian 렌더링 화면.','')
s=s.replace('합성 장면의 forward rasterization과 다른 작업이다.','이번 forward rasterization과 다른 작업이다.')
s=s.replace('기초 MPM core 측정과 전체 제공 task 결과를 구분해 제시한다.','기초 MPM core 측정과 제공 MixingEnv의 전방향 물리 결과를 구분해 제시한다.')
s=s.replace('| MJX-JAX | mujoco=3.16.0; jax=0.12.0 |','| MJX-JAX · Humanoid 기본 시험 | mujoco=3.16.0; jax=0.11.2; private ROCm 7.14.1 |\n| MJX-JAX · 별도 버전 진단 | mujoco=3.16.0; jax=0.12.0; private ROCm 7.14.1 |')
s=re.sub(r'#### 정확도 검증용 CPU 기준 \(보조 자료\)\n.*?(?=\n#### |\Z)','#### GPU sanity check\n\nCPU는 같은 GPU 장면의 상태·궤적을 대조하는 기준으로만 사용했다. CPU 처리량은 보고하지 않는다.\n\n',s,flags=re.S)
s=s.replace('upstream의 forward MPM core만 시험한다. 제거된 Taichi struct.fill과 정적 None 검사 API를 별도 사본에서 호환 수정했다. 물리 수식은 바꾸지 않았으며 diff와 해시를 보존했다. gradient, 학습, full task 환경과 renderer는 시험 범위 밖이다. upstream 소스 payload는 보고서에 재배포하지 않는다.','제거된 Taichi struct.fill과 정적 None 검사 API는 별도 사본에서 호환 수정했다. 물리 수식은 바꾸지 않았으며 diff와 해시를 보존했다. upstream 소스 payload는 보고서에 재배포하지 않는다.')
s=re.sub(r'## 고객 설명에 사용할 시연 순서\n.*?(?=\n## |\Z)', '''## 고객 설명에 사용할 시연 순서

MuJoCo 탭에서 제공 Humanoid 모델의 MJWarp와 MJX 결과를 버전별로 보여준다. 요청한 env 규모별 처리량, 환경당 step/s와 RTF, 반복 시간 범위, 실행 명령을 함께 확인한다. 제어 입력은 0이며 학습된 보행 policy의 성능을 뜻하지 않는다. 공–바닥 기초 측정은 접힌 참고 구획에서 확인할 수 있다.

Genesis는 제공 Franka의 native env batch와 SPH–강체 결합 예제의 독립 GPU 프로세스 복제를 구분해 설명한다. Chrono의 DamBreak와 DEM, incflo의 cavity, nekRS의 TGV는 각 모델의 입자·격자 규모와 시간 간격, 측정 구간을 먼저 제시한다. 특히 DEM은 초기 1 ms 구간이며 nekRS는 연속 궤적의 다섯 측정 창이다.

FluidLab은 제공 MixingEnv의 실제 입자 좌표를, Taichi는 제공 MPM88 예제의 GPU 실행 결과를 보여준다. Instinct Sim은 제공 LIBERO 작업의 GPU 물리·제어·카메라를 포함한 env.step 처리량이다. GSplat은 공유 geometry의 카메라 batch를 측정한 GSplat GPU 렌더링 성능 항목으로 설명한다.

각 탭의 Run ID에서 실제 버전과 반복 시간을 확인한다. 화면은 실제 실행이나 별도 캡처 재실행에서 저장한 것만 사용한다. 수치 출력을 그림으로 만든 경우에는 후처리 시각화라고 표시한다. CPU 실행은 GPU 결과와 같은 장면의 sanity check 근거로만 다룬다.

''',s,flags=re.S)
s=re.sub(r'## Confluence 반영 상태\n.*?(?=\n## |\Z)', '''## Confluence 반영 상태

지정한 Confluence 초안에는 반영하지 못했다. 로컬 Atlassian 인증 설정이 없으며, 브라우저 연결 복구 도구 호출도 자동 승인 검토에서 거부됐다. 검토 사유는 호출의 대상과 동작을 확인할 수 없어 기존 문서 변경 위험을 판단할 수 없다는 것이었다. Confluence 본문을 쓰지 않았다.

사용자가 허용한 수작업 반영용 Markdown과 실제 실행 그림을 제공한다. 시뮬레이터별 본문과 images 폴더의 그림을 옮기고 로컬 근거 링크는 Confluence 첨부 파일 링크로 바꿔야 한다. HTML 보고서는 그림을 포함해 오프라인에서 볼 수 있다.

''',s,flags=re.S)
s=re.sub(r'\n{4,}','\n\n\n',s)
s=re.sub(r'<!-- AMD-SOLUTION -->.*?<!-- /AMD-SOLUTION -->\s*','',s,flags=re.S)
s=re.sub(r'<!-- AMD-BADGE-LEGEND -->.*?<!-- /AMD-BADGE-LEGEND -->\s*','',s,flags=re.S)
legend='<!-- AMD-BADGE-LEGEND -->\n검은 바탕의 흰색 AMD 배지는 AMD 블로그에서 소개하고 GPU 실행 코드·배포·설정 절차를 제공한 솔루션을 표시한다. MI355X 공식 지원이나 이번 시험의 성공을 뜻하지 않는다. Genesis 블로그는 Ryzen AI MAX/Vulkan 경로이며, GSplat의 공개 지원 GPU 목록은 MI300X·MI325X다.\n<!-- /AMD-BADGE-LEGEND -->\n\n'
s=s.replace('Integration repository:',legend+'Integration repository:',1)
parts=re.split(r'^## (.+)\s*$',s,flags=re.M);out=[parts[0]]
for title,content in zip(parts[1::2],parts[2::2]):
 e=next((e for e in p['engines']if e['title']==title),None)
 if e and e['id']=='mujoco':
  missing='\n'.join('![MuJoCo GPU baseline throughput](images/'+name+')'for name in('mujoco-humanoid-throughput.png','mujoco-throughput.png')if 'images/'+name not in content)
  if missing:content=content.replace('</details>\n<!-- /BASELINE-PLOTS -->',missing+'\n\n</details>\n<!-- /BASELINE-PLOTS -->',1)
 if e and e['id']in amd:
  info=amd[e['id']];badge='<span class="amd-mark" style="display:inline-block;background:#000;color:#fff;font-weight:800;padding:2px 9px;line-height:1.4;border-radius:2px">AMD</span>'
  block='<!-- AMD-SOLUTION -->\n'+badge+' · [AMD 블로그 소개]('+info['blog']+') · [GPU 지원 경로]('+info['solution']+')\n<!-- /AMD-SOLUTION -->\n\n'
  content=content.replace('### 1. Simulator 설명\n','### 1. Simulator 설명\n\n'+block,1)
 out+=['## '+title,content]
s='\n'.join(out)
f.write_text(s,encoding='utf-8')
f=B/'docs/benchmark-recipes.md';s=f.read_text(encoding='utf-8')
s=re.sub(r'Native CPU uses[^\n]*','CPU execution is retained only for same-scene GPU sanity checks. CPU throughput is excluded from this campaign and is not a simulator performance result.',s)
s=s.replace('python3 ${LAB_ROOT}/provided_mjx_suite.py','PROVIDED_MJX_ALIGNED=1 python3 ${LAB_ROOT}/provided_mjx_suite.py') if 'PROVIDED_MJX_ALIGNED=1 python3 ${LAB_ROOT}/provided_mjx_suite.py'not in s else s
s=s.replace('`publish_provided_images.py`, `render_final.py`','`publish_provided_images.py`, `gpu_campaign_audit.py`, `enforce_gpu_report_scope.py`, `render_final.py`')
f.write_text(s,encoding='utf-8')
assert not re.search(r'^## .*?(?:PyBullet|Drake|Gazebo|SOFA|URLab|Schola)',(O/'confluence-report.md').read_text(encoding='utf-8'),re.M)
assert 'mujoco-cpu-bench'not in (O/'confluence-report.md').read_text(encoding='utf-8')
data=json.loads((O/'benchmark-data.json').read_text(encoding='utf-8'))
assert not any(x.get('engine')in excluded or x.get('backend_observed')in('cpu','CPU')for x in data)
print('GPU-only scope PASS: 8 physics engines, 1 rendering benchmark; CPU throughput excluded')
