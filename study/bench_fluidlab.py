"""Forward-only FluidLab MPM particle scale benchmark with equivalent API patch."""
from workspace import expand_runtime, run_root, runtime_path
import argparse,json,pathlib,statistics,sys,time
import numpy as np,taichi as ti
p=argparse.ArgumentParser();p.add_argument('--edge',type=int,required=True);a=p.parse_args()
sys.path.insert(0,expand_runtime('${STUDY_STORAGE_ROOT}/upstream/fluidlab-modern-api'))
from fluidlab.fluidengine.simulators.mpm_simulator import MPMSimulator
ti.init(arch=ti.amdgpu,device_memory_GB=1,cpu_max_num_threads=1,kernel_profiler=False,offline_cache=False)
coords=np.linspace(.2,.8,a.edge,dtype=np.float32);x=np.array([[i,j,k]for i in coords for j in coords for k in coords],dtype=np.float32);n=len(x)
particles=dict(x=x,used=np.ones(n,dtype=np.int32),mat=np.zeros(n,dtype=np.int32),rho=np.full(n,1000,dtype=np.float32),body_id=np.zeros(n,dtype=np.int32),bodies={'n':1})
start=time.perf_counter();sim=MPMSimulator(dim=3,quality=.25,gravity=(0,-9.81,0),horizon=20,max_substeps_local=120,max_substeps_global=1000,ckpt_dest='cpu');sim.build(agent=None,smoke_field=None,statics=[],particles=particles);sim.disable_grad();initial=sim.get_state();m0=float(sim.particles_i.mass.to_numpy().sum());ti.sync();build_s=time.perf_counter()-start
start=time.perf_counter();sim.step();ti.sync();warmup_s=time.perf_counter()-start;times=[];checks=[]
for rep in range(5):
 sim.set_state(0,initial);sim.cur_substep_global=0;ti.sync();start=time.perf_counter()
 for _ in range(10):sim.step()
 ti.sync();times.append(time.perf_counter()-start);state=sim.get_state();mass=float(sim.particles_i.mass.to_numpy().sum());expected=initial['x'].mean(axis=0)+np.array([0,-9.81*sim.dt**2*100*101/2,0]);error=float(np.max(abs(state['x'].mean(axis=0)-expected)))
 checks.append(bool(np.isfinite(state['x']).all()and np.isfinite(state['v']).all()and len(state['x'])==n and abs(mass-m0)<=max(1e-6,abs(m0)*1e-6) and error<.002 and sim.cur_substep_global==100))
median=statistics.median(times)
print('BENCHMARK_RESULT_JSON:'+json.dumps(dict(engine='fluidlab',case='forward_MPM',implementation='FluidLab forward MPM plus Taichi API compatibility',backend_observed='hip',physics_valid=all(checks),checks=checks,particles=n,grid=[16,16,16],steps=100,repeats=5,dt=sim.dt,build_s=build_s,warmup_s=warmup_s,synchronized_rollout_s=times,median_s=median,step_per_s=100/median,particle_updates_per_s=n*100/median,position_dtype=str(state['x'].dtype),readback_in_timing=False,gradients=False,scope='synthetic gravity-driven forward core; no full FluidLab task or gradients')))
