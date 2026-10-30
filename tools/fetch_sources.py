"""Link upstream source dependencies by pinned Git checkout, without vendoring."""
import argparse,json,os,pathlib,re,subprocess,uuid

BASE=pathlib.Path(__file__).resolve().parents[1]

def catalog(path=BASE/'configs/upstream-sources.json'):
    data=json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
    ids=set()
    for source in data['sources']:
        assert re.fullmatch(r'[a-z0-9][a-z0-9-]*',source['id']) and source['id']not in ids
        ids.add(source['id'])
        assert re.fullmatch(r'[a-f0-9]{40}',source['revision'])
        assert source['url'].startswith('https://github.com/') or source['url'].startswith('https://gitlab.com/')
    assert all(set(ids_for_engine)<=ids for ids_for_engine in data['engines'].values())
    return data

def git(*args,cwd=None,capture=False):
    result=subprocess.run(['git',*map(str,args)],cwd=cwd,check=True,timeout=900,
                          stdout=subprocess.PIPE if capture else None,text=True)
    return result.stdout.strip()if capture else None

def verify(source,destination):
    if not(destination/'.git').exists():raise ValueError('Existing directory is not an upstream Git checkout: '+source['id'])
    if git('rev-parse','HEAD',cwd=destination,capture=True)!=source['revision']:
        raise ValueError('Existing checkout has another revision; it was not changed: '+source['id'])
    if git('remote','get-url','origin',cwd=destination,capture=True).rstrip('/').removesuffix('.git')!=source['url'].rstrip('/').removesuffix('.git'):
        raise ValueError('Existing checkout has another origin; it was not changed: '+source['id'])
    if git('status','--porcelain',cwd=destination,capture=True):
        raise ValueError('Existing checkout has local changes; it was not changed: '+source['id'])

def fetch(source,root):
    parent=(pathlib.Path(root).resolve()/'upstream');parent.mkdir(parents=True,exist_ok=True)
    destination=parent/source['id']
    assert destination.resolve().is_relative_to(parent.resolve())
    if destination.exists():verify(source,destination);return destination
    stage=parent/(source['id']+'.partial-'+uuid.uuid4().hex)
    assert stage.resolve().is_relative_to(parent.resolve())
    git('clone','--filter=blob:none','--no-checkout',source['url'],stage)
    git('fetch','--depth=1','origin',source['revision'],cwd=stage)
    git('checkout','--detach',source['revision'],cwd=stage)
    verify(source,stage)
    if destination.exists():raise ValueError('Destination appeared during fetch; staging checkout retained')
    stage.rename(destination)
    return destination

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['list','plan','fetch','verify'])
    p.add_argument('--engine',action='append',help='Engine id; repeat to select several, or use all')
    p.add_argument('--root',type=pathlib.Path,default=pathlib.Path(os.environ.get('STUDY_STORAGE_ROOT',BASE/'.runtime')))
    a=p.parse_args();data=catalog()
    if a.action=='list':print(json.dumps(data,ensure_ascii=False,indent=2));return
    if not a.engine:p.error('Select --engine explicitly; plan/fetch never select every dependency implicitly')
    engines=set(data['engines'])if'all'in a.engine else set(a.engine)
    if not engines<=set(data['engines']):p.error('Unknown engine selection')
    selected={source for engine in engines for source in data['engines'][engine]}
    for source in data['sources']:
        if source['id']not in selected:continue
        destination=a.root.resolve()/'upstream'/source['id']
        if a.action=='fetch':fetch(source,a.root)
        elif a.action=='verify':verify(source,destination)
        print(json.dumps(dict(source=source['id'],url=source['url'],revision=source['revision'],destination=str(destination),action=a.action,license_status=source['license_status']),ensure_ascii=False))

if __name__=='__main__':main()
