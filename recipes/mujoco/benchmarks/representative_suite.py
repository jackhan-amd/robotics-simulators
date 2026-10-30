"""Smoke, then the agreed 1000-step articulated MuJoCo sweep."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import os,pathlib,subprocess
R=run_root();S=storage_root();py=S/'venvs/mjwarp-rocm/bin/python'
def task(n,smoke=False):
 name='humanoid-smoke'if smoke else f'humanoid-envs-{n}'
 cmd=['python3',str(R/'run_remote.py'),'--engine','mujoco','--case',name,'--gpu','--wait','--timeout','1800','--',str(py),str(R/'representative_mujoco.py'),'--envs',str(n),'--steps','1000']
 if smoke:cmd+=['--smoke']
 print('HUMANOID_TASK',name,flush=True);return subprocess.run(cmd,timeout=7200).returncode
if task(1,True)==0:
 for n in [2048,4096,8192,16384,32768,65536]:task(n)
