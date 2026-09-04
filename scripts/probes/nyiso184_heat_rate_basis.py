#!/usr/bin/env python3
"""nyiso-184 Phase 0 — gates G0–G4 of PREREG-nyiso184-stgas-heat-rate-basis, NO LP.

Every bar below is read from the pre-registration verbatim; nothing is chosen
here. Gates run in the pre-registered order and the probe returns on S0 (a G0
failure) before any later gate is scored.

* **G0** — the no-LP reconstruction (``scripts.lib.bundle_fleet``) reproduces
  nyiso-183's committed G4d ``model_hr`` per ``ST_GAS`` plant to ±0.005 and
  recovers Ravenswood's bases 9.50 (``ST_GAS``) / 8.80 (``CC_REGULAR``) ±0.01.
* **G1** — eGRID-2023 ``PLNT23``: ``PLHTRT/1000`` == the parquet's 8.800451
  and ``PLHTIAN/PLNGENAN`` == ``PLHTRT``, both to ≤ 1e-5 (relative).
* **G2** — the 2023-vintage ST-family rate at 2500 (a) inside the join's
  window, (b) ≥ the CAMPD-2023 steam-only gross running-hour HR, (c) its
  like-for-like ratio ``r`` inside the eight peers' ``[min, max]`` — the
  peers' range is computed and printed BEFORE Ravenswood's value.
* **G3** — Astoria's G4d ratio with the CAMPD stack-duplicate halves merged
  lands inside that year's eight-peer ``[min, max]`` in ≥ 2 of 3 years.
  **G3b** sizes the merit-panel consequence (no bar, no repair).
* **G4** — the footprint: every (plant, family) the artifact covers, with the
  incumbent rate, the fleet MW and class, and which class-specific mechanism
  keeps precedence; S3 if the applied set does not reach (2500, ST).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
for _p in (str(_REPO), str(_REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.config.paths import EIA_860_DIR, FLEET_DIR, PROCESSED_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.campd import (  # noqa: E402
    merge_stack_duplicate_units,
    stack_duplicate_mask,
)
from market_sim.data.egrid import _EGRID_FILES  # noqa: E402
from market_sim.data.fleet.eia860 import EIA_860_PARQUET_NAME  # noqa: E402
from market_sim.data.fleet.models import MIXED_FACILITY_STEAM_HR  # noqa: E402
from market_sim.pipeline.backcast_config import _NYISO_OFFER_CURVE  # noqa: E402
from scripts.data.derive_egrid_family_heat_rates import APPLIED_VINTAGE  # noqa: E402
from scripts.data.process_eia860 import EGRID_HR_WINDOW_BTU_KWH  # noqa: E402
from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402
from scripts.lib.outage_detect import (  # noqa: E402
    MERIT_HR_MAX,
    MERIT_HR_MIN,
    MIN_REAL_RUN_HOURS,
    REAL_RUN_CF,
)
from scripts.probes.nyiso183_g4c_offer_position import stgas_units  # noqa: E402
from scripts.probes.nyiso183_g4d_offer_anatomy import NAMES, measured_hr  # noqa: E402

KEEPER = _REPO / "results" / "calibration" / "nyiso177_vintage_B1p"
G4D = _REPO / "results" / "calibration" / "_nyiso183_g4d_offer_anatomy.json"
ARTIFACT = PROCESSED_DIR / "egrid_family_heat_rates_NYISO.csv"
RAW = _REPO / "data" / "raw"
YEARS = (2023, 2024, 2025)
ISO = "NYISO"
RAVENSWOOD = 2500
ASTORIA = 8906
PEERS = (2527, 2625, 2516, 2490, 2517, 2480, 8006, 2511)
# Tranche multipliers nyiso-183 §7 recovered the bases through (read, not set):
# the keeper's offer_curve_by_group is null, so the NYISO default curve prices
# it. ST_GAS committed 1.05 / peak 4.20; CC_REGULAR committed 0.90.
COMMITTED_MULT = float(_NYISO_OFFER_CURVE["ST_GAS"]["committed"])
PEAK_MULT = float(_NYISO_OFFER_CURVE["ST_GAS"]["peak"])
CC_COMMITTED_MULT = float(_NYISO_OFFER_CURVE["CC_REGULAR"]["committed"])
# Ravenswood bases nyiso-183 §7 published (the G0 anchors).
G0_ST_BASE, G0_CC_BASE = 9.50, 8.80

# PREREG §4 bars, verbatim.
G0_HR_TOL = 0.005
G0_BASE_TOL = 0.01
G1_REL_TOL = 1e-5
G3_MIN_YEARS = 2

GROUP_FAMILY = {
    "ST_GAS": "ST",
    "ST_CHP": "ST",
    "COAL": "ST",
    "CC_REGULAR": "CC",
    "CC_CHP": "CC",
    "CT_PEAKER": "GT",
    "CT_CHP": "GT",
}


def _plant_frame(state: dict) -> pd.DataFrame:
    fa = state["fleet_arrays"]
    return pd.DataFrame(
        {
            "plant": np.asarray(fa.plant_code).astype(int),
            "klass": np.asarray(fa.plant_group).astype(str),
            "cap_mw": np.asarray(fa.pmax, dtype=float),
            "heat_rate": np.asarray(fa.heat_rate, dtype=float),
        }
    )


def _groups(df: pd.DataFrame) -> dict[int, set[str]]:
    g: dict[int, set[str]] = {}
    for p, k in zip(df["plant"], df["klass"]):
        g.setdefault(int(p), set()).add(str(k))
    return g


def measured_hr_merged(year: int, facility: int) -> dict[str, float] | None:
    """Astoria's ST_GAS units with the RH/SH halves MERGED (heat summed, gross once).

    Same formula as ``measured_hr`` (Σ heatInput / Σ grossLoad over running
    hours, clipped), on the primary's gross with both paths' heat.
    """
    frames = []
    for st in campd.states_for_iso(ISO):
        path = RAW / "campd-unit-level" / f"{st}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(
            path,
            columns=[
                "facilityId",
                "unitId",
                "unitType",
                "date",
                "hour",
                "grossLoad",
                "heatInput",
            ],
        )
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[df["facilityId"] == facility]
        if not df.empty:
            frames.append(df)
    if not frames:
        return None
    df = pd.concat(frames, ignore_index=True)
    raw_units = df["unitId"].astype(str)
    df["unit"] = merge_stack_duplicate_units(df["facilityId"], raw_units)
    dup = stack_duplicate_mask(df["facilityId"], raw_units)
    df["gross"] = (
        pd.to_numeric(df["grossLoad"], errors="coerce").fillna(0.0).mask(dup, 0.0)
    )
    df["heat"] = pd.to_numeric(df["heatInput"], errors="coerce").fillna(0.0)
    # Boilers only (the model's ST_GAS members): exclude the combustion turbine.
    df = df[~df["unitType"].astype(str).str.contains("Combustion turbine", na=False)]
    per_hour = df.groupby(["unit", "date", "hour"], sort=False)[["gross", "heat"]].sum()
    out_rows = []
    for unit, g in per_hour.groupby(level="unit"):
        gross = g["gross"].to_numpy()
        heat = g["heat"].to_numpy()
        peak = float(gross.max()) if gross.size else 0.0
        if peak <= 0:
            continue
        run = gross / peak >= REAL_RUN_CF
        if int(run.sum()) < MIN_REAL_RUN_HOURS:
            continue
        gm, hm = float(gross[run].sum()), float(heat[run].sum())
        if gm <= 0:
            continue
        out_rows.append((unit, float(np.clip(hm / gm, MERIT_HR_MIN, MERIT_HR_MAX)), gm))
    if not out_rows:
        return None
    w = sum(gm for _, _, gm in out_rows)
    return {
        "hr": sum(hr * gm for _, hr, gm in out_rows) / w,
        "gross_gwh": w / 1000.0,
        "units": {u: round(hr, 3) for u, hr, _ in out_rows},
    }


def _campd_unit_totals(year: int, facilities: set[int]) -> pd.DataFrame:
    """Per (facility, unit): all-hours gross MWh, heat MMBtu, running-hour HR."""
    rows = []
    for st in campd.states_for_iso(ISO):
        path = RAW / "campd-unit-level" / f"{st}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(
            path, columns=["facilityId", "unitId", "grossLoad", "heatInput"]
        )
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[df["facilityId"].isin(facilities)]
        for (fac, uid), g in df.groupby(["facilityId", "unitId"], sort=False):
            gross = (
                pd.to_numeric(g["grossLoad"], errors="coerce").fillna(0.0).to_numpy()
            )
            heat = pd.to_numeric(g["heatInput"], errors="coerce").fillna(0.0).to_numpy()
            peak = float(gross.max()) if gross.size else 0.0
            run = (
                gross / peak >= REAL_RUN_CF if peak > 0 else np.zeros(len(gross), bool)
            )
            rows.append(
                {
                    "facility": int(fac),
                    "unit": str(uid),
                    "gross_mwh": float(gross.sum()),
                    "heat_mmbtu": float(heat.sum()),
                    "hr_all": float(heat.sum() / gross.sum())
                    if gross.sum() > 0
                    else None,
                    "hr_run": (
                        float(heat[run].sum() / gross[run].sum())
                        if run.sum() >= MIN_REAL_RUN_HOURS and gross[run].sum() > 0
                        else None
                    ),
                }
            )
    return pd.DataFrame(rows)


def _r_decomposition(
    year: int, members: set[tuple[int, str]], art: pd.DataFrame
) -> dict:
    """POST-HOC: factorise r for Ravenswood's ST + CC families and the peers."""
    yy = f"{APPLIED_VINTAGE % 100:02d}"
    path = FLEET_DIR / _EGRID_FILES[APPLIED_VINTAGE]
    gen = pd.read_excel(
        path,
        sheet_name=f"GEN{yy}",
        skiprows=1,
        usecols=["ORISPL", "GENID", "PRMVR", "GENNTAN"],
    )
    plnt = pd.read_excel(
        path,
        sheet_name=f"PLNT{yy}",
        skiprows=1,
        usecols=["ORISPL", "PLHTIAN", "PLNGENAN"],
    )
    facs = set(PEERS) | {RAVENSWOOD}
    tot = _campd_unit_totals(year, facs)
    out: dict = {
        "note": "POST-HOC locator, no bar; r = annual/loaded x heat-boundary x gross/net"
    }
    # Ravenswood steam family: eGRID GEN rows 1/2/3 <-> CAMPD units 10/20/30.
    rav = tot[tot["facility"] == RAVENSWOOD].set_index("unit")
    g_rav = gen[pd.to_numeric(gen["ORISPL"], errors="coerce") == RAVENSWOOD].copy()
    g_rav.index = g_rav["GENID"].astype(str)
    fam = art[(art["plant_id"] == RAVENSWOOD)].set_index("family")
    st_units = ["10", "20", "30"]
    st_gross = float(rav.loc[st_units, "gross_mwh"].sum())
    st_heat = float(rav.loc[st_units, "heat_mmbtu"].sum())
    st_run_hr = (
        float(rav.loc[st_units, "heat_mmbtu"].sum() / st_gross) if st_gross else None
    )
    # running-hour HR of the family = the G4d helper's statistic (gross-weighted).
    st_hr_run = None
    if not rav.loc[st_units, "hr_run"].isna().any():
        w = rav.loc[st_units, "gross_mwh"]
        st_hr_run = float((rav.loc[st_units, "hr_run"] * w).sum() / w.sum())
    out["ravenswood_ST"] = {
        "eGRID_family_hr": float(fam.loc["ST", "heat_rate_mmbtu_mwh"]),
        "eGRID_HTIAN": float(fam.loc["ST", "htian_mmbtu"]),
        "eGRID_GENNTAN": float(fam.loc["ST", "genntan_mwh"]),
        "campd_gross_all_hours_mwh": st_gross,
        "campd_heat_all_hours_mmbtu": st_heat,
        "campd_hr_all_hours": st_run_hr,
        "campd_hr_running_hours": st_hr_run,
        "factor_annual_over_loaded": None
        if not (st_run_hr and st_hr_run)
        else st_run_hr / st_hr_run,
        "factor_heat_boundary": float(fam.loc["ST", "htian_mmbtu"]) / st_heat
        if st_heat
        else None,
        "factor_gross_over_net": st_gross / float(fam.loc["ST", "genntan_mwh"]),
        "per_generator_net_over_gross": {
            f"gen {gid} / unit {uid}": (
                float(g_rav.loc[gid, "GENNTAN"]) / float(rav.loc[uid, "gross_mwh"])
                if gid in g_rav.index and rav.loc[uid, "gross_mwh"] > 0
                else None
            )
            for gid, uid in (("1", "10"), ("2", "20"), ("3", "30"))
        },
    }
    cc = rav.loc["UCC001"] if "UCC001" in rav.index else None
    if cc is not None and "CC" in fam.index:
        out["ravenswood_CC"] = {
            "eGRID_family_hr": float(fam.loc["CC", "heat_rate_mmbtu_mwh"]),
            "campd_hr_running_hours": cc["hr_run"],
            "r": float(fam.loc["CC", "heat_rate_mmbtu_mwh"]) / cc["hr_run"]
            if cc["hr_run"]
            else None,
            "factor_gross_over_net": float(cc["gross_mwh"])
            / float(fam.loc["CC", "genntan_mwh"]),
        }
    peers = {}
    for p in PEERS:
        units = [u for (f, u) in members if f == p]
        sub = tot[(tot["facility"] == p) & (tot["unit"].isin(units))]
        if sub.empty:
            continue
        prow = plnt[pd.to_numeric(plnt["ORISPL"], errors="coerce") == p]
        if prow.empty or pd.isna(prow["PLNGENAN"].iloc[0]):
            continue
        gross = float(sub["gross_mwh"].sum())
        heat = float(sub["heat_mmbtu"].sum())
        ok = sub.dropna(subset=["hr_run"])
        hr_run = (
            float((ok["hr_run"] * ok["gross_mwh"]).sum() / ok["gross_mwh"].sum())
            if not ok.empty
            else None
        )
        peers[p] = {
            "name": NAMES.get(p, ""),
            "factor_annual_over_loaded": (heat / gross) / hr_run
            if (gross and hr_run)
            else None,
            "factor_heat_boundary": float(prow["PLHTIAN"].iloc[0]) / heat
            if heat
            else None,
            "factor_gross_over_net": gross / float(prow["PLNGENAN"].iloc[0]),
            "plant_net_over_campd_steam_gross": float(prow["PLNGENAN"].iloc[0]) / gross
            if gross
            else None,
        }
    out["peers"] = peers
    return out


