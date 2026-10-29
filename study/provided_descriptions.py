"""Describe the actual supplied GPU examples; keep earlier microbenchmarks as references."""
import json,pathlib,re
B=pathlib.Path(__file__).resolve().parents[1];O=B/'report';p=json.loads((B/'study/plan.json').read_text(encoding='utf-8'));f=O/'confluence-report.md';s=f.read_text(encoding='utf-8')
descriptions={
'mujoco':'제공 Humanoid 관절 모델을 MJWarp HIP와 MJX-JAX ROCm에서 실행한다. 모델은 27 DOF, actuator 21개, body 17개, geom 20개이며 dt=0.005 s다. 제공 keyframe에서 시작하고 control은 0으로 유지한다. 학습된 보행 policy는 포함하지 않는다.\n\n측정 구간은 1000 step이며 초기화·컴파일·warm-up·reset·readback을 제외하고 GPU를 동기화한다. 초기 20 step의 CPU 궤적은 GPU sanity check에 사용했다. 버전별 시도와 실패는 분리해 기록한다. 공–바닥 기초 측정은 참고 구획에 남겼다.',
'instinct':'AMD의 제공 HipLiberoVectorEnv와 고정된 LIBERO spatial task 0을 사용한다. 장면은 검은 bowl을 plate 위로 옮기는 조작 task의 원본 모델·초기 상태이며, 입력은 0인 7차원 action이다. 제공 GPU OSC와 물리 계산, 128×128 카메라 관측 경로를 실행하고 학습 policy는 사용하지 않는다.\n\n처리량은 제공 env.step의 end-to-end 값으로, GPU 물리·제어·렌더링과 관측 전송·성공 판정의 host 작업을 포함한다. 초기화·reset·warm-up은 제외한다. 제공 기본 control frequency는 20 Hz이며 한 제어 step은 약 0.002 s인 물리 step 25개를 포함한다. 순수 physics-only 기초 측정은 참고 구획에 분리했다.',
'genesis':'제공 single_franka_envs.py의 Franka 모델과 sph_rigid.py의 SPH–강체 coupling 모델을 사용한다. Franka는 제공 장면의 관절과 plane을 유지하고 native GPU batch로 env 수를 늘린다. 별도 policy나 controller를 추가하지 않는다.\n\nSPH 예제는 216,000개 입자의 유체와 낙하하는 강체 cube를 포함한다. 제공 재료·경계·입자 해상도·coupling 설정을 유지하며, Scene.step의 dt=0.01 s와 substeps=10을 사용한다. 유체는 GPU 프로세스별 독립 env를 복제하므로 Franka의 native batch와 실행 방식이 다르다.',
'chrono':'이번 평가는 Chrono의 HIP FSI-SPH와 DEM 모듈을 대상으로 한다. 제공 demo_FSI-SPH_DamBreak.cpp와 demo_DEM_repose.cpp를 사용하며, CPU multibody 성능은 포함하지 않는다.\n\nDamBreak는 유체 입자 16,731개를 0.1 s 구간에서 측정했다. DEM repose는 동적·고정 입자 합계 105,704개를 유지하고 1 ms의 초기 과도 구간을 측정했다. DEM의 표 단위는 AdvanceSimulation(0.001 s) 호출이며, 고정 물리 dt는 2.5e-6 s다. 최종 repose angle이나 완성된 mound의 처리량을 나타내지는 않는다. 두 예제 모두 제공 모델·재료·solver를 유지했고 초기화와 최종 상태 검증은 타이머 밖에 두었다.',
'incflo':'제공 benchmark.lid_driven_cavity 입력의 128×128 격자와 50 step을 사용한다. 기본 CFL=0.45, fixed_dt=-1, 재료와 lid 속도를 유지한다. 같은 모델을 GPU 프로세스별로 복제해 env scaling을 측정한다.\n\nInitData 이후 barrier에서 시작해 Evolve를 측정하며, 제공 예제의 diagnostics와 plot 출력은 포함한다. 각 프로세스가 GPU 메모리 대부분을 미리 예약하지 않도록 AMReX 초기 arena 크기만 64 MiB로 설정했다. 기존 격자 크기별 기초 측정은 참고 구획에 분리했다.',
'nekrs':'제공 examples/tgv의 Taylor–Green vortex를 HIP에서 실행한다. 제공 mesh, polynomial order 7, cubature order 9, Re=1600, dt=0.003 s와 solver 설정을 유지한다. env마다 독립적인 단일 MPI rank GPU 프로세스를 실행한다.\n\n초기화와 JIT 뒤 100 step을 예열하고, 이어지는 100-step 구간 5개를 동기화해 측정한다. 이 5개는 매번 초기화한 독립 반복이 아니라 상태가 이어지는 한 궤적의 측정 구간이다. 제공 energy·enstrophy diagnostics는 타이머에 포함한다. 유한 상태와 에너지 감소를 확인했으며, 전체 DNS 정확도 검증은 수행하지 않았다. Ethier 기초 측정은 참고 구획에 남겼다.',
'fluidlab':'제공 MixingEnv의 milk·coffee 입자, cup과 agent를 유지한 forward MPM 시험이다. 입자는 86,527개이며 dt=0.002 s인 env.step 하나가 물리 substep 10개를 포함한다. 제공 agent는 0 action으로 정지시키고, loss·gradient·optimizer와 renderer는 사용하지 않는다.\n\ngeometry·재료·격자·경계 설정을 유지하고 headless 실행 및 Taichi API 호환에 필요한 부분만 보완했다. 초기화·warm-up·reset·검증 readback을 제외하고 env.step 구간을 측정한다. 각 env는 독립 GPU 프로세스다. 기초 MPM core 측정과 전체 제공 task 결과를 구분해 제시한다.',
'taichi':'AMD 공식 b2 payload의 제공 simulation/mpm88.py를 사용한다. 8,192개 입자와 128×128 grid의 MLS-MPM 예제로, 제공 P2G·grid update·G2P 커널, 재료·경계·dt=0.0002 s를 유지한다.\n\nGUI 반복을 headless 측정으로 바꾸고 AMD backend와 seed를 명시했다. 1000 substep 구간을 측정하며 env마다 GPU 프로세스를 하나씩 실행한다. 입자 수·질량·유한 상태와 변위를 확인했다. 이전 독립 입자 중력 적분 수치는 별도의 기초 참고 자료다.',
'gsplat':'물리 시뮬레이터와 구분한 GPU 렌더링 보조 항목이다. 제공 test_garden.npz와 공식 helper를 사용한 111,785개 Gaussian, 648×420 출력에서 카메라 수를 늘린다. 카메라들은 정적 geometry를 공유한다.\n\n제공 자산의 좌표·색상과 helper의 scale·회전·opacity 초기화값을 사용한다. 학습된 checkpoint의 화질이나 학습 시간을 평가하는 시험은 아니다. MI355X 실행 결과는 이번 환경의 실측이며, AMD 문서의 GSplat 지원 GPU 목록과 구분한다.'}
parts=re.split(r'^## (.+)\s*$',s,flags=re.M);out=[parts[0]];archived={}
for title,body in zip(parts[1::2],parts[2::2]):
 e=next((e for e in p['engines']if e['title']==title),None)
 if e and e['id']in descriptions:
  m=re.search(r'(### 1\. Simulator 설명\s*)(.*?)(?=### 2\. Software)',body,flags=re.S)
  if m:
   archived[e['id']]=m[2];licenses=[para for para in m[2].split('\n\n')if any(word in para for word in('라이선스','재배포'))];body=body[:m.start()]+m[1]+descriptions[e['id']]+'\n\n'+'\n\n'.join(licenses)+'\n\n'+body[m.end():]
  if e['id']=='mujoco':body=re.sub(r'^\|\s*cpu\s*\|.*\n','',body,flags=re.M)
 out+=['## '+title,body]
f.write_text('\n'.join(out),encoding='utf-8');archive=B/'_workspace/gpu-scope-revision';archive.mkdir(parents=True,exist_ok=True);(archive/'prior-descriptions.json').write_text(json.dumps(archived,ensure_ascii=False,indent=2),encoding='utf-8')
print('Updated supplied-example descriptions:',len(archived))
