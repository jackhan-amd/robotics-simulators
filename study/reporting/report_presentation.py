"""Present accepted supplied-example measurements as one customer-facing list."""
from workspace import REPO_ROOT
import argparse
import collections
import json
from pathlib import Path
import re

ROOT = REPO_ROOT
TITLE = '시험 결과 · 제공 예제와 env scaling'
BADGE = '<span class="amd-mark" style="display:inline-block;background:#000;color:#fff;font-weight:800;padding:2px 9px">AMD</span>'


REPORT_LABELS = {
    "Taichi Lang · AMD 공식 추가": "Taichi Lang",
    "GSplat · AMD 보조 렌더링": "GSplat",
    "제공 예제 envs scaling 추가 시험": "제공 예제 envs scaling 시험",
    "제공 예제 추가 시험": "제공 예제 시험",
    "제공 LIBERO 추가 시험": "제공 LIBERO 시험",
    "전체 실행 이력과 추가 시험 수치는": "최종 측정 수치는",
    "기존 GPU 기초 측정": "참고 GPU 기초 측정",
    "기존 기초 측정": "참고 기초 측정",
    "기존 GPU 기초 측정과 분리한 추가 시험": "제공 모델의 성능 시험",
    "기존 기초 측정의 PASS와 추가 scaling 완료 여부": "기초 모델 측정과 제공 모델 scaling 결과",
    "추가 시험 진행 중": "시험 진행 중",
    "추가 env scaling": "env scaling",
    "추가 scaling": "scaling",
    "보조 GPU 렌더링 항목": "GSplat GPU 렌더링 성능 항목",
    "별도 GPU 렌더링 보조 항목": "GSplat GPU 렌더링 성능 항목",
    "보조 렌더링 항목": "GSplat GPU 렌더링 성능 항목",
    "GPU 렌더링 보조 항목": "GSplat GPU 렌더링 성능 항목"
}

