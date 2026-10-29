# Published experiment parameters

The [machine-readable manifest](../study/benchmark-parameters.json) records settings from the accepted MI355X measurements: 12 supplied-model/backend paths and 64 environment configurations. The separate 50-record GPU baseline is included under `reference_baseline_settings`; six MJWarp Humanoid configurations overlap, so these counts must not be added.

These are forward simulation and rendering experiments. There is no policy training or optimizer in this campaign, so learning rate, PPO batch size and reward hyperparameters do not apply. The additional GSplat training and WAM inference blog reproductions have not been measured and are not included here.

## Primary measurement settings

| Model / backend | envs | Work per sample | dt / control interval | Warm-up | Adapter |
|---|---|---|---|---|---|
| chrono-dem | 1, 2, 4, 8 | 1 outer advance (400 native substeps) | 0.0010000000474974513 | discarded_full_trials=1 | [code](../study/provided_chrono_replicas.py) |
| chrono-fsi | 1, 2, 4, 8 | 1000 steps/env | 0.0001 | discarded_full_trials=1 | [code](../study/provided_chrono_replicas.py) |
| fluidlab | 1, 2, 4, 8 | 100 steps/env | 0.002 | steps=50 | [code](../study/provided_replicas.py) |
| genesis-sph | 1, 2, 4, 8 | 100 steps/env | 0.01 | steps=50 | [code](../study/provided_replicas.py) |
| genesis-franka | 1, 16, 64, 256, 1024, 2048, 4096, 8192, 16384, 32768, 65536 | 1000 steps/env | 0.01 | steps=100 | [code](../study/provided_genesis_franka.py) |
| gsplat | 1, 2, 4, 8, 16, 32 | 100 frames/camera | not applicable | frames=10 | [code](../study/provided_gsplat_garden.py) |
| incflo | 1, 2, 4, 8 | 50 steps/env | original CFL=0.45, fixed_dt=-1 | discarded_full_trials=1 | [code](../study/provided_incflo.py) |
| instinct | 1, 2, 4, 8, 16, 32 | 100 steps/env | physics 0.002 s; control 0.05 s | control_steps=10 | [code](../study/provided_instinct_libero.py) |
| mujoco-mjx | 2048, 4096, 8192, 16384, 32768, 65536 | 1000 steps/env | 0.005 | full_compiled_rollouts=1 | [code](../study/provided_mjx_humanoid.py) |
| mujoco-mjwarp | 2048, 4096, 8192, 16384, 32768, 65536 | 1000 steps/env | 0.005 | steps=100 | [code](../study/representative_mujoco.py) |
| nekrs | 1, 2, 4, 8 | 100 steps/env | 0.003 | steps=100 | [code](../study/provided_nekrs_windows.py) |
| taichi | 1, 2, 4, 8, 16 | 1000 steps/env | 0.0002 | steps=50 | [code](../study/provided_replicas.py) |

All primary configurations use five samples and synchronized GPU boundaries. Most use reset rollouts; nekRS uses five consecutive trajectory windows after 100 warm steps. Native process replication includes its documented IPC barriers. Build, initialization, validation/readback and rendering are included or excluded as stated per workload in the manifest; Instinct Sim includes GPU cameras/control/observations, while GSplat measures rendering only.

## Physical and execution options

- MuJoCo Humanoid: identical XML SHA-256, dt 0.005 s, Newton solver max 100 iterations, line-search max 50, tolerance 1e-8, FP32, zero controls and supplied initial keyframe. MJWarp allocates nconmax=24 and njmax=64 per world and uses direct HIP without graph capture. MJX uses matched JAX/jaxlib/PJRT/plugin 0.12.0, a JAX scan, one full warm rollout, default compiler options and no XLA_FLAGS override. A 1000-step rollout is distinct from solver iterations.

- Genesis Franka: dt 0.01 s, one substep and the supplied nine-DOF robot. SPH coupling: dt 0.01 s, ten substeps and 216000 particles. Physical geometry/material/solver defaults come from the pinned examples; neither adapter explicitly overrides the upstream initialization seed.

- Chrono FSI-SPH: 16731 particles, dt 0.0001 s and 1000 steps. DEM: 105704 particles and a 1 ms outer horizon, with fixed native dt 2.5e-6 s and 400 internal substeps. This is an initial transient, not a final repose-angle test. Both discard a full process trial before measurement.

- incflo: unmodified 128 by 128 cavity input, 50 steps, CFL 0.45, fixed_dt=-1 (adaptive dt), and a 67108864-byte initial GPU arena per process. Original diagnostics/plot output remain inside the measured native execution scope.

- nekRS: supplied TGV mesh, Re 1600, polynomial order 7, cubature order 9 and dt 0.003 s. Mesh/input hashes and source commit are in the manifest.

- FluidLab: provided MixingEnv version 0, seed 0, 86527 particles, outer dt 0.002 s and ten substeps. Forward/headless execution disables gradients and loss, uses the supplied stationary agent with zero actions, and performs no optimizer step.

- Instinct Sim: LIBERO spatial task 0, first supplied initial state, seed 0, zero seven-dimensional actions, 20 Hz control, 25 physics substeps per control step and 128 by 128 cameras. The supplied OSC/gripper and GPU observation/success pipeline are retained. HP_RENDERER=rt, HP_OBS_LAG=2 and HP_SUCCESS_MODE=robosuite are set in the coordinator.

- Taichi: supplied MPM88, 8192 particles, 128 by 128 grid, dt 0.0002 s, random_seed=0, offline_cache=False and cpu_max_num_threads=1. Physics executes on the AMD GPU; the CPU-thread setting controls host runtime work.

- GSplat: supplied garden fixture, 111785 Gaussians, 648 by 420 pixels, torch seed 0, packed=False, ten warm frames and 100 measured frames per camera. The first camera is cloned for the camera batch, sharing static geometry; no trained checkpoint is used.

## Where the remaining defaults are defined

The manifest enumerates recorded settings and explicit adapter overrides. It does not flatten every internal material, contact, solver, renderer or model default into a new configuration file. Those unchanged values are defined by the pinned upstream source/model files. Follow the recorded source commit, source/model/asset hashes and [software/build observations](../study/software-observations.json), together with the linked adapter. Changing an upstream release while retaining the same command is not the same experiment.

FluidLab upstream source has no explicit root license grant in the pinned snapshot. It is not redistributed or automatically acquired; the source/runtime must be supplied with the rights holder’s permission. Publishing numeric settings does not grant access or redistribution rights to its source/assets. See [LICENSES.md](../LICENSES.md).

The adapter SHA-256 identifies the portable code in this repository, not a byte-for-byte identity claim for the original private execution copy. Published source references use repository paths; server paths, run IDs, raw logs and individual timing history are excluded.

To export settings from your own accepted result bundle, use:

```bash
python study/export_benchmark_parameters.py --data-dir /path/to/results/report \
  --output study/benchmark-parameters.json
```

The exporter checks the cohort sizes for this campaign. It does not infer an unrecorded default or validate a new GPU execution. Follow [the benchmark quick start](benchmark-reproduction.md) for environment setup and measurements.
