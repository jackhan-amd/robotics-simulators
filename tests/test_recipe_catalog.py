"""Recipes must work without any archived study run or generated HTML."""
import ast,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from simulators.catalog import check,resolve,BASE
class RecipeCatalogTests(unittest.TestCase):
 def copy_source(self,dest):
  for name in ['simulators','recipes','configs','tools']:
   shutil.copytree(BASE/name,dest/name,ignore=shutil.ignore_patterns('__pycache__'))
 def test_registry_and_legacy_aliases(self):
  data=check();self.assertEqual(data['engines'],9);self.assertEqual(data['recipes'],16);self.assertFalse(data['local_run_history_required']);self.assertEqual(data['reviewed_configurations'],13);self.assertEqual(data['unreviewed_configurations'],3)
  self.assertEqual(resolve('freefall')['id'],'genesis-freefall');self.assertTrue(all(r['backend']!='cpu' for r in __import__('simulators.catalog',fromlist=['recipes']).recipes()))
 def test_missing_history_and_html_are_supported(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);self.copy_source(root)
   self.assertFalse((root/'results').exists())
   for action in ['check','build']:
    r=subprocess.run([sys.executable,'-m','simulators',action],cwd=root,capture_output=True,text=True,timeout=30)
    self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertTrue((root/'report/report.html').is_file());self.assertFalse((root/'results').exists())
 def test_cpu_fallback_cannot_become_reviewed_gpu(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);self.copy_source(root);path=root/'configs/verification-summary.json';data=json.loads(path.read_text());gpu=next(x for x in data['configurations']if x['backend']!='cpu');gpu['backend']='cpu';path.write_text(json.dumps(data))
   with self.assertRaises(ValueError):check(root)
 def test_no_run_id_or_throughput_in_published_recipe_data(self):
  for name in ['recipes/manifest.json','configs/verification-summary.json']:
   text=(BASE/name).read_text();self.assertNotIn('"run_id"',text);self.assertNotIn('"elapsed_wall_s"',text);self.assertNotIn('"throughput"',text)
 def test_install_scripts_parse_without_execution(self):
  for path in (BASE/'recipes').rglob('*.sh'):
   r=subprocess.run(['bash','-n',str(path)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,str(path)+r.stderr)
 def test_python_sources_parse(self):
  for area in ['tools','recipes','simulators']:
   for path in(BASE/area).rglob('*.py'):ast.parse(path.read_text())
 def test_unknown_recipe_is_rejected(self):
  with self.assertRaises(ValueError):resolve('does-not-exist')
 def test_all_shell_entrypoints_are_linked(self):
  for path in (BASE/'recipes').rglob('*.sh'):
   if path.name=='common.sh':continue
   self.assertIn(path.name,(path.parent/'README.md').read_text(),str(path))
if __name__=='__main__':unittest.main()
