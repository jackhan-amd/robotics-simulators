"""Optional local HTML index built entirely from versioned recipe files."""
from html import escape
from simulators.catalog import BASE, check, inventory


def build():
    result = check()
    items = inventory()['engines']
    links = ''.join('<li><a href="../../'+escape(x['documentation'], quote=True)+'">'+escape(x['title'])+'</a><p>'+escape(x['description'])+'</p></li>' for x in items)
    output = '<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Simulator recipes</title><style>body{font:16px/1.65 system-ui;max-width:960px;margin:40px auto;padding:0 20px}a{color:#155a8e}li{padding:10px}p{margin:4px 0}</style><h1>Simulator recipes</h1><p>각 엔진의 설치·설정·빌드·실행 절차를 연다.</p><ul>'+links+'</ul><p><a href="../../recipes/README.md">공통 준비</a> · <a href="../../docs/verification.md">검증 범위</a> · <a href="../../LICENSES.md">라이선스</a></p></html>'
    folder = BASE / '.runtime' / 'catalog'; folder.mkdir(parents=True, exist_ok=True)
    (folder / 'index.html').write_text(output, encoding='utf-8')
    return dict(result, report='.runtime/catalog/index.html', tracked_html=False)
