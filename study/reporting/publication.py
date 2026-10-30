"""Project private execution evidence into repository-relative publication data."""
from __future__ import annotations
from workspace import source_reference
import hashlib,json,pathlib,re
from workspace import REPO_ROOT,profile

DROP_KEYS={'run_id','smoke_run_id','utc','execution_utc','raw_artifact','command','environment','source_snapshots','source_snapshot_timing','log','trace_ref','private_evidence_ref'}
def repository_reference(text):
 """Name upstream files by repository path, never by their installed location."""
 normalized=str(text).replace('\\','/')
 match=re.search(r'/taichi/examples/(.+\.py)$',normalized)
 if match:return 'AMD Taichi provided example: '+match[1]+' (adapter: study/benchmarks/provided_replicas.py)'
 match=re.search(r'/upstream/([^/]+)/([^\s\"<>`]+)',normalized)
 if match:return match[1]+'/'+match[2]
 values=profile()
 gsplat=values.get('GSPLAT_SOURCE_ROOT','')
 if gsplat and normalized.startswith(gsplat.replace('\\','/')+'/'):return 'gsplat/'+normalized[len(gsplat)+1:]
 root=values.get('LAB_ROOT',values.get('STUDY_RUN_ROOT',''))
 if root and normalized.startswith(root+'/')and normalized.endswith('.py'):
  relative=normalized[len(root)+1:]
  if '/'not in relative:return source_reference(relative)
 return normalized
def sanitize_text(text):
 text=str(text)
 values=profile();replacements={}
 for key,value in values.items():
  if isinstance(value,str)and value and any(part in key for part in('ROOT','PATH','TARGET','CONFLUENCE')):
   replacements[value]='${'+key+'}';replacements[value.replace('\\','\\\\')]='${'+key+'}'
 replacements[str(REPO_ROOT)]='${REPO_ROOT}';replacements[str(REPO_ROOT).replace('\\','/')] ='${REPO_ROOT}'
 replacements[str(REPO_ROOT).replace('\\','\\\\')]='${REPO_ROOT}'
 target=values.get('STUDY_SSH_TARGET','')
 if'@'in target:replacements[target.rsplit('@',1)[1]]='<target host>'
 # Upstream and harness source files use source-tree paths in prose and logs.
 root=values.get('LAB_ROOT',values.get('STUDY_RUN_ROOT',''))
 if root:
  text=re.sub(re.escape(root)+r'/storage/upstream/([^/\s]+)/([^\s\"<>`:)]+)',lambda m:m[1]+'/'+m[2],text)
  text=re.sub(re.escape(root)+r'/([A-Za-z_][A-Za-z0-9_]*\.py)',lambda m:source_reference(m[1]),text)
 storage=values.get('STUDY_STORAGE_ROOT',root+'/storage'if root else'')
 for prefix in filter(None,(storage,'${STUDY_STORAGE_ROOT}')):
  text=re.sub(re.escape(prefix)+r'/official-taichi/root/[^\s\"<>`]+/taichi/examples/([^\s\"<>`]+\.py)',r'AMD Taichi provided example: \1 (adapter: study/benchmarks/provided_replicas.py)',text)
 for old,new in sorted(replacements.items(),key=lambda item:-len(item[0])):text=text.replace(old,new)
 if root:
  basename=pathlib.PurePosixPath(root).name
  text=text.replace(basename+'/storage/','${STUDY_STORAGE_ROOT}/')
 text=re.sub(r'\$\{(?:LAB_ROOT|STUDY_STORAGE_ROOT)\}/(?:storage/)?upstream/([^/\s]+)/([^\s\"<>`:)]+)',lambda m:m[1]+'/'+m[2],text)
 text=re.sub(r'\$\{LAB_ROOT\}/([A-Za-z_][A-Za-z0-9_]*\.py)',lambda m:source_reference(m[1]),text)
 text=re.sub(r'https://[^/\s<>]+\.atlassian\.net[^\s<>\"\x27)]*','<internal document>',text)
 text=re.sub(r'[A-Za-z]:[\\/]Users[\\/][^\s\"<>`]+','<local path>',text)
 text=re.sub(r'/home/[^\s\"<>`:)]+','<external path>',text)
 # Per-execution identifiers stay in private evidence, outside publication data.
 text=re.sub(r'\b\d{8}T\d{6}Z[-_][A-Za-z0-9_-]+','<execution>',text)
 return text
