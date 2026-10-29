# Agent guide

## Scope and starting points

This repository maintains simulator installation/build recipes and small headless physics smokes. World construction, model inference and training workflows belong in robotics-studio.

Read `README.md`, the relevant engine recipe under `recipes/`, and `docs/verification.md` before changing an engine integration.

## Repository map

- `recipes/<engine>/`: installation/build scripts and runnable instructions; `recipes/common.sh` provides shared setup.
- `recipes/engines.json`: engine registry; `recipes/manifest.json`: executable recipe catalog.
- `configs/cases.json`: smoke cases; `configs/sources.json` and dependency locks: source and package pins.
- `smokes/`: bounded physics scenes and backend compatibility helpers.
- `simulators/`: catalog CLI and local HTML generation.
- `tools/`: environment setup, asset acquisition, inventory and run recording.
- `tests/`: repository and harness checks that run without a GPU.

## Making changes

Keep the engine instructions, recipe command, registered case and dependency pins consistent. Update the relevant files together when changing an integration. Keep new smokes small, headless and bounded, with explicit backend selection and numerical checks.

`configs/verification-summary.json` describes previously reviewed configurations. Change its claims only when new evidence has been reviewed. A successful install, process exit or catalog check does not establish physics validity. Follow `docs/verification.md` when recording a new run, and report CPU fallback as `CPU_ONLY`.

Keep runtime sources, environments, models, datasets, caches and raw logs in configured external storage. Do not commit payloads, local environment files or individual run histories. Inspect device usage before a GPU run and run one bounded GPU smoke at a time. Leave existing services and global Python/driver configuration untouched. Throughput measurement requires a separate task.

## Checks

Run from the repository root with Python 3.12:

```bash
python3 -m unittest discover -s tests -v
python3 -m simulators check
python3 tools/assets.py check
python3 -m simulators build
git diff --check
```

The HTML build writes ignored local files under `report/`. These checks validate repository wiring and harness behavior. Use the relevant recipe to validate actual simulator execution; `python3 -m simulators smoke <id>` previews a command and `--execute` runs it.

## Documentation and licensing

Keep each engine recipe complete enough to install, configure, build and run its smoke. Preserve command blocks, data, citations and source pins during prose edits. Follow `docs/writing.md` for documentation conventions.

Keep third-party license notices verbatim. Update `LICENSES.md`, notices and asset metadata when adding a dependency or redistributable asset. The repository's MIT license does not grant rights to external code, models or datasets.
