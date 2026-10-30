# 공통 준비

엔진은 [공통 upstream 연결 방식](../docs/upstream-dependencies.md)으로 고정 commit을 clone합니다. 프로젝트 기본 저장 경로는 Git에서 제외되는 `.runtime/`이며, source 위치와 계산을 실행하는 서버는 별개입니다.

지원 기준은 Linux x86_64와 Python3.12다. C++ 빌드는 CMake·Ninja·C++ compiler가 필요하다. 도구가 없다면 사용자 소유 prefix에 준비한다. 아래 절차는 호스트 driver나 global Python을 변경하지 않는다.

## runtime 저장 경로와 Python

```bash
python3 tools/configure.py --storage-root "$RUNTIME_STORAGE_ROOT" --name simulator
# 출력 예: source '<runtime 저장 경로>/private/environment-simulator.sh'
# 실제 출력한 명령을 실행한다.
```

`uv` 실행 파일과 Python3.12가 필요하다. 이미 있는 Python3.12를 쓸 때는 `PYTHON312`에 그 실행 파일을 지정할 수 있다. `UV_PYTHON_INSTALL_DIR`, cache와 임시 파일은 configure가 지정한 runtime 저장 경로를 사용한다.

| 경로 | 용도 |
|---|---|
| `${STUDY_STORAGE_ROOT}/venvs/<engine>` | 엔진별 Python3.12 환경 |
| `${STUDY_STORAGE_ROOT}/upstream/<engine>` | 고정 source checkout |
| `${STUDY_STORAGE_ROOT}/build`, `install` | 사용자 빌드·설치 |
| `${STUDY_PRIVATE_ROOT}/runs` | 실제 명령·stdout·stderr·source snapshot |
| `${STUDY_PRIVATE_ROOT}/results/runs` | 해당 실행의 JSON |

```bash
python3 tools/collect_inventory.py --node halo \
  --output "$STUDY_PRIVATE_ROOT/inventory.json"
```

Inventory는 연결된 GPU·사용량·메모리·디스크·toolchain을 읽는 사전 점검이다. GPU 시험은 호스트당 하나씩 실행한다. 다른 작업의 서비스를 종료하지 않는다.

<a id="rocm-runtime"></a>
## ROCm runtime

기존 검증 환경은 Torch2.14.1+rocm7.14와 SDK7.14.0을 포함한다. 확인한 공개 PyPI·AMD gfx1151 index에는 이 정확한 조합의 Linux wheel이 없었다. 저장소의 lock은 시험한 의존성 목록이며 wheel을 새로 내려받을 수 있다는 보장은 하지 않는다.

GPU sanity check에 필요한 MuJoCo 패키지는 공개 PyPI에서 준비할 수 있다. 기존 GPU Python 환경을 재현할 때는 엔진별 recipe에 지정한 `VERIFIED_*_ENV`로 사용 허가와 버전이 확인된 Python3.12 prefix를 제공한다. 독립 복사본을 만들며 base 환경은 수정하지 않는다.

```bash
# 예: 기존 Genesis 검증 prefix가 다른 위치에 있을 때
export VERIFIED_GENESIS_AMDGPU_ENV="$EXISTING_GENESIS_PY312_PREFIX"
bash recipes/genesis/install.sh
```

이미 해당 엔진의 `venvs/<engine>/bin/python`이 있으면 설치 스크립트는 그 환경을 사용한다. 복사 후에도 작은 장면의 backend와 수치를 확인한다. 이 경로는 기존 runtime 재현용이며 빈 머신에서 exact GPU wheel을 공개 index로 설치한 검증과 구분한다.

C++ 빌드는 사용자가 준비한 `ROCM_PATH`를 받는다. 지정하지 않으면 기존 Python SDK prefix를 사용한다. SDK가 없을 때는 `VERIFIED_ROCM_BUILD_ENV`가 필요하다.

```bash
# 이미 설치된 HIP SDK의 root를 지정한다.
export ROCM_PATH="$EXISTING_HIP_SDK_ROOT"
"$ROCM_PATH/bin/hipcc" --version
```

새 공개 wheel 조합은 [AMD TheRock releases](https://github.com/ROCm/TheRock/blob/main/RELEASES.md)와 [Python packaging](https://github.com/ROCm/TheRock/blob/main/docs/packaging/python_packaging.md)을 따른다. 조합을 바꾸면 그 버전으로 작은 장면을 다시 확인한다.

## AMD 장치 선택

Inventory의 이름·ISA와 현재 점유를 확인해 선택한다. 여러 GPU가 있으면 번호0을 추정하지 않는다.

```bash
export CHECKED_AMD_DEVICE="<확인한 Radeon8060S selector>"
python3 -m simulators smoke genesis-freefall --execute
```

실행기는 `ROCR_VISIBLE_DEVICES`를 적용하고 child의 logical HIP device0을 사용한다. 장면 코드가 실제 8060S/gfx1151과 요청 backend를 확인한다. GUI renderer는 켜지 않는다.

## Recipe와 결과

각 엔진의 shell 파일은 설치·빌드용이며 명령을 열어 볼 수 있다. `recipes/manifest.json`은 실행 명령·환경 설정·timeout의 원본이다. `smokes/`는 작은 장면과 수치 조건을 포함한다.

프로세스 종료0은 실행 기록 단계다. 새 기록은 `PENDING_VALIDATION`으로 남으며 CPU fallback을 GPU PASS로 바꾸지 않는다. [수치·backend 확인](../docs/verification.md)을 마친 뒤 로컬 기록을 판정한다. 개별 기록과 생성 HTML은 Git에서 제외한다.
