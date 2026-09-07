"""nyiso-210 phase 0 — attribute the 2022 touchpoint's CC_REGULAR over-run.

Zero-LP. Reads ONLY artifacts already committed to ``main``:

* ``results/calibration/<bundle>/hourly/class_band_hourly_<year>.parquet`` and
  ``class_hourly_<year>.parquet`` — the model's CC_REGULAR MW by band x hour,
  P1 pass, plus the ``mw_oil`` dual-fuel column.
* ``frontend/data/backcast/bench/NYISO/<year>.json.gz`` — measured plant
  monthly energy (``c_mon``, CAMPD; ``e_mon``, EIA-923-split).
* ``frontend/data/backcast/runs/<run_id>.js`` — the model's plant monthly
  energy (``m_mon``).

The 2022 rung was solved, scored and registered by nyiso-209; this module
re-reads that run's committed artifacts and identifies nothing against 2022
(rule 22 touchpoint-loop step 2).

Pre-registration:
``results/calibration/PREREG-nyiso210-cc-regular-2022-overrun-attribution.md``
(committed and pushed before this file was written).

Run::

    uv run python scripts/probes/nyiso210_cc_overrun_attribution.py
"""

from __future__ import annotations

import gzip
import json
import statistics
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.backcast_artifacts import decode_run_js  # noqa: E402

KLASS = "CC_REGULAR"
PASS = "P1"
# The committed sidecar emits the economic region as six continuous tranches
# (econc00..econc05) rather than the registry's econ_low/econ_high pair, so the
# partition is reassembled three-way. Construction repair only, no threshold
# moved: results/calibration/ADDENDUM-nyiso210-band-vocabulary-2026-09-06.md
ECON_TRANCHES = tuple(f"econc{i:02d}" for i in range(6))
BANDS = ("committed", "econ", "peak")


def _fold_bands(by_band: "pd.Series") -> dict:
    """Fold the sidecar's tranche vocabulary onto the three-way partition."""
    return {
        "committed": float(by_band.get("committed", 0.0)),
        "econ": float(sum(by_band.get(t, 0.0) for t in ECON_TRANCHES)),
        "peak": float(by_band.get("peak", 0.0)),
    }
IN_SAMPLE = (2023, 2024, 2025)
TARGET = 2022

TOUCHPOINT_RUN = "2026-09-06-nyiso-209-2022-touchpoint"
KEEPER_RUN = "2026-09-06-nyiso-202-startup-aware"
TOUCHPOINT_BUNDLE = ROOT / "results/calibration/nyiso209_2022_touchpoint"
KEEPER_BUNDLE = ROOT / "results/calibration/nyiso202_startup_aware"

BENCH = ROOT / "frontend/data/backcast/bench/NYISO"
RUNS = ROOT / "frontend/data/backcast/runs"

# Rule 8 [R-8760]: every solve is a flat 8,760-hour year, so the hour index maps
# through a fixed non-leap calendar in every year including 2024.
_MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
WINTER = (0, 1, 2, 11)  # Jan, Feb, Mar, Dec
SUMMER = (5, 6, 7, 8)  # Jun, Jul, Aug, Sep

# Pre-registered thresholds (PREREG §3.1, §4). None is selected here.
I1_TOL = 0.05
P2_COMMITTED_TWH = 0.5
P1_ECON_SHARE_PP = 3.0
P3_CV_MAX = 0.35
P4_TOPN = 3
P4_NEW_PLANT_SHARE = 0.30
P5_OIL_TWH = 0.05


def _month_of_hour() -> list[int]:
    """Return the 0-based month index of each of the 8,760 hours."""
    out: list[int] = []
    for month, days in enumerate(_MONTH_DAYS):
        out.extend([month] * days * 24)
    return out


MONTH_OF_HOUR = _month_of_hour()


def _bundle_for(year: int) -> Path:
    return TOUCHPOINT_BUNDLE if year == TARGET else KEEPER_BUNDLE


