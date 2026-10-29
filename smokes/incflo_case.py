#!/usr/bin/env python3
"""Run the one-box cavity probe and read its small native AMReX FAB output."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,required=True);p.add_argument('--backend',choices=('cpu','hip','cuda'),required=True);p.add_argument('--steps',type=int,choices=(10,50),default=10)
a=p.parse_args();base=Path(__file__).resolve().parents[1]
root=Path(os.environ['STUDY_PRIVATE_ROOT'])/'artifacts'/('incflo_'+uuid.uuid4().hex);root.mkdir(parents=True)
name=ctypes.create_string_buffer(256);count=ctypes.c_int()
if a.backend=='hip':
    lib=ctypes.CDLL('libamdhip64.so');assert lib.hipGetDeviceCount(ctypes.byref(count))==0 and count.value==1
    assert lib.hipDeviceGetName(name,256,0)==0
    assert '8060S' in name.value.decode()
elif a.backend=='cuda':
    lib=ctypes.CDLL('libcuda.so.1');assert lib.cuInit(0)==0
    assert lib.cuDeviceGetCount(ctypes.byref(count))==0 and count.value==1
    assert lib.cuDeviceGetName(name,256,0)==0
    assert '3090' in name.value.decode()
if a.backend=='cpu':name.value=b'CPU'
cmd=[str(a.binary.resolve()),str(base/'configs/incflo/cavity16.in'),f'max_step={a.steps}',f'amr.plot_int={a.steps}']
start=time.perf_counter();run=subprocess.run(cmd,cwd=root,capture_output=True,text=True,timeout=280);wall_s=time.perf_counter()-start
(root/'stdout.txt').write_text(run.stdout);(root/'stderr.txt').write_text(run.stderr)
print(run.stdout,flush=True);print(run.stderr,flush=True)
if run.returncode:raise SystemExit(run.returncode)
plots=sorted(root.glob('plt[0-9]*'));plot=plots[-1]
header=(plot/'Header').read_text().splitlines();ncomp=int(header[1]);names=header[2:2+ncomp];assert int(header[2+ncomp])==2
simtime=float(header[3+ncomp]);fab_header=(plot/'Level_0/Cell_H').read_text()
entries=re.findall(r'FabOnDisk:\s+(\S+)\s+(\d+)',fab_header);assert len(entries)==1,'Expected a single small FAB'
file,offset=entries[0]
with (plot/'Level_0'/file).open('rb') as f:
    f.seek(int(offset));line=f.readline();vectors=[]
    for match in re.findall(rb'\(([-0-9, ]+)\)',line):
        values=match.split(b',')
        if len(values)==2:vectors.append(tuple(map(int,values)))
    lo,hi,kind=vectors[-3:];nx,ny=hi[0]-lo[0]+1,hi[1]-lo[1]+1
    assert (nx,ny)==(16,16) and int(line.split()[-1])==ncomp
    assert re.search(rb'^FAB \(\(8',line),'Expected double precision FAB'
    values=np.frombuffer(f.read(),dtype='<f8',count=nx*ny*ncomp).reshape(ncomp,ny,nx)
fields=dict(zip(names,values));u,v,rho=fields['velx'],fields['vely'],fields['density']
ratios=[]
for line in run.stdout.splitlines():
    if 'Final' in line:
        m=re.search(r'resid,\s*resid/bnorm\s*=\s*([-+0-9.eE]+),\s*([-+0-9.eE]+)',line)
        if m:ratios.append(float(m.group(2)))
        else:
            m=re.search(r'resid/bnorm\s*=\s*([-+0-9.eE]+)',line)
            if m:ratios.append(float(m.group(1)))
metrics={'density_relative_error':float(abs(rho-1000).max()/1000),'max_velocity_component':float(max(abs(u).max(),abs(v).max())),
         'mean_kinetic_energy_j_m3':float((0.5*rho*(u*u+v*v)).mean()),'simulation_time_s':simtime,
         'max_final_projection_ratio':max(ratios) if ratios else None,'projection_solves_logged':len(ratios)}
observed='hip' if 'Initializing HIP...' in run.stdout else ('cuda' if 'Initializing CUDA...' in run.stdout else 'cpu')
gates={'backend':observed==a.backend,'finite_fields':bool(np.isfinite(values).all()),'density':metrics['density_relative_error']<=1e-10,
       'velocity':metrics['max_velocity_component']<=1.5,'lid_motion':metrics['mean_kinetic_energy_j_m3']>0,
       'time':abs(simtime-a.steps*0.0001)<=1e-10,'steps':plot.name.endswith(f'{a.steps:05d}'),
       'projection_residual':bool(ratios) and max(ratios)<=1e-6}
print('SMOKE_RESULT_JSON:'+json.dumps({'backend_observed':observed,'physics_valid':all(gates.values()),'gates':gates,
       'metrics':metrics,'steps':a.steps,'dt':0.0001,'cells':256,'shape':[16,16],'wall_s':wall_s,
       'numpy_version':np.__version__,'device_name':name.value.decode(),'g2_qualified':False,'private_artifact_ref':'artifacts/'+root.name},sort_keys=True),flush=True)
raise SystemExit(0 if all(gates.values()) else 3)
