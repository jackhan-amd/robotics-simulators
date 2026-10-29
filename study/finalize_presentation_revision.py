import json,pathlib,re
B=pathlib.Path(__file__).resolve().parents[1];O=B/'report';f=O/'confluence-report.md';s=f.read_text(encoding='utf-8')
s=re.sub(r'(!\[(실제 실행: [^\]]+)\]\(images/[^)]+\))(?!\n\n실제 실행:)',lambda m:m[1]+'\n\n'+m[2]+' — 성능 측정과 분리한 실제 재실행 캡처.',s)
s=re.sub(r'(실제 실행: [^\n]+ — 성능 측정과 분리한 실제 재실행 캡처\.)\n\n\1',r'\1',s)
start=s.index('## Project Chrono');end=s.index('\n## ',start+1);part=s[start:end]
match=re.search(r'(\| 시험 조건.*?\n\|---.*?\n)((?:\|.*\n)+)',part)
if match and '#### Fluid simulation · FSI-SPH'not in part:
 rows=match[2].splitlines();fsi=[r for r in rows if 'fsi'in r];dem=[r for r in rows if 'dem'in r]
 replacement='#### Fluid simulation · FSI-SPH\n\n'+match[1]+'\n'.join(fsi)+'\n\n#### Rigid / granular simulation · DEM\n\n'+match[1]+'\n'.join(dem)+'\n'
 part=part[:match.start()]+replacement+part[match.end():];s=s[:start]+part+s[end:]
f.write_text(s,encoding='utf-8')
review=json.loads((O/'humanizer-review.json').read_text(encoding='utf-8'));review['presentation_revision']=dict(scope='User-requested structural and factual corrections after the prior prose-review snapshot',changes=['14 target tabs: smoke/performance 13, multi-size scaling 7, single-size performance 6, blocked 1','MuJoCo CPU row moved to validation appendix; title excludes CPU','54 primary performance configurations plus 1 CPU validation reference; raw 55 records unchanged','Third-party illustrative screens removed; actual replay frames with provenance added','General, Rigid, Fluid, Multiphysics, Deformable, Framework and Rendering navigation groups'],prose_review='Reviewed for plain technical language; previous automatic humanizer gate applies to its archived snapshot, not this structural revision.')
(O/'humanizer-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
r=B/'study/REPRODUCE.md';text=r.read_text(encoding='utf-8');text=text.replace('The report package includes selected AMD reference images with `images/provenance.json` and `images/AMD-NOTICE.txt`. They are labeled as reference images.','The report uses actual simulation replay captures in `images/actual-provenance.json` and the actual GSplat smoke image. Replay captures are separate from performance timing. Earlier illustrative reference images were removed from the live report.')
r.write_text(text,encoding='utf-8')
audit=json.loads((O/'evidence/measurement-audit.json').read_text());audit.update(primary_performance_configurations=54,cpu_validation_reference_configurations=1,smoke_and_performance_targets=13,scalability_targets=7,single_size_performance_targets=6,unexecuted_targets=1)
(O/'evidence/measurement-audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
