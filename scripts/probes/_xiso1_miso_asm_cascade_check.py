"""xiso-cascade — MISO ASM MCP cascade check: the nested products are CUMULATIVE, so SUM ≠ price.

The instrument rule carried from nyiso-166 (`docs/FINDING-nyiso166-as-reference-
repair-2026-08-31.md` §2): when reserve products NEST BY DURATION/QUALITY, the
published per-product clearing prices are CUMULATIVE — a cleared MW earns the
price of the product it clears (which already internalises every lower product's
shadow price), never the SUM of the posted product prices. Summing the posted
prices double/triple-counts the shared shadow prices. What IS additive is the
shadow prices of DISTINCT nested constraints (that sum is what generates one
cumulative posted price) — never the posted cumulative prices themselves.

MISO's generator ASM MCPs cascade exactly this way: Regulating resources can
clear Spin, Spin resources can clear Supplemental (BPM-002 product
substitution), so `GENREGMCP ≥ GENSPINMCP ≥ GENSUPPMCP` — measured here at
cell grain on every committed year, both markets, every zone row. Two committed
MISO probe records aggregate these posted prices by SUMMING them:

  * `_miso167_summer_scarcity_instrument.py` — ``asm_sum`` (reg+spin+supp) and
    the headline ``asm_share_of_energy_gap_pct`` computed from it (the
    "$484.87 = 118.8 % of the energy gap" line quoted by FINDING-miso167 §3,
    PREREG-miso167 §1, FINDING-miso178 §3, the mechanism-matrix MISO narrative
    and docs/calibration-log/miso.md).
  * `_miso171_reserve_product_decomposition.py::stage4_mcp` — ``regspin`` and
    ``total`` fields in `_miso171_reserve_product_decomposition.json`.

This probe is the ACCEPTANCE TEST for their correction (the nyiso-166 pattern:
an INDEPENDENT construction reproducing the repaired values). It re-implements
each probe's own hour mapping from its documented convention (m167: HE-k EST →
CST hour k−2; m171: the loader's positional HE−1 map) without importing either
probe, reproduces the committed summed values exactly, and emits the corrected
cascade-TOP values (= per-hour max over the three products, = GENREGMCP
wherever the cascade is intact) alongside.

Stages:
  A invariant — GENREGMCP ≥ GENSPINMCP ≥ GENSUPPMCP per (zone, date, HE) cell,
                every committed year (2023–2026) × market (DA/RT) × zone row;
                the DEM* triple reported informationally. A data property of the
                committed raw file alone (no model output, no actuals tail —
                the nyiso-166 §5 rule-22 posture: data prep, not a holdout
                spend).
  B magnitude — market-wide sum/top ratio: all priced cells and the top>$50
                tail, per year × market.
  C m167      — reproduce `_miso167_summer_scarcity_instrument.json`'s
                scarce-set per-product means / sum / share from raw, then the
                corrected top means and corrected share of the committed
                energy gap.
  D m171      — reproduce `_miso171_reserve_product_decomposition.json`
                stage4 per-product means and summed fields on the record's own
                committed scarce-hour sets, then the corrected tops.

Zero solve; nothing here feeds a solve (rule 13). Reads committed artifacts
only. Run:  python3 scripts/probes/_xiso1_miso_asm_cascade_check.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

ASDIR = ROOT / "data" / "raw" / "MISO-AS"
ACTUAL = ROOT / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_MISO.parquet"
M167_JSON = ROOT / "results" / "calibration" / "_miso167_summer_scarcity_instrument.json"
M171_JSON = ROOT / "results" / "calibration" / "_miso171_reserve_product_decomposition.json"
OUT = ROOT / "results" / "calibration" / "_xiso1_miso_asm_cascade_check.json"

#: All ASM MCP years committed under data/raw/MISO-AS (2026 is the partial
#: forward-edge file; stage A/B measure it as a data property only).
INVARIANT_YEARS = (2023, 2024, 2025, 2026)
#: Years the two corrected records cover.
RECORD_YEARS = (2023, 2024, 2025)
HOURS = 8760
HE = [f"he{i:02d}" for i in range(1, 25)]

GEN_CASCADE = ("GENREGMCP", "GENSPINMCP", "GENSUPPMCP")
DEM_CASCADE = ("DEMREGMCP", "DEMSPINMCP", "DEMSUPPMCP")

#: Market-wide zone label per market (the raw files differ).
WIDE = {"rt": "Miso-Wide", "da": "MISO Wide"}

# m167's constants (docstring convention, not an import — independence).
MONTH_START = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8760]
SUMMER = (MONTH_START[5], MONTH_START[9])
SCARCE_RT = 200.0
FORESEEN_DA = 150.0
TAIL_TOP = 50.0


# --------------------------------------------------------------------------
# raw cells
# --------------------------------------------------------------------------
def cascade_cells(year: int, market: str, cascade: tuple[str, str, str]) -> pd.DataFrame:
    """Per (zone, date, HE) cell values of a 3-product cascade, wide by product.

    Cells where any of the three products is missing for that (zone, date) are
    dropped — the invariant is only defined on complete triples.
    """
    df = pd.read_parquet(ASDIR / f"asm_{market}mcp_zonal_{year}.parquet")
    df = df[df["product"].isin(cascade)].copy()
    df["date"] = pd.to_datetime(df["date"])
    long = df.melt(
        id_vars=["date", "zone", "product"], value_vars=HE, var_name="he", value_name="mcp"
    )
    wide = long.pivot_table(
        index=["zone", "date", "he"], columns="product", values="mcp", aggfunc="first"
    )
    return wide.dropna(subset=list(cascade))


def stage_a_invariant(year: int, market: str, cascade: tuple[str, str, str]) -> dict:
    """Cell-grain nesting check: cascade[0] ≥ cascade[1] ≥ cascade[2]."""
    w = cascade_cells(year, market, cascade)
    hi, mid, lo = (w[c].to_numpy(float) for c in cascade)
    mono = (hi >= mid) & (mid >= lo)
    # Posting is 2-decimal; violations within a cent are display ties.
    mono_cent = (hi >= mid - 0.01) & (mid >= lo - 0.01)
    all_eq = (hi == mid) & (mid == lo)
    priced = hi > 0
    rec = {
        "n_cells": int(len(w)),
        "monotone_pct": round(100.0 * float(np.mean(mono)), 4),
        "monotone_within_cent_pct": round(100.0 * float(np.mean(mono_cent)), 4),
        "n_violations": int(np.sum(~mono)),
        "all_three_equal_pct": round(100.0 * float(np.mean(all_eq)), 2),
        "priced_cells_pct": round(100.0 * float(np.mean(priced)), 2),
    }
    if np.any(~mono):
        v = np.where(~mono)[0]
        worst = v[np.argmax(np.maximum(mid - hi, lo - mid)[v])]
        rec["worst_violation_usd"] = round(
            float(max(mid[worst] - hi[worst], lo[worst] - mid[worst])), 4
        )
    return rec


def stage_b_magnitude(year: int, market: str) -> dict:
    """Market-wide sum/top ratio, all priced cells and the top>$50 tail."""
    w = cascade_cells(year, market, GEN_CASCADE)
    w = w[w.index.get_level_values("zone") == WIDE[market]]
    vals = w[list(GEN_CASCADE)].to_numpy(float)
    top = vals.max(axis=1)
    tot = vals.sum(axis=1)
    priced = top > 0
    tail = top > TAIL_TOP
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(priced, tot / np.where(priced, top, 1.0), np.nan)
    rec = {
        "n_hours": int(len(w)),
        "priced_hours": int(np.sum(priced)),
        "sum_over_top_mean_priced": round(float(np.nanmean(ratio)), 3),
        "sum_over_top_eq3_pct_of_priced": round(
            100.0 * float(np.sum(np.isclose(ratio, 3.0)) / max(1, np.sum(priced))), 2
        ),
        "tail_hours_top_gt_50": int(np.sum(tail)),
        "sum_over_top_mean_tail": (
            round(float(np.nanmean(ratio[tail])), 3) if np.any(tail) else None
        ),
    }
    return rec


# --------------------------------------------------------------------------
# stage C — the m167 record, reproduced and corrected
# --------------------------------------------------------------------------
def _m167_wide_mcp(year: int) -> pd.DataFrame:
    """m167's Miso-Wide RT MCP frame on its own CST hour key (HE k → hour k−2).

    Independent re-implementation of `_miso167_summer_scarcity_instrument.
    asm_mcp` from its documented convention (its `_est_he_to_cst_hour`); pivot
    duplicates resolved 'first', matching the probe.
    """
    d = pd.read_parquet(ASDIR / f"asm_rtmcp_zonal_{year}.parquet")
    d = d[d["zone"] == WIDE["rt"]].copy()
    d["date"] = pd.to_datetime(d["date"])
    long = d.melt(id_vars=["date", "product"], value_vars=HE, var_name="he", value_name="mcp")
    k = long["he"].str[2:].astype(int)
    ts = long["date"] + pd.to_timedelta(k - 2, unit="h")
    long = long[(ts.dt.year == year) & ~((ts.dt.month == 2) & (ts.dt.day == 29))]
    ts = ts[long.index]
    base = pd.Timestamp(f"{year}-01-01")
    long = long.assign(hour=((ts - base).dt.total_seconds() // 3600).astype(int))
    long = long[(long["hour"] >= 0) & (long["hour"] < HOURS)]
    return long.pivot_table(index="hour", columns="product", values="mcp", aggfunc="first")


def stage_c_m167(year: int, committed: dict) -> dict:
    """Reproduce the committed m167 scarce-set MCP block; emit the correction."""
    rec_c = committed[str(year)]["reserves"]
    sc_c = rec_c["summer_scarce"]
    gap = float(rec_c["energy_gap_in_scarce_hours"])

    a = pd.read_parquet(ACTUAL)
    a = a[a["year"] == year].set_index("hour").sort_index()
    rt = a["rt"].reindex(range(HOURS)).to_numpy(float)
    hours = np.arange(HOURS)
    scarce = np.flatnonzero((hours >= SUMMER[0]) & (hours < SUMMER[1]) & (rt > SCARCE_RT))

    w = _m167_wide_mcp(year).reindex(scarce)
    means = {p: float(w[p].mean()) for p in GEN_CASCADE}
    rep_sum = float(w[list(GEN_CASCADE)].sum(axis=1).mean())
    top_hourly = w[list(GEN_CASCADE)].max(axis=1)
    top_mean = float(top_hourly.mean())
    top_is_reg = bool((top_hourly == w["GENREGMCP"]).all())

    reproduces = bool(
        int(len(scarce)) == int(sc_c["n"])
        and np.isclose(rep_sum, float(sc_c["miso_asm_mcp_sum"]), rtol=0, atol=1e-6)
        and all(
            np.isclose(means[p], float(sc_c["miso_asm_by_product"][p]), rtol=0, atol=1e-6)
            for p in GEN_CASCADE
        )
    )
    return {
        "n_scarce": int(len(scarce)),
        "committed_n": int(sc_c["n"]),
        "reproduced_sum": round(rep_sum, 2),
        "committed_sum": round(float(sc_c["miso_asm_mcp_sum"]), 2),
        "reproduced_by_product": {p: round(means[p], 2) for p in GEN_CASCADE},
        "reproduces_committed_record": reproduces,
        "corrected_top_mean": round(top_mean, 2),
        "top_equals_genregmcp_in_every_scarce_hour": top_is_reg,
        "sum_over_top": round(rep_sum / top_mean, 2) if top_mean else None,
        "committed_energy_gap": round(gap, 2),
        "committed_share_pct": round(float(rec_c["asm_share_of_energy_gap_pct"]), 1),
        "corrected_share_pct": round(100.0 * top_mean / gap, 1) if gap else None,
    }


# --------------------------------------------------------------------------
# stage D — the m171 stage-4 record, reproduced and corrected
# --------------------------------------------------------------------------
def _m171_series(year: int, market: str) -> dict[str, np.ndarray]:
    """m171's per-product 8760 series on the loader's positional HE−1 map.

    Independent re-implementation of `_miso171_reserve_product_decomposition.
    mcp_series` from the loader's documented convention (`reserve_requirements.
    _to_model_hour`: (day-of-year−1)*24 + HE−1, Feb 29 dropped), duplicate rows
    meaned and posting gaps ffill/bfill'd exactly as the probe does.
    """
    import calendar as _cal

    d = pd.read_parquet(ASDIR / f"asm_{market}mcp_zonal_{year}.parquet")
    d = d[d["zone"] == WIDE[market]].copy()
    d["date"] = pd.to_datetime(d["date"])
    out: dict[str, np.ndarray] = {}
    for p in GEN_CASCADE:
        sub = d[d["product"] == p]
        long = sub.melt(id_vars=["date"], value_vars=HE, var_name="he", value_name="mcp")
        he = long["he"].str[2:].astype(int).to_numpy()
        ts = long["date"]
        doy = ts.dt.dayofyear.to_numpy(int)
        if _cal.isleap(year):
            feb29 = ((ts.dt.month == 2) & (ts.dt.day == 29)).to_numpy()
            doy = np.where(doy > 60, doy - 1, doy)
            idx = np.where(feb29, -1, (doy - 1) * 24 + (he - 1))
        else:
            idx = (doy - 1) * 24 + (he - 1)
        long = long.assign(_hour=idx)
        long = long[long["_hour"] >= 0]
        series = np.full(HOURS, np.nan)
        hourly = long.groupby("_hour")["mcp"].mean()
        gi = hourly.index.to_numpy(int)
        keep = gi < HOURS
        series[gi[keep]] = hourly.to_numpy(float)[keep]
        out[p] = pd.Series(series).ffill().bfill().to_numpy(float)
    return out


def stage_d_m171(committed: dict) -> dict:
    """Reproduce the committed m171 stage-4 MCP blocks; emit the corrections."""
    year = 2025
    y = committed["years"][str(year)]
    rt = _m171_series(year, "rt")
    da = _m171_series(year, "da")

    a = pd.read_parquet(ACTUAL)
    a = a[a["year"] == year].set_index("hour").sort_index()
    da_lmp = a["da"].reindex(range(HOURS)).to_numpy(float)
    rt_lmp = a["rt"].reindex(range(HOURS)).to_numpy(float)
    hours = np.arange(HOURS)

    out = {}
    for block, scarce in (
        ("stage4_published_mcp_by_product", np.asarray(y["scarce47_hours"], int)),
        (
            "stage4_published_mcp_by_product_rt200",
            np.flatnonzero(
                (hours >= SUMMER[0]) & (hours < SUMMER[1]) & (rt_lmp > SCARCE_RT)
            ),
        ),
    ):
        c = y[block]
        foreseen = scarce[da_lmp[scarce] > FORESEEN_DA]
        rt_only = scarce[da_lmp[scarce] <= FORESEEN_DA]
        brec = {
            "n_scarce": int(len(scarce)),
            "committed_n": int(c["n_scarce"]),
            "split_reproduces": (
                int(len(foreseen)) == int(c["n_da_foreseen"])
                and int(len(rt_only)) == int(c["n_rt_only"])
            ),
            "sets": {},
        }
        short = {"reg": "GENREGMCP", "spin": "GENSPINMCP", "supp": "GENSUPPMCP"}
        for label, hset in (("scarce47", scarce), ("da_foreseen", foreseen), ("rt_only", rt_only)):
            srec = {}
            for market, series in (("rt_mcp", rt), ("da_mcp", da)):
                vals = {k: round(float(np.mean(series[short[k]][hset])), 2) for k in short}
                cvals = c[label][market]
                srec[market] = {
                    "reproduces_committed": bool(
                        all(
                            np.isclose(vals[k], float(cvals[k]), rtol=0, atol=0.005)
                            for k in short
                        )
                        and np.isclose(
                            round(vals["reg"] + vals["spin"] + vals["supp"], 2),
                            float(cvals["total"]),
                            rtol=0,
                            atol=0.011,
                        )
                    ),
                    "corrected_top": round(
                        float(
                            np.mean(
                                np.maximum.reduce(
                                    [series[short[k]][hset] for k in short]
                                )
                            )
                        ),
                        2,
                    ),
                    "committed_total_sum": float(cvals["total"]),
                }
                srec[market]["sum_over_top"] = (
                    round(srec[market]["committed_total_sum"] / srec[market]["corrected_top"], 2)
                    if srec[market]["corrected_top"]
                    else None
                )
            brec["sets"][label] = srec
        out[block] = brec
    return out


def main() -> None:
    record: dict = {
        "session": "xiso-cascade",
        "rule": (
            "nested-by-duration posted reserve prices are cumulative: a MW earns "
            "the cascade MAX (= the top product's posted price), never the SUM "
            "(nyiso-166 §2 carried cross-ISO)"
        ),
        "stage_a_invariant": {},
        "stage_b_magnitude": {},
        "stage_c_m167": {},
        "stage_d_m171": {},
    }
    for year in INVARIANT_YEARS:
        for market in ("da", "rt"):
            key = f"{year}_{market}"
            record["stage_a_invariant"][key] = {
                "gen": stage_a_invariant(year, market, GEN_CASCADE),
                "dem": stage_a_invariant(year, market, DEM_CASCADE),
            }
            record["stage_b_magnitude"][key] = stage_b_magnitude(year, market)

    m167 = json.loads(M167_JSON.read_text())
    for year in RECORD_YEARS:
        record["stage_c_m167"][str(year)] = stage_c_m167(year, m167)

    m171 = json.loads(M171_JSON.read_text())
    record["stage_d_m171"] = stage_d_m171(m171)

    OUT.write_text(json.dumps(record, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\n")

    print("== stage A: GENREGMCP >= GENSPINMCP >= GENSUPPMCP (cell grain) ==")
    for key, r in record["stage_a_invariant"].items():
        g = r["gen"]
        print(
            f"  {key}: {g['n_cells']:>7,} cells  monotone {g['monotone_pct']:.4f}%"
            f"  (within-cent {g['monotone_within_cent_pct']:.4f}%)"
            f"  all-equal {g['all_three_equal_pct']:.2f}%"
        )
    print("== stage B: market-wide sum/top ==")
    for key, r in record["stage_b_magnitude"].items():
        print(
            f"  {key}: priced {r['priced_hours']:>5}h ratio {r['sum_over_top_mean_priced']}"
            f"  tail(top>$50) {r['tail_hours_top_gt_50']:>3}h ratio {r['sum_over_top_mean_tail']}"
        )
    print("== stage C: m167 scarce-set record ==")
    for year, r in record["stage_c_m167"].items():
        print(
            f"  {year}: n={r['n_scarce']} reproduces={r['reproduces_committed_record']}"
            f"  sum ${r['committed_sum']} -> top ${r['corrected_top_mean']}"
            f"  share {r['committed_share_pct']}% -> {r['corrected_share_pct']}%"
        )
    print("== stage D: m171 stage-4 record ==")
    for block, b in record["stage_d_m171"].items():
        s = b["sets"]["scarce47"]["rt_mcp"]
        f = b["sets"]["da_foreseen"]["rt_mcp"]
        print(
            f"  {block}: n={b['n_scarce']} split_ok={b['split_reproduces']}"
            f"  scarce47 rt total ${s['committed_total_sum']} -> top ${s['corrected_top']}"
            f"  da_foreseen rt ${f['committed_total_sum']} -> ${f['corrected_top']}"
        )


if __name__ == "__main__":
    main()
