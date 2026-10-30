"""The supplied AMD Humanoid XML, unchanged, through MJX-JAX on ROCm."""
from workspace import expand_runtime, run_root, runtime_path
import argparse,hashlib,json,os,pathlib,statistics,time
import jax,jax.numpy as jp,mujoco,numpy as np
from mujoco import mjx
p=argparse.ArgumentParser();p.add_argument('--envs',type=int,required=True);p.add_argument('--smoke',action='store_true');a=p.parse_args();steps=200 if a.smoke else 1000
source=runtime_path('${STUDY_STORAGE_ROOT}/upstream/mujoco-warp-amd/benchmarks/humanoid/humanoid.xml')
device=jax.devices('rocm')[0];assert 'MI355X'in device.device_kind;jax.config.update('jax_enable_x64',False)
model=mujoco.MjModel.from_xml_path(str(source));cpu=mujoco.MjData(model)
if model.nkey:mujoco.mj_resetDataKeyframe(model,cpu,0)
mx=mjx.put_model(model,impl='jax');one=mjx.put_data(model,cpu,impl='jax');initial=jax.tree.map(lambda x:jp.broadcast_to(x,(a.envs,)+x.shape),one)
probe=jax.jit(lambda d:mjx.step(mx,d));d=one;parity=0.
for _ in range(20):
 mujoco.mj_step(model,cpu);d=probe(d);jax.block_until_ready(d);parity=max(parity,float(abs(np.asarray(d.qpos)-cpu.qpos).max()))
def rollout(data):
 def step(d,_):return jax.vmap(lambda x:mjx.step(mx,x))(d),None
 return jax.lax.scan(step,data,None,length=steps)[0]
start=time.perf_counter();compiled=jax.jit(rollout).lower(initial).compile();compile_s=time.perf_counter()-start
start=time.perf_counter();warm=compiled(initial);jax.block_until_ready(warm);warmup_s=time.perf_counter()-start
times=[];checks=[]
for _ in range(1 if a.smoke else 5):
 start=time.perf_counter();final=compiled(initial);jax.block_until_ready(final);times.append(time.perf_counter()-start)
 q=np.asarray(final.qpos);v=np.asarray(final.qvel);t=np.asarray(final.time)
 checks.append(bool(np.isfinite(q).all()and np.isfinite(v).all()and np.max(abs(t-steps*model.opt.timestep))<.001 and parity<.01 and final.qpos.devices()=={device}))
median=statistics.median(times);valid=all(checks)
print(('SMOKE_RESULT_JSON:'if a.smoke else'BENCHMARK_RESULT_JSON:')+json.dumps(dict(engine='mujoco',implementation='MJX-JAX supplied Humanoid',scene='AMD MJWarp supplied Humanoid XML through MJX-JAX',physics_valid=valid,backend_observed='rocm',device=device.device_kind,source=str(source),model_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),envs=a.envs,steps=steps,dt=model.opt.timestep,repeats=len(times),synchronized_rollout_s=times,median_s=median,env_step_per_s=a.envs*steps/median,rtf_per_env=steps*model.opt.timestep/median,compile_s=compile_s,warmup_s=warmup_s,early_cpu_qpos_max_error=parity,checks=checks,nv=model.nv,nbody=model.nbody,ngeom=model.ngeom,solver_iterations=model.opt.iterations,line_search_iterations=model.opt.ls_iterations,solver_tolerance=model.opt.tolerance,precision='float32',controls='zero; provided default initialization/keyframe',jax=jax.__version__,mujoco=mujoco.__version__,compiler_profile=os.environ.get('STUDY_MJX_COMPILER_PROFILE','default'),xla_flags=os.environ.get('XLA_FLAGS',''),scope='Provided XML physical settings unchanged; JAX scan compilation/warmup/reset/readback excluded; synchronized wall time; basic sanity and 20-step CPU parity, not long-horizon accuracy proof')),flush=True)
raise SystemExit(0 if valid else 3)
