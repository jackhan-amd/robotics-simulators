# Source layout and supported commands

Engine installation, smoke scenes and numerical benchmark adapters are kept
together. The tools directory contains shared execution infrastructure and the
current report workflow.

| Location | Responsibility |
|---|---|
| recipes/<engine>/ | Installation/build instructions and bounded smoke implementations |
| recipes/<engine>/benchmarks/ | Supplied-model and reference benchmark adapters, setup and validation helpers |
| recipes/_shared/ | Shared smoke backend compatibility and library-map inspection |
| tools/runtime/ | Workspace preparation, flat deployment, recording, launch and collection |
| tools/benchmarks/ | Coordinators/helpers shared by several engines |
| tools/capture/ | Cross-engine field/replay capture, outside timed performance |
| tools/reporting/ | Current report generation, evidence audits, packaging and optional prose-review tools |
| configs/benchmarks/ | Maintained test configuration, source provenance and selected MJX compiler profile |
| docs/benchmark-tools.md and docs/benchmark-recipes.md | Common setup and engine reproduction instructions |
| tools/run.py and tools/scripts.json | Explicit local command launcher and source-file registry |

The old root smokes directory has been absorbed into recipes. Its implementations
were relocated, not duplicated. Source paths in recipe commands, CMake builds,
license exceptions, tests and parameter fingerprints follow the new layout.

## Run from a checkout

~~~bash
python3 -m simulators smoke mujoco-mjx-rocm      # bounded-smoke command preview
python3 tools/run.py --list                     # registered source files
python3 tools/run.py bootstrap.py               # requires configured runtime
python3 tools/run.py provided_mjx_suite.py       # prepared MI355X environment
python3 tools/run.py refresh_gpu_report.py       # existing local evidence/report
~~~

Use the launcher for local setup/benchmark/report commands rather than invoking
nested tool scripts directly. It resolves only registered files and their helper
directories. Physics adapters and their source pins remain engine-specific.

## Runtime deployment

The bootstrap copies registered commands and selected configuration into the
configured local benchmark workspace using their stable basenames. This flat
runtime deployment keeps the existing measured coordinator protocol; it is
separate from source organization. Engine checkouts remain pinned upstream
dependencies, not vendored source. See [upstream dependencies](upstream-dependencies.md)
and the [benchmark guide](benchmark-quickstart.md).

Use a fresh runtime workspace after changing the source release. The bootstrap
refuses conflicting adapter files; it does not overwrite a previously measured
deployment. Existing raw receipts and logs stay in runtime storage.

## Removed one-off tools

Twenty-four old inspection, experiment retry, status/watchdog and ad hoc report
editing scripts were removed. They are available in Git history before this
reorganization. Current supplied-model adapters, reference-baseline adapters,
actual capture tools and numerical qualification helpers are retained in their
named categories. Nothing in this refactor constitutes a new GPU performance run.
