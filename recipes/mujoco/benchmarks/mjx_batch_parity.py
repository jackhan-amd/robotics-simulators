"""Compare supplied-model batched GPU states with a short CPU sanity reference."""
import hashlib,json
import jax,jax.numpy as jp,mujoco,numpy as np
from mujoco import mjx
from workspace import storage_root
assert jax.__version__=='0.12.0';jax.config.update('jax_enable_x64',False)
device=jax.devices('rocm')[0];assert'MI355X'in device.device_kind
source=storage_root()/'upstream/mujoco-warp-amd/benchmarks/humanoid/humanoid.xml'
model=mujoco.MjModel.from_xml_path(str(source));cpu=mujoco.MjData(model)
if model.nkey:mujoco.mj_resetDataKeyframe(model,cpu,0)
initial_ctrl_max_abs=float(np.max(abs(cpu.ctrl)))
mx=mjx.put_model(model,impl='jax');one=mjx.put_data(model,cpu,impl='jax')
for _ in range(20):mujoco.mj_step(model,cpu)
reference_q=cpu.qpos.copy();reference_v=cpu.qvel.copy();checks=[]
def rollout(data):
 def step(state,_):return jax.vmap(lambda d:mjx.step(mx,d))(state),None
 return jax.lax.scan(step,data,None,length=20)[0]
for n in(2048,4096,8192,16384,32768,65536):
 initial=jax.tree.map(lambda x:jp.broadcast_to(x,(n,)+x.shape),one)
 final=jax.jit(rollout)(initial);jax.block_until_ready(final)
 q=np.asarray(final.qpos);v=np.asarray(final.qvel);qerror=float(np.max(abs(q-reference_q)));verror=float(np.max(abs(v-reference_v)))
 valid=bool(np.isfinite(q).all()and np.isfinite(v).all()and qerror<1e-3 and verror<1e-2 and final.qpos.devices()=={device})
 checks.append(dict(envs=n,valid=valid,qpos_max_abs_error=qerror,qvel_max_abs_error=verror));print('BATCH_PARITY:'+json.dumps(checks[-1]),flush=True)
 del initial,final,q,v
valid=all(x['valid']for x in checks)
print('SMOKE_RESULT_JSON:'+json.dumps(dict(engine='mujoco',implementation='MJX 0.12 supplied Humanoid batched CPU parity',physics_valid=valid,backend_observed='rocm',device=device.device_kind,envs=65536,env_counts_tested=[x['envs']for x in checks],steps=20,dt=model.opt.timestep,model_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),initial_ctrl_max_abs=initial_ctrl_max_abs,jax=jax.__version__,mujoco=mujoco.__version__,qpos_tolerance=1e-3,qvel_tolerance=1e-2,checks=checks,scope='All batched GPU worlds compared with one 20-step CPU reference, unchanged supplied keyframe and physics. No CPU throughput measurement; short-horizon sanity only.')),flush=True)
raise SystemExit(0 if valid else 3)
