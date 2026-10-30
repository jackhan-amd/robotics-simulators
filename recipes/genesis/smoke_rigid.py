#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Adapted API/example patterns from Genesis World contributors. Study-specific geometry, validation and integration changes.
"""Small procedural rigid cases; tolerances in docs/06_validation.md."""
import argparse
import tempfile
from pathlib import Path
import time
import json
import faulthandler
import numpy as np
from genesis_common import gs, array, init, sync, begin_profile, emit
p=argparse.ArgumentParser()
p.add_argument('--backend',choices=('cpu','amdgpu','cuda'),required=True)
p.add_argument('--case',choices=('freefall','contacts','articulation'),default='freefall')
p.add_argument('--constraint-solver',choices=('Newton','CG'),default='Newton')
p.add_argument('--steps',type=int,default=50)
p.add_argument('--dt',type=float,choices=(0.001,0.0005),default=0.001)
p.add_argument('--sustained',action='store_true')
p.add_argument('--trace-progress',action='store_true',help='Diagnostic per-step sync/timing and 60 s Python stack dumps')
a=p.parse_args()
assert 1 <= a.steps <= 10000
assert not a.sustained or (a.case == 'contacts' and abs(a.steps*a.dt-2.0)<1e-9)
trace_start=time.perf_counter()
def progress(stage,step=None):
    if a.trace_progress:
        print('SMOKE_PROGRESS_JSON:'+json.dumps(dict(stage=stage,step=step,elapsed_s=time.perf_counter()-trace_start)),flush=True)
if a.trace_progress:
    faulthandler.dump_traceback_later(60,repeat=True)
progress('initialize_begin')
print("SMOKE_PHASE: initialize", flush=True)
init(a.backend)
progress('initialize_end')
print("SMOKE_PHASE: initialized", flush=True)
build_start=time.perf_counter()
scene=gs.Scene(sim_options=gs.options.SimOptions(dt=a.dt,substeps=2),rigid_options=gs.options.RigidOptions(constraint_solver=getattr(gs.constraint_solver,a.constraint_solver)),show_viewer=False)
scene.add_entity(gs.morphs.Plane())
objects=[]
tmp=None
if a.case=='articulation':
    tmp=tempfile.TemporaryDirectory(prefix='smoke-pendulum-')
    links='<link name="base"/>'
    for n in (1,2):
        links+=f'<link name="l{n}"><inertial><origin xyz="0 0 -0.1"/><mass value="0.1"/><inertia ixx="0.00034" ixy="0" ixz="0" iyy="0.00034" iyz="0" izz="0.00001"/></inertial><visual><origin xyz="0 0 -0.1"/><geometry><box size="0.02 0.02 0.2"/></geometry></visual><collision><origin xyz="0 0 -0.1"/><geometry><box size="0.02 0.02 0.2"/></geometry></collision></link>'
        parent='base' if n==1 else 'l1'
        xyz='0 0 0' if n==1 else '0 0 -0.2'
        links+=f'<joint name="j{n}" type="revolute"><parent link="{parent}"/><child link="l{n}"/><origin xyz="{xyz}"/><axis xyz="0 1 0"/><limit lower="-1" upper="1" effort="1" velocity="10"/></joint>'
    urdf=Path(tmp.name)/'pendulum.urdf';urdf.write_text('<robot name="procedural_pendulum">'+links+'</robot>')
    robot=scene.add_entity(gs.morphs.URDF(file=str(urdf),fixed=True,pos=(0,0,0.8)))
else:
    for z in ([0.8] if a.case=='freefall' else [0.051,0.153,0.255]):
        objects.append(scene.add_entity(gs.morphs.Box(size=(0.1,0.1,0.1),pos=(0,0,z),fixed=False)))
print("SMOKE_PHASE: scene_build", flush=True)
scene.build();sync();build_s=time.perf_counter()-build_start
progress('build_end')
print("SMOKE_PHASE: scene_built", flush=True)
if a.case=='articulation':
    robot.set_qpos([0.4,-0.2]); initial=array(robot.get_qpos())
else:
    initial=np.stack([array(o.get_pos()).reshape(-1,3)[0] for o in objects])
