2026-10-29에 AMD 공식 블로그를 웹에서 다시 확인했습니다. 공개 성능 자료는 있지만, 이번 제공 예제의 물리 처리량과 모델·단위·계측 범위가 일치하는 비교 수치는 확인하지 못했습니다. 아래 수치를 MI355X의 physics step/s와 나누어 속도 향상 배수로 표시하지 않습니다.

| 자료 | 공개 GPU와 성능 | 이번 측정과의 관계 |
|---|---|---|
| [MuJoCo JAX / XArm7](https://rocm.blogs.amd.com/artificial-intelligence/rocm-jax-mujoco/README.html) | Radeon RX 7900 XTX 실행 사례; num_envs=512 설정 | env 수는 처리량이 아닙니다. Humanoid physics step/s의 비교 기준은 확인하지 못했습니다. |
| [MuJoCo Warp Sim2Real](https://rocm.blogs.amd.com/artificial-intelligence/sim2real-rl-instinct/README.html) | MI300X와 MI355X 단일 GPU의 XArm-6 학습 사례 | 독립 physics step/s를 확인하지 못했습니다. 모델과 제어·학습 경로도 이번 Humanoid와 다릅니다. |
| [Genesis](https://rocm.blogs.amd.com/artificial-intelligence/rocm-genesis/README.html) | Ryzen AI MAX / Vulkan 실행 예제 | 독립 physics FPS를 확인하지 못했습니다. MI355X Franka·SPH 결과와 직접 대조하지 않습니다. |
| [Taichi LLVM 20](https://rocm.blogs.amd.com/artificial-intelligence/taichi_mi300x/README.html) | MI355X 지원과 ray-tracing 예제 출력 76.01607370376587 | 본문 출력에 단위·계측 구간 설명이 충분하지 않아 physics 처리량으로 사용하지 않습니다. 이번 시험은 MPM88입니다. |
| [GSplat](https://rocm.blogs.amd.com/software-tools-optimization/gsplat/README.html) | MI300X; 요약표 7K 학습 158.38 s / 4.81 GB, 30K 학습 888.77 s / 6.89 GB | 학습 시간이며 이번 forward rasterization과 다릅니다. MI355X에서 공식 학습 예제를 별도로 재현합니다. |
| [World Action Models](https://rocm.blogs.amd.com/artificial-intelligence/faster-action-models/README.html) | MI355X; FastWAM 222.55 → 24.17 → 9.59 ms; DiT4DiT/LIBERO 81.47 → 6.49 → 5.65 ms | 각각 baseline, GEAK, GEAK + 2 denoising steps의 정책 결정 지연입니다. 동일 GPU이므로 공개 코드·체크포인트로 별도 재현하며 simulator 처리량과 구분합니다. |

GSplat 글의 요약표는 본문에서 6개 장면 평균이라고 설명하지만 장면별 표에는 Bicycle·Bonsai·Counter·Garden·Kitchen·Room·Stump 7개가 있습니다. 재현 비교는 장면별 값과 제공 benchmark 스크립트를 기준으로 하며, 불분명한 평균은 임의로 다시 계산해 공식 값으로 표시하지 않습니다. Bicycle의 공개 시간은 7K 147.44 s, 30K 1102.74 s입니다. 원래 ROCm 6.4.3 스택과 MI355X에서 실행 가능한 스택의 차이도 기록합니다.

WAM 글의 지연 측정은 MI355X, ROCm 7.14.0, PyTorch 2.11.0 기준입니다. 학습에 사용한 MI325X 여러 개와 W7900 재현 결과는 해당 지연 비교의 GPU가 아닙니다. 성공률은 별도의 closed-loop 평가 지표이므로 짧은 지연 시험만으로 공개 성공률을 재현했다고 주장하지 않습니다. [공식 재현 저장소](https://github.com/AMD-AGI/faster-action-models)는 FastWAM과 CAE-FastWAM 체크포인트 및 지연 도구를 제공합니다. DiT4DiT는 gated Cosmos 모델이 필요하며 CAE-DiT4DiT 체크포인트는 공개되지 않았습니다.

외부 참고로 [nekRS 성능 논문](https://www.frontiersin.org/journals/high-performance-computing/articles/10.3389/fhpcp.2024.1303358/full)은 MI250X 단일 GCD와 V100을 비교합니다. [MuJoCo MJX 문서](https://mujoco.readthedocs.io/en/stable/mjx.html)의 Warp·JAX 예제도 GPU·버전·graph 조건이 달라 직접 비교하지 않습니다. [AMD Simulation 호환성 표](https://rocm.docs.amd.com/projects/simulation/en/latest/about/compatibility-matrix.html)는 공식 지원 범위의 근거로 사용합니다.
