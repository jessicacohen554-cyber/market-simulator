"""soco-68 G-DRIFT (ZERO LP): is the SOCO keeper's LP INPUT bit-identical at HEAD? (adapted from _caiso255_gdrift_identity.py)

Rule 29 ``[R-SCREEN]`` clause (b) admits two classifications for a hunk on the
backcast path and neither is "probably fine": **INERT with its reason cited**,
or **LIVE, and it earns a control solve**. Reading 50+ files of diff to argue
the first is slow, and it gets slower every hour ``main`` advances. This probe
replaces the reading with a measurement, and it is the measurement that binds:
per ``PRECOMMIT-caiso255 §6.2`` the audit that counts is the one against the sha
**the arm is solved at**, so this has to be cheap enough to re-run at solve time.

Three instruments, strongest last:

1. **Every ``ScenarioConfig`` default, both shas.** A field whose default moved
   can change any run that does not name it. A field *added* is harmless only if
   the keeper's recipe does not carry it — reported either way.
2. **Every top-level constant, both shas**, compared BY VALUE. Rule 5
   ``[R-NO-MAGIC]`` puts every number here, so a changed value is a changed model
   unless something downstream gates it off.
3. **The LP's actual inputs, rebuilt at both shas.** Two ``fleet_only`` rebuilds
   per year on the keeper's OWN recipe, ``market_sim`` imported from a sparse
   worktree at the keeper sha in one arm and from HEAD in the other, sharing ONE
   ``data/`` tree by symlink so both read identical bytes off disk. Differenced
   on every LP-visible array by sha256 over the raw bytes.

Instrument 3 subsumes 1 and 2 on everything that reaches the fleet build: a
constant that moved but cannot reach the arrays is settled empirically rather
than argued. What it does NOT cover is LP **construction** and **solve** — those
stay a reading, on the keeper's own committed flags.

NOT COVERED BY CONSTRUCTION, and deliberately: anything applied AFTER the
``fleet_only`` exit. The P1-only conditional offer markup is the CAISO case
(``run_calibration.py`` builds it after the exit), which is why the phase-0
footprint probe rebuilds it separately.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_soco67_gdrift_identity.py
    PYTHONPATH=.:src uv run python scripts/probes/_soco67_gdrift_identity.py \
        --keeper-sha fa23c1f7 --out results/calibration/_soco67_gdrift_at_solve.json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/soco67_span"  # soco-68: the soco-67 keeper
DEFAULT_OUT = REPO / "results/calibration/_soco68/gdrift_input_identity.json"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
T = 8760

#: Every LP-visible fleet array. A field added here is a field the audit starts
#: defending; a field removed is one it stops. Keep it exhaustive.
ARRAYS = (
    "unit_ids",
    "mc_base",
    "pmax",
    "pmin",
    "min_gen",
    "availability",
    "heat_rate",
    "emission_rate",
    "vom",
    # soco-68: LABELS too. soco-67 hashed only numeric LP arrays and so could
    # not see the COAL-SUB relabel (bare COAL -> COAL_BIT) that moved its
    # 2019/2020 class rows; class reporting reads these.
    "plant_group",
    "fuel_type_idx",
    "zone_idx",
    "plant_code",
    "nox_rate",
)

# The child program. Runs INSIDE whichever tree it is pointed at, so the same
# source text measures both arms and no divergence can come from this file.
CHILD = r"""
import contextlib, hashlib, io, json, sys
import numpy as np
sys.path.insert(0, "."); sys.path.insert(0, "scripts"); sys.path.insert(0, "src")
BUNDLE, YEARS, T = sys.argv[1], [int(y) for y in sys.argv[2].split(",")], 8760
ARRAYS = sys.argv[3].split(",")

def sha(a):
    x = np.asarray(a)
    if x.dtype.kind in "UO":
        return hashlib.sha256("\x1f".join(map(str, x.tolist())).encode()).hexdigest()[:24]
    return hashlib.sha256(np.ascontiguousarray(x, dtype=float).tobytes()).hexdigest()[:24]

