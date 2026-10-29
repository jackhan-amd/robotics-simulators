"""Collect remote structured results and logs, update states, render report."""
from workspace import run_root,ssh_prefix,scp_prefix,remote_file
import json,pathlib,shlex,subprocess
B=pathlib.Path(__file__).resolve().parents[1];O=B/'report/evidence/results';O.mkdir(parents=True,exist_ok=True)
import tarfile
subprocess.run(scp_prefix()+[str(B/'study/workspace.py'),str(B/'study/export_evidence.py'),remote_file(str(run_root())+'/')],check=True)
subprocess.run(ssh_prefix()+[shlex.join(['env','LAB_ROOT='+str(run_root()),'python3',str(run_root()/'export_evidence.py')])],check=True)
archive=B/'report/evidence/remote-evidence.tar.gz'
subprocess.run(scp_prefix()+[remote_file(run_root()/'evidence-export.tar.gz'),str(archive)],check=True)
with tarfile.open(archive)as t:
 for member in t.getmembers():
  assert (O/member.name).resolve().is_relative_to(O.resolve())
  t.extract(member,O,filter='data')
p=B/'study/plan.json';plan=json.loads(p.read_text(encoding='utf-8'));records=[]
for f in O.glob('*.json'):
 try:
  j=json.loads(f.read_text(encoding='utf-8'))
  if 'engine'in j and 'run_id'in j:records.append(j)
 except Exception:pass
for e in plan['engines']:
 items=[r for r in records if r['engine']==e['id']]
 if items:
  accepted=[r for r in items if r['status']=='PASS'and r.get('gpu_requested')]
  states=sorted(set(r['status'] for r in accepted))
  e['status']=('PASS · GPU' if e['id']=='mujoco' and 'PASS' in states else ' · '.join(states)) if states else items[-1]['status']
p.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
md=B/'report/confluence-report.md'
renderer='render_final.py'
if not md.exists():raise RuntimeError('Supply the reviewed report Markdown before rendering; collection does not invent a report')
subprocess.run(['python',str(B/'study'/renderer)],check=True)
