"""Separate steady-state Genesis rigid throughput, no per-step readback."""
import argparse,json,statistics,time
import numpy as np,torch,genesis as gs,quadrants as qd
p=argparse.ArgumentParser();p.add_argument('--envs',type=int,required=True);a=p.parse_args()
assert torch.cuda.device_count()==1 and 'MI355X'in torch.cuda.get_device_name(0) and torch.cuda.get_device_properties(0).gcnArchName.split(':')[0]=='gfx950'
gs.init(backend=gs.amdgpu,precision='32',seed=0,logging_level='warning');start=time.perf_counter()
scene=gs.Scene(sim_options=gs.options.SimOptions(dt=.001,substeps=2),show_viewer=False);scene.add_entity(gs.morphs.Plane());box=scene.add_entity(gs.morphs.Box(size=(.1,.1,.1),pos=(0,0,.8)));scene.build(n_envs=a.envs);qd.sync();torch.cuda.synchronize();build_s=time.perf_counter()-start
start=time.perf_counter()
for _ in range(1000):scene.step()
qd.sync();torch.cuda.synchronize();warmup_s=time.perf_counter()-start
times=[];checks=[]
for rep in range(5):
 scene.reset();qd.sync();torch.cuda.synchronize();start=time.perf_counter()
 for _ in range(1000):scene.step()
 qd.sync();torch.cuda.synchronize();times.append(time.perf_counter()-start)
 pos=box.get_pos().detach().cpu().numpy();vel=box.get_vel().detach().cpu().numpy();checks.append(bool(np.isfinite(pos).all()and np.isfinite(vel).all()and(pos[...,2]>=.04).all()and(pos[...,2]<=.07).all()))
median=statistics.median(times)
print('BENCHMARK_RESULT_JSON:'+json.dumps(dict(engine='genesis',implementation='Genesis rigid AMD',backend_observed=gs.backend.name,physics_valid=all(checks),checks=checks,scene='box_plane_contact',precision='float32',envs=a.envs,steps=1000,dt=.001,substeps=2,repeats=5,build_s=build_s,warmup_s=warmup_s,synchronized_rollout_s=times,median_s=median,env_step_per_s=a.envs*1000/median,step_per_s=1000/median,rtf_per_env=1/median,compile_s=build_s,genesis_version=gs.__version__,quadrants_version=str(qd.__version__),torch=torch.__version__,readback_in_timing=False,renderer='software EGL context only, no frames in timed loop')))
gs.destroy()