def customer_copy(text):
    """Keep the customer body focused on experiments and inline reproduction."""
    parts=re.split(r'^## (.+)\s*$',text,flags=re.M)
    plan=json.loads((ROOT/'configs/benchmarks/report-plan.json').read_text(encoding='utf-8'))
    engines={e['title']:e for e in plan['engines']}
    output=[parts[0]]
    common="""git clone https://github.com/jackhan-amd/robotics-simulators.git
cd robotics-simulators
export LAB_ROOT="/path/to/benchmark-runtime"
export STUDY_STORAGE_ROOT="$LAB_ROOT/storage"
export STUDY_WORKTREE="$PWD"
export ROCM_PATH="/path/to/matching/rocm-sdk"
mkdir -p "$LAB_ROOT" "$STUDY_STORAGE_ROOT"
python3 -m venv "$LAB_ROOT/bootstrap-tools"
"$LAB_ROOT/bootstrap-tools/bin/pip" install uv
export PATH="$LAB_ROOT/bootstrap-tools/bin:$PATH"
python3 study/run.py bootstrap.py
source "$LAB_ROOT/env.sh"
"$LAB_ROOT/bin/uv" venv --system-site-packages --python "$(command -v python3)" "$STUDY_STORAGE_ROOT/venvs/base"
python3 study/run.py setup_remote.py"""
    requirements={
      'mujoco':'MJWarp용 mujoco=3.8.1·warp=1.13.0+rocm.0 환경과, 별도의 MJX용 JAX/jaxlib/PJRT/plugin=0.12.0·MuJoCo=3.16.0·ROCm 7.14.1 loader 환경을 사용합니다.',
      'genesis':'Genesis 1.4.4의 AMD GPU 환경, 제공 Franka·SPH 예제와 headless 실행용 라이브러리를 준비합니다.',
      'chrono':'고정 Chrono·Eigen source와 gfx950 HIP 빌드를 준비합니다. 제공 DamBreak·DEM 실행 파일은 계측 barrier를 포함한 빌드를 사용합니다.',
      'incflo':'AMReX·AMReX-Hydro·incflo의 고정 source와 gfx950 HIP 실행 파일을 준비합니다. 제공 cavity 입력과 계측 barrier를 사용합니다.',
      'nekrs':'고정 nekRS source, MPI·Fortran 도구와 HIP/OCCA 빌드를 준비합니다. 제공 TGV mesh·입력과 연속 측정 창을 사용합니다.',
      'fluidlab':'고정 FluidLab source와 AMD Taichi 실행 환경을 준비합니다. 로컬 호환성 사본을 사용하며, 제공 MixingEnv의 forward simulation만 실행합니다.',
      'taichi':'공식 AMD Taichi 1.8.0b2의 Python 3.12 payload와 LLVM 20 호환 runtime을 준비합니다. 제공 MPM88 예제를 사용합니다.',
      'instinct':'Faster Action Models의 고정 simulate source, gfx950 빌드, LIBERO 8f1084e source·task asset과 instinct-sim Python 환경을 준비합니다.',
      'gsplat':'AMD GSplat v1.5.3b2의 고정 source와 ROCm PyTorch 환경을 준비합니다. 측정한 Torch 2.14 환경에서는 allocator API 호환성 처리가 필요합니다.'
    }
    preparation={
      'mujoco':['python3 study/run.py install_gpu.py warp','python3 study/run.py prepare_mjx_aligned.py'],
      'genesis':['python3 study/run.py install_gpu.py genesis'],
      'chrono':['python3 study/run.py build_engine.py chrono','python3 study/run.py build_provided_chrono.py'],
      'incflo':['python3 study/run.py build_engine.py incflo','python3 study/run.py prepare_incflo.py','python3 study/run.py build_provided_incflo.py'],
      'nekrs':['python3 study/run.py build_engine.py nekrs'],
      'fluidlab':['export FLUIDLAB_SOURCE_ROOT="$STUDY_STORAGE_ROOT/upstream/fluidlab"','python3 study/run.py prepare_fluidlab.py'],
      'taichi':['python3 study/run.py docker_extract_taichi.py'],
      'instinct':[],
      'gsplat':['python3 study/run.py install_gpu.py gsplat']
    }
    fence=chr(96)*3
    for heading,body in zip(parts[1::2],parts[2::2]):
        heading=heading.strip()
        if re.search(r'Confluence|humanizer|근거.*문장 검토',heading,re.I):continue
        engine=engines.get(heading)
        if engine:
            body=re.sub(r'<!-- PROVIDED-COMMAND -->.*?<!-- /PROVIDED-COMMAND -->\s*','',body,flags=re.S)
            body=re.sub(r'<!-- EXECUTION-GUIDE -->.*?<!-- /EXECUTION-GUIDE -->\s*','',body,flags=re.S)
            eid=engine['id']
            setup=common+'\npython3 tools/fetch_sources.py fetch --engine '+eid
            setup+='\n'+'\n'.join(preparation[eid])
            if eid=='instinct':
                setup+='\n# instinct-sim Python 환경과 LIBERO 의존성 준비 후 GPU backend 빌드\nexport PYTHON="$STUDY_STORAGE_ROOT/venvs/instinct-sim/bin/python"\nexport HIP_ARCH=gfx950 JOBS=8 HIPCXX="$ROCM_PATH/lib/llvm/bin/clang++"\ncd "$STUDY_STORAGE_ROOT/upstream/faster-action-models"\nbash simulate/build.sh libero "$STUDY_STORAGE_ROOT/build/instinct-sim-libero"'
            block=['<!-- EXECUTION-GUIDE -->','#### 실행 안내','',
              'Linux·Python 3.12와 이 절의 Software 버전에 맞는 ROCm SDK·PyTorch runtime을 사용합니다. 장치 점유를 확인한 뒤 할당된 MI355X GPU에서 한 시험 작업씩 실행합니다. 아래 경로는 사용자가 정하는 로컬 작업 경로입니다.',
              '',requirements[eid],'',
              '<details markdown="1"><summary>환경·source 준비 절차</summary>','',fence+'bash',setup,fence,'','</details>','',
              'Runtime 설치·빌드와 task asset 준비를 마친 뒤 다음 명령으로 제공 예제의 smoke와 envs scaling을 실행합니다. 새 환경의 동작은 GPU backend와 장면별 수치 조건으로 확인해야 합니다.',
              '', '<details markdown="1"><summary>Benchmark 재현 명령</summary>','',fence+'bash',engine['command'],fence,'','</details>','',
              '<!-- /EXECUTION-GUIDE -->','']
            body=body.replace('### 3. Throughput','\n'.join(block)+'\n### 3. Throughput',1)
        output.extend(['## '+heading,body])
    text='\n'.join(output)
    text=re.sub(r'^재현 절차:.*$','재현을 위한 환경 준비와 실행 명령은 각 시뮬레이터의 실행 안내에 수록했습니다.',text,flags=re.M)
    return text

