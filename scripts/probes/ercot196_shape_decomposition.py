"""ercot-196 — the 2024/2025 monthly-shape object, sized from committed artifacts.

Read-only counterfactual attribution in the ercot-189/ercot-193 pattern: NO
lever, NO derive, NO LP, no run registered, keeper untouched. Card R (R-A,
signed 2026-08-13) re-pointed ERCOT bandwidth to the 2024/2025 shape queue;
this probe sizes that object — the years whose C3b already PASSES (2024
0.135, 2025 0.096) — so the shape charter's option board rests on measured
attribution rather than narrative.

Inputs, all committed:
- the keeper's registered dashboard payload (`frontend/data/backcast/runs/
  2026-08-12-run192-arm-coal-peak.js`; byte-identically reproduced by the
  registered `2026-08-13-ercot193-arm-soc` replay, G-REPRO 12/12 sha256);
- the committed ERCOT bench actuals (`frontend/data/backcast/bench/ERCOT/`);
- the committed hub-hourly actual series the C3c tail record derives from
  (`data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet`), used here
  the way `derive_actual_tail.py` uses it — actuals enter counterfactual
  scoring/attribution only, never any model input (rule 13 `[R-MEASURED]`);
- the keeper's own hourly sidecars (`results/calibration/ercot192_arm_B`);
- the keeper's own measured-input files: HH monthly
  (`data/raw/gas-prices/henry_hub_monthly.csv`), the EIA N3045TX3 ERCOT
  electric-power gas series, the thermal DAM availability hourly csv.

Per year (2024, 2025 ONLY — 2023 is out of scope per rulings Q-B/R-A; it
appears in the ceiling citation of the card, not here):
- the rubric's own C3b monthly table (scorer `_wmean`/`_nrmse`, imported);
- counterfactual NRMSE with the top-k residual months scored perfect;
- month-grain tail placement: actual RT hours > $200 and the actual tail
  wedge (mean(rt) − mean(min(rt, 200))), model max-zonal tail hours (the
  `gen_ercot188_attestation._tail_counts` basis), DA−RT basis;
- the gas-shape wedge: generic GAS_MONTHLY_SEASONALITY vs the measured HH
  monthly shape (and the N3045TX3 shape), at the keeper's annual gas level;
- the maintenance-season signature: monthly mean DAM availability fraction
  by thermal class from the committed availability csv;
- monthly model-vs-actual generation by class (payload `volErr.zoneMon`,
  summed across zones).

Calendar note: model, sidecars and the committed hub-hourly series all carry
8760 hours/year (leap-normalized), so non-leap month boundaries are used for
hour->month in both 2024 and 2025; month-edge effects are < 1 day.

Output: ``results/calibration/ercot196_shape_decomposition.json``.

Usage::

    python scripts/probes/ercot196_shape_decomposition.py \
        [--run-id 2026-08-12-run192-arm-coal-peak]
"""

from __future__ import annotations

import argparse
import base64
import csv
import gzip
import json
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO / "frontend" / "data" / "backcast" / "runs"
BENCH_DIR = REPO / "frontend" / "data" / "backcast" / "bench" / "ERCOT"
HOURLY_DIR = REPO / "results" / "calibration" / "ercot192_arm_B" / "hourly"
ACTUAL_HOURLY = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)
HH_MONTHLY = REPO / "data" / "raw" / "gas-prices" / "henry_hub_monthly.csv"
TX_POWER_GAS = REPO / "data" / "raw" / "ercot_electric_power_gas_price.csv"
DAM_AVAIL = REPO / "data" / "raw" / "ercot-thermal-dam-availability-hourly.csv"
OUT = REPO / "results" / "calibration" / "ercot196_shape_decomposition.json"

sys.path.insert(0, str(REPO / "scripts"))
from calibration_verdict import _nrmse, _wmean  # noqa: E402  (the rubric's own arithmetic)

sys.path.insert(0, str(REPO / "src"))
from market_sim.config.fuel_trajectories import GAS_MONTHLY_SEASONALITY  # noqa: E402

DEFAULT_RUN = "2026-08-12-run192-arm-coal-peak"
YEARS = (2024, 2025)
# The keeper's own annual gas levels ($/MMBtu), read from its run_config.json.
KEEPER_GAS_LEVEL = {2024: 2.19, 2025: 3.52}
# Non-leap month lengths in hours (the 8760-hour convention shared by the
# model, its sidecars and the committed hub-hourly actual series).
_MONTH_HOURS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_MONTH_EDGES = [0]
for _d in _MONTH_HOURS:
    _MONTH_EDGES.append(_MONTH_EDGES[-1] + _d * 24)


def month_of_hour(hour: int) -> int:
    for mo in range(12):
        if hour < _MONTH_EDGES[mo + 1]:
            return mo + 1
    return 12


def load_payload(run_id: str) -> dict:
    raw = (RUNS_DIR / f"{run_id}.js").read_text()
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', raw)
    if m is None:
        raise SystemExit(f"no runGz blob in {run_id}.js")
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def load_bench(year: int) -> dict:
    return json.loads(gzip.decompress((BENCH_DIR / f"{year}.json.gz").read_bytes()))[
        "bench"
    ]


