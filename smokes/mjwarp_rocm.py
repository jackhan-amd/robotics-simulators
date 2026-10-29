#!/usr/bin/env python3
"""One-world public AMD MJWarp HIP port, with native CPU parity and kernel evidence."""
import json
import importlib.metadata
import os
from pathlib import Path
import platform
import time

import mujoco
import mujoco_warp as mjw
import numpy as np
import warp as wp

wp.config.kernel_cache_dir = os.environ['STUDY_WARP_CACHE']
expected_arch = os.environ.get('STUDY_AMD_ARCH', 'gfx1151')
expected_name = os.environ.get('STUDY_AMD_NAME', '8060S')
wp.init()
device = wp.get_device('cuda:0')
assert device.is_hip and expected_name in device.name and device.arch_str.split(':')[0] == expected_arch
wp.set_device(device)
started = time.perf_counter()
model = mujoco.MjModel.from_xml_path(str(Path(__file__).resolve().parents[1] / 'configs/freefall.xml'))
cpu = mujoco.MjData(model)
reference = []
for _ in range(500):
    mujoco.mj_step(model, cpu)
    reference.append(np.r_[cpu.qpos.copy(), cpu.qvel.copy()])
reference = np.asarray(reference)
m = mjw.put_model(model)
initial = mujoco.MjData(model)
d = mjw.put_data(model, initial, nworld=1, nconmax=8, njmax=32)
wp.synchronize_device(device)
build_s = time.perf_counter() - started
started = time.perf_counter()
for _ in range(2):
    mjw.step(m, d)
wp.synchronize_device(device)
warmup_s = time.perf_counter() - started
# Reset after compilation, including solver warmstart and contact buffers.
d = mjw.put_data(model, initial, nworld=1, nconmax=8, njmax=32)
wp.synchronize_device(device)
samples, times, contacts, constraints = [], [], [], []
timer = wp.ScopedTimer('physics_probe', print=False, synchronize=True, cuda_filter=wp.TIMING_KERNEL)
started = time.perf_counter()
for i in range(500):
    if i == 0:
        timer.__enter__()
    mjw.step(m, d)
    wp.synchronize_device(device)
    if i == 9:
        timer.__exit__(None, None, None)
    samples.append(np.r_[d.qpos.numpy()[0], d.qvel.numpy()[0]])
    times.append(float(d.time.numpy()[0]))
    contacts.append(int(d.nacon.numpy()[0]))
    constraints.append(int(d.nefc.numpy()[0]))
step_wall_s = time.perf_counter() - started
actual = np.asarray(samples)
z, vz = actual[:, 2], actual[:, 9]
t = np.arange(1, 501) * 0.001
kernels = [r.name for r in timer.timing_results if r.device == device and r.filter == wp.TIMING_KERNEL]
physics_kernels = sorted({n for n in kernels if any(s in n.lower() for s in ('solve', 'integrat', 'collision', 'euler'))})
metrics = {
    'cpu_qpos_max_absolute_error': float(np.max(np.abs(actual[:, :7] - reference[:, :7]))),
    'cpu_qvel_max_absolute_error': float(np.max(np.abs(actual[:, 7:] - reference[:, 7:]))),
    'analytic_z_max_error_m': float(np.max(np.abs(z[:200] - (1 - 9.81*t[:200]**2/2)))),
    'discrete_z_max_error_m': float(np.max(np.abs(z[:200] - (1 - 9.81*0.001**2*np.arange(1,201)*np.arange(2,202)/2)))),
    'min_bottom_z_m': float(z.min()-0.05), 'final_z_m': float(z[-1]),
    'final_vz_m_s': float(vz[-1]), 'time_error_s': abs(times[-1] - 0.5),
    'contact_steps': sum(c > 0 for c in contacts), 'max_contacts': max(contacts),
    'max_constraints': max(constraints), 'kernel_dispatches_profiled': len(kernels),
}
gates = {
    'finite_state': bool(np.isfinite(actual).all() and np.isfinite(times).all()),
    'cpu_qpos': metrics['cpu_qpos_max_absolute_error'] <= 0.002,
    'cpu_qvel': metrics['cpu_qvel_max_absolute_error'] <= 0.15,
    'analytic_freefall': metrics['analytic_z_max_error_m'] <= 0.002,
    'discrete_euler': metrics['discrete_z_max_error_m'] <= 1e-5,
    'penetration': metrics['min_bottom_z_m'] >= -0.01,
    'final_height': metrics['final_z_m'] >= 0.04,
    'final_speed': abs(metrics['final_vz_m_s']) <= 1,
    'contact_occurred': metrics['contact_steps'] > 0,
    'simulation_time': metrics['time_error_s'] <= 1e-5,
    'no_buffer_overflow': max(contacts) <= 8 and max(constraints) <= 32,
    'gpu_resident': d.qpos.device == device and d.qvel.device == device,
    'physics_kernels': bool(physics_kernels),
    'hip_device': bool(device.is_hip and device.arch_str.split(':')[0] == expected_arch),
}
print('SMOKE_RESULT_JSON:' + json.dumps({
    'backend_observed': 'hip', 'implementation': 'MJWarp public AMD-Ecosystem port',
    'physics_valid': all(gates.values()), 'gates': gates, 'metrics': metrics,
    'device_name': device.name, 'hip_arch': device.arch_str,
    'warp_device_alias': str(device), 'mujoco_warp': importlib.metadata.version('mujoco-warp'), 'python': platform.python_version(),
    'mujoco': mujoco.__version__, 'warp': wp.__version__, 'steps': 500, 'dt': 0.001,
    'nworld': 1, 'nconmax': 8, 'njmax': 32, 'warmup_steps': 2,
    'build_s': build_s, 'warmup_s': warmup_s, 'step_wall_s': step_wall_s,
    'physics_kernel_samples': physics_kernels[:8], 'states': actual.tolist(),
    'cpu_states': reference.tolist(), 'times': times, 'contacts': contacts,
    'g2_qualified': False, 'renderer': 'none',
    'notes': '500 instrumented HIP steps; first ten profiled after reset. This port retains cuda:0 as an API alias; is_hip and the explicitly selected ISA/name are asserted. Not G2.',
}, allow_nan=False))
raise SystemExit(0 if all(gates.values()) else 3)
