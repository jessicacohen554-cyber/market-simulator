"""ercot-268 DRIFT BISECT (ZERO LP): where did the ERCOT keeper's re-solve move?

The ercot-mer session re-solved the ERCOT keeper's own recipe at HEAD and did
not reproduce it (``docs/handoffs/RESULT-ercot-mer-keeper-resolve-2026-09-19.md``):
2025 byte-exact, 2021/2022/2024 broad and small, **2023 +6.0 %** on the
load-weighted P1 price. The write-up read the class-energy swaps
(``CC_CHP`` <-> ``CC_REGULAR``, ``CT_CHP`` -> everything) as a plant->class
MAPPING change. That is a hypothesis, not a measurement: a dispatch
reallocation between two adjacent classes looks identical in class-energy
aggregates.

This probe measures it, at zero LP. It rebuilds the keeper's OWN recipe with
``run_year(fleet_only=True)`` at two shas -- the keeper's ``git_sha`` and HEAD
(or any ``--head-sha``) -- sharing ONE ``data/`` tree by symlink so both arms
read identical bytes off disk, and differences can only come from code. Three
layers, narrowest last:

1. **Every LP-visible fleet array**, sha256 over raw bytes. Identical here and
   the fleet build is exonerated: the drift is downstream (LP construction or
   solve), and the mapping-change hypothesis is dead.
2. **The plant->class map itself** -- ``unit_id -> plant_group`` -- as a per-class
   census (unit count, total pmax) AND the exact symmetric difference of each
   class's membership. This is the hypothesis's own object; it answers
   "did CC_CHP lose plants to CC_REGULAR" directly rather than by inference.
3. **The offer surface** ``mc_base`` per class, so a same-membership /
   different-price move is separated from a membership move.

The partition matters and the CAISO ancestor (``_caiso255_gdrift_identity.py``)
had no need of it: the ERCOT keeper is a THREE-config partition (2021-2022
carve-out A, 2023 carve-out B, 2024-2025 forward), so each year is rebuilt under
``replay_keeper.config_partition_overlay``'s own overlay for that year. Without
it a rebuild solves the forward config on a carve-out year -- the ercot-259
defect.

NOT COVERED, deliberately: LP construction and solve. Anything applied after
the ``fleet_only`` exit is invisible here, which is itself informative -- an
"all inputs identical" verdict localizes the drift to exactly that region.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_ercot268_drift_bisect.py
    PYTHONPATH=.:src uv run python scripts/probes/_ercot268_drift_bisect.py \\
        --years 2021 2025 --head-sha 760012f7 --out /tmp/arm.json
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
BUNDLE = REPO / "results/calibration/ercot_mer20260919_five_year"
DEFAULT_OUT = REPO / "results/calibration/_ercot268_drift_bisect.json"
YEARS = (2021, 2022, 2023, 2024, 2025)
T = 8760

#: Every LP-visible fleet array. Exhaustive by intent: a field added here is a
#: field the audit starts defending.
ARRAYS = (
    "unit_ids",
    "mc_base",
    "pmax",
    "pmin",
    "min_gen",
    "availability",
    "heat_rate",
    "emission_rate",
    "nox_rate",
    "so2_rate",
    "vom",
    "zone_idx",
    "fuel_type_idx",
    "plant_code",
    "plant_group",
    "state",
    "ramp10",
    "efficiency_bin",
)

#: Every non-fleet LP input ``run_year`` returns. Renewables are DECISION
#: VARIABLES (rule 3 ``[R-RENEW-VAR]``), so their CF and capacity arrays are LP
#: inputs exactly as much as ``pmax`` is; storage and the fuel-price vector are
#: the same. Hashed alongside ``demand`` so "all inputs identical" means it.
STATE_ARRAYS = (
    "demand",
    "wind_cf",
    "wind_cap",
    "wind_mc",
    "solar_cf",
    "solar_cap",
    "solar_mc",
    "storage_power_cap",
    "fuel_prices",
)

# The child program. Runs INSIDE whichever tree it is pointed at, so one source
# text measures both arms and no divergence can originate in this file.
CHILD = r"""
import contextlib, hashlib, io, json, sys
import numpy as np
sys.path.insert(0, "."); sys.path.insert(0, "scripts"); sys.path.insert(0, "src")
BUNDLE, YEARS = sys.argv[1], [int(y) for y in sys.argv[2].split(",")]
ARRAYS, T = sys.argv[3].split(","), 8760
META_PATH = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else BUNDLE + "/meta.json"
STATE_ARRAYS = sys.argv[5].split(",")

