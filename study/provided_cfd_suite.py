from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import os,pathlib,subprocess
R=run_root();S=storage_root();env=os.environ.copy();sdk=env['ROCM_PATH'];env['LD_LIBRARY_PATH']=sdk+'/lib:'+sdk+'/lib/llvm/lib:'+str(S/'tools/lib')
for engine in ['incflo','nekrs']:
 if os.environ.get('PROVIDED_CFD_ENGINE')and os.environ['PROVIDED_CFD_ENGINE']!=engine:continue
 def run(n,smoke=False):
  windowed=engine=='nekrs'and os.environ.get('PROVIDED_CFD_WINDOWS')=='1';prefix=engine+'-windows'if windowed else engine
  case=f'provided-{prefix}-smoke'if smoke else f'provided-{prefix}-envs-{n}';py=str(S/'venvs/incflo-tools/bin/python')if engine=='incflo'else'python3';script='provided_nekrs_windows.py'if windowed else f'provided_{engine}.py';cmd=['python3',str(R/'run_remote.py'),'--engine',engine,'--case',case,'--gpu','--wait','--timeout','4800','--',py,str(R/script),'--envs',str(n)]
  if smoke:cmd+=['--smoke']
  print('PROVIDED_CFD_TASK',case,flush=True);return subprocess.run(cmd,env=env,timeout=18000).returncode
 if os.environ.get('PROVIDED_CFD_SMOKE_ALREADY_QUALIFIED')=='1' or run(1,True)==0:
  for n in map(int,os.environ.get('PROVIDED_CFD_ENVS','1,2,4,8').split(',')):
   run(n)
