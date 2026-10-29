"""Bilingual, observation-only node report with original command evidence."""
from workspace import expand_runtime, run_root, runtime_path, value
import datetime,html,json,pathlib,shutil
B=pathlib.Path(__file__).resolve().parents[1];E=B/'report/evidence';esc=html.escape
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
dest=B/'.amd-validation/results'/stamp/'node-validation';dest.mkdir(parents=True,exist_ok=True)
captures=[]
for label in ['preflight','final-health']:
 candidates=sorted(E.glob('*-'+label+'.json'));assert candidates
 meta=candidates[-1];r=json.loads(meta.read_text());log=E/r['log']
 shutil.copy2(meta,dest/meta.name);shutil.copy2(log,dest/log.name);captures.append((r,log))
def pair(ko,en):return '<span class="ko">'+ko+'</span><span class="en">'+en+'</span>'
def p(ko,en):return '<p>'+pair(ko,en)+'</p>'
panels={}
panels['scope']='<h2>'+pair('검증 범위','Validation scope')+'</h2>'+p('제공된 단일 GPU 컨테이너의 관측 기록이며 물리 호스트 전체의 시스템 인수 판정은 수행하지 않았다.','These observations cover the supplied single-GPU container, without a claim of full physical-host acceptance.')
panels['scope']+=p('MI355X 제품명, gfx950 ISA, PCI ID 1002:75a3가 일치했다. 프로파일에 온도·전력·대역폭 합격 기준이 없어 임의 기준을 적용하지 않았다.','The MI355X product name, gfx950 ISA and PCI ID 1002:75a3 agreed. No temperature, power or bandwidth acceptance thresholds were supplied, so none were invented.')
panels['inventory']='<h2>'+pair('환경 관측','Environment observations')+'</h2><table><tr><th>Item</th><th>Observed</th></tr>'+''.join('<tr><td>'+a+'</td><td>'+v+'</td></tr>'for a,v in [('Connection',expand_runtime('${STUDY_SSH_TARGET}:${STUDY_SSH_PORT} (direct SSH)')),('GPU','AMD Instinct MI355X × 1 / gfx950 / PCI 1002:75a3'),('GPU VRAM','309220868096 bytes / 288 GiB'),('CPU','AMD EPYC 9575F / 256 host logical CPUs'),('OS / Python','Ubuntu 24.04.5 / Python 3.12.3'),('Runtime','pip ROCm SDK 10.1.0 / PyTorch 2.14.0+rocm10.1.0 / HIP 7.16.26385'),('Container','not published')])+'</table>'
panels['health']='<h2>'+pair('상태와 해석','Health and interpretation')+'</h2>'+p('사전 점검에서 노출된 ECC 오류 수는 0이었고 GPU는 유휴 상태였다. 시험 종료 후 AMD SMI process/metric을 다시 수집했다. 세부 값과 N/A 항목은 원본 JSON 출력에 보존했다.','The exposed preflight ECC counts were zero and the GPU was idle. AMD SMI process/metric output was collected again after measurement. The raw output retains detailed readings and N/A fields.')
panels['health']+=p('GPU 1개를 노출한 컨테이너에서 측정했다. 호스트의 전체 GPU·NIC 토폴로지, 펌웨어 및 네트워크 대역폭 합격 판정은 NOT RUN이다. 제한된 telemetry를 물리 링크 장애로 해석하지 않았다.','Measurements used a container exposing one GPU. Acceptance of the full host GPU/NIC topology, firmware and network bandwidth is NOT RUN. Restricted telemetry was not interpreted as a physical link fault.')
panels['health']+=p('aac 환경에서는 sudo를 사용하지 않았다. 권고된 module load rocm/10.0.0은 module 명령이 없어 실행할 수 없었으며, 제공된 pip SDK를 관측·사용했다.','No sudo was used on AAC. The recommended module load rocm/10.0.0 could not run because the module command was unavailable; the supplied pip SDK was observed and used.')
panels['evidence']='<h2>'+pair('명령과 원본 근거','Commands and raw evidence')+'</h2>'
for r,log in captures:
 relative=log.relative_to(B).as_posix()
 panels['evidence']+='<h3>'+esc(r['id'])+'</h3><p>rc='+str(r['rc'])+'; wall='+f'{r["wall_s"]:.3f}'+' s</p><pre>'+esc(r['command'])+'</pre><p><a href="'+relative+'">'+pair('원본 로그','Raw log')+'</a></p><details><summary>'+pair('로그 열기','Expand log')+'</summary><pre>'+esc(log.read_text(encoding='utf-8'))+'</pre></details>'
panels['evidence']+=p('같은 명령·종료코드·로그를 .amd-validation/results 아래에도 보존했다.','The same commands, exit codes and logs were also preserved under .amd-validation/results.')
css='''*{box-sizing:border-box}body{margin:0;font:15px/1.7 system-ui,"Malgun Gothic",sans-serif;background:#eef2f6;color:#182638}.en{display:none}body.eng .ko{display:none}body.eng .en{display:inline}header{padding:24px;background:#14263e;color:white}.layout{display:flex}nav{width:230px;flex-shrink:0;padding:16px;background:#dfe7ef}nav a{display:block;padding:9px;color:#254463}main{padding:25px;max-width:1400px;min-width:0}.panel{display:none}.panel.active{display:block}table{border-collapse:collapse}td,th{padding:10px;border-bottom:1px solid #bfcddd}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#14263e;color:#e4eef8;padding:16px}button{padding:8px}.dark{background:#172333;color:#dce6ee}.dark nav{background:#24364e}.dark a{color:#8acaff}@media(max-width:800px){.layout{display:block}nav{width:100%;display:flex;overflow:auto}nav a{white-space:nowrap}}'''
names=[('scope','범위','Scope'),('inventory','환경','Environment'),('health','상태·제한','Health / gaps'),('evidence','원본 근거','Evidence')]
panels['evidence']=panels['evidence'].replace('<pre>','<button class="copy">'+pair('복사','Copy')+'</button><pre>')
js="function show(){let id=location.hash.slice(1)||'scope';document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('active',p.id===id));}addEventListener('hashchange',show);show();document.getElementById('lang').onclick=()=>document.body.classList.toggle('eng');document.getElementById('theme').onclick=()=>document.body.classList.toggle('dark');document.querySelectorAll('.copy').forEach(b=>b.onclick=()=>navigator.clipboard.writeText(b.nextElementSibling.innerText));"
doc='<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MI355X node observations</title><style>'+css+'</style><header><h1>'+pair('MI355X 노드 관측 보고서','MI355X node observation report')+'</h1><button id="lang">한국어 / English</button> <button id="theme">Light / Dark</button></header><div class="layout"><nav>'+''.join('<a href="#'+i+'">'+pair(ko,en)+'</a>'for i,ko,en in names)+'</nav><main>'+''.join('<section class="panel" id="'+i+'">'+s+'</section>'for i,s in panels.items())+'</main></div><script>'+js+'</script></html>'
out=B/'validation-report-mi355x.html';out.write_text(doc,encoding='utf-8');print(out)
