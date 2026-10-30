"""Launch one registered benchmark/setup/report command from any source layout."""
import json,runpy,sys
from workspace import activate_imports,script_index,script_path

def main(argv=None):
    args=list(sys.argv[1:]if argv is None else argv)
    if not args or args[0]in('--list','--help','-h'):
        print('Usage: python tools/run.py <script.py> [arguments]')
        print(json.dumps(script_index(),indent=2));return 0
    command=args.pop(0)
    if command not in script_index():raise SystemExit('Unknown registered study command: '+command)
    activate_imports();path=script_path(command)
    sys.argv=[str(path),*args]
    runpy.run_path(str(path),run_name='__main__')
    return 0

if __name__=='__main__':raise SystemExit(main())
