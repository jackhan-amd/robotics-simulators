# AMReX incflo: HIP 2D CFD

## Upstream source connection

This engine follows the [common upstream dependency convention](../../docs/upstream-dependencies.md).
The project tracks its adapters and pinned source declaration; the upstream engine
is a separate Git checkout in configured local runtime storage.

```bash
python3 tools/fetch_sources.py plan --engine incflo
python3 tools/fetch_sources.py fetch --engine incflo
```

Source checkout is separate from the GPU runtime build and smoke below. The source
directory is a project dependency; it does not indicate a remote compute service.

Eulerian incompressible CFD를 작은 2D grid로 실행한다. SPH particle 처리량과 비교하는 장면은 아니다.

| Source | 고정 commit |
|---|---|
| [incflo](https://github.com/AMReX-Fluids/incflo) | `ccb90bc41d9def18dddc4e1c4122a7d517add630` |
| [AMReX](https://github.com/AMReX-Codes/amrex) | `7f2fecd4adefeb6bcbc2a6d87243f062da0ef912` |
| [AMReX-Hydro](https://github.com/AMReX-Fluids/AMReX-Hydro) | `a153304acd787205b170b0f7fd8284627e076056` |

## 빌드

[공통 준비](../README.md)의 HIP SDK와 CMake·Ninja를 사용한다.

```bash
bash recipes/incflo/build.sh
```

주요 설정은 `INCFLO_HIP=ON`, `INCFLO_DIM=2`, `INCFLO_MPI=OFF`, `INCFLO_OMP=OFF`, `INCFLO_EB=OFF`, `AMReX_AMD_ARCH=gfx1151`이다. `AMREX_HOME`과 `AMREX_HYDRO_HOME`을 각각의 고정 checkout으로 지정한다. 결과 binary는 `build/incflo-hip-devel/incflo.ex`다.

## 실행

```bash
python3 -m simulators smoke incflo-hip --execute
```

Harness가 작은 cavity 입력을 만들고50step을 실행한다. Grid·dt·유한 field, 실제 수치 step과 HIP device를 확인한다. 정확도 대조에서는 같은 grid·step의 CPU field와 비교한다. 세부 command와 설정은 `python3 -m simulators show incflo-hip`로 조회한다.

Source/build/cache와 field output은 외장 저장소에 둔다. 각 단계는 제한된 timeout과 병렬 작업2개를 사용한다. BSD-3-Clause 및 AMReX 고지 유지.
