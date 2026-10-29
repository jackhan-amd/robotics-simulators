#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../common.sh"
use_sdk
pin_source https://github.com/AMReX-Fluids/incflo ccb90bc41d9def18dddc4e1c4122a7d517add630 "$STUDY_STORAGE_ROOT/upstream/incflo"
pin_source https://github.com/AMReX-Codes/amrex 7f2fecd4adefeb6bcbc2a6d87243f062da0ef912 "$STUDY_STORAGE_ROOT/upstream/amrex"
pin_source https://github.com/AMReX-Fluids/AMReX-Hydro a153304acd787205b170b0f7fd8284627e076056 "$STUDY_STORAGE_ROOT/upstream/amrex-hydro"
timeout 900 cmake \
  -S \
  "$STUDY_STORAGE_ROOT/upstream/incflo" \
  -B \
  "$STUDY_STORAGE_ROOT/build/incflo-hip-devel" \
  -G \
  Ninja \
  -DINCFLO_HIP=ON \
  -DINCFLO_MPI=OFF \
  -DINCFLO_OMP=OFF \
  -DINCFLO_DIM=2 \
  -DINCFLO_EB=OFF \
  "-DAMREX_HOME=$STUDY_STORAGE_ROOT/upstream/amrex" \
  "-DAMREX_HYDRO_HOME=$STUDY_STORAGE_ROOT/upstream/amrex-hydro" \
  -DAMReX_AMD_ARCH=gfx1151 \
  "-DCMAKE_CXX_COMPILER=$ROCM_PATH/bin/hipcc" \
  "-DHIP_PATH=$ROCM_PATH" \
  "-DCMAKE_PREFIX_PATH=$ROCM_PATH" \
  "-DCMAKE_INSTALL_PREFIX=$STUDY_STORAGE_ROOT/install/incflo-hip"
timeout 900 cmake --build "$STUDY_STORAGE_ROOT/build/incflo-hip-devel" --target incflo --parallel 2
if [ ! -x "$STUDY_STORAGE_ROOT/venvs/incflo-tools/bin/python" ]; then
  uv venv --python 3.12 "$STUDY_STORAGE_ROOT/venvs/incflo-tools"
  uv pip install --python "$STUDY_STORAGE_ROOT/venvs/incflo-tools/bin/python" numpy==2.5.4
fi
