"""Apply the separately reviewed new section after its formal preservation gate."""
import collections,json,pathlib,re,shutil,subprocess,sys
B=pathlib.Path(__file__).resolve().parents[1];O=B/'report'
meta=json.loads((O/'evidence/humanizer-addendum-run.json').read_text());R=pathlib.Path(meta['run_dir']);K=pathlib.Path(meta['skill_root'])
cmd=[sys.executable,'-X','utf8',str(K/'scripts/verify_gates.py'),'--before',str(R/'01_input.txt'),'--after',str(R/'final.md'),'--genre','report','--json']
c=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=120);(R/'05_gate.log').write_text(c.stdout+c.stderr,encoding='utf-8')
gate=json.loads(c.stdout[c.stdout.index('{'):]);(R/'05_gate.json').write_text(json.dumps(gate,ensure_ascii=False,indent=2),encoding='utf-8');assert c.returncode==0,gate
before=(R/'01_input.txt').read_text(encoding='utf-8');after=(R/'final.md').read_text(encoding='utf-8');assert after.count('<!-- HUMANIZE-SUMMARY -->')==1
body=after.split('<!-- HUMANIZE-SUMMARY -->')[0].strip()
def anchors(s):return ([x for x in s.splitlines()if x.startswith('|')],re.findall(r'^#{1,6} .+$',s,re.M),re.findall(r'```.*?```',s,re.S),re.findall(r'\]\(([^)]+)\)',s),collections.Counter(re.findall(r'(?<![\w])\d+(?:[.,]\d+)*(?:e[-+]?\d+)?',s,re.I)))
assert anchors(before)==anchors(body)
after=after.replace('원본 글자 수: 2961',f'원본 글자 수: {len(before.strip())}').replace('최종 본문 글자 수: 2959',f'최종 본문 글자 수: {len(body)}').replace('2. 변경률 30% 이하 충족; 확정 수치는 공통 게이트에서 판정',f'2. 공통 게이트 변경률 {gate["change_rate"]["rate"]*100:.2f}%; gate exit 0')
(R/'final.md').write_text(after,encoding='utf-8')
current=(O/'confluence-report.md').read_text(encoding='utf-8');assert current.count(before.strip())==1
(O/'confluence-report.md').write_text(current.replace(before.strip(),body,1),encoding='utf-8')
dest=O/'evidence/humanizer-addendum';dest.mkdir(exist_ok=True)
for name in ['01_input.txt','05_gate.json','05_gate.log','final.md']:shutil.copy2(R/name,dest/name)
review=json.loads((O/'humanizer-review.json').read_text(encoding='utf-8'));review['additional_official_backend_review']=dict(route='light',run_id=R.name,change_rate=gate['change_rate'],gate=gate['gate'],grade='B',self_check='6/6',edits='C-11: two comma deletions only',immutable_checks='PASS: tables, headings, code, links and numeric tokens unchanged',scope='Instinct Sim chapter added after the initial heavy review; global counts updated from reviewed measurement data.',audit='evidence/humanizer-addendum/')
(O/'humanizer-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(review['additional_official_backend_review'],ensure_ascii=False))
