"""Native Evolve timer sweep with numerical field checks and initialization excluded."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import argparse,json,pathlib,re,statistics,subprocess
p=argparse.ArgumentParser();p.add_argument('--cells',type=int,required=True);a=p.parse_args()
R=run_root();S=storage_root();times=[];end_to_end=[];last=None
for rep in range(6):
 cmd=[str(S/'venvs/incflo-tools/bin/python'),str(R/'incflo_mi355x.py'),'--binary',str(S/'build/incflo-hip-devel/incflo.ex'),'--backend','hip','--steps','100','--cells',str(a.cells)]
 c=subprocess.run(cmd,capture_output=True,text=True,timeout=600);(R/'evidence'/f'incflo-n{a.cells}-rep{rep}.log').write_text(c.stdout+c.stderr)
 if c.returncode:print(c.stdout+c.stderr);raise SystemExit(c.returncode)
 last=json.loads(next(l.split('SMOKE_RESULT_JSON:',1)[1]for l in c.stdout.splitlines()if'SMOKE_RESULT_JSON:'in l));assert last['physics_valid']
 values=re.findall(r'Time spent in Evolve\(\):\s*([-+0-9.eE]+)',c.stdout);assert values
 if rep:times.append(float(values[-1]));end_to_end.append(last['wall_s'])
median=statistics.median(times)
print('BENCHMARK_RESULT_JSON:'+json.dumps(dict(engine='incflo',case=f'cavity_{a.cells}x{a.cells}',backend_observed='hip',physics_valid=True,cells=a.cells**2,shape=[a.cells,a.cells],steps=100,repeats=5,dt=.0001,synchronized_rollout_s=times,median_s=median,step_per_s=100/median,cell_updates_per_s=100*a.cells**2/median,process_wall_s=end_to_end,scope='native Evolve() timer; InitData excluded; final plot I/O included; first full process discarded',last_physics=last)))
