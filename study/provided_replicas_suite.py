from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import os,pathlib,subprocess
R=run_root();S=storage_root();base=os.environ.copy();sdk=base['ROCM_PATH']
for engine in ['taichi','genesis-sph','fluidlab']:
 if os.environ.get('PROVIDED_ENGINE')and os.environ['PROVIDED_ENGINE']!=engine:continue
 env=base.copy();py=S/'venvs'/('genesis-amdgpu'if engine=='genesis-sph'else'taichi')/'bin/python'
 if engine=='genesis-sph':env.update(PYGLET_HEADLESS='1',PYOPENGL_PLATFORM='egl',EGL_PLATFORM='surfaceless',LIBGL_ALWAYS_SOFTWARE='1',MESA_LOADER_DRIVER_OVERRIDE='llvmpipe',LIBGL_DRIVERS_PATH=str(S/'tools/lib/dri'),__EGL_VENDOR_LIBRARY_FILENAMES=str(S/'tools/share/glvnd/egl_vendor.d/50_mesa.json'),LD_LIBRARY_PATH=sdk+'/lib:'+sdk+'/lib/llvm/lib:'+str(S/'tools/lib'))
 if engine in('taichi','fluidlab'):env.update(PYTHONPATH=str(S/expand_runtime('official-taichi/root${PYTHON_SITE_PACKAGES}')),PATH=sdk+'/lib/llvm/bin:'+env['PATH'],LD_LIBRARY_PATH=sdk+'/lib:'+sdk+'/lib/llvm/lib:'+str(S/'tools/lib'))
 if engine=='fluidlab':env.update(PYOPENGL_PLATFORM='egl',EGL_PLATFORM='surfaceless',LIBGL_ALWAYS_SOFTWARE='1',MESA_LOADER_DRIVER_OVERRIDE='llvmpipe',LIBGL_DRIVERS_PATH=str(S/'tools/lib/dri'),__EGL_VENDOR_LIBRARY_FILENAMES=str(S/'tools/share/glvnd/egl_vendor.d/50_mesa.json'))
 def run(n,smoke=False):
  name=f'provided-{engine}-smoke'if smoke else f'provided-{engine}-envs-{n}';cmd=['python3',str(R/'run_remote.py'),'--engine','genesis'if engine=='genesis-sph'else engine,'--case',name,'--wait','--timeout','1800']
  if engine in('taichi','genesis-sph','fluidlab'):cmd+=['--gpu']
  cmd+=['--',str(py),str(R/'provided_replicas.py'),'--engine',engine,'--envs',str(n),'--steps','100'if engine in('genesis-sph','fluidlab')else'1000']
  if smoke:cmd+=['--smoke']
  print('PROVIDED_REPLICA_TASK',name,flush=True);return subprocess.run(cmd,env=env,timeout=1900).returncode
 if run(1,True)==0:
  for n in ([1,2,4,8]if engine in('genesis-sph','fluidlab')else[1,2,4,8,16]):
   if run(n)!=0:break
