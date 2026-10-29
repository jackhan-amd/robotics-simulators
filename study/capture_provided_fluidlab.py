"""Actual provided MixingEnv GPU particle coordinates; separate from measurements."""
from workspace import expand_runtime, run_root, runtime_path
import json,pathlib
import numpy as np
from provided_fluidlab_model import example
R=run_root();reset,advance,check,meta=example();reset();advance(100);checks=check();assert checks['valid']
# The closure exposes the existing env through the advance function's captured sim.
sim=next(c.cell_contents for c in advance.__closure__ if hasattr(c.cell_contents,'simulator'))
state=sim.simulator.get_state();np.savez_compressed(R/'evidence/fluidlab-provided-particles.npz',x=state['x'],v=state['v'])
receipt=dict(engine='fluidlab',physics_valid=True,scene_metadata=meta,checks=checks,steps=100,scope='actual HIP forward replay of supplied MixingEnv; GPU particle data exported for postprocessing; no renderer or capture inside performance measurements')
(R/'evidence/fluidlab-provided-capture.json').write_text(json.dumps(receipt,indent=2));reset.cleanup();print('SMOKE_RESULT_JSON:'+json.dumps(receipt),flush=True)
