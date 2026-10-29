from workspace import expand_runtime, run_root, runtime_path
import hashlib,json,os,pathlib,shutil,tarfile
R=run_root();E=R/'evidence';out=R/'evidence-export.tar.gz'
# Keep native per-trial logs and exact bounded inputs, without caches or payloads.
for receipt in list(E.glob('*.json')):
 try:record=json.loads(receipt.read_text())
 except Exception:continue
 if not isinstance(record,dict)or not record.get('gpu_requested')or 'run_id'not in record:continue
 for result in record.get('results',[]):
  raw=result.get('raw_artifact')
  if not raw:continue
  root=pathlib.Path(raw)
  if not root.is_dir()or not root.resolve().is_relative_to((R/'storage/private').resolve()):continue
  destination=E/'native-artifacts'/record['run_id'];manifest=[]
  for folder,dirs,names in os.walk(root):
   dirs[:]=[d for d in dirs if d not in('.cache','.occa','.git','__pycache__')]
   for name in names:
    source=pathlib.Path(folder)/name
    if source.suffix not in('.log','.json','.par')or source.stat().st_size>20_000_000:continue
    target=destination/source.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists()or source.stat().st_mtime_ns!=target.stat().st_mtime_ns:shutil.copy2(source,target)
    manifest.append(dict(file=str(target.relative_to(E)),sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
  if manifest:(destination/'manifest.json').write_text(json.dumps(dict(original_root=str(root),files=manifest),indent=2))
with tarfile.open(out,'w:gz')as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
print('EXPORTED',out.stat().st_size,'bytes')
