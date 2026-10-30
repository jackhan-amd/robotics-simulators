"""Run batched numerical qualification through the shared GPU recorder lock."""
import os,shlex,subprocess
from workspace import run_root,storage_root
r=run_root();s=storage_root();env=os.environ.copy()
loaded=subprocess.check_output(['bash','-c','source "$1"; env -0','bash',str(s/'compat/mjx714/loader.env')],env=env)
env.update({k.decode():v.decode()for item in loaded.split(b'\0')if b'='in item for k,v in[item.split(b'=',1)]})
env.pop('XLA_FLAGS',None);env.update(JAX_PLATFORMS='rocm',XLA_PYTHON_CLIENT_PREALLOCATE='false')
result=subprocess.run(['python3',str(r/'run_remote.py'),'--engine','mujoco','--case','mjx0120-batch-parity','--gpu','--wait','--timeout','900','--',str(s/'venvs/mujoco-mjx-0120-rocm/bin/python'),str(r/'mjx_batch_parity.py')],env=env,timeout=14400)
raise SystemExit(result.returncode)
