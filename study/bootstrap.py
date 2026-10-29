"""Prepare external directories and a flat deployment from this GPU-only checkout."""
import os,pathlib,shlex,shutil,sys
from workspace import run_root,storage_root,REPO_ROOT
R=run_root();S=storage_root();R.mkdir(parents=True,exist_ok=True)
for p in [R/'bin',R/'logs',R/'evidence',R/'sources',S,S/'private']:p.mkdir(parents=True,exist_ok=True)
source=pathlib.Path(os.environ.get('STUDY_WORKTREE',REPO_ROOT)).resolve()
assert(source/'study/workspace.py').is_file(),'Run from the GPU-only repository checkout'
repo=R/'repo'
if not repo.exists():repo.symlink_to(source,target_is_directory=True)
assert repo.resolve()==source,'Existing workspace repo points elsewhere; use a fresh workspace'
uv=shutil.which('uv');assert uv,'Install uv in a user-owned bootstrap environment first'
if not(R/'bin/uv').exists():shutil.copy2(uv,R/'bin/uv')
for p in(source/'study').iterdir():
 if p.suffix not in('.py','.json'):continue
 target=R/p.name
 if target.resolve()==p.resolve():continue
 if target.exists()and target.read_bytes()!=p.read_bytes():raise RuntimeError('Existing adapter differs; use a fresh workspace: '+p.name)
 if not target.exists():shutil.copy2(p,target)
env=R/'env.sh'
if not env.exists():
 values={'LAB_ROOT':str(R),'STUDY_STORAGE_ROOT':str(S),'STUDY_PRIVATE_ROOT':str(S/'private'),'STUDY_WORKTREE':str(source),'ROCM_PATH':os.environ['ROCM_PATH'],'STUDY_AMD_ARCH':'gfx950','STUDY_AMD_NAME':'MI355X','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
 env.write_text('\n'.join('export '+k+'='+shlex.quote(v)for k,v in values.items())+'\nexport PATH="$LAB_ROOT/bin:$STUDY_STORAGE_ROOT/tools/bin:$ROCM_PATH/bin:$PATH"\nexport HIP_PATH="$ROCM_PATH"\n')
print('External workspace prepared; source',env,'and prepare the documented engine runtime. No GPU test has run.')
