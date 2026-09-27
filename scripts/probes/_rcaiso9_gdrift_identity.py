"""R-CAISO-9 G-DRIFT (ZERO LP): what does caiso_import_cap_floor_static move?

Adapted from ``_rcaiso8_gdrift_identity.py`` (see ``_rcaiso6_gdrift_identity.py``
for the method). Three arms share one ``data/`` tree: the keeper pin ``ee309e39``
(sparse worktree, flag absent), the working tree with the flag OFF, and the
working tree with the flag ON (``--set caiso_import_cap_floor_static=true``
through the same ``prb_overrides`` channel replay_keeper uses). Covers the keeper
``rcaiso8_A_span`` (2022-2025) and its fold ``rcaiso8_A_tp_2019_2021``
(2019-2021), both solved at ``ee309e39``.

Expectation (PRECOMMIT-r-caiso-9 §3): off -> on moves ONLY the 2019-21
``SP15_rest -> SDGE`` link TTC (386 / 718 / 635 -> 1,436 MW); nothing in
2022-25. pin -> off moves nothing.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_rcaiso9_gdrift_identity.py
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
BUNDLES = {
    "rcaiso8_A_span": (2022, 2023, 2024, 2025),
    "rcaiso8_A_tp_2019_2021": (2019, 2020, 2021),
}
PIN = "ee309e39170be7641494a3bdc0b5863fc82d141c"
#: Each bundle's own solve sha (both legs solved at the R-CAISO-8 pin).
PIN_BY_BUNDLE = {"rcaiso8_A_span": PIN, "rcaiso8_A_tp_2019_2021": PIN}
FLAG = "caiso_import_cap_floor_static"
DEFAULT_OUT = REPO / "results/calibration/_rcaiso9/gdrift_input_identity.json"
T = 8760
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
    "plant_group",
    "fuel_type_idx",
    "zone_idx",
    "plant_code",
    "nox_rate",
)

CHILD = r"""
import contextlib, hashlib, io, json, sys
import numpy as np
sys.path.insert(0, "."); sys.path.insert(0, "scripts"); sys.path.insert(0, "src")
BUNDLE, YEARS, T = sys.argv[1], [int(y) for y in sys.argv[2].split(",")], 8760
ARRAYS = sys.argv[3].split(",")
OVR = json.loads(sys.argv[4])

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
    if OVR:
        kw.setdefault("prb_overrides", {}); kw["prb_overrides"].update(OVR)
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
    ic = st["iso_config"]
    links = sorted((l.from_zone, l.to_zone, float(l.ttc_mw)) for l in ic.links)
    lims = sorted((lim.name, repr(lim)) for lim in getattr(ic, "interface_limits", []))
    out["topology"] = out.get("topology", {})
    out["topology"][str(y)] = {"links_sha": hashlib.sha256(repr(links).encode()).hexdigest()[:24],
        "limits_sha": hashlib.sha256(repr(lims).encode()).hexdigest()[:24],
        "links": links, "limits": [l[1][:300] for l in lims]}

print("@@JSON@@" + json.dumps(out))
"""


def _run_arm(tree: Path, bundle: str, years, label: str, ovr: dict) -> dict:
    """Execute CHILD inside ``tree`` for one bundle; return its JSON payload."""
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{tree}:{tree / 'src'}:{tree / 'scripts'}"
    print(f"  [{label}] {bundle} in {tree} ...", flush=True)
    p = subprocess.run(
        [
            sys.executable,
            "-c",
            CHILD,
            str(REPO / "results/calibration" / bundle),
            ",".join(map(str, years)),
            ",".join(ARRAYS),
            json.dumps(ovr),
        ],
        cwd=tree,
        env=env,
        capture_output=True,
        text=True,
    )
    for line in p.stdout.splitlines():
        if line.startswith("@@JSON@@"):
            return json.loads(line[len("@@JSON@@") :])
    raise SystemExit(f"[{label}] no payload rc={p.returncode}\n{p.stderr[-3000:]}")


def _worktree(sha: str, name: str) -> Path:
    """Sparse worktree (src + scripts) at ``sha`` sharing this repo's data/."""
    wt = Path(tempfile.gettempdir()) / f"rcaiso9_wt_{name}"
    if not wt.exists():
        subprocess.run(
            ["git", "worktree", "add", "--no-checkout", "--detach", str(wt), sha],
            cwd=REPO,
            check=True,
        )
        subprocess.run(
            ["git", "sparse-checkout", "set", "src", "scripts", "configs"],
            cwd=wt,
            check=True,
        )
        subprocess.run(["git", "checkout", "--detach", sha], cwd=wt, check=True)
        for d in ("data", "results"):
            (wt / d).symlink_to(REPO / d)
    return wt


def main() -> None:
    """Rebuild every keeper year in three arms and report the differences."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    a = ap.parse_args()
    arms = {
        "pin": (None, {}),
        "off": (REPO, {}),
        "on": (REPO, {FLAG: True}),
    }
    res = {k: {} for k in arms}
    for label, (tree, ovr) in arms.items():
        for bundle, years in BUNDLES.items():
            t = tree
            if t is None:
                sha = PIN_BY_BUNDLE[bundle]
                t = _worktree(sha, f"pin_{sha}")
            res[label][bundle] = _run_arm(t, bundle, years, label, ovr)
    report = {"pin": PIN_BY_BUNDLE, "flag": FLAG, "pairs": {}}
    for x, y in (("pin", "off"), ("off", "on")):
        pr = {}
        for bundle, years in BUNDLES.items():
            A, B = res[x][bundle], res[y][bundle]
            for yr in map(str, years):
                fa, fb = A["fleet_arrays"][yr], B["fleet_arrays"][yr]
                diff = sorted(k for k in fa if fa.get(k) != fb.get(k))
                if A["demand"][yr] != B["demand"][yr]:
                    diff.append("demand")
                ta, tb = A["topology"][yr], B["topology"][yr]
                if ta["links_sha"] != tb["links_sha"]:
                    diff.append(
                        "links: "
                        + repr(
                            sorted(
                                set(map(tuple, tb["links"]))
                                ^ set(map(tuple, ta["links"]))
                            )
                        )
                    )
                if ta["limits_sha"] != tb["limits_sha"]:
                    diff.append(
                        "limits: "
                        + repr(sorted(set(tb["limits"]) ^ set(ta["limits"])))[:1500]
                    )
                pr[yr] = diff
        dflt = [
            k
            for k in res[x]["rcaiso8_A_span"]["scenarioconfig_defaults"]
            if res[x]["rcaiso8_A_span"]["scenarioconfig_defaults"][k]
            != res[y]["rcaiso8_A_span"]["scenarioconfig_defaults"].get(k)
        ]
        added = sorted(
            set(res[y]["rcaiso8_A_span"]["scenarioconfig_defaults"])
            - set(res[x]["rcaiso8_A_span"]["scenarioconfig_defaults"])
        )
        cons = sorted(
            k
            for k in set(res[x]["rcaiso8_A_span"]["constants"])
            | set(res[y]["rcaiso8_A_span"]["constants"])
            if res[x]["rcaiso8_A_span"]["constants"].get(k)
            != res[y]["rcaiso8_A_span"]["constants"].get(k)
        )
        report["pairs"][f"{x}->{y}"] = {
            "per_year_diffs": pr,
            "defaults_changed": dflt,
            "fields_added": added,
            "constants_changed": cons,
        }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
