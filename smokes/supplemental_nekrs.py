"""Small upstream Ethier scene, isolated Docker C++ runtime; no renderer/performance claim."""
import argparse,ctypes,json,os,re,shutil,subprocess,time,uuid
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--backend',choices=('cpu','hip'),required=True);p.add_argument('--steps',type=int,default=10);p.add_argument('--profile',action='store_true');p.add_argument('--budget',type=int,default=280);p.add_argument('--reuse',type=str);a=p.parse_args();assert a.steps==10
s=Path(os.environ['STUDY_STORAGE_ROOT']);private=Path(os.environ['STUDY_PRIVATE_ROOT'])
assert 1<=a.budget<=880
root=private/'artifacts'/(a.reuse if a.reuse else 'nekrs_'+uuid.uuid4().hex);assert root.resolve().is_relative_to((private/'artifacts').resolve())
if not a.reuse:shutil.copytree(s/'upstream/nekrs/examples/ethier',root)
par=root/'ethier.par';text=par.read_text().replace('polynomialOrder = 9','polynomialOrder = 5').replace('numSteps = 100','numSteps = 10').replace('checkpointInterval = 10','checkpointInterval = 1000');par.write_text(text)
name='CPU'
if a.backend=='hip':
 lib=ctypes.CDLL('libamdhip64.so');count=ctypes.c_int();buf=ctypes.create_string_buffer(256)
 assert lib.hipGetDeviceCount(ctypes.byref(count))==0 and count.value==1
 assert lib.hipDeviceGetName(buf,256,0)==0;name=buf.value.decode();assert os.environ['STUDY_AMD_NAME'] in name
container='robotics-nekrs-'+uuid.uuid4().hex[:10]
cmd=['docker','run','--name',container,'--rm','--pull=never','--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--user',str(os.getuid())+':'+str(os.getgid()),'--pids-limit=256','--cpus=2','--memory=8g','--tmpfs=/tmp:rw,size=1g','-v',str(s/'install/nekrs-docker')+':/install:ro','-v',str(root)+':/work:rw','-w','/work','-e','NEKRS_HOME=/install','-e','NEKRS_CACHE_DIR=/work/.cache','-e','OMP_NUM_THREADS=1','-e','OMPI_MCA_osc=pt2pt']
if a.backend=='hip':
 render=Path(os.environ['CHECKED_RENDER_NODE'])
 assert render.parent==Path('/dev/dri') and re.fullmatch(r'renderD[0-9]+',render.name) and render.is_char_device()
 assert os.environ['STUDY_AMD_ARCH']=='gfx1151'
 cmd+=['--device=/dev/kfd','--device='+str(render),'--group-add',str(render.stat().st_gid),'--env','ROCR_VISIBLE_DEVICES']
run='/install/bin/nekrs --setup ethier.par --backend '+('HIP' if a.backend=='hip' else 'CPU')+' --device-id 0'
if a.profile:
 assert a.backend=='hip';run='rocprofv3 --log-level error --kernel-trace --output-format csv --output-directory /work/profile -- '+run
cmd+=['--entrypoint=/bin/bash','sha256:4fa5bc9c24d25ef7e0fe38b23fc5f2b27fc986177bd2f9e496997bcf5af03871','-c',run]
(root/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
try:
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=a.budget)
except subprocess.TimeoutExpired as ex:
 for key in ('stdout','stderr'):
  value=getattr(ex,key) or '';value=value.decode(errors='replace') if isinstance(value,bytes) else value;(root/(key+'.txt')).write_text(value);print(value,flush=True)
 raise
finally:
 alive=subprocess.run(['docker','inspect','--format','{{.State.Running}}',container],capture_output=True,text=True)
 if alive.returncode==0 and alive.stdout.strip()=='true':subprocess.run(['docker','stop','--time','1',container],capture_output=True,text=True,timeout=15)
(root/'stdout.txt').write_text(r.stdout);(root/'stderr.txt').write_text(r.stderr);print(r.stdout,flush=True);print(r.stderr,flush=True)
if r.returncode:raise SystemExit(r.returncode)
rows=[]
for line in r.stdout.splitlines():
 if 'L2 err' in line:
  values=re.findall(r'[-+]?\d+(?:\.\d*)?(?:[EeDd][-+]?\d+)?',line.split('L2 err')[0]);rows.append([float(v.replace('D','E').replace('d','e')) for v in values])
last=rows[-1] if rows else [];finite=all(abs(x)<float('inf') for row in rows for x in row)
# Upstream UDF resets analytic fields for steps1..5; steps6..10 genuinely advance.
gates=dict(ten_steps=bool(last) and int(last[0])==10,time=bool(last) and abs(last[1]-.02)<1e-9,finite=finite and bool(rows),velocity_l2=bool(last) and abs(last[2])<=1e-3,pressure_l2=bool(last) and abs(last[3])<=.1,scalar_l2=bool(last) and max(abs(x) for x in last[4:6])<=1e-3)
print('SMOKE_RESULT_JSON:'+json.dumps(dict(implementation='nekRS Ethier',backend_observed=a.backend,physics_valid=all(gates.values()),gates=gates,metrics=dict(last_l2_row=last,rows=len(rows)),steps=10,dt=.002,polynomial_order=5,elements=32,device_name=name,private_artifact_ref='artifacts/'+root.name,profile_requested=a.profile,g2_qualified=False)),flush=True)
raise SystemExit(0 if all(gates.values()) else 3)
