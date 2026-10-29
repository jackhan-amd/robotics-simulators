"""Bootstrap isolated tools; all paths belong to this study."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import os,pathlib,subprocess,tarfile,urllib.request
R=run_root();S=storage_root()
def run(args):
 print('+',*map(str,args),flush=True);subprocess.run(list(map(str,args)),check=True,timeout=900)
uv=R/'bin/uv'
for name,packages in [('mujoco',['mujoco==3.16.0'])]:
 v=S/'venvs'/name
 if not v.exists():run([uv,'venv','--python','/usr/bin/python3',v])
 run([uv,'pip','install','--python',v/'bin/python',*packages])
# Git/MPI/Fortran are installed in a separate conda prefix, never with sudo.
archive=R/'sources/micromamba.tar.bz2'
if not archive.exists():urllib.request.urlretrieve('https://micro.mamba.pm/api/micromamba/linux-64/latest',archive)
with tarfile.open(archive) as t:
 m=t.getmember('bin/micromamba');p=R/'bin/micromamba';p.write_bytes(t.extractfile(m).read());p.chmod(0o755)
run([R/'bin/micromamba','--root-prefix',S/'cache/mamba','create','-y','-p',S/'tools','-c','conda-forge','git','cmake','ninja','eigen','openmpi','gfortran_linux-64','pkg-config'])
print('SETUP_COMPLETE',flush=True)