def aggregate(value):
 if isinstance(value,dict):return {sanitize_text(str(k)):aggregate(v)for k,v in value.items()if k not in DROP_KEYS and not k.endswith('_run_id')}
 if isinstance(value,list):return [aggregate(v)for v in value]
 if isinstance(value,str):return sanitize_text(value)
 return value
def final_run_ids(campaign):
 ids=set()
 for model in campaign['campaigns']:
  if model['smoke_status']=='PASS'and model.get('smoke_run_id'):ids.add(model['smoke_run_id'])
  ids.update(point['run_id']for point in model['points']if point['status']=='PASS'and point.get('run_id'))
 return ids
def final_evidence(source,destination,campaign):
 """Export selected successful final receipts; diagnostic histories stay private."""
 destination.mkdir(parents=True,exist_ok=True);mapping={}
 for runid in sorted(final_run_ids(campaign)):
  receipt=json.loads((source/'evidence/results'/(runid+'.json')).read_text(encoding='utf-8'))
  assert receipt['status']=='PASS'and receipt.get('gpu_requested')
  name=receipt['engine']+'-'+receipt['case'];name=re.sub(r'[^A-Za-z0-9_.-]','-',name)
  mapping[runid]=name
  cleaned=aggregate(receipt)
  cleaned['reproduction_command']=aggregate(receipt.get('command',[]))
  allowed={'LAB_ROOT','STUDY_STORAGE_ROOT','ROCM_PATH','HIP_PATH','LD_LIBRARY_PATH','PYTHONPATH','XLA_FLAGS','JAX_PLATFORMS','XLA_PYTHON_CLIENT_PREALLOCATE','ROCR_VISIBLE_DEVICES','HIP_VISIBLE_DEVICES','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','LIBGL_ALWAYS_SOFTWARE','PYOPENGL_PLATFORM','PYGLET_HEADLESS','EGL_PLATFORM'}
  cleaned['reproduction_environment']=aggregate({k:v for k,v in receipt.get('environment',{}).items()if k in allowed})
  portable={}
  for relative in cleaned.get('source_sha256',{}):
   source_file=REPO_ROOT/relative
   if source_file.is_file()and source_file.resolve().is_relative_to(REPO_ROOT):portable[relative]=hashlib.sha256(source_file.read_bytes()).hexdigest()
  cleaned['portable_source_sha256']=portable
  cleaned['source_version_note']='source_sha256 identifies the executed file. portable_source_sha256 identifies repository code after replacing machine paths with configuration; those bytes can differ without changing the measurement algorithm.'
  cleaned['execution_log']=name+'.log';cleaned['scope']='Final accepted GPU execution only; private setup paths replaced with repository references or configuration names.'
  raw=(source/'evidence/results'/receipt['log']).read_text(encoding='utf-8',errors='replace')
  if receipt['engine']=='mujoco'and'Failed to import warp'in raw:
   cleaned['log_note']='Optional WARP modules are absent in this JAX environment. This accepted execution explicitly selected the JAX implementation on ROCm; MJWarp was measured in a separate environment.'
  (destination/(name+'.json')).write_text(json.dumps(cleaned,ensure_ascii=False,indent=2),encoding='utf-8')
  (destination/(name+'.log')).write_text(sanitize_text(raw),encoding='utf-8')
 expected={name+extension for name in mapping.values()for extension in('.json','.log')}
 archive=source/'evidence/private-final-history';assert archive.resolve().is_relative_to(source.resolve())
 for old in destination.iterdir():
  if old.suffix not in('.json','.log')or old.name in expected:continue
  assert old.resolve().is_relative_to(destination.resolve())and destination.resolve().is_relative_to(source.resolve())
  archive.mkdir(parents=True,exist_ok=True);digest=hashlib.sha256(old.read_bytes()).hexdigest()[:12]
  target=archive/(old.stem+'-'+digest+old.suffix);number=0
  while target.exists():
   number+=1;target=archive/(old.stem+'-'+digest+'-'+str(number)+old.suffix)
  assert target.resolve().is_relative_to(archive.resolve());old.rename(target)
 return mapping
