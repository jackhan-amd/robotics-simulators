"""JAX MJX headless synchronized sweep on the repository's sphere/plane model."""
from workspace import expand_runtime, run_root, runtime_path
import argparse,json,pathlib,statistics,time
import jax,jax.numpy as jp,numpy as np,mujoco
from mujoco import mjx
p=argparse.ArgumentParser();p.add_argument('--envs',type=int,required=True);p.add_argument('--steps',type=int,default=1000);a=p.parse_args()
devices=jax.devices('rocm');assert len(devices)==1 and ('MI355X'in devices[0].device_kind or 'gfx950'in devices[0].device_kind)
jax.config.update('jax_enable_x64',False)
model=mujoco.MjModel.from_xml_path(expand_runtime('${LAB_ROOT}/repo/configs/freefall.xml'));mx=mjx.put_model(model,impl='jax');one=mjx.make_data(mx,impl='jax')
initial=jax.tree.map(lambda x:jp.broadcast_to(x,(a.envs,)+x.shape),one)
def rollout(data):
 def step(d,_):return jax.vmap(lambda x:mjx.step(mx,x))(d),None
 return jax.lax.scan(step,data,None,length=a.steps)[0]
start=time.perf_counter();compiled=jax.jit(rollout).lower(initial).compile();compile_s=time.perf_counter()-start
start=time.perf_counter();warm=compiled(initial);jax.block_until_ready(warm);warm_s=time.perf_counter()-start
times=[];checks=[];memory=[]
for _ in range(5):
 start=time.perf_counter();final=compiled(initial);jax.block_until_ready(final);times.append(time.perf_counter()-start)
 q=np.asarray(final.qpos);v=np.asarray(final.qvel);t=np.asarray(final.time)
 checks.append(bool(np.isfinite(q).all() and np.isfinite(v).all() and (q[:,2]>=.04).all() and np.max(abs(t-a.steps*.001))<1e-4 and final.qpos.devices()=={devices[0]}))
 memory.append(devices[0].memory_stats())
median=statistics.median(times)
print('BENCHMARK_RESULT_JSON:'+json.dumps(dict(engine='mujoco',implementation='MJX-JAX',backend_observed='rocm',device=devices[0].device_kind,physics_valid=all(checks),checks=checks,scene='repository_freefall_sphere_plane',precision='float32',envs=a.envs,steps=a.steps,dt=.001,repeats=5,compile_s=compile_s,warmup_s=warm_s,synchronized_rollout_s=times,median_s=median,env_step_per_s=a.envs*a.steps/median,step_per_s=a.steps/median,rtf_per_env=a.steps*.001/median,device_memory_stats=memory[-1],readback_in_timing=False,jax=jax.__version__,mujoco=mujoco.__version__)))
