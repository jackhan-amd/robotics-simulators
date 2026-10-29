import os,hashlib,importlib.util,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE/'tools'));import assets

class AssetsTests(unittest.TestCase):
 @unittest.skipIf(os.name=='nt','Requires POSIX symlink semantics; exercised in Linux CI')
 def test_traversal_and_symlink_escape(self):
  with tempfile.TemporaryDirectory()as d,tempfile.TemporaryDirectory()as outside:
   root=Path(d);(root/'link').symlink_to(outside,target_is_directory=True)
   for name in ['../outside','/absolute','link/file']:
    with self.assertRaises(ValueError):assets.asset_path(root,name)
 def test_checksum_and_no_overwrite(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);p=root/'data';p.write_bytes(b'old');spec={'sha256':hashlib.sha256(b'new').hexdigest()}
   with self.assertRaises(ValueError):assets.download('https://example.org/data',p,spec,10**20)
   self.assertEqual(p.read_bytes(),b'old')
 def test_file_fetch_and_reuse(self):
  data=b'verified fixture';spec={'id':'fixture','kind':'file','destination':'assets/data','license_status':'verified','license':'MIT','url':'https://example.org/data','sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
  with tempfile.TemporaryDirectory()as d:
   with patch.object(assets,'urlopen',return_value=io.BytesIO(data)),patch.object(assets.shutil,'disk_usage',return_value=type('Disk',(),{'free':10**12})()):assets.fetch(spec,Path(d),budget=30)
   self.assertEqual(assets.status(spec,Path(d)),'VERIFIED')
   with patch.object(assets,'urlopen',side_effect=AssertionError('Unexpected network')):assets.fetch(spec,Path(d),budget=30)
 def test_unresolved_license_cannot_be_accepted(self):
  spec={'id':'unknown','license_status':'requires_review'}
  with self.assertRaisesRegex(ValueError,'LICENSE_REVIEW_REQUIRED'):assets.fetch(spec,Path('/unused'),accept=True)
 def test_git_blob_hash(self):
  data=b'hello\n';expected=hashlib.sha1(b'blob 6\0'+data).hexdigest()
  with tempfile.TemporaryDirectory()as d:
   f=Path(d)/'text';f.write_bytes(data);self.assertTrue(assets.verify_file(f,{'git_blob_sha1':expected,'bytes':6}))
 def test_manifest_rejects_mutable_revision_and_duplicate_ids(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'manifest.json';x={'id':'source','kind':'git','destination':'upstream/source','url':'https://example.org/source','revision':'main'};p.write_text(json.dumps({'assets':[x]}))
   with self.assertRaises(ValueError):assets.read_manifest(p)
   x['revision']='a'*40;p.write_text(json.dumps({'assets':[x,x]}))
   with self.assertRaises(ValueError):assets.read_manifest(p)

if __name__=='__main__':unittest.main()
