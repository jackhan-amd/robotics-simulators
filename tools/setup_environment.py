#!/usr/bin/env python3
"""Prepare a new Python3.12 project prefix from PyPI or an operator-owned runtime."""
import argparse,json,os,shutil,subprocess,sys,time,shlex
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--name',required=True);p.add_argument('--engine',choices=('mujoco','local-runtime'),required=True);p.add_argument('--base',type=Path);p.add_argument('--execute',action='store_true');p.add_argument('--budget',type=int,default=900);a=p.parse_args()
if not a.name.replace('-','').replace('_','').isalnum():p.error('Use a simple new environment name')
root=Path(os.environ['STUDY_STORAGE_ROOT']).resolve();dest=root/'venvs'/a.name
if not dest.resolve().is_relative_to(root):p.error('Environment path escapes storage')
if not 1<=a.budget<=1800:p.error('Use a finite 1..1800 second setup budget')
plan={'destination':'${STUDY_STORAGE_ROOT}/venvs/'+a.name,'engine':a.engine,'provider':'operator-local-prefix'if a.base else'public-pypi','executes':a.execute,'budget_s':a.budget}
print(json.dumps(plan),flush=True)
if not a.execute:raise SystemExit(0)
if dest.exists():p.error('Destination already exists; no automatic replacement')
private=root/'private/setup';private.mkdir(parents=True,exist_ok=True);env=os.environ.copy();env.update(UV_CACHE_DIR=str(root/'cache/uv-publication'),UV_PYTHON_INSTALL_DIR=str(root/'python'));start=time.monotonic()
if a.base:
 source=a.base.expanduser().resolve();python=source/'bin/python';probe=json.loads(subprocess.check_output([str(python),'-c','import sys,sysconfig,json;print(json.dumps(dict(version=list(sys.version_info[:2]),purelib=sysconfig.get_paths()["purelib"])))'],text=True));assert probe['version']==[3,12],'Python3.12 is required'
 subprocess.run(['uv','venv','--python',str(python),str(dest)],check=True,env=env,timeout=a.budget)
 src=Path(probe['purelib']);target=dest/'lib/python3.12/site-packages'
 # Copies remain independent; no hardlinks or writable overlays into the original runtime.
 files=0;bytes_copied=0
 for current,dirs,names in os.walk(src,followlinks=False):
  if time.monotonic()-start>a.budget:raise TimeoutError('Bounded environment copy stopped; partial prefix retained')
  dirs[:]=[d for d in dirs if d!='__pycache__']
  current=Path(current);relative=current.relative_to(src);out=target/relative;out.mkdir(parents=True,exist_ok=True)
  for dirname in list(dirs):
   f=current/dirname
   if f.is_symlink():
    (out/dirname).symlink_to(os.readlink(f));dirs.remove(dirname)
  for name in names:
   if name.endswith('.pyc') or (current==src and name in ('_virtualenv.py','_virtualenv.pth')):continue
   f=current/name;d=out/name
   if d.exists()or d.is_symlink():raise ValueError('Unexpected existing destination file')
   if f.is_symlink():d.symlink_to(os.readlink(f))
   else:shutil.copy2(f,d);files+=1;bytes_copied+=f.stat().st_size
 # Recreate package entrypoints with the new interpreter; never alter the source prefix.
 for entry in sorted((source/'bin').iterdir()):
  if entry.name.startswith(('python','activate','deactivate')) or entry.name in ('pydoc.bat',):continue
  destination=dest/'bin'/entry.name
  if destination.exists()or destination.is_symlink():continue
  if entry.is_symlink():
   resolved=entry.resolve()
   if resolved.is_relative_to(source):destination.symlink_to(dest/resolved.relative_to(source))
   else:destination.symlink_to(resolved)
  elif entry.is_file():
   content=entry.read_bytes()
   if content.startswith(b'#!'):
    header,sep,body=content.partition(b'\n')
    if b'python'in header:content=("#!/bin/sh\n'''exec' "+shlex.quote(str(dest/'bin/python'))+" \"$0\" \"$@\"\n' '''\n").encode()+body
    content=content.replace(str(source).encode(),str(dest).encode())
    destination.write_bytes(content);shutil.copymode(entry,destination)
   else:shutil.copy2(entry,destination)
 receipt={**plan,'python':[3,12],'copied_regular_files':files,'copied_logical_bytes':bytes_copied,'source_modified':False,'elapsed_s':time.monotonic()-start,'scope':'Independent package copy. Validate actual imports/physics after relocation; no success inferred from setup.'}
else:
 if a.engine=='local-runtime':p.error('local-runtime requires --base')
 python=os.environ.get('PYTHON312','3.12');subprocess.run(['uv','venv','--python',python,str(dest)],check=True,env=env,timeout=a.budget)
 args=['uv','pip','install','--python',str(dest/'bin/python'),'--default-index','https://pypi.org/simple']
 if a.engine=='mujoco':args+=['-r',str(BASE/'configs/mujoco-py312.lock.txt')]

 with (private/(a.name+'.log')).open('w')as log:subprocess.run(args,env=env,stdout=log,stderr=log,check=True,timeout=max(1,a.budget-(time.monotonic()-start)))
 receipt={**plan,'python':[3,12],'elapsed_s':time.monotonic()-start,'scope':'Package installation only; physics evidence is separate.'}
(private/(a.name+'.json')).write_text(json.dumps(receipt,indent=2)+'\n');print('Environment prepared; run its documented smoke and review numerical/backend evidence.')
