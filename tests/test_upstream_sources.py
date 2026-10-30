"""Exercise dependency pinning without network, GPU or upstream payloads."""
import importlib.util,json,pathlib,subprocess,tempfile,unittest
R=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fetch_sources',R/'tools/fetch_sources.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class UpstreamSourcesTests(unittest.TestCase):
    def test_all_catalog_engines_have_pinned_dependencies(self):
        data=module.catalog()
        engines=json.loads((R/'recipes/engines.json').read_text(encoding='utf-8'))['engines']
        self.assertEqual(set(data['engines']),{e['id']for e in engines})
        self.assertTrue(all(data['engines'].values()))
        notices=json.loads((R/'configs/third-party-licenses.json').read_text(encoding='utf-8'))['components']
        by_project={n['project']:n for n in notices}
        for source in data['sources']:
            self.assertEqual(source['revision'],by_project[source['project']]['revision'])
            self.assertEqual(source['url'],by_project[source['project']]['source_url'])

    def test_checkout_pin_and_preserve_existing_changes(self):
        with tempfile.TemporaryDirectory()as directory:
            root=pathlib.Path(directory);origin=root/'origin';origin.mkdir()
            def git(*args):
                return subprocess.check_output(['git',*map(str,args)],cwd=origin,text=True,stderr=subprocess.DEVNULL).strip()
            git('init');(origin/'value').write_text('first');git('add','value')
            git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','first')
            first=git('rev-parse','HEAD');(origin/'value').write_text('second');git('add','value')
            git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','second')
            source=dict(id='fixture',url=origin.as_uri(),revision=first)
            checkout=module.fetch(source,root/'runtime')
            self.assertEqual((checkout/'value').read_text(),'first')
            self.assertEqual(module.fetch(source,root/'runtime'),checkout)
            with self.assertRaisesRegex(ValueError,'another revision'):
                module.fetch(dict(source,revision=git('rev-parse','HEAD')),root/'runtime')
            (checkout/'value').write_text('local edit')
            with self.assertRaisesRegex(ValueError,'local changes'):module.fetch(source,root/'runtime')
            self.assertEqual((checkout/'value').read_text(),'local edit')

if __name__=='__main__':unittest.main()
