"""Prepare an auditable input for the user-requested Korean prose skill."""
from workspace import REPO_ROOT
import argparse,datetime,json,pathlib,secrets,shutil,subprocess,sys
sys.stdout.reconfigure(encoding='utf-8',errors='backslashreplace')
from workspace import skill_root
B=REPO_ROOT
ap=argparse.ArgumentParser();ap.add_argument('--input',default='confluence-report.md');ap.add_argument('--metadata',default='humanizer-run.json');args=ap.parse_args()
skill=skill_root('humanize-korean')
if not(skill/'SKILL.md').is_file():raise RuntimeError('Install epoko77-ai/im-not-ai Codex skill first; see docs/benchmark-tools.md')
stamp=datetime.date.today().isoformat();root=B/'_workspace';root.mkdir(exist_ok=True)
used=[int(p.name.split('-')[3])for p in root.glob(stamp+'-*')if len(p.name.split('-'))>=5]
run=root/f'{stamp}-{max(used,default=0)+1:03d}-{secrets.token_hex(2)}';run.mkdir()
shutil.copy2(B/'report'/args.input,run/'01_input.txt')
subprocess.run([sys.executable,str(skill/'scripts/prepare_monolith_input.py'),'--run-dir',str(run),'--genre','report'],check=True)
(B/'report/evidence'/args.metadata).write_text(json.dumps(dict(skill_root=str(skill),run_dir=str(run)),indent=2),encoding='utf-8')
print((run/'00_metrics.json').read_text(encoding='utf-8'))
