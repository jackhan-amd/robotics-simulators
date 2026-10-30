"""Render reviewed Markdown as a self-contained report with simulator tabs."""
from workspace import REPO_ROOT
from workspace import expand_runtime, run_root, runtime_path
import argparse,base64,datetime,html,json,mimetypes,os,pathlib,re,sys,tempfile
sys.path.insert(0,str(pathlib.Path(tempfile.gettempdir())/'robotics-study-plot-deps'))
import markdown
from polite_korean import html as polite_html
from report_presentation import finalize_copy
B=REPO_ROOT
ap=argparse.ArgumentParser();ap.add_argument('--data-dir',type=pathlib.Path,default=B/'report');ap.add_argument('--input',type=pathlib.Path);ap.add_argument('--output',type=pathlib.Path);ap.add_argument('--plan',type=pathlib.Path);ap.add_argument('--public',action='store_true');args=ap.parse_args()
if args.public:os.environ['STUDY_PUBLIC']='1'
O=args.data_dir.resolve();output=args.output or O/'mi355x-simulator-report.html';esc=html.escape
p=json.loads((args.plan or B/'configs/benchmarks/report-plan.json').read_text(encoding='utf-8'))
amd_engines={e['id']:e for e in p['engines']if e.get('amd_solution')}
def amd_badge(engine):
 return '<span class="amd-mark" title="AMD 블로그 소개·GPU 지원 경로 제공; MI355X 공식 지원·측정 성공 여부는 별도">AMD</span>'if engine in amd_engines else''
count=sum(e.get('primary_performance_configurations',e.get('measured_configurations',0))for e in p['engines'])
text=finalize_copy((args.input or O/'confluence-report.md').read_text(encoding='utf-8'))
pieces=re.split(r'^## (.+)\s*$',text,flags=re.M);sections=dict(zip(pieces[1::2],pieces[2::2]))
def render(source):
 out=markdown.markdown(source,extensions=['tables','fenced_code','sane_lists','md_in_html'])
 def embed(m):
  path=O/m[1];assert path.is_file(),path
  uri='data:'+mimetypes.guess_type(path.name)[0]+';base64,'+base64.b64encode(path.read_bytes()).decode()
  return 'src="'+uri+'"'
 out=re.sub(r'src="(images/[^\"]+)"',embed,out)
 out=out.replace('<table>','<div class="table"><table>').replace('</table>','</table></div>')
 return re.sub(r'<pre>','<button class="copy">명령 복사</button><pre>',out)
def table(headers,rows):
 return '<div class="table"><table><tr>'+''.join('<th>'+esc(x)+'</th>'for x in headers)+'</tr>'+''.join('<tr>'+''.join('<td>'+str(x)+'</td>'for x in row)+'</tr>'for row in rows)+'</table></div>'
panels={}
panels['overview']=f'<h2>GPU 측정 결과</h2><p>GPU 물리 엔진과 별도 GSplat 렌더링의 측정 구성 {count}개입니다.</p>'
panels['overview']+=table(['Simulator','최종 상태','성능 구성 수','고객 설명'],[(f'<a href="#{e["id"]}">{esc(e["title"])}</a>',esc(e['status']),e['measured_configurations'],esc(e['presentation']))for e in p['engines']])
panels['overview']+='<p>PASS는 이 보고서의 작은 시험 장면과 수치 조건을 통과했다는 뜻이다. CPU_ONLY는 CPU 실행이다. 엔진마다 장면과 집계 단위가 다르므로 하나의 성능 순위로 해석할 수 없다.</p>'
panels['overview']+='<h3>실험 개요</h3>'+render(sections.get('실험 개요',sections.get('고객 설명에 사용할 시연 순서','')))
panels['environment']='<h2>측정 환경과 해석</h2>'+render(sections['측정 환경과 해석'])
panels['environment']+=table(['항목','관측값'],[('GPU','AMD Instinct MI355X × 1 · gfx950 · PCI ID 1002:75a3'),('VRAM','309220868096 bytes / 288 GiB'),('CPU','AMD EPYC 9575F · host logical CPUs 256'),('Runtime','SDK 10.1.0 packaging / Torch HIP 7.16.26385; MJX private ROCm 7.14.1'),('작업 경로','${LAB_ROOT}')])
panels['plan']='<h2>'+esc(p.get('report_section_title','시험 방법 및 조건'))+' '+esc(p['version'])+'</h2><p>'+esc(p['state'])+'</p><ol>'+''.join('<li>'+esc(x)+'</li>'for x in p['method'])+'</ol><p><a href="test-plan.json">시험 조건 JSON</a> · <a href="evidence/gpu-smoke-coverage.json">제공 예제 GPU smoke와 실제 Run ID</a></p>'
panels['research']='<h2>외부 공개 성능과 AMD 확인 범위</h2><p>로컬 rocm-blogs commit 630de9e66daee9204d5bb053bcd6be15afd29aab (2026-08-25)와 공식 웹 자료를 조사했다. 공개 수치를 찾지 못했다는 설명은 확인한 자료의 범위에 한정한다.</p>'+render(sections['외부 공개 성능과 AMD 확인 범위'])
panels['environment']=re.sub(r'<tr><td>[^<]+</td><td>\$\{LAB_ROOT\}</td></tr>','',panels['environment'])
records=[]
for f in (O/'evidence/final').glob('*.json'):
 try:r=json.loads(f.read_text(encoding='utf-8'))
 except Exception:continue
 if isinstance(r,dict)and r.get('status')=='PASS'and r.get('gpu_requested'):
  r['_receipt']=f.name;records.append(r)
