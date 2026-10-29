#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../common.sh"
pin_source https://github.com/Nek5000/nekRS 96b3cf9e5bacede16568826c04a21bc0fe50dc7d "$STUDY_STORAGE_ROOT/upstream/nekrs"
# 기존 Docker daemon과 고정 digest image를 사용한다. driver/daemon 설정은 변경하지 않는다.
docker image inspect sha256:4fa5bc9c24d25ef7e0fe38b23fc5f2b27fc986177bd2f9e496997bcf5af03871 > "$STUDY_PRIVATE_ROOT/nekrs-image-replay.json"
mkdir -p "$STUDY_STORAGE_ROOT/build/nekrs-docker" "$STUDY_STORAGE_ROOT/install/nekrs-docker"
export STUDY_UID="$(id -u)" STUDY_GID="$(id -g)"
export STUDY_CONTAINER_NAME="robotics-recipe-build-$$"
timeout 900 docker \
  run \
  --rm \
  --pull=never \
  --network=none \
  --read-only \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --user \
  "${STUDY_UID}:${STUDY_GID}" \
  --pids-limit=128 \
  --cpus=2 \
  --memory=4g \
  --tmpfs=/tmp:rw,size=512m \
  -v \
  "${STUDY_STORAGE_ROOT}/upstream/nekrs:/src:ro" \
  -v \
  "${STUDY_STORAGE_ROOT}/build/nekrs-docker:/build:rw" \
  -v \
  "${STUDY_STORAGE_ROOT}/install/nekrs-docker:/install:rw" \
  --entrypoint=/bin/bash \
  sha256:4fa5bc9c24d25ef7e0fe38b23fc5f2b27fc986177bd2f9e496997bcf5af03871 \
  -c \
  'cmake -S /src -B /build -DCMAKE_INSTALL_PREFIX=/install -DCMAKE_C_COMPILER=mpicc -DCMAKE_CXX_COMPILER=mpicxx -DCMAKE_Fortran_COMPILER=mpif77 -DOCCA_ENABLE_HIP=ON -DOCCA_ENABLE_CUDA=OFF -DOCCA_ENABLE_DPCPP=OFF -DENABLE_ADIOS=OFF -DENABLE_HYPRE_GPU=OFF -DENABLE_CVODE=OFF -DENABLE_CPPTRACE=OFF'
export STUDY_UID="$(id -u)" STUDY_GID="$(id -g)"
export STUDY_CONTAINER_NAME="robotics-recipe-build-$$"
timeout 900 docker \
  run \
  --name \
  "${STUDY_CONTAINER_NAME}" \
  --rm \
  --pull=never \
  --read-only \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --user \
  "${STUDY_UID}:${STUDY_GID}" \
  --pids-limit=128 \
  --cpus=2 \
  --memory=8g \
  --tmpfs=/tmp:rw,size=512m \
  -v \
  "${STUDY_STORAGE_ROOT}/upstream/nekrs:/src:ro" \
  -v \
  "${STUDY_STORAGE_ROOT}/build/nekrs-docker:/build:rw" \
  -v \
  "${STUDY_STORAGE_ROOT}/install/nekrs-docker:/install:rw" \
  --entrypoint=/bin/bash \
  sha256:4fa5bc9c24d25ef7e0fe38b23fc5f2b27fc986177bd2f9e496997bcf5af03871 \
  -c \
  'cmake --build /build --target install --parallel 2'
