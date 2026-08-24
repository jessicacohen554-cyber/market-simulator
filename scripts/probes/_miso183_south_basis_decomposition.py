"""miso-183 — the South-seam MEASUREMENT-BASIS decomposition: defect or bookkeeping?

READ-ONLY. **No LP is solved and nothing here re-enters a solve** (rule 13
``[R-MEASURED]``): every number is a measurement of committed artifacts and
intaken public actuals, written to a JSON record for the finding.

Everything below is frozen by
``results/calibration/PREREG-miso183-south-basis-decomposition-2026-08-24.md``
(committed and pushed BEFORE the source hunt and before any adjudicating
quantity was computed). The hunt closed H-1 NEGATIVE (no retrievable aggregate
RDT flow series), so Leg 3 falls away and the PREREG's reduced verdict mapping
applies: V-BASIS is unreachable; the reachable verdicts are V-TRADE,
V-TRANSFER, V-UNRESOLVED (+ the MIXED escape, all components reported).

Stages (PREREG section 3):
  0  footing — reproduce the scarce-set sizes (11/14/47), the committed pool
     values, VERIFY the pair-level DIBA premise (one row per (hour, diba)) and
     the Midwest copper-plate premise (max intra-Midwest spread) on which the
     Leg-2 spread classifier stands.
  L2 basis-free South intake — measured N_S = L_S - G_S (the new
     miso-regional-balance corpus) vs the model interval
     N_S^m = RDT^m + seam_net^m (keeper sidecar spread classifier + the
     committed miso-174 seam record), with the whole-MISO identity wedge W
     reported (never apportioned) and the +-1h sensitivity pair reported.
  L4 binding-record contrast — the measured pbc RDT N->S binding indicator
     (>=6 of 12 five-minute rows = a binding hour; the >=1 variant reported)
     vs the pool aggregate and each counterparty leg, summer; plus the
     scarce-intersect-binding counts. Confound declared in the PREREG: Leg 4
     alone can never establish V-BASIS.

Sign conventions, stated on every table:
  * EIA-930 ``mw`` is + when MISO EXPORTS; ``net_import = -mw``;
    ``E_pool`` (pool net export) = -(sum of pool net imports).
  * ``N_S`` / ``N_S^m`` are + INTO the South.
  * ``RDT^m`` is + North->South.

Hour keys (frozen): EIA-930 DIBA on the committed -1 h key; the model fixed
non-leap 8760 CST clock; MISO market reports are Market Hour ENDING 1..24 EST
year-round -> CST hour-beginning k-2 (k=1 wraps to the prior day's h23); pbc
5-min rows are EST interval starts -> CST hour H-1 (same wrap). No alignment
search: the +-1h pair on the new corpus is REPORTED, never gated.

Run:
  uv run --no-project --with pyarrow,pandas,numpy --python 3.12 \
    python scripts/probes/_miso183_south_basis_decomposition.py
"""

from __future__ import annotations

import gzip
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.config.interchange_config import MISO_SEAM_DIBA  # noqa: E402

CAL = ROOT / "results" / "calibration"
ACTUAL = ROOT / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_MISO.parquet"
E930_DIBA = ROOT / "data" / "raw" / "eia-930-interchange" / "MISO interchange hourly.parquet"
E930_REGION = ROOT / "data" / "raw" / "MISO_region.parquet"
REGBAL = ROOT / "data" / "raw" / "miso-regional-balance"
PBC = ROOT / "data" / "raw" / "transfer-constraint-binding" / "MISO"
M174 = CAL / "_miso174_seam_overimport_decomposition.json"
KEEPER = CAL / "miso177_rho_B" / "hourly"
OUT = CAL / "_miso183_south_basis_decomposition.json"

YEARS = (2023, 2024, 2025)
HOURS = 8760
MONTH_START = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8760]
SUMMER = (MONTH_START[5], MONTH_START[9])  # Jun 1 .. Sep 30 inclusive
SCARCE_RT = 200.0

