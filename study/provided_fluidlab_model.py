"""Headless forward execution of the supplied MixingEnv, no custom scene."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import hashlib,os,pathlib,sys
import numpy as np
def example():
 import taichi as ti
 R=run_root();S=storage_root();src=S/'upstream/fluidlab-modern-api';sys.path.insert(0,str(src))
 import fluidlab.utils.misc as misc
 misc.is_on_server=lambda:True # Select upstream's existing headless server branch.
 original_init=ti.init
 def init(**kw):
  cache=S/'cache/provided-fluidlab'/str(os.getpid());cache.mkdir(parents=True,exist_ok=True)
  kw.pop('packed',None);kw.update(arch=ti.amdgpu,random_seed=0,cpu_max_num_threads=1,offline_cache=False,offline_cache_file_path=str(cache));original_init(**kw)
 ti.init=init
 try:from fluidlab.envs.mixing_env import MixingEnv
 finally:ti.init=original_init
 assert ti.lang.impl.get_runtime().prog.config().arch==ti.amdgpu
 env=MixingEnv(version=0,loss=False,seed=0);sim=env.taichi_env;sim.disable_grad();initial=sim.get_state();x0=initial['state']['x'].copy();mass0=float(sim.simulator.particles_i.mass.to_numpy().sum());action=np.zeros(env.agent.action_dim,dtype=np.float32)
 def reset():sim.set_state(**initial);ti.sync()
 reset.cleanup=ti.reset
 def advance(steps):
  for _ in range(steps):sim.step(action)
  ti.sync()
 def check():
  state=sim.simulator.get_state();x=state['x'];v=state['v'];mass=float(sim.simulator.particles_i.mass.to_numpy().sum());disp=float(abs(x-x0).max())
  return dict(valid=bool(np.isfinite(x).all()and np.isfinite(v).all()and len(x)==len(x0)and abs(mass-mass0)<=abs(mass0)*1e-6 and x.min()>-.1 and x.max()<1.1 and disp>1e-6),particles=len(x),mass_error=abs(mass-mass0),max_displacement=disp)
 source=src/'fluidlab/envs/mixing_env.py';m=sim.simulator
 meta=dict(model='provided MixingEnv coffee/milk + cup + supplied agent',version='FluidLab 7295eb6; Taichi '+str(ti.__version__),source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),dt=float(m.dt*m.n_substeps),substeps=int(m.n_substeps),particles=len(x0),changes='explicit AMD backend, removed obsolete packed init argument, upstream headless server branch, loss/gradients disabled; stationary zero-action driver; geometry/material/grid/agent/boundaries unchanged',timing_scope='forward TaichiEnv.step; no renderer, RL observation/reward, optimizer or host readback inside timing')
 return reset,advance,check,meta
