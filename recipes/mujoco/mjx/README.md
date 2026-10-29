# MuJoCo MJX-JAX ROCm

MuJoCo scene을 MJX-JAX로 실행하는 ROCm 경로다. 기존 확인 조합은 JAX/JAXlib0.12.0, ROCm plugin/PJRT0.11.2이며 [의존성 목록](../../../configs/mujoco-mjx-rocm-py312.lock.txt)에 고정했다.

## 환경 준비

[공통 ROCm runtime 조건](../../README.md#rocm-runtime)을 따른다. 별도 `venvs/mujoco-mjx-rocm`을 사용하며 Genesis/Torch 환경과 섞지 않는다.

```bash
export VERIFIED_MUJOCO_MJX_ROCM_ENV="$EXISTING_MJX_PY312_PREFIX"
bash recipes/mujoco/mjx/install.sh
```

기존 기록과 같은 loader library가 필요하다. 실행 manifest가 `compat/rocm7.14`와 기존 SDK library 경로를 지정한다. 해당 library를 준비한 Genesis/SDK prefix는 공통 runtime 조건에 포함된다.

## 설정과 실행

실행기는 `JAX_PLATFORMS=rocm`, `XLA_PYTHON_CLIENT_PREALLOCATE=false`와 확인한 AMD selector를 설정한다.

```bash
python3 -m simulators show mujoco-mjx-rocm
python3 -m simulators smoke mujoco-mjx-rocm --execute
```

낙하·접촉 장면의 유한 상태, 중력 기준과 접촉 gate를 검사한다. JAX device가 ROCm GPU인지 확인하고 CPU로 실행되면 CPU 기준 결과로 분류한다. 새 프로세스의 JIT 준비와 실제 step 실행을 구분한다.

공식 자료: [MJX](https://mujoco.readthedocs.io/en/stable/mjx.html), [ROCm JAX](https://rocm.docs.amd.com/projects/jax/en/latest/). Apache-2.0.
