from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import os,pathlib,subprocess
R=run_root();S=storage_root();env=os.environ.copy();sdk=env['ROCM_PATH'];env.update(PYTHONPATH=str(S/expand_runtime('official-taichi/root${PYTHON_SITE_PACKAGES}')),PATH=sdk+'/lib/llvm/bin:'+env['PATH'],LD_LIBRARY_PATH=sdk+'/lib:'+sdk+'/lib/llvm/lib:'+str(S/'tools/lib'),PYOPENGL_PLATFORM='egl',EGL_PLATFORM='surfaceless',LIBGL_ALWAYS_SOFTWARE='1',MESA_LOADER_DRIVER_OVERRIDE='llvmpipe',LIBGL_DRIVERS_PATH=str(S/'tools/lib/dri'),__EGL_VENDOR_LIBRARY_FILENAMES=str(S/'tools/share/glvnd/egl_vendor.d/50_mesa.json'))
raise SystemExit(subprocess.run(['python3',str(R/'run_remote.py'),'--engine','fluidlab','--case','provided-fluidlab-actual-capture','--gpu','--wait','--timeout','900','--',str(S/'venvs/taichi/bin/python'),str(R/'capture_provided_fluidlab.py')],env=env,timeout=18000).returncode)
