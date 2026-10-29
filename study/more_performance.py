"""Continue remaining independent fluid/raster studies in one-GPU sequence."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import os,pathlib,subprocess
R=run_root();S=storage_root();sdk=os.environ['ROCM_PATH']
def run(engine,name,cmd,env):
 print('TASK',name,flush=True)
 return subprocess.run(['python3',str(R/'run_remote.py'),'--engine',engine,'--case',name,'--gpu','--wait','--timeout','900','--',*map(str,cmd)],env=env,timeout=7200).returncode
ge=os.environ.copy();ge.update(PYGLET_HEADLESS='1',PYOPENGL_PLATFORM='egl',EGL_PLATFORM='surfaceless',LIBGL_ALWAYS_SOFTWARE='1',MESA_LOADER_DRIVER_OVERRIDE='llvmpipe',LIBGL_DRIVERS_PATH=str(S/'tools/lib/dri'),__EGL_VENDOR_LIBRARY_FILENAMES=str(S/'tools/share/glvnd/egl_vendor.d/50_mesa.json'),LD_LIBRARY_PATH=sdk+'/lib:'+sdk+'/lib/llvm/lib:'+str(S/'tools/lib'))
for solver in ['sph','mpm']:
 for n in [3,10,20]:run('genesis',f'genesis-{solver}-edge-{n}',[S/'venvs/genesis-amdgpu/bin/python',R/'bench_genesis_fluid.py','--solver',solver,'--edge',str(n)],ge)
ti=os.environ.copy();ti.update(PYTHONPATH=str(S/expand_runtime('official-taichi/root${PYTHON_SITE_PACKAGES}')),PATH=sdk+'/lib/llvm/bin:'+ti['PATH'],LD_LIBRARY_PATH=sdk+'/lib:'+sdk+'/lib/llvm/lib:'+str(S/'tools/lib'))
smoke=run('fluidlab','fluidlab-api-final-smoke',[S/'venvs/taichi/bin/python',R/'repo/smokes/supplemental_fluidlab.py','--backend','hip','--source-root',S/'upstream/fluidlab-modern-api','--steps','10'],ti)
if smoke==0:
 for n in [3,10,20]:run('fluidlab',f'fluidlab-edge-{n}',[S/'venvs/taichi/bin/python',R/'bench_fluidlab.py','--edge',str(n)],ti)
gs=os.environ.copy();gs['LD_LIBRARY_PATH']=sdk+'/lib:'+sdk+'/lib/llvm/lib'
if run('gsplat','gsplat-final-smoke',[S/'venvs/gsplat/bin/python',R/'bench_gsplat.py','--smoke'],gs)==0:
 for n in [10000,100000]:
  for w,h in [(640,480),(1280,720)]:run('gsplat',f'gsplat-n{n}-{w}x{h}',[S/'venvs/gsplat/bin/python',R/'bench_gsplat.py','--gaussians',str(n),'--width',str(w),'--height',str(h)],gs)
