"""Reuse pinned native build objects; replace main only with timer barriers."""
from workspace import storage_root
from workspace import expand_runtime, run_root, runtime_path
import difflib,hashlib,json,os,pathlib,subprocess
R=run_root();S=storage_root();source=S/'upstream/incflo/src/main.cpp';build=S/'build/incflo-hip-devel';out=R/'provided-incflo';out.mkdir(exist_ok=True)
before=source.read_text();helper=r'''
#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <thread>
static void study_ready(){
 amrex::Gpu::synchronize();
 if(const char* p=std::getenv("STUDY_BENCH_READY"))std::ofstream(p).put('1');
 auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(600);
 if(const char* p=std::getenv("STUDY_BENCH_GO"))while(!std::filesystem::exists(p)){
  if(std::chrono::steady_clock::now()>deadline)throw std::runtime_error("barrier timeout");
  std::this_thread::sleep_for(std::chrono::milliseconds(1));
 }
}
static void study_done(){
 amrex::Gpu::synchronize();if(const char* p=std::getenv("STUDY_BENCH_DONE"))std::ofstream(p).put('1');
 auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(600);
 if(const char* p=std::getenv("STUDY_BENCH_VALIDATE"))while(!std::filesystem::exists(p)){
  if(std::chrono::steady_clock::now()>deadline)throw std::runtime_error("validation barrier timeout");
  std::this_thread::sleep_for(std::chrono::milliseconds(1));
 }
}
'''
after=before.replace('void writeBuildInfo();',helper+'\nvoid writeBuildInfo();').replace('my_incflo.Evolve();','study_ready();\n        my_incflo.Evolve();\n        study_done();')
main=out/'main.cpp';main.write_text(after)
commands=subprocess.check_output([str(S/'tools/bin/ninja'),'-C',str(build),'-t','commands','incflo'],text=True).splitlines()
compilecmd=next(c for c in commands if '/src/main.cpp'in c and ' -c 'in c)
import shlex
args=shlex.split(compilecmd);oi=args.index('-o')+1;oldobj=args[oi];args[oi]=str(out/'main.o');args[args.index('-c')+1]=str(main)
subprocess.run(args,cwd=build,check=True,timeout=300)
link=commands[-1].replace(oldobj,str(out/'main.o'));link=link.replace('-o incflo.ex','-o '+str(out/'incflo.ex'))
assert str(out/'main.o')in link and str(out/'incflo.ex')in link,link
subprocess.run(link,shell=True,cwd=build,check=True,timeout=300)
(R/'evidence/provided-incflo-main.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='original/main.cpp',tofile='instrumented/main.cpp')))
(R/'evidence/provided-incflo-build.json').write_text(json.dumps(dict(original_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),instrumented_sha256=hashlib.sha256(main.read_bytes()).hexdigest(),compile=args,link=link,scope='initialization/stepping barriers only; solver and original input unchanged'),indent=2))
print('BUILT',out/'incflo.ex')
