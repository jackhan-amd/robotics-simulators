"""Check relocation wiring and fresh flat runtime deployment without a GPU."""
import json,os,pathlib,subprocess,sys,tempfile,unittest
R=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'study'))
from workspace import script_index,script_path

class SourceLayoutTests(unittest.TestCase):
    def test_registry_covers_every_managed_script(self):
        index=script_index()
        files=set()
        for folder in ['study/runtime','study/reporting','study/benchmarks','study/capture']:
            files.update(p.relative_to(R).as_posix()for p in(R/folder).glob('*.py'))
        files.update(p.relative_to(R).as_posix()for p in(R/'recipes').glob('*/benchmarks/*.py'))
        self.assertEqual(set(index.values()),files)
        self.assertEqual(len(index),len(set(index.values())))
        for name,path in index.items():
            self.assertTrue(script_path(name).is_file())
            self.assertEqual(pathlib.PurePosixPath(path).name,name)

    def test_recipe_commands_resolve_relocated_sources(self):
        data=json.loads((R/'recipes/manifest.json').read_text())
        for row in data['recipes']:
            for arg in row['command']:
                if arg.endswith('.py')and'/'in arg and(chr(36)+'{')not in arg:
                    self.assertTrue((R/arg).is_file(),arg)
        with self.assertRaises(ValueError):script_path('../unregistered.py')

    @unittest.skipIf(os.name=='nt','Flat runtime symlink deployment is Linux-only')
    def test_fresh_bootstrap_and_flat_imports(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=pathlib.Path(tmp);tools=root/'tools';tools.mkdir()
            uv=tools/'uv';uv.write_text('#!/bin/sh\nexit 0\n');uv.chmod(0o755)
            runtime=root/'runtime';env=dict(os.environ,LAB_ROOT=str(runtime),
                STUDY_STORAGE_ROOT=str(root/'storage'),STUDY_WORKTREE=str(R),
                ROCM_PATH=str(root/'sdk'),PATH=str(tools)+os.pathsep+os.environ['PATH'])
            run=subprocess.run([sys.executable,str(R/'study/run.py'),'bootstrap.py'],env=env,capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertEqual((runtime/'repo').resolve(),R)
            self.assertTrue((runtime/'provided_mjx_humanoid.py').is_file())
            self.assertEqual((runtime/'publication.py').read_bytes(),script_path('publication.py').read_bytes())
            check=subprocess.run([sys.executable,str(runtime/'export_benchmark_parameters.py'),'--help'],env=env,capture_output=True,text=True,timeout=30)
            self.assertEqual(check.returncode,0,check.stdout+check.stderr)

if __name__=='__main__':unittest.main()
