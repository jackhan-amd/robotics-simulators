"""Export non-private settings from accepted GPU measurements, without raw history."""
from workspace import script_path, source_reference
import argparse,collections,hashlib,json,pathlib,re
from publication import repository_reference,sanitize_text

FIELDS=set('engine implementation backend_observed device scene model precision envs workers steps requested_steps frames frames_per_env dt physics_dt substeps particles particles_per_env grid cells_per_env gaussians width height camera repeats warmup warmup_steps warmup_frames repeat_mode scaling_mode source source_commit source_sha256 model_source model_sha256 mesh_sha256 asset_sha256 bddl_file bddl_sha256 libero_commit backend_commit nv nu nbody ngeom dofs qpos_width solver_iterations line_search_iterations solver_tolerance nconmax_per_world njmax_per_world controls graph_mode readback_in_timing compiler_profile xla_flags jax mujoco warp genesis_version version torch torch_hip validation_barrier arena_init_bytes native_fixed_dt nominal_native_substeps_per_advance derived_metric_note control_frequency_hz physics_substeps_per_control_step simulation_time_per_rollout scope validation_scope changes timing_scope'.split())
ADAPTERS={
 'chrono-dem':'provided_chrono_replicas.py','chrono-fsi':'provided_chrono_replicas.py',
 'fluidlab':'provided_replicas.py','genesis-sph':'provided_replicas.py',
 'genesis-franka':'provided_genesis_franka.py','gsplat':'provided_gsplat_garden.py',
 'incflo':'provided_incflo.py','instinct':'provided_instinct_libero.py',
 'mujoco-mjx':'provided_mjx_humanoid.py','mujoco-mjwarp':'representative_mujoco.py',
 'nekrs':'provided_nekrs_windows.py','taichi':'provided_replicas.py',
}
WARMUPS={'chrono-dem':{'discarded_full_trials':1},'chrono-fsi':{'discarded_full_trials':1},'incflo':{'discarded_full_trials':1},'fluidlab':{'steps':50,'seed':0},'genesis-sph':{'steps':50,'seed':'inherited from pinned upstream initialization; no explicit adapter override'},'genesis-franka':{'steps':100,'seed':'inherited from pinned upstream initialization; no explicit adapter override'},'gsplat':{'frames':10,'torch_seed':0,'packed':False},'instinct':{'control_steps':10,'seed':0,'init_state':'first supplied task init state replicated across environments'},'mujoco-mjx':{'full_compiled_rollouts':1,'rollout_steps':1000,'jax_enable_x64':False,'cpu_sanity_steps':20},'mujoco-mjwarp':{'steps':100,'cpu_sanity_steps':20},'nekrs':{'steps':100},'taichi':{'steps':50,'random_seed':0,'offline_cache':False,'cpu_max_num_threads':1}}

def key(engine,model):
 if engine=='chrono':return 'chrono-dem'if 'DEM'in model else'chrono-fsi'
 if engine=='genesis':return 'genesis-sph'if 'SPH'in model else'genesis-franka'
 if engine=='mujoco':return 'mujoco-mjx'if 'MJX-JAX'in model else'mujoco-mjwarp'
 return engine

def settings(x):
 result={k:v for k,v in x.items()if k in FIELDS}
 if 'scene_metadata'in x:result['scene_metadata']=settings(x['scene_metadata'])
 for k in ('source','model_source','bddl_file'):
  if k in result:result[k]=repository_reference(result[k])
 return json.loads(sanitize_text(json.dumps(result,ensure_ascii=False)))

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-dir',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
 source=json.loads((a.data_dir/'env-scaling-data.json').read_text(encoding='utf-8'))
 groups=collections.defaultdict(list)
 for row in source['measurements']:
  assert row['status']=='PASS'and row['measurement']['backend_observed']not in('cpu','CPU')
  groups[(row['engine'],row['model'])].append(row)
 primary=[];root=pathlib.Path(__file__).resolve().parent
 for(engine,model),rows in groups.items():
  case=key(engine,model);adapter=ADAPTERS[case];path=script_path(adapter)
  primary.append(dict(id=case,engine=engine,model=model,adapter=source_reference(adapter),portable_adapter_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),envs=sorted(r['envs']for r in rows),warmup_and_explicit_runtime_options=WARMUPS[case],settings_by_env=[settings(r['measurement'])for r in sorted(rows,key=lambda r:r['envs'])]))
 for group in primary:
  if group['engine']=='fluidlab':group['execution_path_coverage']={'measured_paths': ['forward simulation'], 'untested_paths': ['gradient/backward computation', 'learning', 'control/trajectory optimization', 'optimizer iterations'], 'computation_location': 'Same MI355X GPU server as the benchmark; no remote compute service', 'git_tracked': 'Harness, measurement adapters, preparation/compatibility tools and configuration', 'not_vendored': 'Complete upstream FluidLab engine source', 'file_layout': 'Separate local upstream checkout and runtime directories within the benchmark deployment; connected through the common source manifest'}
 baseline=json.loads((a.data_dir/'benchmark-data.json').read_text(encoding='utf-8'))
 assert len(source['measurements'])==64 and len(primary)==12 and len(baseline)==50
 result=dict(schema_version=1,scope='Parameters of the completed MI355X GPU campaign. No training, policy optimization or new GSplat/WAM blog reproduction is claimed.',target=dict(gpu='AMD Instinct MI355X',gpus_used=1,architecture='gfx950',python='3.12.3'),coverage=dict(primary_models=12,primary_configurations=64,reference_baseline_records=50,overlap_note='Six MJWarp Humanoid configurations appear in both cohorts; counts must not be added.',parameter_provenance='Recorded settings and explicit adapter overrides describe the measured paths. Unchanged parameters are identified by pinned upstream example/model files and hashes. This does not establish coverage of other execution paths.',licensing='Upstream engine/model sources remain separate dependencies and are not vendored. Their original terms apply; FluidLab source-license status is recorded in configs/upstream-sources.json.'),source_and_build_versions='report/evidence/software-observations.json',primary=primary,reference_baseline_settings=[settings(x)for x in baseline])
 output=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
 assert not re.search(r'"(?:run_id|raw_artifact|command|log|utc)"',output)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(output,encoding='utf-8');print('Exported settings: 12 primary models, 64 configurations and 50 baseline records')
if __name__=='__main__':main()
