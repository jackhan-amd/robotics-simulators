"""Build original Chrono demos with measurement/barrier hooks, no physical changes."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import datetime,difflib,hashlib,json,os,pathlib,re,subprocess
R=run_root();S=storage_root();up=S/'upstream/chrono';D=R/'provided-chrono';D.mkdir(exist_ok=True);E=R/'evidence'
os.environ['PATH']=str(S/'venvs/base/bin')+':'+str(S/'tools/bin')+':'+os.environ['PATH']
helper=r'''
#include <chrono>
#include <fstream>
#include <filesystem>
#include <thread>
#include <cmath>
#include "chrono/core/ChDataPath.h"
#include "chrono/gpu/ChGpuRuntime.h"
static std::chrono::steady_clock::time_point bench_start;
static int bench_steps=0;
static void bench_paths(){
 if(const char* p=std::getenv("STUDY_CHRONO_DATA")) chrono::SetChronoDataPath(p);
 if(const char* p=std::getenv("STUDY_CHRONO_OUTPUT")) chrono::SetChronoOutputPath(p);
}
static void bench_ready(){
 if(const char* p=std::getenv("STUDY_BENCH_READY")) std::ofstream(p).put('1');
 auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(300);
 if(const char* p=std::getenv("STUDY_BENCH_GO")) while(!std::filesystem::exists(p)){
  if(std::chrono::steady_clock::now()>deadline) throw std::runtime_error("benchmark start timeout");
  std::this_thread::sleep_for(std::chrono::milliseconds(1));
 }
 gpuDeviceSynchronize();bench_start=std::chrono::steady_clock::now();
}
static double bench_done(){
 gpuDeviceSynchronize();double t=std::chrono::duration<double>(std::chrono::steady_clock::now()-bench_start).count();
 if(const char* p=std::getenv("STUDY_BENCH_DONE")) std::ofstream(p).put('1');
 auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(900);
 if(const char* p=std::getenv("STUDY_BENCH_VALIDATE"))while(!std::filesystem::exists(p)){
  if(std::chrono::steady_clock::now()>deadline)throw std::runtime_error("benchmark validation barrier timeout");
  std::this_thread::sleep_for(std::chrono::milliseconds(1));
 }
 return t;
}
'''
archive_stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
for previous in ['provided-chrono-fsi-instrumentation.patch','provided-chrono-dem-instrumentation.patch','provided-chrono-source-receipts.json']:
 prior=E/previous
 if prior.exists():(E/(archive_stamp+'-before-validation-barrier-'+previous)).write_bytes(prior.read_bytes())
receipts={}
for kind,relative in [('fsi','src/demos/fsi/sph/demo_FSI-SPH_DamBreak.cpp'),('dem','src/demos/dem/demo_DEM_repose.cpp')]:
 source=up/relative;original=source.read_text();text=original
 marker='int main(int argc, char* argv[]) {';assert marker in text,kind
 text=text.replace(marker,helper+'\n'+marker+'\n    bench_paths();',1)
 if kind=='fsi':
  call=re.search(r'sysFSI\.DoStepDynamics\([^)]*\);',text);assert call,'original stepping call'
  text=text.replace(call[0],call[0]+' ++bench_steps;',1)
  loop=re.search(r'while\s*\(time\s*<\s*t_end\)\s*\{',text);assert loop,'original FSI loop'
  text=text[:loop.start()]+'const auto bench_count0=sysSPH.GetNumFluidMarkers();\n    bench_ready();\n    '+text[loop.start():]
  validation=r'''
    double bench_wall=bench_done(); auto bench_pos=sysSPH.GetParticlePositions(); auto bench_vel=sysSPH.GetParticleVelocities();
    bool bench_finite=true, bench_bounds=true;
    for(size_t i=0;i<bench_count0;++i){
      bench_finite=bench_finite && std::isfinite(bench_pos[i].x()) && std::isfinite(bench_pos[i].y()) && std::isfinite(bench_pos[i].z()) && std::isfinite(bench_vel[i].Length());
      bench_bounds=bench_bounds && std::abs(bench_pos[i].x())<7 && std::abs(bench_pos[i].y())<1 && bench_pos[i].z()>-0.5 && bench_pos[i].z()<9;
    }
    bool bench_valid=bench_finite && bench_bounds && bench_count0>1000 && sysSPH.GetNumFluidMarkers()==bench_count0 && gpuGetLastError()==gpuSuccess;
    std::cout << std::setprecision(17) << "SMOKE_RESULT_JSON:{\"backend_observed\":\"hip\",\"physics_valid\":" << (bench_valid?"true":"false") << ",\"steps\":" << bench_steps << ",\"dt\":" << step_size << ",\"particles\":" << bench_count0 << ",\"step_wall_s\":" << bench_wall << ",\"finite\":" << (bench_finite?"true":"false") << ",\"bounds\":" << (bench_bounds?"true":"false") << "}" << std::endl;
    return bench_valid?0:3;
'''
 else:
  assert 'dem_sys.AdvanceSimulation(step);'in text
  text=text.replace('dem_sys.AdvanceSimulation(step);','dem_sys.AdvanceSimulation(step); ++bench_steps;',1)
  # The upstream 100-byte output buffers overflow under the longer isolated study path.
  # Keep filename formatting bounded; this changes file-path handling only, never physics.
  text=text.replace('char filename[100];','char filename[4096];').replace('char mesh_filename[100];','char mesh_filename[4096];')
  text=text.replace('sprintf(filename,','snprintf(filename, sizeof(filename),').replace('sprintf(mesh_filename,','snprintf(mesh_filename, sizeof(mesh_filename),')
  # Disable output only; retain original initialization, particles, funnel, contact and integrator.
  text=re.sub(r'^\s*dem_sys\.WriteParticleFile\([^;]+;','',text,flags=re.M);text=re.sub(r'^\s*dem_sys\.WriteMeshes\([^;]+;','',text,flags=re.M)
  loop=re.search(r'while\s*\(time\s*<\s*params.time_end\)\s*\{',text);assert loop,'original DEM loop'
  text=text[:loop.start()]+'const auto bench_count0=dem_sys.GetNumParticles();\n    bench_ready();\n    '+text[loop.start():]
  validation=r'''
    double bench_wall=bench_done();bool bench_finite=true;
    for(size_t i=0;i<bench_count0;++i){auto p=dem_sys.GetParticlePosition(i);auto v=dem_sys.GetParticleVelocity(i);bench_finite=bench_finite && std::isfinite(p.x()) && std::isfinite(p.y()) && std::isfinite(p.z()) && std::isfinite(v.Length());}
    bool bench_valid=bench_finite && bench_count0>1000 && dem_sys.GetNumParticles()==bench_count0 && std::isfinite(dem_sys.GetParticlesKineticEnergy()) && gpuGetLastError()==gpuSuccess;
    std::cout << std::setprecision(17) << "SMOKE_RESULT_JSON:{\"backend_observed\":\"hip\",\"physics_valid\":" << (bench_valid?"true":"false") << ",\"steps\":" << bench_steps << ",\"dt\":" << step << ",\"native_substep_dt\":" << params.step_size << ",\"particles\":" << bench_count0 << ",\"step_wall_s\":" << bench_wall << ",\"finite\":" << (bench_finite?"true":"false") << "}" << std::endl;
    return bench_valid?0:3;
'''
 # Console output is not a physical setting. Drop per-frame diagnostics from the timed loop.
 text=re.sub(r'printf\("Output frame[^;]+;','',text)
 text=text.replace('return 0;',validation,1)
 text='#include <iomanip>\n#include <stdexcept>\n'+text
 (D/(kind+'.cpp')).write_text(text)
 (E/f'provided-chrono-{kind}-instrumentation.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile=relative,tofile='instrumented/'+relative)))
 receipts[kind]=dict(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),instrumented_sha256=hashlib.sha256(text.encode()).hexdigest(),validation_barrier=True,scope='Original supplied demo physical setup unchanged. Runtime asset paths, headless execution, output suppression, bounded output-path formatting (DEM upstream 100-byte buffers overflowed under the study path), ready/go/done/validate barriers and final finite/count/bounds checks only. All environments finish timing before any final validation readback starts.')
(E/'provided-chrono-source-receipts.json').write_text(json.dumps(receipts,indent=2))
cmake='''cmake_minimum_required(VERSION 3.24)
project(provided_chrono_demos LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
find_package(Chrono REQUIRED COMPONENTS FSI_SPH DEM CONFIG)
find_package(hip REQUIRED CONFIG)
foreach(kind fsi dem)
 add_executable(provided_${kind} ${kind}.cpp)
 target_compile_definitions(provided_${kind} PRIVATE CHRONO_USE_HIP)
 target_link_libraries(provided_${kind} PRIVATE ${CHRONO_TARGETS} hip::host)
endforeach()
'''
(D/'CMakeLists.txt').write_text(cmake)
for cmd in [['cmake','-S',str(D),'-B',str(D/'build'),'-G','Ninja','-DChrono_DIR='+str(S/'build/chrono-hip-devel/cmake'),'-DCHRONO_ROCM_ROOT='+os.environ['ROCM_PATH'],'-DCMAKE_PREFIX_PATH='+os.environ['ROCM_PATH'],'-DEIGEN3_INCLUDE_DIR='+str(S/'upstream/eigen')],['cmake','--build',str(D/'build'),'--parallel','4']]:
 print('+',*cmd,flush=True);subprocess.run(cmd,check=True,timeout=600)