out = {"scenarioconfig_defaults": {}, "constants": {}, "fleet_arrays": {}, "demand": {}}

# --- instrument 1: every ScenarioConfig default -----------------------------
import dataclasses
from market_sim.config.scenarios import ScenarioConfig
out["scenarioconfig_defaults"] = {
    f.name: repr(f.default if f.default is not dataclasses.MISSING else f.default_factory())
    for f in dataclasses.fields(ScenarioConfig)
}

# --- instrument 2: every top-level constant, by value -----------------------
from market_sim.config import constants as C
consts = {}
for k in dir(C):
    if k.startswith("_") or k != k.upper():
        continue
    v = getattr(C, k)
    if callable(v):
        continue
    try:
        consts[k] = hashlib.sha256(
            json.dumps(v, sort_keys=True, default=str).encode()
        ).hexdigest()[:24]
    except Exception:
        consts[k] = "UNSERIALIZABLE:" + type(v).__name__
out["constants"] = consts

# --- instrument 3: the LP's actual inputs -----------------------------------
from replay_keeper import derived_run_year_inputs, run_year_kwargs
from run_calibration import run_year
from scripts.lib.bundle_fleet import clear_fleet_caches
meta = json.loads(open(BUNDLE + "/meta.json").read())
for y in YEARS:
    kw = run_year_kwargs(meta); kw.update(derived_run_year_inputs(BUNDLE, y))
    clear_fleet_caches()
    with contextlib.redirect_stderr(io.StringIO()):
        st = run_year(y, meta["iso"], T, float(meta["gas_prices"][str(y)]), {},
                      fleet_only=True, **kw)
    fa = st["fleet_arrays"]
    row = {"n_units": len(fa.unit_ids)}
    for name in ARRAYS:
        arr = st["mc_base"] if name == "mc_base" else getattr(fa, name)
        row[name + "_sha"] = sha(arr)
    out["fleet_arrays"][str(y)] = row
    out["demand"][str(y)] = {"sha": sha(st["demand"]), "shape": list(np.shape(st["demand"]))}

