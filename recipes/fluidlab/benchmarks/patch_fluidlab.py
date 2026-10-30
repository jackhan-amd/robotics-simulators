"""Replace removed scalar-struct .fill API with equivalent explicit zero assignments."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import difflib,hashlib,json,pathlib,shutil
R=run_root();S=storage_root();original=S/'upstream/fluidlab';dest=S/'upstream/fluidlab-modern-api'
if not dest.exists():shutil.copytree(original,dest,ignore=shutil.ignore_patterns('.git','__pycache__'))
p=dest/'fluidlab/fluidengine/simulators/mpm_simulator.py';before=(original/'fluidlab/fluidengine/simulators/mpm_simulator.py').read_text();after=before
replacements={}
for grad in ['','.grad']:
 key=f'self.grid{grad}[f, I].fill(0)'
 replacements[key]='\n            '.join([f'self.grid{grad}[f, I].v_in = ti.Vector.zero(DTYPE_TI, self.dim)',f'self.grid{grad}[f, I].mass = 0.0',f'self.grid{grad}[f, I].v_out = ti.Vector.zero(DTYPE_TI, self.dim)'])
 key=f'self.bodies{grad}[body_id].fill(0)'
 replacements[key]='\n                '.join([f'self.bodies{grad}[body_id].{name} = ti.Vector.zero(DTYPE_TI, self.dim)'for name in ['COM_t0','COM_t1']]+[f'self.bodies{grad}[body_id].{name} = ti.Matrix.zero(DTYPE_TI, self.dim, self.dim)'for name in ['H','R','U','S','V']])
replacements['self.particles.grad[i, j].fill(0)']='\n            '.join([f'self.particles.grad[i, j].{name} = ti.Vector.zero(DTYPE_TI, self.dim)'for name in ['x','v']]+[f'self.particles.grad[i, j].{name} = ti.Matrix.zero(DTYPE_TI, self.dim, self.dim)'for name in ['C','F','F_tmp','U','V','S']])
for old,new in replacements.items():assert old in after;after=after.replace(old,new)
after=after.replace('self.agent = agent','self.agent = agent\n        self.has_agent = agent is not None')
after=after.replace('self.smoke_field = smoke_field','self.smoke_field = smoke_field\n        self.has_smoke_field = smoke_field is not None')
after=after.replace('ti.static(self.agent is not None)','ti.static(self.has_agent)').replace('ti.static(self.agent is None)','ti.static(not self.has_agent)')
after=after.replace('ti.static(self.smoke_field is not None)','ti.static(self.has_smoke_field)')
p.write_text(after)
(R/'evidence/fluidlab-modern-api.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='original/mpm_simulator.py',tofile='modern-api/mpm_simulator.py')))
(R/'evidence/fluidlab-patch-receipt.json').write_text(json.dumps(dict(before_sha256=hashlib.sha256(before.encode()).hexdigest(),after_sha256=hashlib.sha256(after.encode()).hexdigest(),scope='struct zero-initialization only, no solver mathematics changed'),indent=2))
print('Prepared',dest)
