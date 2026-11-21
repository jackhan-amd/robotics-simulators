# FluidLab prerequisites and measurement scope

## MI355X measurement scope: forward simulation

The reported performance covers **forward simulation only** in the supplied `MixingEnv(version=0)`. Gradient/backward computation, training, control or trajectory optimization, and optimizer iterations were not tested. These measurements do not describe those paths.

Physics ran on the **GPU of the same MI355X server** where FluidLab was installed. No other server or external compute service was used. Runtime sources and environments occupy local directories separate from the Git working tree and form part of the benchmark project's execution environment.

| Condition | Measured setting |
|---|---|
| Scene | Supplied MixingEnv: coffee/milk, cup, supplied agent |
| Particles | 86,527 |
| envs | 1, 2, 4, 8; independent GPU process replicas |
| outer dt / substeps | 0.002 s / 10 |
| measured steps / repeats | 100 steps per env / 5 repeats |
| warm-up | 50 steps; excluded from timing |
| seed / control | 0 / stationary agent, zero action |
| Execution scope | forward TaichiEnv.step; excludes loss, gradients, optimizer and renderer |

The public repository includes the [execution adapter](../../recipes/fluidlab/benchmarks/provided_fluidlab_model.py), [timing code](../../tools/benchmarks/provided_replicas.py), [execution coordinator](../../tools/benchmarks/provided_replicas_suite.py), setup and compatibility tools, and configuration. **The complete FluidLab engine source is not committed here.** It is obtained as the upstream dependency described below. This distinction concerns source distribution and file layout, not where computation runs.

## Reviewed gfx1151 MPM core smoke

The earlier local environment ran the FluidLab MPM core with AMD Taichi's `ti.amdgpu`. The scene uses 27 water particles, a 16³ grid, dt 0.0002 s and 250 substeps.

## Upstream connection

Use the [common dependency convention](../../docs/upstream-dependencies.md) shared by all engines.

```bash
export STUDY_STORAGE_ROOT="$PWD/.runtime"
python3 tools/fetch_sources.py fetch --engine fluidlab
export FLUIDLAB_SOURCE_ROOT="$STUDY_STORAGE_ROOT/upstream/fluidlab"
export STUDY_FLUIDLAB_SOURCE="$FLUIDLAB_SOURCE_ROOT"
```

Cloning obtains source code. Runtime builds, compatibility preparation and GPU validation are separate steps.

## Public installation recipe limitations

The [pinned FluidLab source](https://github.com/zhouxian/FluidLab/tree/7295eb6ed7ee92b2be471fd30b432238577f28ce) has no root license grant. Renderer subdirectory licenses do not establish rights to use or redistribute the complete MPM source. This repository distributes neither that source nor the contextual API port patch. The common clone tool connects the pinned upstream commit, as it does for other engines.

These instructions apply to environments with an authorized source/runtime whose API compatibility has been checked. They do not claim a completed public installation path for new users. The reviewed Taichi build used public AMD source commit `d05e4aaf257c172d1b4655c548e038b92df67da2` and LLVM20.1.8. Local artifact identifiers are recorded in the [configuration](../../configs/fluidlab-resolution.json).

## Local prerequisites and execution

```bash
export STUDY_FLUIDLAB_SOURCE="$LICENSED_LOCAL_FLUIDLAB_SOURCE"
bash recipes/fluidlab/check-prerequisites.sh
python3 -m simulators smoke fluidlab-mpm --execute
```

Provide Python3.12 from the dedicated `venvs/fluidlab` and `build/fluidlab-runtime-gfx1151`. The runtime must contain actual gfx1151 ISA bitcode. Leave the original source and installed Taichi unchanged.

Check particle count, mass, domain bounds, center-of-mass gravity behavior, finite state and actual HIP kernels. Retain the CPU comparison of all particle positions and velocities. This recipe covers the forward MPM core; it does not validate the renderer or complete task environment.