def run() -> dict:
    out: dict = {
        "session": "nyiso-184",
        "prereg": "results/calibration/PREREG-nyiso184-stgas-heat-rate-basis.md",
        "bundle": str(KEEPER.relative_to(_REPO)),
        "artifact": str(ARTIFACT.relative_to(_REPO)),
        "applied_vintage": APPLIED_VINTAGE,
        "bars": {
            "G0_hr_tol": G0_HR_TOL,
            "G0_base_tol": G0_BASE_TOL,
            "G1_rel_tol": G1_REL_TOL,
            "G2_window_btu_kwh": list(EGRID_HR_WINDOW_BTU_KWH),
            "G3_min_years": G3_MIN_YEARS,
        },
    }
    g4d = json.loads(G4D.read_text())

    # ---------------- G0 — instrument ----------------
    states: dict[int, dict] = {}
    g0 = {"years": {}, "fires": True}
    for year in YEARS:
        state, _ = reconstruct_bundle_fleet(KEEPER, year, verbose=True)
        states[year] = state
        df = _plant_frame(state)
        st = df[df["klass"] == "ST_GAS"]
        model_hr = (
            st.groupby("plant")
            .apply(
                lambda d: (
                    (d["heat_rate"] * d["cap_mw"]).sum() / max(d["cap_mw"].sum(), 1e-9)
                ),
                include_groups=False,
            )
            .to_dict()
        )
        committed = {
            int(r["plant"]): float(r["model_hr"])
            for r in g4d["years"][str(year)]["rows"]
        }
        worst = 0.0
        rows = []
        for plant, hr in model_hr.items():
            c = committed.get(int(plant))
            d = None if c is None else abs(float(hr) - c)
            worst = max(worst, d or 0.0)
            rows.append(
                {
                    "plant": int(plant),
                    "model_hr": round(float(hr), 4),
                    "committed": c,
                    "abs_diff": d,
                }
            )
        rav = df[df["plant"] == RAVENSWOOD]
        st_hr = sorted(set(np.round(rav.loc[rav["klass"] == "ST_GAS", "heat_rate"], 4)))
        cc_hr = sorted(
            set(np.round(rav.loc[rav["klass"] == "CC_REGULAR", "heat_rate"], 4))
        )
        base_st = min(st_hr) / COMMITTED_MULT if st_hr else None
        base_st_peak = max(st_hr) / PEAK_MULT if st_hr else None
        base_cc = min(cc_hr) / CC_COMMITTED_MULT if cc_hr else None
        ok = (
            worst <= G0_HR_TOL
            and base_st is not None
            and base_cc is not None
            and abs(base_st - G0_ST_BASE) <= G0_BASE_TOL
            and abs(base_st_peak - G0_ST_BASE) <= G0_BASE_TOL
            and abs(base_cc - G0_CC_BASE) <= G0_BASE_TOL
            and abs(base_st - MIXED_FACILITY_STEAM_HR[RAVENSWOOD]) <= G0_BASE_TOL
        )
        g0["years"][str(year)] = {
            "worst_abs_diff_vs_committed": round(worst, 5),
            "ravenswood_st_tranche_hr": st_hr,
            "ravenswood_cc_tranche_hr": cc_hr,
            "base_st_from_committed_tranche": None
            if base_st is None
            else round(base_st, 4),
            "base_st_from_peak_tranche": None
            if base_st_peak is None
            else round(base_st_peak, 4),
            "base_cc_from_committed_tranche": None
            if base_cc is None
            else round(base_cc, 4),
            "pass": bool(ok),
            "rows": rows,
        }
        g0["fires"] &= bool(ok)
    out["G0"] = g0
    print(
        json.dumps({k: v for k, v in g0.items() if k != "years"}),
        "\n",
        json.dumps(
            {
                y: {k: v for k, v in r.items() if k != "rows"}
                for y, r in g0["years"].items()
            },
            indent=1,
        ),
    )
    if not g0["fires"]:
        out["stop"] = "S0: G0 failed — instrument failure, nothing below scored"
        return out

    # ---------------- G1 — the join as an identity ----------------
    parquet = pd.read_parquet(
        EIA_860_DIR / EIA_860_PARQUET_NAME, columns=["plant_id", "heat_rate"]
    )
    parquet_hr = float(
        parquet.loc[parquet["plant_id"] == RAVENSWOOD, "heat_rate"].iloc[0]
    )
    plnt = pd.read_excel(
        FLEET_DIR / _EGRID_FILES[APPLIED_VINTAGE],
        sheet_name=f"PLNT{APPLIED_VINTAGE % 100:02d}",
        skiprows=1,
        usecols=["ORISPL", "PLHTIAN", "PLNGENAN", "PLHTRT"],
    )
    row = plnt[pd.to_numeric(plnt["ORISPL"], errors="coerce") == RAVENSWOOD].iloc[0]
    # eGRID publishes PLHTRT in Btu/kWh; PLHTIAN (MMBtu) / PLNGENAN (MWh) is
    # already MMBtu/MWh. INSTRUMENT REPAIR, disclosed: the first cut divided
    # the ratio by 1,000 a second time and read G1 as failed on a unit error
    # (pre-fix record preserved as _nyiso184_heat_rate_basis_prefix_g1unit.json);
    # the bar is untouched.
    plhtrt = float(row["PLHTRT"]) / 1000.0
    ratio = float(row["PLHTIAN"]) / float(row["PLNGENAN"])
    g1 = {
        "parquet_heat_rate": parquet_hr,
        "egrid_PLHTRT_mmbtu_mwh": plhtrt,
        "egrid_PLHTIAN_over_PLNGENAN": ratio,
        "rel_diff_parquet_vs_PLHTRT": abs(parquet_hr - plhtrt) / plhtrt,
        "rel_diff_PLHTRT_vs_ratio": abs(plhtrt - ratio) / plhtrt,
    }
    g1["fires"] = bool(
        g1["rel_diff_parquet_vs_PLHTRT"] <= G1_REL_TOL
        and g1["rel_diff_PLHTRT_vs_ratio"] <= G1_REL_TOL
    )
    out["G1"] = g1
    print("G1", json.dumps(g1, indent=1))
    if not g1["fires"]:
        out["stop"] = "S1: G1 did not fire — join hypothesis refuted; no repair built"
        return out

    # ---------------- G2 — the family construction at Ravenswood ----------------
    art = pd.read_csv(ARTIFACT)
    fam = art[(art["plant_id"] == RAVENSWOOD) & (art["family"] == "ST")]
    family_hr = float(fam["heat_rate_mmbtu_mwh"].iloc[0]) if not fam.empty else None
    groups23 = _groups(_plant_frame(states[2023]))
    meas23 = measured_hr(2023, stgas_units(2023, groups23))
    lo, hi = EGRID_HR_WINDOW_BTU_KWH
    g2 = {"family_hr_2023_vintage": family_hr}
    g2["G2a_in_window"] = bool(family_hr is not None and lo <= family_hr * 1000.0 <= hi)
    rav_meas = meas23.get(RAVENSWOOD, (None,))[0]
    g2["measured_2023_steam_only_gross_running_hr"] = rav_meas
    g2["G2b_ge_measured"] = bool(
        family_hr is not None and rav_meas is not None and family_hr >= rav_meas
    )
    # G2c: peers' like-for-like ratio FIRST (their plant PLHTRT as carried today).
    parquet_by_plant = (
        parquet.drop_duplicates("plant_id").set_index("plant_id")["heat_rate"].to_dict()
    )
    peer_r = {}
    for p in PEERS:
        m = meas23.get(p, (None,))[0]
        e = parquet_by_plant.get(p)
        if m and e and m > 0:
            peer_r[p] = {
                "name": NAMES.get(p, ""),
                "egrid_plant_hr": float(e),
                "measured_hr": float(m),
                "r": float(e) / float(m),
            }
    rs = [v["r"] for v in peer_r.values()]
    g2["peers_r"] = peer_r
    g2["peers_r_min"] = min(rs) if rs else None
    g2["peers_r_max"] = max(rs) if rs else None
    print("G2c peers' range computed first:", g2["peers_r_min"], g2["peers_r_max"])
    r_rav = None if (family_hr is None or not rav_meas) else family_hr / rav_meas
    g2["ravenswood_r_under_R1"] = r_rav
    g2["ravenswood_r_incumbent_9p5"] = (
        None if not rav_meas else MIXED_FACILITY_STEAM_HR[RAVENSWOOD] / rav_meas
    )
    g2["G2c_in_peer_range"] = bool(
        r_rav is not None and rs and min(rs) <= r_rav <= max(rs)
    )
    g2["fires"] = bool(
        g2["G2a_in_window"] and g2["G2b_ge_measured"] and g2["G2c_in_peer_range"]
    )
    out["G2"] = g2
    print("G2", json.dumps({k: v for k, v in g2.items() if k != "peers_r"}, indent=1))

    # ---------------- POST-HOC locator (no bar, not scored): WHERE the G2c
    # statistic's level comes from. r = (eGRID net-annual HR) / (CAMPD gross
    # running-hour HR) factorises EXACTLY into
    #   [CAMPD gross all-hours HR / CAMPD gross running-hour HR]   (annual vs loaded)
    # x [eGRID HTIAN / CAMPD heat all-hours]                        (heat boundary)
    # x [CAMPD gross all-hours MWh / eGRID GENNTAN]                 (gross -> net)
    # so each plant's r is decomposed into the three, from committed bytes.
    # Written AFTER the gate was read; the gate record above is untouched.
    out["POSTHOC_r_decomposition"] = _r_decomposition(
        2023, stgas_units(2023, groups23), art
    )
    print(
        "POST-HOC r decomposition", json.dumps(out["POSTHOC_r_decomposition"], indent=1)
    )

    # ---------------- G3 — Astoria, two objects ----------------
    g3 = {"years": {}, "hits": 0}
    for year in YEARS:
        rows = {int(r["plant"]): r for r in g4d["years"][str(year)]["rows"]}
        peers = [
            rows[p]["ratio_model_over_measured"]
            for p in PEERS
            if p in rows and rows[p]["ratio_model_over_measured"]
        ]
        model_hr = rows[ASTORIA]["model_hr"]
        merged = measured_hr_merged(year, ASTORIA)
        ratio_raw = rows[ASTORIA]["ratio_model_over_measured"]
        ratio_merged = None if merged is None else model_hr / merged["hr"]
        inside = bool(
            ratio_merged is not None and min(peers) <= ratio_merged <= max(peers)
        )
        g3["hits"] += int(inside)
        g3["years"][str(year)] = {
            "model_hr": model_hr,
            "measured_raw_halves": rows[ASTORIA]["measured_hr"],
            "measured_merged": None if merged is None else round(merged["hr"], 3),
            "merged_units": None if merged is None else merged["units"],
            "ratio_raw": ratio_raw,
            "ratio_merged": None if ratio_merged is None else round(ratio_merged, 3),
            "peer_cluster": [round(min(peers), 3), round(max(peers), 3)],
            "inside": inside,
        }
    g3["fires"] = g3["hits"] >= G3_MIN_YEARS
    # G3b — size only.
    ext = pd.read_csv(RAW / "campd-unit-outages-perunitmerit-NYISO.csv")
    lay = pd.read_csv(RAW / "campd-unit-outages-layup-perunitmerit-NYISO.csv")
    g3["G3b"] = {
        "astoria_rows_in_keeper_extract": int((ext["facility_id"] == ASTORIA).sum()),
        "astoria_window_days_in_keeper_extract": float(
            ext.loc[ext["facility_id"] == ASTORIA, "duration_days"].sum()
        ),
        "astoria_rows_in_layup_file": int((lay["facility_id"] == ASTORIA).sum()),
        "astoria_layup_days": float(
            lay.loc[lay["facility_id"] == ASTORIA, "duration_days"].sum()
        ),
        "panel_reads_raw_parquet": "outage_detect.build_merit_order_panel: pd.read_parquet, no stack_duplicate_mask/merge (code read)",
        "panel_hr_raw_vs_merged_2023": [
            g3["years"]["2023"]["measured_raw_halves"],
            g3["years"]["2023"]["measured_merged"],
        ],
    }
    out["G3"] = g3
    print("G3", json.dumps(g3, indent=1))

    # ---------------- G4 — footprint ----------------
    df23 = _plant_frame(states[2023])
    ct_art = pd.read_csv(PROCESSED_DIR / "campd_ct_heat_rates_NYISO.csv")
    ct_cov = set(ct_art.loc[ct_art["flag"] == "ok", "plant_code"].astype(int))
    chp_path = PROCESSED_DIR / "chp_power_only_heat_rates_NYISO.csv"
    chp_cov: set[int] = set()
    if chp_path.exists():
        chp_df = pd.read_csv(chp_path)
        chp_col = "plant_code" if "plant_code" in chp_df.columns else "plant_id"
        chp_cov = set(chp_df[chp_col].astype(int))
    foot = []
    for r in art.itertuples():
        rows = df23[
            (df23["plant"] == int(r.plant_id))
            & (df23["klass"].map(GROUP_FAMILY) == r.family)
        ]
        classes = sorted(set(rows["klass"]))
        prec = []
        if r.family == "GT" and int(r.plant_id) in ct_cov and "CT_PEAKER" in classes:
            prec.append("measured_ct_heat_rates keeps precedence on CT_PEAKER rows")
        if int(r.plant_id) in chp_cov and any(k.endswith("_CHP") for k in classes):
            prec.append("measured_chp_heat_rates keeps precedence on CHP rows")
        incumbent = (
            sorted(set(np.round(rows["heat_rate"] / COMMITTED_MULT, 3)))
            if not rows.empty
            else []
        )
        foot.append(
            {
                "plant": int(r.plant_id),
                "name": r.plant_name,
                "family": r.family,
                "family_hr": float(r.heat_rate_mmbtu_mwh),
                "plant_plhtrt": r.plant_plhtrt_mmbtu_mwh,
                "flag": r.flag,
                "fleet_mw_2023": round(float(rows["cap_mw"].sum()), 1),
                "fleet_classes": classes,
                "incumbent_base_hr_from_min_tranche_div_1p05": incumbent,
                "precedence": prec,
            }
        )
    applied_reaches = any(
        f["plant"] == RAVENSWOOD and f["family"] == "ST" and f["flag"] == "ok"
        for f in foot
    )
    out["G4"] = {"rows": foot, "applied_reaches_2500_ST": applied_reaches}
    if not applied_reaches:
        out["stop"] = "S3: applied set does not reach (2500, ST)"
    print("G4", pd.DataFrame(foot).drop(columns=["precedence"]).to_string(index=False))
    if not g2["fires"]:
        out["stop"] = "S2: G2 did not fire — no solve spent, R1 not proposed"
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        default=str(
            _REPO / "results" / "calibration" / "_nyiso184_heat_rate_basis.json"
        ),
    )
    args = ap.parse_args()
    res = run()
    Path(args.out).write_text(json.dumps(res, indent=2, default=str))
    print("\nstop:", res.get("stop", "none — G2 fired, A/B authorized"))
    print("written:", args.out)


if __name__ == "__main__":
    main()
