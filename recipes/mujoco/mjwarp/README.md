# MuJoCo Warp 공개 AMD port

AMD 공개 Warp와 MuJoCo Warp source를 HIP/gfx1151로 빌드한다. NVIDIA Warp 계열의 AMD port이며 vendor-neutral HIP solver로 분류하지 않는다. Native MuJoCo CPU 및 MJX-JAX와 환경을 나눈다.

| Source | 고정 commit |
|---|---|
| [AMD-Ecosystem/warp](https://github.com/AMD-Ecosystem/warp) | `2e2673bb7b90eaabb9cb89dc1f55a76f61c13aab` |
| [AMD-Ecosystem/mujoco_warp](https://github.com/AMD-Ecosystem/mujoco_warp) | `9dfdf7ab8d5a996fe143e9e2c1e5da646c6fc14f` |

## 설치·빌드

[공통 준비](../../README.md#rocm-runtime)의 Python3.12 runtime과 HIP SDK가 필요하다. 기존 dependency prefix를 독립 복사한 뒤 고정 source를 빌드한다.

```bash
export VERIFIED_MJWARP_ROCM_ENV="$EXISTING_MJWARP_PY312_PREFIX"
# ROCM_PATH 또는 VERIFIED_ROCM_BUILD_ENV도 준비한다.
bash recipes/mujoco/mjwarp/build.sh
```

Warp build는 `--hip-arch=gfx1151 --jobs=2 --no-use-libmathdx`를 사용한다. 빌드 예산은300초다. 설치 대상은 해당 venv이며 원본 dependency prefix를 바꾸지 않는다.

## 설정과 실행

실행 manifest의 `HIPRTC_COMPILE_OPTIONS_APPEND`가 unsigned 고정폭 정수 type macro와 `-mprintf-kind=buffered`를 지정한다. Source solver는 수정하지 않는다.

```bash
python3 -m simulators show mujoco-mjwarp-rocm
python3 -m simulators smoke mujoco-mjwarp-rocm --execute
```

작은 강체 장면의 실제 step, 접촉·유한 상태·중력 조건을 확인한다. Wrapper가 HIP runtime과 선택 장치의 provenance를 원본 로그에 남긴다. `backend_observed`와 물리 gate를 함께 검사한다.

공식 경로: [AMD sim-to-real recipe](https://rocm.blogs.amd.com/artificial-intelligence/sim2real-rl-instinct/README.html). Apache-2.0 및 dependency별 고지 유지.
