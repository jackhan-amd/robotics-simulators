"""Run a supplied GPU example through the catalog, with no CPU fallback."""
from workspace import script_command
import argparse,os,pathlib,subprocess,sys
from workspace import run_root,storage_root,expand_runtime
p=argparse.ArgumentParser();p.add_argument('engine',choices=['instinct','taichi','gsplat']);a=p.parse_args()
os.environ.setdefault('LAB_ROOT',os.environ['STUDY_RUN_ROOT'])
R=run_root();S=storage_root();(R/'evidence').mkdir(parents=True,exist_ok=True)
script=pathlib.Path(__file__).resolve().parent
env=os.environ.copy()
if a.engine=='taichi':
 env['PYTHONPATH']=str(S/expand_runtime('official-taichi/root${PYTHON_SITE_PACKAGES}'))
 sdk=env['ROCM_PATH'];env['PATH']=sdk+'/lib/llvm/bin:'+env['PATH'];env['LD_LIBRARY_PATH']=sdk+'/lib:'+sdk+'/lib/llvm/lib:'+str(S/'tools/lib')
 command=[*script_command('provided_replicas.py',str(S/'venvs/taichi/bin/python')),'--engine','taichi','--envs','1','--steps','100','--smoke']
elif a.engine=='gsplat':command=[*script_command('provided_gsplat_garden.py',str(S/'venvs/gsplat/bin/python')),'--envs','1','--smoke']
else:
 libero=S/'upstream/libero-provided';config=S/'private/libero-config';config.mkdir(parents=True,exist_ok=True);L=libero/'libero/libero'
 (config/'config.yaml').write_text('\n'.join(k+': '+str(v)for k,v in dict(benchmark_root=L,bddl_files=L/'bddl_files',init_states=L/'init_files',datasets=libero/'libero/datasets',assets=L/'assets').items())+'\n')
 sdk=env['ROCM_PATH'];env.update(PYTHONPATH=':'.join(map(str,[libero,S/'upstream/faster-action-models/simulate/python',S/'build/instinct-sim-libero/python'])),LIBERO_CONFIG_PATH=str(config),MUJOCO_GL='egl',PYOPENGL_PLATFORM='egl',EGL_PLATFORM='surfaceless',HP_RENDERER='rt',HP_OBS_LAG='2',HP_SUCCESS_MODE='robosuite',LD_LIBRARY_PATH=':'.join(map(str,[S/'build/instinct-sim-libero',S/'tools/lib',sdk+'/lib',sdk+'/lib/llvm/lib'])))
 command=[*script_command('provided_instinct_libero.py',str(S/'venvs/instinct-sim/bin/python')),'--envs','1','--smoke']
raise SystemExit(subprocess.run(command,env=env,timeout=850).returncode)
