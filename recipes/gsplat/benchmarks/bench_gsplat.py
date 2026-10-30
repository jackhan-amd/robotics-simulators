"""Synthetic GSplat raster smoke and synchronized frame throughput on the selected HIP GPU."""
from workspace import expand_runtime, run_root, runtime_path
import argparse,json,pathlib,statistics,time
import torch
from gsplat import rasterization
p=argparse.ArgumentParser();p.add_argument('--gaussians',type=int,default=10000);p.add_argument('--width',type=int,default=640);p.add_argument('--height',type=int,default=480);p.add_argument('--smoke',action='store_true');a=p.parse_args()
assert torch.cuda.device_count()==1 and 'MI355X'in torch.cuda.get_device_name(0) and torch.version.hip
torch.manual_seed(0);n=a.gaussians;device='cuda';means=torch.randn(n,3,device=device)*.5;means[:,2]=torch.rand(n,device=device)*2+3;quats=torch.zeros(n,4,device=device);quats[:,0]=1;scales=torch.full((n,3),.015,device=device);opacities=torch.full((n,),.5,device=device);colors=torch.rand(n,3,device=device);views=torch.eye(4,device=device)[None];focal=.8*a.width;K=torch.tensor([[[focal,0,a.width/2],[0,focal,a.height/2],[0,0,1]]],device=device)
def render():return rasterization(means,quats,scales,opacities,colors,views,K,a.width,a.height,packed=False)
start=time.perf_counter()
with torch.no_grad():
 for _ in range(1 if a.smoke else 10):rgb,alpha,info=render()
torch.cuda.synchronize();warmup_s=time.perf_counter()-start
frames=1 if a.smoke else 100;times=[];checks=[];torch.cuda.reset_peak_memory_stats()
with torch.no_grad():
 for rep in range(1 if a.smoke else 5):
  torch.cuda.synchronize();start=time.perf_counter()
  for _ in range(frames):rgb,alpha,info=render()
  torch.cuda.synchronize();times.append(time.perf_counter()-start)
  checks.append(bool(torch.isfinite(rgb).all()and torch.isfinite(alpha).all()and alpha.max()>0 and rgb.shape==(1,a.height,a.width,3)))
median=statistics.median(times)
if a.smoke:
 from PIL import Image
 Image.fromarray((rgb[0].clamp(0,1).cpu().numpy()*255).astype('uint8')).save(expand_runtime('${LAB_ROOT}/evidence/gsplat-synthetic.png'))
print(('SMOKE_RESULT_JSON:'if a.smoke else'BENCHMARK_RESULT_JSON:')+json.dumps(dict(engine='gsplat',implementation='AMD GSplat v1.5.3b2 plus allocator API compatibility',backend_observed='hip',physics_valid=all(checks),checks=checks,validation_scope='finite rendered signal and shape, not physics or perceptual quality',gaussians=n,width=a.width,height=a.height,frames=frames,repeats=len(times),warmup_s=warmup_s,synchronized_rollout_s=times,median_s=median,frames_per_s=frames/median,peak_torch_gpu_memory_bytes=torch.cuda.max_memory_allocated(),torch=torch.__version__,torch_hip=torch.version.hip,packed=False,backward=False,readback_in_timing=False)))
