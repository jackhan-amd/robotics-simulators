"""Refresh the diagnosed report snapshot after the GPU campaign is finalized."""
import json,pathlib,shutil,subprocess,sys
B=pathlib.Path(__file__).resolve().parents[1];meta=json.loads((B/'report/evidence/humanizer-gpu-scope-run.json').read_text(encoding='utf-8'));run=pathlib.Path(meta['run_dir']);skill=pathlib.Path(meta['skill_root'])
c=json.loads((B/'report/gpu-campaign-status.json').read_text(encoding='utf-8'));assert c['status']!='IN_PROGRESS'
assert (run/'02_diagnosis.md').is_file()
shutil.copy2(run/'01_input.txt',run/'01_diagnosis_input.txt')
shutil.copy2(B/'report/confluence-report.md',run/'01_input.txt')
subprocess.run([sys.executable,str(skill/'scripts/prepare_monolith_input.py'),'--run-dir',str(run),'--genre','report','--diagnosis',str(run/'02_diagnosis.md'),'--chunk'],check=True)
m=json.loads((run/'chunk_manifest.json').read_text(encoding='utf-8'));print(json.dumps({k:m[k]for k in('chunk_count','body_chunk_count','passthrough_chunk_count','lossless_check')}));print(str(run))
