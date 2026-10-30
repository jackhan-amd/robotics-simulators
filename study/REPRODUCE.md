# MI355X simulator study: reproduction

This directory contains the local study harness. Measured results, package freezes, patches, source pins and raw logs are under `../report/evidence/`. Results apply to the bounded scenes in this harness; they do not establish full robot training performance or application certification.

## Recorded target and source

- Target: one AMD Instinct MI355X, gfx950, 288 GiB VRAM; AMD EPYC 9575F host.
- Ubuntu 24.04.5; Python 3.12.3 for the GPU simulation environments.
- Base PyTorch: 2.14.0+rocm10.1.0; `torch.version.hip`: 7.16.26385. SDK packaging version and HIP runtime version are recorded separately.
- Integration repository: `haanjack/robotics-sim-lab`, commit `d1adb4a0cd5f55ce80443e642092190de9d12f6e`.
- Engine source commits: `../report/evidence/results/software-sources-and-builds.json`.
- Package freezes: `../report/evidence/results/software-*.txt`. Conda environments include explicit package URLs. A pip freeze containing a local source path is paired with the source commit above; it is not a portable wheel lock by itself.

The target was supplied as a container with ROCm SDK and Torch already installed. These were retained. `module` and a Docker daemon were unavailable. Reproduction requires the recorded base SDK/Torch and isolated environments built from the source pins and package receipts. Use the successful execution profile for each engine. Diagnostic scripts are retained as source for investigation; they are not a setup sequence.

## Paths and common environment

On the existing study target:

```bash
ssh -o StrictHostKeyChecking=no -p ${STUDY_SSH_PORT} ${STUDY_SSH_TARGET}
source ${LAB_ROOT}/env.sh
export PATH="$STUDY_STORAGE_ROOT/tools/bin:$PATH"
export LD_LIBRARY_PATH="$ROCM_PATH/lib:$ROCM_PATH/lib/llvm/lib"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
cd "$STUDY_WORKTREE"
```

Configure locations through `study/workspace.py` using the ignored private profile or environment variables described in [README.md](README.md). The measured deployment copied the selected `study/` adapters into `${LAB_ROOT}/` and extracted the integration repository into its `repo/` subdirectory. Runtime sources, builds and environments stay in configured runtime storage. `study/runtime/run_remote.py` checks the target architecture and serializes jobs with a shared lock. Use `--wait` when another study job holds the lock. Inspect GPU processes before starting a run.

The wrapper writes `<UTC>-<case>-<suffix>.json` and `.log` into the remote `evidence/` directory. Keep these together. Use the case's successful JSON command, selected environment and parent capture receipt to reproduce that measurement. GPU APIs may call the HIP device `cuda:0`; the smoke separately checks the actual AMD name, architecture and HIP runtime.

## MuJoCo

The engine sections reproduce the earlier GPU baselines. **Supplied-example env scaling** contains the primary workloads and current run commands. Keep these measurement scopes separate.

CPU execution is retained only for same-scene GPU sanity checks. CPU throughput is excluded from this campaign and is not a simulator performance result.

MJX uses the isolated ROCm 7.14.1 runtime in `mujoco-mjx-rocm`. The base SDK 10 library set could not satisfy this PJRT build's SMI ABI. The loader preparation is part of the integration repository:

```bash
python3 tools/prepare_rocm_loader.py \
  --runtime-venv "$STUDY_STORAGE_ROOT/venvs/mujoco-mjx-rocm" \
  --output-dir "$STUDY_STORAGE_ROOT/compat/mjx714"
source "$STUDY_STORAGE_ROOT/compat/mjx714/loader.env"
export XLA_PYTHON_CLIENT_PREALLOCATE=false
python3 "$LAB_ROOT/sweep_mujoco.py" mjx
```

The effective loader is also in `evidence/results/mjx-loader.env`. MJX uses JAX 0.12.0, jaxlib 0.12.0, ROCm PJRT/plugin 0.11.2 and MuJoCo/MJX 3.16.0. It compiles a 1000-step JAX scan returning only the final state, warms one full rollout, then times five reset rollouts with `block_until_ready` before readback.

