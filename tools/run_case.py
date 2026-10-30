#!/usr/bin/env python3
"""Bounded child execution. Status remains pending until evidence is reviewed."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

BASE = Path(__file__).resolve().parents[1]
BACKENDS = ('cpu', 'cuda', 'amdgpu', 'hip')


def numeric_tree(value):
    """Export numerical evidence only; raw strings remain private."""
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, list):
        return [numeric_tree(v) for v in value if not isinstance(v, str)]
    if isinstance(value, dict):
        return {k: numeric_tree(v) for k, v in value.items()
                if k.replace('_', '').isalnum() and not isinstance(v, str)}
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--node', required=True, choices=('halo', 'node1'))
    p.add_argument('--suite', required=True)
    p.add_argument('--case', required=True)
    p.add_argument('--backend', required=True, choices=BACKENDS)
    p.add_argument('--timeout', type=int, default=300)
    p.add_argument('--run-kind', choices=('physics', 'configure', 'build', 'preflight', 'training'),
                   help='Explicit stage for non-CMake builds; never grants physics validity')
    p.add_argument('--private-root', type=Path, default=os.environ.get('STUDY_PRIVATE_ROOT'))
    p.add_argument('command', nargs=argparse.REMAINDER)
    args = p.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    limit = 7200 if args.run_kind in ('configure','build','preflight') else 1800
    if not command or not 1 <= args.timeout <= limit:
        p.error(f'Provide a command and timeout 1..{limit} seconds (default 300; extended budget only for explicit G0 stages)')
    if args.private_root is None:
        p.error('Set STUDY_PRIVATE_ROOT or --private-root to private evidence storage')
    catalog = json.loads((BASE / 'configs/cases.json').read_text())
    if not any(c['suite'] == args.suite and c['id'] == args.case and args.node in c['nodes'] for c in catalog):
        p.error('Unknown case/node; add it to configs/cases.json first')
    run_id = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8]
    evidence_ref = Path('runs') / args.node / run_id
    private = args.private_root / evidence_ref
    public = args.private_root / 'results' / evidence_ref
    private.mkdir(parents=True, exist_ok=False)
    public.mkdir(parents=True, exist_ok=False)
    # Capture the source actually launched, even if documentation is edited while
    # a long authorized diagnostic is still running.
    git = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=BASE, capture_output=True, text=True)
    state = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=BASE,
                           capture_output=True, text=True)
    # Preserve the exact source bytes hashed at launch, even across later edits.
    script_hashes = {}
    for f in (BASE / 'recipes').rglob('*'):
        if not f.is_file() or not (f.suffix in ('.py', '.cpp', '.cc', '.h', '.hh') or f.name == 'CMakeLists.txt'):
            continue
        relative = f.relative_to(BASE)
        content = f.read_bytes()
        script_hashes[str(relative)] = hashlib.sha256(content).hexdigest()
        snapshot = private / 'source_snapshot' / relative
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes(content)
    start = time.perf_counter()
    timed_out = False
    try:
        with (private / 'stdout.txt').open('w') as outlog, (private / 'stderr.txt').open('w') as errlog:
            child = subprocess.Popen(command, cwd=BASE, stdout=outlog, stderr=errlog,
                                     text=True, errors='replace', start_new_session=True)
            try:
                child.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                # Only the process group created for this test; never unrelated services.
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
            rc = 124 if timed_out else child.returncode
    except OSError as exc:
        (private / 'stderr.txt').write_text(str(exc))
        rc = 127
    elapsed = time.perf_counter() - start
    out = (private / 'stdout.txt').read_text(errors='replace')
    err = (private / 'stderr.txt').read_text(errors='replace')
    emitted = None
    for line in out.splitlines():
        if line.startswith('SMOKE_RESULT_JSON:'):
            try:
                candidate = json.loads(line.split(':', 1)[1])
                emitted = candidate if isinstance(candidate, dict) else None
            except ValueError:
                emitted = None
    status = 'PENDING_VALIDATION' if rc == 0 else 'FAIL'
    observed = (emitted or {}).get('backend_observed')
    result = {
        'schema_version': 2, 'run_id': run_id,
        'captured_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'node': args.node, 'suite': args.suite, 'case_id': args.case,
        'device_target': os.environ.get('STUDY_AMD_ARCH') if args.backend in ('hip', 'amdgpu') else None,
        'backend_requested': args.backend, 'backend_observed': observed if observed in BACKENDS else None,
        'run_kind': args.run_kind or (('build' if '--build' in command else 'configure') if Path(command[0]).name == 'cmake' else ('preflight' if args.suite == 'environment' else 'physics')),
        'exit_code': rc, 'timed_out': timed_out, 'elapsed_wall_s': round(elapsed, 6),
        'timeout_budget_s': args.timeout,
        'status': status, 'validation': {'reviewed': False, 'g1': None, 'g2': False},
        'measurement': numeric_tree(emitted), 'git_sha': git.stdout.strip() if git.returncode == 0 else None,
        'tracked_source_dirty': bool(state.stdout.strip()), 'smoke_sha256': script_hashes,
        'settings': {k: os.environ[k] for k in ('QD_NUM_THREADS', 'OMP_NUM_THREADS', 'GS_ENABLE_ZEROCOPY', 'QD_KERNEL_PROFILER', 'QD_PERFDISPATCH_FORCE', 'QD_ENABLE_HIP_MEMPOOL', 'QD_GRAPH', 'HSA_XNACK', 'STUDY_ALTERNATIVE') if k in os.environ},
        'private_evidence_ref': str(evidence_ref),
    }
    (private / 'execution.json').write_text(json.dumps({**result, 'command': command, 'emitted': emitted, 'environment': {k: v for k, v in os.environ.items() if k in ('UTPX_MODE', 'STUDY_ALTERNATIVE', 'QD_GRAPH', 'HSA_XNACK', 'HIP_PATH', 'LD_PRELOAD', 'STUDY_MANAGED_POLICY', 'STUDY_DEM_DIAGNOSTICS', 'HIP_HOST_COHERENT', 'AMD_SERIALIZE_KERNEL', 'AMD_SERIALIZE_COPY', 'AMD_LOG_LEVEL', 'QD_ENABLE_HIP_MEMPOOL', 'STUDY_QD_RUNTIME_DIR', 'STUDY_AMD_ARCH', 'STUDY_AMD_NAME', 'CUDA_VISIBLE_DEVICES', 'HIP_VISIBLE_DEVICES', 'ROCR_VISIBLE_DEVICES', 'LD_LIBRARY_PATH', 'LLVM_PATH', 'XDG_CACHE_HOME', 'GS_CACHE_FILE_PATH', 'TMPDIR', 'JAX_PLATFORMS', 'XLA_PYTHON_CLIENT_PREALLOCATE', 'GS_ENABLE_ZEROCOPY', 'QD_NUM_THREADS', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'QD_KERNEL_PROFILER', 'QD_PERFDISPATCH_FORCE', 'STUDY_WARP_CACHE', 'UV_CACHE_DIR', 'QD_OFFLINE_CACHE_FILE_PATH', 'HIPRTC_COMPILE_OPTIONS_APPEND', 'WARP_CACHE_PATH', 'ROCM_PATH', 'HIP_PATH')}}, indent=2)+'\n')
    temporary_result = public / 'result.json.tmp'
    temporary_result.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    temporary_result.replace(public / 'result.json')
    print(f'{status} | {args.node} | {args.suite}/{args.case} | run {run_id}')
    print(f'Local record: {public / "result.json"}')
    return 0 if rc == 0 else 2


if __name__ == '__main__':
    sys.exit(main())
