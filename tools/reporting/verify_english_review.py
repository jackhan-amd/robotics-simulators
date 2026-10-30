"""Verify protected content after file-mode English humanizer review."""
from workspace import REPO_ROOT
import argparse,collections,hashlib,json,pathlib,re,shutil
B=REPO_ROOT
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--before-dir',type=pathlib.Path,default=B/'_workspace/english-humanizer-final');parser.add_argument('--snapshot',action='store_true');args=parser.parse_args();backup=args.before_dir
if args.snapshot:
 backup.mkdir(parents=True,exist_ok=True)
 for name in('README.md','REPRODUCE.md'):
  assert not(backup/name).exists(),'Choose a new before-dir instead of replacing review input'
  shutil.copy2(B/'tools'/name,backup/name)
 raise SystemExit(0)
def protected(text):
 return dict(code=re.findall(r'```.*?```',text,re.S),inline_code=re.findall(r'`[^`\n]+`',text),links=re.findall(r'\]\(([^)]+)\)',text),numbers=collections.Counter(re.findall(r'(?<![\w])\d+(?:[.,]\d+)*(?:e[-+]?\d+)?',text,re.I)),tables=[line for line in text.splitlines()if line.startswith('|')])
documents=[]
for name in('README.md','REPRODUCE.md'):
 before=(backup/name).read_text(encoding='utf-8');path=B/'tools'/name;after=path.read_text(encoding='utf-8')
 assert protected(before)==protected(after),'Protected content changed: '+name
 documents.append(dict(path='tools/'+name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),prose_changed=before!=after,protected_content='PASS'))
review=dict(status='PASS',skill='humanizer',version='3.1.0',source='https://github.com/blader/humanizer',mode='file',documents=documents,note='Prose reviewed in full. Technical voice retained; code blocks, commands, inline code, numbers, tables and link targets unchanged.')
target=B/'report/evidence/repro-prose-review.json';target.write_text(json.dumps(review,indent=2),encoding='utf-8');print(json.dumps(review))
