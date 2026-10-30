"""Env-equivalent camera batch scaling using GSplat's supplied garden fixture/helper."""
from workspace import expand_runtime, run_root, runtime_path
import argparse,hashlib,json,pathlib,statistics,time
import numpy as np,torch
from gsplat import rasterization
from gsplat._helper import load_test_data
p=argparse.ArgumentParser();p.add_argument('--envs',type=int,required=True);p.add_argument('--smoke',action='store_true');a=p.parse_args();torch.manual_seed(0)
assert torch.cuda.device_count()==1 and torch.version.hip and 'MI355X'in torch.cuda.get_device_name(0)
source=runtime_path('${GSPLAT_SOURCE_ROOT}/assets/test_garden.npz');means,quats,scales,opacities,colors,viewmats,Ks,width,height=load_test_data(data_path=str(source),device='cuda');viewmats=viewmats[:1].repeat(a.envs,1,1);Ks=Ks[:1].repeat(a.envs,1,1)
def render():return rasterization(means,quats,scales,opacities,colors,viewmats,Ks,width,height,packed=False)
start=time.perf_counter()
for _ in range(10):rgb,alpha,_=render()
torch.cuda.synchronize();warmup=time.perf_counter()-start;times=[];checks=[];frames=1 if a.smoke else 100
for _ in range(1 if a.smoke else 5):
 torch.cuda.synchronize();start=time.perf_counter()
 for i in range(frames):rgb,alpha,_=render()
 torch.cuda.synchronize();times.append(time.perf_counter()-start);checks.append(bool(torch.isfinite(rgb).all()and torch.isfinite(alpha).all()and alpha.max()>0 and rgb.shape==(a.envs,height,width,3)))
if a.smoke:
 from PIL import Image
 Image.fromarray((rgb[0].clamp(0,1).cpu().numpy()*255).astype(np.uint8)).save(expand_runtime('${LAB_ROOT}/evidence/gsplat-provided-garden.png'))
median=statistics.median(times);valid=all(checks)
print(('SMOKE_RESULT_JSON:'if a.smoke else'BENCHMARK_RESULT_JSON:')+json.dumps(dict(engine='gsplat',implementation='provided garden fixture / native camera batch',physics_valid=valid,validation_scope='finite rendered image/alpha, correct shape; renderer, no physics simulation',backend_observed='hip',scene='load_test_data default crop/grid from supplied assets/test_garden.npz',source_commit='ff8bc5489545bcc1b5a2b997d975834429a0d7af',asset_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),envs=a.envs,gaussians=len(means),width=width,height=height,frames=frames*a.envs,frames_per_env=frames,repeats=len(times),synchronized_rollout_s=times,median_s=median,frames_per_s=a.envs*frames/median,per_env_frames_per_s=frames/median,warmup_frames=10,warmup_s=warmup,checks=checks,peak_torch_gpu_memory_bytes=torch.cuda.max_memory_allocated(),scope='unmodified supplied helper data and camera; seed 0; clone first camera N times, shared static Gaussian geometry; no invented scene or training checkpoint; readback/build excluded')))
raise SystemExit(0 if valid else 3)
