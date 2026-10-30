# Copy to your external workspace as env.sh; supply locations before sourcing.
: "${LAB_ROOT:?Set LAB_ROOT to an external study workspace}"
: "${ROCM_PATH:?Set ROCM_PATH to the matching ROCm SDK root}"
export LAB_ROOT ROCM_PATH
export STUDY_STORAGE_ROOT="${STUDY_STORAGE_ROOT:-$LAB_ROOT/storage}"
export STUDY_WORKTREE="${STUDY_WORKTREE:-$LAB_ROOT/repo}"
export STUDY_PRIVATE_ROOT="${STUDY_PRIVATE_ROOT:-$STUDY_STORAGE_ROOT/private}"
export STUDY_AMD_ARCH=gfx950 STUDY_AMD_NAME=MI355X
export ROCR_VISIBLE_DEVICES=0 HIP_VISIBLE_DEVICES=0
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export HIP_PATH="$ROCM_PATH"
# Internal package path in the pinned AMD Taichi image payload.
export PYTHON_SITE_PACKAGES="${PYTHON_SITE_PACKAGES:-/usr/local/lib/python3.12/dist-packages}"
export LD_LIBRARY_PATH="$ROCM_PATH/lib:$ROCM_PATH/lib/llvm/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