def finalize_copy(text):
    """Apply finished-report labels while preserving measurement scope."""
    for old, new in sorted(REPORT_LABELS.items(), key=lambda item: -len(item[0])):
        text = text.replace(old, new)
    text = text.replace('물리 시뮬레이터와 구분한 GSplat GPU 렌더링 성능 항목입니다.',
                        'GSplat의 MI355X GPU 실행 성능을 측정했습니다.')
    text = text.replace('물리 시뮬레이터와 구분한 GPU 렌더링 보조 항목입니다.',
                        'GSplat의 MI355X GPU 실행 성능을 측정했습니다.')
    text = text.replace('별도 policy나 controller를 추가하지 않습니다.',
                        '제공 장면의 실행 경로를 사용하며 별도 policy나 controller는 사용하지 않습니다.')
    note='GSplat의 측정 대상은 forward rasterization의 camera-frames/s입니다. 문서에 포함한 실제 렌더링 화면은 제공 예제의 실행을 설명하는 자료이며, 이미지 저장과 host readback은 처리량 계측에서 제외했습니다. 학습과 backward 성능은 측정하지 않았습니다.'
    parts=re.split(r'(^## GSplat\s*\n)',text,flags=re.M)
    if len(parts)==3 and note not in parts[2]:
        parts[2]=re.sub(r'(### 1\. Simulator 설명\r?\n)',lambda m:m[1]+'\n'+note+'\n',parts[2],count=1)
        text=''.join(parts)
    text=text.replace('GSplat은 GSplat GPU 렌더링 성능 항목', 'GSplat은 GPU 렌더링 성능 시험')
    text=text.replace('별도로 추진하는' + ' 블로그 재현 시험의 학습 시간·정책 추론 지연과 구분합니다.', '학습 시간·정책 추론 지연은 이번 측정 범위에 포함하지 않았습니다.')
    return customer_copy(text)

