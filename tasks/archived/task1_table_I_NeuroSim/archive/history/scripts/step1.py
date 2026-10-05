#!/usr/bin/env python3
"""NeuroSim Step 1. Standard library only. Never builds or runs in cloud storage."""
import argparse
import datetime
import glob
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time

URL = "https://github.com/neurosim/NeuroSim.git"
SNAPSHOTS = [
    ("2DInferenceV1.4", "8a88abf85844c0e1ba17cc771ea535fff6040456", "Inference_pytorch/NeuroSIM"),
    ("2DInferenceDCIMV1.0-dev", "38eedf926fc1a712df3627f36bb82b097ba6b9cb", "Inference_pytorch/NeuroSIM"),
    ("2DInferenceV1.5-dev", "9825ef40bf14d12a72c99d8e32ff8c499aeddf24", "NeuroSIM"),
    ("2DTrainingV2.1", "f80a4345f70dcb1ddfd003d3ddcfbd067b55a79a", "Training_pytorch/NeuroSIM"),
    ("MLPInferenceV3.0", "6098feabaf17b8209a8edbef4a9c963b5f015132", "."),
    ("3DInferenceV1.0", "6d2ee9b9b5067c4c8660ad8cd0cbedcab477ba69", None),
]

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n")

def portable(data, root, management):
    """Keep machine-private workspace paths in local records, not shared artifacts."""
    text = json.dumps(data, ensure_ascii=True)
    for path, replacement in ((management, "${MANAGEMENT_ROOT}"), (management.parents[1], "${REPO_ROOT}"), (root, "${NEUROSIM_ROOT}")):
        text = text.replace(json.dumps(str(path), ensure_ascii=True)[1:-1], replacement)
    return json.loads(text)

