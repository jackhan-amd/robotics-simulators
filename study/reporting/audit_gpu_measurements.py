"""Independent arithmetic and provenance checks for published GPU measurements."""
from workspace import REPO_ROOT
import argparse,csv,datetime,json,math,pathlib,statistics
B=REPO_ROOT
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--data-dir',type=pathlib.Path,default=B/'report');parser.add_argument('--accepted-evidence',action='store_true');args=parser.parse_args();O=args.data_dir;d=json.loads((O/'env-scaling-data.json').read_text(encoding='utf-8'))
csvrows=list(csv.DictReader((O/'env-scaling-data.csv').open(encoding='utf-8-sig')));assert len(csvrows)==len(d['measurements'])
for row,csvrow in zip(d['measurements'],csvrows):
 x=row['measurement'];times=x['synchronized_rollout_s'];assert len(times)==5 and all(math.isfinite(t)and t>0 for t in times)
 median=statistics.median(times);assert math.isclose(row['median_s'],median,rel_tol=1e-12)
 steps=x.get('steps',x.get('frames_per_env'));assert steps and steps>0
 if row['metric']=='frames_per_s':assert x['frames']==x['envs']*steps
 throughput=x['envs']*steps/median;assert math.isclose(row['throughput'],throughput,rel_tol=1e-9),(row['case'],throughput,row['throughput'])
 assert float(csvrow['throughput'])==row['throughput']
 if not args.accepted_evidence:assert csvrow['run_id']==row['run_id']
 assert x['physics_valid']and x['backend_observed']in('hip','rocm','amdgpu')and row['status']=='PASS'
 path=O/'evidence/final'/(row['engine']+'-'+row['case']+'.json')if args.accepted_evidence else O/'evidence/results'/(row['run_id']+'.json')
 receipt=json.loads(path.read_text(encoding='utf-8'));assert receipt['gpu_requested']and receipt['status']=='PASS'and receipt['rc']==0 and receipt['case']==row['case']
 if row['engine']in('chrono','incflo'):assert x['validation_barrier']
 if row['metric']=='env_advance_calls_per_s':assert row['engine']=='chrono'and x['native_fixed_dt']==2.5e-6 and x['nominal_native_substeps_per_advance']==400
 if row['rtf_per_env']is not None:
  simtime=x['steps']/x['control_frequency_hz']if row['engine']=='instinct'else(x['simulation_time_per_rollout']if row['engine']=='incflo'else x['steps']*x['dt'])
  assert math.isclose(row['rtf_per_env'],simtime/median,rel_tol=1e-9),row['case']
result=dict(status='PASS',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),published_gpu_configurations=len(d['measurements']),samples_each=5,checks=['GPU-qualified zero-exit receipt','finite positive synchronized samples','median and throughput formula','JSON/CSV equality','per-env RTF with control/adaptive-step semantics','Chrono/incflo validation barrier','DEM outer advance call distinguished from native fixed substep'])
(O/'evidence/throughput-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
