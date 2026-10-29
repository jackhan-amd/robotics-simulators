"""Capture the local report in a separate headless Edge profile for layout QA."""
import pathlib,subprocess,tempfile
B=pathlib.Path(__file__).resolve().parents[1];O=B/'report/evidence/layout';O.mkdir(exist_ok=True)
edge=pathlib.Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')
url=(B/'report/mi355x-simulator-report.html').as_uri()
for name,fragment,size in [('mujoco','#mujoco','1600,1200'),('overview','','1440,1000'),('env-scaling','#env-scaling','1600,1200'),('mobile','#mujoco','600,1000')]:
 with tempfile.TemporaryDirectory(prefix='robotics-report-edge-')as profile:
  cmd=[str(edge),'--headless','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-extensions','--user-data-dir='+profile,'--screenshot='+str(O/(name+'.png')),'--window-size='+size,'--virtual-time-budget=2000',url+fragment]
  c=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
  (O/(name+'.log')).write_text(c.stdout+c.stderr,encoding='utf-8')
  assert c.returncode==0 and (O/(name+'.png')).is_file(),name
print('Captured desktop and mobile previews')
