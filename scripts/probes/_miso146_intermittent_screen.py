"""miso-146 probe — an INTERMITTENT-RESOURCE SCREEN for MISO's masked offer corpus.

PREREG ``results/calibration/PREREG-miso146-intermittent-screen-2026-08-09.md``
(pushed before any adjudicating statistic).

**No LP solve, no keeper replay, no mechanism, no parameter.**  This probe
classifies rows of an INPUT corpus so that downstream lanes can state their
universe; nothing it produces enters the LP.

THE IDENTIFICATION
------------------
An intermittent resource's declared economic maximum is a **forecast**; a
thermal resource's is a **rating**.  Three features from declarations alone
(PREREG §4.1), computed per ``unit_code`` per year per market over the landed
Jun 1 - Aug 31 window, with ``C`` the unit's own p99 ``ecomax_mw``:

* ``interior_frac`` — share of declaring hours with ``0.05C < ecomax < 0.95C``
* ``step_frac``     — share of consecutive declaring hour-pairs moving > 0.02C
* ``n_levels_frac`` — distinct ecomax levels (1 % of C grain) / declaring hours
* ``night_ratio``   — mean ecomax h01-04 / mean ecomax h12-14 (solar signature)

Decision rule, fixed a priori in PREREG §4.2 and NOT moved:
``interior_frac > 0.50 AND step_frac > 0.50`` -> INTERMITTENT.

TRAP 8 — THE SCREEN THAT FINDS WHAT IT WAS BUILT TO FIND
--------------------------------------------------------
``step_price_usd_per_mwh`` is **excluded from the feature set by
construction**: :func:`load_declarations` never reads the price column, and the
assertion in :func:`unit_features` fails loudly if it ever appears.  Offer price
is the HELD-OUT validation attribute (P-3b), and EIA-860 is a second control
sharing no column with the corpus at all (P-2/P-3).

TRAP 5 — CLASS BY THE BACK DOOR
--------------------------------
The screen is strictly TWO-WAY.  The NON-INTERMITTENT population is never
partitioned, no statistic here conditions on a thermal class, and the
wind/solar sub-split is declared non-load-bearing in PREREG §4.3 (it exists
only because EIA-860 publishes wind and solar separately).

Probe hygiene (miso-140b §6): repo root on ``sys.path`` and
``load_zonal_shares`` asserted non-None, via ``_miso143_stack.hygiene``.

Usage::

    python scripts/probes/_miso146_intermittent_screen.py \
        [--out results/calibration/_miso146_intermittent_screen.json] [--no-gc]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))  # probe hygiene, miso-140b §6 -- REPO ROOT
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _miso143_stack import YEARS, hygiene, windows  # noqa: E402
from _miso145_offer_conduct import (  # noqa: E402
    load_real_segments,
    price_at_pctl,
)
from market_sim.config import paths  # noqa: E402

MARKETS = ("DA", "RT")

# --- PREREG §4.2: the decision rule, fixed a priori and NOT moved -----------
THR_INTERIOR = 0.50
THR_STEP = 0.50
#: PREREG §4.2 sensitivity sweep — both thresholds moved together.
SWEEP = (0.30, 0.40, 0.50, 0.60, 0.70)
#: PREREG §4.1 feature constants.
INTERIOR_LO, INTERIOR_HI = 0.05, 0.95
STEP_REL = 0.02
LEVEL_GRAIN = 0.01
NIGHT_HOD, DAY_HOD = (1, 2, 3, 4), (12, 13, 14)
#: PREREG §4.3 — solar-like sub-label.  REPORTED, never load-bearing.
THR_NIGHT_SOLAR = 0.15
#: PREREG §5, P-1 — the middle band whose MW share tests bimodality.
MIDBAND = (0.30, 0.70)

#: miso-145's committed 2025 JJA h12-17 corpus readings (PREREG §3, G-F0).
#: The totals are LOAD-WEIGHTED (the conduct probe); the <= $0 masses are
#: UNWEIGHTED window means (the cheap-mass probe).  Both constructions are
#: reproduced on their OWN basis and labelled — never blended.
GF0_COMMITTED = {
    "unweighted_total_gw": {"RT": 106.140, "DA": 131.871},
    "unweighted_mw_le_0_gw": {"RT": 19.945, "DA": 17.654},
    "loadweighted_total_gw": {"RT": 107.007, "DA": 131.969},
}
GF0_TOL_GW = 0.05

#: PREREG §3, G-F1 — miso-142/143's six committed window deficits (TRAP 7).
COMMITTED_DEFICITS = {
    "2023|W1_jun_jul_h8_20": -4.750,
    "2023|JJA_h12_17": -8.333,
    "2024|W1_jun_jul_h8_20": -10.676,
    "2024|JJA_h12_17": -10.671,
    "2025|W1_jun_jul_h8_20": -30.999,
    "2025|JJA_h12_17": -30.435,
}
GF1_TOL = 0.01
TAIL_USD = 200.0

#: PREREG §5 — the EIA-860 control brackets, restated here as the bars the
#: probe scores itself against.  Reference side only; recomputed live by
#: :func:`eia860_control` and asserted to match these registered values.
P2_BRACKET_MW = {2023: (23751.0, 47294.0), 2024: (26724.0, 53032.0), 2025: (32839.0, 64671.0)}
P3_BRACKET_MW = {2023: (83754.0, 160529.0), 2024: (83839.0, 160692.0), 2025: (84331.0, 161634.0)}
P3B_INT_MIN_SHARE = 0.60
P3B_NONINT_MAX_SHARE = 0.15
P4_MIN_SHARE = 0.70
P1_MAX_MIDBAND_SHARE = 0.20
#: PREREG §6, G-C — the two-sided verdict bars on the screened LEVEL term.
GC_REINSTATE_USD = 18.0
GC_CONFIRM_USD = 9.0


# ------------------------------------------------------- the declaration side


def load_declarations(year: int, market: str) -> pd.DataFrame:
    """Per unit-hour declared capability for the whole landed summer.

    TRAP 8: the offer PRICE column is deliberately NOT in the column list.
    """
    path = paths.clean_path("energy-offers", iso="MISO", year=year, market=market)
    df = pd.read_parquet(
        path, columns=["unit_code", "interval_start_local", "ecomax_mw"]
    )
    df = df.drop_duplicates(["unit_code", "interval_start_local"])
    # The -1 sentinel is not a capability declaration; PREREG §4.1 clips at 0.
    df["ecomax"] = np.clip(df["ecomax_mw"].to_numpy(float), 0.0, None)
    df["hod"] = df["interval_start_local"].dt.hour
    return df.sort_values(["unit_code", "interval_start_local"], kind="stable")


def unit_features(decl: pd.DataFrame) -> pd.DataFrame:
    """The PREREG §4.1 features, one row per ``unit_code``."""
    assert not any("price" in c for c in decl.columns), (
        "TRAP 8: offer price must never enter the feature set"
    )
    cap = decl.groupby("unit_code")["ecomax"].quantile(0.99).rename("C")
    d = decl.join(cap, on="unit_code")
    C = d["C"].to_numpy(float)
    e = d["ecomax"].to_numpy(float)
    pos = C > 0.0

    d["_interior"] = pos & (e > INTERIOR_LO * C) & (e < INTERIOR_HI * C)
    # Consecutive-hour moves within a unit; the first row of each unit has no
    # predecessor and is excluded from the denominator by construction.
    same = d["unit_code"].to_numpy() == np.roll(d["unit_code"].to_numpy(), 1)
    same[0] = False
    prev = np.roll(e, 1)
    d["_pair"] = same
    d["_moved"] = same & pos & (np.abs(e - prev) > STEP_REL * C)
    d["_level"] = np.where(pos, np.round(e / np.maximum(C, 1e-9) / LEVEL_GRAIN), -1.0)

    g = d.groupby("unit_code")
    night = d[d["hod"].isin(NIGHT_HOD)].groupby("unit_code")["ecomax"].mean()
    day = d[d["hod"].isin(DAY_HOD)].groupby("unit_code")["ecomax"].mean()

    feat = pd.DataFrame(
        {
            "C": cap,
            "n_hours": g.size(),
            "interior_frac": g["_interior"].mean(),
            "step_frac": g["_moved"].sum() / g["_pair"].sum().replace(0, np.nan),
            "n_levels_frac": g["_level"].nunique() / g.size(),
            "mean_ecomax": g["ecomax"].mean(),
        }
    )
    feat["night_ratio"] = (night / day.replace(0.0, np.nan)).reindex(feat.index)
    return feat.fillna({"step_frac": 0.0})


def classify(feat: pd.DataFrame, thr_interior: float, thr_step: float) -> pd.Series:
    """PREREG §4.2 — the two-way rule.  Returns a boolean ``is_intermittent``."""
    return (feat["interior_frac"] > thr_interior) & (feat["step_frac"] > thr_step)


# --------------------------------------------------------- the EIA-860 control


def eia860_control() -> dict:
    """PREREG §5/§10 — MISO registry capability in service by Jul 1 of each year.

    Reference side only.  The corpus is MASKED; NO per-unit join to EIA-860
    exists or is attempted anywhere in this session.
    """
    root = REPO / "data/raw/eia-860"
    gen = pd.read_parquet(root / "eia860_generator_operable.parquet")
    plant = pd.read_parquet(root / "eia860_plant.parquet")
    ba = plant[["Plant Code", "Balancing Authority Code"]].drop_duplicates("Plant Code")
    m = gen.merge(ba, on="Plant Code", how="left")
    m = m[m["Balancing Authority Code"].astype(str).str.upper() == "MISO"].copy()
    m["np_mw"] = pd.to_numeric(m["Nameplate Capacity (MW)"], errors="coerce")
    m["sum_mw"] = pd.to_numeric(m["Summer Capacity (MW)"], errors="coerce")
    oy = pd.to_numeric(m["Operating Year"], errors="coerce")
    om = pd.to_numeric(m["Operating Month"], errors="coerce").fillna(1)

    out: dict = {}
    for year in YEARS:
        ins = (oy < year) | ((oy == year) & (om <= 7))
        s = m[ins]
        vre = s[s["Energy Source 1"].isin(["WND", "SUN"])]
        non = s[~s["Energy Source 1"].isin(["WND", "SUN"])]
        out[str(year)] = {
            "vre_nameplate_all_mw": round(float(vre["np_mw"].sum()), 1),
            "vre_nameplate_ge20mw_mw": round(
                float(vre.loc[vre["np_mw"] >= 20, "np_mw"].sum()), 1
            ),
            "wnd_nameplate_all_mw": round(
                float(vre.loc[vre["Energy Source 1"] == "WND", "np_mw"].sum()), 1
            ),
            "sun_nameplate_all_mw": round(
                float(vre.loc[vre["Energy Source 1"] == "SUN", "np_mw"].sum()), 1
            ),
            "nonvre_summer_all_mw": round(float(non["sum_mw"].sum()), 1),
            "nonvre_summer_ge20mw_mw": round(
                float(non.loc[non["np_mw"] >= 20, "sum_mw"].sum()), 1
            ),
            "n_vre_gen": int(len(vre)),
            "n_nonvre_gen": int(len(non)),
        }
    return out


# ------------------------------------------------------------------ the gates


def gate_gf0(seg_by_market: dict[str, pd.DataFrame], n_hours: int, wgt_by_market) -> dict:
    """G-F0 (HARD STOP) — reproduce miso-145's committed universe readings."""
    rec: dict = {"tolerance_gw": GF0_TOL_GW, "markets": {}}
    worst = 0.0
    for market, segs in seg_by_market.items():
        unw_total = float(segs["seg_mw"].sum() / n_hours / 1000.0)
        unw_cheap = float(
            segs.loc[segs["seg_price"] <= 0.0, "seg_mw"].sum() / n_hours / 1000.0
        )
        lw_total = float(wgt_by_market[market])
        d = {
            "unweighted_total_gw": round(unw_total, 3),
            "committed_unweighted_total_gw": GF0_COMMITTED["unweighted_total_gw"][market],
            "unweighted_mw_le_0_gw": round(unw_cheap, 3),
            "committed_unweighted_mw_le_0_gw": GF0_COMMITTED["unweighted_mw_le_0_gw"][market],
            "loadweighted_total_gw": round(lw_total, 3),
            "committed_loadweighted_total_gw": GF0_COMMITTED["loadweighted_total_gw"][market],
        }
        d["delta_unweighted_total_gw"] = round(
            unw_total - d["committed_unweighted_total_gw"], 4
        )
        d["delta_unweighted_mw_le_0_gw"] = round(
            unw_cheap - d["committed_unweighted_mw_le_0_gw"], 4
        )
        d["delta_loadweighted_total_gw"] = round(
            lw_total - d["committed_loadweighted_total_gw"], 4
        )
        worst = max(
            worst,
            abs(d["delta_unweighted_total_gw"]),
            abs(d["delta_unweighted_mw_le_0_gw"]),
            abs(d["delta_loadweighted_total_gw"]),
        )
        rec["markets"][market] = d
    rec["worst_abs_delta_gw"] = round(worst, 4)
    rec["verdict"] = "PASS" if worst <= GF0_TOL_GW else "FAIL"
    return rec


