"""Supplied TGV trajectory: 100 warm steps + five consecutive 100-step windows."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import argparse,difflib,hashlib,json,math,os,pathlib,re,shutil,statistics,subprocess,time,uuid
p=argparse.ArgumentParser();p.add_argument('--envs',type=int,required=True);p.add_argument('--smoke',action='store_true');a=p.parse_args();R=run_root();S=storage_root();source=S/'upstream/nekrs/examples/tgv';root=S/'private/provided-tgv-windows'/uuid.uuid4().hex;root.mkdir(parents=True);windows=1 if a.smoke else 5;total_steps=100*(windows+1)
before=(source/'tgv.udf').read_text();helper=r'''
#include <chrono>
#include <filesystem>
#include <fstream>
#include <thread>
#include <cstdlib>
static void study_windows(int tstep){
 if(tstep<100 || tstep%100)return;
 platform->device.finish();
 const int index=tstep/100-1;
 std::string base=std::getenv("STUDY_WINDOW_DIR");
 if(index>0)std::ofstream(base+"/done-"+std::to_string(index-1)).put('1');
 int windows=std::atoi(std::getenv("STUDY_WINDOWS"));
 if(index==windows){
  auto limit=std::chrono::steady_clock::now()+std::chrono::seconds(1200);
  std::string finish=std::getenv("STUDY_WINDOW_FINISH");
  while(!std::filesystem::exists(finish)){
   if(std::chrono::steady_clock::now()>limit)throw std::runtime_error("study completion barrier timeout");
   std::this_thread::sleep_for(std::chrono::milliseconds(1));
  }
  return;
 }
 std::ofstream(base+"/ready-"+std::to_string(index)).put('1');
 std::string go=std::string(std::getenv("STUDY_WINDOW_GO"))+"-"+std::to_string(index);
 auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(1200);
 while(!std::filesystem::exists(go)){
  if(std::chrono::steady_clock::now()>deadline)throw std::runtime_error("study window barrier timeout");
  std::this_thread::sleep_for(std::chrono::milliseconds(1));
 }
}
'''
after=before.replace('void UDF_ExecuteStep(double time, int tstep)',helper+'\nvoid UDF_ExecuteStep(double time, int tstep)').replace('  printDiagnostics(nrs, time, tstep);','  printDiagnostics(nrs, time, tstep);\n  study_windows(tstep);')
(R/'evidence/provided-tgv-windows.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='original/tgv.udf',tofile='instrumented/tgv.udf')))
casebase=S/'cache/provided-tgv-window-cases';casebase.mkdir(parents=True,exist_ok=True);dirs=[]
for i in range(a.envs):
 d=casebase/str(i)
 if not d.exists():
  seeds=[x/'0'for x in sorted((S/'private/provided-tgv').iterdir())if(x/'trial-warmup/0.done').exists()]
  seed=casebase/'0'if(casebase/'0').exists()else(seeds[-1]if seeds else source)
  shutil.copytree(source,d)
  if(seed/'.occa').exists():shutil.copytree(seed/'.occa',d/'.occa')
 (d/'tgv.udf').write_text(after);text=(source/'tgv.par').read_text();text=re.sub(r'^endTime\s*=.*$',f'endTime = {total_steps*.003:.3f}',text,flags=re.M);(d/'tgv.par').write_text(text);dirs.append(d)
env=os.environ.copy();sdk=env['ROCM_PATH'];env.update(NEKRS_HOME=str(S/'install/nekrs-native'),OMPI_MCA_pml='ob1',OMPI_MCA_btl='self,tcp',UCX_TLS='self,sm',OCCA_HIP_COMPILER=sdk+'/bin/hipcc',PATH=str(S/'tools/bin')+':'+sdk+'/bin:'+env['PATH'],LD_LIBRARY_PATH=sdk+'/lib:'+sdk+'/lib/llvm/lib:'+str(S/'tools/lib')+':'+str(S/'install/nekrs-native/lib'))
procs=[];logs=[];times=[];barriers=[];start_build=time.perf_counter()
def waitfiles(paths,timeout):
 deadline=time.monotonic()+timeout
 while not all(p.exists()for p in paths):
  if any(p.poll()is not None for p in procs):raise RuntimeError('Native TGV exited before window barrier')
  if time.monotonic()>deadline:raise TimeoutError('Native TGV setup/window timeout')
  time.sleep(.002)
try:
 for i,d in enumerate(dirs):
  barrier=root/str(i);barrier.mkdir();barriers.append(barrier);e=env.copy();e.update(NEKRS_CACHE_DIR=str(d/'.cache'),OCCA_CACHE_DIR=str(d/'.occa'),STUDY_WINDOW_DIR=str(barrier),STUDY_WINDOW_GO=str(root/'go'),STUDY_WINDOW_FINISH=str(root/'finish'),STUDY_WINDOWS=str(windows));f=(root/f'{i}.log').open('w');logs.append(f);procs.append(subprocess.Popen([str(S/'install/nekrs-native/bin/nekrs'),'--setup','tgv.par','--backend','HIP','--device-id','0'],cwd=d,env=e,stdout=f,stderr=subprocess.STDOUT))
 waitfiles([d/'ready-0'for d in barriers],1800);build_and_warm_s=time.perf_counter()-start_build
 for rep in range(windows):
  waitfiles([d/f'ready-{rep}'for d in barriers],60);start=time.perf_counter();(root/f'go-{rep}').touch();waitfiles([d/f'done-{rep}'for d in barriers],900);times.append(time.perf_counter()-start)
 (root/'finish').touch()
 for p in procs:assert p.wait(timeout=90)==0
 for f in logs:f.close()
 checks=[]
 for i in range(a.envs):
  text=(root/f'{i}.log').read_text();v=[tuple(map(float,x))for x in re.findall(r'time=\s*([-+0-9.eE]+)\s+enst=\s*([-+0-9.eE]+)\s+energy=\s*([-+0-9.eE]+)',text)];assert v
  valid=all(math.isfinite(x)for row in v for x in row)and abs(v[-1][0]-total_steps*.003)<1e-5 and v[-1][1]>0 and 0<v[-1][2]<=v[0][2]+1e-5 and 'HIP'in text;assert valid
  checks.append(dict(valid=valid,initial_diagnostic=v[0],final_diagnostic=v[-1],diagnostic_count=len(v)))
 median=statistics.median(times);payload=dict(engine='nekrs',implementation='provided TGV / independent HIP processes / consecutive windows',scene='examples/tgv Re=1600',physics_valid=True,backend_observed='hip',envs=a.envs,steps=100,dt=.003,polynomial_order=7,cubature_order=9,repeats=windows,repeat_mode='consecutive trajectory windows, not independently reset repetitions',warmup_steps=100,initialization_and_warmup_s=build_and_warm_s,synchronized_rollout_s=times,median_s=median,env_step_per_s=a.envs*100/median,rtf_per_env=.3/median,checks=checks,source_commit='96b3cf9e5bacede16568826c04a21bc0fe50dc7d',source_sha256=hashlib.sha256((source/'tgv.udf').read_bytes()).hexdigest(),mesh_sha256=hashlib.sha256((source/'tgv.re2').read_bytes()).hexdigest(),raw_artifact=str(root),scope='supplied mesh, p7/cubature9, Re1600, dt0.003, solver unchanged; 100 warm steps then five consecutive 100-step windows along one trajectory; synchronized ready/go/done barriers; init/JIT/warmup excluded; original diagnostics included; basic finite/energy-decay sanity only')
except Exception:
 for f in root.glob('*.log'):print(str(f),f.read_text(errors='replace')[-2200:])
 raise
finally:
 for p in procs:
  if p.poll()is None:
   p.terminate()
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:p.kill();p.wait()
 for f in logs:f.close()
print(('SMOKE_RESULT_JSON:'if a.smoke else'BENCHMARK_RESULT_JSON:')+json.dumps(payload),flush=True)
