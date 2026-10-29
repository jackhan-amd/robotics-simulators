"""Restore checkout line endings only when they match the pinned upstream hash."""
import argparse,hashlib,json,pathlib
B=pathlib.Path(__file__).resolve().parents[1];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args();changes=[]
for component in json.loads((B/'configs/third-party-licenses.json').read_text(encoding='utf-8'))['components']:
 for notice in component.get('notices',[]):
  path=(B/notice['file']).resolve();assert path.is_relative_to((B/'third_party_notices').resolve())
  original=path.read_bytes()
  if hashlib.sha256(original).hexdigest()==notice['sha256']:continue
  restored=original.replace(b'\r\n',b'\n')
  assert hashlib.sha256(restored).hexdigest()==notice['sha256'],'Mismatch beyond checkout line endings: '+notice['file']
  changes.append((path,restored))
if a.apply:
 for path,payload in changes:path.write_bytes(payload)
print(json.dumps(dict(status='RESTORED'if a.apply else'PREVIEW',files=len(changes),scope='Exact pinned upstream bytes; no legal text edits')))