DIBA_KEY_SHIFT = -1  # FROZEN (miso-174 section 4 / miso-175); never searched here
SOUTH = MISO_SEAM_DIBA["South"]

# The armed RDT/RPE constants (config.constants, cited there to the JOA and
# the 2024 MISO SOM section III.B). PREREG section 3 Leg-2 classifier bands.
RDT_N2S_DERATED = 0.92 * 3000.0   # 2,760 MW
RDT_N2S_CONTRACT = 3000.0
RDT_S2N_DERATED = 0.92 * 2500.0   # 2,300 MW
RDT_S2N_CONTRACT = 2500.0
RPE_VALUE = 200.0

# Committed pool-basis scarce gaps (miso-174 section 1) — the object O_y.
O_GAP = {2023: 0.633, 2024: 0.350, 2025: 1.191}

# PREREG section 3/4 frozen lines.
S2_TRANSFER = 0.5
S2_EXONERATE = 0.25
D4_CLEAN_GW = 0.3
D4_SUGGEST_GW = 0.75
BINDING_MAJORITY = 6  # of 12 five-minute rows


# --------------------------------------------------------------------------
# clocks
# --------------------------------------------------------------------------
def _nonleap_hour(y: int, m: int, d: int, hour_cst: int) -> int:
    """Model hour index for a CST calendar hour on the fixed non-leap clock."""
    if m == 2 and d == 29:
        return -1
    doy = (date(y, m, d) - date(y, 1, 1)).days + 1
    if date(y, 12, 31).timetuple().tm_yday == 366 and doy > 60:
        doy -= 1
    h = (doy - 1) * 24 + hour_cst
    return h if 0 <= h < HOURS else -1


# --------------------------------------------------------------------------
# loaders (the committed miso-182 machinery, verbatim where marked)
# --------------------------------------------------------------------------
def diba_wide(year: int, shift_h: int = DIBA_KEY_SHIFT) -> pd.DataFrame:
    """Measured per-DIBA NET IMPORT (MW) on the model hour key (miso-182 verbatim)."""
    d = pd.read_parquet(E930_DIBA).copy()
    ts = pd.DatetimeIndex(d["local_time"]) + pd.Timedelta(hours=shift_h)
    keep = (ts.year == year) & ~((ts.month == 2) & (ts.day == 29))
    d = d[keep]
    ts = ts[keep]
    doy = ts.dayofyear.to_numpy()
    if bool(pd.Timestamp(f"{year}-12-31").dayofyear == 366):
        doy = np.where(doy > 60, doy - 1, doy)
    d = d.assign(hour=(doy - 1) * 24 + ts.hour.to_numpy())
    d = d[(d["hour"] >= 0) & (d["hour"] < HOURS)]
    dup = int(d.duplicated(["hour", "diba"]).sum())  # pair-level premise check
    w = d.pivot_table(index="hour", columns="diba", values="mw", aggfunc="first")
    w.attrs["duplicate_hour_diba_rows"] = dup
    return (-w).reindex(range(HOURS))  # net import


def actual_lmp(year: int) -> pd.DataFrame:
    """MISO measured RT/DA hub LMP on the model hour key (miso-182 verbatim)."""
    a = pd.read_parquet(ACTUAL)
    return a[a["year"] == year][["hour", "rt", "da"]].reset_index(drop=True)


def hour_sets(year: int) -> dict[str, np.ndarray]:
    """The FROZEN miso-174/178 hour sets as boolean masks over 8760."""
    a = actual_lmp(year)
    rt = a.set_index("hour")["rt"].reindex(range(HOURS)).to_numpy(dtype=float)
    idx = np.arange(HOURS)
    summer = (idx >= SUMMER[0]) & (idx < SUMMER[1])
    scarce = summer & (rt > SCARCE_RT)
    return {"annual": np.ones(HOURS, dtype=bool), "summer": summer, "scarce": scarce}


