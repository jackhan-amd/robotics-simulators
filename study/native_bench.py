"""Build measured variants separately, retaining original solver and physics gates."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import argparse,json,os,pathlib,statistics,subprocess,time
p=argparse.ArgumentParser();p.add_argument('engine',choices=['chrono-fsi','chrono-dem']);a=p.parse_args()
R=run_root();S=storage_root();repo=R/'repo';dest=R/'native-bench'/a.engine;dest.mkdir(parents=True,exist_ok=True)
env=os.environ.copy();env['PATH']=str(S/'venvs/base/bin')+':'+str(S/'tools/bin')+':'+env['PATH']
def run(cmd):print('+',*map(str,cmd),flush=True);subprocess.run(list(map(str,cmd)),env=env,check=True,timeout=600)
if a.engine.startswith('chrono'):
 source=repo/'smokes/chrono';text=(source/('fsi_sph.cpp'if a.engine=='chrono-fsi'else'dem.cpp')).read_text()
 text=text.replace('if (steps != 10 && steps != 50) return 2;','if (steps < 1 || steps > 1000) return 2;')
 if a.engine=='chrono-fsi':
  # Keep validation readbacks for this small reference benchmark and label the cost.
  text=text.replace('for (int n = 1; n <= steps; ++n) {','for (int n = 1; n <= steps; ++n) {\n        if(n == 11) begin = std::chrono::steady_clock::now();')
 else:
  text=text.replace('#include <iostream>','#include <iostream>\n#include <chrono>')
  text=text.replace('for (int n = 1; n <= steps; ++n) {','auto begin = std::chrono::steady_clock::now();\n    for (int n = 1; n <= steps; ++n) {\n        if(n == 11) begin = std::chrono::steady_clock::now();')
  text=text.replace('bool conserved = count == 27','double step_s=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();\n    bool conserved = count == 27')
  text=text.replace('<< ",\\\"radius_cm', '<< ",\\\"step_wall_s\\\":" << step_s << ",\\\"radius_cm')
 (dest/'fsi_sph.cpp').write_text(text if a.engine=='chrono-fsi'else(source/'fsi_sph.cpp').read_text())
 (dest/'dem.cpp').write_text(text if a.engine=='chrono-dem'else(source/'dem.cpp').read_text())
 (dest/'CMakeLists.txt').write_text((source/'CMakeLists.txt').read_text())
 run(['cmake','-S',dest,'-B',dest/'build','-G','Ninja','-DChrono_DIR='+str(S/'build/chrono-hip-devel/cmake'),'-DSTUDY_BACKEND=hip','-DSTUDY_WITH_DEM=ON','-DCHRONO_ROCM_ROOT='+os.environ['ROCM_PATH'],'-DCMAKE_PREFIX_PATH='+os.environ['ROCM_PATH'],'-DEIGEN3_INCLUDE_DIR='+str(S/'upstream/eigen')]);run(['cmake','--build',dest/'build','--parallel','4'])
 binary=dest/'build'/('chrono_fsi_smoke'if a.engine=='chrono-fsi'else'chrono_dem_smoke');total_steps=1000 if a.engine=='chrono-fsi' else 250;cmd=[str(binary),str(total_steps)];timed_steps=total_steps-10
 env['LD_LIBRARY_PATH']=os.environ['ROCM_PATH']+'/lib:'+os.environ['ROCM_PATH']+'/lib/llvm/lib:'+str(S/'build/chrono-hip-devel/lib')
times=[];payloads=[]
for rep in range(6):
 c=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=300);(dest/f'run-{rep}.log').write_text(c.stdout+c.stderr)
 if c.returncode:print(c.stdout+c.stderr,flush=True);raise SystemExit(c.returncode)
 x=json.loads(next(line.split('SMOKE_RESULT_JSON:',1)[1]for line in c.stdout.splitlines()if'SMOKE_RESULT_JSON:'in line));assert x['physics_valid']
 if rep:times.append(x['step_wall_s']);payloads.append(x)
median=statistics.median(times)
print('BENCHMARK_RESULT_JSON:'+json.dumps(dict(engine='chrono',case=a.engine,backend_observed='hip',physics_valid=True,steps=timed_steps,repeats=5,warmup='10 native steps per repetition for Chrono; one complete discarded process for all',synchronized_rollout_s=times,median_s=median,step_per_s=timed_steps/median,dt=payloads[-1]['dt'],validation_readback_in_timing=a.engine.startswith('chrono'),scope='small instrumented 27-particle reference, not large-particle production throughput',last_physics=payloads[-1])))
