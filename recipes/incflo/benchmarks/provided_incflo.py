"""Fixed original 128² cavity, independent GPU process replicas."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import argparse,hashlib,json,os,pathlib,re,statistics,subprocess,time,uuid
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--envs',type=int,required=True);p.add_argument('--smoke',action='store_true');a=p.parse_args();R=run_root();S=storage_root();source=S/'upstream/incflo/test_2d/benchmark.lid_driven_cavity';root=S/'private/provided-incflo'/uuid.uuid4().hex;root.mkdir(parents=True);steps=50
def fields(folder):
 plot=sorted(folder.glob('plt[0-9]*'))[-1];h=(plot/'Header').read_text().splitlines();nc=int(h[1]);names=h[2:2+nc];assert int(h[2+nc])==2;values=np.full((nc,128,128),np.nan)
 for name,offset in re.findall(r'FabOnDisk:\s+(\S+)\s+(\d+)',(plot/'Level_0/Cell_H').read_text()):
  with (plot/'Level_0'/name).open('rb')as f:
   f.seek(int(offset));line=f.readline();vec=[tuple(map(int,m.split(b',')))for m in re.findall(rb'\(([-0-9, ]+)\)',line)if len(m.split(b','))==2];lo,hi,kind=vec[-3:];nx,ny=hi[0]-lo[0]+1,hi[1]-lo[1]+1;assert line.startswith(b'FAB ((8');x=np.frombuffer(f.read(nx*ny*nc*8),dtype='<f8').reshape(nc,ny,nx);values[:,lo[1]:hi[1]+1,lo[0]:hi[0]+1]=x
 d=dict(zip(names,values));rho=d['density'];u=d['velx'];v=d['vely'];energy=float((.5*rho*(u*u+v*v)).mean());density=float(abs(rho-1000).max()/1000);velocity=float(max(abs(u).max(),abs(v).max()));simtime=float(h[3+nc]);text=(folder/'stdout.log').read_text()
 return dict(valid=bool(np.isfinite(values).all()and density<1e-10 and 0<velocity<=1.5 and energy>0 and simtime>0 and plot.name.endswith('00050')and 'Initializing HIP'in text),density_relative_error=density,max_velocity=velocity,mean_kinetic_energy=energy,simulation_time=simtime,plot=str(plot))
def trial(rep):
 folder=root/str(rep);folder.mkdir();go=folder/'go';procs=[];logs=[];dirs=[]
 try:
  for i in range(a.envs):
   d=folder/str(i);d.mkdir();dirs.append(d);env=os.environ.copy();env.update(STUDY_BENCH_READY=str(d/'ready'),STUDY_BENCH_GO=str(go),STUDY_BENCH_DONE=str(d/'done'),STUDY_BENCH_VALIDATE=str(folder/'validate'));f=(d/'stdout.log').open('w');logs.append(f);procs.append(subprocess.Popen([str(R/'provided-incflo/incflo.ex'),str(source),'amrex.the_arena_init_size=67108864'],cwd=d,env=env,stdout=f,stderr=subprocess.STDOUT))
  deadline=time.monotonic()+300
  while not all((d/'ready').exists()for d in dirs):
   if any(p.poll()is not None for p in procs):raise RuntimeError('initialization failed')
   if time.monotonic()>deadline:raise TimeoutError('init timeout')
   time.sleep(.005)
  start=time.perf_counter();go.touch();deadline=time.monotonic()+600
  while not all((d/'done').exists()for d in dirs):
   if any(p.poll()not in(None,0)for p in procs):raise RuntimeError('stepping failed')
   if time.monotonic()>deadline:raise TimeoutError('step timeout')
   time.sleep(.001)
  elapsed=time.perf_counter()-start;(folder/'validate').touch()
  for p in procs:assert p.wait(timeout=30)==0
  for f in logs:f.close()
  checks=[fields(d)for d in dirs];assert all(c['valid']for c in checks);return elapsed,checks
 finally:
  for p in procs:
   if p.poll()is None:
    p.terminate()
    try:p.wait(timeout=10)
    except subprocess.TimeoutExpired:p.kill();p.wait()
  for f in logs:f.close()
try:
 warm,_=trial('warmup');times=[];checks=[]
 for rep in range(1 if a.smoke else 5):t,c=trial(rep);times.append(t);checks.append(c)
 median=statistics.median(times)
 payload=dict(engine='incflo',implementation='provided cavity / independent HIP processes',scene='test_2d/benchmark.lid_driven_cavity unmodified input',physics_valid=True,backend_observed='hip',envs=a.envs,steps=steps,grid=[128,128],cells_per_env=16384,repeats=len(times),synchronized_rollout_s=times,median_s=median,env_step_per_s=a.envs*steps/median,cell_updates_per_s=a.envs*steps*16384/median,warmup_s=warm,checks=checks,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_commit='ccb90bc41d9def18dddc4e1c4122a7d517add630',dt='original CFL=0.45, fixed_dt=-1',raw_artifact=str(root),validation_barrier=True,arena_init_bytes=67108864,scope='native ready/go/done/validation-release barriers; InitData excluded; original 50 steps, 128², material, lid and CFL unchanged; provided plot output and diagnostics included; finalization and validation released only after all env timers finish')
 print(('SMOKE_RESULT_JSON:'if a.smoke else'BENCHMARK_RESULT_JSON:')+json.dumps(payload))
except Exception:
 for f in root.rglob('stdout.log'):print(str(f),f.read_text(errors='replace')[-2000:])
 raise
