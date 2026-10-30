"""Publish only retained frames from an actual GPU replay/render."""
from workspace import REPO_ROOT
import hashlib,json,pathlib,re,shutil,sys,tempfile
from publication import repository_reference
B=REPO_ROOT;O=B/'report';E=O/'evidence/results';images=O/'images';f=O/'confluence-report.md';s=f.read_text(encoding='utf-8');entries=[]
extras={};garden_caption='제공된 `assets/test_garden.npz`와 공식 helper를 사용해 MI355X에서 렌더링한 실제 출력이다. 좌표·색상은 제공 자산이며 scale·회전·opacity는 helper 초기화값이다. 학습된 checkpoint의 화질을 나타내지 않는다.'
garden=E/'gsplat-provided-garden.png'
if garden.exists():
 shutil.copy2(garden,images/garden.name);s=re.sub(r'!\[[^\]]*\]\(images/gsplat-synthetic.png\)',f'![제공 garden fixture의 실제 MI355X GPU 렌더링](images/{garden.name})',s)
 s=s.replace('이번 MI355X smoke 실행에서 생성한 합성 Gaussian 구름의 화면.','제공된 `assets/test_garden.npz`와 공식 helper를 사용해 MI355X에서 렌더링한 실제 출력이다. 좌표·색상은 제공 자산이며 scale·회전·opacity는 helper 초기화값이다. 학습된 checkpoint의 화질을 나타내지 않는다.')
 entries.append(dict(file=garden.name,sha256=hashlib.sha256(garden.read_bytes()).hexdigest(),source='provided GSplat garden smoke',evidence='raw GPU rendering saved by provided_gsplat_garden.py; supplied fixture/helper, no trained checkpoint'))
 extras['GSplat · AMD 보조 렌더링']=[f'![제공 garden fixture의 실제 MI355X GPU 렌더링](images/{garden.name})','',garden_caption,'']
libero=E/'instinct-provided-libero.png'
if libero.exists():
 shutil.copy2(libero,images/libero.name);extras['Instinct Sim · Faster Action Models backend']=[f'![실제 LIBERO task 0 GPU 카메라 관측](images/{libero.name})','','제공 LIBERO spatial task 0의 실제 GPU 카메라 관측이다. smoke의 20회 env.step 뒤에 저장한 원본 관측이며, 저장은 측정 구간에서 제외했다.',''];entries.append(dict(file=libero.name,sha256=hashlib.sha256(libero.read_bytes()).hexdigest(),source='provided LIBERO task 0 GPU smoke, original agentview_image'))
