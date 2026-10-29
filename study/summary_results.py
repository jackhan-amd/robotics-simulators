import json,pathlib
B=pathlib.Path(__file__).resolve().parents[1];O=B/'report/evidence/results';rows=[]
for f in O.glob('*.json'):
 try:r=json.loads(f.read_text(encoding='utf-8'))
 except Exception:continue
 if not isinstance(r,dict)or 'engine'not in r:continue
 for x in r.get('results',[]):
  if x.get('repeats',0)>=5 and x.get('synchronized_rollout_s'):
   rows.append(dict(engine=r['engine'],case=r['case'],status=r['status'],impl=x.get('implementation'),envs=x.get('envs'),particles=x.get('particles'),shape=x.get('shape'),median_s=x.get('median_s'),env_step_per_s=x.get('env_step_per_s'),step_per_s=x.get('step_per_s'),frames_per_s=x.get('frames_per_s')))
for row in sorted(rows,key=lambda x:(x['engine'],x['case'])):print(json.dumps(row))
print('MEASURED_CASES',len(rows))
