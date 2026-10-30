"""Configurable study paths; machine-specific values belong outside version control."""
from __future__ import annotations
import json,os,pathlib,shlex,tempfile

_HERE=pathlib.Path(__file__).resolve().parent
REPO_ROOT=pathlib.Path(os.environ.get('STUDY_WORKTREE',_HERE.parent if _HERE.name=='study'else _HERE/'repo'))
def profile():
 path=pathlib.Path(os.environ.get('STUDY_PROFILE',REPO_ROOT/'private/study-profile.json'))
 return json.loads(path.read_text(encoding='utf-8'))if path.is_file()else{}
def value(key,default=None):
 return os.environ.get(key,profile().get(key,default))
def configured_path(text):
 # Remote POSIX paths must retain '/' when a Windows client builds SSH commands.
 if os.name=='nt'and str(text).startswith('/'):return pathlib.PurePosixPath(text)
 return pathlib.Path(text).expanduser()
def run_root():
 root=value('LAB_ROOT',value('STUDY_RUN_ROOT'))
 if not root:raise RuntimeError('Set LAB_ROOT or STUDY_RUN_ROOT to an external study workspace; see study/README.md')
 return configured_path(root)
def storage_root():
 configured=value('STUDY_STORAGE_ROOT')
 return configured_path(configured)if configured else run_root()/'storage'
def report_root():return pathlib.Path(value('STUDY_REPORT_ROOT',REPO_ROOT/'report')).expanduser()
def skill_root(name):return pathlib.Path(value('STUDY_SKILLS_ROOT',pathlib.Path.home()/'.codex/skills'))/name
def expand_runtime(template):
 """Expand configured locations; retain portable placeholders in public mode."""
 if os.environ.get('STUDY_PUBLIC')=='1':return template
 root=value('LAB_ROOT',value('STUDY_RUN_ROOT'))
 values={
  'REPO_ROOT':str(REPO_ROOT),'LAB_ROOT':root,
  'STUDY_STORAGE_ROOT':value('STUDY_STORAGE_ROOT',str(configured_path(root)/'storage')if root else None),
  'STUDY_SSH_TARGET':value('STUDY_SSH_TARGET'),'STUDY_SSH_PORT':str(value('STUDY_SSH_PORT',22)),
  'ROCM_PATH':value('ROCM_PATH'),'ROCM_BLOGS_ROOT':value('ROCM_BLOGS_ROOT'),
  'HUMANIZER_SKILL_ROOT':str(skill_root('humanize-korean'))if '${HUMANIZER_SKILL_ROOT}'in template else None,
  'NODE_VALIDATION_SKILL_ROOT':str(skill_root('amd-node-validation'))if '${NODE_VALIDATION_SKILL_ROOT}'in template else None,
  'WARP_CACHE_ROOT':value('WARP_CACHE_ROOT',str(pathlib.Path(tempfile.gettempdir())/'robotics-sim-lab-warp')),
  'GSPLAT_SOURCE_ROOT':value('GSPLAT_SOURCE_ROOT',str(configured_path(root)/'storage/upstream/gsplat')if root else None),
  'ETHIER_CASE_ROOT':value('ETHIER_CASE_ROOT',str(pathlib.Path(tempfile.gettempdir())/'robotics-sim-lab-ethier')),
  # This is a path inside the pinned Taichi image, not the caller's venv.
  'PYTHON_SITE_PACKAGES':value('PYTHON_SITE_PACKAGES','/usr/local/lib/python3.12/dist-packages'),
  'CONFLUENCE_SITE':value('CONFLUENCE_SITE'),'CONFLUENCE_DRAFT_URL':value('CONFLUENCE_DRAFT_URL')}
 for key,location in values.items():
  if location is not None:template=template.replace('${'+key+'}',str(location))
 return template
def runtime_path(template):
 text=expand_runtime(template)
 if '${'in text:raise RuntimeError('Unconfigured study path: '+text)
 return pathlib.Path(text)
def ssh_target():
 target=value('STUDY_SSH_TARGET')
 if not target:raise RuntimeError('Set STUDY_SSH_TARGET or use an ignored private/study-profile.json')
 return target
def ssh_prefix():
 return ['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20','-o','ServerAliveInterval=30','-o','ServerAliveCountMax=10','-o','StrictHostKeyChecking='+('no'if value('STUDY_STRICT_HOST_KEY_CHECKING',True)is False else'yes'),'-p',str(value('STUDY_SSH_PORT',22)),ssh_target()]
def scp_prefix():
 return ['scp','-q','-o','ServerAliveInterval=30','-o','StrictHostKeyChecking='+('no'if value('STUDY_STRICT_HOST_KEY_CHECKING',True)is False else'yes'),'-P',str(value('STUDY_SSH_PORT',22))]
def remote_file(path):return ssh_target()+':'+shlex.quote(str(path))


def script_index():
    return json.loads((REPO_ROOT/'study/scripts.json').read_text(encoding='utf-8'))['scripts']

def source_reference(name):
    return script_index().get(name, 'study/'+name)

def script_path(name):
    """Resolve a registered source file, or its unchanged flat-deployment name."""
    if name not in script_index():raise ValueError('Unregistered study command: '+name)
    flat=_HERE/name
    if _HERE.name!='study' and flat.is_file():return flat
    return REPO_ROOT/script_index()[name]

def script_command(name, interpreter=None):
    import sys
    return [interpreter or sys.executable, str(REPO_ROOT/'study/run.py'), name]

def activate_imports():
    """Expose only the registered helper directories to study command imports."""
    import sys
    paths=[REPO_ROOT/'study']+sorted({(REPO_ROOT/path).parent for path in script_index().values()})
    for path in reversed(paths):
        if str(path) not in sys.path:sys.path.insert(0,str(path))
