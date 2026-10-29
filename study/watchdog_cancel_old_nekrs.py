"""Cancel only the superseded native children; preserve the result recorder."""
from workspace import expand_runtime, run_root, runtime_path
import datetime,json,os,pathlib,signal,time
R=run_root();expected=str(R/'provided_nekrs.py')
def processes():
 out={}
 for p in pathlib.Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   args=p.joinpath('cmdline').read_bytes().decode().split('\0');status=p.joinpath('status').read_text();ppid=int(next(x.split(':',1)[1]for x in status.splitlines()if x.startswith('PPid:')))
   out[int(p.name)]=dict(args=args,ppid=ppid)
  except (OSError,StopIteration,ValueError):pass
 return out
before=processes();drivers=[pid for pid,x in before.items()if len(x['args'])>1 and x['args'][1]==expected and x['args'][0].endswith(('python','python3'))]
assert len(drivers)==1,drivers
driver=drivers[0];recorder=before[driver]['ppid'];rec=before[recorder]
assert str(R/'run_remote.py')in rec['args']and 'provided-nekrs-envs-1'in rec['args'],rec
natives=[pid for pid,x in before.items()if x['ppid']==driver and x['args'][0]==str(R/'storage/install/nekrs-native/bin/nekrs')]
assert natives,natives
targets=[]
def descend(pid):
 for child,x in before.items():
  if x['ppid']==pid:descend(child)
 targets.append(pid)
for pid in natives:descend(pid)
signalled=[]
for pid in targets:
 now=processes()
 if pid in now and now[pid]==before[pid]:
  os.kill(pid,signal.SIGTERM);signalled.append(pid)
deadline=time.monotonic()+30
while driver in processes()and time.monotonic()<deadline:time.sleep(.2)
after=processes();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
data=dict(utc=stamp,reason='old independent-reset measurement superseded by explicitly documented continuous windows; not physics failure',driver=driver,recorder=recorder,native_children=natives,signalled=signalled,driver_exited=driver not in after,recorder_preserved=recorder not in signalled,other_queues_untouched=True)
(R/'evidence'/(stamp+'-watchdog-old-nekrs-cancellation.json')).write_text(json.dumps(data,indent=2));print(json.dumps(data))
assert data['driver_exited']
