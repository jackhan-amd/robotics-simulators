#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../common.sh"
test -d "${STUDY_FLUIDLAB_SOURCE:?Operator-reviewed and licensed local API-compatible FluidLab source required}"
test -x "$STUDY_STORAGE_ROOT/venvs/fluidlab/bin/python"
test -f "$STUDY_STORAGE_ROOT/build/fluidlab-runtime-gfx1151/oclc_isa_version_1151.bc"
printf '%s\n' 'Local prerequisites found. This script does not download or redistribute unlicensed source.'
