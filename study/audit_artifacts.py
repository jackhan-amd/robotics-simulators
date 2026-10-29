"""Validate delivered links, tab structure, embedded images and measurement data."""
import argparse,base64,hashlib,io,json,pathlib,re,sys,tempfile
from html.parser import HTMLParser
from urllib.parse import unquote
sys.path.insert(0,str(pathlib.Path(tempfile.gettempdir())/'robotics-study-plot-deps'))
from PIL import Image
B=pathlib.Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--data-dir',type=pathlib.Path,default=B/'report');parser.add_argument('--plan',type=pathlib.Path,default=B/'study/plan.json');args=parser.parse_args();O=args.data_dir;source=O/'mi355x-simulator-report.html'
class Page(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.hrefs=[];self.images=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id'in a:self.ids.append(a['id'])
  if tag=='a':self.hrefs.append(a.get('href',''))
  if tag=='img':self.images.append(a['src'])
p=Page();s=source.read_text(encoding='utf-8');p.feed(s)
assert '\ufffd'not in s
assert len(p.ids)==len(set(p.ids))
plan=json.loads(args.plan.read_text(encoding='utf-8'))
assert all(e['id']in p.ids for e in plan['engines'])
broken=[]
for url in p.hrefs:
 if url.startswith('#'):
  if url[1:]not in p.ids:broken.append(url)
 elif not re.match(r'\w+://',url):
  if not (source.parent/unquote(url.split('#')[0])).resolve().exists():broken.append(url)
assert not broken,broken
for uri in p.images:
 assert uri.startswith('data:image/'),uri
 Image.open(io.BytesIO(base64.b64decode(uri.split(',',1)[1]))).verify()
data=json.loads((O/'benchmark-data.json').read_text(encoding='utf-8'));assert len(data)==sum(e['measured_configurations']for e in plan['engines'])
excluded={'pybullet','drake','gazebo','sofa','urlab'}
assert not excluded.intersection(p.ids),'CPU-only simulator tab is outside the requested scope'
assert all(x.get('engine')not in excluded and x.get('backend_observed')not in('cpu','CPU')for x in data)
assert all(len(x['synchronized_rollout_s'])==5 and x['physics_valid']for x in data)
md=(O/'confluence-report.md').read_text(encoding='utf-8')
assert 'mujoco-cpu-bench'not in md and 'mujoco-cpu-bench'not in s
assert '시뮬레이터 탭에 상세 수록'not in md
assert {e['id']for e in plan['engines']if e.get('amd_solution')}=={'mujoco','instinct','genesis','taichi','gsplat'}
assert s.count('class="amd-mark"')>=15
assert 'AMD 코드·자료 기반' in md and '¹ 검은 AMD 블록' in md
assert '제공 예제 envs scaling ·' not in s
assert '| 실행 |' not in md
assert '고객 설명 순서' not in s and '고객 설명에 사용할 시연 순서' not in s
assert len(p.images)==len(re.findall(r'!\[[^\]]*\]\(images/[^)]+\)',md)), 'Every Markdown image must render, including collapsed reference sections'
for title in ('### 1. Simulator 설명','### 2. Software','### 3. Throughput','### 4. Throughput plot'):assert md.count(title)==len(plan['engines']),(title,md.count(title))
result=dict(status='PASS',simulator_tabs=len(plan['engines']),performance_records=len(data),repeats_each=5,embedded_images=len(p.images),local_links_checked=len(p.hrefs),broken_links=broken,report_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),markdown_sha256=hashlib.sha256((O/'confluence-report.md').read_bytes()).hexdigest())
(O/'evidence/artifact-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
