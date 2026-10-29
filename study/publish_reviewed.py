"""Adopt reviewed prose only after formal gates and immutable-content checks."""
import collections,json,pathlib,re,shutil,subprocess,sys
B=pathlib.Path(__file__).resolve().parents[1];O=B/'report'
meta=json.loads((O/'evidence/humanizer-run.json').read_text());R=pathlib.Path(meta['run_dir']);K=pathlib.Path(meta['skill_root'])
decision=json.loads((R/'09_finalize.json').read_text(encoding='utf-8'))
assert 'hold_and_report'not in json.dumps(decision)
cmd=[sys.executable,'-X','utf8',str(K/'scripts/verify_gates.py'),'--before',str(R/'01_input.txt'),'--after',str(R/'final.md'),'--genre','report','--json']
c=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=120)
(R/'05_gate.log').write_text(c.stdout+c.stderr,encoding='utf-8')
gate=json.loads(c.stdout[c.stdout.index('{'):]);(R/'05_gate.json').write_text(json.dumps(gate,ensure_ascii=False,indent=2),encoding='utf-8')
assert c.returncode==0,(c.returncode,gate['gate'])
before=(R/'01_input.txt').read_text(encoding='utf-8');after=(R/'final.md').read_text(encoding='utf-8')
assert after.count('<!-- HUMANIZE-SUMMARY -->')==1
body=after.split('<!-- HUMANIZE-SUMMARY -->')[0].rstrip()+'\n'
def protected(s):
 return dict(tables=[x for x in s.splitlines()if x.startswith('|')],headings=re.findall(r'^#{1,6} .+$',s,re.M),code=re.findall(r'```.*?```',s,re.S),links=re.findall(r'\]\(([^)]+)\)',s),numbers=collections.Counter(re.findall(r'(?<![\w])\d+(?:[.,]\d+)*(?:e[-+]?\d+)?',s,re.I)))
a=protected(before);b=protected(body)
for key in a:assert a[key]==b[key],key
(O/'confluence-report.md').write_text(body,encoding='utf-8')
dest=O/'evidence/humanizer';dest.mkdir(exist_ok=True)
for name in ['01_input.txt','02_diagnosis.md','04_gate.json','05_gate.json','05_gate.log','09_finalize.json','final.md']:
 shutil.copy2(R/name,dest/name)
review=dict(skills=[dict(name='humanize-korean',source='https://github.com/epoko77-ai/im-not-ai',route='heavy',run_id=R.name),dict(name='humanizer',source='https://github.com/blader/humanizer',version='3.1.0')],change_rate=gate['change_rate'],gate=gate['gate'],immutable_checks='PASS: tables, headings, code, image/source links and numeric tokens unchanged',finalizer=decision,supplemental_prose='REPRODUCE.md, node-report prose and HTML template reviewed with humanizer principles; factual technical scope and commands retained.',audit='evidence/humanizer/')
(O/'humanizer-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(gate=gate['gate'],change_rate=gate['change_rate'],finalizer=decision),ensure_ascii=False))
