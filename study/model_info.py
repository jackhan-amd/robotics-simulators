from workspace import expand_runtime, run_root, runtime_path
import json,mujoco
m=mujoco.MjModel.from_xml_path(expand_runtime('${LAB_ROOT}/repo/configs/freefall.xml'))
print(json.dumps(dict(mujoco=mujoco.__version__,nbody=m.nbody,nv=m.nv,nq=m.nq,nu=m.nu,ngeom=m.ngeom,timestep=m.opt.timestep,solver=str(mujoco.mjtSolver(m.opt.solver)),iterations=m.opt.iterations,ls_iterations=m.opt.ls_iterations,tolerance=m.opt.tolerance,integrator=str(mujoco.mjtIntegrator(m.opt.integrator)),cone=str(mujoco.mjtCone(m.opt.cone)),jacobian=str(mujoco.mjtJacobian(m.opt.jacobian)),disableflags=int(m.opt.disableflags))))
