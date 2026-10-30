"""Install one GPU backend in a study-owned prefix; preserve base SDK/Torch."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import argparse,os,pathlib,subprocess
p=argparse.ArgumentParser();p.add_argument('engine',choices=['genesis','mjx','taichi','warp','gsplat']);a=p.parse_args()
R=run_root();S=storage_root();uv=R/'bin/uv';tools=S/'tools/bin';base=S/'venvs/base/bin'
os.environ['PATH']=str(base)+':'+str(tools)+':'+os.environ['PATH']
def run(args,timeout=1200,cwd=None):
 print('+',*map(str,args),flush=True);subprocess.run(list(map(str,args)),check=True,timeout=timeout,cwd=cwd)
name={'genesis':'genesis-amdgpu','mjx':'mujoco-mjx-rocm','taichi':'taichi','warp':'mjwarp-rocm','gsplat':'gsplat'}[a.engine];v=S/'venvs'/name
if not v.exists():run([uv,'venv','--system-site-packages','--python','/usr/bin/python3',v])
def pip(*pkgs):run([uv,'pip','install','--python',v/'bin/python',*pkgs])
def source(url,sha,name):
 dest=S/'upstream'/name
 if not dest.exists():
  run(['git','clone','--filter=blob:none','--no-checkout',url,dest]);run(['git','-C',dest,'fetch','--depth=1','origin',sha]);run(['git','-C',dest,'checkout','--detach',sha])
 return dest
if a.engine=='genesis':
 src=source('https://github.com/Genesis-Embodied-AI/genesis-world','90d55545c193082a8e32f9b1b6b7732f14d89be8','genesis-world')
 pip(src)
elif a.engine=='mjx':pip('jax==0.12.0','jaxlib==0.12.0','jax-rocm7-pjrt==0.12.0','jax-rocm7-plugin==0.12.0','mujoco==3.16.0','mujoco-mjx==3.16.0')
elif a.engine=='taichi':pip('amd-taichi==1.8.0b2','--index-url','https://pypi.amd.com/simple','--extra-index-url','https://pypi.org/simple','--index-strategy','unsafe-best-match')
elif a.engine=='warp':
 w=source('https://github.com/AMD-Ecosystem/warp','2e2673bb7b90eaabb9cb89dc1f55a76f61c13aab','warp-amd');m=source('https://github.com/AMD-Ecosystem/mujoco_warp','9dfdf7ab8d5a996fe143e9e2c1e5da646c6fc14f','mujoco-warp-amd')
 pip('mujoco==3.8.1','numpy','setuptools','wheel')
 run([v/'bin/python',w/'build_lib.py','--rocm-path',os.environ['ROCM_PATH'],'--hip-arch=gfx950','--jobs=8','--no-use-libmathdx'],timeout=1800,cwd=w)
 pip('--no-deps',w,m)
else:
 src=S/'upstream/gsplat'
 if not src.exists():run(['git','clone','--recurse-submodules','https://github.com/AMD-Ecosystem/gsplat.git',src])
 run(['git','-C',src,'fetch','--depth=1','origin','ff8bc5489545bcc1b5a2b997d975834429a0d7af']);run(['git','-C',src,'checkout','--detach','ff8bc5489545bcc1b5a2b997d975834429a0d7af']);pip('ninja','jaxtyping','rich','numpy','setuptools','wheel')
 os.environ.update(PYTORCH_ROCM_ARCH='gfx950',MAX_JOBS='8',BUILD_NO_CUDA='0')
 pip('--no-build-isolation','--no-deps',src)
run([v/'bin/python','-m','pip','freeze']) if (v/'bin/pip').exists() else None