print("SMOKE_PHASE: warmup", flush=True)
warm_start=time.perf_counter()
for n in range(5):
    progress('warmup_step_begin',n+1);scene.step();progress('warmup_step_returned',n+1)
    if a.trace_progress:sync();progress('warmup_step_synced',n+1)
sync();warmup_s=time.perf_counter()-warm_start
progress('warmup_end')
if a.sustained:
    scene.reset();sync()
print("SMOKE_PHASE: measured_steps", flush=True)
progress('profile_begin');begin_profile();progress('profile_end'); start=time.perf_counter(); samples=[];velocities=[];quaternions=[]
for n in range(a.steps):
    progress('measured_step_begin',n+1)
    scene.step()
    progress('measured_step_returned',n+1)
    if a.trace_progress:sync();progress('measured_step_synced',n+1)
    if a.case=='articulation': samples.append(array(robot.get_qpos()).reshape(-1).tolist())
    else:
        samples.append([array(o.get_pos()).reshape(-1,3)[0].tolist() for o in objects])
        velocities.append([array(o.get_vel()).reshape(-1,3)[0].tolist() for o in objects])
    if a.sustained:quaternions.append([array(o.get_quat()).reshape(-1,4)[0].tolist() for o in objects])
    progress('measured_readback_end',n+1)
sync();step_wall_s=time.perf_counter()-start
x=np.asarray(samples); gates={'finite_state':bool(np.isfinite(x).all())};metrics={}
if a.case=='articulation':
    metrics={'max_abs_angle':float(abs(x).max()),'motion':float(abs(x[-1]-initial).max())}
    gates.update(joint_limits=metrics['max_abs_angle']<=1.02,motion=metrics['motion']>=1e-7)
else:
    v=np.asarray(velocities);gates['finite_velocity']=bool(np.isfinite(v).all())
    if a.case=='freefall':
        t=(np.arange(a.steps)+6)*a.dt
        metrics={'analytic_z_error_m':float(abs(x[:,0,2]-(initial[0,2]-9.81*t*t/2)).max()),'velocity_error_m_s':float(abs(v[:,0,2]+9.81*t).max())}
        gates.update(analytic_freefall=metrics['analytic_z_error_m']<=0.002,velocity=metrics['velocity_error_m_s']<=0.01)
    else:
        metrics={'min_bottom_z_m':float(x[:,:,2].min()-0.05),'max_speed':float(abs(v).max()),'max_rise_m':float((x[:,:,2]-initial[:,2]).max()),'max_drop_m':float((initial[:,2]-x[:,:,2]).max())}
        gates.update(penetration=metrics['min_bottom_z_m']>=-0.01,speed=metrics['max_speed']<=5,rise=metrics['max_rise_m']<=0.05,drop=metrics['max_drop_m']<=0.1)
if a.sustained:
    q=np.asarray(quaternions);w,qx,qy,qz=np.moveaxis(q,-1,0)
    zextent=0.05*(abs(2*(qx*qz-w*qy))+abs(2*(qy*qz+w*qx))+abs(1-2*(qx*qx+qy*qy)))
    metrics.update(oriented_min_corner_z_m=float((x[:,:,2]-zextent).min()),quaternion_norm_error=float(abs(np.linalg.norm(q,axis=-1)-1).max()),tail_max_speed_component_m_s=float(abs(v[int(0.8*a.steps):]).max()),final_center_height_error_m=float(abs(x[-1,:,2]-np.array([0.05,0.15,0.25])).max()))
    gates.update(oriented_penetration=metrics['oriented_min_corner_z_m']>=-0.001,quaternion_finite=bool(np.isfinite(q).all()),quaternion_normalized=metrics['quaternion_norm_error']<=1e-3,settled=metrics['tail_max_speed_component_m_s']<=0.02,final_center_height=metrics['final_center_height_error_m']<=0.003)
if a.trace_progress:faulthandler.cancel_dump_traceback_later()
emit(a.backend,gates,trace_progress=a.trace_progress,scene_case=a.case,constraint_solver=a.constraint_solver,steps=a.steps,dt=a.dt,sustained=a.sustained,reset_after_warmup=a.sustained,substeps=2,warmup=5,build_s=build_s,warmup_s=warmup_s,step_wall_s=step_wall_s,metrics=metrics,positions=samples,velocities=velocities)
