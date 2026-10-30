"""Sequential remaining bounded performance series; each action retains its own evidence."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import os,pathlib,subprocess
R=run_root();S=storage_root();base_env=os.environ.copy()
def run(engine,name,command,env=None,gpu=True,timeout=900):
 cmd=['python3',str(R/'run_remote.py'),'--engine',engine,'--case',name,'--wait','--timeout',str(timeout)]
 if gpu:cmd+=['--gpu']
 print('PERFORMANCE_TASK',name,flush=True)
 return subprocess.run(cmd+['--',*map(str,command)],env=env or base_env,timeout=3600).returncode
sdk=base_env['ROCM_PATH'];native=base_env.copy();native['LD_LIBRARY_PATH']=sdk+'/lib:'+sdk+'/lib/llvm/lib:'+str(S/'build/chrono-hip-devel/lib')
rc=run('chrono','chrono-dem-smoke',[S/'build/chrono-smoke-hip/chrono_dem_smoke','50'],native)
run('chrono','chrono-fsi-bench',['python3',R/'native_bench.py','chrono-fsi'],native)
if rc==0:run('chrono','chrono-dem-bench',['python3',R/'native_bench.py','chrono-dem'],native)
ti=base_env.copy();ti.update(PYTHONPATH=str(S/expand_runtime('official-taichi/root${PYTHON_SITE_PACKAGES}')),PATH=sdk+'/lib/llvm/bin:'+ti['PATH'],LD_LIBRARY_PATH=sdk+'/lib:'+sdk+'/lib/llvm/lib')
for n in [1024,65536,1048576]:run('taichi',f'taichi-particles-{n}',[S/'venvs/taichi/bin/python',R/'bench_taichi.py','--particles',str(n)],ti)
ge=base_env.copy();ge.update(PYGLET_HEADLESS='1',PYOPENGL_PLATFORM='egl',EGL_PLATFORM='surfaceless',LIBGL_ALWAYS_SOFTWARE='1',MESA_LOADER_DRIVER_OVERRIDE='llvmpipe',LIBGL_DRIVERS_PATH=str(S/'tools/lib/dri'),__EGL_VENDOR_LIBRARY_FILENAMES=str(S/'tools/share/glvnd/egl_vendor.d/50_mesa.json'),LD_LIBRARY_PATH=sdk+'/lib:'+sdk+'/lib/llvm/lib:'+str(S/'tools/lib'))
for n in [1,64,256,1024]:run('genesis',f'genesis-rigid-envs-{n}',[S/'venvs/genesis-amdgpu/bin/python',R/'bench_genesis.py','--envs',str(n)],ge)
