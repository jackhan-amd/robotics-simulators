"""Preserve pinned upstream license notices for the study's extra dependencies."""
from workspace import REPO_ROOT
import hashlib,json,pathlib,urllib.error,urllib.request
B=REPO_ROOT
projects=[('GSplat AMD distribution','gsplat-study','AMD-Ecosystem/gsplat','ff8bc5489545bcc1b5a2b997d975834429a0d7af',()),('Instinct Sim / Faster Action Models','instinct-sim-study','AMD-AGI/faster-action-models','a5fa73101988870e51f04fe1e7be5da56dda3841',('simulate/LICENSE','simulate/NOTICE','simulate/PROVENANCE.md')),('LIBERO study dependency','libero-study','Lifelong-Robot-Learning/LIBERO','8f1084e3132a39270c3a13ebe37270a43ece2a01',())]
manifest=B/'configs/third-party-licenses.json';data=json.loads(manifest.read_text(encoding='utf-8'));added=[]
for project,slug,repository,revision,extras in projects:
 notices=[];license_text=''
 for candidates in(('LICENSE','LICENSE.md','LICENSE.txt'),*((p,)for p in extras)):
  for relative in candidates:
   raw='https://raw.githubusercontent.com/'+repository+'/'+revision+'/'+relative
   try:
    with urllib.request.urlopen(raw,timeout=30)as response:payload=response.read()
   except urllib.error.HTTPError as error:
    if error.code==404:continue
    raise
   target=B/'third_party_notices'/slug/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(payload)
   notices.append(dict(file=target.relative_to(B).as_posix(),sha256=hashlib.sha256(payload).hexdigest(),upstream_path=relative,url='https://github.com/'+repository+'/blob/'+revision+'/'+relative))
   if not license_text:license_text=payload.decode('utf-8')
   break
  else:raise RuntimeError('Pinned notice missing: '+project+' / '+str(candidates))
 license_id='Apache-2.0'if'Apache License'in license_text and'Version 2.0'in license_text else('MIT'if'MIT License'in license_text else'See preserved upstream notice')
 entry=dict(project=project,source_url='https://github.com/'+repository,revision=revision,license=license_id,license_status='verified_source_text',notices=notices,upstream_payload_in_git=False,scope='External study dependency. Parent license does not replace bundled third-party, model, dataset or asset terms; see retained provenance. No runtime or asset payload is included.')
 data['components']=[x for x in data['components']if x['project']!=project]+[entry];added.append(dict(project=project,license=license_id,notices=len(notices)))
manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(added))
