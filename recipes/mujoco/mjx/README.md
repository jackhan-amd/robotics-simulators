# MuJoCo MJX-JAX ROCm

This ROCm path runs MuJoCo scenes through MJX-JAX. The earlier reviewed stack used JAX/JAXlib0.12.0 and ROCm plugin/PJRT0.11.2, pinned in the [dependency list](../../../configs/mujoco-mjx-rocm-py312.lock.txt).

## Prepare the environment

Follow the [common ROCm runtime prerequisites](../../README.md#rocm-runtime). Use the separate `venvs/mujoco-mjx-rocm` environment and keep it isolated from Genesis/Torch.

```bash
export VERIFIED_MUJOCO_MJX_ROCM_ENV="$EXISTING_MJX_PY312_PREFIX"
bash recipes/mujoco/mjx/install.sh
```

Use the loader libraries from the recorded environment. The execution manifest selects `compat/rocm7.14` and the existing SDK library paths. The Genesis/SDK prefix providing those libraries is part of the common runtime prerequisites.

## Configure and run

The runner sets `JAX_PLATFORMS=rocm`, `XLA_PYTHON_CLIENT_PREALLOCATE=false` and the verified AMD selector.

```bash
python3 -m simulators show mujoco-mjx-rocm
python3 -m simulators smoke mujoco-mjx-rocm --execute
```

Check finite state, gravity reference and contact gates in the free-fall/contact scene. Confirm that JAX selects a ROCm GPU; classify CPU execution as a CPU reference result. Separate JIT preparation in a new process from actual stepping.

Official references: [MJX](https://mujoco.readthedocs.io/en/stable/mjx.html), [ROCm JAX](https://rocm.docs.amd.com/projects/jax/en/latest/). Apache-2.0.
