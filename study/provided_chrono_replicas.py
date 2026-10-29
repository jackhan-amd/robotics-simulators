"""Synchronized replicas of original Chrono examples, initialization excluded."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import argparse,hashlib,json,os,pathlib,re,statistics,subprocess,time,uuid
p=argparse.ArgumentParser();p.add_argument('--kind',choices=['fsi','dem'],required=True);p.add_argument('--envs',type=int,required=True);p.add_argument('--smoke',action='store_true');a=p.parse_args();horizon=.1 if a.kind=='fsi'else .001
R=run_root();S=storage_root();binary=R/'provided-chrono/build'/('provided_'+a.kind);root=S/'private/provided-chrono'/uuid.uuid4().hex;root.mkdir(parents=True);env=os.environ.copy();sdk=env['ROCM_PATH'];env.update(LD_LIBRARY_PATH=str(S/'build/chrono-hip-devel/lib')+':'+sdk+'/lib:'+sdk+'/lib/llvm/lib',STUDY_CHRONO_DATA=str(S/'upstream/chrono/data')+'/',STUDY_CHRONO_OUTPUT=str(root)+'/',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
def trial(rep):
 folder=root/str(rep);folder.mkdir();go=folder/'go';validate=folder/'validate';procs=[];logs=[]
 try:
  for i in range(a.envs):
   e=env.copy();e.update(STUDY_BENCH_READY=str(folder/f'{i}.ready'),STUDY_BENCH_GO=str(go),STUDY_BENCH_DONE=str(folder/f'{i}.done'),STUDY_BENCH_VALIDATE=str(validate))
   cmd=[str(binary)]
   if a.kind=='fsi':cmd+=['--no_vis','--quiet','--t_end','0.1']
   else:
    source=S/'upstream/chrono/data/dem/repose.json';text=source.read_text();text=re.sub(r'("time_end"\s*:\s*)[-+0-9.eE]+',r'\g<1>'+str(horizon),text,count=1);text=re.sub(r'("output_dir"\s*:\s*)"[^"]+"',r'\g<1>"replica_'+str(i)+'"',text,count=1);f=folder/f'{i}.json';f.write_text(text);cmd+=[str(f)]
   f=(folder/f'{i}.log').open('w');logs.append(f);procs.append(subprocess.Popen(cmd,env=e,cwd=folder,stdout=f,stderr=subprocess.STDOUT))
  deadline=time.monotonic()+300
  while not all((folder/f'{i}.ready').exists()for i in range(a.envs)):
   if any(c.poll()is not None for c in procs):raise RuntimeError('Native provided example exited before initialization barrier')
   if time.monotonic()>deadline:raise TimeoutError('Native provided example init timeout')
   time.sleep(.01)
  start=time.perf_counter();go.touch();deadline=time.monotonic()+900
  while not all((folder/f'{i}.done').exists()for i in range(a.envs)):
   if any(c.poll()not in(None,0)for c in procs):raise RuntimeError('Native example failed during stepping')
   if time.monotonic()>deadline:raise TimeoutError('Native provided example stepping timeout')
   time.sleep(.001)
  elapsed=time.perf_counter()-start
  # Every process has synchronized and signalled .done; stop the common timer
  # before allowing any final GPU state readback from an early-finishing env.
  validate.touch()
  for c in procs:assert c.wait(timeout=60)==0
  for f in logs:f.close()
  records=[]
  for i in range(a.envs):
   text=(folder/f'{i}.log').read_text(errors='replace');record=json.loads(next(line.split('SMOKE_RESULT_JSON:',1)[1]for line in text.splitlines()if'SMOKE_RESULT_JSON:'in line));assert record['physics_valid'];records.append(record)
  return elapsed,records
 finally:
  for c in procs:
   if c.poll()is None:c.terminate()
  for c in procs:
   try:c.wait(timeout=5)
   except subprocess.TimeoutExpired:c.kill();c.wait()
  for f in logs:
   if not f.closed:f.close()
try:
 warm,preview=trial('warmup');times=[];checks=[]
 for rep in range(1 if a.smoke else 5):
  t,items=trial(rep);times.append(t);checks.append(items)
 model=checks[-1][0];steps=model['steps'];assert all(x['steps']==steps for row in checks for x in row);median=statistics.median(times)
 print(('SMOKE_RESULT_JSON:'if a.smoke else'BENCHMARK_RESULT_JSON:')+json.dumps(dict(engine='chrono',implementation='provided Chrono '+('SPH DamBreak'if a.kind=='fsi'else'DEM repose')+' / independent GPU processes',physics_valid=True,validation_barrier=True,backend_observed='hip',scene='demo_FSI-SPH_DamBreak.cpp'if a.kind=='fsi'else'demo_DEM_repose.cpp + data/dem/repose.json',source_commit='6f4004c358e5d0029aa3e39fc5ed13d66216f494',envs=a.envs,steps=steps,dt=model['dt'],particles_per_env=model['particles'],repeats=len(times),synchronized_rollout_s=times,median_s=median,env_step_per_s=a.envs*steps/median,step_per_s=steps/median,rtf_per_env=steps*model['dt']/median,warmup='one complete discarded process trial',warmup_s=warm,checks=checks,raw_artifact=str(root),scope='original model/material/solver unchanged; supported horizon: FSI 0.1s / DEM 0.001s; DEM initial-transient short window; one process per env; initialization excluded with ready/go/done barrier; native demo stepping and its own diagnostics included; all envs complete before final validation/readback via explicit validate barrier; particle/file output and GUI disabled')))
except Exception:
 for f in sorted(root.rglob('*.log')):print(str(f),f.read_text(errors='replace')[-1500:],flush=True)
 raise
