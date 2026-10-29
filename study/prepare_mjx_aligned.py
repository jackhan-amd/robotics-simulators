"""Recreate the matched study environment in fresh, isolated prefixes."""
import argparse,pathlib,subprocess
from workspace import REPO_ROOT,run_root,storage_root
from mjx_profiles import selected
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sdk-index-url',default='https://repo.amd.com/rocm/whl-multi-arch/');p.add_argument('--version',choices=('0.11.2','0.12.0'),default=selected()['version']);a=p.parse_args()
r=run_root();s=storage_root();uv=r/'bin/uv';runtime=s/'venvs/mujoco-mjx-rocm';aligned=s/'venvs'/('mujoco-mjx-0112-rocm'if a.version=='0.11.2'else'mujoco-mjx-0120-rocm')
assert not aligned.exists(),'Refusing to modify an existing measured environment; use a fresh external workspace'
def run(command):subprocess.run(list(map(str,command)),check=True)
if not runtime.exists():run([uv,'venv','--python','/usr/bin/python3',runtime])
core=runtime/'lib/python3.12/site-packages/_rocm_sdk_core/lib/libamdhip64.so.7'
if not core.exists():
 run([uv,'pip','install','--python',runtime/'bin/python','--index-url',a.sdk_index_url,'--extra-index-url','https://pypi.org/simple','--index-strategy','unsafe-best-match','rocm-sdk-core==7.14.1','rocm-sdk-libraries==7.14.1','rocm-sdk-device-gfx950==7.14.1'])
assert core.is_file()
run([uv,'venv','--system-site-packages','--python','/usr/bin/python3',aligned])
run([uv,'pip','install','--python',aligned/'bin/python',*[package+'=='+a.version for package in('jax','jaxlib','jax-rocm7-pjrt','jax-rocm7-plugin')],'mujoco==3.16.0','mujoco-mjx==3.16.0','numpy==2.5.4'])
run([aligned/'bin/python',REPO_ROOT/'tools/prepare_rocm_loader.py','--runtime-venv',runtime,'--output-dir',s/'compat/mjx714'])
print('Matched environment prepared; source the isolated loader and use the selected provided_mjx_suite.py profile')
