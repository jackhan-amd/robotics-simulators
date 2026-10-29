"""Unmodified AMD LIBERO vector backend and pinned, supplied LIBERO task."""
from workspace import expand_runtime, run_root, runtime_path
import argparse,hashlib,json,pathlib,statistics,time
import numpy as np,torch
from libero.libero import benchmark,get_libero_path
from instinct_sim_libero.vector import HipLiberoVectorEnv
p=argparse.ArgumentParser();p.add_argument('--envs',type=int,required=True);p.add_argument('--smoke',action='store_true');a=p.parse_args();R=run_root();steps=20 if a.smoke else 100
suite=benchmark.get_benchmark_dict()['libero_spatial']();task=suite.get_task(0);bddl=pathlib.Path(get_libero_path('bddl_files'))/task.problem_folder/task.bddl_file
# LIBERO's provided task/init state and AMD's provided vector facade; no MJCF generation.
args=dict(bddl_file_name=str(bddl),camera_heights=128,camera_widths=128)
start=time.perf_counter();env=HipLiberoVectorEnv(args,num_envs=a.envs,seed=0);init_file=pathlib.Path(get_libero_path('init_states'))/task.problem_folder/task.init_states_file;states=torch.load(init_file,map_location='cpu',weights_only=False);init_states=[np.asarray(states[0]).copy()for _ in range(a.envs)];env.reset(init_states);engine=env._slots[0]._env.engine;engine.sync();build_s=time.perf_counter()-start
actions={i:np.zeros(7,dtype=np.float64)for i in range(a.envs)}
def reset():env.reset(init_states);engine.sync()
start=time.perf_counter()
for _ in range(10):env.step(actions)
engine.sync();warm_s=time.perf_counter()-start;times=[];checks=[]
try:
 for rep in range(1 if a.smoke else 5):
  reset();start=time.perf_counter()
  for _ in range(steps):observations=env.step(actions)
  engine.sync();times.append(time.perf_counter()-start);q=np.asarray(engine.data.read_qpos_d());v=np.asarray(engine.data.read_qvel());finite=bool(np.isfinite(q).all()and np.isfinite(v).all());images=[]
  for i,result in observations.items():
   obs=result[0];img=np.asarray(obs['agentview_image']);images.append(bool(img.shape==(128,128,3)and np.isfinite(img).all()and img.max()>img.min()))
  checks.append(dict(valid=finite and all(images),finite_state=finite,nonuniform_camera_images=all(images),qpos_shape=list(q.shape)))
  if a.smoke:
   from PIL import Image
   Image.fromarray(np.asarray(observations[0][0]['agentview_image']).astype(np.uint8)).save(R/'evidence/instinct-provided-libero.png')
 median=statistics.median(times);valid=all(c['valid']for c in checks);model=env._slots[0]._env.model;dt=float(model.timestep)
 payload=dict(engine='instinct',implementation='provided HipLiberoVectorEnv / native GPU batch',scene='LIBERO spatial task 0: '+task.name,physics_valid=valid,backend_observed='hip',envs=a.envs,steps=steps,repeats=len(times),synchronized_rollout_s=times,median_s=median,env_step_per_s=a.envs*steps/median,build_s=build_s,warmup_s=warm_s,checks=checks,physics_dt=dt,camera=[128,128],bddl_file=str(bddl),bddl_sha256=hashlib.sha256(bddl.read_bytes()).hexdigest(),libero_commit='8f1084e3132a39270c3a13ebe37270a43ece2a01',backend_commit='a5fa73101988870e51f04fe1e7be5da56dda3841',controls='zero 7-delta action; supplied OSC/gripper pipeline; no learned policy',scope='provided task, reference initialization/reset and GPU physics/OSC/camera/observation pipeline unchanged; env.step end-to-end includes renderer, success checking and observation transfer; build/reset/warmup excluded; synchronized GPU boundary timer')
finally:env.close()
print(('SMOKE_RESULT_JSON:'if a.smoke else'BENCHMARK_RESULT_JSON:')+json.dumps(payload),flush=True)
raise SystemExit(0 if payload['physics_valid']else 3)