def population_readings(
    segs: pd.DataFrame, label: pd.Series, n_hours: int
) -> dict:
    """Per-population MW/composition on a segment frame carrying ``unit_code``.

    TRAP 1: BOTH populations are reported in full (MW, units, share) and the
    cheap mass is NEVER netted between them.
    """
    is_int = segs["unit_code"].map(label).fillna(False).to_numpy(bool)
    out: dict = {}
    for name, sel in (("intermittent", is_int), ("non_intermittent", ~is_int)):
        s = segs[sel]
        out[name] = {
            "hour_mean_offered_gw": round(float(s["seg_mw"].sum() / n_hours / 1000.0), 3),
            "hour_mean_le_0_gw": round(
                float(s.loc[s["seg_price"] <= 0.0, "seg_mw"].sum() / n_hours / 1000.0), 3
            ),
            "n_units": int(s["unit_code"].nunique()),
            "n_segments": int(s.shape[0]),
        }
        tot = max(1e-9, float(s["seg_mw"].sum()))
        out[name]["share_of_own_mw_le_0"] = round(
            float(s.loc[s["seg_price"] <= 0.0, "seg_mw"].sum()) / tot, 4
        )
        # POST-HOC, NOT PRE-REGISTERED, and labelled as such wherever quoted:
        # the <= $0 mass decomposed by DECLARATION (must-run / self-schedule).
        # These are declarations, never fuel labels -- no thermal class is
        # resolved or inferred anywhere (TRAP 5).
        cheap = s[s["seg_price"] <= 0.0]
        out[name]["posthoc_le_0_decomposition"] = {
            "must_run_gw": round(
                float(cheap.loc[cheap["must_run"], "seg_mw"].sum() / n_hours / 1000.0), 3
            ),
            "self_scheduled_gw": round(
                float(cheap.loc[cheap["self_sched_mw"] > 0.0, "seg_mw"].sum() / n_hours / 1000.0),
                3,
            ),
            "neither_gw": round(
                float(
                    cheap.loc[
                        ~cheap["must_run"] & ~(cheap["self_sched_mw"] > 0.0), "seg_mw"
                    ].sum()
                    / n_hours
                    / 1000.0
                ),
                3,
            ),
            "n_units_must_run": int(cheap.loc[cheap["must_run"], "unit_code"].nunique()),
        }
    return out


