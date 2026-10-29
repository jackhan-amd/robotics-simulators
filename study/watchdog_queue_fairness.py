"""Pause only a verified coordinator between benchmarks, never its measured child."""
from workspace import expand_runtime, run_root, runtime_path
import argparse,datetime,json,os,pathlib,signal
R=run_root();state=R/'evidence/watchdog-nekrs-queue-schedule.json'
p=argparse.ArgumentParser();p.add_argument('action',choices=['pause','resume','status']);p.add_argument('--pid',type=int);a=p.parse_args();pid=a.pid
if a.action=='status':
 data=json.loads(state.read_text());cutoff=datetime.datetime.fromisoformat(data['utc']).timestamp();completed={};active=[]
 targets=['provided-instinct-libero-smoke','provided-fluidlab-smoke','provided-incflo-smoke']
 for f in (R/'evidence').glob('*.json'):
  if f.stat().st_mtime<cutoff:continue
  try:j=json.loads(f.read_text())
  except Exception:continue
  if isinstance(j,dict)and j.get('case')in targets and 'run_id'in j:completed[j['case']]=dict(status=j['status'],run_id=j['run_id'])
 procs={}
 for d in pathlib.Path('/proc').iterdir():
  if not d.name.isdigit():continue
  try:procs[int(d.name)]=(int(next(x.split(':',1)[1]for x in d.joinpath('status').read_text().splitlines()if x.startswith('PPid:'))),d.joinpath('cmdline').read_bytes().decode().split('\0'))
  except (OSError,StopIteration,ValueError):pass
 for n,(parent,args)in procs.items():
  if str(R/'run_remote.py')in args:
   children=[c for c,x in procs.items()if x[0]==n];case=args[args.index('--case')+1]
   active.append(dict(pid=n,case=case,children=children))
 print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed=completed,all_target_smokes_completed=len(completed)==3,queue=active)));raise SystemExit(0)
assert pid is not None,'Specify the verified coordinator PID with --pid'
proc=pathlib.Path('/proc')/str(pid);args=proc.joinpath('cmdline').read_bytes().decode().split('\0');start=proc.joinpath('stat').read_text().split()[21]
assert args[:2]==['python3',str(R/'provided_cfd_suite.py')],args
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
if a.action=='pause':
 children=[]
 for child in pathlib.Path('/proc').iterdir():
  if not child.name.isdigit():continue
  try:
   child_args=child.joinpath('cmdline').read_bytes().decode().split('\0');child_status=child.joinpath('status').read_text()
   if f'PPid:\t{pid}\n'in child_status and str(R/'run_remote.py')in child_args and any(x.startswith('provided-nekrs-windows-')for x in child_args):children.append(int(child.name))
  except OSError:pass
 assert len(children)==1,children
 data=dict(utc=now,pid=pid,starttime=start,child_recorders_preserved=children,action='SIGSTOP coordinator only',reason='Prevent repeated lock reacquisition while older engine smoke jobs wait; active native benchmark and recorder remain running',waiting_for=['instinct','fluidlab','incflo'])
 os.kill(pid,signal.SIGSTOP)
else:
 data=json.loads(state.read_text());assert data['starttime']==start
 os.kill(pid,signal.SIGCONT);data.update(resumed_utc=now,action='SIGCONT coordinator only')
state.write_text(json.dumps(data,indent=2));print(json.dumps(data))