def _mean(x: np.ndarray, m: np.ndarray) -> float:
    v = x[m]
    v = v[np.isfinite(v)]
    return float(v.mean()) if v.size else float("nan")


def regional_series(year: int, kind: str, region: str, shift_extra: int = 0) -> np.ndarray:
    """Hourly MW series from the miso-regional-balance corpus on the model clock.

    ``kind``: "load" (actual_mw) or "gen" (fuel == Total). HE k EST maps to CST
    hour-beginning k-2 (k=1 wraps to the prior day h23); ``shift_extra`` is the
    REPORTED-ONLY +-1h sensitivity knob (never gated; PREREG section 3).
    """
    out = np.full(HOURS, np.nan)
    if kind == "load":
        df = pd.read_csv(REGBAL / f"miso_regional_load_{year}.csv.gz")
        df = df[df["region"] == region]
        val = "actual_mw"
    else:
        df = pd.read_csv(REGBAL / f"miso_regional_genmix_{year}.csv.gz")
        val = "mw"
        if region == "MISO_SUM":
            # Whole-MISO gen = sum of the three regional Total columns (the
            # workbook's own Total block labels its sum column "MISO", which
            # the consolidation skips as a sub-header — same quantity).
            df = df[(df["region"].isin(["Central", "North", "South"])) & (df["fuel"] == "Total")]
            df = (df.groupby(["market_date", "he_est"], as_index=False)["mw"].sum()
                    .assign(region="MISO_SUM"))
        else:
            df = df[(df["region"] == region) & (df["fuel"] == "Total")]
    for mdate, he, v in df[["market_date", "he_est", val]].itertuples(index=False):
        y, m, d = int(mdate[:4]), int(mdate[5:7]), int(mdate[8:10])
        h_cst = int(he) - 2 + shift_extra  # HE k EST -> CST hour-beginning k-2
        if h_cst < 0:
            prev = date(y, m, d) - pd.Timedelta(days=1)
            if prev.year != year:
                continue
            h = _nonleap_hour(prev.year, prev.month, prev.day, h_cst + 24)
        elif h_cst > 23:
            nxt = date(y, m, d) + pd.Timedelta(days=1)
            if nxt.year != year:
                continue
            h = _nonleap_hour(nxt.year, nxt.month, nxt.day, h_cst - 24)
        else:
            h = _nonleap_hour(y, m, d, h_cst)
        if h >= 0:
            out[h] = v
    return out


def e930_ti_net_import(year: int) -> np.ndarray:
    """Whole-MISO measured net import (MW) from EIA-930 TI (UTC -> CST-6)."""
    d = pd.read_parquet(E930_REGION)
    d = d[d["type"] == "TI"].copy()
    ts = pd.DatetimeIndex(d["period"]).tz_convert("UTC") - pd.Timedelta(hours=6)
    out = np.full(HOURS, np.nan)
    for t, v in zip(ts, d["value_mwh"].to_numpy(dtype=float)):
        if t.year != year:
            continue
        h = _nonleap_hour(t.year, t.month, t.day, t.hour)
        if h >= 0:
            out[h] = -v  # TI + = net export; net import = -TI
    return out


def keeper_spread(year: int) -> np.ndarray:
    """Keeper P1 zonal price spread MISO-South minus Midwest, hourly ($/MWh)."""
    sy = pd.read_parquet(KEEPER / f"system_{year}.parquet")
    sy = sy[sy["pass"] == "P1"]
    piv = sy.pivot_table(index="hour", columns="zone", values="price").reindex(range(HOURS))
    mw_zones = [z for z in piv.columns if z.startswith("MISO-") and z != "MISO-South"]
    mw_spread = float((piv[mw_zones].max(axis=1) - piv[mw_zones].min(axis=1)).max())
    s = (piv["MISO-South"] - piv["MISO-East"]).to_numpy(dtype=float)
    return s, mw_spread


