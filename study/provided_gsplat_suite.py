from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import os,pathlib,subprocess
R=run_root();S=storage_root();os.environ['LD_LIBRARY_PATH']=os.environ['ROCM_PATH']+'/lib:'+os.environ['ROCM_PATH']+'/lib/llvm/lib'
def run(n,smoke=False):
 name='provided-garden-smoke'if smoke else f'provided-garden-envs-{n}';cmd=['python3',str(R/'run_remote.py'),'--engine','gsplat','--case',name,'--gpu','--wait','--timeout','1200','--',str(S/'venvs/gsplat/bin/python'),str(R/'provided_gsplat_garden.py'),'--envs',str(n)]
 if smoke:cmd+=['--smoke']
 print('PROVIDED_GARDEN_TASK',name,flush=True);return subprocess.run(cmd,timeout=1300).returncode
rc=run(1,True)
if rc==0:
 for n in [1,2,4,8,16,32]:
  rc=run(n)
  if rc:break
raise SystemExit(rc)
