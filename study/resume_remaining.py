"""Bounded remaining GPU campaign, persistent across a local SSH interruption."""
from workspace import expand_runtime, run_root, runtime_path
import datetime,json,os,pathlib,subprocess
R=run_root()
stages=[
 ('MJX remaining requested sizes','provided_mjx_suite.py',dict(PROVIDED_MJX_ALIGNED='1',PROVIDED_MJX_ENVS='16384,32768,65536')),
 ('Chrono FSI gated remaining sizes','provided_chrono_suite.py',dict(PROVIDED_CHRONO_KIND='fsi',PROVIDED_CHRONO_ENVS='4,8',PROVIDED_CHRONO_SMOKE_ALREADY_QUALIFIED='1')),
 ('Chrono DEM gated sweep','provided_chrono_suite.py',dict(PROVIDED_CHRONO_KIND='dem',PROVIDED_CHRONO_ENVS='1,2,4,8')),
 ('incflo gated remaining sizes','provided_cfd_suite.py',dict(PROVIDED_CFD_ENGINE='incflo',PROVIDED_CFD_ENVS='4,8',PROVIDED_CFD_SMOKE_ALREADY_QUALIFIED='1'))]
results=[]
for title,script,settings in stages:
 print('RESUME_STAGE',datetime.datetime.now(datetime.timezone.utc).isoformat(),title,flush=True)
 env=os.environ.copy();env.update(settings,PYTHONUNBUFFERED='1')
 try:rc=subprocess.run(['python3',str(R/script)],env=env,timeout=12000).returncode
 except subprocess.TimeoutExpired:rc=124
 results.append(dict(stage=title,rc=rc));print('RESUME_STAGE_DONE',json.dumps(results[-1]),flush=True)
(R/'evidence/resume-remaining-completion.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stages=results),indent=2))
print('RESUME_ALL_STAGES_FINISHED',flush=True)
