"""Synthetic fluid scale sweep, steady-state GPU stepping without per-step readback."""
import argparse,json,statistics,time
import numpy as np,torch,genesis as gs,quadrants as qd
p=argparse.ArgumentParser();p.add_argument('--solver',choices=['sph','mpm'],required=True);p.add_argument('--edge',type=int,required=True);a=p.parse_args()
gs.init(backend=gs.amdgpu,precision='32',seed=0,logging_level='warning');start=time.perf_counter()
opts=dict(lower_bound=(-1,-1,0),upper_bound=(1,1,2),particle_size=.04)
extra={'mpm_options':gs.options.MPMOptions(grid_density=32,**opts)}if a.solver=='mpm'else{'sph_options':gs.options.SPHOptions(hash_grid_cell_size=.08,**opts)}
scene=gs.Scene(sim_options=gs.options.SimOptions(dt=.001,substeps=2),show_viewer=False,**extra);scene.add_entity(gs.morphs.Plane());material=gs.materials.MPM.Liquid(sampler='regular')if a.solver=='mpm'else gs.materials.SPH.Liquid(sampler='regular',mu=.01);water=scene.add_entity(morph=gs.morphs.Box(pos=(0,0,1),size=(.04*a.edge,)*3),material=material);scene.build();qd.sync();torch.cuda.synchronize();build_s=time.perf_counter()-start
initial=water.get_particles_pos().detach().cpu().numpy().reshape(-1,3);count=len(initial)
start=time.perf_counter()
for _ in range(10):scene.step()
qd.sync();torch.cuda.synchronize();warmup_s=time.perf_counter()-start
times=[];checks=[]
for rep in range(5):
 scene.reset();qd.sync();torch.cuda.synchronize();start=time.perf_counter()
 for _ in range(100):scene.step()
 qd.sync();torch.cuda.synchronize();times.append(time.perf_counter()-start)
 state=water.get_state();x=state.pos.detach().cpu().numpy().reshape(-1,3);v=state.vel.detach().cpu().numpy();checks.append(bool(np.isfinite(x).all()and np.isfinite(v).all()and len(x)==count and abs(x[:,2].mean()-(initial[:,2].mean()-.5*9.81*.1**2))<.005))
median=statistics.median(times)
print('BENCHMARK_RESULT_JSON:'+json.dumps(dict(engine='genesis',case='fluid_'+a.solver,implementation='Genesis '+a.solver.upper(),backend_observed=gs.backend.name,physics_valid=all(checks),checks=checks,particles=count,requested_edge=a.edge,particle_size=.04,steps=100,repeats=5,dt=.001,substeps=2,build_s=build_s,compile_s=build_s,warmup_s=warmup_s,synchronized_rollout_s=times,median_s=median,step_per_s=100/median,particle_updates_per_s=count*100/median,readback_in_timing=False,scope='suspended liquid cube forward integration, not developed dam-break',genesis_version=gs.__version__)))
gs.destroy()
