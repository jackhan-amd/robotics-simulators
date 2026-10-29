"""MJWarp native HIP direct-step sweep, with reset between repetitions."""
from workspace import expand_runtime, run_root, runtime_path
import argparse,importlib.metadata,json,os,statistics,time
import mujoco,mujoco_warp as mjw,numpy as np,warp as wp
p=argparse.ArgumentParser();p.add_argument('--envs',type=int,required=True);p.add_argument('--steps',type=int,default=1000);a=p.parse_args()
wp.config.kernel_cache_dir=os.environ['STUDY_WARP_CACHE'];wp.init();device=wp.get_device('cuda:0');assert device.is_hip and 'MI355X'in device.name and device.arch_str.split(':')[0]=='gfx950';wp.set_device(device)
start=time.perf_counter();model=mujoco.MjModel.from_xml_path(expand_runtime('${LAB_ROOT}/repo/configs/freefall.xml'));m=mjw.put_model(model);d=mjw.put_data(model,mujoco.MjData(model),nworld=a.envs,nconmax=8,njmax=32);wp.synchronize_device(device);build_s=time.perf_counter()-start
start=time.perf_counter()
for _ in range(500):mjw.step(m,d)
wp.synchronize_device(device);warmup_s=time.perf_counter()-start
capture_s=0.0
times=[];checks=[]
for rep in range(5):
 mjw.reset_data(m,d);wp.synchronize_device(device);start=time.perf_counter()
 for _ in range(a.steps):mjw.step(m,d)
 wp.synchronize_device(device);times.append(time.perf_counter()-start)
 q=d.qpos.numpy();v=d.qvel.numpy();t=d.time.numpy();checks.append(bool(np.isfinite(q).all()and np.isfinite(v).all()and(q[:,2]>=.04).all()and np.max(abs(t-a.steps*.001))<1e-4))
median=statistics.median(times)
print('BENCHMARK_RESULT_JSON:'+json.dumps(dict(engine='mujoco',implementation='MJWarp HIP direct',backend_observed='hip',device=device.name,hip_arch=device.arch_str,physics_valid=all(checks),checks=checks,scene='repository_freefall_sphere_plane',precision='float32',graph_mode='disabled: this port synchronizes inside step, incompatible with graph capture',envs=a.envs,steps=a.steps,dt=.001,repeats=5,compile_s=build_s+capture_s,warmup_s=warmup_s,synchronized_rollout_s=times,median_s=median,env_step_per_s=a.envs*a.steps/median,step_per_s=a.steps/median,rtf_per_env=a.steps*.001/median,nconmax_per_world=8,njmax_per_world=32,readback_in_timing=False,mujoco=mujoco.__version__,warp=wp.__version__,mujoco_warp=importlib.metadata.version('mujoco-warp'))))
