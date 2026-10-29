"""Record one isolated engine command and numerical marker, never infer PASS from rc."""
from workspace import expand_runtime, run_root, runtime_path
import argparse,datetime,fcntl,hashlib,json,os,pathlib,shutil,signal,subprocess,time,uuid
p=argparse.ArgumentParser();p.add_argument('--engine',required=True);p.add_argument('--case',required=True);p.add_argument('--gpu',action='store_true');p.add_argument('--wait',action='store_true');p.add_argument('--timeout',type=int,default=900);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
R=run_root();E=R/'evidence';E.mkdir(exist_ok=True)
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');runid=stamp+'-'+a.case+'-'+uuid.uuid4().hex[:6]
cmd=a.command[1:] if a.command and a.command[0]=='--' else a.command
env=os.environ.copy();env.update(STUDY_AMD_ARCH='gfx950',STUDY_AMD_NAME='MI355X',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
if not a.gpu:env.update(ROCR_VISIBLE_DEVICES='',HIP_VISIBLE_DEVICES='',CUDA_VISIBLE_DEVICES='')
if a.wait:
 def start_order(pid):return(int((pathlib.Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()[19]),pid)
 my_order=start_order(os.getpid());announced=False
 while True:
  older=[]
  for entry in pathlib.Path('/proc').iterdir():
   if not entry.name.isdigit()or int(entry.name)==os.getpid():continue
   try:
    args=(entry/'cmdline').read_bytes().split(b'\0')
    if str(R/'run_remote.py').encode()in args and start_order(int(entry.name))<my_order:older.append(int(entry.name))
   except (FileNotFoundError,PermissionError,ProcessLookupError):continue
  if not older:break
  if not announced:print('FIFO_WAIT',a.case,'older study recorder PIDs',sorted(older),flush=True);announced=True
  time.sleep(.25)
lock=(R/'gpu.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX if a.wait else fcntl.LOCK_EX|fcntl.LOCK_NB)
if a.gpu:
 subprocess.run(['amd-smi','process','--json'],stdout=(E/(runid+'-process-before.json')).open('w'),stderr=subprocess.STDOUT)
 subprocess.run(['amd-smi','metric','--json'],stdout=(E/(runid+'-metric-before.json')).open('w'),stderr=subprocess.STDOUT)
source_hashes={};source_snapshots={}
for arg in cmd:
 path=pathlib.Path(arg)
 if not path.is_absolute():path=R/'repo'/path
 if path.is_file()and path.suffix in('.py','.xml','.in','.par'):
  digest=hashlib.sha256(path.read_bytes()).hexdigest();source_hashes[str(path)]=digest;snapshot=E/'source-snapshots'/runid/(digest[:12]+'-'+path.name);snapshot.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,snapshot);source_snapshots[str(path)]=str(snapshot.relative_to(E))
execution_utc=datetime.datetime.now(datetime.timezone.utc).isoformat();start=time.perf_counter();log=E/(runid+'.log')
with log.open('w') as f:
 child=subprocess.Popen(cmd,env=env,cwd=R/'repo',stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
 try:rc=child.wait(timeout=a.timeout)
 except subprocess.TimeoutExpired:
  os.killpg(child.pid,signal.SIGTERM)
  try:child.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
  rc=124
raw=log.read_text(errors='replace');markers=[]
for line in raw.splitlines():
 for tag in ('SMOKE_RESULT_JSON:','BENCHMARK_RESULT_JSON:'):
  if tag in line:
   try:markers.append(json.loads(line.split(tag,1)[1]))
   except Exception:pass
valid=bool(markers) and all(x.get('physics_valid',x.get('g1',False)) for x in markers) and rc==0
receipt_keys=['LAB_ROOT','STUDY_STORAGE_ROOT','STUDY_AMD_ARCH','STUDY_AMD_NAME','ROCR_VISIBLE_DEVICES','HIP_VISIBLE_DEVICES','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','ROCM_PATH','HIP_PATH','LD_LIBRARY_PATH','PYTHONPATH','STUDY_WARP_CACHE','XLA_PYTHON_CLIENT_PREALLOCATE','XLA_FLAGS','JAX_PLATFORMS','LIBERO_CONFIG_PATH','HP_RENDERER','HP_OBS_LAG','HP_SUCCESS_MODE','MUJOCO_GL','PYOPENGL_PLATFORM','EGL_PLATFORM','LIBGL_ALWAYS_SOFTWARE','HIPRTC_COMPILE_OPTIONS_APPEND']
result=dict(engine=a.engine,case=a.case,run_id=runid,utc=stamp,execution_utc=execution_utc,command=cmd,environment={k:env[k]for k in receipt_keys if k in env},source_sha256=source_hashes,source_snapshots=source_snapshots,source_snapshot_timing='before subprocess launch',repository_commit='d1adb4a0cd5f55ce80443e642092190de9d12f6e',rc=rc,wall_s=time.perf_counter()-start,status=('PASS' if a.gpu else 'CPU_ONLY') if valid else ('BLOCKED' if rc in (124,127) else 'FAIL'),gpu_requested=a.gpu,results=markers,log=log.name)
(E/(runid+'.json')).write_text(json.dumps(result,indent=2))
if a.gpu:subprocess.run(['amd-smi','metric','--json'],stdout=(E/(runid+'-metric-after.json')).open('w'),stderr=subprocess.STDOUT)
print(json.dumps({k:v for k,v in result.items() if k!='results'}));print(raw[-2500:]);raise SystemExit(rc)
