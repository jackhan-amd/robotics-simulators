"""Record a no-change Korean document review without rewriting source bytes."""
from workspace import REPO_ROOT
import argparse,hashlib,json,pathlib
B=REPO_ROOT
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=pathlib.Path,required=True);p.add_argument('--document',type=pathlib.Path,required=True);p.add_argument('--output',required=True);a=p.parse_args();r=a.run_dir
gate=json.loads((r/'08_gate.json').read_text(encoding='utf-8'));hashes=json.loads((r/'08_gate_hashes.json').read_text(encoding='utf-8'))
assert gate['gate']['exit_code']==0 and hashes['exit_code']==0
for name in('01_input.txt','final.md'):assert hashes[name]==hashlib.sha256((r/name).read_bytes()).hexdigest()
before=(r/'01_input.txt').read_text(encoding='utf-8');after=(r/'final.md').read_text(encoding='utf-8');assert after.count('<!-- HUMANIZE-SUMMARY -->')==1
body=after.split('<!-- HUMANIZE-SUMMARY -->')[0].rstrip();assert body==before.rstrip()==a.document.read_text(encoding='utf-8').rstrip(),'This recorder handles unchanged light reviews only'
review=dict(status='PASS',skill='humanize-korean',route='light',document=a.document.as_posix(),sha256=hashlib.sha256(a.document.read_bytes()).hexdigest(),gate=gate,note='Reviewed prose already clear. Source bytes, legal notices, tables, commands and links preserved.')
(B/'report/evidence'/a.output).write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8');print('Recorded Korean light review:',a.document)
