#!/usr/bin/env python3
"""Create study-local loader aliases; never modify the supplied runtime venv."""
import argparse
from pathlib import Path
import shlex
p=argparse.ArgumentParser();p.add_argument('--runtime-venv',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
a=p.parse_args();site=a.runtime_venv.resolve()/'lib/python3.12/site-packages';a.output_dir.mkdir(parents=True,exist_ok=True)
core=site/'_rocm_sdk_core/lib';assert (core/'libamdhip64.so.7').is_file()
links={'libamdhip64.so':core/'libamdhip64.so.7','libhiprtc.so':core/'libhiprtc.so.7'}
numa=Path('/usr/lib/x86_64-linux-gnu/libnuma.so.1')
if numa.is_file():links['libnuma.so']=numa
for name,target in links.items():
 dest=a.output_dir/name
 if dest.is_symlink():assert dest.resolve()==target.resolve()
 elif dest.exists():raise RuntimeError('Refusing to replace existing loader file')
 else:dest.symlink_to(target.resolve())
paths=[str(a.output_dir.resolve())]
for pkg in sorted(site.glob('_rocm*')):
 for sub in ['lib','lib/llvm/lib']:
  if (pkg/sub).is_dir():paths.append(str((pkg/sub).resolve()))
env=a.output_dir/'loader.env';env.write_text('export LD_LIBRARY_PATH='+shlex.quote(':'.join(paths))+'\n'+'export LLVM_PATH='+shlex.quote(str((core/'llvm').resolve()))+'\n')
print('Created study-local loader links and loader.env; source that file for the test process only.')
