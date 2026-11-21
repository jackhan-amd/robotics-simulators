# Common prerequisites

Clone pinned engine commits using the [common upstream dependency convention](../docs/upstream-dependencies.md). The default storage directory is the Git-ignored `.runtime/`. Source location and the server performing computation are separate choices.

The baseline platform is Linux x86_64 with Python3.12. C++ builds require CMake, Ninja and a C++ compiler. Install missing tools in a user-owned prefix. These steps leave the host driver and global Python installation untouched.

## Runtime storage and Python

```bash
python3 tools/configure.py --storage-root "$RUNTIME_STORAGE_ROOT" --name simulator
# Example output: source '<runtime storage>/private/environment-simulator.sh'
# Run the command printed by the tool.
```

Provide the `uv` executable and Python3.12. To use an existing Python3.12, set `PYTHON312` to its executable. `UV_PYTHON_INSTALL_DIR`, caches and temporary files use the runtime storage selected by configure.

| Path | Purpose |
|---|---|
| `${STUDY_STORAGE_ROOT}/venvs/<engine>` | Per-engine Python3.12 environments |
| `${STUDY_STORAGE_ROOT}/upstream/<engine>` | Pinned source checkouts |
| `${STUDY_STORAGE_ROOT}/build`, `install` | User-owned builds and installations |
| `${STUDY_PRIVATE_ROOT}/runs` | Actual commands, stdout, stderr and source snapshots |
| `${STUDY_PRIVATE_ROOT}/results/runs` | Per-run JSON results |

```bash
python3 tools/collect_inventory.py --node halo \
  --output "$STUDY_PRIVATE_ROOT/inventory.json"
```

Inventory reads connected GPUs, utilization, memory, disk and toolchain information before execution. Run one GPU test per host at a time. Leave other workloads and services running.

<a id="rocm-runtime"></a>
## ROCm runtime

The reviewed environment included Torch2.14.1+rocm7.14 and SDK7.14.0. The public PyPI and AMD gfx1151 indexes checked did not provide Linux wheels for this exact combination. Dependency locks record the tested packages; they do not guarantee that those wheels remain downloadable.

MuJoCo packages for GPU sanity checks are available from public PyPI. To restore a reviewed GPU Python environment, supply an authorized Python3.12 prefix with the expected versions through the engine recipe's `VERIFIED_*_ENV` variable. Setup creates an independent copy and leaves the base environment unchanged.

```bash
# Example: the reviewed Genesis prefix is stored elsewhere.
export VERIFIED_GENESIS_AMDGPU_ENV="$EXISTING_GENESIS_PY312_PREFIX"
bash recipes/genesis/install.sh
```

If `venvs/<engine>/bin/python` already exists, the installer uses it. Check the backend and numerical results with a bounded scene after copying. This procedure restores an existing runtime; it does not establish a clean-machine installation of the exact GPU wheels from a public index.

C++ builds use the supplied `ROCM_PATH`, or the existing Python SDK prefix when unset. If no SDK is available, provide `VERIFIED_ROCM_BUILD_ENV`.

```bash
# Set the root of an installed HIP SDK.
export ROCM_PATH="$EXISTING_HIP_SDK_ROOT"
"$ROCM_PATH/bin/hipcc" --version
```

For public wheel combinations, follow [AMD TheRock releases](https://github.com/ROCm/TheRock/blob/main/RELEASES.md) and [Python packaging](https://github.com/ROCm/TheRock/blob/main/docs/packaging/python_packaging.md). Validate a bounded scene again whenever the version combination changes.

## Select an AMD device

Use inventory to check the GPU name, ISA and current occupancy. On a multi-GPU host, identify the intended device rather than assuming index 0.

```bash
export CHECKED_AMD_DEVICE="<verified Radeon8060S selector>"
python3 -m simulators smoke genesis-freefall --execute
```

The runner sets `ROCR_VISIBLE_DEVICES` and uses logical HIP device 0 in the child process. Scene code checks the actual 8060S/gfx1151 and requested backend. GUI rendering stays disabled.

## Recipes and results

Engine shell scripts install and build their dependencies; inspect them to see the commands. `recipes/manifest.json` defines execution commands, environment settings and timeouts. Engine-owned smoke files under `recipes/` contain bounded scenes and numerical gates.

A zero process exit code records execution. New results remain `PENDING_VALIDATION`; CPU fallback cannot become GPU PASS. Review the local record after [numerical and backend checks](../docs/verification.md). Individual run records and generated HTML are excluded from Git.
