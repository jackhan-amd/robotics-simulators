# nekRS: HIP Ethier CFD

## Upstream source connection

This engine follows the [common upstream dependency convention](../../docs/upstream-dependencies.md).
The project tracks its adapters and pinned source declaration; the upstream engine
is a separate Git checkout in configured local runtime storage.

```bash
python3 tools/fetch_sources.py plan --engine nekrs
python3 tools/fetch_sources.py fetch --engine nekrs
```

Source checkout is separate from the GPU runtime build and smoke below. The source
directory is a project dependency; it does not indicate a remote compute service.

Build [nekRS](https://github.com/Nek5000/nekRS) commit `96b3cf9e5bacede16568826c04a21bc0fe50dc7d` with HIP enabled and CUDA disabled. The scene uses upstream Ethier with 32 elements, polynomial order 5, dt 0.002 s and 10 steps.

## Build environment

In addition to the [common prerequisites](../README.md), provide an existing Docker daemon and the pinned builder image. The reviewed image ID is:

```bash
docker image inspect sha256:4fa5bc9c24d25ef7e0fe38b23fc5f2b27fc986177bd2f9e496997bcf5af03871
```

This recipe builds and runs sources in an environment that already has this image. It neither downloads the image nor changes daemon storage. The image ID identifies a local artifact, not a public registry download location. Validate the scene separately when using another MPI/HIP builder.

## Build

```bash
bash recipes/nekrs/build.sh
```

Use `OCCA_ENABLE_HIP=ON`, `OCCA_ENABLE_CUDA=OFF`, `OCCA_ENABLE_DPCPP=OFF`, `ENABLE_HYPRE_GPU=OFF`, with ADIOS/CVODE/CPPTRACE OFF. MPI C/C++/Fortran compilers are the image's `mpicc`, `mpicxx` and `mpif77`. Mount sources read-only and build/install directories from runtime storage. Use 2 parallel jobs and a 900-second build limit.

## Run

Use inventory and sysfs to identify the actual 8060S render node.

```bash
export CHECKED_RENDER_NODE="<verified /dev/dri/renderD... path>"
python3 -m simulators smoke nekrs-hip --execute
```

Allow 900 seconds for the wrapper and 880 seconds for the child, including initial JIT. Check that numerical steps 6–10 advance, final time is 0.02 s, velocity L2≤1e-3, pressure L2≤0.1 and scalar L2≤1e-3, and HIP kernels execute. Steps 1–5 alone are insufficient because the upstream UDF resets the analytic field there.

Keep raw logs and JIT caches in private runtime storage. BSD-3-Clause.
