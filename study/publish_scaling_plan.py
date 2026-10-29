import json,pathlib
B=pathlib.Path(__file__).resolve().parents[1];O=B/'report';p=json.loads((B/'study/env-scaling-plan.json').read_text());f=O/'confluence-report.md';s=f.read_text(encoding='utf-8');title='## 제공 예제 envs scaling 추가 시험'
body=[title,'','추가 시험 진행 중이다. 각 엔진에 제공되는 예제·모델을 사용하며, 임의의 로봇·FEM·유체 장면을 새로 구성하지 않는다. 모델과 물리 설정은 유지하고 headless 실행·env 복제·동기화·계측만 추가한다. 기존 단순 장면 결과와 추가 시험 결과는 별도로 제시한다.','','| 대상 | 제공 예제 | 현재 상태 |','|---|---|---|']+[f'| {e["engine"]} | `{e["example"]}` | {e["status"]} |'for e in p['cases']]+['','GPU native batch와 별도 프로세스의 독립 env 복제를 구분한다. envs 수만 늘리고 env당 모델 규모는 고정한다. 5회 반복, warm-up·reset 제외, 동기화 실행시간을 기록한다. 자산이나 backend 기능이 부족한 경우 해당 제공 예제를 미실행으로 명시한다.','']
if title in s:
 start=s.index(title);end=s.find('\n## ',start+1);s=s[:start]+'\n'.join(body)+s[end if end>=0 else len(s):]
else:s=s.replace('## 시험 범위와 완료 상태','\n'.join(body)+'\n## 시험 범위와 완료 상태',1)
f.write_text(s,encoding='utf-8');(O/'env-scaling-plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
