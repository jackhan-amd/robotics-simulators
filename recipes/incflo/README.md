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

Run Eulerian incompressible CFD on a small 2D grid. This workload does not provide a like-for-like comparison with SPH particle throughput.

| Source | Pinned commit |
|---|---|
| [incflo](https://github.com/AMReX-Fluids/incflo) | `ccb90bc41d9def18dddc4e1c4122a7d517add630` |
| [AMReX](https://github.com/AMReX-Codes/amrex) | `7f2fecd4adefeb6bcbc2a6d87243f062da0ef912` |
| [AMReX-Hydro](https://github.com/AMReX-Fluids/AMReX-Hydro) | `a153304acd787205b170b0f7fd8284627e076056` |

## Build

Use the HIP SDK, CMake and Ninja from the [common prerequisites](../README.md).

```bash
bash recipes/incflo/build.sh
```

The main options are `INCFLO_HIP=ON`, `INCFLO_DIM=2`, `INCFLO_MPI=OFF`, `INCFLO_OMP=OFF`, `INCFLO_EB=OFF` and `AMReX_AMD_ARCH=gfx1151`. Set `AMREX_HOME` and `AMREX_HYDRO_HOME` to their pinned checkouts. The output binary is `build/incflo-hip-devel/incflo.ex`.

## Run

```bash
python3 -m simulators smoke incflo-hip --execute
```

The harness creates a small cavity input and runs 50 steps. Check the grid, dt, finite fields, actual numerical progress and HIP device. Accuracy checks compare CPU fields at the same grid and step count. Inspect commands and settings with `python3 -m simulators show incflo-hip`.

Keep sources, builds, caches and field output in runtime storage. Each stage uses a bounded timeout and 2 parallel jobs. Retain BSD-3-Clause and AMReX notices.
