#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../common.sh"
recorded_python genesis-amdgpu VERIFIED_GENESIS_AMDGPU_ENV
pin_source https://github.com/Genesis-Embodied-AI/genesis-world 90d55545c193082a8e32f9b1b6b7732f14d89be8 "$STUDY_STORAGE_ROOT/upstream/genesis-world"
python3 tools/prepare_rocm_loader.py --runtime-venv "$STUDY_STORAGE_ROOT/venvs/genesis-amdgpu" --output-dir "$STUDY_STORAGE_ROOT/compat/rocm7.14"
"$STUDY_STORAGE_ROOT/venvs/genesis-amdgpu/bin/python" -c 'import genesis,torch,quadrants; assert torch.version.hip; print(torch.__version__, torch.version.hip)'
