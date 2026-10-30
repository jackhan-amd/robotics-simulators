# Project Chrono: HIP FSI-SPH·DEM

## Upstream source connection

This engine follows the [common upstream dependency convention](../../docs/upstream-dependencies.md).
The project tracks its adapters and pinned source declaration; the upstream engine
is a separate Git checkout in configured local runtime storage.

```bash
python3 tools/fetch_sources.py plan --engine chrono
python3 tools/fetch_sources.py fetch --engine chrono
```

Source checkout is separate from the GPU runtime build and smoke below. The source
directory is a project dependency; it does not indicate a remote compute service.

[Chrono](https://github.com/projectchrono/chrono) commit `6f4004c358e5d0029aa3e39fc5ed13d66216f494`의 FSI-SPH와 DEM을 HIP/gfx1151로 빌드한다. Native multibody core는 별도 CPU solver다.

## 필요한 도구

[공통 외장 경로](../README.md), CMake≥3.24, Ninja, C++17 compiler, HIP SDK와 Eigen source가 필요하다. Eigen은 script가 commit `3147391d946bb4b6c68edd901f2add6ac1f31f8c`로 가져온다. `ROCM_PATH` 또는 공통 SDK provider를 준비한다.

## 빌드

```bash
bash recipes/chrono/build.sh
```

Source는 `upstream/chrono`, build는 `build/chrono-hip-devel`에 둔다. 주요 설정은 다음과 같다.

```text
CHRONO_GPU_BACKEND=HIP
CHRONO_HIP_ARCHITECTURES=gfx1151
CMAKE_HIP_ARCHITECTURES=gfx1151
CH_ENABLE_MODULE_FSI=ON
CH_ENABLE_MODULE_DEM=ON
BUILD_TESTING=OFF
```

Script는 `Chrono_fsisph`, `Chrono_dem`, `ChronoModels_robot`을 빌드한 뒤 `recipes/chrono/smoke`의 작은 실행 파일을 `build/chrono-smoke-hip`에 만든다. 병렬 작업2개, 단계별 최대900초다. 원본 compiler·CMake 인자는 [build.sh](build.sh)에서 확인한다.

## 실행

```bash
python3 -m simulators smoke chrono-fsi --execute
python3 -m simulators smoke chrono-dem --execute
```

각 장면은50step이다. FSI-SPH는 particle·boundary·mass·유한 상태를, DEM은 중력·접촉·상태 조건을 확인한다. 실제 HIP physics kernel과 선택한 장치를 확인한다.

공식 자료: [AMD GPU build guide](https://github.com/projectchrono/chrono/blob/main/docs/README_AMD_GPU.md). Linux gfx1151의 이 장면과 upstream의 다른 OS·GPU 결과를 구분한다. BSD-3-Clause.
