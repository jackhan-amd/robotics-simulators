"""Sequential Genesis physics checks using software EGL only for context setup."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import os,pathlib,subprocess
R=run_root();S=storage_root();py=S/'venvs/genesis-amdgpu/bin/python'
os.environ.update(PYGLET_HEADLESS='1',PYOPENGL_PLATFORM='egl',EGL_PLATFORM='surfaceless',LIBGL_ALWAYS_SOFTWARE='1',MESA_LOADER_DRIVER_OVERRIDE='llvmpipe',LIBGL_DRIVERS_PATH=str(S/'tools/lib/dri'),__EGL_VENDOR_LIBRARY_FILENAMES=str(S/'tools/share/glvnd/egl_vendor.d/50_mesa.json'))
os.environ['LD_LIBRARY_PATH']=os.environ['ROCM_PATH']+'/lib:'+os.environ['ROCM_PATH']+'/lib/llvm/lib:'+str(S/'tools/lib')
cases=[('articulation',['recipes/genesis/smoke_rigid.py','--backend','amdgpu','--case','articulation']),('contact',['recipes/genesis/smoke_rigid.py','--backend','amdgpu','--case','contacts','--steps','2000','--sustained'])]
for solver in ['sph','mpm','coupling']:
 args=['recipes/genesis/smoke_fluid.py','--backend','amdgpu','--solver',solver,'--steps','50']
 if solver!='mpm':args+=['--mass-readout','static_info']
 cases.append((solver,args))
for name,args in cases:
 print('GENESIS_SMOKE',name,flush=True)
 subprocess.run(['python3',str(R/'run_remote.py'),'--engine','genesis','--case','genesis-'+name+'-smoke','--gpu','--timeout','900','--',str(py),*args],timeout=960)
