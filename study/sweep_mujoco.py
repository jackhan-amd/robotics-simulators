"""Run requested MuJoCo environment sizes sequentially, recording each independently."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import argparse,os,pathlib,subprocess
p=argparse.ArgumentParser();p.add_argument('backend',choices=['mjx','mjwarp']);a=p.parse_args()
R=run_root();S=storage_root();v=S/'venvs'/('mujoco-mjx-rocm' if a.backend=='mjx' else 'mjwarp-rocm')
for n in [2048,4096,8192,16384,32768,65536]:
 print('START',a.backend,n,flush=True)
 cmd=['python3',str(R/'run_remote.py'),'--engine','mujoco','--case',f'{a.backend}-envs-{n}','--gpu','--timeout','1200','--',str(v/'bin/python'),str(R/('bench_mjx.py' if a.backend=='mjx' else 'bench_mjwarp.py')),'--envs',str(n)]
 rc=subprocess.run(cmd,timeout=1250).returncode
 print('FINISH',a.backend,n,'rc',rc,flush=True)
