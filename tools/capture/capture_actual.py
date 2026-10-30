"""Capture actual replay frames separately from all timed measurements."""
from workspace import expand_runtime, run_root, runtime_path
import argparse,json,pathlib
p=argparse.ArgumentParser();p.add_argument('engine',choices=['mujoco','genesis']);a=p.parse_args()
R=run_root();O=R/'evidence'
if a.engine=='mujoco':
 import os,mujoco,mujoco_warp as mjw,warp as wp,numpy as np
 from PIL import Image
 wp.config.kernel_cache_dir=os.environ['STUDY_WARP_CACHE'];wp.init();device=wp.get_device('cuda:0');assert device.is_hip;wp.set_device(device)
 path=R/'storage/upstream/mujoco-warp-amd/benchmarks/humanoid/humanoid.xml';m=mujoco.MjModel.from_xml_path(str(path));cpu=mujoco.MjData(m);mujoco.mj_resetDataKeyframe(m,cpu,0);wm=mjw.put_model(m);d=mjw.put_data(m,cpu,nworld=1,nconmax=24,njmax=64)
 m.vis.global_.offwidth=960;m.vis.global_.offheight=640;renderer=mujoco.Renderer(m,height=640,width=960);cam=mujoco.MjvCamera();cam.distance=3.4;cam.azimuth=135;cam.elevation=-18;cam.lookat[:]=[0,0,.75]
 frames=[]
 for step in range(1001):
  if step in (0,100,1000):
   wp.synchronize_device(device);cpu.qpos[:]=d.qpos.numpy()[0];cpu.qvel[:]=d.qvel.numpy()[0];mujoco.mj_forward(m,cpu);renderer.update_scene(cpu,camera=cam);name=f'mujoco-actual-humanoid-{step:04d}.png';Image.fromarray(renderer.render()).save(O/name);frames.append(dict(file=name,step=step,time_s=step*m.opt.timestep))
  if step<1000:mjw.step(wm,d)
 renderer.close();valid=bool(np.isfinite(d.qpos.numpy()).all())
 meta=dict(engine='mujoco',physics_valid=valid,frames=frames,model_source=str(path),physics='MJWarp HIP, 1 world, same keyframe/zero controls as benchmark',render='MuJoCo offscreen software EGL; capture replay excluded from throughput')
else:
 import genesis as gs,torch,numpy as np,quadrants as qd
 gs.init(backend=gs.amdgpu,precision='32',seed=0,logging_level='warning')
 scene=gs.Scene(sim_options=gs.options.SimOptions(dt=.001,substeps=2),sph_options=gs.options.SPHOptions(lower_bound=(-1,-1,0),upper_bound=(1,1,2),particle_size=.04,hash_grid_cell_size=.08),show_viewer=False)
 scene.add_entity(gs.morphs.Plane());water=scene.add_entity(morph=gs.morphs.Box(pos=(0,0,1),size=(.4,)*3),material=gs.materials.SPH.Liquid(sampler='regular',mu=.01));cam=scene.add_camera(res=(960,640),pos=(2,2,1.8),lookat=(0,0,.8),GUI=False);scene.build();frames=[]
 from PIL import Image
 for step in range(101):
  if step in(0,100):
   qd.sync();torch.cuda.synchronize();rgb,*_=cam.render(rgb=True);name=f'genesis-actual-sph-{step:04d}.png';Image.fromarray(rgb).save(O/name);frames.append(dict(file=name,step=step,time_s=step*.001))
  if step<100:scene.step()
 valid=bool(np.isfinite(water.get_particles_pos().detach().cpu().numpy()).all());meta=dict(engine='genesis',physics_valid=valid,frames=frames,physics='Genesis AMD SPH, 1000 particles, dt .001, substeps 2; same benchmark scene',render='Genesis camera offscreen replay; excluded from throughput');gs.destroy()
(O/(a.engine+'-actual-capture.json')).write_text(json.dumps(meta,indent=2));print('SMOKE_RESULT_JSON:'+json.dumps(meta))
