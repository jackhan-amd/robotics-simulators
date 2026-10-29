"""Rebuild and audit the delivery using only its packaged source and evidence."""
import argparse,json,pathlib,secrets,subprocess,sys,zipfile
B=pathlib.Path(__file__).resolve().parents[1];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=pathlib.Path,default=B/'report/mi355x-simulator-results.zip');a=p.parse_args()
root=B/'_workspace'/('delivery-replay-'+secrets.token_hex(4));root.mkdir(parents=True);assert root.resolve().is_relative_to((B/'_workspace').resolve())
def unpack(archive):
 with zipfile.ZipFile(archive)as z:
  assert z.testzip()is None
  for item in z.infolist():assert(root/item.filename).resolve().is_relative_to(root.resolve())
  z.extractall(root)
unpack(a.bundle);unpack(root/'report/mi355x-reproduction-code.zip')
commands=[['study/render_final.py','--data-dir','report','--plan','report/test-plan.json'],['study/audit_gpu_measurements.py','--data-dir','report','--accepted-evidence'],['study/audit_artifacts.py','--data-dir','report','--plan','report/test-plan.json']]
logs=[]
for command in commands:
 r=subprocess.run([sys.executable,*command],cwd=root,capture_output=True,text=True,encoding='utf-8',timeout=180)
 logs.append(' '.join(command)+'\n'+r.stdout+r.stderr);assert r.returncode==0,r.stdout+r.stderr
result=dict(status='PASS',scope='Offline report generation and arithmetic/link/image audits from delivered source, accepted evidence and assets only. No private profile, raw history, SSH or GPU required.',checks=len(commands),directory=root.name)
(B/'report/evidence/delivery-replay.log').write_text('\n'.join(logs),encoding='utf-8');(B/'report/delivery-replay-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
