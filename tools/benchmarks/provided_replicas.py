"""Independent replicas of supplied examples; no new scene/model construction."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import argparse,ast,hashlib,importlib.metadata,json,multiprocessing as mp,os,pathlib,runpy,statistics,sys,time,traceback,types
import numpy as np
R=run_root();S=storage_root()
def example(engine):
 if engine=='fluidlab':
  from provided_fluidlab_model import example as supplied
  return supplied()
 if engine=='genesis-sph':
  import genesis as gs,quadrants as qd,torch
  source=S/'upstream/genesis-world/examples/coupling/sph_rigid.py';captured={}
  class Ready(Exception):pass
  old_init=gs.init;old_build=gs.Scene.build
  def init(**kw):kw['backend']=gs.amdgpu;kw['logging_level']='warning';old_init(**kw)
  def build(self,*args,**kw):old_build(self,*args,**kw);captured['scene']=self;raise Ready()
  gs.init=init;gs.Scene.build=build;old_args=sys.argv;sys.argv=[str(source)]
  try:runpy.run_path(str(source),run_name='__main__')
  except Ready:pass
  finally:gs.init=old_init;gs.Scene.build=old_build;sys.argv=old_args
  scene=captured['scene'];water=scene.entities[1];cube=scene.entities[2];initial=water.get_particles_pos().detach().cpu().numpy().copy();assert gs.backend.name=='amdgpu'
  def sync():qd.sync();torch.cuda.synchronize()
  def reset():scene.reset();sync()
  def advance(steps):
   for _ in range(steps):scene.step()
   sync()
  def check():
   state=water.get_state();x=state.pos.detach().cpu().numpy().reshape(-1,3);v=state.vel.detach().cpu().numpy();c=cube.get_pos().detach().cpu().numpy();bounds=bool((x[:,0]>-.05).all()and(x[:,0]<1.05).all()and(abs(x[:,1])<1.05).all()and(x[:,2]>-.05).all()and(x[:,2]<2.45).all())
   return dict(valid=bool(np.isfinite(x).all()and np.isfinite(v).all()and np.isfinite(c).all()and bounds and len(x)==len(initial.reshape(-1,3))),particles=len(x),bounds=bounds,cube_position=c.tolist())
  meta=dict(model='provided SPH liquid + falling rigid cube coupling example',dt=float(scene.dt),substeps=int(scene.substeps),particles=len(initial.reshape(-1,3)),version=gs.__version__,source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),changes='explicit AMD backend, headless and warning log level; supplied scene, materials, bounds, resolution and coupling unchanged')
 elif engine=='taichi':
  import taichi as ti
  source=S/expand_runtime('official-taichi/root${PYTHON_SITE_PACKAGES}/taichi/examples/simulation/mpm88.py');tree=ast.parse(source.read_text());body=[]
  for node in tree.body:
   if isinstance(node,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='gui'for x in node.targets):break
   if isinstance(node,ast.Expr)and isinstance(node.value,ast.Call)and isinstance(node.value.func,ast.Attribute)and node.value.func.attr=='init':
    cache=S/'cache/provided-mpm88'/str(os.getpid());cache.mkdir(parents=True,exist_ok=True)
    node=ast.parse('ti.init(arch=ti.amdgpu, random_seed=0, cpu_max_num_threads=1, offline_cache=False, offline_cache_file_path='+repr(str(cache))+')').body[0]
   body.append(node)
  module=types.ModuleType('provided_mpm88');module.__file__=str(source);sys.modules[module.__name__]=module;exec(compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),str(source),'exec'),module.__dict__)
  assert ti.lang.impl.get_runtime().prog.config().arch==ti.amdgpu
  arrays={k:getattr(module,k).to_numpy()for k in ['x','v','C','J']}
  def reset():
   for k,v in arrays.items():getattr(module,k).from_numpy(v)
   ti.sync()
  reset.cleanup=ti.reset
  def advance(steps):
   for _ in range(steps):module.substep()
   ti.sync()
  def check():
   x=module.x.to_numpy();v=module.v.to_numpy();j=module.J.to_numpy();mass=float(module.grid_m.to_numpy().sum());expected=module.n_particles*module.p_mass
   return dict(valid=bool(np.isfinite(x).all()and np.isfinite(v).all()and np.isfinite(j).all()and x.min()>-.02 and x.max()<1.02 and abs(mass-expected)<expected*1e-4 and abs(x-arrays['x']).max()>1e-4),particles=len(x),grid_mass_error=abs(mass-expected),min_J=float(j.min()),max_displacement=float(abs(x-arrays['x']).max()))
  meta=dict(model='provided MPM88 MLS-MPM liquid example',particles=module.n_particles,grid=[module.n_grid]*2,dt=module.dt,version=str(ti.__version__),source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),changes='HIP backend + fixed random seed; GUI loop omitted; kernels/material/grid/boundaries unchanged')
 else:raise ValueError('GPU engine required: '+engine)
 return reset,advance,check,meta
def worker(conn,engine,count):
 try:
  worlds=[example(engine)for _ in range(count)]
  for reset,advance,check,meta in worlds:
   advance(50)
   reset()
  conn.send(('ready',worlds[0][3]))
  while True:
   cmd,arg=conn.recv()
   if cmd=='stop':break
   if cmd=='reset':
    for reset,_,_,_ in worlds:reset()
    conn.send(('reset',None))
   elif cmd=='run':
    for _,advance,_,_ in worlds:advance(arg)
    conn.send(('done',None))
   elif cmd=='check':conn.send(('checks',[check()for _,_,check,_ in worlds]))
 except BaseException:conn.send(('error',traceback.format_exc()))
 finally:
  if 'worlds'in locals():
   for reset,_,_,_ in worlds:
    cleanup=getattr(reset,'cleanup',None)
    if cleanup:cleanup()
   del worlds
   import gc;gc.collect()
  conn.close()
def main():
 p=argparse.ArgumentParser();p.add_argument('--engine',choices=['taichi','fluidlab','genesis-sph'],required=True);p.add_argument('--envs',type=int,required=True);p.add_argument('--steps',type=int,default=1000);p.add_argument('--smoke',action='store_true');a=p.parse_args();workers=a.envs;ctx=mp.get_context('spawn');children=[];pipes=[]
 def receive(c):
  if not c.poll(300):raise TimeoutError('example worker exceeded bounded wait')
  tag,value=c.recv()
  if tag=='error':raise RuntimeError(value)
  return value
 try:
  start=time.perf_counter()
  for i in range(workers):
   parent,child=ctx.Pipe();proc=ctx.Process(target=worker,args=(child,a.engine,a.envs//workers+(i<a.envs%workers)));proc.start();child.close();children.append(proc);pipes.append(parent)
  metas=[receive(c)for c in pipes];build_s=time.perf_counter()-start;times=[];checks=[]
  for _ in range(1 if a.smoke else 5):
   for c in pipes:c.send(('reset',None))
   for c in pipes:receive(c)
   start=time.perf_counter()
   for c in pipes:c.send(('run',a.steps))
   for c in pipes:receive(c)
   times.append(time.perf_counter()-start)
   for c in pipes:c.send(('check',None))
   checks.append([x for c in pipes for x in receive(c)])
  median=statistics.median(times);valid=all(x['valid']for row in checks for x in row);meta=metas[0];gpu=True;payload=dict(engine='genesis'if a.engine=='genesis-sph'else a.engine,implementation='provided example / independent environment replicas',physics_valid=valid,backend_observed='hip'if gpu else'cpu',envs=a.envs,workers=workers,requested_steps=a.steps,repeats=len(times),synchronized_rollout_s=times,median_s=median,build_s=build_s,scene_metadata=meta,checks=checks,scaling_mode='one GPU process per env',scope='provided model and physical settings; timed IPC barrier + rollout, warm-up/build/reset excluded unless episode auto-reset; validation outside timer')
  payload.update(steps=a.steps,dt=meta['dt'],env_step_per_s=a.envs*a.steps/median,step_per_s=a.steps/median,rtf_per_env=a.steps*meta['dt']/median)
 finally:
  for c in pipes:
   try:c.send(('stop',None))
   except Exception:pass
  for child in children:
   child.join(30)
   if child.is_alive():child.terminate();child.join()
  bad=[child.exitcode for child in children if child.exitcode!=0]
  if bad:raise RuntimeError('example worker cleanup/exit failed: '+str(bad))
 payload['worker_exitcodes']=[child.exitcode for child in children]
 print(('SMOKE_RESULT_JSON:'if a.smoke else'BENCHMARK_RESULT_JSON:')+json.dumps(payload),flush=True);return 0 if valid else 3
if __name__=='__main__':raise SystemExit(main())
