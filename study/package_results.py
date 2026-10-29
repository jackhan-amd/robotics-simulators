"""Package reviewed source and final evidence, excluding diagnostic histories."""
import csv,hashlib,io,json,pathlib,re,subprocess,zipfile
from publication import aggregate,sanitize_text
B=pathlib.Path(__file__).resolve().parents[1];O=B/'report'
assert json.loads((O/'gpu-campaign-status.json').read_text(encoding='utf-8'))['status']=='COMPLETED','Finish the primary GPU campaign before packaging'
review=json.loads((O/'humanizer-review.json').read_text(encoding='utf-8'));assert review['status']=='PASS'
assert review['markdown_sha256']==hashlib.sha256((O/'confluence-report.md').read_bytes()).hexdigest(),'Review the current report snapshot before packaging'
subprocess.run(['python',str(B/'tools/audit_publication.py')],check=True)
names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=B).decode('utf-8').split('\0')
forbidden={'private','report','_workspace','.amd-validation','workspace'}
code=sorted({B/p for p in names if p and(B/p).is_file()and pathlib.Path(p).parts[0]not in forbidden and'__pycache__'not in pathlib.Path(p).parts})
source=O/'mi355x-reproduction-code.zip'
with zipfile.ZipFile(source,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for f in code:
  relative=f.relative_to(B).as_posix()
  if f.suffix=='.sh':z.writestr(relative,f.read_bytes().replace(b'\r\n',b'\n'))
  else:z.write(f,relative)
bundle=O/'mi355x-simulator-results.zip'
used_images=set(re.findall(r'images/([^\s)"\x27]+)',(O/'confluence-report.md').read_text(encoding='utf-8')))
files=[O/'mi355x-simulator-report.html',O/'confluence-report.md',B/'study/REPRODUCE.md']
files += [p for p in(O/'images').iterdir()if p.is_file()and p.name in used_images]
files += [p for p in(O/'evidence/final').iterdir()if p.is_file()and p.suffix in('.json','.log')]
document=(O/'mi355x-simulator-report.html').read_text(encoding='utf-8')
for link in re.findall(r'href="([^"]+)"',document):
 if link.startswith(('#','http:','https:','data:')):continue
 path=(O/link).resolve()
 assert path.is_relative_to(B),'Report dependency outside repository'
 assert path.exists(),'Missing report dependency: '+link
 assert not re.search(r'evidence/results/\d{8}T',link),'Historical run link remained'
 files.append(path)
json_names=('test-plan.json','benchmark-data.json','env-scaling-data.json','env-scaling-plan.json','gpu-campaign-status.json','humanizer-review.json')
with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for f in sorted(set(files)):
  if f.parent==O and f.name in json_names:continue
  relative=f.relative_to(B).as_posix()
  if f.name=='software-sources-and-builds.json':z.writestr(relative,(B/'study/software-observations.json').read_bytes())
  elif f.suffix=='.json':z.writestr(relative,json.dumps(aggregate(json.loads(f.read_text(encoding='utf-8'))),ensure_ascii=False,indent=2))
  elif f.suffix=='.csv':
   rows=list(csv.DictReader(f.open(encoding='utf-8-sig')));fields=[k for k in rows[0]if k!='run_id']if rows else[];output=io.StringIO();writer=csv.DictWriter(output,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(aggregate(rows));z.writestr(relative,output.getvalue())
  elif f.suffix=='.md'and not f.is_relative_to(O):z.write(f,relative)
  elif f.suffix in('.md','.html','.log'):
   raw=f.read_bytes().decode('utf-8');cleaned=sanitize_text(raw)
   if f==O/'confluence-report.md':assert hashlib.sha256(cleaned.encode('utf-8')).hexdigest()==review['markdown_sha256'],'Publication changed the reviewed Markdown'
   z.writestr(relative,cleaned)
  else:z.write(f,relative)
 for name in json_names:
  z.writestr('report/'+name,json.dumps(aggregate(json.loads((O/name).read_text(encoding='utf-8'))),ensure_ascii=False,indent=2))
 for name in('mjx-runtime-profile.json','gpu-smoke-coverage.json','measurement-audit.json','repro-prose-review.json','licenses-prose-review.json'):
  path=O/'evidence'/name
  if path.exists()and path not in files:z.writestr('report/evidence/'+name,json.dumps(aggregate(json.loads(path.read_text(encoding='utf-8'))),ensure_ascii=False,indent=2))
 z.write(source,source.relative_to(B).as_posix())
manifest=[dict(file=f.name,bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest())for f in(source,bundle)]
(O/'delivery-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(manifest))
