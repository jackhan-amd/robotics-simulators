"""Start a bounded study coordinator independently of the local SSH session."""
import argparse,datetime,json,pathlib,shlex,subprocess
from workspace import REPO_ROOT,run_root,ssh_prefix
p=argparse.ArgumentParser();p.add_argument('--script',required=True);p.add_argument('--label',required=True);p.add_argument('--env',action='append',default=[]);a=p.parse_args()
assert pathlib.PurePath(a.script).name==a.script and a.script.endswith('.py')
assert a.label.replace('-','').replace('_','').isalnum()
settings={}
for item in a.env:
 key,value=item.split('=',1);assert key.replace('_','').isalnum();settings[key]=value
r=run_root();code='\n'.join([
 'import json,os,pathlib,subprocess',f'r=pathlib.Path({str(r)!r})',f'label={a.label!r}',f'script={a.script!r}',
 'e=r/"evidence";e.mkdir(exist_ok=True)',
 'pidfile=e/(label+".pid")',
 'old=int(pidfile.read_text()) if pidfile.exists() else None',
 'assert old is None or not (pathlib.Path("/proc")/str(old)/"cmdline").exists(), "Coordinator PID still exists; inspect before relaunch"',
 f'env=os.environ.copy();env.update({settings!r});env["PYTHONUNBUFFERED"]="1"',
 'log=e/(label+".log")',
 'with log.open("w") as output:',
 ' child=subprocess.Popen(["python3",str(r/script)],cwd=r,env=env,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)',
 'pidfile.write_text(str(child.pid))',
 'print(json.dumps(dict(pid=child.pid,script=script,label=label,log=log.name)))'])
command='cd '+shlex.quote(str(r))+' && . ./env.sh && '+shlex.join(['python3','-c',code])
c=subprocess.run(ssh_prefix()+[command],capture_output=True,text=True,encoding='utf-8',timeout=90);assert c.returncode==0,c.stderr+c.stdout
receipt=json.loads(c.stdout.strip().splitlines()[-1]);receipt.update(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),settings=settings)
out=REPO_ROOT/'report/evidence';out.mkdir(parents=True,exist_ok=True);(out/(a.label+'-launch.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps(receipt))
