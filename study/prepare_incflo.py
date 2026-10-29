"""Restore missing cavity input from the pinned upstream benchmark and adapt device/size checks."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import pathlib
R=run_root();S=storage_root();repo=R/'repo'
target=repo/'configs/incflo/cavity16.in';target.parent.mkdir(exist_ok=True)
text=(S/'upstream/incflo/test_2d/benchmark.lid_driven_cavity').read_text()
text+='\nincflo.fixed_dt = 0.0001\namr.n_cell = 16 16\namr.max_grid_size = 16\namr.blocking_factor = 8\nmac_proj.verbose = 2\nnodal_proj.verbose = 2\n'
target.write_text(text)
src=(repo/'smokes/incflo_case.py').read_text()
src=src.replace("assert '8060S' in name.value.decode()","assert os.environ['STUDY_AMD_NAME'] in name.value.decode()")
src=src.replace("choices=(10,50),default=10","default=10")
src=src.replace("a=p.parse_args();base=Path(__file__).resolve().parents[1]",expand_runtime("p.add_argument('--cells',type=int,default=16)\na=p.parse_args();base=Path('${LAB_ROOT}/repo')"))
src=src.replace("f'amr.plot_int={a.steps}']","f'amr.plot_int={a.steps}',f'amr.n_cell={a.cells} {a.cells}',f'amr.max_grid_size={a.cells}']")
src=src.replace("(nx,ny)==(16,16)","(nx,ny)==(a.cells,a.cells)")
src=src.replace("'cells':256,'shape':[16,16]","'cells':a.cells**2,'shape':[a.cells,a.cells]")
(R/'incflo_mi355x.py').write_text(src)
print('Prepared input from pinned upstream and MI355X-only harness; solver unchanged.')
