#!/usr/bin/env bash
# Shared paths for user-owned simulator installs; no system configuration changes.
RECIPE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RECIPE_ROOT"
: "${STUDY_STORAGE_ROOT:?Configure approved external storage and source its private environment file first}"
export STUDY_WORKTREE="$RECIPE_ROOT"
export STUDY_PRIVATE_ROOT="${STUDY_PRIVATE_ROOT:-$STUDY_STORAGE_ROOT/private}"
export UV_CACHE_DIR="$STUDY_STORAGE_ROOT/cache/uv-publication"
export UV_PYTHON_INSTALL_DIR="$STUDY_STORAGE_ROOT/python"
export TMPDIR="$STUDY_STORAGE_ROOT/tmp"
export XDG_CACHE_HOME="$STUDY_STORAGE_ROOT/cache"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
mkdir -p "$STUDY_PRIVATE_ROOT" "$TMPDIR" "$XDG_CACHE_HOME" "$STUDY_STORAGE_ROOT/venvs" "$STUDY_STORAGE_ROOT/upstream"
test -w "$STUDY_STORAGE_ROOT"

pin_source() {
  local url="$1" sha="$2" dest="$3"
  if [ ! -e "$dest" ]; then
    timeout 300 git clone --filter=blob:none --no-checkout "$url" "$dest"
    timeout 300 git -C "$dest" fetch --depth=1 origin "$sha"
    git -C "$dest" checkout --detach "$sha"
  fi
  test "$(git -C "$dest" rev-parse HEAD)" = "$sha"
}

public_python() {
  local engine="$1" name="$2"
  if [ ! -x "$STUDY_STORAGE_ROOT/venvs/$name/bin/python" ]; then
    python3 tools/setup_environment.py --engine "$engine" --name "$name" --execute
  fi
  "$STUDY_STORAGE_ROOT/venvs/$name/bin/python" -c 'import sys; assert sys.version_info[:2] == (3,12)'
}

recorded_python() {
  local name="$1" provider="$2"
  if [ ! -x "$STUDY_STORAGE_ROOT/venvs/$name/bin/python" ]; then
    local supplied="${!provider:-}"
    if [ -z "$supplied" ]; then
      printf '%s\n' "Provide $provider: an existing reviewed Python3.12 prefix. See recipes/README.md#rocm-runtime."
      return 2
    fi
    python3 tools/setup_environment.py --engine local-runtime --name "$name" --base "$supplied" --execute
  fi
  "$STUDY_STORAGE_ROOT/venvs/$name/bin/python" -c 'import sys; assert sys.version_info[:2] == (3,12)'
}

use_sdk() {
  if [ -z "${ROCM_PATH:-}" ]; then
    recorded_python rocm-build VERIFIED_ROCM_BUILD_ENV
    ROCM_PATH="$("$STUDY_STORAGE_ROOT/venvs/rocm-build/bin/python" -m rocm_sdk path --root)"
  fi
  export ROCM_PATH HIP_PATH="$ROCM_PATH"
  test -x "$ROCM_PATH/bin/hipcc"
}
