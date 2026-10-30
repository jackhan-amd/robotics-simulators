# Licenses for included GPU simulators and dependencies

The repository tooling retains the original [MIT license](LICENSE) and copyright.
Files adapted from upstream projects retain the terms in [license-exceptions.json](configs/license-exceptions.json).
External runtime packages, containers, models and assets retain their own licenses; they are not redistributed here.

| Included component or dependency | License | Original notices |
|---|---|---|
| MuJoCo | Apache-2.0 | [LICENSE](third_party_notices/mujoco/LICENSE) |
| Genesis World | Apache-2.0 | [LICENSE](third_party_notices/genesis-world/LICENSE) |
| Chrono | BSD-3-Clause | [LICENSE](third_party_notices/chrono/LICENSE) |
| incflo | BSD-3-Clause | [LICENSE](third_party_notices/incflo/LICENSE) |
| AMReX | BSD-3-Clause | [LICENSE](third_party_notices/amrex/LICENSE) · [NOTICE](third_party_notices/amrex/NOTICE) |
| AMReX-Hydro | BSD-3-Clause | [LICENSE](third_party_notices/amrex-hydro/LICENSE) |
| Quadrants | Apache-2.0 | [LICENSE](third_party_notices/quadrants/LICENSE) |
| Eigen | MPL-2.0 (Eigen core; other files may have separate licenses) | [COPYING.APACHE](third_party_notices/eigen/COPYING.APACHE) · [COPYING.BSD](third_party_notices/eigen/COPYING.BSD) · [COPYING.GPL](third_party_notices/eigen/COPYING.GPL) · [COPYING.LGPL](third_party_notices/eigen/COPYING.LGPL) · [COPYING.MINPACK](third_party_notices/eigen/COPYING.MINPACK) · [COPYING.MPL2](third_party_notices/eigen/COPYING.MPL2) · [COPYING.README](third_party_notices/eigen/COPYING.README) |
| MuJoCo Warp (optional CUDA reference) | Apache-2.0 | No root license grant found; source not redistributed |
| NVIDIA Warp (MJWarp dependency) | Apache-2.0 | No root license grant found; source not redistributed |
| MJWarp public AMD port | Apache-2.0 | [LICENSE](third_party_notices/mjwarp-public-amd-port/LICENSE) |
| Warp public AMD port | Apache-2.0 | [LICENSE.md](third_party_notices/warp-public-amd-port/LICENSE.md) |
| fluidlab | None | No root license grant found; source not redistributed |
| nekrs | BSD-3-Clause | [LICENSE](third_party_notices/nekrs/LICENSE) |
| taichi-amd | Apache-2.0 | [LICENSE](third_party_notices/taichi-amd/LICENSE) |
| GSplat AMD distribution | Apache-2.0 | [LICENSE](third_party_notices/gsplat-study/LICENSE) |
| Instinct Sim / Faster Action Models | Apache-2.0 | [LICENSE](third_party_notices/instinct-sim-study/LICENSE) · [LICENSE](third_party_notices/instinct-sim-study/simulate/LICENSE) · [NOTICE](third_party_notices/instinct-sim-study/simulate/NOTICE) · [PROVENANCE.md](third_party_notices/instinct-sim-study/simulate/PROVENANCE.md) |
| LIBERO study dependency | MIT | [LICENSE](third_party_notices/libero-study/LICENSE) |

Only the included GPU simulator stack and its dependencies are listed. GSplat is a rendering adjunct; LIBERO supplies the Instinct Sim task/assets.

FluidLab has no explicit root license grant in the pinned source. Its upstream code and contextual patches are not bundled. The common `tools/fetch_sources.py fetch --engine fluidlab` command provides an explicit pinned upstream clone connection. The local integration requires source/runtime supplied with the rights holder’s permission; see [prerequisites](recipes/fluidlab/README.md).

The [license manifest](configs/third-party-licenses.json) records pinned sources, original notice URLs and SHA-256 hashes. Apache notices, BSD conditions, Eigen file-specific terms and upstream attribution are retained verbatim. A source project license does not grant rights to every container component or external asset.
