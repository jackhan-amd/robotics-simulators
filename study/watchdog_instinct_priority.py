"""Fair scheduling of this study's coordinators; measured children keep running."""
from workspace import expand_runtime, run_root, runtime_path
import argparse,datetime,json,os,pathlib,signal
R=run_root();F=R/'evidence/watchdog-instinct-priority.json'
p=argparse.ArgumentParser();p.add_argument('action',choices=['pause','status','resume']);a=p.parse_args()
def inventory():
 out={}
 for d in pathlib.Path('/proc').iterdir():
  if not d.name.isdigit():continue
  try:
   args=d.joinpath('cmdline').read_bytes().decode().split('\0');status=d.joinpath('status').read_text();stat=d.joinpath('stat').read_text().split();parent=int(next(x.split(':',1)[1]for x in status.splitlines()if x.startswith('PPid:')))
   out[int(d.name)]=dict(args=args,starttime=stat[21],state=stat[2],ppid=parent)
  except (OSError,ValueError,StopIteration):pass
 return out
now=datetime.datetime.now(datetime.timezone.utc).isoformat();procs=inventory()
data=json.loads(F.read_text())if F.exists()else dict(utc=now,paused=[],reason='Prevent repeated coordinator lock reacquisition until the oldest Instinct smoke completes; active recorder/native measurement children untouched')
cutoff=datetime.datetime.fromisoformat(data['utc']).timestamp();completed=[]
for f in (R/'evidence').glob('*provided-instinct-libero-smoke*.json'):
 if f.stat().st_mtime<cutoff:continue
 try:j=json.loads(f.read_text())
 except Exception:continue
 if isinstance(j,dict)and j.get('case')=='provided-instinct-libero-smoke'and 'run_id'in j:completed.append(dict(status=j['status'],run_id=j['run_id']))
if a.action=='pause'and not completed:
 target=[(pid,x)for pid,x in procs.items()if str(R/'run_remote.py')in x['args']and 'provided-instinct-libero-smoke'in x['args']];assert target,'No pending Instinct smoke recorder'
 data['target_recorders']=[pid for pid,x in target]
 for pid,x in procs.items():
  args=x['args']
  if len(args)<2:continue
  path=pathlib.Path(args[1])
  if path.parent!=R or not path.name.startswith('provided_')or not path.name.endswith('suite.py')or path.name=='provided_instinct_suite.py':continue
  assert args[0].endswith(('python','python3')),args
  if not any(y['pid']==pid and y['starttime']==x['starttime']for y in data['paused']):data['paused'].append(dict(pid=pid,starttime=x['starttime'],args=args,state_before=x['state'],paused_utc=now))
  if x['state']!='T':os.kill(pid,signal.SIGSTOP)
elif a.action=='resume':
 assert completed,'Instinct smoke has not completed'
 for x in data['paused']:
  pid=x['pid']
  if pid in procs and procs[pid]['starttime']==x['starttime']and procs[pid]['args']==x['args']:os.kill(pid,signal.SIGCONT)
 data.update(resumed_utc=now,completed=completed)
data['last_check_utc']=now
F.write_text(json.dumps(data,indent=2))
active=[]
for pid,x in procs.items():
 if str(R/'run_remote.py')in x['args']:
  args=x['args'];active.append(dict(pid=pid,case=args[args.index('--case')+1],children=[p for p,y in procs.items()if y['ppid']==pid]))
print(json.dumps(dict(utc=now,action=a.action,paused_pids=[x['pid']for x in data['paused']],completed=completed,queue=active)))
