"""caiso-256 (ZERO LP): operationalize the rule-29 screen's S-1 "implied displacement".

PRECOMMIT-caiso255 §7.2 / ADDENDUM-caiso254 §3.2 register S-1 as "CT_PEAKER
energy RISES, within a factor of 3 of the displacement F(y) implies" but leave
"implies" unquantified. This probe fixes the quantity BEFORE the screen solve
so the gate cannot be read to fit its result:

    dE_implied = sum_i pmax_i * #{ t : mc_new_i <= lambda_{z(i),t} < mc_old_i }   [MWh]

over every CT_PEAKER tranche i whose P0 offer FALLS under the repair, where
lambda is the KEEPER's committed P1 zonal price (``system_<year>.parquet``) and
(mc_old, mc_new) are the tranche's assembled ``mc_base`` on the frozen
(``fa23c1f7``) and the repaired (HEAD) artifact pair — i.e. the hours in which
the keeper's own price already sat between the tranche's old and new offer, so
that at the new offer the tranche is in merit where it was not. It is a
first-order, price-held-fixed estimate — the reason the gate carries a factor
of 3 both ways.

Both rebuilds are the keeper's own ``fleet_only`` recipe with only the two
artifact files swapped on disk (the caiso-255 phase-0 seam). HEAD's artifacts
are restored on exit whatever happens.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_caiso256_s1_implied_displacement.py --year 2023
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

BUNDLE = REPO / "results/calibration/caiso252_b1_notrim"
OUT = REPO / "results/calibration/_caiso256_s1_implied_displacement.json"
KEEPER_SHA = "fa23c1f7"
VSRC = "data/raw/_validation-source"
ARTIFACTS = (
    f"{VSRC}/caiso_offer_curve_measured.json",
    f"{VSRC}/caiso_offer_surface_condbinned.json",
    f"{VSRC}/caiso_offer_surface_summary.csv",
)
T = 8760
TARGET = "CT_PEAKER"


def _git_show(sha: str, path: str) -> bytes:
    return subprocess.run(["git", "show", f"{sha}:{path}"], cwd=REPO, check=True, capture_output=True).stdout


def _rebuild(year: int) -> dict:
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(str(BUNDLE), year))
    clear_fleet_caches()
    with contextlib.redirect_stderr(io.StringIO()):
        st = run_year(year, meta["iso"], T, float(meta["gas_prices"][str(year)]), {}, fleet_only=True, **kw)
    fa = st["fleet_arrays"]
    fleet = st["fleet"]
    units = list(getattr(fleet, "generators", fleet))
    # class label per LP row: prefer a FleetArrays vector, else the unit object
    klass = None
    for name in ("klass", "plant_group", "group", "offer_group", "bin_group", "unit_class"):
        if hasattr(fa, name):
            klass = np.asarray(getattr(fa, name)).astype(str)
            break
    if klass is None:
        for name in ("klass", "group", "offer_group", "bin_group"):
            if units and hasattr(units[0], name):
                klass = np.array([str(getattr(u, name)) for u in units])
                break
    zone = None
    for name in ("zone_idx", "zone_index", "zone_ids", "zone"):
        if hasattr(fa, name):
            zone = np.asarray(getattr(fa, name))
            break
    if zone is None and units and hasattr(units[0], "zone"):
        zone = np.array([str(getattr(u, "zone")) for u in units])
    if klass is None or zone is None:
        raise SystemExit(f"no class/zone vector found; FleetArrays fields: {[k for k in dir(fa) if not k.startswith('_')]}")
    return {
        "unit_ids": np.asarray(fa.unit_ids).astype(str),
        "mc": np.asarray(st["mc_base"], dtype=float),
        "pmax": np.asarray(fa.pmax, dtype=float),
        "klass": klass,
        "zone": zone,
        "zone_names": list(getattr(st.get("config"), "zone_names", []) or []),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--year", type=int, default=2023)
    a = ap.parse_args()
    y = a.year

    head_bytes = {p: (REPO / p).read_bytes() for p in ARTIFACTS}
    try:
        for p in ARTIFACTS:
            (REPO / p).write_bytes(_git_show(KEEPER_SHA, p))
        frozen = _rebuild(y)
        for p, b in head_bytes.items():
            (REPO / p).write_bytes(b)
        repaired = _rebuild(y)
    finally:
        for p, b in head_bytes.items():
            (REPO / p).write_bytes(b)
        subprocess.run(["git", "status", "--short", VSRC], cwd=REPO)

    if not np.array_equal(frozen["unit_ids"], repaired["unit_ids"]):
        raise SystemExit("unit_ids differ between the two rebuilds — the swap moved the fleet, not the offer")
    mc_old, mc_new, pmax, klass, zone = frozen["mc"], repaired["mc"], repaired["pmax"], repaired["klass"], repaired["zone"]
    if mc_old.ndim == 2:  # (n_gen, T) — take the annual mean offer per tranche for the band, keep hourly for the count
        pass

    s = pd.read_parquet(BUNDLE / f"hourly/system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    lam = s.pivot_table(index="hour", columns="zone", values="price").reindex(range(T))
    zone_cols = list(lam.columns)

    def zone_name(z) -> str:
        if isinstance(z, (int, np.integer)):
            names = repaired["zone_names"] or zone_cols
            return str(names[int(z)])
        return str(z)

    tgt = klass == TARGET
    fell = tgt & ((mc_new.mean(axis=-1) if mc_new.ndim == 2 else mc_new) < (mc_old.mean(axis=-1) if mc_old.ndim == 2 else mc_old) - 1e-9)
    rows = []
    de = 0.0
    for i in np.flatnonzero(fell):
        zn = zone_name(zone[i])
        if zn not in lam.columns:
            continue
        lz = lam[zn].to_numpy(dtype=float)
        lo = mc_new[i] if mc_new.ndim == 1 else mc_new[i]
        hi = mc_old[i] if mc_old.ndim == 1 else mc_old[i]
        n = int(np.sum((lz >= lo) & (lz < hi)))
        e = float(pmax[i]) * n
        de += e
        rows.append({"unit": str(repaired["unit_ids"][i]), "zone": zn, "pmax": float(pmax[i]),
                     "mc_old": float(np.mean(hi)), "mc_new": float(np.mean(lo)), "hours_in_band": n, "mwh": e})
    # POST-HOC, REPORTED ONLY (added after the 2023 screen was scored; never a
    # gate): the same count with at most ONE tranche's worth of MW per
    # (plant, hour), so sibling tranches of one plant whose bands all contain
    # lambda are not counted five times over. Recorded for an owner re-charter,
    # not for this session's verdict, which stays on the registered count.
    plant_hours: dict[str, np.ndarray] = {}
    plant_cap: dict[str, float] = {}
    for i in np.flatnonzero(fell):
        zn = zone_name(zone[i])
        if zn not in lam.columns:
            continue
        pkey = str(repaired["unit_ids"][i]).split("_econ")[0].split("_peak")[0].split("_comm")[0]
        lz = lam[zn].to_numpy(dtype=float)
        hit = ((lz >= mc_new[i]) & (lz < mc_old[i])).astype(float) * float(pmax[i])
        plant_hours[pkey] = np.maximum(plant_hours.get(pkey, np.zeros(T)), hit)
        plant_cap[pkey] = max(plant_cap.get(pkey, 0.0), float(pmax[i]))
    de_dedup = float(sum(v.sum() for v in plant_hours.values()))
    n_tgt = int(tgt.sum())
    rose = int((tgt & ((mc_new.mean(axis=-1) if mc_new.ndim == 2 else mc_new) > (mc_old.mean(axis=-1) if mc_old.ndim == 2 else mc_old) + 1e-9)).sum())
    res = {
        "session": "caiso-256", "year": y, "target_class": TARGET,
        "definition": "dE_implied = sum_i pmax_i * #{t: mc_new_i <= lambda_z(i),t < mc_old_i} over CT_PEAKER tranches whose P0 offer fell; lambda = keeper committed P1 zonal price; first-order, price held fixed",
        "n_target_tranches": n_tgt, "n_fell": int(fell.sum()), "n_rose": rose,
        "dE_implied_gwh": round(de / 1e3, 3),
        "POST_HOC_reported_only_dE_plant_dedup_gwh": round(de_dedup / 1e3, 3),
        "POST_HOC_n_plants": len(plant_hours),
        "S1_band_gwh": [round(de / 3e3, 3), round(3 * de / 1e3, 3)],
        "keeper_ct_peaker_twh": None,
        "top_rows": sorted(rows, key=lambda r: -r["mwh"])[:12],
    }
    ch = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{y}.parquet")
    ch = ch[(ch["pass"] == "P1") & (ch.klass == TARGET)]
    res["keeper_ct_peaker_twh"] = round(float(ch.mw.sum()) / 1e6, 4)
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "top_rows"}, indent=1))
    for r in res["top_rows"][:6]:
        print(r)


if __name__ == "__main__":
    main()
