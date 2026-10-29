"""Small, read-only view of this study's GPU queue and latest results."""
from workspace import expand_runtime, run_root, runtime_path
import datetime,json,pathlib,re,subprocess
R=run_root();files=sorted((R/'evidence').glob('*.json'),key=lambda f:f.stat().st_mtime,reverse=True);shown=0
print('UTC',datetime.datetime.now(datetime.timezone.utc).isoformat())
for f in files:
 try:j=json.loads(f.read_text())
 except Exception:continue
 if not isinstance(j,dict)or not j.get('case','').startswith('provided-')or 'run_id'not in j:continue
 print(json.dumps({k:j.get(k)for k in('engine','case','status','rc','wall_s','run_id','execution_utc')}));shown+=1
 if shown>=12:break
for line in subprocess.check_output(['ps','-eo','pid,ppid,etimes,pcpu,args'],text=True).splitlines():
 if re.search(re.escape(str(R))+r'/(?:provided_[^ /]+\.py|capture_provided[^ /]+\.py)|nekrs --setup|spawn_main',line):print(line)
for f in pathlib.Path('/sys/class/drm').glob('card*/device/gpu_busy_percent'):
 try:
  value=int(f.read_text());
  if value:print('GPU_BUSY',str(f),value)
 except Exception:pass
