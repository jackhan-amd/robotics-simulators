# Genesis World: rigid and fluid simulation

## Upstream source connection

This engine follows the [common upstream dependency convention](../../docs/upstream-dependencies.md).
The project tracks its adapters and pinned source declaration; the upstream engine
is a separate Git checkout in configured local runtime storage.

```bash
python3 tools/fetch_sources.py plan --engine genesis
python3 tools/fetch_sources.py fetch --engine genesis
```

Source checkout is separate from the GPU runtime build and smoke below. The source
directory is a project dependency; it does not indicate a remote compute service.

Use explicit `gs.amdgpu` selection for rigid bodies, articulation, contact, SPH, MPM and fixed-rigid SPH boundaries. Keep the viewer and renderer disabled.

The pinned [Genesis World](https://github.com/Genesis-Embodied-AI/genesis-world) source is `90d55545c193082a8e32f9b1b6b7732f14d89be8`. The recorded Python stack is Genesis1.4.4, Quadrants1.3.3 and Torch2.14.1+rocm7.14. See the [ROCm lock](../../configs/genesis-rocm-py312.lock.txt) for the full list.

## Install

Prepare the Python3.12 prefix described in the [common runtime prerequisites](../README.md#rocm-runtime). The script prepares `venvs/genesis-amdgpu`, checks out pinned sources and creates loader aliases in user storage.

```bash
export VERIFIED_GENESIS_AMDGPU_ENV="$EXISTING_GENESIS_PY312_PREFIX"
bash recipes/genesis/install.sh
```

For a current installation on a clean machine, follow the [official installation guide](https://genesis-world.readthedocs.io/en/latest/user_guide/overview/installation.html). Validate that combination with a bounded scene separately from restoring the exact runtime above.

## Scenes and settings

| Recipe ID | Scene | Required settings |
|---|---|---|
| `genesis-freefall` | Sphere free fall and contact, 50 steps | explicit AMD backend |
| `genesis-articulation` | Articulated rigid body, 50 steps | explicit AMD backend |
| `genesis-contact` | Rigid-body contact, 50 steps | `GS_ENABLE_ZEROCOPY=0`, monolithic contact solve |
| `genesis-sph` | Small SPH scene, 50 steps | `GS_ENABLE_ZEROCOPY=0`, `--mass-readout static_info` |
| `genesis-mpm` | Small MPM scene, 50 steps | explicit AMD backend |
| `genesis-coupling` | SPH + fixed rigid boundary, 50step | `GS_ENABLE_ZEROCOPY=0`, `--mass-readout static_info` |

The contact path uses `QD_PERFDISPATCH_FORCE=func_solve_body:func_solve_body_monolith`. SPH readout uses `static_info` from the pinned source. No solver/runtime patch is installed. Each scene records particle count, cell size, dt and substeps in its raw JSON marker.

## Run

```bash
python3 -m simulators smoke genesis-freefall --execute
python3 -m simulators smoke genesis-articulation --execute
python3 -m simulators smoke genesis-contact --execute
python3 -m simulators smoke genesis-sph --execute
python3 -m simulators smoke genesis-mpm --execute
python3 -m simulators smoke genesis-coupling --execute
```

Run one job at a time. The manifest applies settings to the child process. Inspect the actual command and environment with `python3 -m simulators show genesis-contact`.

Check `quadrants_arch=Arch.amdgpu`, the actual 8060S/gfx1151, profiled physics kernels and each scene's numerical gates. Rigid checks cover free fall, articulation and contact. Fluid checks cover particle count, mass, domain bounds, finite state and CPU comparison. The coupling scene uses a fixed rigid boundary.

Apache-2.0. Retain the [original notice](../../third_party_notices/genesis-world/LICENSE).
