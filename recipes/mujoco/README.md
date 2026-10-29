# MuJoCo GPU backends

Use [MJX-JAX on ROCm](mjx/README.md) or [MJWarp on AMD GPUs](mjwarp/README.md).
Each backend has its own environment, source pins and bounded smoke. Native
MuJoCo may be imported only for a short same-scene numerical sanity check;
there is no standalone CPU recipe or CPU throughput entry.

For the supplied Humanoid model and MI355X environment scaling, follow
[the study reproduction guide](../../study/REPRODUCE.md).
