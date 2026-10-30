"""Extract official AMD Taichi Python payload from its documented container, no daemon."""
from workspace import expand_runtime, run_root, runtime_path
import hashlib,json,pathlib,tarfile,urllib.parse,urllib.request
R=run_root();D=R/'storage/official-taichi';D.mkdir(exist_ok=True)
repo='rocm/taichi';tag='taichi-1.8.0b2_rocm7.0.0_ubuntu24.04_py3.12.3'
auth=json.load(urllib.request.urlopen('https://auth.docker.io/token?service=registry.docker.io&scope=repository:'+repo+':pull'))['token']
def request(path):return urllib.request.urlopen(urllib.request.Request('https://registry-1.docker.io/v2/'+repo+'/'+path,headers={'Authorization':'Bearer '+auth,'Accept':'application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.oci.image.index.v1+json'}),timeout=180)
manifest=json.load(request('manifests/'+tag))
if 'manifests'in manifest:
 target=next(x for x in manifest['manifests'] if x['platform']['architecture']=='amd64');manifest=json.load(request('manifests/'+target['digest']))
(D/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('TOTAL_COMPRESSED_GB',sum(x['size']for x in manifest['layers'])/1e9,flush=True)
found=[]
for i,layer in enumerate(manifest['layers']):
 digest=layer['digest'];f=D/('layer-'+str(i)+'.tar.gz')
 print('LAYER',i,layer['size'],flush=True)
 if not f.exists():
  h=hashlib.sha256()
  with request('blobs/'+digest) as src,f.open('wb') as dst:
   while block:=src.read(8*1024*1024):dst.write(block);h.update(block)
  assert h.hexdigest()==digest.split(':')[1]
 with tarfile.open(f) as t:
  members=t.getmembers()
  for m in members:
   # Preserve just Python package, shared linker, and optional source dist/wheel.
   wanted=(('/site-packages/taichi/' in m.name or '/dist-packages/taichi/'in m.name or '/site-packages/taichi-'in m.name or '/dist-packages/taichi-'in m.name or 'amd_taichi-'in m.name or '/bin/ld.lld'in m.name) and m.isfile())
   if wanted:
    dest=D/'root'/m.name
    if not dest.resolve().is_relative_to((D/'root').resolve()):continue
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(t.extractfile(m).read());dest.chmod(m.mode);found.append(m.name)
 print('MATCHES',len(found),flush=True)
 # Keep compressed layer evidence until all extraction is reviewed; no broad cleanup.
(D/'extracted.json').write_text(json.dumps(found,indent=2))
print('EXTRACTED',len(found),flush=True)
