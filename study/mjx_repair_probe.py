"""Stage-labelled reproduction of MJX Humanoid; physical settings stay unchanged."""
import argparse,hashlib,json,os,pathlib,statistics,time
def stage(name,**fields):print('PROBE_STAGE:'+json.dumps(dict(stage=name,monotonic=time.monotonic(),**fields)),flush=True)
p=argparse.ArgumentParser();p.add_argument('--envs',type=int,required=True);p.add_argument('--steps',type=int,default=1000);p.add_argument('--repeats',type=int,default=1);p.add_argument('--batch-axis',type=int,choices=(0,-1),default=0);a=p.parse_args()
stage('import')
import jax,jax.numpy as jp,mujoco,numpy as np
from mujoco import mjx
if os.environ.get('STUDY_MJX_BARRIER')=='com_velocity':
 from mjx_rocm_workaround import install_com_velocity_barrier
 install_com_velocity_barrier();stage('com_velocity_barrier_installed')
device=jax.devices('rocm')[0];assert 'MI355X'in device.device_kind;jax.config.update('jax_enable_x64',False)
source=pathlib.Path(os.environ['STUDY_STORAGE_ROOT'])/'upstream/mujoco-warp-amd/benchmarks/humanoid/humanoid.xml'
model=mujoco.MjModel.from_xml_path(str(source));cpu=mujoco.MjData(model)
if model.nkey:mujoco.mj_resetDataKeyframe(model,cpu,0)
stage('model_upload',device=str(device),model_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
mx=mjx.put_model(model,impl='jax');one=mjx.put_data(model,cpu,impl='jax')
initial=jax.tree.map(lambda x:jp.broadcast_to(x,(a.envs,)+x.shape)if a.batch_axis==0 else jp.broadcast_to(jp.expand_dims(x,-1),x.shape+(a.envs,)),one);jax.block_until_ready(initial)
stage('initial_broadcast_ready')
probe=jax.jit(lambda d:mjx.step(mx,d));d=one;parity=0.
for _ in range(20):
 mujoco.mj_step(model,cpu);d=probe(d);jax.block_until_ready(d);parity=max(parity,float(abs(np.asarray(d.qpos)-cpu.qpos).max()))
stage('cpu_parity_ready',max_error=parity)
def rollout(data):
 def step(d,_):return jax.vmap(lambda x:mjx.step(mx,x),in_axes=a.batch_axis,out_axes=a.batch_axis)(d),None
 return jax.lax.scan(step,data,None,length=a.steps)[0]
stage('compile_start');start=time.perf_counter();compiled=jax.jit(rollout).lower(initial).compile();compile_s=time.perf_counter()-start
stage('compile_done',seconds=compile_s);start=time.perf_counter();warm=compiled(initial);jax.block_until_ready(warm);warmup_s=time.perf_counter()-start
stage('warmup_done',seconds=warmup_s);times=[];checks=[]
for rep in range(a.repeats):
 start=time.perf_counter();final=compiled(initial);jax.block_until_ready(final);times.append(time.perf_counter()-start)
 q=np.asarray(final.qpos);v=np.asarray(final.qvel);t=np.asarray(final.time);checks.append(bool(np.isfinite(q).all()and np.isfinite(v).all()and np.max(abs(t-a.steps*model.opt.timestep))<.001 and parity<.01 and final.qpos.devices()=={device}));stage('repeat_done',rep=rep,seconds=times[-1],valid=checks[-1])
median=statistics.median(times);valid=all(checks)
payload=dict(engine='mujoco',implementation='MJX-JAX supplied Humanoid / repair probe',scene='AMD MJWarp supplied Humanoid XML through MJX-JAX',physics_valid=valid,backend_observed='rocm',device=device.device_kind,model_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),envs=a.envs,steps=a.steps,dt=model.opt.timestep,repeats=a.repeats,synchronized_rollout_s=times,median_s=median,env_step_per_s=a.envs*a.steps/median,compile_s=compile_s,warmup_s=warmup_s,early_cpu_qpos_max_error=parity,checks=checks,jax=jax.__version__,mujoco=mujoco.__version__,xla_flags=os.environ.get('XLA_FLAGS',''),scope='Supplied Humanoid and solver unchanged; stage-labelled diagnostic; synchronized rollout; no CPU fallback')
print(('BENCHMARK_RESULT_JSON:'if a.repeats==5 else'SMOKE_RESULT_JSON:')+json.dumps(payload),flush=True)
raise SystemExit(0 if valid else 3)
