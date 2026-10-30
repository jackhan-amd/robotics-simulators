"""Recorded allocator API compatibility patch for PyTorch 2.14; no raster math changes."""
from workspace import expand_runtime, run_root, runtime_path
import hashlib,json,pathlib,subprocess
root=runtime_path('${GSPLAT_SOURCE_ROOT}');changes=[]
for p in (root/'gsplat').rglob('*'):
 if not p.is_file()or p.suffix not in ('.cu','.cpp','.hip','.h','.hpp','.cuh'):continue
 text=p.read_text(errors='replace');new=text
 for symbol in ['c10::hip::HIPCachingAllocator::get()','c10::cuda::CUDACachingAllocator::get()']:
  new=new.replace(symbol,'c10::GetAllocator(c10::DeviceType::CUDA)')
 if new!=text:
  new='#include <c10/core/Allocator.h>\n'+new
  changes.append(dict(path=str(p.relative_to(root)),before_sha256=hashlib.sha256(text.encode()).hexdigest(),after_sha256=hashlib.sha256(new.encode()).hexdigest()))
  p.write_text(new)
out=runtime_path('${LAB_ROOT}/evidence/gsplat-allocator-patch.json');out.write_text(json.dumps(changes,indent=2));print(json.dumps(changes))