def rdt_interval(spread: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    """PREREG Leg-2 classifier: per-hour [low, high] MW for the model RDT flow."""
    lo = np.full(HOURS, -RDT_S2N_DERATED)
    hi = np.full(HOURS, RDT_N2S_DERATED)
    unconstrained = np.abs(spread) <= 1.0
    rpe_only = (spread > 1.0) & (np.abs(spread - RPE_VALUE) <= 1.0)
    n2s = (spread > 1.0) & ~rpe_only
    s2n = spread < -1.0
    lo[rpe_only], hi[rpe_only] = 0.0, RDT_N2S_DERATED
    lo[n2s], hi[n2s] = RDT_N2S_DERATED, RDT_N2S_CONTRACT
    lo[s2n], hi[s2n] = -RDT_S2N_CONTRACT, -RDT_S2N_DERATED
    counts = {"unconstrained": int(unconstrained.sum()), "rpe_only": int(rpe_only.sum()),
              "n2s_binding": int(n2s.sum()), "s2n_binding": int(s2n.sum())}
    return lo, hi, counts


def pbc_binding_hours(year: int, token: str = "RDT_MW_SO") -> tuple[np.ndarray, np.ndarray]:
    """Measured RT RDT binding rows per hour: (majority >=6/12 mask, >=1-row mask).

    ``token`` "RDT_MW_SO" is the North->South constraint (the Leg-4 gate
    direction); "RDT_SO_MW" (South->North) is computed as reported-only
    coverage context.
    """
    counts = np.zeros(HOURS, dtype=int)
    with gzip.open(PBC / f"miso_pbc_rt_{year}.csv.gz", "rt") as fh:
        next(fh)
        for line in fh:
            parts = line.split(",", 2)
            if len(parts) < 2 or token not in parts[1]:
                continue
            ts = parts[0].strip()
            m, d, y = int(ts[0:2]), int(ts[3:5]), int(ts[6:10])
            if y != year:
                continue
            hh = int(ts[11:13]) - 1  # EST hour-beginning -> CST
            if hh < 0:
                prev = date(y, m, d) - pd.Timedelta(days=1)
                if prev.year != year:
                    continue
                h = _nonleap_hour(prev.year, prev.month, prev.day, 23)
            else:
                h = _nonleap_hour(y, m, d, hh)
            if h >= 0:
                counts[h] += 1
    return counts >= BINDING_MAJORITY, counts >= 1


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main() -> None:
    m174 = json.loads(M174.read_text())
    rec: dict = {
        "session": "miso-183",
        "prereg": "PREREG-miso183-south-basis-decomposition-2026-08-24.md",
        "keeper_bundle": "miso177_rho_B (unchanged; no LP spent)",
        "hunt": {
            "H1_rdt_flow_series": "NEGATIVE — Leg 3 falls away (reduced mapping)",
            "H2_regional_load": "rf_al (docs.misoenergy.org) intaken",
            "H3_regional_gen": "sr_gfm RT State Estimator sheet intaken",
        },
        "model_side_source": {
            "seam_net": "_miso174_seam_overimport_decomposition.json (miso169_gated_A, PRUNED; drift carried)",
            "rdt_interval": "miso177_rho_B system sidecar spread classifier (PREREG Leg-2 bands)",
        },
        "sign_convention": ("net_import = -mw; E_pool = pool net EXPORT; N_S + into South; "
                            "RDT^m + North->South"),
        "stage0_footing": {}, "stageL2_south_intake": {}, "stageL4_binding_contrast": {},
        "verdict": {},
    }

    s2_by_year: dict[int, dict] = {}
    d4_by_year: dict[int, dict] = {}

    for y in YEARS:
        ys = str(y)
        sets = hour_sets(y)
        w = diba_wide(y)
        south_cols = [c for c in w.columns if str(c) in SOUTH]
        pool_net_imp = w[south_cols].sum(axis=1, min_count=1).to_numpy(dtype=float)
        e_pool = -pool_net_imp  # + = MISO exports to the pool

        # ---- stage 0: footing + the two structural premises
        m174_meas = m174["stage2_measured_by_seam"][ys]
        rec["stage0_footing"][ys] = {
            "n_scarce": int(sets["scarce"].sum()),
            "measured_south_net_import_gw_annual": _mean(pool_net_imp, sets["annual"]) / 1000.0,
            "m174_committed": m174_meas.get("annual", {}).get("South_gw"),
            "duplicate_hour_diba_rows": int(w.attrs["duplicate_hour_diba_rows"]),
            "pair_level_premise": "one row per (hour, diba)" if w.attrs["duplicate_hour_diba_rows"] == 0
                                   else "VIOLATED — disclose",
        }

        # ---- Leg 2: measured N_S and the wedge
        l_s = regional_series(y, "load", "South")
        g_s = regional_series(y, "gen", "South")
        n_s = l_s - g_s
        l_tot = regional_series(y, "load", "MISO")
        g_tot = regional_series(y, "gen", "MISO_SUM")
        ni_tot = e930_ti_net_import(y)
        wedge = (l_tot - g_tot) - ni_tot
        # +-1h sensitivity (REPORTED-ONLY)
        n_s_p1 = regional_series(y, "load", "South", +1) - regional_series(y, "gen", "South", +1)
        n_s_m1 = regional_series(y, "load", "South", -1) - regional_series(y, "gen", "South", -1)

        spread, mw_spread = keeper_spread(y)
        lo, hi, cls_counts = rdt_interval(spread)
        m174_model = m174["stage3_model_by_seam"][ys]
        seam_key = {"annual": "annual", "summer": "summer", "scarce": "summer_scarce_rt200"}

        # Per-set classifier composition (PREREG: "per-set counts of each class").
        unc = np.abs(spread) <= 1.0
        rpe = (spread > 1.0) & (np.abs(spread - RPE_VALUE) <= 1.0)
        n2s_m = (spread > 1.0) & ~rpe
        s2n_m = spread < -1.0
        per_set_cls = {name: {"unconstrained": int((unc & mask).sum()),
                              "rpe_only": int((rpe & mask).sum()),
                              "n2s_binding": int((n2s_m & mask).sum()),
                              "s2n_binding": int((s2n_m & mask).sum())}
                       for name, mask in sets.items()}

        leg2 = {"classifier_counts": cls_counts,
                "classifier_counts_by_set": per_set_cls,
                "m174_separation_hours_note": (
                    "miso-174 section 5 counted 2432/2705/5086 nonzero South-Midwest "
                    "separation hours; this classifier's nonzero-spread total differs "
                    "slightly (the +-$1 dead band) and is reported per set above"),
                "midwest_copperplate_max_spread": mw_spread,
                "spread_levels_top": pd.Series(np.round(spread[np.abs(spread) > 1.0]))
                                       .value_counts().head(8).to_dict(),
                "identity_wedge_gw_by_set": {},
                "sets": {}}
        for name, mask in sets.items():
            seam = float(m174_model[seam_key[name]]["South_gw"])  # net import (+ into South)
            nsm_lo = _mean(lo, mask) / 1000.0 + seam
            nsm_hi = _mean(hi, mask) / 1000.0 + seam
            ns = _mean(n_s, mask) / 1000.0
            leg2["sets"][name] = {
                "measured_N_S_gw": ns,
                "measured_N_S_gw_shift_p1": _mean(n_s_p1, mask) / 1000.0,
                "measured_N_S_gw_shift_m1": _mean(n_s_m1, mask) / 1000.0,
                "model_N_S_gw_interval": [nsm_lo, nsm_hi],
                "model_seam_net_import_gw_cited": seam,
                "coverage_hours": int(np.isfinite(n_s[mask]).sum()),
                "n_hours": int(mask.sum()),
            }
            leg2["identity_wedge_gw_by_set"][name] = _mean(wedge, mask) / 1000.0
        sc = leg2["sets"]["scarce"]
        mid = 0.5 * (sc["model_N_S_gw_interval"][0] + sc["model_N_S_gw_interval"][1])
        dn = sc["measured_N_S_gw"] - mid
        s2_ends = [(sc["measured_N_S_gw"] - sc["model_N_S_gw_interval"][1]) / O_GAP[y],
                   (sc["measured_N_S_gw"] - sc["model_N_S_gw_interval"][0]) / O_GAP[y]]
        wsc = leg2["identity_wedge_gw_by_set"]["scarce"]
        leg2["s2"] = {"delta_N_scarce_gw": dn, "O_y_gw": O_GAP[y],
                      "s2_mid": dn / O_GAP[y], "s2_ends": s2_ends,
                      "s2_mid_wedge_minus": (dn - abs(wsc)) / O_GAP[y],
                      "s2_mid_wedge_plus": (dn + abs(wsc)) / O_GAP[y]}
        rec["stageL2_south_intake"][ys] = leg2
        s2_by_year[y] = leg2["s2"]

        # ---- Leg 4: binding contrast
        bind_maj, bind_any = pbc_binding_hours(y)
        s2n_maj, s2n_any = pbc_binding_hours(y, token="RDT_SO_MW")  # reported-only
        summer = sets["summer"]
        on, off = summer & bind_maj, summer & ~bind_maj
        legs = {}
        for c in south_cols:
            v = -w[c].to_numpy(dtype=float)  # net export
            legs[str(c)] = {"binding_mean_gw": _mean(v, on) / 1000.0,
                            "nonbinding_mean_gw": _mean(v, off) / 1000.0}
        d4 = _mean(e_pool, on) / 1000.0 - _mean(e_pool, off) / 1000.0
        on1, off1 = summer & bind_any, summer & ~bind_any
        d4_any = _mean(e_pool, on1) / 1000.0 - _mean(e_pool, off1) / 1000.0
        d4_by_year[y] = {
            "n_binding_maj_annual": int(bind_maj.sum()), "n_binding_any_annual": int(bind_any.sum()),
            "n_binding_maj_summer": int(on.sum()),
            "scarce_and_binding_maj": int((sets["scarce"] & bind_maj).sum()),
            "scarce_and_binding_any": int((sets["scarce"] & bind_any).sum()),
            "s2n_binding_maj_annual_reported": int(s2n_maj.sum()),
            "s2n_binding_any_annual_reported": int(s2n_any.sum()),
            "scarce_and_s2n_maj_reported": int((sets["scarce"] & s2n_maj).sum()),
            "scarce_and_s2n_any_reported": int((sets["scarce"] & s2n_any).sum()),
            "model_n2s_binding_hours": cls_counts["n2s_binding"],
            "E_pool_binding_mean_gw": _mean(e_pool, on) / 1000.0,
            "E_pool_nonbinding_mean_gw": _mean(e_pool, off) / 1000.0,
            "D4_gw": d4,
            "D4_gw_any_variant_reported": d4_any,
            "per_leg_net_export": legs,
        }
        rec["stageL4_binding_contrast"][ys] = d4_by_year[y]

    # ---- verdict (PREREG section 4, reduced mapping — Leg 3 unavailable)
    v = {"leg3": "unavailable (H-1 negative) — V-BASIS unreachable by construction"}
    s25 = s2_by_year[2025]
    d45 = d4_by_year[2025]["D4_gw"]
    transfer = all(e >= S2_TRANSFER for e in s25["s2_ends"])
    exonerated = all(abs(e) <= S2_EXONERATE for e in [s25["s2_mid"]]) and \
        all(e <= S2_EXONERATE for e in [max(s25["s2_ends"])])
    south_surplus = s25["s2_mid"] <= -S2_EXONERATE
    wheel_clean = np.isfinite(d45) and d45 <= D4_CLEAN_GW
    wheel_suggest = np.isfinite(d45) and d45 >= D4_SUGGEST_GW
    if transfer:
        v["verdict_2025"] = "V-TRANSFER"
    elif (exonerated or south_surplus) and wheel_clean:
        v["verdict_2025"] = "V-TRADE"
    elif (exonerated or south_surplus) and wheel_suggest:
        v["verdict_2025"] = "V-UNRESOLVED (wheel-carriage suggested but unprovable without R_t)"
    else:
        v["verdict_2025"] = "MIXED — components reported at full magnitude"
    v["components_2025"] = {"s2": s25, "D4_gw": d45,
                            "exonerated": bool(exonerated), "south_surplus": bool(south_surplus),
                            "transfer": bool(transfer), "wheel_clean": bool(wheel_clean),
                            "wheel_suggest": bool(wheel_suggest)}
    v["concurrence_2023"] = {"s2": s2_by_year[2023], "D4_gw": d4_by_year[2023]["D4_gw"]}
    v["reported_only_2024"] = {"s2": s2_by_year[2024], "D4_gw": d4_by_year[2024]["D4_gw"],
                               "note": "EIA-930 internal inconsistency year (r=0.8286)"}
    rec["verdict"] = v

    OUT.write_text(json.dumps(rec, indent=2, default=str))
    print(f"wrote {OUT}\n")

    for y in YEARS:
        ys = str(y)
        f = rec["stage0_footing"][ys]
        print(f"=== {y} footing: n_scarce={f['n_scarce']}  pool annual NI "
              f"{f['measured_south_net_import_gw_annual']:+.3f} GW (m174 {f['m174_committed']:+.3f})  "
              f"dup(hour,diba)={f['duplicate_hour_diba_rows']}")
        l2 = rec["stageL2_south_intake"][ys]
        print(f"    classifier: {l2['classifier_counts']}  midwest max spread {l2['midwest_copperplate_max_spread']:.4f}")
        for name in ("annual", "summer", "scarce"):
            s = l2["sets"][name]
            print(f"    {name:7s} N_S meas {s['measured_N_S_gw']:+.3f} GW "
                  f"(±1h {s['measured_N_S_gw_shift_m1']:+.3f}/{s['measured_N_S_gw_shift_p1']:+.3f}) "
                  f" model [{s['model_N_S_gw_interval'][0]:+.3f}, {s['model_N_S_gw_interval'][1]:+.3f}] "
                  f" wedge {l2['identity_wedge_gw_by_set'][name]:+.3f}  cov {s['coverage_hours']}/{s['n_hours']}")
        print(f"    s2: mid {l2['s2']['s2_mid']:+.3f}  ends [{l2['s2']['s2_ends'][0]:+.3f}, {l2['s2']['s2_ends'][1]:+.3f}] "
              f" wedge± [{l2['s2']['s2_mid_wedge_minus']:+.3f}, {l2['s2']['s2_mid_wedge_plus']:+.3f}]")
        d4 = rec["stageL4_binding_contrast"][ys]
        print(f"    L4: binding maj/any {d4['n_binding_maj_annual']}/{d4['n_binding_any_annual']} h "
              f"(model N2S {d4['model_n2s_binding_hours']} h)  scarce∩bind {d4['scarce_and_binding_maj']}"
              f"/{d4['scarce_and_binding_any']}  D4 {d4['D4_gw']:+.3f} GW")
        for c, lg in d4["per_leg_net_export"].items():
            print(f"        {c:6s} bind {lg['binding_mean_gw']:+.3f} / nonbind {lg['nonbinding_mean_gw']:+.3f} GW")
    print("\nVERDICT 2025:", rec["verdict"]["verdict_2025"])


if __name__ == "__main__":
    main()
