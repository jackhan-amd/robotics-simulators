# FluidLab 실행 조건과 측정 범위

## MI355X 측정 범위: forward simulation만 측정

현재 성능 결과는 제공 `MixingEnv(version=0)`의 **forward simulation만** 측정한 것입니다. Gradient/backward 계산, 학습, 제어·궤적 최적화와 optimizer 반복은 시험하지 않았습니다. 이 결과를 해당 경로의 성능으로 해석하지 않습니다.

물리 계산은 FluidLab 엔진을 설치한 **동일 MI355X 서버의 GPU**에서 실행했습니다. 다른 서버나 외부 계산 서비스를 호출한 것이 아닙니다. 실행용 source·환경을 Git working tree와 분리한 로컬 디렉터리에 배치했다는 의미이며, 이 의존성도 전체 benchmark project의 실행 환경에 해당합니다.

| 조건 | 측정 설정 |
|---|---|
| 장면 | 제공 MixingEnv: coffee/milk, cup, supplied agent |
| 입자 수 | 86,527 |
| envs | 1, 2, 4, 8; 독립 GPU 프로세스 복제 |
| outer dt / substeps | 0.002초 / 10 |
| measured steps / 반복 | env당 100 step / 5회 |
| warm-up | 50 step; 계측 제외 |
| seed / 제어 | 0 / stationary agent, zero action |
| 실행 범위 | forward TaichiEnv.step; loss·gradient·optimizer·renderer 제외 |

공개 Git에 add·commit된 것은 [실행 어댑터](../../recipes/fluidlab/benchmarks/provided_fluidlab_model.py), [계측 코드](../../tools/benchmarks/provided_replicas.py), [실행 coordinator](../../tools/benchmarks/provided_replicas_suite.py), 준비·호환성 도구와 설정입니다. **FluidLab 원본 엔진 source 전체는 이 Git 저장소에 add·commit되어 있지 않습니다.** 아래 upstream source를 별도 의존성으로 사용합니다. 이는 파일 배치·소스 배포 방식에 관한 구분이며 계산 위치에 관한 구분이 아닙니다.

## 기존 gfx1151 MPM core smoke

기존 로컬 환경에서는 FluidLab MPM core를 AMD Taichi의 `ti.amdgpu`로 실행했다. 장면은 물27입자, grid16³, dt0.0002초, 250substeps다.

## Upstream 연결

모든 엔진의 [공통 의존성 연결 방식](../../docs/upstream-dependencies.md)을 사용합니다.

```bash
export STUDY_STORAGE_ROOT="$PWD/.runtime"
python3 tools/fetch_sources.py fetch --engine fluidlab
export FLUIDLAB_SOURCE_ROOT="$STUDY_STORAGE_ROOT/upstream/fluidlab"
export STUDY_FLUIDLAB_SOURCE="$FLUIDLAB_SOURCE_ROOT"
```

Clone은 source 확보 단계이며 runtime 빌드·호환성 준비·GPU 검증은 별도 단계입니다.

## 공개 설치 recipe의 제약

[고정 FluidLab source](https://github.com/zhouxian/FluidLab/tree/7295eb6ed7ee92b2be471fd30b432238577f28ce)에 root license grant가 없다. Renderer 하위 라이선스로 MPM source 전체의 사용·재배포 권한을 추정하지 않는다. 이 저장소는 해당 source와 contextual API port patch를 배포하지 않습니다. 다른 엔진과 같은 공통 clone 도구로 고정 upstream commit을 연결합니다.

따라서 이 항목은 기존에 사용 허가와 API 호환성을 확인한 source/runtime이 있는 환경의 실행 절차다. 새 사용자용 공개 설치가 완료됐다고 표시하지 않는다. Taichi는 공개 AMD source commit `d05e4aaf257c172d1b4655c548e038b92df67da2`와 LLVM20.1.8을 사용했다. 로컬 artifact 식별은 [구성 정보](../../configs/fluidlab-resolution.json)에 있다.

## 로컬 prerequisites와 실행

```bash
export STUDY_FLUIDLAB_SOURCE="$LICENSED_LOCAL_FLUIDLAB_SOURCE"
bash recipes/fluidlab/check-prerequisites.sh
python3 -m simulators smoke fluidlab-mpm --execute
```

전용 `venvs/fluidlab`의 Python3.12와 `build/fluidlab-runtime-gfx1151`이 필요하다. Runtime에는 실제 gfx1151 ISA bitcode를 사용한다. 원본 source와 installed Taichi를 덮어쓰지 않는다.

Particle 수·mass·domain·COM 중력·유한 상태와 실제 HIP kernel을 확인한다. 전체 particle 위치·속도의 CPU 기준 대조도 유지한다. 이 recipe는 forward MPM core 범위이며 renderer·전체 task 환경의 실행을 뜻하지 않는다.
