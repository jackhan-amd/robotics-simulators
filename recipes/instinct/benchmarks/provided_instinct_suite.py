from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import json,os,pathlib,subprocess
R=run_root();S=storage_root();env=os.environ.copy();sdk=env['ROCM_PATH'];libero=S/'upstream/libero-provided';config=S/'private/libero-config';config.mkdir(exist_ok=True);L=libero/'libero/libero'
(config/'config.yaml').write_text('\n'.join(k+': '+str(v)for k,v in dict(benchmark_root=L,bddl_files=L/'bddl_files',init_states=L/'init_files',datasets=libero/'libero/datasets',assets=L/'assets').items())+'\n')
env.update(PYTHONPATH=':'.join(map(str,[libero,S/'upstream/faster-action-models/simulate/python',S/'build/instinct-sim-libero/python'])),LIBERO_CONFIG_PATH=str(config),MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',MESA_LOADER_DRIVER_OVERRIDE='llvmpipe',LIBGL_DRIVERS_PATH=str(S/'tools/lib/dri'),HP_RENDERER='rt',HP_OBS_LAG='2',HP_SUCCESS_MODE='robosuite',LD_LIBRARY_PATH=':'.join(map(str,[S/'build/instinct-sim-libero',S/'tools/lib',sdk+'/lib',sdk+'/lib/llvm/lib'])))
env.update(MUJOCO_GL='egl',PYOPENGL_PLATFORM='egl',EGL_PLATFORM='surfaceless',__EGL_VENDOR_LIBRARY_FILENAMES=str(S/'tools/share/glvnd/egl_vendor.d/50_mesa.json'))
def run(n,smoke=False):
 case='provided-instinct-libero-smoke'if smoke else f'provided-instinct-libero-envs-{n}';cmd=['python3',str(R/'run_remote.py'),'--engine','instinct','--case',case,'--gpu','--wait','--timeout','1800','--',str(S/'venvs/instinct-sim/bin/python'),str(R/'provided_instinct_libero.py'),'--envs',str(n)]
 if smoke:cmd+=['--smoke']
 print('PROVIDED_INSTINCT_TASK',case,flush=True);return subprocess.run(cmd,env=env,timeout=18000).returncode
if run(1,True)==0:
 for n in [1,2,4,8,16,32]:
  if run(n)!=0:break
