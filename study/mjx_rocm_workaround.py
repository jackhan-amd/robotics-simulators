"""Optional compiler barriers; no model parameters or physics formulas change."""
import functools

def install_com_velocity_barrier():
 import jax
 from mujoco.mjx._src import scan
 if getattr(scan.body_tree,'_study_com_velocity_barrier',False):return
 original=scan.body_tree
 @functools.wraps(original)
 def body_tree(model,fn,*args,**kwargs):
  if fn.__qualname__.startswith('com_vel.'):
   inner=fn
   @functools.wraps(inner)
   def fn(*items):
    result=inner(*items)
    return jax.tree.map(jax.lax.optimization_barrier,result)
  return original(model,fn,*args,**kwargs)
 body_tree._study_com_velocity_barrier=True
 scan.body_tree=body_tree
