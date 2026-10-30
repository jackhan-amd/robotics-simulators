"""Publish the current report's reviewed prose after strict fidelity checks."""
from workspace import REPO_ROOT, script_command
import argparse,collections,hashlib,json,pathlib,re,subprocess,sys
ap=argparse.ArgumentParser();ap.add_argument('--metadata',default='humanizer-gpu-scope-run.json');args=ap.parse_args()
B=REPO_ROOT;O=B/'report';meta=json.loads((O/'evidence'/args.metadata).read_text(encoding='utf-8'));R=pathlib.Path(meta['run_dir']);K=pathlib.Path(meta['skill_root'])
decision=json.loads((R/'09_finalize.json').read_text(encoding='utf-8'));assert 'hold_and_report'not in json.dumps(decision)
gate=json.loads((R/'10_gate_final.json').read_text(encoding='utf-8'));receipt=json.loads((R/'10_gate_final_hashes.json').read_text(encoding='utf-8'))
assert gate['gate']['exit_code']==0 and receipt['exit_code']==0
for name in ('01_input.txt','final.md'):
 assert receipt[name]==hashlib.sha256((R/name).read_bytes()).hexdigest(),'Gate input changed: '+name
before=(R/'01_input.txt').read_text(encoding='utf-8');after=(R/'final.md').read_text(encoding='utf-8');assert after.count('<!-- HUMANIZE-SUMMARY -->')==1
body=after.split('<!-- HUMANIZE-SUMMARY -->')[0].rstrip()+'\n'
assert (O/'confluence-report.md').read_text(encoding='utf-8').rstrip()==before.rstrip(),'Report changed after the final review snapshot'
def protected(s):
 return dict(tables=[x for x in s.splitlines()if x.startswith('|')],headings=re.findall(r'^#{1,6} .+$',s,re.M),code=re.findall(r'```.*?```',s,re.S),inline_code=re.findall(r'`[^`\n]+`',s),links=re.findall(r'\]\(([^)]+)\)',s),numbers=collections.Counter(re.findall(r'(?<![\w])\d+(?:[.,]\d+)*(?:e[-+]?\d+)?',s,re.I)),html_markers=re.findall(r'<!--.*?-->',s,re.S))
a=protected(before);b=protected(body)
for key in a:assert a[key]==b[key],key
(O/'confluence-report.md').write_text(body,encoding='utf-8')
(R/'immutable-checks.json').write_text(json.dumps(dict(status='PASS',protected=list(a),before_sha256=hashlib.sha256(before.encode()).hexdigest(),after_sha256=hashlib.sha256(body.encode()).hexdigest()),indent=2),encoding='utf-8')
subprocess.run([*script_command('update_humanizer_review.py'),'--run-dir',str(R)],check=True)
for name in ('render_final.py','audit_gpu_measurements.py','audit_artifacts.py'):
 subprocess.run(script_command(name),check=True)
print('Reviewed GPU report published; data, commands and links preserved')
