#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Adapted API/example patterns from Genesis World contributors. Study-specific geometry, validation and integration changes.
"""Small headless adaptations of upstream coupling/sph_rigid.py and tutorials/mpm.py."""
import argparse
import time
import numpy as np
from genesis_common import gs,array,init,sync,begin_profile,emit
p=argparse.ArgumentParser();p.add_argument('--backend',choices=('cpu','amdgpu','cuda'),required=True)
p.add_argument('--solver',choices=('sph','mpm','coupling'),required=True);p.add_argument('--steps',type=int,choices=(10,50),default=10)
p.add_argument('--mass-readout',choices=('accessor','static_info'),default='accessor',help='Explicit read-only diagnostic alternative to the broken upstream SPH mass accessor')
a=p.parse_args();init(a.backend);start=time.perf_counter()
opts=dict(lower_bound=(-0.3,-0.3,0),upper_bound=(0.3,0.3,0.6),particle_size=0.04)
scene=gs.Scene(sim_options=gs.options.SimOptions(dt=0.001,substeps=2),show_viewer=False,
               **({'mpm_options':gs.options.MPMOptions(grid_density=32,**opts)} if a.solver=='mpm' else {'sph_options':gs.options.SPHOptions(hash_grid_cell_size=0.08,**opts)}))
scene.add_entity(gs.morphs.Plane())
material=gs.materials.MPM.Liquid(sampler='regular') if a.solver=='mpm' else gs.materials.SPH.Liquid(sampler='regular',mu=0.01)
water=scene.add_entity(morph=gs.morphs.Box(pos=(0,0,0.25),size=(0.12,0.12,0.12)),material=material)
cube=None
if a.solver=='coupling':
    cube=scene.add_entity(morph=gs.morphs.Box(pos=(0,0,0.19),size=(0.06,0.06,0.06),fixed=True),material=gs.materials.Rigid(needs_coup=True,coup_friction=0))
scene.build();sync();build_s=time.perf_counter()-start
def read_mass():
    if a.mass_readout=='accessor':
        return float(array(water.get_mass()).sum())
    assert a.solver in ('sph','coupling')
    # This procedural scene contains one fluid entity. Preserve the original
    # upstream accessor and solver; inspect the initialized static mass field.
    mass=array(scene.sim.sph_solver.particles_info.mass.to_numpy()).reshape(-1)
    assert len(mass)==len(array(water.get_particles_pos()).reshape(-1,3))
    # SPH upstream defines volume as 0.8 * particle_size**3 (not a cube volume).
    assert np.allclose(mass,0.8*(0.04**3)*1000,rtol=1e-5,atol=1e-8)
    return float(mass.sum())
initial=array(water.get_particles_pos()).reshape(-1,3);m0=read_mass();count=len(initial)
warm=time.perf_counter();scene.step();sync();warmup_s=time.perf_counter()-warm
begin_profile();start=time.perf_counter();samples=[];finite=True;max_speed=0.;inside=True
for _ in range(a.steps):
    scene.step();state=water.get_state();x=array(state.pos).reshape(-1,3);v=array(state.vel)
    finite &= bool(np.isfinite(x).all() and np.isfinite(v).all()); max_speed=max(max_speed,float(abs(v).max()))
    inside &= bool((x>=np.array([-0.32,-0.32,-0.02])).all() and (x<=np.array([0.32,0.32,0.62])).all())
    samples.append(x.mean(axis=0).tolist())
sync();step_wall_s=time.perf_counter()-start;m1=read_mass();end=array(water.get_particles_pos()).reshape(-1,3)
t=(a.steps+1)*0.001;error=abs(end[:,2].mean()-(initial[:,2].mean()-9.81*t*t/2));drift=abs(m1-m0)/m0
metrics={'mass_initial_kg':m0,'mass_final_kg':m1,'relative_mass_drift':drift,'com_freefall_error_m':float(error),'max_speed_m_s':max_speed}
metrics['static_info_mass_readout']=a.mass_readout=='static_info'
gates={'finite_state':finite,'domain_bounds':inside,'speed':max_speed<=5,'particle_count':len(end)==count and count>0,'mass_conservation':drift<=1e-6}
if cube is None:gates.update(com_freefall=error<=0.005,downward_com=end[:,2].mean()<initial[:,2].mean())
else:gates['fixed_rigid']=bool(abs(array(cube.get_pos()).reshape(3)-np.array([0,0,0.19])).max()<=1e-6)
emit(a.backend,gates,solver=a.solver,steps=a.steps,dt=0.001,substeps=2,particles=count,particle_size=0.04,grid_cell_size=0.03125 if a.solver=='mpm' else 0.08,warmup=1,build_s=build_s,warmup_s=warmup_s,step_wall_s=step_wall_s,metrics=metrics,com_samples=samples)
