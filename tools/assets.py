#!/usr/bin/env python3
"""Pinned external assets. No payloads, credentials or local receipts belong in Git."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import time
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen
import uuid

BASE = Path(__file__).resolve().parents[1]


def relative(value):
    p = PurePosixPath(value)
    if p.is_absolute() or not p.parts or any(x in ('..', '.', '.git') for x in p.parts):
        raise ValueError('Unsafe asset-relative path')
    return p


def read_manifest(path):
    data = json.loads(Path(path).read_text())
    seen = set()
    for item in data['assets']:
        if item['id'] in seen or not re.fullmatch(r'[a-z0-9][a-z0-9_-]*', item['id']):
            raise ValueError('Duplicate or invalid asset ID')
        seen.add(item['id'])
        relative(item['destination'])
        if item['kind'] not in ('file', 'git', 'huggingface', 'container'):
            raise ValueError('Unknown asset provider')
        if item['kind'] in ('git', 'huggingface') and not re.fullmatch('[a-f0-9]{40}', item['revision']):
            raise ValueError('Full immutable source revision required')
        for spec in item.get('files', []):
            relative(spec['path'])
            if not re.fullmatch('[a-f0-9]{64}', spec.get('sha256', '')) and not re.fullmatch('[a-f0-9]{40}', spec.get('git_blob_sha1', '')):
                raise ValueError('Expected file checksum required')
        if item['kind'] == 'file' and not re.fullmatch('[a-f0-9]{64}', item.get('sha256', '')):
            raise ValueError('Expected SHA256 required')
        for url in [item.get('url', ''), item.get('license_url', '')]:
            if url and (urlsplit(url).scheme != 'https' or urlsplit(url).username):
                raise ValueError('Public HTTPS asset URLs required')
    return data


def asset_path(root, destination):
    root = Path(root).resolve()
    path = root / str(relative(destination))
    # Existing links may point into another subtree of this approved volume.
    if not path.resolve().is_relative_to(root):
        raise ValueError('Asset destination escapes external storage')
    return path


def digest(path, algorithm='sha256', git_blob=False):
    h = hashlib.new(algorithm)
    if git_blob:
        h.update(b'blob ' + str(path.stat().st_size).encode() + b'\0')
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def verify_file(path, spec):
    if not path.is_file():
        return False
    if spec.get('bytes') is not None and path.stat().st_size != spec['bytes']:
        return False
    if spec.get('sha256'):
        return digest(path) == spec['sha256']
    return digest(path, 'sha1', True) == spec['git_blob_sha1']


def status(item, root):
    path = asset_path(root, item['destination'])
    if (path / 'COLD_STORAGE.json').is_file() or any((p / 'COLD_STORAGE.json').is_file() for p in path.parents if p.is_relative_to(Path(root).resolve())):
        return 'COLD_ARCHIVE'
    if item['kind'] == 'file':
        return 'VERIFIED' if verify_file(path, item) else 'MISSING' if not path.exists() else 'CHECKSUM_MISMATCH'
    if item['kind'] == 'git':
        if not (path / '.git').exists():
            return 'MISSING'
        r = subprocess.run(['git', '-C', str(path), 'rev-parse', 'HEAD'], capture_output=True, text=True, timeout=30)
        return 'VERIFIED' if r.returncode == 0 and r.stdout.strip() == item['revision'] else 'REVISION_MISMATCH'
    if item['kind'] == 'container':
        r = subprocess.run(['docker', 'image', 'inspect', item['image']], capture_output=True, text=True, timeout=30)
        return 'AVAILABLE_EXTERNALLY' if r.returncode == 0 else 'MISSING'
    return 'VERIFIED' if item.get('files') and all(verify_file(path / f['path'], f) for f in item['files']) else 'MISSING_OR_INCOMPLETE'


def download(url, path, spec, deadline):
    if path.exists():
        if verify_file(path, spec):
            return
        raise ValueError('Refusing to overwrite an existing asset with a different checksum')
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + '.partial-' + uuid.uuid4().hex)
    with urlopen(Request(url, headers={'User-Agent': 'robotics-asset-manager/1'}), timeout=60) as response, partial.open('xb') as out:
        while True:
            if time.monotonic() > deadline:
                raise TimeoutError('Asset download budget exceeded; partial file retained')
            data = response.read(4 * 1024 * 1024)
            if not data:
                break
            out.write(data)
    if not verify_file(partial, spec):
        raise ValueError('Downloaded checksum mismatch; partial file retained')
    partial.rename(path)


def fetch(item, root, budget=1800, accept=False):
    if item['license_status'] != 'verified':
        if item['license_status'] != 'restricted' or not accept:
            raise ValueError('LICENSE_REVIEW_REQUIRED: ' + item['id'])
    path = asset_path(root, item['destination'])
    if status(item, root) in ('VERIFIED', 'AVAILABLE_EXTERNALLY'):
        return
    estimate = item.get('bytes') or sum(f.get('bytes', 0) for f in item.get('files', []))
    root.mkdir(parents=True, exist_ok=True)
    if estimate and shutil.disk_usage(root).free < estimate + 2 * 1024**3:
        raise ValueError('Insufficient external storage for this asset')
    deadline = time.monotonic() + budget
    if item['kind'] == 'container':
        raise ValueError('Prepare the fixed image in operator-managed Docker storage; this tool does not change Docker or pull large images')
    if item['kind'] == 'file':
        download(item['url'], path, item, deadline)
    elif item['kind'] == 'git':
        if path.exists():
            raise ValueError('Existing source has a different revision; use a separate destination')
        path.parent.mkdir(parents=True, exist_ok=True)
        stage = path.with_name(path.name + '.partial-' + uuid.uuid4().hex)
        subprocess.run(['git', 'clone', '--filter=blob:none', '--no-checkout', item['url'], str(stage)], check=True, timeout=budget)
        subprocess.run(['git', '-C', str(stage), 'fetch', '--depth=1', 'origin', item['revision']], check=True, timeout=max(1, deadline-time.monotonic()))
        subprocess.run(['git', '-C', str(stage), 'checkout', '--detach', item['revision']], check=True, timeout=max(1, deadline-time.monotonic()))
        stage.rename(path)
    else:
        prefix = 'https://huggingface.co/' + ('datasets/' if item.get('repo_type') == 'dataset' else '') + item['repo_id'] + '/resolve/' + item['revision'] + '/'
        if not item.get('files'):
            raise ValueError('Pinned file inventory is missing')
        for spec in item['files']:
            download(prefix + quote(spec['path'], safe='/'), path / spec['path'], spec, deadline)
    observed = status(item, root)
    if observed != 'VERIFIED':
        raise ValueError('Post-download verification failed: ' + observed)
    receipt = root / 'private' / 'asset-receipts' / (item['id'] + '.json')
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({'id': item['id'], 'revision': item.get('revision'), 'verified': True, 'license': item.get('license'), 'license_url': item.get('license_url')}, indent=2)+'\n')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, default=BASE/'assets/manifest.json')
    p.add_argument('--root', type=Path, default=os.environ.get('STUDY_STORAGE_ROOT'))
    p.add_argument('action', choices=('list', 'check', 'plan', 'fetch', 'verify'))
    p.add_argument('ids', nargs='*')
    p.add_argument('--budget', type=int, default=1800)
    p.add_argument('--accept-restricted-license', action='store_true')
    a = p.parse_args(argv)
    try:
        data = read_manifest(a.manifest)
        selected = [x for x in data['assets'] if not a.ids or x['id'] in a.ids]
        if set(a.ids) - {x['id'] for x in selected}:
            raise ValueError('Unknown asset ID')
        if a.action == 'check':
            print(json.dumps({'valid': True, 'assets': len(data['assets'])}));return 0
        if a.action in ('fetch', 'verify') and a.root is None:
            raise ValueError('Set the authorized external STUDY_STORAGE_ROOT')
        if not 1 <= a.budget <= 7200:
            raise ValueError('Use a finite 1..7200 second asset budget')
        if a.action == 'fetch' and not a.ids:
            raise ValueError('Select explicit asset IDs; no implicit bulk downloads')
        rows=[]
        for x in selected:
            if a.action == 'fetch':fetch(x, a.root, a.budget, a.accept_restricted_license)
            row={k:x.get(k) for k in ['id','kind','license','license_status','destination','bytes']}
            if a.action in ('verify','fetch'):row['status']=status(x,a.root)
            rows.append(row)
        print(json.dumps(rows,indent=2))
        return 3 if a.action=='verify' and any(x['status'] not in ('VERIFIED','AVAILABLE_EXTERNALLY')for x in rows) else 0
    except (ValueError,OSError,subprocess.SubprocessError) as e:
        print(type(e).__name__+': '+str(e),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
