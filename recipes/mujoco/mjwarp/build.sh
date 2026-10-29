#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../../common.sh"
recorded_python mjwarp-rocm VERIFIED_MJWARP_ROCM_ENV
use_sdk
pin_source https://github.com/AMD-Ecosystem/warp 2e2673bb7b90eaabb9cb89dc1f55a76f61c13aab "$STUDY_STORAGE_ROOT/upstream/warp-amd"
pin_source https://github.com/AMD-Ecosystem/mujoco_warp 9dfdf7ab8d5a996fe143e9e2c1e5da646c6fc14f "$STUDY_STORAGE_ROOT/upstream/mujoco-warp-amd"
timeout 300 "$STUDY_STORAGE_ROOT/venvs/mjwarp-rocm/bin/python" "$STUDY_STORAGE_ROOT/upstream/warp-amd/build_lib.py" --rocm-path "$ROCM_PATH" --hip-arch=gfx1151 --jobs=2 --no-use-libmathdx
uv pip install --no-deps --python "$STUDY_STORAGE_ROOT/venvs/mjwarp-rocm/bin/python" "$STUDY_STORAGE_ROOT/upstream/warp-amd" "$STUDY_STORAGE_ROOT/upstream/mujoco-warp-amd"