def _run_id_for(year: int) -> str:
    return TOUCHPOINT_RUN if year == TARGET else KEEPER_RUN


def band_month_table(year: int) -> dict:
    """Model CC_REGULAR energy by band and month, from ``class_band_hourly``."""
    path = _bundle_for(year) / "hourly" / f"class_band_hourly_{year}.parquet"
    df = pd.read_parquet(path)
    df = df[(df["pass"] == PASS) & (df["klass"] == KLASS)].copy()
    df["month"] = df["hour"].map(lambda h: MONTH_OF_HOUR[int(h) % 8760])
    raw_band = df.groupby("band")["mw"].sum() / 1e6  # MWh -> TWh
    by_band = _fold_bands(raw_band)
    by_band_month = (
        df.groupby(["band", "month"])["mw"].sum().unstack(fill_value=0.0) / 1e3
    )  # GWh
    oil = float(df["mw_oil"].sum() / 1e6)
    return {
        "bands_twh": {b: round(by_band[b], 4) for b in BANDS},
        "raw_bands_twh": {
            str(b): round(float(v), 4) for b, v in raw_band.sort_index().items()
        },
        "band_month_gwh": {
            b: [round(float(v), 2) for v in by_band_month.loc[b].tolist()]
            for b in by_band_month.index
        },
        "total_twh": round(float(sum(by_band.values())), 4),
        "oil_twh": round(oil, 4),
    }


def class_total_twh(year: int) -> float:
    """Model CC_REGULAR annual energy from ``class_hourly`` (the band-sum check)."""
    path = _bundle_for(year) / "hourly" / f"class_hourly_{year}.parquet"
    df = pd.read_parquet(path)
    sel = df[(df["pass"] == PASS) & (df["klass"] == KLASS)]
    return round(float(sel["mw"].sum() / 1e6), 4)


def plant_table(year: int) -> dict:
    """Per-plant model and measured CC_REGULAR monthly energy (GWh) and annual (TWh)."""
    bench = json.load(gzip.open(BENCH / f"{year}.json.gz"))["bench"]["plants"]
    payload = decode_run_js((RUNS / f"{_run_id_for(year)}.js").read_text())
    model_plants = payload["years"][str(year)]["plants"]

    rows: dict[str, dict] = {}
    for code, bp in bench.items():
        if bp.get("group") != KLASS:
            continue
        mp = model_plants.get(code) or {}
        m_mon = mp.get("m_mon") or [0.0] * 12
        c_mon = bp.get("c_mon") or [0.0] * 12
        rows[code] = {
            "name": bp.get("name"),
            "zone": bp.get("zone"),
            "npl_mw": bp.get("npl"),
            "nodata": bool(bp.get("nodata")),
            "model_twh": round(float(mp.get("m_ann") or 0.0), 4),
            "campd_twh": round(float(bp.get("c_ann") or 0.0), 4),
            "e923_twh": round(float(bp.get("e_ann") or 0.0), 4),
            "gap_twh": round(float(mp.get("m_ann") or 0.0) - float(bp.get("c_ann") or 0.0), 4),
            "model_mon_gwh": [round(float(v), 2) for v in m_mon],
            "campd_mon_gwh": [round(float(v), 2) for v in c_mon],
            "in_payload": code in model_plants,
        }
    # Model-side plants the bench does not carry in this class are reported too:
    # they are model energy with no measured counterpart at all.
    return rows


def summarise(rows: dict) -> dict:
    model = sum(r["model_twh"] for r in rows.values())
    campd = sum(r["campd_twh"] for r in rows.values())
    return {
        "n_plants": len(rows),
        "model_twh": round(model, 4),
        "campd_twh": round(campd, 4),
        "gap_twh": round(model - campd, 4),
    }


