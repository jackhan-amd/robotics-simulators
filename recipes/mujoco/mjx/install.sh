#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../../common.sh"
recorded_python mujoco-mjx-rocm VERIFIED_MUJOCO_MJX_ROCM_ENV
"$STUDY_STORAGE_ROOT/venvs/mujoco-mjx-rocm/bin/python" -c 'import jax; print(jax.__version__)'
