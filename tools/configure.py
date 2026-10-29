#!/usr/bin/env python3
"""Create an external storage environment; leave system Python and services alone."""
import argparse, json, shlex
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--storage-root',type=Path,required=True);p.add_argument('--name',choices=('simulator','studio'),required=True);a=p.parse_args()
root=a.storage_root.expanduser().resolve();root.mkdir(parents=True,exist_ok=True)
for name in ['venvs','upstream','models','datasets','assets','cache/uv-publication','tmp','private']: (root/name).mkdir(parents=True,exist_ok=True)
values={'STUDY_STORAGE_ROOT':str(root),'STUDY_PRIVATE_ROOT':str(root/'private'),'UV_CACHE_DIR':str(root/'cache/uv-publication'),'UV_PYTHON_INSTALL_DIR':str(root/'python'),'XDG_CACHE_HOME':str(root/'cache'),'TMPDIR':str(root/'tmp'),'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
file=root/'private'/('environment-'+a.name+'.sh');content='\n'.join('export '+k+'='+shlex.quote(v)for k,v in values.items())+'\n'
if file.exists()and file.read_text()!=content:raise SystemExit('Existing environment differs; inspect it before creating another name')
file.write_text(content);file.chmod(0o600)
print('source '+shlex.quote(str(file)))
