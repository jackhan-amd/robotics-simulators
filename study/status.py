"""Small progress summary from locally retained logs."""
import json,pathlib
B=pathlib.Path(__file__).resolve().parents[1]
for label in ['performance-series','humanoid-series','fluidlab-patched-smoke','nekrs-smoke']:
 files=sorted((B/'report/evidence').glob('*-'+label+'.log'))
 if not files:continue
 print(label)
 for line in files[-1].read_text(encoding='utf-8').splitlines():
  if line.startswith('{"engine"'):
   try:
    j=json.loads(line);print(json.dumps({k:j.get(k)for k in ['engine','case','rc','status','wall_s']}))
   except Exception:pass
  if line.startswith(('PERFORMANCE_TASK','HUMANOID_TASK')):print(line)
