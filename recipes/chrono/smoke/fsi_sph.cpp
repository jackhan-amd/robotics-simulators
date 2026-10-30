// SPDX-License-Identifier: BSD-3-Clause
// Adapted API/example patterns from Project Chrono Development Team. Study-specific geometry, validation and integration changes.
// Small external adaptation of Project Chrono's demo_FSI-SPH_DamBreak.cpp.
// Upstream setup pattern: Copyright Project Chrono, BSD-3-Clause.
// Procedural scene and gates: docs/06_validation.md. Core multibody remains CPU.
#include <algorithm>
#include <cstdlib>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>
#include "chrono/physics/ChSystemSMC.h"
#include "chrono/utils/ChUtilsSamplers.h"
#include "chrono_fsi/sph/ChFsiSystemSPH.h"
#include "chrono/gpu/ChGpuRuntime.h"
using namespace chrono;
using namespace chrono::fsi::sph;
int main(int argc, char** argv) {
    const int steps = argc > 1 ? std::stoi(argv[1]) : 10;
    if (steps != 10 && steps != 50) return 2;
    const double dt = 0.0001;
    auto begin = std::chrono::steady_clock::now();
    int device = -1;
    gpuDeviceProp prop{};
    if (gpuGetDevice(&device) != gpuSuccess || gpuGetDeviceProperties(&prop, device) != gpuSuccess) return 4;
#ifdef CHRONO_USE_HIP
    const char* observed = "hip";
    const char* expected = std::getenv("STUDY_AMD_ARCH");
    if (std::string(prop.gcnArchName).substr(0, std::string(prop.gcnArchName).find(":")) != (expected ? expected : "gfx1151")) return 5;
#else
    const char* observed = "cuda";
    if (prop.major != 8 || prop.minor != 6 || std::string(prop.name).find("3090") == std::string::npos) return 5;
#endif
    std::cout << "SMOKE_DEVICE: " << prop.name << " index=" << device << std::endl;
    ChSystemSMC mbs;
    ChFsiFluidSystemSPH sph;
    ChFsiSystemSPH fsi(&mbs, &sph);
    fsi.SetVerbose(false);
    fsi.SetStepSizeCFD(dt);
    fsi.SetStepsizeMBD(dt);
    fsi.SetGravitationalAcceleration(ChVector3d(0, 0, -9.81));
    ChFsiFluidSystemSPH::FluidProperties fluid;
    fluid.density = 1000;
    fluid.viscosity = 0.01;
    sph.SetCfdSPH(fluid);
    ChFsiFluidSystemSPH::SPHParameters params;
    params.integration_scheme = IntegrationScheme::RK2;
    params.initial_spacing = 0.04;
    params.d0_multiplier = 1.2;
    params.max_velocity = 1;
    params.shifting_method = ShiftingMethod::NONE;
    params.viscosity_method = ViscosityMethod::LAMINAR;
    params.boundary_method = BoundaryMethod::ADAMI;
    params.num_proximity_search_steps = 1;
    sph.SetSPHParameters(params);
    sph.SetComputationalDomain(ChAABB(ChVector3d(-0.4, -0.4, -0.2), ChVector3d(0.4, 0.4, 0.8)));
    utils::ChGridSampler<> sampler(0.04);
    auto points = sampler.SampleBox(ChVector3d(0, 0, 0.25), ChVector3d(0.04, 0.04, 0.04));
    for (auto& point : points) sph.AddSPHParticle(point, 1000, 0, 0.01);
    auto ground = chrono_types::make_shared<ChBody>();
    ground->SetFixed(true);
    ground->EnableCollision(false);
    mbs.AddBody(ground);
    auto bce = sph.CreatePointsBoxContainer(ChVector3d(0.6, 0.6, 0.6), {2, 2, 2});
    fsi.AddFsiBoundary(bce, ChFrame<>(ChVector3d(0, 0, 0.3), QUNIT));
    fsi.Initialize();
    gpuDeviceSynchronize();
    double build_s = std::chrono::duration<double>(std::chrono::steady_clock::now() - begin).count();
    const size_t count = sph.GetNumFluidMarkers();
    const double mass = count * sph.GetParticleMass();
    auto initial = sph.GetParticlePositions();
    if (!count || initial.size() < count) return 6;
    double z0 = 0;
    for (size_t i = 0; i < count; ++i) z0 += initial[i].z() / count;
    bool finite = true, bounds = true, density = true;
    double max_speed = 0, max_com_error = 0;
    begin = std::chrono::steady_clock::now();
    for (int n = 1; n <= steps; ++n) {
        fsi.DoStepDynamics(dt);
        if (gpuDeviceSynchronize() != gpuSuccess) return 7;
        auto pos = sph.GetParticlePositions();
        auto vel = sph.GetParticleVelocities();
        auto properties = sph.GetParticleFluidProperties();
        if (pos.size() < count || vel.size() < count || properties.size() < count) return 8;
        double com_z = 0;
        for (size_t i = 0; i < count; ++i) {
            finite = finite && std::isfinite(pos[i].x()) && std::isfinite(pos[i].y()) && std::isfinite(pos[i].z()) &&
                     std::isfinite(vel[i].Length()) && std::isfinite(properties[i].x());
            bounds = bounds && std::abs(pos[i].x()) <= 0.31 && std::abs(pos[i].y()) <= 0.31 && pos[i].z() >= -0.01 && pos[i].z() <= 0.61;
            density = density && properties[i].x() >= 800 && properties[i].x() <= 1200;
            max_speed = std::max(max_speed, vel[i].Length());
            com_z += pos[i].z() / count;
        }
        max_com_error = std::max(max_com_error, std::abs(com_z - (z0 - 9.81 * n * n * dt * dt / 2)));
    }
    gpuDeviceSynchronize();
    double step_s = std::chrono::duration<double>(std::chrono::steady_clock::now() - begin).count();
    bool conserved = sph.GetNumFluidMarkers() == count && std::abs(sph.GetParticleMass() * count - mass) <= mass * 1e-6;
    bool valid = finite && bounds && density && conserved && max_speed <= 2 && max_com_error <= 0.0005 && gpuGetLastError() == gpuSuccess;
    std::cout << std::setprecision(12) << std::boolalpha
              << "SMOKE_RESULT_JSON:{\"backend_observed\":\"" << observed << "\",\"physics_valid\":" << valid
              << ",\"steps\":" << steps << ",\"dt\":" << dt << ",\"particles\":" << count
              << ",\"boundary_markers\":" << sph.GetNumBoundaryMarkers() << ",\"particle_spacing\":0.04,\"kernel_multiplier\":1.2"
              << ",\"build_s\":" << build_s << ",\"step_wall_s\":" << step_s << ",\"g2_qualified\":false"
              << ",\"gates\":{\"finite\":" << finite << ",\"bounds\":" << bounds << ",\"density\":" << density
              << ",\"mass\":" << conserved << ",\"speed\":" << (max_speed <= 2) << ",\"com\":" << (max_com_error <= 0.0005)
              << "},\"metrics\":{\"mass_kg\":" << mass << ",\"max_speed\":" << max_speed << ",\"max_com_error_m\":" << max_com_error << "}}" << std::endl;
    return valid ? 0 : 3;
}
