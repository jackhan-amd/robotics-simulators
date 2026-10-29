"""Measure the shipped single_franka_envs.py scene; only bypass visualization."""
from workspace import expand_runtime, run_root, runtime_path
import argparse,hashlib,json,pathlib,runpy,statistics,sys,time
import genesis as gs,quadrants as qd,numpy as np,torch
p=argparse.ArgumentParser();p.add_argument('--envs',type=int,required=True);p.add_argument('--steps',type=int,default=1000);p.add_argument('--smoke',action='store_true');a=p.parse_args()
R=run_root();source=R/'storage/upstream/genesis-world/examples/rigid/single_franka_envs.py';captured={}
class SceneReady(Exception):pass
original_init=gs.init;original_build=gs.Scene.build
def init(**kw):kw['backend']=gs.amdgpu;original_init(**kw)
def build(self,*args,**kw):
 result=original_build(self,*args,**kw);captured['scene']=self;raise SceneReady()
gs.init=init;gs.Scene.build=build;sys.argv=[str(source),'-g','-b',str(a.envs),'-s',str(a.steps)];start=time.perf_counter()
try:runpy.run_path(str(source),run_name='__main__')
except SceneReady:pass
finally:gs.init=original_init;gs.Scene.build=original_build
scene=captured['scene'];robot=scene.entities[1]
def sync():qd.sync();torch.cuda.synchronize()
sync();build_s=time.perf_counter()-start;initial=robot.get_qpos().detach().cpu().numpy().copy();dt=float(scene.dt);substeps=int(scene.substeps)
start=time.perf_counter()
for _ in range(100):scene.step()
sync();warmup_s=time.perf_counter()-start;times=[];checks=[];samples=[]
for rep in range(1 if a.smoke else 5):
 scene.reset();sync();start=time.perf_counter()
 for _ in range(a.steps):scene.step()
 sync();times.append(time.perf_counter()-start);q=robot.get_qpos().detach().cpu().numpy();v=robot.get_dofs_velocity().detach().cpu().numpy();checks.append(bool(np.isfinite(q).all()and np.isfinite(v).all()and np.max(abs(q))<10));samples.append(q.reshape(-1,q.shape[-1])[0].tolist())
median=statistics.median(times);valid=all(checks);meta=dict(engine='genesis',implementation='Genesis provided single_franka_envs.py / native batch',physics_valid=valid,backend_observed=gs.backend.name,scene='upstream single_franka_envs.py unmodified physics scene',source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_commit='90d55545c193082a8e32f9b1b6b7732f14d89be8',envs=a.envs,steps=a.steps,repeats=len(times),dt=dt,substeps=substeps,dofs=int(v.shape[-1]),qpos_width=int(q.shape[-1]),build_s=build_s,warmup_s=warmup_s,warmup_steps=100,synchronized_rollout_s=times,median_s=median,env_step_per_s=a.envs*a.steps/median,step_per_s=a.steps/median,rtf_per_env=a.steps*dt/median,checks=checks,first_env_qpos=samples,genesis_version=gs.__version__,torch=torch.__version__,scope='Provided Franka + plane model and default simulation parameters unchanged; GPU backend explicit, per-step camera render/printing disabled; no policy/controller added; build/reset/readback excluded')
print(('SMOKE_RESULT_JSON:'if a.smoke else'BENCHMARK_RESULT_JSON:')+json.dumps(meta),flush=True);gs.destroy();raise SystemExit(0 if valid else 3)
