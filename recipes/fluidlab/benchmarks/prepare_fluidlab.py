"""Prepare dependencies for a separately supplied FluidLab source checkout."""
from workspace import expand_runtime, run_root, runtime_path,storage_root,value
import os,pathlib,subprocess
R=run_root();S=storage_root();src=pathlib.Path(value('FLUIDLAB_SOURCE_ROOT',S/'upstream/fluidlab'))
os.environ['PATH']=str(S/'tools/bin')+':'+os.environ['PATH']
def run(cmd):print('+',*map(str,cmd),flush=True);subprocess.run(list(map(str,cmd)),check=True,timeout=600)
if not src.exists():raise RuntimeError('Provide a separately authorized source checkout through FLUIDLAB_SOURCE_ROOT; see LICENSES.md')
commit=subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip()
assert commit=='7295eb6ed7ee92b2be471fd30b432238577f28ce','Use the recorded source pin'
run([R/'bin/uv','pip','install','--python',S/'venvs/taichi/bin/python','yacs','trimesh','scipy','pyyaml','mesh_to_sdf','imageio'])
run(['git','-C',src,'status','--short'])
