"""Temporarily pause a verified coordinator, preserving its measured child."""
import argparse,json,os,pathlib,signal,subprocess,sys,time
from workspace import run_root
p=argparse.ArgumentParser();p.add_argument('action',choices=('pause','resume','expire','cancel'));p.add_argument('--pid',type=int,required=True);p.add_argument('--script',required=True);p.add_argument('--seconds',type=int,default=1800);a=p.parse_args()
r=run_root();assert pathlib.PurePath(a.script).name==a.script and a.script.startswith('provided_')and a.script.endswith('_suite.py')
assert 60<=a.seconds<=3600
proc=pathlib.Path('/proc')/str(a.pid);expected=['python3',str(r/a.script)]
def identity():
 assert proc.stat().st_uid==os.getuid()
 assert proc.joinpath('cmdline').read_bytes().decode().split('\0')[:2]==expected
 return proc.joinpath('stat').read_text().rsplit(')',1)[1].split()[19]
lease=r/'evidence'/(a.script.removesuffix('.py')+'-pause-lease.json')
if a.action=='expire':
 time.sleep(a.seconds)
 data=json.loads(lease.read_text())
 if data.get('active')and data['start']==identity():os.kill(a.pid,signal.SIGCONT);data['active']=False;data['expired']=True;lease.write_text(json.dumps(data))
elif a.action=='pause':
 start=identity();os.kill(a.pid,signal.SIGSTOP)
 data=dict(pid=a.pid,script=a.script,start=start,active=True,seconds=a.seconds,scope='Coordinator only; measured child continues')
 lease.write_text(json.dumps(data,indent=2))
 subprocess.Popen([sys.executable,str(pathlib.Path(__file__).resolve()),'expire','--pid',str(a.pid),'--script',a.script,'--seconds',str(a.seconds)],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
 print(json.dumps(data))
elif a.action=='cancel':
 data=json.loads(lease.read_text());assert data['start']==identity();active=[]
 for child in pathlib.Path('/proc').iterdir():
  if not child.name.isdigit():continue
  try:
   fields=child.joinpath('stat').read_text().rsplit(')',1)[1].split()
   if int(fields[1])==a.pid and fields[0]!='Z':active.append(int(child.name))
  except(FileNotFoundError,PermissionError,ProcessLookupError):pass
 assert not active,'Measured child or recorder still active; do not cancel coordinator'
 data.update(active=False,cancelled=True);lease.write_text(json.dumps(data,indent=2));os.kill(a.pid,signal.SIGTERM)
 try:os.kill(a.pid,signal.SIGCONT)
 except ProcessLookupError:pass
 print(json.dumps(data))
else:
 data=json.loads(lease.read_text());assert data['start']==identity();os.kill(a.pid,signal.SIGCONT);data['active']=False;lease.write_text(json.dumps(data,indent=2));print(json.dumps(data))
