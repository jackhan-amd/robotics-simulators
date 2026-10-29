"""Stop only the superseded coordinator, leaving its active native smoke intact."""
from workspace import expand_runtime, run_root, runtime_path
import os,pathlib,signal
expected=expand_runtime('${LAB_ROOT}/provided_cfd_suite.py')
for folder in pathlib.Path('/proc').iterdir():
 if not folder.name.isdigit():continue
 try:
  args=(folder/'cmdline').read_bytes().split(b'\0');env=dict(x.split(b'=',1)for x in (folder/'environ').read_bytes().split(b'\0')if b'='in x)
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if expected.encode()not in args or env.get(b'PROVIDED_CFD_ENGINE')or env.get(b'PROVIDED_CFD_WINDOWS'):continue
 os.kill(int(folder.name),signal.SIGTERM);print('Stopped superseded coordinator only:',folder.name,'active smoke/native descendants retained')