records.sort(key=lambda r:r.get('utc',''))
for e in p['engines']:
 s='<h2>'+esc(e['title'])+'</h2>'+render(sections[e['title']])
 s+='<details><summary>최종 성공 실행 로그</summary>'
 for r in records:
  if r['engine']!=e['id']:continue
  s+='<p>'+esc(r['case'])+' · <a href="evidence/final/'+esc(r['_receipt'])+'">JSON</a> · <a href="evidence/final/'+esc(r['execution_log'])+'">log</a></p>'
 s+='</details>';panels[e['id']]=s
names=[('overview','전체 결과'),('environment','측정 환경'),('plan','시험 방법 및 조건'),('research','외부 성능 조사')]+[(e['id'],e['title'])for e in p['engines']]
if '실험 개요' in sections:
 panels['overview']='<h2>실험 개요</h2>'+render(sections['실험 개요'])+'<h3>시험 결과 · 제공 예제와 env scaling</h3>'+render(sections['시험 결과 · 제공 예제와 env scaling'])
if '시험 범위와 완료 상태'in sections:
 panels['overview']='<h2>시험 범위와 완료 상태</h2>'+render(sections['시험 범위와 완료 상태'])+'<h3>고객 설명 순서</h3>'+render(sections['고객 설명에 사용할 시연 순서'])
groups=[('일반 안내',['overview','environment','plan','research']),('Rigid simulation',['mujoco','instinct']),('Fluid simulation',['incflo','nekrs','fluidlab']),('Multiphysics · Rigid / Fluid',['genesis','chrono']),('Simulation framework',['taichi']),('Rendering',['gsplat'])]
labels=dict(names);nav_html=''.join('<div class="nav-group"><div class="nav-heading">'+esc(title)+'</div>'+''.join(f'<a href="#{i}">{esc(labels[i])}</a>'for i in ids if i in labels)+'</div>'for title,ids in groups)
if '제공 예제 envs scaling 시험'in sections:
 panels['env-scaling']='<h2>제공 예제 envs scaling 시험 · 진행 중</h2>'+render(sections['제공 예제 envs scaling 시험'])
 nav_html=nav_html.replace('<a href="#overview">','<a href="#env-scaling">제공 예제 envs scaling · 진행 중</a><a href="#overview">',1)
css='''*{box-sizing:border-box}body{font:15px/1.7 system-ui,"Malgun Gothic",sans-serif;margin:0;background:#eef2f6;color:#182638}header{padding:25px 32px;background:#14263e;color:white}h1{font-size:26px;margin:0}header p{margin:5px 0;color:#c6d3e3}.layout{display:flex;min-height:85vh}nav{width:265px;flex-shrink:0;padding:14px;background:#dfe7ef}nav a{display:block;padding:8px 12px;color:#254463;text-decoration:none;border-radius:6px}nav a.active{background:#174f7b;color:white}main{max-width:1420px;flex:1;min-width:0;padding:28px}.panel{display:none}.panel.active{display:block}h2{margin-top:0}h3{margin-top:28px;border-bottom:1px solid #c4d2df;padding-bottom:6px}p{max-width:1120px}table{border-collapse:collapse;width:100%;display:block;overflow:auto;background:white}th,td{text-align:left;padding:10px;vertical-align:top;border-bottom:1px solid #d8e1e9}th{background:#dce7f0}pre{white-space:pre-wrap;overflow-wrap:anywhere;padding:18px;background:#122238;color:#e2edf6;border-radius:6px;font:13px/1.6 Consolas,monospace}code{overflow-wrap:anywhere}.badge{display:inline-block;background:#fff1c9;color:#6b4b00;padding:3px 10px;border-radius:5px}button{cursor:pointer;padding:7px 14px;border:1px solid #aabccd;border-radius:4px}img{max-width:100%;max-height:600px;background:white}details{margin:20px 0}.dark{background:#172333;color:#dce6ee}.dark table{background:#233449}.dark th{background:#32465e}.dark nav{background:#1c2d42}.dark nav a{color:#c6daed}.dark a{color:#8acaff}@media(max-width:850px){.layout{display:block}nav{width:100%;display:flex;overflow:auto;position:sticky;top:0}nav a{white-space:nowrap}main{padding:16px}header{padding:20px}}@media print{nav,button{display:none}.panel{display:block;break-before:page}main{padding:0}.layout{display:block}pre{background:#eee;color:black}}'''
js='''function show(){let id=location.hash.slice(1)||'overview';if(!document.getElementById(id))id='overview';document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('active',p.id===id));document.querySelectorAll('nav a').forEach(a=>a.classList.toggle('active',a.hash==='#'+id));}addEventListener('hashchange',show);show();document.getElementById('theme').onclick=()=>document.body.classList.toggle('dark');document.querySelectorAll('.copy').forEach(b=>b.onclick=()=>navigator.clipboard.writeText(b.nextElementSibling.innerText));'''
css+=' .table{overflow:auto}table{display:table;width:100%}header{min-height:165px}'
css+=' .nav-heading{font-size:12px;font-weight:700;color:#576f86;padding:18px 10px 4px;text-transform:uppercase}.dark .nav-heading{color:#aac1d4}@media(max-width:850px){.nav-group{display:flex;align-items:center;flex-shrink:0;border-right:1px solid #aabccc}.nav-heading{white-space:nowrap;padding:8px}}'
js=js.replace("a.hash==='#'+id));}","a.hash==='#'+id));setTimeout(()=>scrollTo(0,0),0);}")
stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
css+=' .amd-mark{display:inline-block;background:#000!important;color:#fff!important;font:800 12px/1.4 system-ui,sans-serif;letter-spacing:.4px;padding:2px 8px;border-radius:2px;vertical-align:middle;white-space:nowrap}nav .amd-mark{margin-left:5px;font-size:10px;padding:1px 5px}'
css+=' #env-scaling th:first-child,#env-scaling td:first-child{min-width:140px}#env-scaling th:last-child,#env-scaling td:last-child{white-space:nowrap;min-width:100px}#env-scaling td:nth-child(2){overflow-wrap:anywhere;min-width:300px;max-width:650px}'
for engine,e in amd_engines.items():
 nav_html=nav_html.replace('href="#'+engine+'">'+esc(e['title'])+'</a>','href="#'+engine+'">'+esc(e['title'])+' '+amd_badge(engine)+'</a>')
