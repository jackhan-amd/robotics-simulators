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
        '각 시뮬레이터 탭에서 모든 env 규모의 처리량·반복 시간·측정 범위·실행 명령·최종 로그를 확인할 수 있습니다. 표의 Chrono DEM 단위는 1 ms AdvanceSimulation 호출이며 단일 내부 물리 substep이 아닙니다. 기존 GPU 기초 측정 50개 구성은 각 탭의 접힌 참고 구획에 유지했습니다. 이 중 MJWarp Humanoid 6개는 본 시험과 중복되므로 구성 수를 합산하지 않습니다.',
        '',
        '[전체 측정 JSON](env-scaling-data.json) · [CSV](env-scaling-data.csv) · [GPU smoke 근거](evidence/gpu-smoke-coverage.json)',
        '',
    ]
    parts = re.split(r'^## (.+)\s*$', text, flags=re.M)
    output = [parts[0]]
    inserted = False
    for heading, content in zip(parts[1::2], parts[2::2]):
        heading = heading.strip()
        if heading in ('제공 예제 envs scaling 추가 시험', '시험 범위와 완료 상태', TITLE):
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

Instinct Sim은 LIBERO 작업의 물리·제어·카메라를 포함한 env.step을 측정했습니다. GSplat은 공유 geometry의 카메라 batch를 측정한 렌더링 항목입니다. 별도로 추진하는 블로그 재현 시험의 학습 시간·정책 추론 지연과 구분합니다.

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
    target.write_bytes(text.encode('utf-8'))
    print('Unified supplied-example summary:', len(groups), 'models;', len(data['measurements']), 'configurations')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir', type=Path, default=ROOT / 'report')
    update(p.parse_args().data_dir)
