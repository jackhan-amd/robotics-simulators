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

Build FSI-SPH and DEM from [Chrono](https://github.com/projectchrono/chrono) commit `6f4004c358e5d0029aa3e39fc5ed13d66216f494` for HIP/gfx1151. The native multibody core uses a separate CPU solver.

## Required tools

Prepare [common runtime storage](../README.md), CMake≥3.24, Ninja, a C++17 compiler, the HIP SDK and Eigen sources. The script fetches Eigen commit `3147391d946bb4b6c68edd901f2add6ac1f31f8c`. Set `ROCM_PATH` or provide the common SDK environment.

## Build

```bash
bash recipes/chrono/build.sh
```

Sources are stored in `upstream/chrono` and builds in `build/chrono-hip-devel`. The main options are:

```text
CHRONO_GPU_BACKEND=HIP
CHRONO_HIP_ARCHITECTURES=gfx1151
CMAKE_HIP_ARCHITECTURES=gfx1151
CH_ENABLE_MODULE_FSI=ON
CH_ENABLE_MODULE_DEM=ON
BUILD_TESTING=OFF
```

The script builds `Chrono_fsisph`, `Chrono_dem` and `ChronoModels_robot`, then compiles the bounded executables from `recipes/chrono/smoke` into `build/chrono-smoke-hip`. It uses 2 parallel jobs and a 900-second limit per stage. See [build.sh](build.sh) for compiler and CMake arguments.

## Run

```bash
python3 -m simulators smoke chrono-fsi --execute
python3 -m simulators smoke chrono-dem --execute
```

Each scene runs for 50 steps. FSI-SPH checks particles, boundaries, mass and finite state; DEM checks gravity, contact and state conditions. Confirm the actual HIP physics kernels and selected device.

Official reference: [AMD GPU build guide](https://github.com/projectchrono/chrono/blob/main/docs/README_AMD_GPU.md). These Linux gfx1151 scenes have a separate scope from upstream results on other operating systems or GPUs. BSD-3-Clause.