def model_monthly(ypay: dict) -> list[float | None]:
    """The scorer's own C3b model vector: demand-weighted across zones of pMon."""
    lmp = ypay.get("lmp", {})
    out: list[float | None] = []
    for mo in range(12):
        pairs = []
        for z in lmp.values():
            pm = (z.get("pMon") or [None] * 12)[mo]
            dm = (z.get("dMon") or [0.0] * 12)[mo]
            if pm is not None:
                pairs.append((pm, dm))
        out.append(_wmean(pairs) if pairs else None)
    return out


def actual_monthly(bench: dict) -> list[float | None]:
    avg = bench.get("avgLMP") or {}
    return avg.get("rt_lw_mon") or avg.get("da_lw_mon") or avg.get("rt_mon")


def monthly_table(model: list, act: list) -> tuple[list[dict], float]:
    cells = [
        (mo, m, a)
        for mo, (m, a) in enumerate(zip(model, act), start=1)
        if m is not None and a is not None
    ]
    total_sq = sum((m - a) ** 2 for _, m, a in cells)
    rows = [
        {
            "month": mo,
            "model": round(m, 2),
            "actual": round(a, 2),
            "resid": round(m - a, 2),
            "sq_share": round(((m - a) ** 2) / total_sq, 4) if total_sq else None,
        }
        for mo, m, a in cells
    ]
    return rows, _nrmse([m for _, m, _ in cells], [a for _, _, a in cells])


def counterfactuals(model: list, act: list, rows: list[dict]) -> dict:
    """NRMSE with the top-k |resid| months scored perfect, cumulatively."""
    ranked = sorted(rows, key=lambda r: -abs(r["resid"]))

    def cf(perfect: set[int]) -> float:
        mvec = [
            (a if mo in perfect else m)
            for mo, (m, a) in enumerate(zip(model, act), start=1)
            if m is not None and a is not None
        ]
        avec = [a for m, a in zip(model, act) if m is not None and a is not None]
        return round(_nrmse(mvec, avec), 4)

    out = {}
    chosen: set[int] = set()
    for k in range(1, 4):
        chosen.add(ranked[k - 1]["month"])
        out[f"top{k}_perfect"] = {"months": sorted(chosen), "nrmse": cf(set(chosen))}
    # Level-vs-shape split: NRMSE with the uniform annual-mean bias removed
    # (the same _nrmse arithmetic on model - mean(resid)); what remains is
    # pure month-shape error, since _nrmse does not itself de-mean.
    cells = [
        (m, a)
        for m, a in zip(model, act)
        if m is not None and a is not None
    ]
    bias = sum(m - a for m, a in cells) / len(cells)
    out["uniform_bias"] = round(bias, 2)
    out["level_removed_nrmse"] = round(
        _nrmse([m - bias for m, _ in cells], [a for _, a in cells]), 4
    )
    return out


def tail_by_month(year: int) -> list[dict]:
    act = pd.read_parquet(ACTUAL_HOURLY)
    act = act[act["year"] == year].sort_values("hour")
    sys_df = pd.read_parquet(HOURLY_DIR / f"system_{year}.parquet")
    sys_df = sys_df[(sys_df["year"] == year) & (sys_df["pass"] == "P1")]
    # gen_ercot188_attestation._tail_counts basis: max across zones per hour.
    model_hourly_max = sys_df.groupby("hour")["price"].max()
    rows = []
    for mo in range(1, 13):
        lo, hi = _MONTH_EDGES[mo - 1], _MONTH_EDGES[mo]
        a = act[(act["hour"] >= lo) & (act["hour"] < hi)]
        mh = model_hourly_max[(model_hourly_max.index >= lo) & (model_hourly_max.index < hi)]
        s = sys_df[(sys_df["hour"] >= lo) & (sys_df["hour"] < hi)]
        # The committed published-adder overlay's demand-weighted $/MWh. The
        # scored pMon is energy-only (verified: dw(price) == pMon dw annual to
        # the cent) while the actual rt_lw_mon is settlement RTSPP — this
        # column measures that basis wedge, month by month.
        ovl = float(
            ((s["rtordpa_overlay"] + s["ordc_adder"]) * s["demand"]).sum()
            / s["demand"].sum()
        )
        rt = a["rt"]
        rows.append(
            {
                "month": mo,
                "actual_rt_gt200_h": int((rt > 200.0).sum()),
                "actual_rt_gt100_h": int((rt > 100.0).sum()),
                "model_maxzonal_gt100_h": int((mh > 100.0).sum()),
                "actual_tail_wedge": round(float(rt.mean() - rt.clip(upper=200.0).mean()), 2),
                "actual_rt_mean": round(float(rt.mean()), 2),
                "actual_da_minus_rt": round(float(a["da"].mean() - rt.mean()), 2),
                "model_maxzonal_gt200_h": int((mh > 200.0).sum()),
                "model_overlay_dw": round(ovl, 2),
            }
        )
    return rows


