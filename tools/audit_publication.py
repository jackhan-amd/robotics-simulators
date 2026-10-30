"""Check publishable source files for configured private identifiers."""
from __future__ import annotations
import argparse,hashlib,json,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from workspace import profile

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--directory',type=pathlib.Path,help='Check an explicit release directory instead of Git-visible source')
 args=parser.parse_args()
 if args.directory:files=[p for p in args.directory.rglob('*')if p.is_file()]
 else:
  names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode('utf-8').split('\0')
  files=[ROOT/p for p in names if p and(ROOT/p).is_file()]
 private=profile();tokens=[str(ROOT),ROOT.as_posix(),str(ROOT).replace('\\','\\\\')]
 for key,value in private.items():
  if isinstance(value,str)and len(value)>=6 and any(k in key for k in('ROOT','PATH','TARGET','CONFLUENCE')):
   tokens.extend((value,value.replace('\\','/'),value.replace('\\','\\\\')))
 target=private.get('STUDY_SSH_TARGET','')
 if'@'in target:tokens.append(target.rsplit('@',1)[1])
 findings=[];checked=0;notices=0
 for path in files:
  if path.suffix.lower()not in('.py','.md','.json','.html','.csv','.txt','.log','.sh','.toml','.yaml','.yml','.ps1'):continue
  checked+=1;text=path.read_text(encoding='utf-8',errors='replace')
  if any(token in text for token in tokens):findings.append(str(path.relative_to(ROOT))if path.is_relative_to(ROOT)else path.name)
 if not args.directory:
  for component in json.loads((ROOT/'configs/third-party-licenses.json').read_text(encoding='utf-8'))['components']:
   for notice in component.get('notices',[]):
    path=ROOT/notice['file'];notices+=1
    if not path.is_file()or hashlib.sha256(path.read_bytes()).hexdigest()!=notice['sha256']:findings.append('notice checksum: '+notice['file'])
 print(json.dumps({'status':'FAIL'if findings else'PASS','checked_files':checked,'notice_hashes_checked':notices,'files_with_private_values_or_notice_mismatch':findings},indent=2))
 return bool(findings)

if __name__=='__main__':raise SystemExit(main())
