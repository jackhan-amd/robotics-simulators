#!/usr/bin/env python3
"""MuJoCo MJX-JAX GPU versus the native CPU scene; never use Warp implicitly."""
import json
import os
from pathlib import Path
import platform
import time
import numpy as np
import mujoco
from mujoco import mjx
import jax
import jax.numpy as jp
from jax.extend import backend as jax_backend
import jaxlib

jax.config.update('jax_enable_x64',False)
backend=jax_backend.get_backend('rocm')
devices=jax.devices('rocm')
print('JAX_RUNTIME:',backend.platform,backend.platform_version,devices,flush=True)
assert len(devices)==1, 'Exactly one isolated GPU required'
device=devices[0]
assert 'ROCM' in backend.platform_version.upper(), 'ROCm backend required'
assert os.environ.get('STUDY_AMD_NAME', '8060S') in device.device_kind or os.environ.get('STUDY_AMD_ARCH', 'gfx1151') in device.device_kind, 'Unexpected AMD device'
model=mujoco.MjModel.from_xml_path(str(Path(__file__).resolve().parents[3]/'configs/freefall.xml'))
cpu=mujoco.MjData(model);reference=[]
for _ in range(500):
    mujoco.mj_step(model,cpu);reference.append([float(cpu.qpos[2]),float(cpu.qvel[2])])
reference=np.asarray(reference)
with jax.default_device(device):
    mx=mjx.put_model(model,impl='jax');initial=mjx.make_data(mx,impl='jax')
    def rollout(data):
        def step(d,_):
            d=mjx.step(mx,d)
            return d,jp.concatenate((d.qpos,d.qvel,jp.reshape(d.time,(1,))))
        return jax.lax.scan(step,data,None,length=500)
    start=time.perf_counter();compiled=jax.jit(rollout).lower(initial).compile();compile_s=time.perf_counter()-start
    start=time.perf_counter();warm=compiled(initial);jax.block_until_ready(warm);warmup_s=time.perf_counter()-start
    timings=[];trajectories=[];gpu_resident=True
    for _ in range(3):
        start=time.perf_counter();final,samples=compiled(initial);jax.block_until_ready((final,samples));timings.append(time.perf_counter()-start)
        gpu_resident &= samples.devices()=={device};trajectories.append(np.asarray(samples))
x_full=trajectories[0];x=x_full[:,[2,9,13]]; t=np.arange(1,201)*0.001
metrics={'analytic_z_error_m':float(abs(x[:200,0]-(1-9.81*t*t/2)).max()),
         'discrete_z_error_m':float(abs(x[:200,0]-(1-9.81*0.001**2*np.arange(1,201)*(np.arange(1,201)+1)/2)).max()),
         'min_bottom_z_m':float(x[:,0].min()-0.05),'final_z_m':float(x[-1,0]),
         'time_error_s':abs(float(x[-1,2])-0.5),'cpu_max_z_error_m':float(abs(x[:,0]-reference[:,0]).max()),
         'cpu_max_vz_error_m_s':float(abs(x[:,1]-reference[:,1]).max()),
         'repeat_max_error':max(float(abs(v-x_full).max()) for v in trajectories)}
gates={'gpu_resident':bool(gpu_resident),'finite_state':all(bool(np.isfinite(v).all()) for v in trajectories),
       'analytic_freefall':metrics['analytic_z_error_m']<=0.002,'discrete_euler':metrics['discrete_z_error_m']<=1e-5,
       'penetration':metrics['min_bottom_z_m']>=-0.01,'final_height':metrics['final_z_m']>=0.04,
       'time':metrics['time_error_s']<=1e-5,'contact':bool((x[:,0]<=0.05).any()),
       'cpu_z':metrics['cpu_max_z_error_m']<=0.002,'cpu_vz':metrics['cpu_max_vz_error_m_s']<=0.15}
print('SMOKE_RESULT_JSON:'+json.dumps({'backend_observed':'amdgpu','physics_valid':all(gates.values()),'gates':gates,
      'metrics':metrics,'steps':500,'dt':0.001,'repeats':3,'compile_s':compile_s,'warmup_s':warmup_s,
      'synchronized_rollout_s':timings,'jax':jax.__version__,'jaxlib':jaxlib.__version__,
      'mujoco':mujoco.__version__,'python':platform.python_version(),'device_kind':device.device_kind,
      'platform_version':backend.platform_version,'implementation':'MJX-JAX','g2_qualified':False,
      'full_state_sample_width':int(x_full.shape[1]),'trajectory':x.tolist()},sort_keys=True),flush=True)
raise SystemExit(0 if all(gates.values()) else 3)