MJWarp uses MuJoCo 3.8.1, AMD Warp commit `2e2673bb7b90eaabb9cb89dc1f55a76f61c13aab` and AMD mujoco_warp commit `9dfdf7ab8d5a996fe143e9e2c1e5da646c6fc14f`. `install_gpu.py warp` records the native gfx950 build with eight jobs. Restore the common SDK environment before running it:

```bash
source "$LAB_ROOT/env.sh"
export LD_LIBRARY_PATH="$ROCM_PATH/lib:$ROCM_PATH/lib/llvm/lib"
export STUDY_WARP_CACHE=${WARP_CACHE_ROOT}
python3 "$LAB_ROOT/sweep_mujoco.py" mjwarp
python3 "$LAB_ROOT/representative_suite.py"
```

The `/home` filesystem rejected colon characters in gfx950 cache filenames; `/tmp` was used for Warp's cache. No typedef/HIPRTC macro workaround was required by the successful configuration. Graph capture failed with `Cannot synchronize stream while graph capture active`; all published MJWarp throughput is direct HIP execution, including synchronization inside this port's step implementation. The sphere warms 500 steps; the Humanoid warms 100 steps after a separate 20-step CPU parity probe. Both time 1000 steps × 5, synchronize at rollout boundaries and perform validation readback after the timer.

`representative_mujoco.py` loads the pinned upstream `benchmarks/humanoid/humanoid.xml`, SHA256 `9b29ea10152748e66a0a77f7651efbbb8282fef9621e7cb8d220ca157c41e61a`. It resets keyframe 0 for every repetition. Zero controls, no trained policy, nv=27, nu=21, nbody=17, ngeom=20, dt=0.005 s, Newton solver, max iterations=100, line-search max=50, tolerance=1e-8, FP32, 24 contacts/world and 64 constraints/world. `qualify_humanoid.py` separately instruments contact activity and buffer headroom; it is not a throughput run. Requested env counts are 2048, 4096, 8192, 16384, 32768 and 65536.

## Genesis

Genesis 1.4.4 source is pinned in the source receipt; Quadrants is 1.3.3. A software EGL context was required for headless initialization. Rendering is absent from the measured loop. The successful environment is:

```bash
export PYGLET_HEADLESS=1 PYOPENGL_PLATFORM=egl EGL_PLATFORM=surfaceless
export LIBGL_ALWAYS_SOFTWARE=1 MESA_LOADER_DRIVER_OVERRIDE=llvmpipe
export LIBGL_DRIVERS_PATH="$STUDY_STORAGE_ROOT/tools/lib/dri"
export __EGL_VENDOR_LIBRARY_FILENAMES="$STUDY_STORAGE_ROOT/tools/share/glvnd/egl_vendor.d/50_mesa.json"
export LD_LIBRARY_PATH="$ROCM_PATH/lib:$ROCM_PATH/lib/llvm/lib:$STUDY_STORAGE_ROOT/tools/lib"
python3 "$LAB_ROOT/genesis_suite.py"
```

The original contact recipe's monolithic setting was also checked separately with `GS_ENABLE_ZEROCOPY=0` and `QD_PERFDISPATCH_FORCE=func_solve_body:func_solve_body_monolith`; see `genesis-contact-monolith-smoke`. The throughput series uses the normal dispatch in `bench_genesis.py` and `bench_genesis_fluid.py`. Rigid envs: 1, 64, 256, 1024; SPH/MPM particle counts: 27, 1000, 8000. The fluid scene is a suspended cube, not a developed dam-break. `performance_suite.py` and `more_performance.py` preserve the successful launch environments and series.

## Chrono, incflo and nekRS

These native builds target gfx950. Compiler paths/options are preserved in `software-sources-and-builds.json`. `build_engine.py`, `native_bench.py`, `prepare_incflo.py` and `nekrs_case.py` contain the study build/case preparation. Read the matching capture logs for the successful CMake generator and user toolchain configuration.

