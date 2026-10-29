# FluidLab 로컬 MPM 실행 조건

기존 로컬 환경에서는 FluidLab MPM core를 AMD Taichi의 `ti.amdgpu`로 실행했다. 장면은 물27입자, grid16³, dt0.0002초, 250substeps다.

## 공개 설치 recipe의 제약

[고정 FluidLab source](https://github.com/zhouxian/FluidLab/tree/7295eb6ed7ee92b2be471fd30b432238577f28ce)에 root license grant가 없다. Renderer 하위 라이선스로 MPM source 전체의 사용·재배포 권한을 추정하지 않는다. 이 저장소는 해당 source와 contextual API port patch를 배포하거나 자동 취득하지 않는다.

따라서 이 항목은 기존에 사용 허가와 API 호환성을 확인한 source/runtime이 있는 환경의 실행 절차다. 새 사용자용 공개 설치가 완료됐다고 표시하지 않는다. Taichi는 공개 AMD source commit `d05e4aaf257c172d1b4655c548e038b92df67da2`와 LLVM20.1.8을 사용했다. 로컬 artifact 식별은 [구성 정보](../../configs/fluidlab-resolution.json)에 있다.

## 로컬 prerequisites와 실행

```bash
export STUDY_FLUIDLAB_SOURCE="$LICENSED_LOCAL_FLUIDLAB_SOURCE"
bash recipes/fluidlab/check-prerequisites.sh
python3 -m simulators smoke fluidlab-mpm --execute
```

전용 `venvs/fluidlab`의 Python3.12와 `build/fluidlab-runtime-gfx1151`이 필요하다. Runtime에는 실제 gfx1151 ISA bitcode를 사용한다. 원본 source와 installed Taichi를 덮어쓰지 않는다.

Particle 수·mass·domain·COM 중력·유한 상태와 실제 HIP kernel을 확인한다. 전체 particle 위치·속도의 CPU 기준 대조도 유지한다. 이 recipe는 forward MPM core 범위이며 renderer·전체 task 환경의 실행을 뜻하지 않는다.