# --------------------------------------------------------------------- driver


def run(out_path: Path | None = None, run_gc: bool = True) -> dict:
    """Execute G-F0, P-1..P-4, the sweep, and (conditionally) G-F1 + G-C."""
    hygiene()
    wins = windows()
    jja = np.nonzero(wins["JJA_h12_17"])[0]
    control = eia860_control()

    res: dict = {
        "prereg": "results/calibration/PREREG-miso146-intermittent-screen-2026-08-09.md",
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "posture": (
            "NO LP, NO SOLVE, NO ARM, NO ScenarioConfig FIELD, NO PARAMETER. "
            "A classification of an INPUT corpus (PREREG §2c)."
        ),
        "rule": {
            "interior_frac_gt": THR_INTERIOR,
            "step_frac_gt": THR_STEP,
            "note": "PREREG §4.2, fixed a priori, NOT moved after any measurement",
        },
        "eia860_control": control,
        "features": {},
        "screen": {},
        "predictions": {},
        "sweep": {},
    }

    # --- features + classification, every year and market ------------------
    labels: dict[tuple[int, str], pd.Series] = {}
    for year in YEARS:
        for market in MARKETS:
            decl = load_declarations(year, market)
            feat = unit_features(decl)
            lab = classify(feat, THR_INTERIOR, THR_STEP)
            labels[(year, market)] = lab

            solar_like = lab & (feat["night_ratio"] < THR_NIGHT_SOLAR)
            key = f"{year}|{market}"
            res["features"][key] = {
                "n_units": int(len(feat)),
                "sum_C_mw": round(float(feat["C"].sum()), 1),
                "mean_n_hours": round(float(feat["n_hours"].mean()), 1),
            }
            res["screen"][key] = {
                "intermittent": {
                    "n_units": int(lab.sum()),
                    "sum_C_mw": round(float(feat.loc[lab, "C"].sum()), 1),
                },
                "non_intermittent": {
                    "n_units": int((~lab).sum()),
                    "sum_C_mw": round(float(feat.loc[~lab, "C"].sum()), 1),
                },
                # PREREG §4.3 -- REPORTED, never load-bearing.
                "solar_like_reported_only": {
                    "n_units": int(solar_like.sum()),
                    "sum_C_mw": round(float(feat.loc[solar_like, "C"].sum()), 1),
                },
                "wind_like_reported_only": {
                    "n_units": int((lab & ~solar_like).sum()),
                    "sum_C_mw": round(float(feat.loc[lab & ~solar_like, "C"].sum()), 1),
                },
            }

            # --- P-1 bimodality, MW-weighted over interior_frac -------------
            midband = (feat["interior_frac"] >= MIDBAND[0]) & (
                feat["interior_frac"] <= MIDBAND[1]
            )
            tot_C = max(1e-9, float(feat["C"].sum()))
            res["predictions"].setdefault("P1_bimodality", {})[key] = {
                "midband_mw_share": round(float(feat.loc[midband, "C"].sum()) / tot_C, 4),
                "bar_lt": P1_MAX_MIDBAND_SHARE,
                "verdict": (
                    "PASS"
                    if float(feat.loc[midband, "C"].sum()) / tot_C < P1_MAX_MIDBAND_SHARE
                    else "FAIL"
                ),
                "histogram_mw_by_interior_decile": [
                    round(
                        float(
                            feat.loc[
                                (feat["interior_frac"] >= i / 10.0)
                                & (feat["interior_frac"] < (i + 1) / 10.0 + (i == 9) * 1e-9),
                                "C",
                            ].sum()
                        ),
                        1,
                    )
                    for i in range(10)
                ],
            }

            # --- P-2 / P-3 magnitude controls (DA book is the reference) ----
            if market == "DA":
                lo2, hi2 = P2_BRACKET_MW[year]
                lo3, hi3 = P3_BRACKET_MW[year]
                sc_i = float(feat.loc[lab, "C"].sum())
                sc_n = float(feat.loc[~lab, "C"].sum())
                res["predictions"].setdefault("P2_positive_control", {})[str(year)] = {
                    "screened_intermittent_sum_C_mw": round(sc_i, 1),
                    "bracket_mw": [lo2, hi2],
                    "verdict": "PASS" if lo2 <= sc_i <= hi2 else ("FAIL_LOW" if sc_i < lo2 else "FAIL_HIGH"),
                    "gating": False,
                }
                res["predictions"].setdefault("P3_negative_control", {})[str(year)] = {
                    "screened_non_intermittent_sum_C_mw": round(sc_n, 1),
                    "bracket_mw": [lo3, hi3],
                    "verdict": "PASS" if lo3 <= sc_n <= hi3 else ("FAIL_LOW" if sc_n < lo3 else "FAIL_HIGH"),
                    "gating": True,
                }

            # --- the sweep (TRAP 6) -----------------------------------------
            res["sweep"].setdefault(key, {})
            for t in SWEEP:
                l2 = classify(feat, t, t)
                res["sweep"][key][f"thr_{t:g}"] = {
                    "n_intermittent": int(l2.sum()),
                    "sum_C_mw": round(float(feat.loc[l2, "C"].sum()), 1),
                }

    # --- 2025 JJA h12-17: G-F0, P-3b, P-4 on the segment frame --------------
    n_h = int(jja.size)
    seg25 = {
        m: load_real_segments(2025, m, jja, with_meta=True) for m in MARKETS
    }
    lw_totals = _loadweighted_totals(2025, jja, seg25)
    res["gates"] = {"G_F0": gate_gf0(seg25, n_h, lw_totals)}

    res["predictions"]["P3b_heldout_price"] = {}
    res["predictions"]["P4_contamination_removed"] = {}
    for market in MARKETS:
        pops = population_readings(seg25[market], labels[(2025, market)], n_h)
        res["screen"][f"2025|{market}|JJA_h12_17_populations"] = pops
        res["predictions"]["P3b_heldout_price"][market] = {
            "intermittent_share_le_0": pops["intermittent"]["share_of_own_mw_le_0"],
            "non_intermittent_share_le_0": pops["non_intermittent"]["share_of_own_mw_le_0"],
            "bars": {"intermittent_min": P3B_INT_MIN_SHARE, "non_intermittent_max": P3B_NONINT_MAX_SHARE},
            "verdict": (
                "PASS"
                if pops["intermittent"]["share_of_own_mw_le_0"] >= P3B_INT_MIN_SHARE
                and pops["non_intermittent"]["share_of_own_mw_le_0"] <= P3B_NONINT_MAX_SHARE
                else "FAIL"
            ),
            "gating": True,
        }
        committed = GF0_COMMITTED["unweighted_mw_le_0_gw"][market]
        share = pops["intermittent"]["hour_mean_le_0_gw"] / max(1e-9, committed)
        res["predictions"]["P4_contamination_removed"][market] = {
            "intermittent_le_0_gw": pops["intermittent"]["hour_mean_le_0_gw"],
            "committed_total_le_0_gw": committed,
            "share_of_cheap_mass": round(float(share), 4),
            "bar_min": P4_MIN_SHARE,
            "verdict": "PASS" if share >= P4_MIN_SHARE else "FAIL",
            "gating": True,
        }

    # POST-HOC, NOT PRE-REGISTERED: the size of the crossing the screen is
    # supposed to close.  The model's fleet carries NO wind/solar rows (they
    # are LP decision variables), so the crossing is the corpus's intermittent
    # OFFERED capability against the keeper's own VRE DISPATCH in the SAME
    # hours -- miso-145's committed 16.286 GW, reproduced here, not quoted.
    from _miso143_stack import sidecar_classes  # noqa: PLC0415

    piv = sidecar_classes(2025)
    vre = {
        c: round(float(piv[c].to_numpy(float)[jja].mean() / 1000.0), 3)
        for c in ("wind", "solar")
        if c in piv.columns
    }
    vre["wind_plus_solar_gw"] = round(sum(vre.values()), 3)
    res["posthoc_crossing_2025_JJA"] = {
        "keeper_sidecar_vre_dispatch": vre,
        "committed_miso145_vre_dispatch_gw": 16.286,
        "screened_intermittent_offered_gw": {
            m: res["screen"][f"2025|{m}|JJA_h12_17_populations"]["intermittent"][
                "hour_mean_offered_gw"
            ]
            for m in MARKETS
        },
    }

    res["branch"] = _branch(res)
    # PREREG §6: G-C's LEVEL leg is reported under BOTH surviving branches --
    # under BUILT it carries the two-sided verdict, under BOUNDED it is
    # reported with its bound and marked NOT-LICENSING (no verdict fires and
    # miso-145's standing rule STANDS).
    gc_ok = res["branch"] in ("BRANCH-SCREEN-BUILT", "BRANCH-SCREEN-BOUNDED")
    if run_gc and gc_ok and res["gates"]["G_F0"]["verdict"] == "PASS":
        res["G_C"] = _run_gc(labels, licensing=res["branch"] == "BRANCH-SCREEN-BUILT")
    else:
        res["G_C"] = {
            "run": False,
            "reason": f"branch={res['branch']}, G-F0={res['gates']['G_F0']['verdict']}",
        }

    if out_path:
        out_path.write_text(json.dumps(res, indent=1))
    return res


