# Execution verification

After installation and source builds, run the bounded scene in each recipe. Check the observed backend, numerical results and device in `SMOKE_RESULT_JSON`. A zero child exit code alone does not establish G1 validity for a new run.

| Stage | Checks |
|---|---|
| Installation and build | Python3.12, pinned sources and dependencies, compiler settings, generated binaries |
| Backend | Actual CPU/HIP/AMD solver selection and GPU name/ISA |
| Physics | Finite state, dt, steps and scene-specific gravity, contact, mass or field gates |
| CPU comparison | Same scene, scale and dt, using the declared tolerances |
| GPU execution | Physics kernel profiler/trace and actual numerical steps |

Keep GPU rendering and policy inference outside these headless scenes. Mark native CPU runs as `CPU_ONLY`. A requested GPU run that falls back to CPU cannot receive GPU PASS. Performance validation, G2, is a separate task.

## Retained verification scope

The 3 catalog entries for Instinct Sim, Taichi and GSplat are marked `UNREVIEWED_CATALOG_ENTRY`. Earlier MI355X benchmark measurements do not validate a new catalog execution.

[verification-summary.json](../configs/verification-summary.json) retains the scope of the 13 included GPU configurations reviewed through 2026-10-23. It records engine, scene, backend and numerical gates, excluding throughput, individual run IDs, journals and raw logs. It does not automatically validate a new installation or run.

New run JSON is stored at `${STUDY_PRIVATE_ROOT}/results/runs/<node>/<id>/result.json`; actual commands, raw logs and source snapshots go under `${STUDY_PRIVATE_ROOT}/runs/<node>/<id>/`. Results remain `PENDING_VALIDATION` until reviewed. Keep raw evidence out of Git.

Historical CUDA records and current ROCm recipes may use different implementations or settings. Entries without `cuda_reference_status` make no CUDA execution claim. Earlier RTX3090 comparisons remain in the local research archive.
