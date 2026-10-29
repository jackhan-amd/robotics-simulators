"""Read installed XLA's supported flags without running a simulation."""
import os,subprocess,sys
env=os.environ.copy();env['XLA_FLAGS']='--help'
c=subprocess.run([sys.executable,'-c','import jax; jax.devices()'],env=env,capture_output=True,text=True,timeout=30)
matches=[line for line in(c.stdout+c.stderr).splitlines()if any(k in line for k in('unroll','fusion','double_buffer','vectoriz'))]
print('\n'.join(matches));assert matches
