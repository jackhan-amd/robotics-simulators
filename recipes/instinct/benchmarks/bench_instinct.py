"""Bounded independent physics check and synchronized Instinct Sim sweep."""
from workspace import expand_runtime, run_root, runtime_path
import argparse,hashlib,json,pathlib,statistics,time
import instinct_sim as sim,mujoco,numpy as np
p=argparse.ArgumentParser();p.add_argument('--envs',type=int,default=1);p.add_argument('--steps',type=int,default=1000);p.add_argument('--smoke',action='store_true');a=p.parse_args()
path=runtime_path('${LAB_ROOT}/repo/configs/freefall.xml');xml=path.read_text();m=sim.PhysicsModel.from_xml(xml);e=sim.PhysicsEngine();start=time.perf_counter();assert e.init(m,a.envs,0);e.sync();build_s=time.perf_counter()-start
assert (m.nq,m.nv,m.nbody,m.ngeom)==(7,6,2,2)
dt=m.timestep;opt=e.options;options={k:str(getattr(opt,k))for k in ['solver','iterations','tolerance','enable_contact','enable_limits']}
cpu_m=mujoco.MjModel.from_xml_string(xml);cpu=mujoco.MjData(cpu_m)
initial=e.read_state()[0];early=[];contacts=[];samples=[]
if a.smoke:
 for i in range(500):
  e.step();e.sync();q=e.read_state()[0];v=e.data.read_qvel();c=e.data.read_contacts();mujoco.mj_step(cpu_m,cpu)
  if i<50:early.append(float(abs(q[0]-cpu.qpos).max()))
  contacts.append(int(np.max(c['ncon'])));samples.append(float(q[0,2]))
 # Parsed model parameters are float32: 9.81 cannot meet a 1e-8 double-literal comparison.
 gates=dict(finite=bool(np.isfinite(q).all()and np.isfinite(v).all()),early_cpu_parity=max(early)<.002,contact_occurred=max(contacts)>0,penetration=min(samples)>=.04,final_height=abs(float(q[0,2])-.05)<.03,fall=float(q[0,2])<float(initial[0,2])-.1,gravity=abs(m.gravity[2]+9.81)<1e-6,dt=abs(dt-.001)<1e-10)
 payload=dict(engine='instinct',implementation='AMD Instinct Sim / LIBERO preset',physics_valid=all(gates.values()),gates=gates,backend_observed='hip',envs=a.envs,steps=500,dt=dt,early_cpu_qpos_error=max(early),max_contacts=max(contacts),min_center_z=min(samples),final_z=float(q[0,2]),solver_options=options,mujoco=mujoco.__version__,build_s=build_s,model_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
 payload.update(gravity_observed=list(m.gravity),gravity_parameter_abs_tolerance=1e-6)
 print('SMOKE_RESULT_JSON:'+json.dumps(payload));raise SystemExit(0 if payload['physics_valid']else 3)
start=time.perf_counter();e.step_n(1000);e.sync();warmup_s=time.perf_counter()-start;times=[];checks=[]
for rep in range(5):
 e.reset();e.sync();start=time.perf_counter();e.step_n(a.steps);e.sync();times.append(time.perf_counter()-start)
 q=e.read_state()[0];v=e.data.read_qvel();c=e.data.read_contacts();checks.append(bool(np.isfinite(q).all()and np.isfinite(v).all()and(q[:,2]>=.04).all()and(q[:,2]<initial[:,2]-.1).all()and np.min(c['ncon'])>0))
median=statistics.median(times)
print('BENCHMARK_RESULT_JSON:'+json.dumps(dict(engine='instinct',implementation='AMD Instinct Sim / LIBERO preset',backend_observed='hip',physics_valid=all(checks),checks=checks,scene='repository_sphere_plane',source_commit='a5fa73101988870e51f04fe1e7be5da56dda3841',envs=a.envs,steps=a.steps,repeats=5,dt=dt,build_s=build_s,compile_s=build_s,warmup_s=warmup_s,warmup_steps=1000,synchronized_rollout_s=times,median_s=median,env_step_per_s=a.envs*a.steps/median,step_per_s=a.steps/median,rtf_per_env=a.steps*dt/median,solver_options=options,state_readback_dtype=str(q.dtype),readback_in_timing=False,execution='native step_n(1000), engine.sync at boundaries; renderer and policy absent',mujoco=mujoco.__version__,model_sha256=hashlib.sha256(path.read_bytes()).hexdigest())))
raise SystemExit(0 if all(checks)else 3)