```bash
export LD_LIBRARY_PATH="$ROCM_PATH/lib:$ROCM_PATH/lib/llvm/lib:$STUDY_STORAGE_ROOT/build/chrono-hip-devel/lib"
python3 "$LAB_ROOT/native_bench.py" chrono-fsi
python3 "$LAB_ROOT/native_bench.py" chrono-dem
python3 "$LAB_ROOT/bench_incflo.py" --cells 256
python3 "$LAB_ROOT/bench_nekrs.py"
```

Chrono FSI and DEM use 27 particles; per-step synchronization and numerical readbacks are included in timing. FSI times 990 steps after ten warm steps; DEM times 240 after ten. DEM uses cm/g/s.

The original incflo cavity input was absent. `prepare_incflo.py` restores the pinned upstream lid-driven cavity input. The study builds 2D HIP without MPI/OpenMP/EB, measures 64²/128²/256² grids with dt=0.0001 s, 100 steps × 5, discards the first complete process and uses the native Evolve timer. InitData is excluded and final plot output is included.

nekRS uses one MPI rank, HIP, Ethier, 32 elements, polynomial order 5 and dt=0.002 s. It discards the first complete process; subsequent runs each discard ten steps before timing 100 using native `elapsedStep`. Cold JIT preparation is recorded separately. `nekrs_case.py` sets user OpenMPI's `pml=ob1`, `btl=self,tcp` after UCX warnings; it does not configure RoCE or measure multi-node communication.

## Taichi and FluidLab

AMD's official b2 payload was extracted with `docker_extract_taichi.py` from `rocm/taichi:taichi-1.8.0b2_rocm7.0.0_ubuntu24.04_py3.12.3`; no Docker daemon was needed. The release announces Taichi 1.8.0, LLVM 20.1.8, commit 104dc18b.

```bash
export PYTHONPATH="$STUDY_STORAGE_ROOT/official-taichi/root${PYTHON_SITE_PACKAGES}"
export PATH="$ROCM_PATH/lib/llvm/bin:$PATH"
export LD_LIBRARY_PATH="$ROCM_PATH/lib:$ROCM_PATH/lib/llvm/lib:$STUDY_STORAGE_ROOT/tools/lib"
"$STUDY_STORAGE_ROOT/venvs/taichi/bin/python" "$LAB_ROOT/bench_taichi.py" --particles 1048576
"$STUDY_STORAGE_ROOT/venvs/taichi/bin/python" "$LAB_ROOT/bench_fluidlab.py" --edge 20
```

Taichi measures independent gravity particles without interactions. FluidLab measures forward MPM only, grid 16³, dt=0.0002 s, particle counts 27/1000/8000, 100 substeps × 5. `patch_fluidlab.py` adapts old struct initialization and static None checks in a separate source copy. Its patch and receipt preserve the change; solver mathematics is retained. Upstream FluidLab has no explicit license in the checked snapshot. Its source payload is excluded from the report bundle.

## Instinct Sim backend from Faster Action Models

The Instinct Sim backend is `simulate/` in `AMD-AGI/faster-action-models`, commit `a5fa73101988870e51f04fe1e7be5da56dda3841`. It targets gfx950 and reads MJCF. The public evaluation uses it behind LIBERO/RoboCasa. This study checks the independent physics API; policy inference, the OSC controller and camera rendering are outside this measurement.

```bash
# After cloning the pinned repository into storage/upstream/faster-action-models:
"$LAB_ROOT/bin/uv" venv --system-site-packages --python /usr/bin/python3 "$STUDY_STORAGE_ROOT/venvs/instinct-sim"
"$LAB_ROOT/bin/uv" pip install --python "$STUDY_STORAGE_ROOT/venvs/instinct-sim/bin/python" pybind11 mujoco==3.3.2 numpy
cd "$STUDY_STORAGE_ROOT/upstream/faster-action-models"
export PYTHON="$STUDY_STORAGE_ROOT/venvs/instinct-sim/bin/python"
export HIP_ARCH=gfx950 JOBS=8 HIPCXX="$ROCM_PATH/lib/llvm/bin/clang++"
bash simulate/build.sh libero "$STUDY_STORAGE_ROOT/build/instinct-sim-libero"
export PYTHONPATH="$STUDY_STORAGE_ROOT/build/instinct-sim-libero/python"
export LD_LIBRARY_PATH="$STUDY_STORAGE_ROOT/build/instinct-sim-libero:$ROCM_PATH/lib:$ROCM_PATH/lib/llvm/lib"
python3 "$LAB_ROOT/instinct_suite.py"
```