doc='<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MI355X Robotics Simulator 시험 보고서</title><style>'+css+'</style></head><body><header><h1>MI355X Robotics Simulator 시험 보고서</h1><p>시험 진행 중 · MI355X 1 GPU · '+str(count)+'개 성능 구성 × 5회 · 갱신 '+stamp+'</p><button id="theme">밝게 / 어둡게</button></header><div class="layout"><nav>'+''.join(f'<a href="#{i}">{esc(n)}</a>'for i,n in names)+'</nav><main>'+''.join(f'<section class="panel" id="{i}">{s}</section>'for i,s in panels.items())+'</main></div><script>'+js+'</script></body></html>'
output.write_text(doc,encoding='utf-8')
doc=doc.replace(''.join(f'<a href="#{i}">{esc(n)}</a>'for i,n in names),nav_html).replace(str(count)+'개 성능 구성 × 5회',str(count)+'개 성능 구성 + CPU 검증 기준 1개 · 각 5회')
doc=re.sub(r' \+ CPU 검증 (?:기준|기록) 1개','',doc)
doc=doc.replace(str(count)+'개 성능 구성',str(count)+'개 GPU 기초 측정 구성')
campaign=O/'gpu-campaign-status.json'
if campaign.exists():
 c=json.loads(campaign.read_text(encoding='utf-8'));label={'IN_PROGRESS':'제공 예제 GPU 시험 진행 중','COMPLETED':'제공 예제 GPU 시험 완료','COMPLETED_WITH_LIMITATIONS':'제공 예제 GPU 시험 완료 · 제약 사항 포함'}[c['status']]
 doc=doc.replace('시험 진행 중 · MI355X 1 GPU · '+str(count)+'개 GPU 기초 측정 구성 · 각 5회',label+' · MI355X 1 GPU · 제공 예제 '+str(c['counts']['PASS'])+'/'+str(c['expected_configurations'])+' PASS · 기초 GPU '+str(count)+'개 구성 별도')
 if c['status']!='IN_PROGRESS':doc=doc.replace('제공 예제 envs scaling 시험 · 진행 중','제공 예제 envs scaling 시험 · 실행 완료').replace('제공 예제 envs scaling · 진행 중','제공 예제 envs scaling · 실행 완료')
if args.public:
 doc=doc.replace('confluence-report.md','report.md').replace('../docs/benchmark-recipes.md','../../../docs/benchmark-recipes.md').replace('evidence/results/software-sources-and-builds.json','software.json').replace('evidence/measurement-audit.json','gpu-campaign-status.json').replace('evidence/smoke-coverage.json','smoke-coverage.json').replace('evidence/gpu-smoke-coverage.json','smoke-coverage.json')
 doc=doc.replace('보고서 Markdown','공개 보고서 Markdown').replace('Confluence 초안에는 자동으로 반영하지 못했다. 첨부 Markdown과 images 폴더를 이용해 본문과 그림을 붙일 수 있다.','공개 본문과 집계 자료는 이 폴더에 있으며, 연결 설정과 개별 실행 로그는 포함하지 않는다.')
doc=doc.replace('64/64 PASS','64개 구성').replace('고객 설명에 사용할 시연 순서','실험 개요').replace('고객 설명 순서','실험 개요')
output.write_text(polite_html(doc),encoding='utf-8')
(O/'test-plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
print('Rendered',len(panels),'tabs from reviewed Markdown')
