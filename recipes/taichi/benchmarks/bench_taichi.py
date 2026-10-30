"""Analytic-gravity smoke and steady-state parallel particle integration on HIP."""
import argparse,json,statistics,time
import numpy as np,taichi as ti
p=argparse.ArgumentParser();p.add_argument('--particles',type=int,default=1024);p.add_argument('--smoke',action='store_true');a=p.parse_args()
ti.init(arch=ti.amdgpu,default_fp=ti.f32,offline_cache=True)
assert ti.lang.impl.get_runtime().prog.config().arch==ti.amdgpu
n=a.particles;dt=.0001;steps=200 if a.smoke else 1000
z=ti.field(ti.f32,shape=n);v=ti.field(ti.f32,shape=n)
@ti.kernel
def reset():
 for i in z:z[i]=1.;v[i]=0.
@ti.kernel
def step():
 for i in z:
  v[i]-=9.81*dt;z[i]+=v[i]*dt
start=time.perf_counter();reset();step();ti.sync();jit_s=time.perf_counter()-start
times=[];checks=[]
for rep in range(1 if a.smoke else 5):
 reset();ti.sync();start=time.perf_counter()
 for i in range(steps):step()
 ti.sync();times.append(time.perf_counter()-start)
 positions=z.to_numpy();vel=v.to_numpy();expected=1-9.81*dt*dt*steps*(steps+1)/2
 checks.append(bool(np.isfinite(positions).all()and np.isfinite(vel).all()and np.max(abs(positions-expected))<.0002 and np.max(abs(vel+9.81*steps*dt))<.0001))
median=statistics.median(times)
print(('SMOKE_RESULT_JSON:'if a.smoke else 'BENCHMARK_RESULT_JSON:')+json.dumps(dict(engine='taichi',implementation='AMD Taichi official b2 container payload',backend_observed='amdgpu',physics_valid=all(checks),checks=checks,version=str(ti.__version__),particles=n,steps=steps,dt=dt,jit_s=jit_s,repeats=len(times),synchronized_rollout_s=times,median_s=median,step_per_s=steps/median,particle_updates_per_s=n*steps/median,readback_in_timing=False,scene='independent_particle_gravity_no_contact')))