The CMake project version is 0.1.0. The LIBERO preset uses `HP_BOXBOX_DIST_SCALE=1`, `MJCCD_MAX_ITERATIONS=50` and `MJC_FAN_LDS_STATUS=0`. Native build time was about 100.90 s. The current SDK 10.1.0 build differs from the official article's ROCm 7.14 environment. The source solver was not patched. Package versions and native CMake settings are in the software receipts.

`bench_instinct.py` uses the repository sphere/plane, dt=0.001 s, Newton max iterations=100, tolerance=1e-8. It checks 500 smoke steps, including the first 50 against CPU MuJoCo 3.3.2, then measures the requested six env sizes with 1000 warm steps and 1000 measured steps × 5. Timing covers native C++ `step_n` and boundary stream synchronization; readback follows the timer. qpos readback is float64, while parsed dt/gravity show float32 representation. Gravity-parameter comparisons use tolerance 1e-6 to allow that representation; the physical gates remain unchanged. In this harness the JSON `build_s` / `compile_s` fields describe engine initialization, not native CMake compilation.

## GSplat

GSplat is a rendering workload. AMD's documented GPU list names MI300X/MI325X; this MI355X trial is exploratory. The successful source is official tag v1.5.3b2, commit `ff8bc5489545bcc1b5a2b997d975834429a0d7af`. `patch_gsplat_allocator.py` adapts the removed allocator alias to PyTorch 2.14 using `c10::GetAllocator(c10::DeviceType::CUDA)` without changing rasterization equations. The patch receipt is preserved.

```bash
export LD_LIBRARY_PATH="$ROCM_PATH/lib:$ROCM_PATH/lib/llvm/lib"
"$STUDY_STORAGE_ROOT/venvs/gsplat/bin/python" "$LAB_ROOT/bench_gsplat.py" --smoke
"$STUDY_STORAGE_ROOT/venvs/gsplat/bin/python" "$LAB_ROOT/bench_gsplat.py" --gaussians 100000 --width 1280 --height 720
```

Measurements use a synthetic cloud, forward only, packed=False, ten warm frames then 100 frames × 5 with GPU synchronization. Each repetition is only tens of milliseconds; use longer trials and a real trained scene before estimating production rendering performance. `gsplat-synthetic.png` is an image from the actual smoke.

## Evaluation scope


## Supplied-example env scaling

Use only supplied upstream examples and models. Keep physical geometry, materials, resolution, solver and native controller settings. The adapters add headless execution, replication, reset/synchronization, bounded horizons and measurement. Source paths, hashes, changes and timing scopes are retained in the JSON results. A failed smoke must be resolved before its performance sweep is accepted.

From the existing server workspace, source `env.sh` and run the relevant coordinator (each uses the common GPU lock):

```bash
python3 ${LAB_ROOT}/representative_suite.py
PROVIDED_MJX_ALIGNED=1 python3 ${LAB_ROOT}/provided_mjx_suite.py
python3 ${LAB_ROOT}/provided_scaling_suite.py
PROVIDED_ENGINE=genesis-sph python3 ${LAB_ROOT}/provided_replicas_suite.py
python3 ${LAB_ROOT}/provided_chrono_suite.py
PROVIDED_CFD_ENGINE=incflo python3 ${LAB_ROOT}/provided_cfd_suite.py
PROVIDED_CFD_ENGINE=nekrs PROVIDED_CFD_WINDOWS=1 python3 ${LAB_ROOT}/provided_cfd_suite.py
PROVIDED_ENGINE=fluidlab python3 ${LAB_ROOT}/provided_replicas_suite.py
python3 ${LAB_ROOT}/provided_instinct_suite.py
PROVIDED_ENGINE=taichi python3 ${LAB_ROOT}/provided_replicas_suite.py
python3 ${LAB_ROOT}/provided_gsplat_suite.py
```

