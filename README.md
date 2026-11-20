# Robotics simulators on AMD GPUs

GPU simulator installation recipes, bounded headless smokes and MI355X
throughput/scalability benchmarks. Original copyright and third-party notices
are retained.

## MI355X performance snapshot

Measurements used one AMD Instinct MI355X (gfx950, 288 GiB), Ubuntu 24.04.5
and Python 3.12.3. Each row shows the median of five synchronized samples at
the highest-throughput environment count tested for that workload.

| Simulator / backend | Supplied workload | Envs / cameras | Throughput | Unit |
|---|---|---:|---:|---|
| MuJoCo MJX-JAX | Humanoid | 65,536 | 485,624.779 | env-steps/s |
| MuJoCo MJWarp | Humanoid | 65,536 | 4,940,426.031 | env-steps/s |
| Instinct Sim | LIBERO spatial task 0 | 32 | 1,183.118 | env-steps/s |
| Genesis World | Franka | 65,536 | 3,941,084.509 | env-steps/s |
| Genesis World | SPH liquid / rigid coupling | 8 | 35.104 | env-steps/s |
| Project Chrono | FSI-SPH DamBreak | 4 | 2,064.136 | env-steps/s |
| Project Chrono | DEM repose | 4 | 0.119 | env-advance-calls/s (1 ms) |
| AMReX incflo | 2D lid-driven cavity | 4 | 60.568 | env-steps/s |
| nekRS | Taylor–Green vortex, Re=1600 | 4 | 23.986 | env-steps/s |
| FluidLab | MixingEnv, forward only | 4 | 9.650 | env-steps/s |
| Taichi Lang | MPM88 liquid | 8 | 3,967.819 | env-steps/s |
| GSplat | Garden fixture, forward rasterization | 32 | 6,754.008 | camera-frames/s |

Scenes, time steps, solvers and timing boundaries differ across rows, so these
values do not rank the simulators. Envs use native GPU batching or independent
GPU processes; GSplat batches cameras. Instinct Sim includes physics, control,
camera rendering and host observation work. Chrono DEM counts 1 ms advance
calls, each containing internal substeps. FluidLab covers forward simulation;
GSplat covers forward rasterization. Their training and gradient performance
was not measured.

See [benchmark settings](docs/benchmark-parameters.md) for models, warm-up,
solver and timing parameters, [engine recipes](docs/benchmark-recipes.md) for
software versions and commands, and the [quick start](docs/benchmark-quickstart.md)
to run a benchmark. The full tabbed report, plots and accepted execution logs
remain local; generated report files are excluded from Git.

## Simulator recipes

| Component | GPU workload | Installation and execution |
|---|---|---|
| MuJoCo MJX / MJWarp | Articulated rigid-body physics | [GPU recipes](recipes/mujoco/README.md), [Humanoid benchmark](docs/benchmark-recipes.md) |
| Genesis World | Rigid, SPH, MPM and coupled physics | [Recipe](recipes/genesis/README.md), [Benchmarks](docs/benchmark-tools.md) |
| Project Chrono | HIP FSI-SPH and DEM | [Recipe](recipes/chrono/README.md), [Benchmarks](docs/benchmark-recipes.md) |
| AMReX incflo | HIP Eulerian CFD | [Recipe](recipes/incflo/README.md), [Benchmarks](docs/benchmark-recipes.md) |
| nekRS | HIP spectral-element CFD | [Recipe](recipes/nekrs/README.md), [Benchmarks](docs/benchmark-recipes.md) |
| FluidLab | HIP MPM; operator-authorized upstream required | [Local prerequisites](recipes/fluidlab/README.md) |
| Instinct Sim | LIBERO GPU physics, control and cameras | [Recipe](recipes/instinct/README.md) |
| Taichi Lang | AMD GPU MPM88 | [Recipe](recipes/taichi/README.md) |
| GSplat | GPU Gaussian rasterization; rendering benchmark | [Recipe](recipes/gsplat/README.md) |

The first eight components perform physics simulation. GSplat is a separate
rendering library. CPU-only engines and standalone CPU performance tests are
excluded. Short CPU calculations remain only where a GPU numerical sanity check
requires them.

[Experiment settings](docs/benchmark-parameters.md) lists model, solver, env count, warm-up, seed and timing settings; a locally generated JSON snapshot can include both measured cohorts.

All engines use [pinned upstream dependency links](docs/upstream-dependencies.md) and the common `tools/fetch_sources.py` clone tool. Engine dependencies may live under the project-local, Git-ignored `.runtime/` directory; this is a file-layout choice, not remote computation.

See [the source layout](docs/repository-layout.md) for engine-owned smoke/benchmark code, shared benchmark infrastructure and supported entry points.

For clone-to-benchmark instructions, follow [the benchmark quick start](docs/benchmark-quickstart.md).

Start with [common prerequisites](recipes/README.md), [verification rules](docs/verification.md)
and the relevant engine recipe. Core smokes preserve their reviewed gfx1151
configuration. The separate [MI355X benchmarks](docs/benchmark-tools.md) provides gfx950 build
adapters and supplied-example environment scaling; those targets are not interchangeable.
The historical review summary does not validate a new machine or run.

```bash
python3 -m simulators list
python3 -m simulators check
python3 -m simulators smoke mujoco-mjx-rocm    # preview only
```

Keep upstream sources, Python environments, models, datasets, caches, raw logs
and credentials in configured external storage. No server address, private
profile, individual run history or generated report is included in this repository.
See [benchmark configuration](configs/benchmark-profile.example.json) and source/dependency observations (local output: `report/evidence/software-observations.json`).

Run repository checks with Python 3.12:

```bash
python3 -m unittest discover -s tests -v
python3 -m simulators check
python3 tools/assets.py check
python3 -m simulators build
python3 tools/audit_publication.py
git diff --check
```

These checks validate wiring and recording behavior. Actual GPU physics and
throughput require the documented engine runtime and separate evidence review.

Our tooling retains its [MIT license](LICENSE). Adapted code and external
dependencies keep their own terms; see [LICENSES.md](LICENSES.md),
[file exceptions](configs/license-exceptions.json) and [verbatim notices](third_party_notices/).

The optional recipe index generated by `python3 -m simulators build` is stored at `.runtime/catalog/index.html`, separate from benchmark reports. `report/mi355x-simulator-report.html` is the customer report; its linked evidence, images and regeneration inputs remain local under `report/`.