def main() -> None:
    years = (TARGET,) + IN_SAMPLE
    band = {y: band_month_table(y) for y in years}
    cls = {y: class_total_twh(y) for y in years}
    plants = {y: plant_table(y) for y in years}
    psum = {y: summarise(plants[y]) for y in years}

    # ---- I1: payload plant sum vs parquet class total -----------------------
    i1 = {}
    for y in years:
        c = cls[y]
        p = psum[y]["model_twh"]
        rel = abs(p - c) / c if c else float("inf")
        i1[y] = {
            "class_hourly_twh": c,
            "payload_plant_sum_twh": p,
            "abs_gap_twh": round(p - c, 4),
            "rel_gap": round(rel, 4),
            "pass": bool(rel <= I1_TOL),
        }
    i1_pass = all(v["pass"] for v in i1.values())

    # ---- band-sum reconciliation (parquet internal) -------------------------
    band_recon = {
        y: {
            "band_sum_twh": band[y]["total_twh"],
            "class_hourly_twh": cls[y],
            "abs_gap_twh": round(band[y]["total_twh"] - cls[y], 4),
        }
        for y in years
    }

    # ---- P2 / P1 / P3: the band axis ---------------------------------------
    ins_mean = {
        b: round(statistics.mean(band[y]["bands_twh"][b] for y in IN_SAMPLE), 4)
        for b in BANDS
    }
    tgt = band[TARGET]["bands_twh"]
    delta = {b: round(tgt[b] - ins_mean[b], 4) for b in BANDS}
    pct = {
        b: (round((tgt[b] - ins_mean[b]) / ins_mean[b], 4) if ins_mean[b] else None)
        for b in BANDS
    }

    def _share(d: dict) -> dict:
        tot = sum(d.values())
        return {b: (round(100.0 * d[b] / tot, 2) if tot else 0.0) for b in BANDS}

    tgt_share = _share(tgt)
    ins_share_by_year = {y: _share(band[y]["bands_twh"]) for y in IN_SAMPLE}
    ins_share = {
        b: round(statistics.mean(ins_share_by_year[y][b] for y in IN_SAMPLE), 2)
        for b in BANDS
    }
    econ_tgt = tgt_share["econ"]
    econ_ins = ins_share["econ"]
    econ_pp = round(econ_tgt - econ_ins, 2)

    p2 = bool(delta["committed"] > P2_COMMITTED_TWH)
    p1 = bool((not p2) and econ_pp >= P1_ECON_SHARE_PP)
    pcts = [v for v in pct.values() if v is not None]
    cv = (
        round(statistics.pstdev(pcts) / abs(statistics.mean(pcts)), 4)
        if pcts and statistics.mean(pcts)
        else None
    )
    p3 = bool((not p2) and (not p1) and cv is not None and cv < P3_CV_MAX)
    verdict = (
        "P2 (M1 forcing)"
        if p2
        else "P1 (M2 merit position)"
        if p1
        else "P3 (M3 availability)"
        if p3
        else "UNRESOLVED at band grain"
    )

    # ---- monthly gap, class level (winter vs summer weighting) --------------
    month_gap = {}
    for y in years:
        m_mon = [0.0] * 12
        c_mon = [0.0] * 12
        for r in plants[y].values():
            for i in range(12):
                m_mon[i] += r["model_mon_gwh"][i]
                c_mon[i] += r["campd_mon_gwh"][i]
        gap = [round(m_mon[i] - c_mon[i], 2) for i in range(12)]
        month_gap[y] = {
            "model_gwh": [round(v, 2) for v in m_mon],
            "campd_gwh": [round(v, 2) for v in c_mon],
            "gap_gwh": gap,
            "winter_gap_gwh": round(sum(gap[i] for i in WINTER), 2),
            "summer_gap_gwh": round(sum(gap[i] for i in SUMMER), 2),
        }

    # ---- P4: plant grain ----------------------------------------------------
    p4: dict = {"evaluated": i1_pass}
    if i1_pass:
        tgt_rank = sorted(
            plants[TARGET].items(), key=lambda kv: -abs(kv[1]["gap_twh"])
        )
        ins_gap: dict[str, float] = {}
        for y in IN_SAMPLE:
            for code, r in plants[y].items():
                ins_gap[code] = ins_gap.get(code, 0.0) + r["gap_twh"] / len(IN_SAMPLE)
        ins_rank = sorted(ins_gap.items(), key=lambda kv: -abs(kv[1]))
        tgt_top = [c for c, _ in tgt_rank[:P4_TOPN]]
        ins_top = [c for c, _ in ins_rank[:P4_TOPN]]
        overlap = [c for c in tgt_top if c in ins_top]
        total_gap = psum[TARGET]["gap_twh"]
        new_plants = [
            {
                "code": c,
                "name": plants[TARGET][c]["name"],
                "zone": plants[TARGET][c]["zone"],
                "gap_twh": plants[TARGET][c]["gap_twh"],
                "share_of_total_gap": (
                    round(plants[TARGET][c]["gap_twh"] / total_gap, 4)
                    if total_gap
                    else None
                ),
            }
            for c in tgt_top
            if c not in ins_top
            and total_gap
            and plants[TARGET][c]["gap_twh"] / total_gap > P4_NEW_PLANT_SHARE
        ]
        p4.update(
            {
                "target_top": [
                    {
                        "code": c,
                        "name": plants[TARGET][c]["name"],
                        "zone": plants[TARGET][c]["zone"],
                        "gap_twh": plants[TARGET][c]["gap_twh"],
                        "share_of_total_gap": (
                            round(plants[TARGET][c]["gap_twh"] / total_gap, 4)
                            if total_gap
                            else None
                        ),
                    }
                    for c in tgt_top
                ],
                "in_sample_top": [
                    {
                        "code": c,
                        "name": plants[IN_SAMPLE[0]].get(c, {}).get("name"),
                        "mean_gap_twh": round(ins_gap[c], 4),
                    }
                    for c in ins_top
                ],
                "overlap": overlap,
                "fires": bool(len(overlap) >= 2),
                "falsifier_new_plants": new_plants,
            }
        )

    # ---- P5: dual fuel ------------------------------------------------------
    p5 = {
        "oil_twh_by_year": {y: band[y]["oil_twh"] for y in years},
        "target_oil_twh": band[TARGET]["oil_twh"],
        "within_prediction": bool(band[TARGET]["oil_twh"] <= P5_OIL_TWH),
    }

    out = {
        "session": "nyiso-210",
        "prereg": (
            "results/calibration/"
            "PREREG-nyiso210-cc-regular-2022-overrun-attribution.md"
        ),
        "iso": "NYISO",
        "klass": KLASS,
        "keeper": KEEPER_RUN,
        "touchpoint": TOUCHPOINT_RUN,
        "zero_lp": True,
        "I1_instrument_identity": {"per_year": i1, "pass": i1_pass, "tol": I1_TOL},
        "band_sum_reconciliation": band_recon,
        "bands": {
            "target_twh": tgt,
            "in_sample_mean_twh": ins_mean,
            "delta_twh": delta,
            "pct_change": pct,
            "target_share_pct": tgt_share,
            "in_sample_mean_share_pct": ins_share,
            "in_sample_share_by_year": ins_share_by_year,
            "econ_share_pp_move": econ_pp,
            "pct_change_cv": cv,
            "by_year_twh": {y: band[y]["bands_twh"] for y in years},
        },
        "band_month_gwh": {y: band[y]["band_month_gwh"] for y in years},
        "class_month_gap": month_gap,
        "plant_summary": psum,
        "plants": plants,
        "predictions": {
            "P2_forcing_fires": p2,
            "P1_merit_fires": p1,
            "P3_availability_fires": p3,
            "P4_plant_grain": p4,
            "P5_dual_fuel": p5,
            "verdict": verdict,
        },
    }
    dest = ROOT / "results/calibration/_nyiso210_cc_overrun_attribution.json"
    dest.write_text(json.dumps(out, indent=1, sort_keys=False, default=str))
    print(json.dumps({k: v for k, v in out.items() if k != "plants"}, indent=1,
                     default=str)[:9000])
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
