#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../common.sh"
use_sdk
pin_source https://github.com/projectchrono/chrono 6f4004c358e5d0029aa3e39fc5ed13d66216f494 "$STUDY_STORAGE_ROOT/upstream/chrono"
pin_source https://gitlab.com/libeigen/eigen 3147391d946bb4b6c68edd901f2add6ac1f31f8c "$STUDY_STORAGE_ROOT/upstream/eigen"
timeout 900 cmake \
  -S \
  "$STUDY_STORAGE_ROOT/upstream/chrono" \
  -B \
  "$STUDY_STORAGE_ROOT/build/chrono-hip-devel" \
  -G \
  Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  "-DCHRONO_ROCM_ROOT=$ROCM_PATH" \
  "-DCMAKE_HIP_COMPILER=$ROCM_PATH/lib/llvm/bin/clang++" \
  "-DCMAKE_HIP_COMPILER_ROCM_ROOT=$ROCM_PATH" \
  "-DCMAKE_PREFIX_PATH=$ROCM_PATH" \
  -DCHRONO_GPU_BACKEND=HIP \
  -DCHRONO_HIP_ARCHITECTURES=gfx1151 \
  -DCMAKE_HIP_ARCHITECTURES=gfx1151 \
  -DCH_ENABLE_MODULE_FSI=ON \
  -DCH_ENABLE_MODULE_DEM=ON \
  -DBUILD_DEMOS=ON \
  -DBUILD_TESTING=OFF \
  "-DEIGEN3_INCLUDE_DIR=$STUDY_STORAGE_ROOT/upstream/eigen"
timeout 900 cmake --build "$STUDY_STORAGE_ROOT/build/chrono-hip-devel" --target Chrono_fsisph Chrono_dem ChronoModels_robot --parallel 2
timeout 900 cmake \
  -S \
  recipes/chrono/smoke \
  -B \
  "$STUDY_STORAGE_ROOT/build/chrono-smoke-hip" \
  -G \
  Ninja \
  "-DChrono_DIR=$STUDY_STORAGE_ROOT/build/chrono-hip-devel/cmake" \
  -DSTUDY_BACKEND=hip \
  -DSTUDY_WITH_DEM=ON \
  "-DCHRONO_ROCM_ROOT=$ROCM_PATH" \
  "-DCMAKE_PREFIX_PATH=$ROCM_PATH" \
  "-DEIGEN3_INCLUDE_DIR=$STUDY_STORAGE_ROOT/upstream/eigen"
timeout 300 cmake --build "$STUDY_STORAGE_ROOT/build/chrono-smoke-hip" --parallel 2
