# MI355X simulator measurements

See [the common upstream dependency convention](../docs/upstream-dependencies.md) for every engine’s source URL, commit and clone command.

Engine-specific benchmark adapters now live in `recipes/<engine>/benchmarks/`. This directory contains shared runtime, coordination, capture and reporting code for the MI355X study. The core simulator catalog remains in `recipes/` and `simulators/`; this study adds supplied-example throughput and environment scaling measurements.

The physics study covers MuJoCo MJX/MJWarp, Genesis, Chrono HIP, incflo HIP, nekRS HIP, FluidLab HIP, Instinct Sim and Taichi AMD. GSplat is a separate rendering workload. CPU execution provides short, same-scene sanity references for GPU results. It is excluded from performance totals.

## Configure configured runtime storage

Copy `configs/benchmark-profile.example.json` to the ignored `private/study-profile.json`, or set the corresponding environment variables. Supply your SSH alias, runtime workspace, storage and ROCm paths. Keep credentials, runtime environments, upstream checkouts, caches and raw execution history outside version control.

`study/workspace.py` resolves configuration for the Windows client and Linux target. `LAB_ROOT` names the runtime workspace. `STUDY_STORAGE_ROOT` holds dependencies. `STUDY_WORKTREE` identifies a checkout or extracted repository on the target. Set `STUDY_PROFILE` to use a different private profile.

The [source layout](../docs/repository-layout.md) separates engine adapters from shared infrastructure. Run local commands through `python study/run.py <script.py>`. The bootstrap deploys registered commands with stable basenames and the repository at `repo/`; do not copy arbitrary source directories by hand.

## Run a bounded measurement

Read the engine recipe, `docs/verification.md` and [REPRODUCE.md](REPRODUCE.md). Prepare the pinned engine environment and inspect current device activity. `study/runtime/run_remote.py` serializes GPU work using a shared lock. Run one GPU job at a time; leave other services and the global driver/Python configuration unchanged.

The `provided_*_suite.py` coordinators select supplied upstream models, perform a smoke check and then measure environment scaling. Native process replicas use a shared validation barrier. Each accepted configuration records five synchronized timing samples. Do not compare throughput across different scene types as if they were equivalent workloads.

The final MJX Humanoid profile uses matched JAX/jaxlib/PJRT/plugin 0.12.0 and the isolated ROCm loader described in REPRODUCE.md. `configs/benchmarks/mjx-profile.json` selects `jax0120-default`; `recipes/mujoco/benchmarks/provided_mjx_suite.py` uses the default compiler options with no XLA_FLAGS override. The supplied physical settings remain unchanged.

[prepare_mjx_aligned.py](../recipes/mujoco/benchmarks/prepare_mjx_aligned.py) creates that environment in fresh external prefixes and refuses to modify an existing measured environment. software-observations.json (local output: `report/evidence/software-observations.json`) records observed package versions, source commits and build settings. Use [env.example.sh](runtime/env.example.sh) as the common environment template.

`study/runtime/launch_remote.py` starts a persistent coordinator through the configured SSH connection. Use `--help` for its script, label and environment arguments. The target writes raw receipts and logs into external evidence storage. `study/runtime/collect.py` imports them into the ignored local `report/` directory.

## Build and review reports

Use Python 3.12 for repository checks. Install the reporting dependencies from `study/reporting/requirements.txt` in a separate environment.

```bash
python study/run.py refresh_gpu_report.py --collect
```

The refresh validates measurements, updates the campaign matrix, generates plots and exports only the selected successful execution logs to `report/evidence/final/`. Raw diagnostics remain in private evidence. `study/reporting/publication.py` replaces machine-specific paths with configuration names or repository source paths. Review the final artifacts for disclosures before distribution.

After factual updates, apply `humanize-korean` to Korean prose and `humanizer` to English prose. Preserve numerical data, source pins, commands, tables and link targets. Do not regenerate the Markdown after prose review without checking the new output again.

The HTML report retains separate simulator tabs and groups rigid, fluid, multiphysics, framework and rendering workloads. Replay captions identify the upstream source file and this repository's capture adapter. Render/capture time is excluded where stated in each measurement scope.

## Publication boundaries

Commit reusable code, configuration templates and aggregate measurements after review. Do not commit private profiles, SSH transcripts, individual execution histories, virtual environments, upstream payloads or generated contextual patches. Third-party source and assets retain their original license terms; see `LICENSES.md`. The repository MIT license does not grant rights to those payloads.

The local report and source archives are review artifacts. Generating them does not publish or push this repository.

## Rebuild a delivered report offline

Extract the customer results ZIP, then extract its reproduction-code ZIP into the same directory. After installing the reporting dependencies, run these commands from that directory:

```bash
python study/run.py render_final.py --data-dir report --plan report/test-plan.json
python study/run.py audit_gpu_measurements.py --data-dir report --accepted-evidence
python study/run.py audit_artifacts.py --data-dir report --plan report/test-plan.json
```

These commands use the delivered aggregate data, accepted receipts and saved images. They require no SSH connection, private profile or GPU. Raw diagnostic history stays outside the delivery.

Generated HTML, report Markdown, measured-parameter exports, software observations and review records belong only under the Git-ignored `report/` directory. Git retains source pins, execution configuration, scripts and maintained instructions. Customer reports embed per-engine execution guidance and omit document-authoring workflow records.
