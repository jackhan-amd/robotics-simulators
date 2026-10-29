"""Replay supplied examples on the GPU; camera frames never enter timing data."""
from workspace import expand_runtime, run_root, runtime_path
import argparse,hashlib,json,pathlib,runpy,sys
import genesis as gs,numpy as np,quadrants as qd,torch
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('case',choices=['franka','sph']);a=p.parse_args();R=run_root();source=R/'storage/upstream/genesis-world/examples'/('rigid/single_franka_envs.py'if a.case=='franka'else'coupling/sph_rigid.py');captured={};cameras=[]
class Ready(Exception):pass
old_init=gs.init;old_build=gs.Scene.build;old_camera=gs.Scene.add_camera
def init(**kw):kw.update(backend=gs.amdgpu,logging_level='warning');old_init(**kw)
def camera(self,*args,**kw):c=old_camera(self,*args,**kw);cameras.append(c);return c
def build(self,*args,**kw):
 if not cameras:camera(self,res=(960,640),pos=(3,-3,2.5),lookat=(.5,0,1),GUI=False)
 old_build(self,*args,**kw);captured['scene']=self;raise Ready()
gs.init=init;gs.Scene.build=build;gs.Scene.add_camera=camera;sys.argv=[str(source)]+(['-g','-b','1','-s','1000']if a.case=='franka'else[])
try:runpy.run_path(str(source),run_name='__main__')
except Ready:pass
finally:gs.init=old_init;gs.Scene.build=old_build;gs.Scene.add_camera=old_camera
scene=captured['scene'];stop=1000 if a.case=='franka'else 100;frames=[]
for step in range(stop+1):
 if step in(0,stop):
  qd.sync();torch.cuda.synchronize();rgb,*_=cameras[0].render(rgb=True);name=f'genesis-provided-{a.case}-{step:04d}.png';Image.fromarray(rgb).save(R/'evidence'/name);frames.append(dict(file=name,step=step,time_s=step*float(scene.dt)))
 if step<stop:scene.step()
valid=True
for e in scene.entities:
 if hasattr(e,'get_particles_pos'):valid=valid and bool(np.isfinite(e.get_particles_pos().detach().cpu().numpy()).all())
meta=dict(engine='genesis',physics_valid=valid,backend_observed='hip',provided_case=a.case,source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),frames=frames,scope='supplied example scene/physics unchanged; 1 GPU environment replay; camera only added if absent; offscreen capture excluded from all performance timers')
(R/f'evidence/genesis-provided-{a.case}-capture.json').write_text(json.dumps(meta,indent=2));print('SMOKE_RESULT_JSON:'+json.dumps(meta));gs.destroy();raise SystemExit(0 if valid else 3)
