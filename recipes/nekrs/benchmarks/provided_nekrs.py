"""Supplied Taylor-Green vortex, original order/material/dt; bounded time horizon."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import argparse,difflib,hashlib,json,math,os,pathlib,re,shutil,statistics,subprocess,time,uuid
p=argparse.ArgumentParser();p.add_argument('--envs',type=int,required=True);p.add_argument('--smoke',action='store_true');a=p.parse_args();R=run_root();S=storage_root();source=S/'upstream/nekrs/examples/tgv';root=S/'private/provided-tgv'/uuid.uuid4().hex;root.mkdir(parents=True);steps=100
before=(source/'tgv.udf').read_text();helper=r'''
#include <chrono>
#include <filesystem>
#include <fstream>
#include <thread>
#include <cstdlib>
static void study_barrier(int tstep){
 if(tstep==0){
  platform->device.finish();
  if(const char* p=std::getenv("STUDY_BENCH_READY"))std::ofstream(p).put('1');
  auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(1200);
  if(const char* p=std::getenv("STUDY_BENCH_GO"))while(!std::filesystem::exists(p)){
   if(std::chrono::steady_clock::now()>deadline)throw std::runtime_error("study barrier timeout");
   std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
 }
 if(tstep==100){platform->device.finish();if(const char* p=std::getenv("STUDY_BENCH_DONE"))std::ofstream(p).put('1');}
}
'''
# UDF is compiled after platform declarations; put helpers immediately before callbacks.
after=before.replace('void UDF_ExecuteStep(double time, int tstep)',helper+'\nvoid UDF_ExecuteStep(double time, int tstep)').replace('  printDiagnostics(nrs, time, tstep);','  printDiagnostics(nrs, time, tstep);\n  study_barrier(tstep);')
(R/'evidence/provided-tgv-udf.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='original/tgv.udf',tofile='instrumented/tgv.udf')))
dirs=[];casebase=S/'cache/provided-nekrs-tgv-cases';casebase.mkdir(parents=True,exist_ok=True)
for i in range(a.envs):
 d=casebase/str(i)
 if not d.exists():
  seeds=[old/'0'for old in sorted((S/'private/provided-tgv').iterdir())if(old/'trial-warmup/0.done').exists()and(old/'0/tgv.udf').exists()and(old/'0/tgv.udf').read_text()==after]
  seed=casebase/'0'if(casebase/'0').exists()else(seeds[-1]if seeds else source)
  shutil.copytree(seed,d)
 (d/'tgv.udf').write_text(after);text=(d/'tgv.par').read_text();text=re.sub(r'^endTime\s*=.*$', 'endTime = 0.3',text,flags=re.M);(d/'tgv.par').write_text(text);dirs.append(d)
env=os.environ.copy();sdk=env['ROCM_PATH'];env.update(NEKRS_HOME=str(S/'install/nekrs-native'),OMPI_MCA_pml='ob1',OMPI_MCA_btl='self,tcp',UCX_TLS='self,sm',OCCA_HIP_COMPILER=sdk+'/bin/hipcc',PATH=str(S/'tools/bin')+':'+sdk+'/bin:'+env['PATH'],LD_LIBRARY_PATH=sdk+'/lib:'+sdk+'/lib/llvm/lib:'+str(S/'tools/lib')+':'+str(S/'install/nekrs-native/lib'))
def trial(rep):
 folder=root/('trial-'+str(rep));folder.mkdir();go=folder/'go';logs=[];procs=[]
 try:
  for i,d in enumerate(dirs):
   e=env.copy();e.update(NEKRS_CACHE_DIR=str(d/'.cache'),OCCA_CACHE_DIR=str(d/'.occa'),STUDY_BENCH_READY=str(folder/f'{i}.ready'),STUDY_BENCH_GO=str(go),STUDY_BENCH_DONE=str(folder/f'{i}.done'));f=(folder/f'{i}.log').open('w');logs.append(f);procs.append(subprocess.Popen([str(S/'install/nekrs-native/bin/nekrs'),'--setup','tgv.par','--backend','HIP','--device-id','0'],cwd=d,env=e,stdout=f,stderr=subprocess.STDOUT))
  deadline=time.monotonic()+1200
  while not all((folder/f'{i}.ready').exists()for i in range(a.envs)):
   if any(p.poll()is not None for p in procs):raise RuntimeError('TGV init/JIT failed')
   if time.monotonic()>deadline:raise TimeoutError('TGV init/JIT timeout')
   time.sleep(.02)
  start=time.perf_counter();go.touch();deadline=time.monotonic()+900
  while not all((folder/f'{i}.done').exists()for i in range(a.envs)):
   if any(p.poll()not in(None,0)for p in procs):raise RuntimeError('TGV native stepping failed')
   if time.monotonic()>deadline:raise TimeoutError('TGV stepping timeout')
   time.sleep(.001)
  elapsed=time.perf_counter()-start
  for p in procs:assert p.wait(timeout=60)==0
  for f in logs:f.close()
  checks=[]
  for i in range(a.envs):
   text=(folder/f'{i}.log').read_text();v=[tuple(map(float,x))for x in re.findall(r'time=\s*([-+0-9.eE]+)\s+enst=\s*([-+0-9.eE]+)\s+energy=\s*([-+0-9.eE]+)',text)];assert v
   valid=all(math.isfinite(x)for row in v for x in row)and abs(v[-1][0]-.3)<1e-6 and v[-1][1]>0 and 0<v[-1][2]<=v[0][2]+1e-5 and 'HIP'in text
   checks.append(dict(valid=valid,first_diagnostic=v[0],last_diagnostic=v[-1],diagnostic_count=len(v)));assert valid
  return elapsed,checks
 finally:
  for p in procs:
   if p.poll()is None:p.terminate();p.wait(timeout=15)
  for f in logs:f.close()
try:
 warm,_=trial('warmup');times=[];checks=[]
 for rep in range(1 if a.smoke else 5):t,c=trial(rep);times.append(t);checks.append(c)
 median=statistics.median(times)
 print(('SMOKE_RESULT_JSON:'if a.smoke else'BENCHMARK_RESULT_JSON:')+json.dumps(dict(engine='nekrs',implementation='provided TGV / independent HIP processes',scene='examples/tgv Re=1600',physics_valid=True,backend_observed='hip',envs=a.envs,steps=100,dt=.003,polynomial_order=7,cubature_order=9,repeats=len(times),synchronized_rollout_s=times,median_s=median,env_step_per_s=a.envs*100/median,rtf_per_env=.3/median,warmup_s=warm,checks=checks,source_commit='96b3cf9e5bacede16568826c04a21bc0fe50dc7d',source_sha256=hashlib.sha256((source/'tgv.udf').read_bytes()).hexdigest(),mesh_sha256=hashlib.sha256((source/'tgv.re2').read_bytes()).hexdigest(),raw_artifact=str(root),scope='provided mesh/order/material/solver/dt unchanged; horizon shortened from 20 to 0.3 s; per-env one-rank HIP; init/JIT excluded via callback barrier; original energy/enstrophy diagnostics included; basic finite/decay sanity, not complete DNS validation')))
except Exception:
 for f in sorted(root.rglob('*.log')):print(str(f),f.read_text(errors='replace')[-2500:])
 raise
