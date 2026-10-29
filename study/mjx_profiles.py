"""Named software profiles shared by measurement and publication tools."""
import json,pathlib
from workspace import REPO_ROOT
PROFILES={
 'jax0112-safe-fusion':dict(version='0.11.2',compiler_profile='safe-fusion',xla_flags='--xla_disable_hlo_passes=fusion',case_prefix='provided-mjx714-jax0112-humanoid',venv='mujoco-mjx-0112-rocm'),
 'jax0120-default':dict(version='0.12.0',compiler_profile='default',xla_flags='',case_prefix='provided-mjx714-jax0120-humanoid',venv='mujoco-mjx-0120-rocm')}
def selected():
 path=REPO_ROOT/'study/mjx-profile.json'
 if not path.is_file():path=pathlib.Path(__file__).with_name('mjx-profile.json')
 name=json.loads(path.read_text(encoding='utf-8'))['profile']if path.is_file()else'jax0112-safe-fusion'
 return dict(name=name,**PROFILES[name])
