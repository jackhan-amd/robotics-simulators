"""Retain accepted prose edits when measurement tables are regenerated."""
from workspace import REPO_ROOT
import collections,json,pathlib,re
B=REPO_ROOT;file=B/'report/confluence-report.md';before=file.read_text(encoding='utf-8');after=before;applied=0
for rule in json.loads((B/'study/reporting/prose-rules.json').read_text(encoding='utf-8'))['rules']:
 if rule['before']in after:after=after.replace(rule['before'],rule['after']);applied+=1
def protected(text):
 return dict(tables=[x for x in text.splitlines()if x.startswith('|')],headings=re.findall(r'^#{1,6} .+$',text,re.M),code=re.findall(r'```.*?```',text,re.S),inline=re.findall(r'`[^`\n]+`',text),links=re.findall(r'\]\(([^)]+)\)',text),numbers=collections.Counter(re.findall(r'(?<![\w])\d+(?:[.,]\d+)*(?:e[-+]?\d+)?',text,re.I)),markers=re.findall(r'<!--.*?-->',text,re.S))
assert protected(before)==protected(after),'Protected report content changed'
file.write_text(after,encoding='utf-8');print('Reapplied accepted prose edits:',applied)
