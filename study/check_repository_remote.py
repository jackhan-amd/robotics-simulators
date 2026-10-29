"""Run CPU harness checks on Python 3.12 between GPU jobs, under the study lock."""
import json,pathlib,shlex,subprocess
from workspace import REPO_ROOT,run_root,ssh_prefix,scp_prefix,remote_file
r=run_root();target=r/'repo'
subprocess.run(ssh_prefix()+[shlex.join(['mkdir','-p',str(target/'study')])],check=True)
for relative in('study/workspace.py','study/publication.py','tests/test_study_publication.py'):
 subprocess.run(scp_prefix()+[str(REPO_ROOT/relative),remote_file(target/relative)],check=True)
code='\n'.join([
 'import pathlib,subprocess,sys',
 'assert sys.version_info[:2]==(3,12),sys.version',
 'commands=[["python3","-m","unittest","discover","-s","tests","-v"],["python3","-m","simulators","check"],["python3","tools/assets.py","check"],["python3","-m","simulators","build"]]',
 'sys.path.insert(0,"study")',
 'from workspace import storage_root,expand_runtime',
 'example=storage_root()/expand_runtime("official-taichi/root${PYTHON_SITE_PACKAGES}/taichi/examples/simulation/mpm88.py")',
 'assert example.is_file(), "Pinned Taichi payload example path missing"',
 'print("TAICHI_PAYLOAD_SOURCE_PATH_PASS",flush=True)',
 'for command in commands:',
 ' print("CHECK",*command,flush=True);subprocess.run(command,check=True)',
 'print("REPOSITORY_CHECKS_PASS")'])
shell='set -e\n. '+shlex.quote(str(r/'env.sh'))+'\nexport PATH="$STUDY_STORAGE_ROOT/tools/bin:$PATH"\ncd '+shlex.quote(str(target))+'\n'+shlex.join(['python3','-c',code])
command=shlex.join(['flock',str(r/'gpu.lock'),'bash','-c',shell])
result=subprocess.run(ssh_prefix()+[command],capture_output=True,text=True,encoding='utf-8',timeout=14400)
out=REPO_ROOT/'report/evidence';(out/'repository-checks-final.log').write_text(result.stdout+result.stderr,encoding='utf-8')
receipt=dict(status='PASS'if result.returncode==0 else'FAIL',rc=result.returncode,python='3.12',platform='Linux',scope='Repository wiring and publication filters; no simulator throughput or GPU physics validation',log='repository-checks-final.log')
(out/'repository-checks-final.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps(receipt));raise SystemExit(result.returncode)
