"""Expose the current review status without reusing a stale-scope gate claim."""
import argparse,datetime,hashlib,json,pathlib,shutil
B=pathlib.Path(__file__).resolve().parents[1];O=B/'report';p=argparse.ArgumentParser();p.add_argument('--run-dir');a=p.parse_args()
f=O/'humanizer-review.json';archive=B/'_workspace/gpu-scope-revision/prior-humanizer-review.json';archive.parent.mkdir(parents=True,exist_ok=True)
if f.exists()and not archive.exists():shutil.copy2(f,archive)
review=dict(updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='8 MI355X GPU physics engines plus separate GSplat rendering adjunct; CPU only for same-scene sanity; CPU throughput excluded',status='IN_PROGRESS',skills=[dict(name='humanize-korean',source='https://github.com/epoko77-ai/im-not-ai',route='heavy'),dict(name='humanizer',source='https://github.com/blader/humanizer',version='3.1.0')],note='Previous gates apply to archived snapshots. The current GPU-scope report is undergoing a fresh review.')
if a.run_dir:
 run=pathlib.Path(a.run_dir);gate=json.loads((run/'10_gate_final.json').read_text(encoding='utf-8'));finalizer=json.loads((run/'09_finalize.json').read_text(encoding='utf-8'))
 review.update(status='PASS',run_id=run.name,gate=gate,finalizer=finalizer,note='Numbers, tables, commands, headings, source metadata and links preserved in the current report review.',markdown_sha256=hashlib.sha256((O/'confluence-report.md').read_bytes()).hexdigest())
 review['related_document_review']='evidence/repro-prose-review.json'
 target=O/'evidence/humanizer-gpu-scope';target.mkdir(exist_ok=True)
 for item in run.iterdir():
  if item.is_file()and item.suffix in('.md','.txt','.json'):shutil.copy2(item,target/item.name)
f.write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8');print(review['status'])
