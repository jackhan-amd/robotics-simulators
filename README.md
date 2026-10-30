# Robotics simulators on AMD GPUs

GPU simulator installation recipes, bounded headless smokes and MI355X
throughput/scalability adapters. This repository is derived from
[haanjack/robotics-sim-lab](https://github.com/haanjack/robotics-sim-lab).
Original copyright and third-party notices are retained.

| Component | GPU workload | Installation and execution |
|---|---|---|
| MuJoCo MJX / MJWarp | Articulated rigid-body physics | [GPU recipes](recipes/mujoco/README.md), [Humanoid study](study/REPRODUCE.md) |
| Genesis World | Rigid, SPH, MPM and coupled physics | [Recipe](recipes/genesis/README.md), [study](study/README.md) |
| Project Chrono | HIP FSI-SPH and DEM | [Recipe](recipes/chrono/README.md), [study](study/REPRODUCE.md) |
| AMReX incflo | HIP Eulerian CFD | [Recipe](recipes/incflo/README.md), [study](study/REPRODUCE.md) |
| nekRS | HIP spectral-element CFD | [Recipe](recipes/nekrs/README.md), [study](study/REPRODUCE.md) |
| FluidLab | HIP MPM; operator-authorized upstream required | [Local prerequisites](recipes/fluidlab/README.md) |
| Instinct Sim | LIBERO GPU physics, control and cameras | [Recipe](recipes/instinct/README.md) |
| Taichi Lang | AMD GPU MPM88 | [Recipe](recipes/taichi/README.md) |
| GSplat | GPU Gaussian rasterization; rendering benchmark | [Recipe](recipes/gsplat/README.md) |

The first eight components perform physics simulation. GSplat is a separate
rendering library. CPU-only engines and standalone CPU performance tests are
excluded. Short CPU calculations remain only where a GPU numerical sanity check
requires them.

[Experiment settings](docs/benchmark-parameters.md) lists model, solver, env count, warm-up, seed and timing settings; the JSON manifest covers both measured cohorts.

All engines use [pinned upstream dependency links](docs/upstream-dependencies.md) and the common `tools/fetch_sources.py` clone tool. Engine dependencies may live under the project-local, Git-ignored `.runtime/` directory; this is a file-layout choice, not remote computation.

See [the source layout](docs/repository-layout.md) for engine-owned smoke/benchmark code, shared study infrastructure and supported entry points.

For clone-to-benchmark instructions, follow [the reproduction quick start](docs/benchmark-reproduction.md).

Start with [common prerequisites](recipes/README.md), [verification rules](docs/verification.md)
and the relevant engine recipe. Core smokes preserve their reviewed gfx1151
configuration. The separate [MI355X study](study/README.md) provides gfx950 build
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
See [study configuration](configs/benchmark-profile.example.json) and [source/dependency observations](configs/benchmarks/software.json).

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
