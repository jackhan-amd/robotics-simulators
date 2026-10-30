# Genesis World: Rigid와 Fluid

## Upstream source connection

This engine follows the [common upstream dependency convention](../../docs/upstream-dependencies.md).
The project tracks its adapters and pinned source declaration; the upstream engine
is a separate Git checkout in configured local runtime storage.

```bash
python3 tools/fetch_sources.py plan --engine genesis
python3 tools/fetch_sources.py fetch --engine genesis
```

Source checkout is separate from the GPU runtime build and smoke below. The source
directory is a project dependency; it does not indicate a remote compute service.

Explicit `gs.amdgpu`로 강체·관절·접촉, SPH, MPM과 fixed-rigid SPH 경계를 실행한다. Viewer와 renderer를 켜지 않는다.

고정 source는 [Genesis World](https://github.com/Genesis-Embodied-AI/genesis-world)의 `90d55545c193082a8e32f9b1b6b7732f14d89be8`다. 기록한 Python 조합은 Genesis1.4.4, Quadrants1.3.3, Torch2.14.1+rocm7.14다. 전체 목록은 [ROCm lock](../../configs/genesis-rocm-py312.lock.txt)에 있다.

## 설치

[공통 runtime 조건](../README.md#rocm-runtime)의 Python3.12 prefix를 준비한다. Script는 `venvs/genesis-amdgpu`와 고정 source checkout을 준비하고 사용자 디렉터리에 loader alias를 만든다.

```bash
export VERIFIED_GENESIS_AMDGPU_ENV="$EXISTING_GENESIS_PY312_PREFIX"
bash recipes/genesis/install.sh
```

빈 머신의 최신 설치는 [공식 설치 안내](https://genesis-world.readthedocs.io/en/latest/user_guide/overview/installation.html)를 따른다. 그 조합은 위 exact runtime 재현과 별도로 작은 장면을 확인해야 한다.

## 장면과 설정

| Recipe ID | 장면 | 필요한 설정 |
|---|---|---|
| `genesis-freefall` | 구체 낙하·접촉, 50step | explicit AMD backend |
| `genesis-articulation` | 관절 강체, 50step | explicit AMD backend |
| `genesis-contact` | 강체 접촉, 50step | `GS_ENABLE_ZEROCOPY=0`, monolithic contact solve |
| `genesis-sph` | 작은 SPH, 50step | `GS_ENABLE_ZEROCOPY=0`, `--mass-readout static_info` |
| `genesis-mpm` | 작은 MPM, 50step | explicit AMD backend |
| `genesis-coupling` | SPH + fixed rigid boundary, 50step | `GS_ENABLE_ZEROCOPY=0`, `--mass-readout static_info` |

접촉 경로는 `QD_PERFDISPATCH_FORCE=func_solve_body:func_solve_body_monolith`를 사용한다. SPH readout은 고정 source의 `static_info`를 읽는다. Solver/runtime patch를 설치하지 않는다. 각 장면의 particle 수, cell size, dt·substeps는 원본 JSON marker에 기록한다.

## 실행

```bash
python3 -m simulators smoke genesis-freefall --execute
python3 -m simulators smoke genesis-articulation --execute
python3 -m simulators smoke genesis-contact --execute
python3 -m simulators smoke genesis-sph --execute
python3 -m simulators smoke genesis-mpm --execute
python3 -m simulators smoke genesis-coupling --execute
```

한 번에 한 건씩 실행한다. 설정은 manifest가 child에 적용한다. `python3 -m simulators show genesis-contact`로 실제 명령과 환경을 확인할 수 있다.

`quadrants_arch=Arch.amdgpu`, 실제 8060S/gfx1151, profiler의 physics kernel과 각 장면의 수치 gate를 확인한다. Rigid는 낙하·관절·접촉 상태를, Fluid는 particle count·mass·domain·유한 상태와 CPU 기준을 대조한다. Coupling 장면의 rigid boundary는 고정이다.

Apache-2.0. [원본 고지](../../third_party_notices/genesis-world/LICENSE)를 유지한다.
