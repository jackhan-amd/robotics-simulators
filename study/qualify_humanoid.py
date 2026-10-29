"""Instrumented 1000-step contact/solver validation, separate from throughput timing."""
from workspace import expand_runtime, run_root, runtime_path
import json,os,pathlib
import mujoco,mujoco_warp as mjw,numpy as np,warp as wp
R=run_root();path=R/'storage/upstream/mujoco-warp-amd/benchmarks/humanoid/humanoid.xml';wp.config.kernel_cache_dir=os.environ['STUDY_WARP_CACHE'];wp.init();device=wp.get_device('cuda:0');assert device.is_hip and 'MI355X'in device.name;wp.set_device(device)
model=mujoco.MjModel.from_xml_path(str(path));cpu=mujoco.MjData(model)
if model.nkey:mujoco.mj_resetDataKeyframe(model,cpu,0)
m=mjw.put_model(model);d=mjw.put_data(model,cpu,nworld=1,nconmax=24,njmax=64);finite=True;max_contacts=0;max_constraints=0;contact_steps=0;penetration=0.;parity=0.
for i in range(1000):
 mjw.step(m,d);wp.synchronize_device(device);q=d.qpos.numpy();v=d.qvel.numpy();n=int(d.nacon.numpy()[0]);constraints=int(d.nefc.numpy()[0]);max_contacts=max(max_contacts,n);max_constraints=max(max_constraints,constraints);contact_steps+=int(n>0);finite=finite and bool(np.isfinite(q).all()and np.isfinite(v).all())
 if n:penetration=min(penetration,float(d.contact.dist.numpy()[:min(n,24)].min()))
 if i<20:mujoco.mj_step(model,cpu);parity=max(parity,float(np.max(abs(q[0]-cpu.qpos))))
time_error=abs(float(d.time.numpy()[0])-5.)
gates=dict(finite=finite,cpu_initial_parity=parity<.01,contact_present=contact_steps>0,contact_capacity=max_contacts<24,constraint_capacity=max_constraints<64,contact_penetration=penetration>=-.05,time=time_error<.001)
print('SMOKE_RESULT_JSON:'+json.dumps(dict(engine='mujoco',case='humanoid_1000_step_qualification',implementation='MJWarp official Humanoid',backend_observed='hip',physics_valid=all(gates.values()),gates=gates,metrics=dict(max_contacts=max_contacts,max_constraints=max_constraints,contact_steps=contact_steps,min_contact_distance_m=penetration,initial_cpu_qpos_max_error=parity,time_error_s=time_error),steps=1000,dt=.005,envs=1,scope='instrumented validation; excluded from throughput results')))
raise SystemExit(0 if all(gates.values())else 3)