def output(cmd, cwd=None):
    return subprocess.check_output(cmd, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()

def tree_hashes(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(Path(root).rglob("*"))
            if p.is_file() and p.name != ".git"}

def checked_root():
    root = Path(os.environ.get("NEUROSIM_ROOT", str(Path.home() / "neurosim"))).expanduser()
    root = root.resolve()
    lowered = str(root).lower()
    if any(s in lowered for s in ("onedrive", "icloud", "mobile documents", "cloudstorage", "dropbox")):
        raise RuntimeError("NEUROSIM_ROOT resolves into cloud storage: " + str(root))
    root.mkdir(parents=True, exist_ok=True)
    for name in ("upstream", "worktrees", "build", "envs", "runs/step1", "cache/tmp", "cache/homebrew", "staging"):
        p = root / name
        p.mkdir(parents=True, exist_ok=True)
        if root not in p.resolve().parents:
            raise RuntimeError("Local subdirectory escapes root via a symlink: " + str(p))
    os.environ.update(TMPDIR=str(root / "cache/tmp"),
                      HOMEBREW_CACHE=str(root / "cache/homebrew"),
                      HOMEBREW_TEMP=str(root / "cache/tmp"),
                      HOMEBREW_LOGS=str(root / "runs/step1/homebrew-logs"),
                      HOMEBREW_NO_AUTO_UPDATE="1",
                      HOMEBREW_NO_INSTALL_CLEANUP="1",
                      GIT_OPTIONAL_LOCKS="0",
                      PYTHONDONTWRITEBYTECODE="1")
    return root

def bootstrap():
    """Execute a hash-addressed local copy of the canonical scripts."""
    root = checked_root()
    if os.environ.get("NEUROSIM_LOCAL_COPY") == "1":
        os.chdir(root)
        return root, Path(os.environ["NEUROSIM_MANAGEMENT"])
    management = Path(__file__).resolve().parents[1]
    source = management / "scripts"
    hashes = {p.name: sha(p) for p in sorted(source.iterdir()) if p.is_file()}
    digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    stage = root / "staging" / ("scripts-" + digest)
    stage.mkdir(exist_ok=True)
    for name, expected in hashes.items():
        target = stage / name
        if target.exists() and sha(target) != expected:
            raise RuntimeError("Existing staged script was modified: " + str(target))
        if not target.exists():
            shutil.copy2(source / name, target)
    hash_file = stage / "script_hashes.json"
    if hash_file.exists():
        if json.loads(hash_file.read_text()) != hashes:
            raise RuntimeError("Staged script manifest differs: " + str(hash_file))
    else:
        write_json(hash_file, hashes)
    env = os.environ.copy()
    env.update(NEUROSIM_LOCAL_COPY="1", NEUROSIM_MANAGEMENT=str(management),
               NEUROSIM_SCRIPT_DIGEST=digest, NEUROSIM_INVOCATION_CWD=os.getcwd())
    os.execve(sys.executable, [sys.executable, str(stage / "step1.py")] + sys.argv[1:], env)

class Session:
    def __init__(self, root, label):
        self.root = root
        run_id = os.environ.get("NEUROSIM_RUN_ID") or (label + "-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + str(os.getpid()))
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", run_id):
            raise RuntimeError("NEUROSIM_RUN_ID must be a simple directory name")
        self.run = root / "runs/step1" / run_id
        self.run.mkdir(exist_ok=False)
        self.commands = []
        self.script_hashes = json.loads((Path(__file__).parent / "script_hashes.json").read_text())
        write_json(self.run / "script_hashes.json", self.script_hashes)
    def command(self, cmd, name, cwd=None, stdin=None, check=True):
        cwd = Path(cwd or self.run).resolve()
        if self.root != cwd and self.root not in cwd.parents:
            raise RuntimeError("Command cwd must be local: " + str(cwd))
        start = time.time()
        log = self.run / (name + ".log")
        with log.open("w") as f:
            proc = subprocess.run([str(c) for c in cmd], cwd=cwd, input=stdin, text=True,
                                  stdout=f, stderr=subprocess.STDOUT)
        self.commands.append({"argv": [str(c) for c in cmd], "cwd": str(cwd),
                              "exit_code": proc.returncode, "seconds": time.time()-start,
                              "log": str(log), "stdin": stdin})
        write_json(self.run / "commands.json", self.commands)
        if check and proc.returncode:
            raise RuntimeError("Command failed (" + str(proc.returncode) + "): " + str(log))
        return proc.returncode, log.read_text(errors="replace")

def find_gnu_cxx():
    explicit = os.environ.get("NEUROSIM_CXX")
    candidates = [explicit] if explicit else []
    if not explicit:
        dirs = os.environ.get("PATH", "").split(os.pathsep)
        dirs.extend(("/opt/homebrew/bin", "/usr/local/bin"))
        for directory in dict.fromkeys(dirs):
            candidates.extend(glob.glob(str(Path(directory) / "g++-[0-9]*")))
    candidates = sorted(set(candidates), key=lambda s: [int(n) for n in re.findall(r"\d+", s)], reverse=True)
    for cxx in candidates:
        try:
            macros = subprocess.check_output([cxx, "-dM", "-E", "-x", "c++", "-"], input="", text=True)
            if "__GNUC__" in macros and "__clang__" not in macros:
                return str(Path(cxx).absolute())
        except (OSError, subprocess.CalledProcessError):
            continue
    if explicit:
        raise RuntimeError("NEUROSIM_CXX is not a functioning GNU C++ compiler: " + explicit)
    return None

def probe(root, management, session):
    path = root / "staging" / ("probe-" + session.run.name)
    path.mkdir(exist_ok=False)
    source = path / "probe.py"
    source.write_text("from pathlib import Path\np=Path(__file__).with_name('result.txt')\np.write_text('cross_directory_probe PASS value=42\\n')\nprint(p.read_text().strip())\n")
    # The actual access/launch originates from the caller's cloud working directory.
    cwd = Path(os.environ["NEUROSIM_INVOCATION_CWD"])
    proc = subprocess.run([sys.executable, str(source)], cwd=cwd, text=True, capture_output=True)
    result = {"status": "PASS" if proc.returncode == 0 and "value=42" in proc.stdout else "FAIL",
              "invocation_cwd": str(cwd), "local_path": str(path), "exit_code": proc.returncode,
              "stdout": proc.stdout, "stderr": proc.stderr, "read_back": (path / "result.txt").read_text(),
              "script_sha256": sha(source), "launch_argv": [sys.executable, str(source)],
              "script_read_verified": "value=42" in source.read_text()}
    dest = management / "results/smoke/cross_directory_probe.json"
    write_json(dest, portable(result, root, management))
    write_json(session.run / "cross_directory_probe.json", result)
    shutil.copy2(path / "result.txt", management / "results/smoke/cross_directory_probe.txt")
    source.unlink()
    (path / "result.txt").unlink()
    path.rmdir()
    if result["status"] != "PASS":
        raise RuntimeError("Cross-directory probe failed")

def setup(root, management, session):
    probe(root, management, session)
    if subprocess.run(["xcode-select", "-p"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
        raise RuntimeError("BLOCKED: run xcode-select --install and complete the macOS installer, then rerun")
    cxx = find_gnu_cxx()
    installed = []
    if cxx is None:
        brew = shutil.which("brew")
        if not brew:
            raise RuntimeError("BLOCKED: install Homebrew using https://brew.sh, then rerun")
        session.command([brew, "install", "gcc"], "brew-install-gcc")
        installed.append("gcc (and Homebrew dependencies)")
        cxx = find_gnu_cxx()
    if not cxx:
        raise RuntimeError("GNU C++ compiler still unavailable")
    session.command(["xcode-select", "-p"], "xcode-select")
    omp_source = session.run / "openmp_probe.cpp"
    omp_source.write_text('#include <omp.h>\n#include <cstdio>\nint main(){long sum=0; int threads=0;\n#pragma omp parallel reduction(+:sum)\n{\n#pragma omp single\nthreads=omp_get_num_threads();\n#pragma omp for\nfor(int i=1;i<=1000;++i) sum+=i;\n}\nprintf("sum=%ld threads=%d\\n",sum,threads);return sum==500500&&threads>0?0:1;}\n')
    omp_binary = session.run / "openmp_probe"
    session.command([cxx, "-O2", "-fopenmp", str(omp_source), "-o", str(omp_binary)], "openmp-build")
    session.command([omp_binary], "openmp-run")
    session.command(["file", omp_binary], "openmp-file")
    session.command(["otool", "-L", omp_binary], "openmp-libraries")
    env = os.environ.copy()
    env["DYLD_PRINT_LIBRARIES"] = "1"
    with (session.run / "openmp-dyld.log").open("w") as f:
        subprocess.run([str(omp_binary)], cwd=session.run, env=env, stdout=f, stderr=subprocess.STDOUT, check=True)
    tools = {}
    for name, cmd in (("git", ["git", "--version"]), ("make", ["make", "--version"]),
                      ("python", [sys.executable, "--version"]), ("cxx", [cxx, "--version"]),
                      ("apple_clang", ["/usr/bin/clang++", "--version"]), ("brew", ["brew", "--version"])):
        tools[name] = {"path": shutil.which(cmd[0]) or cmd[0], "version": output(cmd)}
    environment = {"recorded_at_utc": utc(), "os": output(["sw_vers"]), "architecture": platform.machine(),
                   "tools": tools, "xcode_developer_directory": output(["xcode-select", "-p"]),
                   "clt_pkg": subprocess.run(["pkgutil", "--pkg-info", "com.apple.pkg.CLTools_Executables"], text=True, capture_output=True).stdout,
                   "compiler_target": output([cxx, "-dumpmachine"]),
                   "compiler_binary": output(["file", "-L", cxx]),
                   "openmp_test": {"status": "PASS", "compile_flags": ["-O2", "-fopenmp"],
                                   "result": (session.run / "openmp-run.log").read_text().strip(),
                                   "executable_architecture": (session.run / "openmp-file.log").read_text().strip(),
                                   "linked_libraries": (session.run / "openmp-libraries.log").read_text(),
                                   "loaded_runtime_libraries": [line for line in (session.run / "openmp-dyld.log").read_text().splitlines() if "libgomp" in line or "libstdc++" in line or "libgcc_s" in line],
                                   "runtime_load_log": "openmp-dyld.log"},
                   "installed_by_this_setup_invocation": installed,
                   "brew_gcc_dependencies": output(["brew", "list", "--versions", "gcc", "gmp", "isl", "mpfr", "libmpc", "xz"]),
                   "python_packages_installed": [], "full_environment_exported": False}
    if (root / "dependency-installation.json").exists():
        environment["installation_record"] = json.loads((root / "dependency-installation.json").read_text())
    write_json(management / "provenance/environment.json", portable(environment, root, management))
    write_json(root / "machine_paths.json", {"home": str(Path.home()), "local_root": str(root),
        "management_root": str(management), "setup_run": str(session.run), "compiler": cxx,
        "invocation_cwd": os.environ["NEUROSIM_INVOCATION_CWD"]})
    _, heads_text = session.command(["git", "ls-remote", "--heads", URL], "remote-heads")
    heads = dict((line.split()[1].removeprefix("refs/heads/"), line.split()[0]) for line in heads_text.splitlines())
    (management / "provenance/remote_heads.tsv").write_text("sha\tref\n" + heads_text)
    upstream = root / "upstream/NeuroSim"
    if not upstream.exists():
        session.command(["git", "clone", "--filter=blob:none", "--no-checkout", URL, str(upstream)], "clone")
    else:
        if output(["git", "remote", "get-url", "origin"], upstream) != URL:
            raise RuntimeError("Existing upstream origin does not match")
        if output(["git", "config", "--get", "remote.origin.promisor"], upstream) != "true":
            raise RuntimeError("Existing upstream is not the expected partial clone")
        session.command(["git", "fetch", "--filter=blob:none", "origin"], "fetch", upstream)
    session.command(["git", "config", "extensions.worktreeConfig", "true"], "worktree-config", upstream)
    entries = []
    machine_worktrees = {}
    notices = ["NeuroSim upstream notices and citation entries", "Source URL: " + URL, "", "These are upstream notices, preserved without changing their terms.", ""]
    for branch, locked, core in SNAPSHOTS:
        label = branch.replace(".", "_")
        names = output(["git", "ls-tree", "-r", "--name-only", locked], upstream).splitlines()
        docs = [n for n in names if (n.count("/") == 0 and re.search(r"readme|license|copying|citation", n, re.I))]
        if core and core != ".":
            selected = [n for n in names if n.startswith(core + "/") and Path(n).suffix.lower() in (".cpp", ".h", ".hpp", ".c", ".md", ".txt")]
            selected += [n for n in names if n.startswith(core + "/") and Path(n).name.lower() in ("makefile", "license", "readme")]
        elif core == ".":
            selected = [n for n in names if Path(n).suffix.lower() in (".cpp", ".h", ".hpp", ".c") or Path(n).name.lower() == "makefile"]
        else:
            selected = []
        selected = sorted(set(selected + docs))
        if core and not any(Path(n).suffix == ".cpp" for n in selected):
            raise RuntimeError("No C++ core found at locked location: " + branch)
        wt = root / "worktrees" / (branch + "-" + locked[:12])
        if not wt.exists():
            session.command(["git", "worktree", "add", "--detach", "--no-checkout", str(wt), locked], "worktree-"+label, upstream)
        elif output(["git", "rev-parse", "HEAD"], wt) != locked:
            raise RuntimeError("Existing worktree SHA differs: " + str(wt))
        if output(["git", "status", "--porcelain", "--untracked-files=all"], wt) and (wt / selected[0]).exists():
            raise RuntimeError("Existing worktree has user changes: " + str(wt))
        session.command(["git", "sparse-checkout", "set", "--no-cone", "--stdin"], "sparse-"+label, wt,
                        stdin="".join("/"+n+"\n" for n in selected))
        session.command(["git", "checkout", "--detach", locked], "checkout-"+label, wt)
        remote = heads.get(branch)
        relation = "equal" if remote == locked else "not_queried"
        if remote and remote != locked:
            rc, _ = session.command(["git", "merge-base", "--is-ancestor", locked, remote], "ancestry-"+label, upstream, check=False)
            relation = "locked_is_ancestor_of_remote" if rc == 0 else "diverged_or_remote_behind"
        _, diff = session.command(["git", "status", "--porcelain", "--untracked-files=all"], "status-"+label, wt)
        if diff.strip():
            raise RuntimeError("Sparse worktree is not clean: " + str(wt))
        hashes = tree_hashes(wt)
        core_candidates = [n.rsplit("/", 1)[0] if "/" in n else "." for n in names if Path(n).name == "main.cpp"]
        for doc in docs:
            if "readme" in doc.lower():
                content = (wt / doc).read_text(errors="replace")
                notices += ["Branch: " + branch, "Locked README: https://github.com/neurosim/NeuroSim/blob/" + locked + "/" + doc]
                notices += [line for line in content.splitlines() if "Creative Commons" in line or "Copyright" in line or "copyright" in line]
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if "required to cite" in line:
                        notices.extend(lines[i:i+5])
                notices.append("")
        if core and (wt / core / "main.cpp").exists():
            source_text = (wt / core / "main.cpp").read_text(errors="replace")
            if source_text.startswith("/*"):
                notice = source_text.split("*/",1)[0]+"*/"
                notices += ["C++ copyright header: " + branch + "/" + core + "/main.cpp", notice, ""]
        write_json(session.run / (label + "-source-hashes.json"), hashes)
        entries.append({"branch": branch, "locked_sha": locked, "remote_head_at_query": remote,
                        "remote_relation": relation, "core_path": core, "selected_paths": selected,
                        "core_paths_from_tree": core_candidates if core is None else [core],
                        "method": "partial clone blob:none; independent non-cone sparse worktree; exact file whitelist",
                        "source_files": len(hashes), "source_manifest_sha256": sha(session.run / (label + "-source-hashes.json")),
                        "worktree_clean": True, "documentation_entries": docs,
                        "copyright_and_citation_entries": docs + [n for n in selected if Path(n).name in ("main.cpp", "Param.cpp")],
                        "step1_scope": "README navigation only; NOT_RUN" if not core else "C++ source ready"})
        machine_worktrees[branch] = str(wt)
    lock = {"schema_version": 1, "upstream_url": URL, "queried_at_utc": utc(), "snapshots": entries,
            "main_role": "version/documentation entry; not a unique computational implementation",
            "main_head_at_query": heads.get("main"), "upstream_notices": "upstream-notices.txt"}
    write_json(management / "provenance/neurosim.lock.json", lock)
    (management / "provenance/upstream-notices.txt").write_text("\n".join(notices)+"\n")
    write_json(root / "worktrees.json", machine_worktrees)
    main_sha = heads.get("main")
    if main_sha:
        _, readme = session.command(["git", "show", main_sha + ":README.md"], "main-README", upstream)
        (session.run / "main-README.md").write_text(readme)
    result = {"status": "PASS", "timestamp_utc": utc(), "run": str(session.run),
              "script_digest": os.environ["NEUROSIM_SCRIPT_DIGEST"], "cxx": cxx,
              "worktree_count": len(entries), "remote_heads_count": len(heads)}
    write_json(session.run / "setup-summary.json", result)
    write_json(root / "setup-latest.json", result)
    print(json.dumps(result, indent=2))

def smoke(root, management, session):
    from smoke_io import generate_inputs, validate_output
    if not (root / "setup-latest.json").exists():
        raise RuntimeError("Run setup_step1.sh first")
    cxx = find_gnu_cxx()
    if not cxx:
        raise RuntimeError("Run setup_step1.sh: GNU compiler unavailable")
    paths = json.loads((root / "worktrees.json").read_text())
    build_root = root / "build" / session.run.name
    build_root.mkdir(exist_ok=False)
    build_results = {}
    parameters = {}
    for branch, locked, core in SNAPSHOTS[:2]:
        wt = Path(paths[branch])
        if output(["git", "rev-parse", "HEAD"], wt) != locked or output(["git", "status", "--porcelain", "--untracked-files=all"], wt):
            raise RuntimeError("Locked worktree was changed: " + branch)
        source = wt / core
        destination = build_root / branch
        shutil.copytree(source, destination)
        manifest = tree_hashes(source)
        if manifest != tree_hashes(destination):
            raise RuntimeError("Build copy source hash mismatch: " + branch)
        write_json(session.run / (branch + "-build-source-hashes.json"), manifest)
        rc, _ = session.command([shutil.which("make"), "-j"+os.environ.get("NEUROSIM_JOBS", "4"), "CXX="+cxx],
                                 "build-"+branch, destination, check=False)
        build_results[branch] = {"status": "PASS" if rc == 0 and (destination / "main").is_file() else "FAIL",
                                 "locked_sha": locked, "exit_code": rc, "source_matches_locked_worktree": True,
                                 "source_manifest_sha256": sha(session.run / (branch + "-build-source-hashes.json")),
                                 "source_patches": [], "make_override": "CXX="+cxx,
                                 "upstream_cxxflags": "-fopenmp -O3 -std=c++0x -w"}
        if build_results[branch]["status"] == "PASS":
            _, libraries = session.command(["otool", "-L", destination / "main"], "libraries-"+branch)
            _, binary_info = session.command(["file", destination / "main"], "binary-"+branch)
            build_results[branch].update(binary_sha256=sha(destination / "main"), libraries=libraries,
                                         architecture=binary_info)
            fields = ["technode", "operationmode", "memcelltype", "accesstype", "transistortype", "deviceroadmap", "temp",
                      "numRowSubArray", "numColSubArray", "numRowParallel", "cellBit", "levelOutput", "numColMuxed",
                      "pipeline", "speedUpDegree", "synchronous", "novelMapping", "globalBusType", "globalBufferType", "chipActivation",
                      "SARADC", "currentMode", "sync_data_transfer", "parallelRead", "clkFreq", "algoWeightMin", "algoWeightMax"]
            if branch == "2DInferenceDCIMV1.0-dev":
                fields.append("toggle_enforce")
            dump_source = session.run / (branch+"-param-dump.cpp")
            dump_source.write_text('#include <string>\n#include <iostream>\nusing std::string;\n#include "Param.h"\nint main(){Param p;\n' +
                "\n".join('std::cout << "'+f+'=" << p.'+f+' << "\\n";' for f in fields) + '\n}\n')
            dump_binary = session.run / (branch+"-param-dump")
            session.command([cxx, "-std=c++0x", "-I", destination, dump_source, destination / "Param.cpp", "-o", dump_binary], "param-build-"+branch)
            _, dump_text = session.command([dump_binary], "param-run-"+branch)
            defaults = dict(line.split("=", 1) for line in dump_text.splitlines())
            effective = defaults.copy()
            if branch == "2DInferenceV1.4":
                effective.update(synapseBit="8", numBitInput="8", numRowSubArray="128", numRowParallel="128", numRowPerSynapse="1", numColPerSynapse="8", conventionalParallel="1")
            parameters[branch] = {"constructor_values": defaults, "effective_smoke_initial_values": effective if branch == "2DInferenceV1.4" else None,
                                  "evidence": "Compiled unmodified Param.cpp with a read-only constructor field dump; V1.4 argv overrides match original main; measured clock period is in simulator stdout",
                                  "param_cpp_sha256": sha(source / "Param.cpp"),
                                  "simulation_status": "RUN" if branch == "2DInferenceV1.4" else "NOT_RUN",
                                  "dcim_supported_subarray": "256x256 only according to locked README" if "DCIM" in branch else None}
    write_json(session.run / "builds.json", build_results)
    write_json(session.run / "parameters.json", parameters)
    metadata = generate_inputs(session.run / "inputs")
    validations = []
    if build_results["2DInferenceV1.4"]["status"] == "PASS":
        main_binary = build_root / "2DInferenceV1.4/main"
        inputs = session.run / "inputs"
        command = [main_binary, inputs / "network.csv", "8", "8", "128", "128", inputs / "weights.csv", inputs / "input.csv"]
        for n in (1, 2):
            execution = session.run / ("execution-"+str(n))
            execution.mkdir()
            rc, stdout = session.command(command, "v14-run-"+str(n), execution, check=False)
            result = validate_output(stdout)
            result["exit_code"] = rc
            result["assertions"]["exit_zero"] = rc == 0
            result["status"] = "PASS" if all(result["assertions"].values()) else "FAIL"
            result["stdout_sha256"] = sha(session.run / ("v14-run-"+str(n)+".log"))
            write_json(session.run / ("assertions-run-"+str(n)+".json"), result)
            validations.append(result)
    equal = (len(validations) == 2 and all(v["status"] == "PASS" for v in validations)
             and bool(validations[0]["stable_numeric_lines"])
             and validations[0]["stable_numeric_lines"] == validations[1]["stable_numeric_lines"])
    comparison = {"status": "PASS" if equal else "FAIL", "comparison": "exact printed numeric lines, excluding wall-clock Total Run-time",
                  "compared_line_count": len(validations[0]["stable_numeric_lines"]) if validations else 0,
                  "changed_numeric_lines": [] if equal else {"first": validations[0]["stable_numeric_lines"] if validations else [], "second": validations[1]["stable_numeric_lines"] if len(validations)>1 else []}}
    write_json(session.run / "repeat-comparison.json", comparison)
    if validations and validations[0]["status"] == "PASS":
        parameters["2DInferenceV1.4"]["runtime_observed"] = {
            "clock_period_ns_printed": validations[0]["metrics"]["chip_clock_period_ns"],
            "pipeline_cycle_ns_printed": validations[0]["metrics"]["pipeline_cycle_ns"],
            "speedUpDegree": 1,
            "evidence": "Original main stdout clock period; ChipDesignInitialize bounds speedUpDegree to max IFM/min IFM = 1 for this one-layer network. Initial clkFreq is replaced by the simulated clock."}
        write_json(session.run / "parameters.json", parameters)
    success = all(b["status"] == "PASS" for b in build_results.values()) and equal and all(v["status"] == "PASS" for v in validations)
    summary = {"status": "PASS" if success else "PARTIAL", "timestamp_utc": utc(), "run_id": session.run.name,
               "used_original_main": True, "test_driver_used_for_simulation": False,
               "compiler": cxx, "builds": build_results, "parameters": parameters,
               "input_manifest": metadata, "repeat": comparison,
               "runs": [{k: v for k,v in value.items() if k != "stable_numeric_lines"} for value in validations],
               "script_hashes": session.script_hashes,
               "branches_not_run": [branch for branch,_,_ in SNAPSHOTS[1:]],
               "source_patches": [], "rho_tau": "NOT_EVALUATED"}
    write_json(session.run / "smoke-summary.json", summary)
    if os.environ.get("NEUROSIM_EXPORT", "1") == "1":
        write_json(root / "smoke-latest.json", {"run": str(session.run), "status": summary["status"]})
    # Small explicit export whitelist; full logs and binaries remain local.
    if os.environ.get("NEUROSIM_EXPORT", "1") == "1":
        export = management / "results/smoke" / session.run.name
        export.mkdir(exist_ok=False)
        for name in ("smoke-summary.json", "parameters.json", "repeat-comparison.json", "script_hashes.json"):
            write_json(export / name, portable(json.loads((session.run / name).read_text()), root, management))
        key_commands = [c for c in session.commands if any(s in c["log"] for s in ("build-2DInference", "v14-run"))]
        write_json(export / "commands.json", portable(key_commands, root, management))
        for n in (1,2):
            source = session.run / ("v14-run-"+str(n)+".log")
            if source.exists():
                shutil.copy2(source, export / source.name)
        shutil.copytree(session.run / "inputs", export / "inputs")
        write_json(management / "results/smoke/latest.json", {"run_id": session.run.name, "status": summary["status"]})
    print(json.dumps({"status": summary["status"], "run": str(session.run), "builds": {k:v["status"] for k,v in build_results.items()},
                      "repeat": comparison["status"], "metrics": validations[0]["metrics"] if validations else {}}, indent=2))
    if not success:
        raise RuntimeError("Smoke checks did not all pass; inspect " + str(session.run))

def main():
    root, management = bootstrap()
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("setup", "smoke"))
    args = parser.parse_args()
    session = Session(root, args.action)
    try:
        {"setup": setup, "smoke": smoke}[args.action](root, management, session)
    except Exception as exc:
        write_json(session.run / "failure.json", {"status": "FAIL", "error": str(exc), "timestamp_utc": utc()})
        print(str(exc), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
