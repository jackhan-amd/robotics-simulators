"""Publication filters must keep final GPU evidence separate from diagnostics."""
import json,os,pathlib,sys,tempfile,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'study'))
import publication
import workspace

class StudyPublicationTests(unittest.TestCase):
 def test_source_references_and_private_paths(self):
  with patch.object(publication,'profile',return_value={'LAB_ROOT':'/external/work','STUDY_SSH_TARGET':'user@private-host'}):
   value=publication.sanitize_text('/external/work/storage/upstream/genesis-world/examples/coupling/sph_rigid.py /external/work/capture_provided_genesis.py user@private-host')
   self.assertEqual(value,'genesis-world/examples/coupling/sph_rigid.py study/capture_provided_genesis.py ${STUDY_SSH_TARGET}')
 def test_aggregates_drop_individual_history(self):
  data=publication.aggregate({'run_id':'private','command':['private command'],'measurement':{'envs':4096,'synchronized_rollout_s':[1,2,3,4,5]},'smoke_run_id':'private'})
  self.assertEqual(data,{'measurement':{'envs':4096,'synchronized_rollout_s':[1,2,3,4,5]}})
 def test_packaged_example_uses_logical_source_reference(self):
  source='${STUDY_STORAGE_ROOT}/official-taichi/root/usr/local/lib/python3.12/site-packages/taichi/examples/simulation/mpm88.py'
  self.assertEqual(publication.repository_reference(source),'AMD Taichi provided example: simulation/mpm88.py (adapter: study/provided_replicas.py)')
  self.assertNotIn('official-taichi/root',publication.sanitize_text(source))
 def test_only_final_successful_gpu_runs_selected(self):
  campaign={'campaigns':[{'smoke_status':'PASS','smoke_run_id':'smoke-final','points':[{'status':'PASS','run_id':'accepted'},{'status':'FAIL','run_id':'rejected'},{'status':'REMEASUREMENT_PENDING','run_id':'superseded'}]}]}
  self.assertEqual(publication.final_run_ids(campaign),{'smoke-final','accepted'})
 def test_environment_overrides_private_profile(self):
  with patch.object(workspace,'profile',return_value={'STUDY_SSH_TARGET':'profile-alias'}),patch.dict(os.environ,{'STUDY_SSH_TARGET':'environment-alias'}):
   self.assertEqual(workspace.ssh_target(),'environment-alias')
 def test_windows_client_preserves_remote_posix_paths(self):
  with patch.object(workspace.os,'name','nt'):
   self.assertEqual(str(workspace.configured_path('/external/work')/'storage'),'/external/work/storage')
 def test_unconfigured_paths_fail_before_execution(self):
  with patch.object(workspace,'profile',return_value={}),patch.dict(os.environ,{},clear=True):
   with self.assertRaises(RuntimeError):workspace.run_root()
   with self.assertRaises(RuntimeError):workspace.ssh_target()
 def test_taichi_image_path_does_not_follow_active_venv(self):
  with patch.object(workspace,'profile',return_value={}),patch.dict(os.environ,{},clear=True):
   self.assertEqual(workspace.expand_runtime('${PYTHON_SITE_PACKAGES}'),'/usr/local/lib/python3.12/dist-packages')
 def test_json_escaped_windows_workspace_is_redacted(self):
  fake=pathlib.PureWindowsPath('C:/private/review')
  with patch.object(publication,'REPO_ROOT',fake),patch.object(publication,'profile',return_value={}):
   cleaned=publication.sanitize_text(json.dumps({'path':str(fake/'document.md')}))
   self.assertEqual(json.loads(cleaned)['path'],'${REPO_ROOT}\\document.md')
 def test_final_projection_archives_superseded_profile_logs(self):
  with tempfile.TemporaryDirectory()as directory:
   root=pathlib.Path(directory);raw=root/'evidence/results';raw.mkdir(parents=True);out=root/'evidence/final';out.mkdir()
   (out/'old-profile.json').write_text('{}',encoding='utf-8');(out/'old-profile.log').write_text('superseded',encoding='utf-8')
   receipt=dict(engine='mujoco',case='accepted-case',status='PASS',gpu_requested=True,rc=0,log='accepted.log',results=[])
   (raw/'accepted.json').write_text(json.dumps(receipt),encoding='utf-8');(raw/'accepted.log').write_text('successful final execution',encoding='utf-8')
   campaign={'campaigns':[{'smoke_status':'PENDING','points':[{'status':'PASS','run_id':'accepted'}]}]}
   publication.final_evidence(root,out,campaign)
   self.assertEqual({p.name for p in out.iterdir()},{'mujoco-accepted-case.json','mujoco-accepted-case.log'})
   self.assertEqual(len(list((root/'evidence/private-final-history').iterdir())),2)

if __name__=='__main__':unittest.main()
