import argparse,pathlib
base=pathlib.Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('log',type=pathlib.Path);p=parser.parse_args().log
s=p.read_text(encoding='utf-8');lines=s.splitlines();print(s[:1000])
keys=['.def("read_state"','.def("options"','.def_property("options"','.def_property_readonly("timestep"','m.def("','"read_contacts"']
for i,line in enumerate(lines):
 if any(k in line for k in keys):print('\n'.join(lines[max(0,i-2):min(len(lines),i+24)]))
