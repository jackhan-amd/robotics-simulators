"""Queue one isolated matched-version diagnostic without interrupting a GPU child."""
import argparse,json,pathlib,shlex,subprocess
from workspace import REPO_ROOT,run_root,storage_root,ssh_prefix,scp_prefix,remote_file
p=argparse.ArgumentParser();p.add_argument('--coordinator-pid',type=int,required=True);a=p.parse_args();r=run_root();s=storage_root()
for name in('coordinator_lease.py','prepare_mjx012_probe.py','mjx_repair_probe.py'):
 subprocess.run(scp_prefix()+[str(REPO_ROOT/'study'/name),remote_file(r/name)],check=True)
def remote(command,timeout=3600):
 prefix='. '+shlex.quote(str(r/'env.sh'))+' && '
 return subprocess.run(ssh_prefix()+[prefix+command],capture_output=True,text=True,encoding='utf-8',timeout=timeout)
control=shlex.join(['python3',str(r/'coordinator_lease.py')])
arguments=shlex.join(['--pid',str(a.coordinator_pid),'--script','provided_mjx_suite.py','--seconds','1800'])
pause=remote(control+' pause '+arguments);assert pause.returncode==0,pause.stderr
success=False;out=REPO_ROOT/'report/evidence';out.mkdir(exist_ok=True)
try:
 prep=remote(shlex.join(['python3',str(r/'prepare_mjx012_probe.py')]),timeout=900)
 (out/'mjx012-preparation.log').write_text(prep.stdout+prep.stderr,encoding='utf-8')
 assert prep.returncode==0,prep.stderr[-3000:]
 loader=shlex.quote(str(s/'compat/mjx714/loader.env'))
 command='. '+loader+' && unset XLA_FLAGS STUDY_MJX_BARRIER && export JAX_PLATFORMS=rocm XLA_PYTHON_CLIENT_PREALLOCATE=false && '+shlex.join(['python3',str(r/'run_remote.py'),'--engine','mujoco','--case','mjx0120-default-fusion-humanoid-probe-4096','--gpu','--wait','--timeout','420','--',str(s/'venvs/mujoco-mjx-0120-rocm/bin/python'),str(r/'mjx_repair_probe.py'),'--envs','4096','--steps','1000','--repeats','1'])
 result=remote(command)
 (out/'mjx012-diagnostic.log').write_text(result.stdout+result.stderr,encoding='utf-8')
 success=result.returncode==0
 print(json.dumps(dict(probe_status='PASS'if success else'FAIL',coordinator_paused=success,automatic_resume_seconds=1800,log='mjx012-diagnostic.log')))
 print(result.stdout[-4500:])
finally:
 if not success:
  resume=remote(control+' resume '+arguments);assert resume.returncode==0,resume.stderr
