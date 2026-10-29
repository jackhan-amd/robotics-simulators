"""The public catalog and notices must match the GPU-only release scope."""
import hashlib,json,pathlib,unittest
R=pathlib.Path(__file__).resolve().parents[1]
class GPUScopeTests(unittest.TestCase):
 def test_only_gpu_catalog_entries(self):
  rows=json.loads((R/'recipes/manifest.json').read_text())['recipes']
  self.assertEqual({r['engine']for r in rows},{'mujoco','genesis','chrono','incflo','nekrs','fluidlab','instinct','taichi','gsplat'})
  self.assertTrue(all(r['backend']in('hip','amdgpu','cuda')for r in rows))
 def test_original_notice_bytes_and_adaptations(self):
  components=json.loads((R/'configs/third-party-licenses.json').read_text())['components']
  for c in components:
   self.assertFalse(any(x in c['project'].lower()for x in('pybullet','gazebo','drake','sofa','dart')))
   for n in c.get('notices',[]):self.assertEqual(hashlib.sha256((R/n['file']).read_bytes()).hexdigest(),n['sha256'])
  for item in json.loads((R/'configs/license-exceptions.json').read_text())['files']:self.assertTrue((R/item['file']).is_file())