print("@@JSON@@" + json.dumps(out))
"""


def _run_arm(tree: Path, label: str) -> dict:
    """Execute CHILD inside ``tree`` and return its JSON payload."""
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{tree}:{tree / 'src'}:{tree / 'scripts'}"
    env["MARKET_SIM_P1_BASIS_SEED"] = "0"
    print(f"  [{label}] rebuilding in {tree} ...", flush=True)
    p = subprocess.run(
        [
            sys.executable,
            "-c",
            CHILD,
            str(BUNDLE),
            ",".join(map(str, YEARS)),
            ",".join(ARRAYS),
        ],
        cwd=tree,
        env=env,
        capture_output=True,
        text=True,
    )
    tag = "@@JSON@@"
    for line in p.stdout.splitlines():
        if line.startswith(tag):
            return json.loads(line[len(tag) :])
    raise SystemExit(
        f"[{label}] child produced no payload (rc={p.returncode})\n"
        f"--- stdout tail ---\n{p.stdout[-2000:]}\n--- stderr tail ---\n{p.stderr[-3000:]}"
    )


def _diff(a: dict, b: dict) -> dict:
    """Key-wise comparison of two flat dicts -> added / removed / changed."""
    ka, kb = set(a), set(b)
    return {
        "added": sorted(kb - ka),
        "removed": sorted(ka - kb),
        "changed": sorted(k for k in ka & kb if a[k] != b[k]),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--keeper-sha",
        default=None,
        help="the control sha (default: the keeper bundle's own meta.git_sha)",
    )
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    a = ap.parse_args()

    meta = json.loads((BUNDLE / "meta.json").read_text())
    keeper_sha = a.keeper_sha or meta["git_sha"]
    head_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True
    ).stdout.strip()
    print(f"G-DRIFT identity: keeper {keeper_sha} -> HEAD {head_sha[:8]}", flush=True)

    with tempfile.TemporaryDirectory(prefix="soco68_gdrift_") as tmp:
        wt = Path(tmp) / "keeper_tree"
        subprocess.run(
            [
                "git",
                "worktree",
                "add",
                "--detach",
                "--no-checkout",
                str(wt),
                keeper_sha,
            ],
            cwd=REPO,
            check=True,
            capture_output=True,
        )
        try:
            # Code only: the DATA tree is shared by symlink below, so both arms
            # read identical bytes and any difference must come from the code.
            subprocess.run(
                ["git", "sparse-checkout", "set", "--no-cone", "src/", "scripts/"],
                cwd=wt,
                check=True,
                capture_output=True,
            )
            subprocess.run(["git", "checkout"], cwd=wt, check=True, capture_output=True)
            for shared in ("data", "results", "config", "configs"):
                src = REPO / shared
                if src.exists() and not (wt / shared).exists():
                    (wt / shared).symlink_to(src)

            keeper = _run_arm(wt, "keeper")
            head = _run_arm(REPO, "HEAD")
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(wt)],
                cwd=REPO,
                capture_output=True,
            )

    cfg = _diff(keeper["scenarioconfig_defaults"], head["scenarioconfig_defaults"])
    cfg["note"] = (
        f"{len(keeper['scenarioconfig_defaults'])} -> "
        f"{len(head['scenarioconfig_defaults'])} fields compared by value"
    )
    cfg["existing_fields_changed"] = cfg.pop("changed")
    cfg["fields_added"], cfg["fields_removed"] = cfg.pop("added"), cfg.pop("removed")

    consts = _diff(keeper["constants"], head["constants"])
    consts["note"] = (
        f"{len(keeper['constants'])} -> {len(head['constants'])} top-level "
        "constants compared by value"
    )

    arrays_identical, mismatches = True, []
    for y in map(str, YEARS):
        for k, v in head["fleet_arrays"][y].items():
            if keeper["fleet_arrays"][y].get(k) != v:
                arrays_identical = False
                mismatches.append(f"{y}.{k}")
        if keeper["demand"][y] != head["demand"][y]:
            arrays_identical = False
            mismatches.append(f"{y}.demand")

    res = {
        "session": "soco-68",
        "what": (
            "G-DRIFT under rule 29(b): every LP INPUT the keeper's recipe builds, "
            "measured at the keeper sha and at HEAD, on one shared data tree"
        ),
        "keeper_sha": keeper_sha,
        "head_sha": head_sha,
        "method": (
            "two fleet_only rebuilds per year on the keeper's OWN recipe (bundle "
            "soco67_span meta + derived_run_year_inputs), market_sim "
            "imported from a sparse worktree at the keeper sha in one arm and "
            "from HEAD in the other, differenced by sha256 over the raw bytes of "
            "every LP-visible array. Data dir shared by symlink so both arms read "
            "identical bytes on disk."
        ),
        "not_covered": (
            "LP CONSTRUCTION and SOLVE, and anything applied after the fleet_only "
            "exit (the P1-only conditional offer markup is the CAISO case). Those "
            "are closed on the keeper's own committed flags, not by this probe."
        ),
        "scenarioconfig_defaults": cfg,
        "constants": consts,
        "fleet_arrays": {
            "keeper": keeper["fleet_arrays"],
            "head": head["fleet_arrays"],
        },
        "demand": {"keeper": keeper["demand"], "head": head["demand"]},
        "mismatches": mismatches,
        "verdict": (
            "ALL LP INPUTS BIT-IDENTICAL" if arrays_identical else "INPUTS DIFFER"
        ),
    }
    a.out.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")

    print(f"\nScenarioConfig: {cfg['note']}")
    print(f"  existing defaults CHANGED: {cfg['existing_fields_changed'] or 'NONE'}")
    print(f"  added: {cfg['fields_added'] or 'none'}")
    print(f"constants: {consts['note']}")
    print(
        f"  CHANGED: {consts['changed'] or 'NONE'}   added: {consts['added'] or 'none'}"
    )
    print(f"\nVERDICT: {res['verdict']}")
    if mismatches:
        print(f"  MISMATCHES: {mismatches}")
    print(f"wrote {a.out}")
    sys.exit(0 if arrays_identical else 1)


if __name__ == "__main__":
    main()
