# Upstream dependencies and local project layout

This repository manages example adapters, GPU execution/measurement tools,
verification code and report generation. The simulator engines remain upstream
projects. Every engine is connected by a public source URL and fixed commit in
[upstream-sources.json](../configs/upstream-sources.json), with one common clone tool.
No complete engine source tree is copied into this repository's Git history.
Adapted small examples retain their original notices and license exceptions.

## One dependency convention for every engine

```bash
python3 tools/fetch_sources.py list
python3 tools/fetch_sources.py plan --engine fluidlab
python3 tools/fetch_sources.py fetch --engine fluidlab
python3 tools/fetch_sources.py verify --engine fluidlab
# Explicitly select another engine, several engines, or all:
python3 tools/fetch_sources.py fetch --engine mujoco --engine genesis
python3 tools/fetch_sources.py plan --engine all
```

The default storage root is `<project>/.runtime`. Set `STUDY_STORAGE_ROOT` or
`--root` to use another local runtime-storage directory. The tool clones each
selected source into `<runtime-root>/upstream/<source-id>`, checks out the fixed
commit and verifies origin, revision and a clean working tree. Existing checkouts
with another revision/origin or local changes are preserved and rejected. A failed
download leaves its staging directory for inspection. There is no implicit bulk fetch.

```text
robotics-simulators/                 project checkout
  recipes/, smokes/, study/, tools/ tracked harness and adapted examples
  configs/upstream-sources.json     tracked dependency URLs and commits
  .runtime/                        local runtime files; Git ignored
    upstream/fluidlab/             independent upstream Git checkout
    upstream/genesis-world/        independent upstream Git checkout
    upstream/...                   other selected upstream projects
    venvs/, build/, install/        separately prepared runtimes
```

These dependency directories are part of the benchmark deployment. Their file
location says nothing about remote computation. In the reported experiments,
the engine and benchmark ran on the same MI355X GPU server. This repository's Git
tracks the harness and dependency declarations; each cloned engine checkout has
its own upstream Git origin. The clone tool does not use a remote compute service.

## Source checkout is separate from runtime preparation

Fetch only retrieves pinned source. Follow each recipe and the
[benchmark quick start](benchmark-reproduction.md) to build/install the GPU runtime,
prepare assets, run smoke and measure throughput. Python wheels and official images
may provide some engine runtimes; the corresponding source pin remains available
for attribution and parameter inspection. Native submodule/dependency initialization
stays in the documented engine build procedure.

FluidLab uses the same dependency mechanism. With the project-local default:

```bash
export STUDY_STORAGE_ROOT="$PWD/.runtime"
python3 tools/fetch_sources.py fetch --engine fluidlab
export FLUIDLAB_SOURCE_ROOT="$STUDY_STORAGE_ROOT/upstream/fluidlab"
export STUDY_FLUIDLAB_SOURCE="$FLUIDLAB_SOURCE_ROOT"
```

The benchmark's compatibility adapter may prepare a separate working copy; the
pinned upstream checkout stays unchanged. Only forward simulation was measured:
gradient/backward, learning and optimization paths were not tested. The pinned
FluidLab tree has no explicit root license grant recorded; cloning a public source
does not change its terms or establish redistribution rights. See
[LICENSES.md](../LICENSES.md). The repository does not redistribute that source or
generated contextual patches.
