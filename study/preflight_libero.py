"""Dependency/asset checks only; never creates or steps a simulation."""
from workspace import expand_runtime, run_root, runtime_path
import ast,pathlib,subprocess
R=run_root();source=R/'provided_instinct_suite.py';tree=ast.parse(source.read_text());body=[]
for node in tree.body:
 if isinstance(node,ast.FunctionDef):break
 body.append(node)
namespace={};exec(compile(ast.Module(body=body,type_ignores=[]),str(source),'exec'),namespace)
code='''import hashlib,json,pathlib,torch,mujoco,robosuite
from libero.libero import benchmark,get_libero_path
from libero.libero.envs import env_wrapper
from instinct_sim_env import hip_env
suite=benchmark.get_benchmark_dict()['libero_spatial']();task=suite.get_task(0)
p=pathlib.Path(get_libero_path('init_states'))/task.problem_folder/task.init_states_file
states=torch.load(p,map_location='cpu',weights_only=False)
print(json.dumps(dict(task=task.name,init_states_shape=list(states.shape),init_states_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),mujoco=mujoco.__version__,robosuite=robosuite.__version__,torch=torch.__version__,scope='imports and supplied initial-state load only; no simulator constructed/stepped')))
'''
raise SystemExit(subprocess.run([str(namespace['S']/'venvs/instinct-sim/bin/python'),'-c',code],env=namespace['env'],timeout=120).returncode)
