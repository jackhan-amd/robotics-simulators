"""Shared observable backend evidence; strings are retained in private markers."""
import json
import os
import platform
import numpy as np
import genesis as gs
import quadrants as qd
import torch


def array(v):
    if hasattr(v, 'detach'):
        v = v.detach().cpu().numpy()
    return np.asarray(v, dtype=float)


def init(backend):
    os.environ.setdefault('QD_KERNEL_PROFILER', '1')
    torch.set_num_threads(1)
    if backend != 'cpu':
        assert torch.cuda.is_available(), 'Torch GPU runtime unavailable'
        assert torch.cuda.device_count() == 1, 'Expose exactly one checked GPU'
        props = torch.cuda.get_device_properties(0)
        if backend == 'amdgpu':
            assert torch.version.hip and props.gcnArchName.split(':')[0] == os.environ.get('STUDY_AMD_ARCH', 'gfx1151'), 'Unexpected isolated AMD ISA'
            assert os.environ.get('STUDY_AMD_NAME', '8060S') in props.name, 'Unexpected isolated AMD device'
            print('SELECTED_AMD_DEVICE:', props.name, props.gcnArchName, flush=True)
        else:
            assert not torch.version.hip and props.name.endswith('RTX 3090'), 'Expected idle RTX 3090'
    runtime_dir = os.environ.get('STUDY_QD_RUNTIME_DIR')
    if runtime_dir:
        assert backend == 'amdgpu', 'Runtime patch is AMD-only'
        qd._lib.core.set_lib_dir(runtime_dir.encode())
    gs.init(backend=getattr(gs, backend), precision='32', seed=0, logging_level='warning')


def sync():
    qd.sync()
    if gs.device.type == 'cuda':
        torch.cuda.synchronize()


def begin_profile():
    sync()
    if qd.lang.impl.get_runtime().prog.config().kernel_profiler:
        qd.profiler.clear_kernel_profiler_info()


def emit(backend, gates, **data):
    sync()
    arch = qd.lang.impl.get_runtime().prog.config().arch
    observed = gs.backend.name
    profile_enabled = bool(qd.lang.impl.get_runtime().prog.config().kernel_profiler)
    profiler_s = qd.profiler.get_kernel_profiler_total_time() if profile_enabled else 0.0
    if profile_enabled:
        qd.profiler.print_kernel_profiler_info()
    backend_valid = observed == backend and arch == getattr(qd, 'cpu' if backend == 'cpu' else backend)
    kernel_evidence = profiler_s > 0
    gates['backend_verified'] = bool(backend_valid)
    if backend != 'cpu' and profile_enabled:
        gates['profiled_simulation_kernels'] = bool(kernel_evidence)
    valid = all(gates.values())
    gates = {key: bool(value) for key, value in gates.items()}
    payload = dict(backend_observed=observed, physics_valid=valid, gates=gates,
                   python=platform.python_version(), torch=torch.__version__,
                   torch_hip=torch.version.hip, torch_cuda=torch.version.cuda,
                   genesis_version=gs.__version__, quadrants_version=str(qd.__version__),
                   quadrants_arch=str(arch), torch_device=str(gs.device),
                   hip_arch=torch.cuda.get_device_properties(0).gcnArchName if backend == 'amdgpu' else None,
                   gpu_name=torch.cuda.get_device_name(0) if gs.device.type == 'cuda' else None,
                   profiler_s=profiler_s, external_trace_required=(backend != 'cpu' and not profile_enabled), g2_qualified=False, **data)
    print('SMOKE_RESULT_JSON:'+json.dumps(payload, sort_keys=True), flush=True)
    gs.destroy()
    raise SystemExit(0 if valid else 3)
