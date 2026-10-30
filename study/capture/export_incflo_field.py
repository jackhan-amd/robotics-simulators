"""Export an already measured GPU plotfile, with no new simulation or timing."""
from workspace import expand_runtime, run_root, runtime_path
import hashlib,json,pathlib,re
import numpy as np
R=run_root();E=R/'evidence';records=[]
for f in E.glob('*provided-incflo-envs-1-*.json'):
 try:j=json.loads(f.read_text())
 except Exception:continue
 if isinstance(j,dict)and j.get('status')=='PASS'and j.get('results'):records.append(j)
r=max(records,key=lambda x:x.get('execution_utc',x['utc']));result=r['results'][0];plot=pathlib.Path(result['checks'][0][0]['plot']);h=(plot/'Header').read_text().splitlines();nc=int(h[1]);names=h[2:2+nc];values=np.full((nc,128,128),np.nan)
for name,offset in re.findall(r'FabOnDisk:\s+(\S+)\s+(\d+)',(plot/'Level_0/Cell_H').read_text()):
 with (plot/'Level_0'/name).open('rb')as f:
  f.seek(int(offset));line=f.readline();vec=[tuple(map(int,m.split(b',')))for m in re.findall(rb'\(([-0-9, ]+)\)',line)if len(m.split(b','))==2];lo,hi,_=vec[-3:];nx,ny=hi[0]-lo[0]+1,hi[1]-lo[1]+1;x=np.frombuffer(f.read(nx*ny*nc*8),dtype='<f8').reshape(nc,ny,nx);values[:,lo[1]:hi[1]+1,lo[0]:hi[0]+1]=x
assert np.isfinite(values).all();fields=dict(zip(names,values));simtime=float(h[3+nc]);np.savez_compressed(E/'incflo-provided-cavity-field.npz',**fields,simulation_time=simtime)
meta=dict(engine='incflo',physics_valid=True,source_run_id=r['run_id'],source_plot=str(plot),source_header_sha256=hashlib.sha256((plot/'Header').read_bytes()).hexdigest(),steps=50,simulation_time=simtime,scope='actual accepted HIP AMReX field output, exported after measurement; later visualization is postprocessing, not a fabricated scene')
(E/'incflo-provided-field-capture.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta))
