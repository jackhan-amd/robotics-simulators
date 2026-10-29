# nekRS: HIP Ethier CFD

[nekRS](https://github.com/Nek5000/nekRS) commit `96b3cf9e5bacede16568826c04a21bc0fe50dc7d`를 HIP 활성·CUDA 비활성으로 빌드한다. 장면은 upstream Ethier의32요소, polynomial order5, dt0.002초, 10step이다.

## 빌드 환경

[공통 준비](../README.md) 외에 기존 Docker daemon과 고정 builder image가 필요하다. 확인한 image ID는 아래와 같다.

```bash
docker image inspect sha256:4fa5bc9c24d25ef7e0fe38b23fc5f2b27fc986177bd2f9e496997bcf5af03871
```

이 recipe는 해당 image를 이미 보유한 환경의 source build·실행 절차다. Script가 image를 내려받거나 daemon storage를 바꾸지 않는다. Image ID는 로컬 artifact 식별자이며 공개 registry download 주소를 대신하지 않는다. 다른 MPI·HIP builder를 사용하면 별도 장면 확인이 필요하다.

## 빌드

```bash
bash recipes/nekrs/build.sh
```

`OCCA_ENABLE_HIP=ON`, `OCCA_ENABLE_CUDA=OFF`, `OCCA_ENABLE_DPCPP=OFF`, `ENABLE_HYPRE_GPU=OFF`, ADIOS/CVODE/CPPTRACE OFF를 사용한다. MPI C/C++/Fortran compiler는 image 안의 `mpicc`, `mpicxx`, `mpif77`이다. Source는 read-only, build·install은 외장 prefix를 mount한다. 병렬 작업2개, build 예산900초다.

## 실행

Inventory와 sysfs를 보고 8060S의 실제 render node를 지정한다.

```bash
export CHECKED_RENDER_NODE="<확인한 /dev/dri/renderD... 경로>"
python3 -m simulators smoke nekrs-hip --execute
```

처음의 JIT를 포함해 wrapper900초, child880초 예산을 사용한다. 수치6~10step이 실제로 전진하는지, 최종 time0.02초, velocity L2≤1e-3, pressure L2≤0.1, scalar L2≤1e-3과 HIP kernel을 확인한다. Upstream UDF가 analytic field를 재설정하는1~5step만으로 판정하지 않는다.

원본 로그와 JIT cache는 외장 private artifact에 남긴다. BSD-3-Clause.
