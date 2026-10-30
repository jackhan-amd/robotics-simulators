from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import os,pathlib,subprocess
R=run_root();S=storage_root();env=os.environ.copy()
env['PYTHONPATH']=str(S/'build/instinct-sim-libero/python');env['LD_LIBRARY_PATH']=str(S/'build/instinct-sim-libero')+':'+env['ROCM_PATH']+'/lib:'+env['ROCM_PATH']+'/lib/llvm/lib'
def run(n,smoke=False):
 cmd=['python3',str(R/'run_remote.py'),'--engine','instinct','--case','instinct-smoke'if smoke else f'instinct-envs-{n}','--gpu','--wait','--timeout','1200','--',str(S/'venvs/instinct-sim/bin/python'),str(R/'bench_instinct.py'),'--envs',str(n)]
 if smoke:cmd+=['--smoke']
 print('INSTINCT_TASK',n,smoke,flush=True);return subprocess.run(cmd,env=env,timeout=1300).returncode
rc=run(1,True)
if rc==0:
 for n in [2048,4096,8192,16384,32768,65536]:
  rc=run(n)
  if rc!=0:break
raise SystemExit(rc)
