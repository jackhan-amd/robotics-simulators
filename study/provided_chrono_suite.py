from workspace import expand_runtime, run_root, runtime_path
import os,pathlib,subprocess
R=run_root()
for kind in ['fsi','dem']:
 if os.environ.get('PROVIDED_CHRONO_KIND')and os.environ['PROVIDED_CHRONO_KIND']!=kind:continue
 def run(n,smoke=False):
  name=f'provided-chrono-{kind}-smoke'if smoke else f'provided-chrono-{kind}-envs-{n}';cmd=['python3',str(R/'run_remote.py'),'--engine','chrono','--case',name,'--gpu','--wait','--timeout','2400','--','python3',str(R/'provided_chrono_replicas.py'),'--kind',kind,'--envs',str(n)]
  if smoke:cmd+=['--smoke']
  print('PROVIDED_CHRONO_TASK',name,flush=True);return subprocess.run(cmd,timeout=2500).returncode
 if os.environ.get('PROVIDED_CHRONO_SMOKE_ALREADY_QUALIFIED')=='1' or run(1,True)==0:
  for n in map(int,os.environ.get('PROVIDED_CHRONO_ENVS','1,2,4,8').split(',')):
   run(n)
