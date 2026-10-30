"""Headless FluidLab original MPM core via explicit Taichi backend, 27 particles/10 substeps."""
import argparse,ctypes,json,os,sys,time,hashlib
from pathlib import Path
import numpy as np
import taichi as ti
p=argparse.ArgumentParser();p.add_argument('--backend',choices=('cpu','hip'),required=True);p.add_argument('--stage',choices=('legacy_init','mpm'),default='mpm');p.add_argument('--source-root',type=Path);p.add_argument('--runtime-dir',type=Path);p.add_argument('--steps',type=int,choices=(10,50,250),default=10);a=p.parse_args()
if a.source_root:sys.path.insert(0,str(a.source_root.resolve()))
if a.runtime_dir:ti._lib.core.set_lib_dir(os.fsencode(a.runtime_dir.resolve()))
arch=ti.cpu if a.backend=='cpu' else ti.amdgpu
if a.stage=='legacy_init':
 try:ti.init(arch=arch,device_memory_GB=.125,packed=True)
 except Exception as e:
  print('FLUIDLAB_API_JSON:'+json.dumps(dict(stage=a.stage,taichi=list(ti.__version__),error_type=type(e).__name__,error=str(e),g1=False)),flush=True);raise
 raise SystemExit(0)
name='CPU';hip_runtime_version=None
if a.backend=='hip':
 lib=ctypes.CDLL('libamdhip64.so');count=ctypes.c_int();buf=ctypes.create_string_buffer(256)
 assert lib.hipGetDeviceCount(ctypes.byref(count))==0 and count.value==1
 assert lib.hipDeviceGetName(buf,256,0)==0;name=buf.value.decode();assert os.environ['STUDY_AMD_NAME'] in name
 version=ctypes.c_int();assert lib.hipRuntimeGetVersion(ctypes.byref(version))==0;hip_runtime_version=version.value
start=time.perf_counter();ti.init(arch=arch,device_memory_GB=.125,cpu_max_num_threads=1,kernel_profiler=True,offline_cache=False)
assert ti.lang.impl.current_cfg().arch==arch
if a.backend=='hip':
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_shared'))
 from proc_maps import library_paths
 paths=library_paths(Path('/proc/self/maps').read_text(),'libamdhip64.so');assert len(paths)==1
 path=Path(next(iter(paths)));print('FLUIDLAB_RUNTIME_RECEIPT_JSON:'+json.dumps(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),hip_runtime_version=hip_runtime_version)),flush=True)
from fluidlab.fluidengine.simulators.mpm_simulator import MPMSimulator
import fluidlab
if a.source_root:assert Path(fluidlab.__file__).resolve().is_relative_to(a.source_root.resolve())
source_sha256=hashlib.sha256((Path(fluidlab.__file__).parent/'fluidengine/simulators/mpm_simulator.py').read_bytes()).hexdigest()
x=np.array([[.45+i*.025,.5+j*.025,.45+k*.025] for i in range(3) for j in range(3) for k in range(3)],dtype=np.float32);n=len(x)
particles=dict(x=x,used=np.ones(n,dtype=np.int32),mat=np.zeros(n,dtype=np.int32),rho=np.full(n,1000,dtype=np.float32),body_id=np.zeros(n,dtype=np.int32),bodies={'n':1})
sim=MPMSimulator(dim=3,quality=.25,gravity=(0,-9.81,0),horizon=a.steps//10+1,max_substeps_local=a.steps+10,max_substeps_global=1000,ckpt_dest='disk')
sim.build(agent=None,smoke_field=None,statics=[],particles=particles);sim.disable_grad();initial=sim.get_state();m0=sim.particles_i.mass.to_numpy().sum()
for _ in range(a.steps//10):sim.step()
ti.sync();state=sim.get_state();m1=sim.particles_i.mass.to_numpy().sum();total_t=a.steps*sim.dt
expected=initial['x'].mean(axis=0)+np.array([0,-9.81*sim.dt*sim.dt*a.steps*(a.steps+1)/2,0]);err=float(np.max(np.abs(state['x'].mean(axis=0)-expected)))
gates=dict(finite=bool(np.isfinite(state['x']).all() and np.isfinite(state['v']).all()),particle_count=len(state['x'])==27 and int(state['used'].sum())==27,mass=bool(abs(m1-m0)/m0<=1e-6),freefall_com=err<=5e-5,downward=bool(state['x'][:,1].mean()<initial['x'][:,1].mean()),bounds=bool(((state['x']>=0)&(state['x']<=1)).all()),speed=bool(abs(state['v']).max()<=max(.1,1.2*9.81*total_t)),step_count=sim.cur_substep_global==a.steps,backend=ti.lang.impl.current_cfg().arch==arch)
try:profile_s=ti.profiler.get_kernel_profiler_total_time();ti.profiler.print_kernel_profiler_info()
except Exception:profile_s=None
payload=dict(implementation='FluidLab MPMSimulator',source_sha256=source_sha256,compatibility_api=bool(a.source_root and 'modern-api' in a.source_root.name),runtime_target_overlay=bool(a.runtime_dir),backend_observed=a.backend,physics_valid=all(gates.values()),gates=gates,taichi=list(ti.__version__),device_name=name,hip_runtime_version=hip_runtime_version,steps=a.steps,dt=sim.dt,particles=27,grid=[16,16,16],metrics=dict(mass_initial_native=float(m0),mass_final_native=float(m1),relative_mass_drift=float(abs(m1-m0)/m0),com_error_m=err,max_speed_m_s=float(abs(state['v']).max()),time_s=total_t),profile_s=profile_s,wall_s=time.perf_counter()-start,g2_qualified=False,field_samples=dict(initial=initial['x'].tolist(),final=state['x'].tolist(),velocity=state['v'].tolist()))
print('SMOKE_RESULT_JSON:'+json.dumps(payload,sort_keys=True),flush=True);ti.reset();raise SystemExit(0 if all(gates.values()) else 3)
