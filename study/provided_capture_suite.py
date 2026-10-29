from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import os,pathlib,subprocess
R=run_root();S=storage_root();e=os.environ.copy();sdk=e['ROCM_PATH'];e.update(PYGLET_HEADLESS='1',PYOPENGL_PLATFORM='egl',EGL_PLATFORM='surfaceless',LIBGL_ALWAYS_SOFTWARE='1',MESA_LOADER_DRIVER_OVERRIDE='llvmpipe',LIBGL_DRIVERS_PATH=str(S/'tools/lib/dri'),__EGL_VENDOR_LIBRARY_FILENAMES=str(S/'tools/share/glvnd/egl_vendor.d/50_mesa.json'),LD_LIBRARY_PATH=sdk+'/lib:'+sdk+'/lib/llvm/lib:'+str(S/'tools/lib'))
for case in ['franka','sph']:
 subprocess.run(['python3',str(R/'run_remote.py'),'--engine','genesis','--case','provided-capture-'+case,'--gpu','--wait','--timeout','900','--',str(S/'venvs/genesis-amdgpu/bin/python'),str(R/'capture_provided_genesis.py'),case],env=e,timeout=18000)