def gas_by_month(year: int) -> list[dict]:
    hh = {}
    with open(HH_MONTHLY) as f:
        for r in csv.DictReader(f):
            if int(r["year"]) == year:
                hh[int(r["month"])] = float(r["price_usd_mmbtu"])
    tx = {}
    with open(TX_POWER_GAS) as f:
        for r in csv.DictReader(f):
            if int(r["year"]) == year:
                tx[int(r["month"])] = float(r["price_usd_mcf"]) / 1.037  # mcf->MMBtu
    hh_mean = sum(hh.values()) / len(hh)
    tx_mean = sum(tx.values()) / len(tx)
    level = KEEPER_GAS_LEVEL[year]
    rows = []
    for mo in range(1, 13):
        hh_shape = hh[mo] / hh_mean
        tx_shape = tx[mo] / tx_mean if mo in tx else None
        generic = GAS_MONTHLY_SEASONALITY[mo]
        rows.append(
            {
                "month": mo,
                "hh": round(hh[mo], 3),
                "hh_shape": round(hh_shape, 3),
                "generic_shape": round(generic, 3),
                "wedge_mmbtu_at_keeper_level": round(level * (hh_shape - generic), 3),
                "tx_n3045tx3_mmbtu": round(tx[mo], 3) if mo in tx else None,
                "tx_shape": round(tx_shape, 3) if tx_shape else None,
            }
        )
    return rows


def availability_by_month(year: int) -> dict[str, list[float]]:
    """Monthly mean DAM availability fraction by thermal class (model input)."""
    out: dict[str, dict[int, list[float]]] = {}
    with open(DAM_AVAIL) as f:
        for r in csv.DictReader(f):
            y, mo = int(r["date"][:4]), int(r["date"][5:7])
            if y != year:
                continue
            vals = [
                float(r[f"he{h:02d}"]) for h in range(1, 25) if r[f"he{h:02d}"] != ""
            ]
            out.setdefault(r["class"], {}).setdefault(mo, []).extend(vals)
    return {
        cls: [round(sum(v[mo]) / len(v[mo]), 4) if mo in v else None for mo in range(1, 13)]
        for cls, v in sorted(out.items())
    }


def class_gen_by_month(ypay: dict) -> dict[str, dict[str, list[float]]]:
    """Monthly model-vs-actual generation by class, summed across zones (TWh)."""
    out = {}
    for cls, rec in (ypay.get("volErr") or {}).items():
        zm = rec.get("zoneMon") or {}
        msum = [0.0] * 12
        asum = [0.0] * 12
        for z in zm.values():
            for i in range(12):
                if z.get("m") and z["m"][i] is not None:
                    msum[i] += z["m"][i]
                if z.get("a") and z["a"][i] is not None:
                    asum[i] += z["a"][i]
        out[cls] = {
            "model": [round(x, 3) for x in msum],
            "actual": [round(x, 3) for x in asum],
            "delta": [round(m - a, 3) for m, a in zip(msum, asum)],
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-id", default=DEFAULT_RUN)
    args = ap.parse_args()
    pay = load_payload(args.run_id)
    result: dict = {"run_id": args.run_id, "years": {}}
    for year in YEARS:
        ypay = pay["years"][str(year)]
        model = model_monthly(ypay)
        act = actual_monthly(load_bench(year))
        rows, nrmse = monthly_table(model, act)
        result["years"][str(year)] = {
            "nrmse": round(nrmse, 4),
            "months": rows,
            "counterfactuals": counterfactuals(model, act, rows),
            "tail": tail_by_month(year),
            "gas": gas_by_month(year),
            "dam_availability_monthly": availability_by_month(year),
            "class_gen_monthly": class_gen_by_month(ypay),
            "storage_monthly_net_gwh": (ypay.get("storage") or {}).get(
                "monthly_net_gwh"
            ),
        }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    for year in YEARS:
        y = result["years"][str(year)]
        tot_act = sum(t["actual_rt_gt200_h"] for t in y["tail"])
        tot_mod = sum(t["model_maxzonal_gt200_h"] for t in y["tail"])
        print(f"{year}: NRMSE {y['nrmse']:.4f} | actual RT>200 {tot_act} h | "
              f"model max-zonal>200 {tot_mod} h")
        for r, t, g in zip(y["months"], y["tail"], y["gas"]):
            print(
                f"  m{r['month']:02d} model {r['model']:7.2f} act {r['actual']:7.2f} "
                f"resid {r['resid']:7.2f} sq {r['sq_share']:.3f} | "
                f"tail act {t['actual_rt_gt200_h']:3d}h wedge {t['actual_tail_wedge']:5.2f} "
                f"mod {t['model_maxzonal_gt200_h']:3d}h | da-rt {t['actual_da_minus_rt']:6.2f} | "
                f"gas wedge {g['wedge_mmbtu_at_keeper_level']:6.3f}"
            )
        cfs = y["counterfactuals"]
        for k, cf in cfs.items():
            if isinstance(cf, dict):
                print(f"  {k}: months {cf['months']} -> NRMSE {cf['nrmse']:.4f}")
        print(
            f"  uniform bias {cfs['uniform_bias']:+.2f} $/MWh -> "
            f"level-removed NRMSE {cfs['level_removed_nrmse']:.4f}"
        )
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
