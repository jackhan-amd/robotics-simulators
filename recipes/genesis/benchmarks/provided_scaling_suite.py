"""Sequential, bounded execution of the provided Franka native env sweep."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import os,pathlib,subprocess
R=run_root();S=storage_root();env=os.environ.copy();sdk=env['ROCM_PATH']
env.update(PYGLET_HEADLESS='1',PYOPENGL_PLATFORM='egl',EGL_PLATFORM='surfaceless',LIBGL_ALWAYS_SOFTWARE='1',MESA_LOADER_DRIVER_OVERRIDE='llvmpipe',LIBGL_DRIVERS_PATH=str(S/'tools/lib/dri'),__EGL_VENDOR_LIBRARY_FILENAMES=str(S/'tools/share/glvnd/egl_vendor.d/50_mesa.json'),LD_LIBRARY_PATH=sdk+'/lib:'+sdk+'/lib/llvm/lib:'+str(S/'tools/lib'))
def run(n,smoke=False):
 name='provided-franka-smoke'if smoke else f'provided-franka-envs-{n}';cmd=['python3',str(R/'run_remote.py'),'--engine','genesis','--case',name,'--gpu','--wait','--timeout','1200','--',str(S/'venvs/genesis-amdgpu/bin/python'),str(R/'provided_genesis_franka.py'),'--envs',str(n),'--steps','1000']
 if smoke:cmd+=['--smoke']
 print('PROVIDED_FRANKA_TASK',name,flush=True);return subprocess.run(cmd,env=env,timeout=1300).returncode
rc=run(1,True)
if rc==0:
 for n in [1,16,64,256,1024,2048,4096,8192,16384,32768,65536]:
  rc=run(n)
  if rc:break
raise SystemExit(rc)