def update(folder):
    target = folder / 'confluence-report.md'
    text = target.read_bytes().decode('utf-8')
    data = json.loads((folder / 'env-scaling-data.json').read_text(encoding='utf-8'))
    plan = json.loads((folder / 'test-plan.json').read_text(encoding='utf-8'))
    engines = {e['id']: e for e in plan['engines']}
    groups = collections.defaultdict(list)
    for row in data['measurements']:
        groups[(row['engine'], row['model'])].append(row)
    body = [
        'MI355X 1 GPU에서 8개 물리 시뮬레이터와 별도 렌더링 라이브러리 GSplat을 시험했습니다. 아래 목록은 제공 예제의 최종 성능·확장성 시험 64개 구성을 모델별로 통합한 것입니다. 각 구성은 5회 측정했으며, 표에는 측정한 env 규모 중 처리량이 가장 높은 구성의 중앙값을 제시합니다.',
        '',
        '모델·물리 설정은 제공 예제를 유지했습니다. GPU native batch와 독립 GPU 프로세스 복제를 구분하며, GSplat의 envs는 카메라 수입니다. CPU는 같은 장면의 짧은 sanity check에만 사용했습니다. 모델·단위·계측 범위가 다르므로 시뮬레이터 사이의 성능 순위를 나타내지 않습니다.',
        '',
        '| Simulator / backend | 제공 예제 | 측정한 envs | 최대 처리량의 envs | 처리량 중앙값 | 단위 | AMD 코드·자료 기반¹ |',
        '|---|---|---|---:|---:|---|---|',
    ]
    names = {
        'mujoco': 'MuJoCo', 'instinct': 'Instinct Sim', 'genesis': 'Genesis World',
        'chrono': 'Project Chrono', 'incflo': 'AMReX incflo', 'nekrs': 'nekRS',
        'fluidlab': 'FluidLab', 'taichi': 'Taichi Lang', 'gsplat': 'GSplat',
    }
    for engine in engines:
        for (eid, model), rows in groups.items():
            if eid != engine:
                continue
            rows = sorted(rows, key=lambda r: r['envs'])
            peak = max(rows, key=lambda r: r['throughput'])
            backend = (' · MJX-JAX' if 'MJX-JAX' in model else ' · MJWarp') if eid == 'mujoco' else ''
            unit = {'env_step_per_s': 'env-steps/s', 'frames_per_s': 'camera-frames/s',
                    'env_advance_calls_per_s': 'env-advance-calls/s (1 ms)'}[peak['metric']]
            basis = BADGE + (' 공식 튜토리얼 / upstream Genesis' if eid == 'genesis' else ' 공식 GPU 코드') if engines[eid].get('amd_solution') else '—'
            body.append(f"| [{names[eid]}{backend}](#{eid}) | {model} | {', '.join(str(r['envs']) for r in rows)} | {peak['envs']:,} | {peak['throughput']:,.3f} | {unit} | {basis} |")
    body += ['',
        '¹ 검은 AMD 블록은 AMD 공식 블로그·문서에서 소개하고 공개한 GPU 코드 또는 튜토리얼을 근간으로 시험했다는 뜻입니다. MuJoCo는 AMD의 MJWarp·ROCm JAX, Instinct Sim은 AMD-AGI, Taichi·GSplat은 AMD 배포 코드를 사용했습니다. Genesis는 AMD 공식 튜토리얼에서 소개한 upstream 프로젝트이며 AMD가 개발한 엔진이라는 뜻은 아닙니다. 해당 탭의 AMD 소개·저장소 링크에서 근거를 확인할 수 있습니다. 이 표시는 MI355X 공식 인증을 뜻하지 않습니다. Genesis 글은 Ryzen AI MAX/Vulkan, GSplat의 공식 GPU 목록은 MI300X·MI325X 기준입니다.',
        '',
        '각 시뮬레이터 탭에서 모든 env 규모의 처리량·반복 시간·측정 범위·실행 명령·최종 로그를 확인할 수 있습니다. 표의 Chrono DEM 단위는 1 ms AdvanceSimulation 호출이며 단일 내부 물리 substep이 아닙니다. 참고 GPU 기초 측정 50개 구성은 각 탭의 접힌 참고 구획에 유지했습니다. 이 중 MJWarp Humanoid 6개는 본 시험과 중복되므로 구성 수를 합산하지 않습니다.',
        '',
        '[전체 측정 JSON](env-scaling-data.json) · [CSV](env-scaling-data.csv) · [GPU smoke 근거](evidence/gpu-smoke-coverage.json)',
        '',
    ]
    parts = re.split(r'^## (.+)\s*$', text, flags=re.M)
    output = [parts[0]]
    inserted = False
    for heading, content in zip(parts[1::2], parts[2::2]):
        heading = heading.strip()
        if heading in ('제공 예제 envs scaling 시험', '시험 범위와 완료 상태', TITLE):
            if not inserted:
                output.extend(['## ' + TITLE, '\n\n' + '\n'.join(body)])
                inserted = True
            continue
        if heading == '고객 설명에 사용할 시연 순서':
            heading = '실험 개요'
            content = '''

본 시험은 MI355X 한 개에서 제공 예제의 동작과 env 규모에 따른 처리량을 확인하는 데 목적이 있습니다. 설치 확인, bounded smoke, 성능 측정, env scaling 순서로 진행했습니다. 수치와 재현 절차는 시뮬레이터별 탭에 정리했습니다.

MuJoCo는 같은 Humanoid XML을 MJWarp와 MJX-JAX로 실행했습니다. 두 backend의 버전과 실행 방식은 별도로 기록했습니다. 제어 입력은 0이며 학습된 보행 정책의 성능을 평가한 결과는 아닙니다. Genesis는 Franka native batch와 SPH–강체 결합 예제의 독립 GPU 프로세스 복제를 측정했습니다.

Chrono의 DamBreak·DEM, incflo의 cavity, nekRS의 TGV는 모델의 입자·격자 규모와 시간 간격, 측정 구간을 함께 기록했습니다. DEM은 초기 1 ms 구간이며 nekRS의 다섯 표본은 연속 궤적의 측정 창입니다. FluidLab은 MixingEnv, Taichi는 MPM88 제공 예제를 사용했습니다.

Instinct Sim은 LIBERO 작업의 물리·제어·카메라를 포함한 env.step을 측정했습니다. GSplat은 공유 geometry의 카메라 batch를 측정한 렌더링 항목입니다. 학습 시간·정책 추론 지연은 이번 측정 범위에 포함하지 않았습니다.

각 구성은 GPU 동기화 후 5회 계측했습니다. 캡처·시각화는 별도 실행했으며 측정 시간에 포함하지 않았습니다. 그림은 실제 실행에서 저장한 화면 또는 실제 수치의 후처리 시각화입니다. CPU는 같은 장면의 짧은 GPU sanity check에만 사용했습니다.

'''
        output.extend(['## ' + heading, content])
    text = '\n'.join(output)
    # Remove redundant execution-status columns, retaining the evidence links.
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if not line.startswith('|'):
            continue
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if '실행' not in cells:
            continue
        index = cells.index('실행')
        j = i
        while j < len(lines) and lines[j].startswith('|'):
            row = [cell.strip() for cell in lines[j].strip().strip('|').split('|')]
            assert len(row) == len(cells), (i, j)
            row.pop(index)
            lines[j] = '| ' + ' | '.join(row) + ' |\n'
            j += 1
    text = ''.join(lines)
    research = ROOT / 'docs/reference-performance.md'
    if research.exists():
        text = re.sub(r'(## 외부 공개 성능과 AMD 확인 범위\n).*?(?=\n## |\Z)',
                      lambda m: m[1] + '\n' + research.read_text(encoding='utf-8') + '\n', text, flags=re.S)
    target.write_bytes(finalize_copy(text).encode('utf-8'))
    print('Unified supplied-example summary:', len(groups), 'models;', len(data['measurements']), 'configurations')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir', type=Path, default=ROOT / 'report')
    update(p.parse_args().data_dir)
