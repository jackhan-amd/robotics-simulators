"""Prepare a separate matched JAX 0.12 environment; leave existing runtimes intact."""
import os,pathlib,subprocess
from workspace import run_root,storage_root
r=run_root();s=storage_root();venv=s/'venvs/mujoco-mjx-0120-rocm';uv=r/'bin/uv'
if not venv.exists():subprocess.run([str(uv),'venv','--system-site-packages','--python','/usr/bin/python3',str(venv)],check=True)
subprocess.run([str(uv),'pip','install','--python',str(venv/'bin/python'),'jax==0.12.0','jaxlib==0.12.0','jax-rocm7-pjrt==0.12.0','jax-rocm7-plugin==0.12.0','mujoco==3.16.0','mujoco-mjx==3.16.0','numpy==2.5.4'],check=True)
subprocess.run([str(uv),'pip','freeze','--python',str(venv/'bin/python')],check=True)
