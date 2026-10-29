"""Read install/run recipes without depending on a local experiment history."""
import json
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]


def read_json(path):
    def invalid(value):
        raise ValueError('Non-finite JSON value: ' + value)
    return json.loads(Path(path).read_text(), parse_constant=invalid)


def recipes(base=BASE):
    return read_json(Path(base) / 'recipes/manifest.json')['recipes']


def resolve(identifier, base=BASE):
    data = read_json(Path(base) / 'recipes/manifest.json')
    identifier = data.get('aliases', {}).get(identifier, identifier)
    found = next((r for r in data['recipes'] if r['id'] == identifier), None)
    if found is None:
        raise ValueError('Unknown recipe: ' + identifier)
    return found


def inventory(base=BASE, engine=None):
    base = Path(base)
    data = read_json(base / 'recipes/engines.json')
    selected = [r for r in data['engines'] if engine is None or r['id'] == engine]
    if not selected:
        raise ValueError('Unknown simulator: ' + str(engine))
    rows = recipes(base)
    return {'engines': [dict(item, recipes=[r for r in rows if r['engine'] == item['id']]) for item in selected],
            'executes_simulation': False}


def check(base=BASE):
    base = Path(base)
    rows = recipes(base)
    engines = inventory(base)['engines']
    engine_ids = [r['id'] for r in engines]
    ids = [r['id'] for r in rows]
    configs = [r['configuration'] for r in rows]
    if len(ids) != len(set(ids)) or len(configs) != len(set(configs)):
        raise ValueError('Duplicate recipe or physics configuration')
    if len(engine_ids) != len(set(engine_ids)) or set(engine_ids) != {r['engine'] for r in rows}:
        raise ValueError('Engine registry does not match recipes')
    cases = {(r['suite'], r['id']) for r in read_json(base / 'configs/cases.json')}
    for row in rows:
        if not row['command'] or not 1 <= row['timeout_s'] <= 1800:
            raise ValueError('Missing command or invalid bounded timeout')
        if (row['suite'], row['case']) not in cases:
            raise ValueError('Recipe case is not registered')
        if row['backend'] not in ('hip', 'amdgpu', 'cuda'):
            raise ValueError('Unknown backend')
        if not (base / row['documentation']).is_file():
            raise ValueError('Missing engine recipe document: ' + row['id'])
        if row.get('lock') and not (base / 'configs' / row['lock']).is_file():
            raise ValueError('Missing dependency lock')
    # A compact review summary describes prior scenes; it never validates a new child exit.
    summary = read_json(base / 'configs/verification-summary.json')['configurations']
    expected_reviewed={r['configuration']for r in rows if r.get('review_status')!='UNREVIEWED_CATALOG_ENTRY'}
    if {r['configuration']for r in summary}!=expected_reviewed or len(summary)!=len({r['configuration']for r in summary}):
        raise ValueError('Reviewed configuration summary contains unknown or duplicate entries')
    by_config = {r['configuration']: r for r in rows}
    for item in summary:
        expected = by_config[item['configuration']]
        if (item['g1'] is not True or item['backend'] != expected['backend'] or
                item['status'] != ('CPU_ONLY' if item['backend'] == 'cpu' else 'PASS')):
            raise ValueError('Review summary changes the physics backend or validity')
        if item['backend'] != 'cpu' and item['device'] != 'gfx1151':
            raise ValueError('Unexpected reviewed GPU target')
    return {'engines': len(engines), 'recipes': len(rows), 'reviewed_configurations':len(summary),'unreviewed_configurations':len(configs)-len(summary),'local_run_history_required': False,
            'executes_simulation': False}
