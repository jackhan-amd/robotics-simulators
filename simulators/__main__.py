"""Inspect simulator recipes or explicitly execute one bounded smoke."""
import argparse
import json
from pathlib import Path
import sys
from simulators.catalog import check, inventory, resolve


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    commands.add_parser('list')
    commands.add_parser('check')
    commands.add_parser('build', help='Build optional local HTML; no run history required')
    show = commands.add_parser('show'); show.add_argument('id')
    smoke = commands.add_parser('smoke'); smoke.add_argument('id'); smoke.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    try:
        if args.action == 'list':
            for engine in inventory()['engines']:
                print(engine['title'] + ': ' + engine['documentation'])
                for row in engine['recipes']:
                    print('  ' + row['id'] + ' [' + row['backend'] + ']')
            return 0
        if args.action == 'show':
            data = inventory()
            if args.id in {r['id'] for r in data['engines']}:
                result = inventory(engine=args.id)
            else:
                result = resolve(args.id)
        elif args.action == 'smoke':
            sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
            from workflows import execute
            return execute(resolve(args.id), args.execute)
        elif args.action == 'build':
            from simulators.site import build
            result = build()
        else:
            result = check()
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (KeyError, OSError, ValueError, AssertionError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