MuJoCo keeps 1000 measured steps and the requested 2048–65536 envs. Genesis uses the supplied Franka and SPH–rigid coupling examples. Chrono uses the full supplied DamBreak and repose models, with bounded horizons; DEM's 105704-particle 1 ms window is an initial-transient measurement (400 native substeps), not validation of the final repose angle. Its upstream 100-byte filename buffers overflowed under the long study path; the instrumented copy uses bounded path formatting. The original physics source remains untouched.

The incflo input is the unmodified 128² cavity with CFL 0.45 and 50 steps. Only the AMReX initial GPU arena allocation is limited to 64 MiB per process so independent replicas do not each reserve most of VRAM. Native initialization is excluded by a barrier; original diagnostics and plot output are included. nekRS uses the supplied TGV mesh, p7/cubature9, Re1600 and dt0.003. Its windowed measurement warms 100 steps and records five consecutive 100-step trajectory windows, explicitly not independently reset repetitions. Initialization/JIT and the warm segment are outside its timer; original diagnostics remain inside.

FluidLab uses the provided MixingEnv in forward, headless mode with a stationary supplied agent and no optimizer; scene physics is retained. Only forward simulation was measured. Gradient/backward computation, learning and optimization paths were not tested. The engine executes on the same MI355X GPU server; separate local source/runtime directories do not mean remote computation. Instinct Sim uses AMD's supplied HipLiberoVectorEnv with the pinned LIBERO spatial task, GPU physics/OSC/camera observations and zero actions; its end-to-end env.step metric includes observation and success-check overhead. Taichi uses the provided MPM88 kernels and settings. GSplat uses test_garden.npz and its supplied helper; replicated cameras share geometry and the helper's initialized Gaussians, not a trained checkpoint.

Final accepted measurements are in `report/env-scaling-data.json` and CSV, separate from the earlier GPU baseline. The campaign matrix tracks requested configurations. Diagnostic history stays private. Accepted receipts retain executed-source hashes and portable-source hashes; machine paths were replaced with configuration for publication, so those file bytes can differ. The delivered code archive identifies the portable source used for reproduction.

The final MJX Humanoid sweep uses matched JAX/jaxlib/ROCm PJRT/plugin 0.12.0 and an isolated ROCm 7.14.1 loader. The selected `jax0120-default` profile leaves XLA_FLAGS unset and preserves the supplied physical settings. All six requested environment sizes passed five measured rollouts. A separate check compares every batched world's qpos/qvel after 20 steps with the same model's CPU reference. This is a short-horizon sanity check; CPU throughput and long-horizon accuracy are outside its scope. Earlier diagnostics stay private, and the report links only to accepted final executions.

Chrono and incflo native replicas signal completion and wait for a common validation/finalization release. The parent stops the timer after every replica is done, then permits GPU readback or teardown. Earlier timings without `validation_barrier=true` are provisional history and excluded from the primary supplied-example results. nekRS similarly waits at the final trajectory-window completion gate before any process exits; this avoids interpreting an early normal exit as a failed measurement barrier.

## Collect and rebuild

On Windows, `capture.py` retains exact SSH launch commands and `collect.py` imports the remote evidence archive after checking extraction paths. Run `python -X utf8 study/run.py refresh_gpu_report.py --collect` from the local repository root to refresh the GPU report, campaign status, plots and arithmetic audits. Review the prose again after a content refresh. `benchmark-data.json` contains the earlier GPU baseline, while `env-scaling-data.json` contains the final accepted supplied-example measurements. Use the registered refresh command for current reports; old one-off report generators have been removed from the source tree. The offline rebuild commands in [README.md](README.md) use the delivered evidence without collecting private history.

The report uses actual simulation replay captures in `images/actual-provenance.json` and the actual GSplat smoke image. Replay captures are separate from performance timing. Source code and third-party assets retain their original licenses; the report does not grant additional redistribution rights.
