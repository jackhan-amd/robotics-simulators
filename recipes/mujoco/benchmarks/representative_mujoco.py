"""Add official articulated humanoid to the recorded MJWarp sweep without private inputs."""
from workspace import expand_runtime, run_root, runtime_path
import argparse,hashlib,json,os,pathlib,statistics,time
import mujoco,mujoco_warp as mjw,numpy as np,warp as wp
p=argparse.ArgumentParser();p.add_argument('--envs',type=int,required=True);p.add_argument('--steps',type=int,default=1000);p.add_argument('--smoke',action='store_true');a=p.parse_args()
path=runtime_path('${STUDY_STORAGE_ROOT}/upstream/mujoco-warp-amd/benchmarks/humanoid/humanoid.xml')
wp.config.kernel_cache_dir=os.environ['STUDY_WARP_CACHE'];wp.init();device=wp.get_device('cuda:0');assert device.is_hip and 'MI355X'in device.name;wp.set_device(device)
start=time.perf_counter();model=mujoco.MjModel.from_xml_path(str(path));cpu=mujoco.MjData(model)
if model.nkey:mujoco.mj_resetDataKeyframe(model,cpu,0)
initial_qpos=cpu.qpos.copy();m=mjw.put_model(model);d=mjw.put_data(model,cpu,nworld=a.envs,nconmax=24,njmax=64);wp.synchronize_device(device);build_s=time.perf_counter()-start
# Compare the first twenty physical steps to native CPU before a long contact rollout.
cpu_ref=[];gpu_probe=[]
for _ in range(20):
 mujoco.mj_step(model,cpu);mjw.step(m,d);wp.synchronize_device(device);cpu_ref.append(cpu.qpos.copy());gpu_probe.append(d.qpos.numpy()[0].copy())
parity=float(np.max(np.abs(np.array(cpu_ref)-np.array(gpu_probe))))
if a.smoke:
 for _ in range(180):mjw.step(m,d)
 wp.synchronize_device(device);q=d.qpos.numpy();v=d.qvel.numpy();valid=bool(np.isfinite(q).all()and np.isfinite(v).all()and parity<.01)
 print('SMOKE_RESULT_JSON:'+json.dumps(dict(engine='mujoco',case='official_humanoid',implementation='MJWarp HIP direct Humanoid',backend_observed='hip',physics_valid=valid,early_cpu_qpos_max_error=parity,envs=a.envs,steps=200,dt=model.opt.timestep,nv=model.nv,nu=model.nu,nbody=model.nbody,ngeom=model.ngeom,model_sha256=hashlib.sha256(path.read_bytes()).hexdigest())));raise SystemExit(0 if valid else 3)
start=time.perf_counter()
for _ in range(100):mjw.step(m,d)
wp.synchronize_device(device);warmup_s=time.perf_counter()-start
times=[];checks=[]
for rep in range(5):
 mjw.reset_data(m,d)
 # Match initial keyframe qpos used in the smoke while retaining reset solver buffers.
 wp.copy(d.qpos,wp.array(np.broadcast_to(initial_qpos,(a.envs,model.nq)).copy(),dtype=wp.float32,device=device))
 wp.synchronize_device(device);start=time.perf_counter()
 for _ in range(a.steps):mjw.step(m,d)
 wp.synchronize_device(device);times.append(time.perf_counter()-start)
 q=d.qpos.numpy();v=d.qvel.numpy();t=d.time.numpy();checks.append(bool(np.isfinite(q).all()and np.isfinite(v).all()and np.max(abs(t-a.steps*model.opt.timestep))<.001 and parity<.01))
median=statistics.median(times)
print('BENCHMARK_RESULT_JSON:'+json.dumps(dict(engine='mujoco',case='official_humanoid',implementation='MJWarp HIP direct Humanoid',backend_observed='hip',physics_valid=all(checks),checks=checks,scene='official_MJWarp_humanoid_crouching',model_source=str(path),model_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),envs=a.envs,steps=a.steps,dt=model.opt.timestep,repeats=5,compile_s=build_s,warmup_s=warmup_s,synchronized_rollout_s=times,median_s=median,env_step_per_s=a.envs*a.steps/median,step_per_s=a.steps/median,rtf_per_env=a.steps*model.opt.timestep/median,nv=model.nv,nu=model.nu,nbody=model.nbody,ngeom=model.ngeom,solver_iterations=model.opt.iterations,line_search_iterations=model.opt.ls_iterations,solver_tolerance=model.opt.tolerance,early_cpu_qpos_max_error=parity,nconmax_per_world=24,njmax_per_world=64,mujoco=mujoco.__version__,warp=wp.__version__,precision='float32',controls='zero; no trained policy',readback_in_timing=False,graph_mode='direct HIP; no graph capture')))