sys.path.insert(0,str(pathlib.Path(tempfile.gettempdir())/'robotics-study-plot-deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt,numpy as np
field=E/'incflo-provided-cavity-field.npz';receipt=E/'incflo-provided-field-capture.json'
if field.exists()and receipt.exists():
 meta=json.loads(receipt.read_text());assert meta['physics_valid'];d=np.load(field);u=d['velx'];v=d['vely'];speed=np.sqrt(u*u+v*v);t=float(d['simulation_time']);xy=(np.arange(128)+.5)/128;fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained');im=axes[0].imshow(speed,origin='lower',extent=(0,1,0,1),cmap='viridis');fig.colorbar(im,ax=axes[0],label='speed (simulation units)');axes[0].set_title('Actual HIP velocity field');axes[1].streamplot(xy,xy,u,v,density=1.4,color=speed,cmap='viridis');axes[1].set_title('Streamlines from recorded velocity')
 for ax in axes:ax.set(xlabel='x',ylabel='y',xlim=(0,1),ylim=(0,1));ax.set_aspect('equal')
 fig.suptitle(f'Supplied cavity | 50 steps | t={t:.6f}');name='incflo-provided-actual-field.png';fig.savefig(images/name,dpi=160);plt.close(fig)
 extras['AMReX incflo']=[f'![실제 incflo GPU 계산 결과의 유동장](images/{name})','',f'실제 HIP 계산에서 저장한 128×128 field를 후처리했다. 제공 cavity의 50 step 뒤 t={t:.9f} 상태이며, 후처리와 그림 저장은 성능 측정에서 제외했다.',''];entries.append(dict(file=name,source_run_id=meta['source_run_id'],source_npz=field.name,source_npz_sha256=hashlib.sha256(field.read_bytes()).hexdigest(),render='Matplotlib postprocessing of actual GPU output; not a GUI screenshot'))
particles=E/'fluidlab-provided-particles.npz';receipt=E/'fluidlab-provided-capture.json'
if particles.exists()and receipt.exists():
 meta=json.loads(receipt.read_text());assert meta['physics_valid'];d=np.load(particles);x=d['x'];v=d['v'];stride=5;fig=plt.figure(figsize=(7,5.5));ax=fig.add_subplot(projection='3d');color=np.linalg.norm(v[::stride],axis=1);plot=ax.scatter(x[::stride,0],x[::stride,2],x[::stride,1],c=color,s=1,cmap='viridis',rasterized=True);ax.set(xlabel='x',ylabel='z',zlabel='y (vertical)',title=f'Actual HIP MixingEnv particle state | {len(x):,} particles | 100 steps');fig.colorbar(plot,ax=ax,shrink=.6,label='speed (simulation units)');fig.tight_layout();name='fluidlab-provided-actual-particles.png';fig.savefig(images/name,dpi=160);plt.close(fig)
 extras['FluidLab']=[f'![실제 MixingEnv GPU 입자 좌표](images/{name})','','제공 MixingEnv의 실제 GPU 입자 좌표를 100 env.step 뒤에 저장해 시각화했다. 화면에는 전체 입자의 5개 중 1개를 표시했고, 원본 전체 좌표·속도를 보존했다. 데이터 저장과 시각화는 성능 측정에서 제외했다.',''];entries.append(dict(file=name,source_npz=particles.name,source_npz_sha256=hashlib.sha256(particles.read_bytes()).hexdigest(),render='Matplotlib visualization of actual GPU particle coordinates, every fifth point; not a GUI screenshot'))
parts=re.split(r'^## (.+)\s*$',s,flags=re.M);out=[parts[0]]
for title,body in zip(parts[1::2],parts[2::2]):
 if title in extras:
  body=re.sub(r'<!-- PROVIDED-CAPTURES -->.*?<!-- /PROVIDED-CAPTURES -->\s*','',body,flags=re.S)
  if title=='GSplat · AMD 보조 렌더링':body=re.sub(r'!\[[^\]]*\]\(images/gsplat-provided-garden.png\)','',body).replace(garden_caption,'')
  body+='\n<!-- PROVIDED-CAPTURES -->\n#### 실제 제공 예제 결과\n\n'+'\n'.join(extras[title])+'\n<!-- /PROVIDED-CAPTURES -->\n'
 if title=='Genesis World':
  new=[]
  for case in('franka','sph'):
   meta=E/f'genesis-provided-{case}-capture.json'
   if not meta.exists():continue
   receipt=json.loads(meta.read_text(encoding='utf-8'))
   receipt['source']=repository_reference(receipt['source'])
   if not receipt.get('physics_valid'):continue
   for frame in receipt['frames']:
    src=E/frame['file']
    if not src.exists():continue
    shutil.copy2(src,images/src.name);new+=[f"![제공 {case} 실제 GPU replay · step {frame['step']}](images/{src.name})",'',f"제공 `{receipt['source']}`의 GPU replay에서 step {frame['step']}에 캡처했다. 카메라 렌더링과 캡처는 성능 측정에서 제외했다.",''];entries.append(dict(**frame,source=receipt['source'],source_sha256=receipt['source_sha256'],receipt=meta.name,sha256=hashlib.sha256(src.read_bytes()).hexdigest()))
  if new:
   body=re.sub(r'<!-- PROVIDED-CAPTURES -->.*?<!-- /PROVIDED-CAPTURES -->\s*','',body,flags=re.S)
   body+='\n<!-- PROVIDED-CAPTURES -->\n#### 제공 예제 실제 실행 화면\n\n'+'\n'.join(new)+'\n<!-- /PROVIDED-CAPTURES -->\n'
 out+=['## '+title,body]
f.write_text('\n'.join(out),encoding='utf-8');(images/'provided-provenance.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8');print('Published actual provided-example frames:',len(entries))
