#!/usr/bin/env python3
"""Read-only toolchain/device snapshot. Local JSON is intentionally gitignored."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]

def cmd(args, timeout=8):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return {"cmd": args, "rc": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError) as e:
        return {"cmd": args, "error": type(e).__name__ + ": " + str(e)[:200]}

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--node", choices=("halo", "node1"), required=True)
    a.add_argument("--output", type=Path)
    args = a.parse_args()
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    payload = {
        "node": args.node,
        "captured_at_utc": now,
        "os": platform.platform(),
        "kernel": platform.release(),
        "python": sys.version,
        "hardware_expected": "gfx1151 Radeon 8060S" if args.node == "halo" else "2x RTX 3090 sm_86",
        "device_nodes_accessible": {dev: Path(dev).exists() and os.access(dev, os.R_OK | os.W_OK)
                                    for dev in ("/dev/kfd", "/dev/dri")},
        "render_nodes": {str(dev): os.access(dev, os.R_OK | os.W_OK) for dev in Path("/dev/dri").glob("renderD*")},
        "commands": {},
    }
    lookups = {
        "lscpu": ["lscpu"],
        "gpu_pci": ["lspci", "-nn"],
        "rocm_smi": ["rocm-smi", "--showproductname", "--showuse", "--showmemuse", "--showpids"],
        "rocminfo": ["rocminfo"],
        "hipcc": ["hipcc", "--version"],
        "nvidia_smi": ["nvidia-smi", "--query-gpu=index,name,compute_cap,driver_version,memory.total,memory.used,utilization.gpu", "--format=csv"],
        "nvcc": ["nvcc", "--version"],
        "git": ["git", "--version"],
        "gpu_processes": ["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,used_memory", "--format=csv"],
        "memory": ["free", "-h"],
        "disk": ["df", "-h", str(BASE)],
        "process_usage": ["ps", "-eo", "comm,pcpu,pmem", "--sort=-pcpu"],
    }
    for name, command in lookups.items():
        payload["commands"][name] = cmd(command)
    out = args.output or BASE / "results" / f"inventory_{args.node}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved (local / untracked): {out}")
    if args.node == "halo":
        print("Verify *observed* gfx1151 and Radeon 8060S; W7900 should NOT be selected by default.")
    else:
        print("Verify actual available RTX 3090 and obtain permission before GPU compute.")

if __name__ == "__main__":
    main()