def sha(a):
    if a is None:
        return "NONE"
    if isinstance(a, dict):
        return hashlib.sha256(json.dumps(a, sort_keys=True, default=str).encode()).hexdigest()[:24]
    x = np.asarray(a)
    if x.dtype.kind in "UO":
        return hashlib.sha256("\x1f".join(map(str, x.ravel().tolist())).encode()).hexdigest()[:24]
    return hashlib.sha256(np.ascontiguousarray(x, dtype=float).tobytes()).hexdigest()[:24]

out = {"scenarioconfig_defaults": {}, "constants": {}, "fleet_arrays": {},
       "demand": {}, "class_map": {}, "class_census": {}}

import dataclasses
from market_sim.config.scenarios import ScenarioConfig
out["scenarioconfig_defaults"] = {
    f.name: repr(f.default if f.default is not dataclasses.MISSING else f.default_factory())
    for f in dataclasses.fields(ScenarioConfig)
}

from market_sim.config import constants as C
consts = {}
for k in dir(C):
    if k.startswith("_") or k != k.upper():
        continue
    v = getattr(C, k)
    if callable(v):
        continue
    try:
        consts[k] = hashlib.sha256(json.dumps(v, sort_keys=True, default=str).encode()).hexdigest()[:24]
    except Exception:
        consts[k] = "UNSERIALIZABLE:" + type(v).__name__
out["constants"] = consts

from replay_keeper import (run_year_kwargs, derived_run_year_inputs,
                           config_partition_overlay, apply_config_overlay)
from run_calibration import run_year
from scripts.lib.bundle_fleet import clear_fleet_caches
meta = json.loads(open(META_PATH).read())
for y in YEARS:
    kw = run_year_kwargs(meta); kw.update(derived_run_year_inputs(BUNDLE, y))
    overlay = config_partition_overlay(meta, y)
    apply_config_overlay(kw, overlay)
    clear_fleet_caches()
    with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
        st = run_year(y, meta["iso"], T, float(meta["gas_prices"][str(y)]), {},
                      fleet_only=True, **kw)
    fa = st["fleet_arrays"]
    row = {"n_units": len(fa.unit_ids),
           "overlay_keys": sorted(overlay),
           "overlay_sha": sha(np.array([json.dumps(overlay, sort_keys=True, default=str)]))}
    for name in ARRAYS:
        arr = st["mc_base"] if name == "mc_base" else getattr(fa, name, None)
        row[name + "_sha"] = sha(arr)
    out["fleet_arrays"][str(y)] = row
    out["demand"][str(y)] = {
        name: sha(st.get(name)) for name in STATE_ARRAYS
    }
    out["demand"][str(y)]["demand_shape"] = list(np.shape(st["demand"]))

    # Layer 2/3: the plant->class map and the per-class offer surface.
    groups = (["" ] * len(fa.unit_ids) if fa.plant_group is None
              else [str(g) for g in fa.plant_group])
    out["class_map"][str(y)] = dict(zip(map(str, fa.unit_ids), groups))
    mc = np.asarray(st["mc_base"], dtype=float)
    mc1 = mc.mean(axis=1) if mc.ndim == 2 else mc
    pmax = np.asarray(fa.pmax, dtype=float)
    census = {}
    for i, g in enumerate(groups):
        c = census.setdefault(g, {"n": 0, "pmax": 0.0, "mc_pmax_wt": 0.0})
        c["n"] += 1
        c["pmax"] += float(pmax[i])
        c["mc_pmax_wt"] += float(mc1[i]) * float(pmax[i])
    for g, c in census.items():
        c["pmax"] = round(c["pmax"], 6)
        c["mc_mean_pmax_wt"] = round(c["mc_pmax_wt"] / c["pmax"], 8) if c["pmax"] else None
        del c["mc_pmax_wt"]
    out["class_census"][str(y)] = census

