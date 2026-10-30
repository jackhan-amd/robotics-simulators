"""Add missing development aliases inside the private Mesa/GLVND prefix only."""
from workspace import expand_runtime, run_root, runtime_path
import hashlib,json,os,pathlib,subprocess
R=run_root();lib=R/'storage/tools/lib';items=[]
for name,version in [('EGL','1'),('GL','1'),('OpenGL','0'),('GLX','0'),('GLdispatch','0')]:
 target=lib/f'lib{name}.so.{version}';alias=lib/f'lib{name}.so';assert target.is_file()and target.resolve().is_relative_to(lib.resolve())
 if not os.path.lexists(alias):alias.symlink_to(target.name)
 assert alias.resolve()==target.resolve();items.append(dict(alias=str(alias),target=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
(R/'evidence/headless-library-aliases.json').write_text(json.dumps(dict(scope='private user prefix only; no driver/global library changes',aliases=items),indent=2))
env=os.environ.copy();sdk=env['ROCM_PATH'];env.update(LD_LIBRARY_PATH=str(lib)+':'+sdk+'/lib:'+sdk+'/lib/llvm/lib',PYOPENGL_PLATFORM='egl',EGL_PLATFORM='surfaceless')
cmd=[str(R/'storage/venvs/taichi/bin/python'),'-c','from mesh_to_sdf import mesh_to_sdf; from OpenGL import GL, EGL; print("HEADLESS_IMPORT_PASS", bool(GL.glGetError), bool(EGL.eglGetCurrentContext))']
raise SystemExit(subprocess.run(cmd,env=env,timeout=60).returncode)
