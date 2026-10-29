"""Plan and execute one bounded recorded workflow in external storage."""
import contextlib, json, os
from pathlib import Path
import re, subprocess, sys, uuid

BASE=Path(__file__).resolve().parents[1]


def expand(value,env):
    def replacement(m):
        if m.group(1) not in env:raise ValueError('Set required environment variable '+m.group(1))
        return env[m.group(1)]
    return re.sub(r'\$\{([A-Z][A-Z0-9_]*)\}',replacement,value)


def execute(recipe,run=False):
    if not run:
        print(json.dumps({'executes':False,'suite':recipe['suite'],'case':recipe.get('case',recipe.get('case_id')),'command':recipe['command'],'environment':recipe.get('environment',{}),'timeout_s':recipe.get('timeout_s',300)},indent=2));return 0
    if os.name!='posix':raise ValueError('Actual GPU execution requires Linux; command previews work on any platform')
    import fcntl
    env=os.environ.copy();root=Path(env['STUDY_STORAGE_ROOT']).resolve();private=Path(env.get('STUDY_PRIVATE_ROOT',str(root/'private')));private.mkdir(parents=True,exist_ok=True);env.update(STUDY_WORKTREE=str(BASE),STUDY_PRIVATE_ROOT=str(private),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    env['STUDY_RUN_ROOT']=str(private/'workflow-output'/recipe.get('id','smoke')/uuid.uuid4().hex)
    Path(env['STUDY_RUN_ROOT']).parent.mkdir(parents=True,exist_ok=True)
    for k,v in recipe.get('environment',{}).items():env[k]=expand(v,env)
    gpu=recipe.get('gpu_required',recipe['backend']!='cpu')
    budget=recipe.get('timeout_s',300)
    if not 1<=budget<=1800:raise ValueError('Physics workflow budget must be 1..1800 seconds')
    inventory=private/('inventory-'+uuid.uuid4().hex+'.json')
    subprocess.run([sys.executable,str(BASE/'tools/collect_inventory.py'),'--node','halo','--output',str(inventory)],check=True,env=env,cwd=BASE,timeout=180)
    lock=contextlib.nullcontext()
    if gpu:
        captured=json.loads(inventory.read_text());info=captured['commands']['rocminfo'];arch=recipe.get('target_arch','gfx1151');name=recipe.get('target_name','8060S');assert info.get('rc')==0 and arch in info['stdout']and name in info['stdout'],'Expected AMD device not observed'
        targets=re.findall(r'^\s*Name:\s+(gfx[0-9]+)\s*$',info['stdout'],re.M)
        selector=os.environ.get('CHECKED_AMD_DEVICE')
        if selector is None:
            if targets!=[arch]:raise ValueError('Multiple HSA GPUs; provide CHECKED_AMD_DEVICE explicitly')
            selector='0'
        available=int(re.search(r'MemAvailable:\s+(\d+)',Path('/proc/meminfo').read_text()).group(1))*1024
        if available<(10 if recipe['suite']=='nekrs'else 6)*2**30:raise ValueError('Insufficient current memory for this bounded workflow; existing services remain running')
        env.update(ROCR_VISIBLE_DEVICES=selector,HIP_VISIBLE_DEVICES='0',STUDY_AMD_ARCH=arch,STUDY_AMD_NAME=name)
        lock=(private/'study-gpu.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    else:
        env.update(ROCR_VISIBLE_DEVICES='',HIP_VISIBLE_DEVICES='',CUDA_VISIBLE_DEVICES='')
    if 'PY312' not in env:
        candidates=sorted((root/'python').glob('cpython-3.12*/bin/python3.12'))
        if candidates:env['PY312']=str(candidates[-1])
    command=[expand(v,env)for v in recipe['command']]
    with lock:
        result=subprocess.run([sys.executable,str(BASE/'tools/run_case.py'),'--node','halo','--suite',recipe['suite'],'--case',recipe.get('case',recipe.get('case_id')),'--backend',recipe['backend'],'--timeout',str(budget),'--',*command],env=env,cwd=BASE,timeout=budget+30)
    # Deliberately retains PENDING_VALIDATION until the physics-specific evidence review.
    return result.returncode
