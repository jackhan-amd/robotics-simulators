"""Publish the accepted MJX execution profile, retaining diagnostics privately."""
import json,pathlib,re
from mjx_profiles import selected
MJX=selected()
B=pathlib.Path(__file__).resolve().parents[1];O=B/'report'
c=json.loads((O/'gpu-campaign-status.json').read_text(encoding='utf-8'))
model=next(x for x in c['campaigns']if x['model'].startswith('MJX-JAX '))
accepted=[p['envs']for p in model['points']if p['status']=='PASS']
summary=dict(runtime='JAX/jaxlib/ROCm plugin '+MJX['version']+'; isolated ROCm 7.14.1',model='supplied Humanoid, unchanged physics',compiler_profile=MJX['compiler_profile'],xla_flags=MJX['xla_flags'],accepted_envs=accepted,complete=len(accepted)==len(model['expected_envs']),scope='Matching software versions and isolated loader. No physics changes or global driver changes.')
(O/'evidence/mjx-runtime-profile.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
f=O/'confluence-report.md';s=f.read_text(encoding='utf-8')
s=re.sub(r'<!-- MJX-(?:FAILURE|WORKAROUND)-NOTE -->.*?<!-- /MJX-(?:FAILURE|WORKAROUND)-NOTE -->\s*','',s,flags=re.S)
note='<!-- MJX-WORKAROUND-NOTE -->\n\nMJX는 `safe-fusion` 실행 설정과 `XLA_FLAGS=--xla_disable_hlo_passes=fusion`을 사용한다. 제공 Humanoid의 물리 설정은 유지했다. 처리량에는 fusion 비활성화에 따른 비용이 반영된다. 이 설정은 관찰된 GPU 실행 오류를 피하기 위한 workaround이며, 공급업체가 근본 원인을 확인한 결과는 아니다. [최종 실행 설정](evidence/mjx-workaround.json).\n\n<!-- /MJX-WORKAROUND-NOTE -->\n\n'
if MJX['compiler_profile']=='default':note='<!-- MJX-WORKAROUND-NOTE -->\n\nMJX는 JAX·jaxlib·ROCm PJRT·plugin을 모두 `'+MJX['version']+'`으로 맞추고 ROCm 7.14.1의 별도 loader를 사용한다. `XLA_FLAGS`를 지정하지 않고 기본 fusion 설정으로 측정했다. 제공 Humanoid의 물리 설정은 유지했다. JAX 환경의 선택적 Warp import 안내는 별도로 시험한 MJWarp 환경과 구분해 읽어야 한다. [최종 실행 설정](evidence/mjx-runtime-profile.json).\n\n<!-- /MJX-WORKAROUND-NOTE -->\n\n'
note=note.replace('evidence/mjx-workaround.json','evidence/mjx-runtime-profile.json')
start=s.index('## MuJoCo · MJX / MJWarp');end=s.find('\n## ',start+4);end=end if end>=0 else len(s)
chapter=s[start:end].replace('### 3. Throughput\n','### 3. Throughput\n'+note,1)
s=s[:start]+chapter+s[end:];f.write_text(s,encoding='utf-8')
print('MJX',MJX['name'],'accepted envs:',accepted)
