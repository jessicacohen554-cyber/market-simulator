#!/usr/bin/env python3
"""Run a python script in-process and report its true peak RSS (VmHWM).

PERF-A probe helper (NOT-FOR-MERGE): GitHub runners ship no GNU time, so
``/usr/bin/time -v`` is unavailable; VmHWM from /proc/self/status is the
kernel's high-water mark for this process and costs nothing.

Usage: python rss_wrap.py <script.py> [args...]
"""

import runpy
import sys
import time


def _vm(field: str) -> float:
    with open("/proc/self/status") as f:
        for ln in f:
            if ln.startswith(field + ":"):
                return int(ln.split()[1]) / 2**20  # kB -> GiB
    return 0.0


def main() -> int:
    script, argv = sys.argv[1], sys.argv[2:]
    sys.argv = [script, *argv]
    t0 = time.time()
    code = 0
    try:
        runpy.run_path(script, run_name="__main__")
    except SystemExit as e:  # scripts exit via SystemExit(main())
        code = int(e.code or 0)
    wall = time.time() - t0
    print(
        f"[rss_wrap] wall {wall:.1f} s, peak RSS (VmHWM) {_vm('VmHWM'):.2f} GiB, "
        f"final RSS {_vm('VmRSS'):.2f} GiB, exit {code}",
        flush=True,
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
