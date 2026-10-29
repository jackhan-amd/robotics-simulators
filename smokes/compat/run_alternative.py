"""Run an existing smoke with explicit provenance; no upstream file mutation."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys

p = argparse.ArgumentParser()
p.add_argument('--source-root', type=Path)
p.add_argument('script', type=Path)
p.add_argument('arguments', nargs=argparse.REMAINDER)
a = p.parse_args()
sys.path.insert(0, str(a.script.resolve().parent))
if a.source_root:
    sys.path.insert(0, str(a.source_root.resolve()))
lib = ctypes.CDLL('libamdhip64.so')
version = ctypes.c_int()
assert lib.hipRuntimeGetVersion(ctypes.byref(version)) == 0
print('ALTERNATIVE_RUNTIME_VERSION:' + str(version.value), flush=True)
count = ctypes.c_int()
assert lib.hipGetDeviceCount(ctypes.byref(count)) == 0 and count.value == 1
name = ctypes.create_string_buffer(256)
assert lib.hipDeviceGetName(name, len(name), 0) == 0
assert os.environ['STUDY_AMD_NAME'] in name.value.decode()
print('ALTERNATIVE_DEVICE_JSON:' + json.dumps(dict(device_name=name.value.decode(), count=count.value)), flush=True)
# Absolute mapped paths stay only in private stdout, never in the public marker.
from proc_maps import library_paths
paths = library_paths(Path('/proc/self/maps').read_text(), 'libamdhip64.so.')
assert len(paths) == 1
path = paths.pop()
print('ALTERNATIVE_RUNTIME_RECEIPT:' + json.dumps(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())), flush=True)
sys.argv = [str(a.script)] + a.arguments
if a.source_root:
    import genesis
    assert Path(genesis.__file__).resolve().is_relative_to(a.source_root.resolve())
    sph = a.source_root/'genesis/engine/solvers/sph_solver.py'
    print('ALTERNATIVE_GENESIS_SOURCE_SHA256:' + hashlib.sha256(sph.read_bytes()).hexdigest(), flush=True)
runpy.run_path(str(a.script), run_name='__main__')
