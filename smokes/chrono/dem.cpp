// SPDX-License-Identifier: BSD-3-Clause
// Adapted API/example patterns from Project Chrono Development Team. Study-specific geometry, validation and integration changes.
// Procedural small DEM adaptation of Chrono demo_DEM_movingBoundary setup.
// Upstream: Project Chrono, BSD-3-Clause (see third_party_notices).
#include <algorithm>
#include <cstdlib>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <vector>
#include "chrono_dem/physics/ChSystemDem.h"
#include "chrono/gpu/ChGpuRuntime.h"
using namespace chrono;
using namespace chrono::dem;
int main(int argc, char** argv) {
    int steps = argc > 1 ? std::stoi(argv[1]) : 10;
    if (steps != 10 && steps != 50) return 2;
    int device = -1;
    gpuDeviceProp prop{};
    if (gpuGetDevice(&device) != gpuSuccess || gpuGetDeviceProperties(&prop, device) != gpuSuccess) return 4;
#ifdef CHRONO_USE_HIP
    const char* backend = "hip";
    const char* expected = std::getenv("STUDY_AMD_ARCH");
    if (std::string(prop.gcnArchName).substr(0, std::string(prop.gcnArchName).find(":")) != (expected ? expected : "gfx1151")) return 5;
#else
    const char* backend = "cuda";
    if (prop.major != 8 || prop.minor != 6 || std::string(prop.name).find("3090") == std::string::npos) return 5;
#endif
    std::cout << "SMOKE_DEVICE: " << prop.name << std::endl;
    // User units are chosen as cm, g, s; distinct from the FSI scene's SI units.
    const float dt = 1e-4f;
    ChSystemDem dem(0.1f, 2.5f, ChVector3f(10, 10, 10));
    dem.SetBDFixed(true);
    dem.SetPsiFactors(32, 16);
    dem.SetKn_SPH2SPH(1e5);
    dem.SetKn_SPH2WALL(1e5);
    dem.SetGn_SPH2SPH(10);
    dem.SetGn_SPH2WALL(10);
    dem.SetFrictionMode(CHDEM_FRICTION_MODE::FRICTIONLESS);
    dem.SetTimeIntegrator(CHDEM_TIME_INTEGRATOR::FORWARD_EULER);
    dem.SetFixedStepSize(dt);
    dem.SetGravitationalAcceleration(ChVector3f(0, 0, -980));
    std::vector<ChVector3f> points;
    for (int x = -1; x <= 1; ++x)
        for (int y = -1; y <= 1; ++y)
            for (int z = -1; z <= 1; ++z) points.emplace_back(x * 0.3f, y * 0.3f, 2 + z * 0.3f);
    dem.SetParticles(points);
    dem.Initialize();
    gpuDeviceSynchronize();
    const auto count = dem.GetNumParticles();
    double z0 = 0;
    for (size_t i = 0; i < count; ++i) z0 += dem.GetParticlePosition(i).z() / count;
    bool finite = true, bounds = true;
    double max_com_error = 0, max_vz_error = 0;
    for (int n = 1; n <= steps; ++n) {
        double advanced=dem.AdvanceSimulation(dt);
        if (std::getenv("STUDY_DEM_DIAGNOSTICS") && (n==1 || n==steps)) {
            std::cout << "DEM_DIAGNOSTIC: step=" << n << " advanced=" << advanced << " sim_time=" << dem.GetSimTime() << " vz=" << dem.GetParticleVelocity(0).z() << " az=" << dem.GetParticleLinAcc(0).z() << " z=" << dem.GetParticlePosition(0).z() << std::endl;
        }
        if (gpuDeviceSynchronize() != gpuSuccess) return 7;
        double com = 0;
        for (size_t i = 0; i < count; ++i) {
            auto p = dem.GetParticlePosition(i);
            auto v = dem.GetParticleVelocity(i);
            finite = finite && std::isfinite(p.x()) && std::isfinite(p.y()) && std::isfinite(p.z()) && std::isfinite(v.Length());
            bounds = bounds && std::abs(p.x()) <= 4.9 && std::abs(p.y()) <= 4.9 && std::abs(p.z()) <= 4.9;
            com += p.z() / count;
            max_vz_error = std::max(max_vz_error, std::abs(v.z() + 980.0 * n * dt));
        }
        max_com_error = std::max(max_com_error, std::abs(com - (z0 - 490.0 * n * n * dt * dt)));
    }
    bool conserved = count == 27 && dem.GetNumParticles() == count;
    bool valid = finite && bounds && conserved && max_com_error <= 0.002 && max_vz_error <= 0.2;
    std::cout << std::boolalpha << std::setprecision(12)
              << "SMOKE_RESULT_JSON:{\"backend_observed\":\"" << backend << "\",\"physics_valid\":" << valid
              << ",\"steps\":" << steps << ",\"dt\":" << dt << ",\"particles\":" << count
              << ",\"radius_cm\":0.1,\"density_g_cm3\":2.5,\"gravity_cm_s2\":-980,\"g2_qualified\":false"
              << ",\"gates\":{\"finite\":" << finite << ",\"bounds\":" << bounds << ",\"particle_count\":" << conserved
              << ",\"com\":" << (max_com_error <= 0.002) << ",\"velocity\":" << (max_vz_error <= 0.2)
              << "},\"metrics\":{\"max_com_error_cm\":" << max_com_error << ",\"max_vz_error_cm_s\":" << max_vz_error << "}}" << std::endl;
    return valid ? 0 : 3;
}