def _loadweighted_totals(year: int, hours: np.ndarray, seg: dict) -> dict:
    """Load-weighted window-mean offered capability, miso-145's own construction."""
    from _miso137_c3a_gap_decomposition import model_hourly

    _h, _p, w_model, _z = model_hourly(year)
    w = w_model[hours]
    wgt = w / max(1e-9, w.sum())
    out = {}
    for market, segs in seg.items():
        tot = segs.groupby("hour")["seg_mw"].sum().reindex(hours).fillna(0.0).to_numpy()
        out[market] = float((tot * wgt).sum() / 1000.0)
    return out


def _branch(res: dict) -> str:
    """PREREG §6 — the pre-committed branch, decided by the GATING predictions."""
    if res["gates"]["G_F0"]["verdict"] != "PASS":
        return "BRANCH-INSTRUMENT-FAIL"
    p3b = all(v["verdict"] == "PASS" for v in res["predictions"]["P3b_heldout_price"].values())
    p4 = all(v["verdict"] == "PASS" for v in res["predictions"]["P4_contamination_removed"].values())
    p3 = all(v["verdict"] == "PASS" for v in res["predictions"]["P3_negative_control"].values())
    if not p3b:
        return "BRANCH-NO-SCREEN"
    if p3 and p4:
        return "BRANCH-SCREEN-BUILT"
    return "BRANCH-SCREEN-BOUNDED"


