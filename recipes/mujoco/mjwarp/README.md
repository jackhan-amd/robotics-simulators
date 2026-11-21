# MuJoCo Warp: public AMD port

Build the public AMD Warp and MuJoCo Warp sources for HIP/gfx1151. This is an AMD port of the NVIDIA Warp stack, not a vendor-neutral HIP solver. Keep its environment separate from native MuJoCo CPU and MJX-JAX.

| Source | Pinned commit |
|---|---|
| [AMD-Ecosystem/warp](https://github.com/AMD-Ecosystem/warp) | `2e2673bb7b90eaabb9cb89dc1f55a76f61c13aab` |
| [AMD-Ecosystem/mujoco_warp](https://github.com/AMD-Ecosystem/mujoco_warp) | `9dfdf7ab8d5a996fe143e9e2c1e5da646c6fc14f` |

## Install and build

Provide the Python3.12 runtime and HIP SDK from the [common prerequisites](../../README.md#rocm-runtime). Create an independent copy of the dependency prefix, then build the pinned sources.

```bash
export VERIFIED_MJWARP_ROCM_ENV="$EXISTING_MJWARP_PY312_PREFIX"
# Also provide ROCM_PATH or VERIFIED_ROCM_BUILD_ENV.
bash recipes/mujoco/mjwarp/build.sh
```

The Warp build uses `--hip-arch=gfx1151 --jobs=2 --no-use-libmathdx` with a 300-second build limit. It installs into the dedicated venv and leaves the original dependency prefix unchanged.

## Configure and run

The execution manifest sets `HIPRTC_COMPILE_OPTIONS_APPEND` with unsigned fixed-width integer type macros and `-mprintf-kind=buffered`. The source solver is unchanged.

```bash
python3 -m simulators show mujoco-mjwarp-rocm
python3 -m simulators smoke mujoco-mjwarp-rocm --execute
```

Check actual stepping, contact, finite state and gravity conditions in the bounded rigid-body scene. The wrapper records HIP runtime and selected-device provenance in the raw log. Check `backend_observed` together with the physics gates.

Official recipe: [AMD sim-to-real recipe](https://rocm.blogs.amd.com/artificial-intelligence/sim2real-rl-instinct/README.html). Retain Apache-2.0 and dependency-specific notices.
