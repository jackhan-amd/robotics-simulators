"""Repeated native nekRS steady-state solve times after ten warm-up steps."""
from workspace import expand_runtime, run_root, runtime_path
import json,pathlib,statistics,subprocess
R=run_root();times=[];samples=[];last=None
for rep in range(6):
 c=subprocess.run(['python3',str(R/'nekrs_case.py'),'--steps','110','--order','5'],capture_output=True,text=True,timeout=1000)
 (R/'evidence'/f'nekrs-bench-rep-{rep}.log').write_text(c.stdout+c.stderr)
 if c.returncode:print(c.stdout+c.stderr);raise SystemExit(c.returncode)
 last=json.loads(next(line.split('SMOKE_RESULT_JSON:',1)[1]for line in c.stdout.splitlines()if'SMOKE_RESULT_JSON:'in line));assert last['physics_valid']
 if rep:
  assert len(last['steady_step_s'])==100;times.append(sum(last['steady_step_s']));samples.append(last['steady_step_s'])
median=statistics.median(times)
print('BENCHMARK_RESULT_JSON:'+json.dumps(dict(engine='nekrs',case='Ethier_p5',implementation='nekRS native Ethier',backend_observed='hip',physics_valid=True,steps=100,repeats=5,warmup_steps=10,dt=.002,polynomial_order=5,elements=32,local_grid_points=32*6**3,synchronized_rollout_s=times,median_s=median,step_per_s=100/median,grid_point_updates_per_s=100*32*6**3/median,native_solver_timer=True,initialization_in_timing=False,last_l2_row=last['last_l2_row'])))
