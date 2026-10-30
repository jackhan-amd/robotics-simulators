# Taichi Lang on MI355X

## Upstream source connection

This engine follows the [common upstream dependency convention](../../docs/upstream-dependencies.md).
The project tracks its adapters and pinned source declaration; the upstream engine
is a separate Git checkout in configured local runtime storage.

```bash
python3 tools/fetch_sources.py plan --engine taichi
python3 tools/fetch_sources.py fetch --engine taichi
```

Source checkout is separate from the GPU runtime build and smoke below. The source
directory is a project dependency; it does not indicate a remote compute service.

Use the official AMD Taichi 1.8.0b2 Python 3.12 payload. `recipes/taichi/benchmarks/docker_extract_taichi.py` extracts the documented image without a Docker daemon. Provide `venvs/taichi`, `ROCM_PATH` and the payload under `official-taichi/root`. The wrapper selects the supplied MPM88 example and explicit AMD backend.

See [common configuration](../README.md), [MI355X quick start](../../docs/benchmark-reproduction.md)
and [recorded software and commands](../../docs/benchmark-recipes.md). Runtime sources,
environments and assets stay in external `STUDY_STORAGE_ROOT`.

```bash
python3 -m simulators smoke taichi-provided-gpu
python3 -m simulators smoke taichi-provided-gpu --execute
```

Execution requires Linux, one available MI355X GPU and the prepared engine runtime.
The command is bounded to 900 seconds and uses the provided example adapter with
GPU backend checks. Review its numerical/image checks and device evidence;
process exit alone does not establish validity. GSplat validates rendering only.
This new catalog entry is unreviewed as a catalog workflow; prior MI355X supplied
example measurements are documented separately and are not re-certified here.

Original licenses and notices are listed in [LICENSES.md](../../LICENSES.md).
