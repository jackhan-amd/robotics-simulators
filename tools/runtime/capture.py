"""Run one remote study action, retaining the exact command and raw output locally."""
from workspace import REPO_ROOT
from workspace import ssh_prefix
import argparse,datetime,json,pathlib,subprocess,time,sys
sys.stdout.reconfigure(errors='backslashreplace')
p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('command');p.add_argument('--timeout',type=int,default=1800);a=p.parse_args()
root=REPO_ROOT/'report/evidence';root.mkdir(parents=True,exist_ok=True)
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
stem=root/(stamp+'-'+a.label)
cmd=ssh_prefix()+[a.command]
start=time.perf_counter()
with stem.with_suffix('.log').open('w',encoding='utf-8') as log:
 try:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=a.timeout);rc=r.returncode
 except subprocess.TimeoutExpired:rc=124
meta=dict(id=stamp+'-'+a.label,label=a.label,utc=stamp,command=a.command,rc=rc,wall_s=time.perf_counter()-start,log=stem.with_suffix('.log').name)
stem.with_suffix('.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
print(json.dumps(meta));print(stem.with_suffix('.log').read_text(encoding='utf-8')[-5000:])