print("@@JSON@@" + json.dumps(out))
"""


def _run_arm(
    tree: Path, label: str, years: tuple[int, ...], meta_path: str = ""
) -> dict:
    """Execute CHILD inside ``tree`` and return its JSON payload."""
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{tree}:{tree / 'src'}:{tree / 'scripts'}"
    env["MARKET_SIM_P1_BASIS_SEED"] = "0"
    # Set/frozenset ``repr`` ordering is hash-salted, so without this three
    # set-valued constants read as "changed" in a self-comparison of one sha.
    env["PYTHONHASHSEED"] = "0"
    print(f"  [{label}] rebuilding in {tree} ...", flush=True)
    p = subprocess.run(
        [
            sys.executable,
            "-c",
            CHILD,
            str(BUNDLE),
            ",".join(map(str, years)),
            ",".join(ARRAYS),
            meta_path,
            ",".join(STATE_ARRAYS),
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
        f"--- stdout tail ---\n{p.stdout[-3000:]}\n"
        f"--- stderr tail ---\n{p.stderr[-4000:]}"
    )


def _diff(a: dict, b: dict) -> dict:
    """Key-wise comparison of two flat dicts -> added / removed / changed."""
    ka, kb = set(a), set(b)
    return {
        "added": sorted(kb - ka),
        "removed": sorted(ka - kb),
        "changed": sorted(k for k in ka & kb if a[k] != b[k]),
    }


def _class_moves(keeper: dict, head: dict) -> dict:
    """Units whose ``plant_group`` differs between the arms, by (from -> to)."""
    moves: dict[str, list[str]] = {}
    for uid, g_keep in keeper.items():
        g_head = head.get(uid, "<ABSENT>")
        if g_head != g_keep:
            moves.setdefault(f"{g_keep} -> {g_head}", []).append(uid)
    for uid in head:
        if uid not in keeper:
            moves.setdefault(f"<ABSENT> -> {head[uid]}", []).append(uid)
    return {k: sorted(v) for k, v in sorted(moves.items())}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--keeper-sha",
        default=None,
        help="the control sha (default: the keeper bundle's own meta.git_sha)",
    )
    ap.add_argument(
        "--head-sha",
        default=None,
        help="the treatment sha (default: the working tree at HEAD, no worktree)",
    )
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    ap.add_argument(
        "--meta",
        default="",
        help=(
            "meta.json to use as the recipe for BOTH arms (default: the "
            "bundle's own). Point it at the SUPERSEDED keeper's meta to "
            "difference two code shas on one unchanged recipe."
        ),
    )
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    a = ap.parse_args()

    meta = json.loads(
        Path(a.meta).read_text() if a.meta else (BUNDLE / "meta.json").read_text()
    )
    keeper_sha = a.keeper_sha or meta["git_sha"]
    head_sha = (
        a.head_sha
        or subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True
        ).stdout.strip()
    )
    years = tuple(a.years)
    print(
        f"ercot-268 drift bisect: {keeper_sha} -> {head_sha[:12]}  years={years}",
        flush=True,
    )

    with tempfile.TemporaryDirectory(prefix="ercot268_") as tmp:
        trees: dict[str, Path] = {}
        made: list[Path] = []
        for label, sha_ in (("keeper", keeper_sha), ("head", head_sha)):
            if label == "head" and a.head_sha is None:
                trees[label] = REPO
                continue
            wt = Path(tmp) / f"{label}_tree"
            subprocess.run(
                ["git", "worktree", "add", "--detach", "--no-checkout", str(wt), sha_],
                cwd=REPO,
                check=True,
                capture_output=True,
            )
            made.append(wt)
            # Code only: the DATA tree is shared by symlink, so both arms read
            # identical bytes and any difference must come from the code.
            subprocess.run(
                ["git", "sparse-checkout", "set", "--no-cone", "src/", "scripts/"],
                cwd=wt,
                check=True,
                capture_output=True,
            )
            subprocess.run(["git", "checkout"], cwd=wt, check=True, capture_output=True)
            for shared in ("data", "results", "config", "configs", "pyproject.toml"):
                src = REPO / shared
                if src.exists() and not (wt / shared).exists():
                    (wt / shared).symlink_to(src)
            trees[label] = wt
        try:
            meta_path = str(Path(a.meta).resolve()) if a.meta else ""
            keeper = _run_arm(trees["keeper"], "keeper", years, meta_path)
            head = _run_arm(trees["head"], "head", years, meta_path)
        finally:
            for wt in made:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(wt)],
                    cwd=REPO,
                    capture_output=True,
                )

    cfg = _diff(keeper["scenarioconfig_defaults"], head["scenarioconfig_defaults"])
    consts = _diff(keeper["constants"], head["constants"])

    arrays_identical, mismatches = True, []
    per_year: dict[str, dict] = {}
    for y in map(str, years):
        row: dict = {"array_mismatches": []}
        for k, v in head["fleet_arrays"][y].items():
            if keeper["fleet_arrays"][y].get(k) != v:
                arrays_identical = False
                row["array_mismatches"].append(k)
                mismatches.append(f"{y}.{k}")
        for k, v in head["demand"][y].items():
            if keeper["demand"][y].get(k) != v:
                arrays_identical = False
                row["array_mismatches"].append(k)
                mismatches.append(f"{y}.{k}")
        row["class_moves"] = _class_moves(keeper["class_map"][y], head["class_map"][y])
        row["n_units_moved"] = sum(len(v) for v in row["class_moves"].values())
        census_delta = {}
        ck, ch = keeper["class_census"][y], head["class_census"][y]
        for g in sorted(set(ck) | set(ch)):
            k_, h_ = ck.get(g, {}), ch.get(g, {})
            if k_ != h_:
                census_delta[g] = {"keeper": k_, "head": h_}
        row["class_census_delta"] = census_delta
        per_year[y] = row

    res = {
        "session": "ercot-268",
        "what": (
            "Every LP INPUT the ERCOT keeper's recipe builds, measured at the "
            "keeper sha and at a treatment sha on one shared data tree, plus the "
            "plant->class map and the per-class offer surface"
        ),
        "bundle": str(BUNDLE.relative_to(REPO)),
        "keeper_sha": keeper_sha,
        "head_sha": head_sha,
        "years": list(years),
        "method": (
            "two run_year(fleet_only=True) rebuilds per year on the keeper's OWN "
            "recipe (meta + derived_run_year_inputs + the year's "
            "config_partition_overlay), market_sim imported from a sparse "
            "worktree at each sha, data/ shared by symlink, differenced by "
            "sha256 over raw bytes."
        ),
        "not_covered": "LP construction and solve, and anything after the fleet_only exit.",
        "scenarioconfig_defaults": cfg,
        "constants": consts,
        "per_year": per_year,
        "fleet_arrays": {
            "keeper": keeper["fleet_arrays"],
            "head": head["fleet_arrays"],
        },
        "class_census": {
            "keeper": keeper["class_census"],
            "head": head["class_census"],
        },
        "state_arrays": {"keeper": keeper["demand"], "head": head["demand"]},
        "mismatches": mismatches,
        "verdict": "ALL LP INPUTS BIT-IDENTICAL"
        if arrays_identical
        else "INPUTS DIFFER",
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")

    print(f"\nScenarioConfig defaults: changed={cfg['changed'] or 'NONE'}")
    print(f"  added={len(cfg['added'])} removed={len(cfg['removed'])}")
    print(
        f"constants: changed={consts['changed'] or 'NONE'} added={len(consts['added'])}"
    )
    for y, row in per_year.items():
        print(
            f"\n{y}: array mismatches={row['array_mismatches'] or 'NONE'} | "
            f"units re-classed={row['n_units_moved']}"
        )
        for move, uids in row["class_moves"].items():
            print(f"    {move}: {len(uids)} unit(s)  e.g. {uids[:6]}")
        for g, d in row["class_census_delta"].items():
            print(f"    census {g!r}: keeper={d['keeper']} head={d['head']}")
    print(f"\nVERDICT: {res['verdict']}")
    print(f"wrote {a.out}")
    sys.exit(0 if arrays_identical else 1)


if __name__ == "__main__":
    main()
