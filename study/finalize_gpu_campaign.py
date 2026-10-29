"""Reconcile completion language with the current qualified GPU campaign."""
import json,pathlib,re
B=pathlib.Path(__file__).resolve().parents[1];O=B/'report'
c=json.loads((O/'gpu-campaign-status.json').read_text(encoding='utf-8'))
f=O/'env-scaling-data.json';d=json.loads(f.read_text(encoding='utf-8'));d['status']=c['status']
d['campaign_counts']=c['counts'];d['expected_primary_configurations']=c['expected_configurations']
d['count_note']='Primary matrix and earlier GPU baseline share the six MJWarp Humanoid runs; do not add the two counts. Only final accepted measurements are published.'
f.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
for f in (B/'study/env-scaling-plan.json',O/'env-scaling-plan.json'):
 p=json.loads(f.read_text(encoding='utf-8'));p['status']=c['status'];f.write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
if c['status']=='IN_PROGRESS':print('Campaign still in progress');raise SystemExit(0)
assert not c['counts']['PENDING']and not c['counts']['REMEASUREMENT_PENDING']
assert all(x['smoke_status']=='PASS'for x in c['campaigns'])
f=O/'confluence-report.md';s=f.read_text(encoding='utf-8')
s=s.replace('추가 env scaling은 진행 중이다.','요청한 제공 예제 env scaling을 모두 실행했다. 실패 구성에는 처리량을 제시하지 않는다.')
s=s.replace('추가 시험 진행 중이다. MI355X GPU에서 계산하는','요청한 env 규모의 실행을 마쳤다. MI355X GPU에서 계산하는')
s=s.replace('제공 예제의 현재 진행 상태는 아래와 같다.','제공 예제의 최종 실행 상태는 아래와 같다.')
f.write_text(s,encoding='utf-8')
print('Final campaign:',c['status'],c['counts'])
