"""NYISO-NEXT-18 phase 0 (ZERO LP): what sets Upstate_West's price in CE-binding hours.

The owner's question: is the 2021 Upstate_West over-pricing a LINK that is too loose,
or an upstate SUPPLY STACK priced too high? Reads only committed artifacts:

* the keeper's P1 hourlies (``results/calibration/nyisonext16_{2021,span}/hourly``);
* the keeper's registered run payloads (``frontend/data/backcast/runs/<id>.js``,
  per-plant hourly model MW) and the NYISO bench (per-plant hourly CAMPD MW);
* the measured NYISO DA zonal LBMP proxy and IESO intertie price
  (``data/raw/seam-neighbour-price``), the NYISO RT fuel mix
  (``data/raw/NYISO/fuel-mix``) and the curated ``nyiso-interface-flows``
  CENTRAL EAST loading (run ``scripts/regenerate_clean.py nyiso-interface-flows``).

Blocks, per year, split by measured CENTRAL EAST loading (>= 0.85 of posted limit):

* ``price``: Upstate_West / Capital_Hudson model vs measured DA; the model
  Capital - Upstate spread against the measured one; the share of hours with
  Upstate_West below $15 (model vs measured); the model CH/UW price ratio.
* ``mix``: NYCA class energy, model (P1 class hourly) vs NYISO RT fuel mix.
* ``zonal_gas``: CAMPD-matched gas-plant MW by model zone, model vs CAMPD.
* ``nuclear_monthly``: NYCA nuclear MW by month, model vs fuel mix.

The 2021 upstate headroom test (every UW gas MW cheaper than the UW model price
already runs) needs the fleet-only rebuild and lives in
``nyisonext18_fleet_census.py``. Record: ``results/phase0/nyiso/_nyisonext18_phase0.json``.

Usage::

    python3 scripts/probes/nyisonext18_phase0.py --out results/phase0/nyiso/_nyisonext18_phase0.json
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in ("scripts", "scripts/probes", "scripts/data", "."):
    sys.path.insert(0, str(REPO / p))

import nyisonext17_phase0 as p17  # noqa: E402

p13 = p17.p13
CAL = REPO / "results/calibration"
BUNDLE = p17.BUNDLE
YEARS = p17.YEARS
RUNS = {
    2021: "2026-09-30-nyisonext16-winter-spread-2021",
    **{y: "2026-09-30-nyisonext16-winter-spread-span" for y in range(2022, 2026)},
}
GAS = ("CC_", "CT_", "ST_")
_PAYLOAD: dict[str, dict] = {}


def _payload(run_id: str) -> dict:
    """Decoded registered run payload (base64 gzip JSON inside the ``.js``)."""
    if run_id not in _PAYLOAD:
        s = (REPO / "frontend/data/backcast/runs" / f"{run_id}.js").read_text()
        b = re.search(r'="([A-Za-z0-9+/=]+)"', s).group(1)
        _PAYLOAD[run_id] = json.loads(gzip.decompress(base64.b64decode(b)))
    return _PAYLOAD[run_id]


def _dec(b: str) -> np.ndarray:
    """Dashboard uint8 percent-of-nameplate series -> float array (8760)."""
    return np.frombuffer(base64.b64decode(b), dtype=np.uint8).astype(float)[:8760]


def _fuel_mix(y: int) -> pd.DataFrame:
    """NYISO RT fuel mix, hour-of-year (local) x fuel category, MW."""
    fm = pd.read_csv(REPO / f"data/raw/NYISO/fuel-mix/NYISO_fuelmix_hourly_{y}.csv.gz")
    t = pd.to_datetime(fm.interval_start_local.str[:19])
    fm["hoy"] = ((t - pd.Timestamp(f"{y}-01-01")) / pd.Timedelta("1h")).astype(int)
    fm = fm[(fm.hoy >= 0) & (fm.hoy < 8760)]
    return fm.pivot_table(
        index="hoy", columns="fuel_category", values="gen_mw", aggfunc="mean"
    ).reindex(range(8760))


def _r(x: float) -> float:
    return round(float(x), 2)


def year_block(y: int) -> dict:
    """All phase-0 blocks for one year."""
    meas, mod = p13.meas_da(y), p13.model_prices(y)
    uwa = meas[list(p13.UPSTATE)].mean(axis=1).to_numpy()
    cha = meas["CAPITL"].to_numpy()
    uwm = mod.Upstate_West.to_numpy()
    chm = mod.Capital_Hudson.to_numpy()
    ratio = p17._ce_ratio(y)
    hi = ratio >= 0.85
    lo = (~hi) & np.isfinite(ratio)
    ok = np.isfinite(uwa) & np.isfinite(uwm)
    out: dict = {"price": {}, "mix": {}, "zonal_gas": {}}
    for nm, m in (("ce_ge_085", hi & ok), ("ce_lt_085", lo & ok)):
        out["price"][nm] = {
            "hours": int(m.sum()),
            "uw_model": _r(uwm[m].mean()),
            "uw_meas": _r(uwa[m].mean()),
            "ch_model": _r(chm[m].mean()),
            "ch_meas": _r(np.nanmean(cha[m])),
            "spread_model": _r((chm - uwm)[m].mean()),
            "spread_meas": _r(np.nanmean((cha - uwa)[m])),
            "uw_lt15_share_model": round(float((uwm[m] < 15).mean()), 3),
            "uw_lt15_share_meas": round(float((uwa[m] < 15).mean()), 3),
        }
    out["price"]["uw_quantiles_model"] = np.round(
        np.nanquantile(uwm, [0.01, 0.1, 0.5]), 2
    ).tolist()
    out["price"]["uw_quantiles_meas"] = np.round(
        np.nanquantile(uwa, [0.01, 0.1, 0.5]), 2
    ).tolist()
    out["price"]["ch_uw_ratio_model_q10_50_90"] = np.round(
        np.nanquantile(chm / uwm, [0.1, 0.5, 0.9]), 3
    ).tolist()

    M = _fuel_mix(y)
    c = pd.read_parquet(CAL / BUNDLE[y] / "hourly" / f"class_hourly_{y}.parquet")
    c = c[c["pass"] == "P1"]
    C = (
        c.pivot_table(index="hour", columns="klass", values="mw", observed=True)
        .reindex(range(8760))
        .fillna(0)
    )
    gm = C[[k for k in C.columns if str(k).startswith(GAS)]].sum(axis=1)
    ga = M["Natural Gas"] + M["Dual Fuel"]
    have = M.notna().all(axis=1).to_numpy()
    for nm, m in (("ce_ge_085", hi & have), ("ce_lt_085", lo & have)):
        out["mix"][nm] = {
            "hydro": [round(C["hydro"][m].mean()), round(M["Hydro"][m].mean())],
            "nuclear": [round(C["nuclear"][m].mean()), round(M["Nuclear"][m].mean())],
            "wind": [round(C["wind"][m].mean()), round(M["Wind"][m].mean())],
            "gas_dual": [round(gm[m].mean()), round(ga[m].mean())],
        }
    mon = p17._mon()
    nuc = C["nuclear"].to_numpy()
    out["nuclear_monthly"] = {
        "model": [round(float(nuc[mon == k].mean())) for k in range(12)],
        "meas": [
            round(float(np.nanmean(M["Nuclear"].to_numpy()[mon == k])))
            for k in range(12)
        ],
    }

    P = _payload(RUNS[y])["years"][str(y)]["plants"]
    B = json.load(gzip.open(REPO / f"frontend/data/backcast/bench/NYISO/{y}.json.gz"))[
        "bench"
    ]["plants"]
    agg: dict[str, dict] = {}
    for key, b in B.items():
        mp = P.get(key)
        if not b.get("campd") or b.get("nodata") or b.get("ct_only"):
            continue
        if not mp or not mp.get("m"):
            continue
        a = agg.setdefault(
            b["zone"], {"m": np.zeros(8760), "c": np.zeros(8760), "cap": 0.0}
        )
        npl = b.get("npl") or 1
        a["m"] += _dec(mp["m"]) * npl / 100
        a["c"] += _dec(b["campd"]) * npl / 100
        a["cap"] += npl
    for z, a in agg.items():
        out["zonal_gas"][z] = {
            "matched_mw": round(a["cap"]),
            "ce_ge_085": [round(a["m"][hi].mean()), round(a["c"][hi].mean())],
            "ce_lt_085": [round(a["m"][lo].mean()), round(a["c"][lo].mean())],
        }
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    rec = {str(y): year_block(y) for y in YEARS}
    Path(a.out).write_text(json.dumps(rec, indent=1) + "\n")
    for y, r in rec.items():
        print(y, json.dumps(r["price"]["ce_ge_085"]))
        print("  mix", json.dumps(r["mix"]["ce_ge_085"]))
        print("  nuclear", r["nuclear_monthly"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
