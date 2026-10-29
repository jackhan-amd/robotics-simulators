"""Native single-rank HIP Ethier case, numerical gates from the repository smoke."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import argparse,json,math,os,pathlib,re,shutil,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--steps',type=int,default=10);p.add_argument('--order',type=int,default=5);a=p.parse_args()
R=run_root();S=storage_root();root=runtime_path('${ETHIER_CASE_ROOT}')/f'p{a.order}-n{a.steps}';root.parent.mkdir(exist_ok=True)
if not root.exists():shutil.copytree(S/'upstream/nekrs/examples/ethier',root)
par=root/'ethier.par';text=par.read_text();text=re.sub(r'polynomialOrder\s*=\s*\d+',f'polynomialOrder = {a.order}',text);text=re.sub(r'numSteps\s*=\s*\d+',f'numSteps = {a.steps}',text);text=re.sub(r'checkpointInterval\s*=\s*\d+','checkpointInterval = 10000',text);par.write_text(text)
env=os.environ.copy();env.update(NEKRS_HOME=str(S/'install/nekrs-native'),NEKRS_CACHE_DIR=str(root/'.cache'),OCCA_CACHE_DIR=str(root/'.occa'),OMPI_MCA_pml='ob1',OMPI_MCA_btl='self,tcp',UCX_TLS='self,sm',OMP_NUM_THREADS='1',OCCA_HIP_COMPILER=os.environ['ROCM_PATH']+'/bin/hipcc')
env['PATH']=str(S/'tools/bin')+':'+os.environ['ROCM_PATH']+'/bin:'+env['PATH'];env['LD_LIBRARY_PATH']=os.environ['ROCM_PATH']+'/lib:'+os.environ['ROCM_PATH']+'/lib/llvm/lib:'+str(S/'tools/lib')+':'+str(S/'install/nekrs-native/lib')
cmd=[str(S/'install/nekrs-native/bin/nekrs'),'--setup','ethier.par','--backend','HIP','--device-id','0']
start=time.perf_counter();c=subprocess.run(cmd,cwd=root,env=env,capture_output=True,text=True,timeout=900);elapsed=time.perf_counter()-start;(root/'stdout.log').write_text(c.stdout);(root/'stderr.log').write_text(c.stderr);print(c.stdout,flush=True);print(c.stderr,flush=True)
if c.returncode:raise SystemExit(c.returncode)
rows=[]
for line in c.stdout.splitlines():
 if 'L2 err'in line:
  vals=re.findall(r'[-+]?\d+(?:\.\d*)?(?:[EeDd][-+]?\d+)?',line.split('L2 err')[0]);rows.append([float(x.replace('D','E').replace('d','e'))for x in vals])
last=rows[-1]if rows else[]
gates=dict(steps=bool(last)and int(last[0])==a.steps,time=bool(last)and abs(last[1]-.002*a.steps)<1e-8,finite=bool(rows)and all(math.isfinite(x)for row in rows for x in row),velocity=bool(last)and abs(last[2])<=1e-3,pressure=bool(last)and abs(last[3])<=.1,scalar=bool(last)and max(abs(x)for x in last[4:6])<=1e-3,hip='HIP'in c.stdout)
step_times=[float(x)for x in re.findall(r'elapsedStep=\s*([-+0-9.eE]+)s',c.stdout)]
steady=step_times[10:] if len(step_times)>10 else []
print('SMOKE_RESULT_JSON:'+json.dumps(dict(engine='nekrs',implementation='nekRS native Ethier',backend_observed='hip',physics_valid=all(gates.values()),gates=gates,steps=a.steps,dt=.002,polynomial_order=a.order,elements=32,last_l2_row=last,wall_s=elapsed,steady_step_s=steady,raw_artifact=str(root))))
raise SystemExit(0 if all(gates.values()) else 3)
