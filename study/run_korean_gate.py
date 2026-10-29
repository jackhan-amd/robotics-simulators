"""Capture the installed Korean skill gate and its exact input hashes."""
import argparse,hashlib,json,pathlib,subprocess,sys
from workspace import skill_root
sys.stdout.reconfigure(encoding='utf-8')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=pathlib.Path,required=True);p.add_argument('--output',default='08_gate');a=p.parse_args();r=a.run_dir
paths=[r/'01_input.txt',r/'final.md'];before={f.name:hashlib.sha256(f.read_bytes()).hexdigest()for f in paths}
c=subprocess.run([sys.executable,str(skill_root('humanize-korean')/'scripts/verify_gates.py'),'--before',str(paths[0]),'--after',str(paths[1]),'--genre','report','--json'],capture_output=True,text=True,encoding='utf-8')
raw=c.stdout+c.stderr;(r/(a.output+'_output.txt')).write_text(raw,encoding='utf-8')
gate=None
for index,char in enumerate(c.stdout):
 if char!='{':continue
 try:parsed=json.loads(c.stdout[index:])
 except json.JSONDecodeError:continue
 if isinstance(parsed,dict)and'gate'in parsed:gate=parsed;break
assert gate is not None,'Gate output unavailable; inspect saved output'
assert before=={f.name:hashlib.sha256(f.read_bytes()).hexdigest()for f in paths},'Input changed while gate ran'
(r/(a.output+'.json')).write_text(json.dumps(gate,ensure_ascii=False,indent=2),encoding='utf-8')
(r/(a.output+'_hashes.json')).write_text(json.dumps(dict(before,exit_code=c.returncode),indent=2),encoding='utf-8')
print(json.dumps(dict(exit_code=c.returncode,change_rate=gate['change_rate']['rate'],output=a.output)));raise SystemExit(c.returncode)
