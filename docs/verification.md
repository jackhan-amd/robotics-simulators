# 동작 확인 기준

설치와 source build가 끝나면 각 recipe의 작은 장면을 실행한다. `SMOKE_RESULT_JSON`의 실제 backend, 수치와 device를 확인한다. Child 종료0만으로 새 run의 G1을 확정하지 않는다.

| 확인 단계 | 확인할 내용 |
|---|---|
| 설치·빌드 | Python3.12, 고정 source·dependency, compiler 설정, binary 생성 |
| Backend | 실제 solver의 CPU/HIP/AMD 선택과 실제 GPU 이름·ISA |
| 물리 | 유한 상태, dt·step, 중력·접촉·mass·field 등 해당 장면의 gate |
| CPU 대조 | 같은 장면·규모·dt에서 선언한 허용치로 비교 |
| GPU 실행 | physics kernel profiler/trace와 실제 numerical step |

Headless 장면에는 GPU renderer와 policy 추론을 섞지 않는다. Native CPU 실행은 `CPU_ONLY`로 표시한다. GPU를 요청했는데 CPU로 실행되면 GPU PASS로 올리지 않는다. 성능 G2는 별도 범위다.

## 보존한 검증 범위

Instinct Sim·Taichi·GSplat의 새 카탈로그 연결 3개는 `UNREVIEWED_CATALOG_ENTRY`로 구분합니다. 이전 MI355X study 측정과 새 카탈로그 실행의 검증은 별개입니다.

2026-10-23까지 검토한 GPU 구성 중 이 저장소에 포함된 13개 구성의 범위만 [verification-summary.json](../configs/verification-summary.json)에 유지한다. 각 엔진·scene·backend와 수치 gate를 담고 throughput·개별 run ID·일지·raw log를 포함하지 않는다. 이 요약은 새 설치나 새 실행을 자동 검증하지 않는다.

새 실행의 JSON은 `${STUDY_PRIVATE_ROOT}/results/runs/<node>/<id>/result.json`, 실제 명령·원본 로그·source snapshot은 `${STUDY_PRIVATE_ROOT}/runs/<node>/<id>/`에 남긴다. 결과 상태는 검토 전 `PENDING_VALIDATION`이다. Raw evidence는 Git에 추가하지 않는다.

CUDA 열의 과거 기록과 현재 ROCm recipe는 구현·설정이 다를 수 있다. `cuda_reference_status`가 없는 항목은 이 저장소가 CUDA 실행을 주장하지 않는 항목이다. 기존 RTX3090 비교 기록은 로컬 연구 archive에 보존한다.