def _run_gc(labels: dict, licensing: bool = True) -> dict:
    """G-C — miso-145's LEVEL term restated on the SCREENED universe.

    Under ``BRANCH-SCREEN-BUILT`` (``licensing=True``) the PREREG §6 two-sided
    verdict fires.  Under ``BRANCH-SCREEN-BOUNDED`` the same numbers are
    reported but NO verdict fires and the reading is marked NOT-LICENSING.
    Either way this produces a FINDING and at most an owner escalation — never
    an arm (PREREG §9, rules 19/24).
    """
    from _miso137_c3a_gap_decomposition import actual_hourly, model_hourly
    from _miso145_offer_conduct import model_block, model_curve_readings

    wins = windows()
    out: dict = {"run": True, "gf1": {}, "level": {}}
    for year in YEARS:
        mb = model_block(year)
        rt_actual, _da = actual_hourly(year)
        _h, _p, w_model, _z = model_hourly(year)
        union = np.nonzero(np.logical_or.reduce(list(wins.values())))[0]
        seg_cache = {
            m: load_real_segments(year, m, union, with_meta=True) for m in MARKETS
        }
        for wname, sel in wins.items():
            ok = sel & np.isfinite(mb["p1_price"]) & np.isfinite(rt_actual)
            hours = np.nonzero(ok)[0]
            anchor, target = mb["p1_price"][hours], rt_actual[hours]
            w = w_model[hours]
            wgt = w / max(1e-9, w.sum())
            model_lw = float((anchor * w).sum() / max(1e-9, w.sum()))
            actual_lw = float((target * w).sum() / max(1e-9, w.sum()))
            key = f"{year}|{wname}"
            out["gf1"][key] = {
                "deficit": round(model_lw - actual_lw, 3),
                "committed": COMMITTED_DEFICITS[key],
                "delta": round(model_lw - actual_lw - COMMITTED_DEFICITS[key], 4),
            }
            ordinary = target <= TAIL_USD

            for bracket in ("lo", "hi"):
                mcr = model_curve_readings(mb, hours, bracket, anchor)
                pc = np.clip(
                    mcr["mw_below_anchor"] / np.maximum(1e-9, mcr["mw_total"]), 0.0, 1.0
                )
                for market in MARKETS:
                    segs_all = seg_cache[market]
                    segs = segs_all[segs_all["hour"].isin(hours)]
                    lab = labels[(year, market)]
                    is_int = segs["unit_code"].map(lab).fillna(False).to_numpy(bool)
                    for uni, s in (
                        ("all", segs),
                        ("screened_non_intermittent", segs[~is_int]),
                    ):
                        rp = price_at_pctl(
                            hours,
                            s["hour"].to_numpy(),
                            s["seg_price"].to_numpy(float),
                            s["seg_mw"].to_numpy(float),
                            pc,
                        )
                        fin = np.isfinite(rp)
                        wl = wgt * fin
                        wl = wl / max(1e-9, wl.sum())
                        wo = wgt * ordinary * fin
                        wo = wo / max(1e-9, wo.sum())
                        out["level"].setdefault(key, {}).setdefault(bracket, {}).setdefault(
                            market, {}
                        )[uni] = {
                            "LEVEL_term_usd_per_mwh": round(
                                float(((rp - anchor) * wl)[fin].sum()), 3
                            ),
                            "ordinary_LEVEL_term_usd_per_mwh": round(
                                float(((rp - anchor) * wo)[fin].sum()), 3
                            ),
                            "real_at_model_percentile_usd": round(
                                float((rp * wl)[fin].sum()), 3
                            ),
                            "n_segments": int(s.shape[0]),
                        }

    headline = out["level"]["2025|JJA_h12_17"]["lo"]["RT"]["screened_non_intermittent"][
        "LEVEL_term_usd_per_mwh"
    ]
    out["headline_screened_LEVEL_2025_JJA_RT_lo"] = headline
    out["licensing"] = licensing
    out["verdict"] = (
        (
            "REINSTATED"
            if headline >= GC_REINSTATE_USD
            else ("CONFIRMED-ABSENT" if headline <= GC_CONFIRM_USD else "INDETERMINATE")
        )
        if licensing
        else "NOT-LICENSING (BRANCH-SCREEN-BOUNDED -- PREREG §6; no verdict fires)"
    )
    out["bars"] = {"reinstate_ge": GC_REINSTATE_USD, "confirm_absent_le": GC_CONFIRM_USD}
    out["gf1_verdict"] = (
        "PASS"
        if max(abs(v["delta"]) for v in out["gf1"].values()) <= GF1_TOL
        else "FAIL"
    )
    return out


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        default="results/calibration/_miso146_intermittent_screen.json",
        type=Path,
    )
    ap.add_argument("--no-gc", action="store_true", help="skip the G-C level leg")
    args = ap.parse_args()
    res = run(out_path=args.out, run_gc=not args.no_gc)
    print(f"G-F0 {res['gates']['G_F0']['verdict']} "
          f"(worst |Δ| {res['gates']['G_F0']['worst_abs_delta_gw']} GW)")
    for pid in ("P1_bimodality", "P2_positive_control", "P3_negative_control",
                "P3b_heldout_price", "P4_contamination_removed"):
        block = res["predictions"][pid]
        print(f"{pid}: " + ", ".join(
            f"{k}={v.get('verdict')}" for k, v in block.items()
        ))
    print(f"BRANCH: {res['branch']}")
    if res["G_C"].get("run"):
        print(f"G-C: {res['G_C']['verdict']} "
              f"(screened LEVEL {res['G_C']['headline_screened_LEVEL_2025_JJA_RT_lo']}), "
              f"G-F1 {res['G_C']['gf1_verdict']}")
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
