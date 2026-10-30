from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import os,pathlib,subprocess
from mjx_profiles import selected
R=run_root();S=storage_root();env=os.environ.copy()
loader=S/'compat/mjx714/loader.env';assert loader.is_file()
loaded=subprocess.check_output(['bash','-c','source "$1"; env -0','bash',str(loader)],env=env)
env.update({k.decode():v.decode()for item in loaded.split(b'\0')if b'='in item for k,v in[item.split(b'=',1)]})
env.update(JAX_PLATFORMS='rocm',XLA_PYTHON_CLIENT_PREALLOCATE='false',STUDY_MJX_RUNTIME_PROFILE='rocm7.14.1')
version=os.environ.get('PROVIDED_MJX_VERSION',selected()['version']);assert version in('0.11.2','0.12.0')
profile=os.environ.get('PROVIDED_MJX_COMPILER_PROFILE','default'if version=='0.12.0'else'safe-fusion')
assert profile in('default','safe-fusion')
assert profile!='safe-fusion'or os.environ.get('PROVIDED_MJX_DISABLE_GRAPHS')!='1','Use default profile for separate command-buffer diagnostics'
env['STUDY_MJX_COMPILER_PROFILE']=profile
if profile=='safe-fusion':env['XLA_FLAGS']='--xla_disable_hlo_passes=fusion'
else:env.pop('XLA_FLAGS',None)
aligned=os.environ.get('PROVIDED_MJX_ALIGNED','1')=='1';python=S/'venvs'/('mujoco-mjx-0112-rocm'if aligned else'mujoco-mjx-rocm')/'bin/python';prefix='provided-mjx714-jax0112-humanoid'if aligned else'provided-mjx714-humanoid'
if version=='0.12.0':python=S/'venvs/mujoco-mjx-0120-rocm/bin/python';prefix='provided-mjx714-jax0120-humanoid'
if os.environ.get('PROVIDED_MJX_DISABLE_GRAPHS')=='1':env['XLA_FLAGS']='--xla_gpu_enable_command_buffer= --xla_gpu_enable_latency_hiding_scheduler=false'
def run(n,smoke=False):
 name=prefix+'-smoke'if smoke else f'{prefix}-envs-{n}'
 if os.environ.get('PROVIDED_MJX_DISABLE_GRAPHS')=='1':name+='-no-command-buffer'
 cmd=['python3',str(R/'run_remote.py'),'--engine','mujoco','--case',name,'--gpu','--wait','--timeout','7200','--',str(python),str(R/'provided_mjx_humanoid.py'),'--envs',str(n)]
 if smoke:cmd+=['--smoke']
 print('PROVIDED_MJX_TASK',name,flush=True);return subprocess.run(cmd,env=env,timeout=14400).returncode
if run(1,True)==0:
 for n in map(int,os.environ.get('PROVIDED_MJX_ENVS','2048,4096,8192,16384,32768,65536').split(',')):
  if run(n)!=0:print('FAILED independent env size; continuing requested sweep:',n,flush=True)
