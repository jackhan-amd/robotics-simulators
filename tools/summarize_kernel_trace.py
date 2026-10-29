#!/usr/bin/env python3
"""Export safe actual-device kernel evidence from a private rocprofv3 CSV trace."""
import argparse,csv,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--trace',type=Path,required=True);p.add_argument('--isa',required=True);p.add_argument('--run-id',required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--kind',choices=('chrono','dem'),required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
agent_files=list(a.trace.rglob('*agent_info.csv'));trace_files=list(a.trace.rglob('*kernel_trace.csv'))
assert len(agent_files)==len(trace_files)==1
agents=list(csv.DictReader(agent_files[0].open()));rows=list(csv.DictReader(trace_files[0].open()));assert rows
by_id={'Agent '+row['Node_Id']:row for row in agents}
observed={by_id[row['Agent_Id']]['Name'] for row in rows}
assert observed=={a.isa},observed
assert all(int(r['End_Timestamp'])>int(r['Start_Timestamp']) for r in rows)
terms=('chrono::fsi::sph::',) if a.kind=='chrono' else ('integrateSpheres','computeSphereForces','populateSpheres','initializeLocalPositions')
names=sorted({r['Kernel_Name'] for r in rows if any(t in r['Kernel_Name'] for t in terms)})
assert names and all('/' not in name for name in names)
out=dict(trace_kind='rocprofv3 HIP kernel dispatch trace',run_id=a.run_id,isa_observed=a.isa,kernel_dispatches=len(rows),physics_kernel_samples=names[:12],binary_sha256=hashlib.sha256(a.binary.read_bytes()).hexdigest(),raw_trace_private=True,g2_qualified=False)
a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='physics_kernel_samples'}))
