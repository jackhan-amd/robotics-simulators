"""Adapt repository build recipes to gfx950 and the observed user SDK."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import argparse,os,pathlib,subprocess
p=argparse.ArgumentParser();p.add_argument('engine',choices=['chrono','incflo','nekrs']);a=p.parse_args()
R=run_root();S=storage_root();repo=R/'repo';tools=S/'tools';base=S/'venvs/base'
# The supplied Git blobs contain CRCRLF in shell files; normalize the study copy.
for script in (repo/'recipes').rglob('*.sh'):
 raw=script.read_bytes()
 if b'\r' in raw:script.write_bytes(raw.replace(b'\r',b''))
os.environ['PATH']=str(base/'bin')+':'+str(tools/'bin')+':'+os.environ['PATH'];os.environ['CMAKE_POLICY_VERSION_MINIMUM']='3.5'
def run(cmd,timeout=1800,cwd=repo):
 print('+',*map(str,cmd),flush=True);subprocess.run(list(map(str,cmd)),check=True,timeout=timeout,cwd=cwd)
if a.engine in ['chrono','incflo']:
 # Architecture substitution is recorded; source and physics solver remain unchanged.
 recipe=(repo/'recipes'/a.engine/'build.sh').read_text().replace('gfx1151','gfx950').replace('--parallel 2','--parallel 8').replace('timeout 900','timeout 1800')
 recipe=recipe.replace('source "$(dirname "${BASH_SOURCE[0]}")/../common.sh"',f'source "{repo}/recipes/common.sh"')
 if a.engine=='chrono':
  # Eigen pin is GitLab-hosted; recipe keeps it unchanged unless fetch fails.
  pass
 dest=R/(a.engine+'-gfx950-build.sh');dest.write_text(recipe)
 run(['bash',dest],timeout=5400)
else:
 src=S/'upstream/nekrs';sha='96b3cf9e5bacede16568826c04a21bc0fe50dc7d'
 if not src.exists():
  run(['git','clone','--filter=blob:none','--no-checkout','https://github.com/Nek5000/nekRS',src]);run(['git','-C',src,'fetch','--depth=1','origin',sha]);run(['git','-C',src,'checkout','--detach',sha])
 run(['git','-C',src,'submodule','update','--init','--recursive'],timeout=900)
 b=S/'build/nekrs-native-make';i=S/'install/nekrs-native'
 run(['cmake','-S',src,'-B',b,'-G','Unix Makefiles','-DCMAKE_INSTALL_PREFIX='+str(i),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_PREFIX_PATH='+str(tools),'-DCMAKE_C_COMPILER='+str(tools/'bin/mpicc'),'-DCMAKE_CXX_COMPILER='+str(tools/'bin/mpicxx'),'-DCMAKE_Fortran_COMPILER='+str(tools/'bin/mpifort'),'-DOCCA_ENABLE_HIP=ON','-DOCCA_ENABLE_CUDA=OFF','-DOCCA_ENABLE_DPCPP=OFF','-DENABLE_ADIOS=OFF','-DENABLE_HYPRE_GPU=OFF','-DENABLE_CVODE=OFF','-DENABLE_CPPTRACE=OFF'])
 run(['cmake','--build',b,'--target','install','--parallel','8'],timeout=3600)
