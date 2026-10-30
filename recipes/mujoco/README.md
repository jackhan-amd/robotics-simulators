# MuJoCo GPU backends

## Upstream source connection

This engine follows the [common upstream dependency convention](../../docs/upstream-dependencies.md).
The project tracks its adapters and pinned source declaration; the upstream engine
is a separate Git checkout in configured local runtime storage.

```bash
python3 tools/fetch_sources.py plan --engine mujoco
python3 tools/fetch_sources.py fetch --engine mujoco
```

Source checkout is separate from the GPU runtime build and smoke below. The source
directory is a project dependency; it does not indicate a remote compute service.

Use [MJX-JAX on ROCm](mjx/README.md) or [MJWarp on AMD GPUs](mjwarp/README.md).
Each backend has its own environment, source pins and bounded smoke. Native
MuJoCo may be imported only for a short same-scene numerical sanity check;
there is no standalone CPU recipe or CPU throughput entry.

For the supplied Humanoid model and MI355X environment scaling, follow
[the study reproduction guide](../../study/REPRODUCE.md).
