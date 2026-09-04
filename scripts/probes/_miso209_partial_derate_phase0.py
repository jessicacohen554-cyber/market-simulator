"""miso-209 phase 0 — the coal-side availability object: does the unit-grain
partial-derate layer (``unit_partial_outage_windows``) carry it? (zero-solve)

miso-208 located the model's summer-2025 shoulder surplus on the COAL side
(model coal +3.43 GW over EIA-930 at 97.7 % of the model's own capability) and
bounded MISO's published unplanned record at 7.05 GW raw / 4.94 GW
feasibility-clipped on the 52 shoulder days.  This probe measures the one
registered, fuel-identified, unit-grain form that could carry that quantity —
the FROZEN partial-plateau detector run on MISO's coal units
(``scripts/data/derive_campd_unit_outages.py --partial-windows --iso MISO``) —
through the PRODUCTION consumer, per population, 2023-2025:

  W1  what the extract holds (rows, units, coal-only, derate factors);
  W2  the shoulder-day removed MW (nominal and effective) by region and band,
      against the bracket [3.4, 7.05] GW; W2b the SHALLOW revealed sub-ceiling
      gap the frozen form cannot see (diagnostic);
  W3  double-count census: plateau unit-hours inside the armed windows, and
      the statistical coal layer vs the window layers on the shoulder days;
  W4  the re-priced lift of the W2 MW (miso-208's engine), share of the gap;
  W5  2023/2024 (leave-one-year-out);
  W6  physical feasibility vs EIA-930 metered coal+gas daily max;
  R-208 miso-208's coal-side excess re-scored net of the layer.

PREREG ``results/calibration/PREREG-miso209-partial-derate-phase0-2026-09-04.md``
pushed at ``b7ed8e21`` BEFORE the extract was derived.  Rule 22: 2023-2025
only.  No LP is solved.

Usage::

    PYTHONPATH=src python3 scripts/probes/_miso209_partial_derate_phase0.py
"""

from __future__ import annotations

import dataclasses
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso208_find_the_supply as m208  # noqa: E402  (re-points the keeper)
from _miso134_ct_night_order_screen import (  # noqa: E402
    build_year,
    keeper_config,
    keeper_prices,
)
from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    _unit_outage_factors_from_events,
    outage_hour_mask,
    unit_outage_derate_factors,
    unit_outage_event_window,
    unit_outage_maxgen_derate_factors,
    unit_outage_short_derate_factors,
    unit_partial_outage_derate_factors,
)
from scripts.data import derive_thermal_tranches as dtt  # noqa: E402
from scripts.lib.outage_detect import _plateau_state  # noqa: E402

m207 = m208.m207
KEEPER = m208.KEEPER
OUT = REPO / "results/calibration/_miso209_partial_derate_phase0.json"
PRODUCTION_PARTIAL_CSV = RAW_DATA_DIR / "campd-partial-outages-MISO.csv"
# The PRODUCTION extract carries 0 rows (W1): the deriver's revealed-availability
# filter drops every partial plateau by construction (a running unit "reveals"
# availability). W2-W6 are therefore measured on a DIAGNOSTIC extract derived
# with the deriver's own --no-inmerit-filter switch, written OUTSIDE data/raw
# (never consumable by a solve); its path is passed in MISO209_PARTIAL_CSV.
PARTIAL_CSV = Path(os.environ.get("MISO209_PARTIAL_CSV", str(PRODUCTION_PARTIAL_CSV)))
STD_CSV = RAW_DATA_DIR / "campd-unit-outages-MISO.csv"
SHORT_CSV = RAW_DATA_DIR / "campd-unit-outages-short-MISO.csv"
MAXGEN_CSV = RAW_DATA_DIR / "campd-unit-outages-maxgen-unitroute-MISO.csv"

YEARS = (2023, 2024, 2025)
HOURS = 8760
COAL_POOL = m207.COAL_POOL
GAS = m207.GAS_CLASSES
BRACKET_GW = (3.4, 7.05)
LICENSE = 0.25
BASELOAD_CF = 0.55
NET_ADJ_GROSS_ONLY = (
    0.93  # coal parasitic share for plants without a measured factor (disclosed)
)
REGION_OF_ZONE = {
    "MISO-West": "North",
    "MISO-Plains": "North",  # straddles North/Central (IA vs MO) — disclosed
    "MISO-Illinois": "Central",
    "MISO-Indiana": "Central",
    "MISO-East": "Central",
    "MISO-South": "South",
}
BOILER_TOKENS = ("boiler", "fired", "stoker", "cyclone", "fluidized")


def _hoy_day_mask(start, stop_excl, year: int) -> np.ndarray:
    return outage_hour_mask(start, stop_excl, year, HOURS)


def unit_window_masks(
    df: pd.DataFrame, year: int, start_col: str, end_col: str, hour_grain: bool
) -> dict:
    """{(facility_id, unit_id): bool[HOURS]} for one extract in ``year``."""
    out: dict[tuple[int, str], np.ndarray] = {}
    if df.empty:
        return out
    for r in df.itertuples(index=False):
        if start_col == "outage_start":
            s, e = unit_outage_event_window(r, hour_grain)
        else:
            s, e = (
                pd.Timestamp(getattr(r, start_col)),
                pd.Timestamp(getattr(r, end_col)),
            )
        m = _hoy_day_mask(s, e, year)
        if not m.any():
            continue
        key = (int(r.facility_id), str(r.unit_id))
        out[key] = out.get(key, np.zeros(HOURS, bool)) | m
    return out


def main() -> None:  # noqa: PLR0915
    cfg0 = keeper_config()
    zon = pd.read_parquet(m208.ZONAL)
    m208rec = json.loads(m208.OUT.read_text())["years"]
    mon = m207._hour_month()
    jj = np.where(np.isin(mon, (6, 7)))[0]
    hod = np.arange(HOURS) % 24
    bins_path = getattr(cfg0, "campd_bins_path", None)
    kw = dict(
        cc_steam_part_reclass=bool(getattr(cfg0, "cc_steam_part_reclass", False)),
        cc_nameplate_basis=bool(getattr(cfg0, "unit_outage_lp_capacity_basis", False)),
        fleet_status_scope=bool(getattr(cfg0, "unit_outage_fleet_status_scope", False)),
        st_capacity_basis=bool(getattr(cfg0, "unit_outage_st_capacity_basis", False)),
        per_unit_clip=bool(getattr(cfg0, "unit_outage_per_unit_clip", False)),
    )
    part = pd.read_csv(PARTIAL_CSV) if PARTIAL_CSV.exists() else pd.DataFrame()
    std = pd.read_csv(STD_CSV)
    short = pd.read_csv(SHORT_CSV)
    mg = pd.read_csv(MAXGEN_CSV)
    report: dict = {
        "charter": "miso-209 phase 0 — the coal-side availability object through unit_partial_outage_windows; zero-solve; nothing armed.",
        "prereg": "results/calibration/PREREG-miso209-partial-derate-phase0-2026-09-04.md @ b7ed8e21",
        "keeper": "2026-09-03-miso-202-unitclip",
        "extract": str(PARTIAL_CSV),
        "production_extract_rows": int(len(pd.read_csv(PRODUCTION_PARTIAL_CSV)))
        if PRODUCTION_PARTIAL_CSV.exists()
        else None,
        "w1_extract": {
            "exists": bool(PARTIAL_CSV.exists()),
            "rows": int(len(part)),
            "rows_by_group": {
                str(k): int(v) for k, v in part["plant_group"].value_counts().items()
            }
            if len(part)
            else {},
            "rows_by_year": {
                str(k): int(v)
                for k, v in pd.to_datetime(part["outage_start"])
                .dt.year.value_counts()
                .sort_index()
                .items()
            }
            if len(part)
            else {},
            "distinct_units": int(part.groupby(["facility_id", "unit_id"]).ngroups)
            if len(part)
            else 0,
            "distinct_plants": int(part["facility_id"].nunique()) if len(part) else 0,
            "derate_factor_mean": round(float(part["derate_factor"].mean()), 3)
            if len(part)
            else None,
            "derate_factor_p10_p50_p90": [
                round(float(x), 3)
                for x in np.percentile(part["derate_factor"], [10, 50, 90])
            ]
            if len(part)
            else None,
            "duration_days_mean": round(float(part["duration_days"].mean()), 1)
            if len(part)
            else None,
            "removed_mw_days_total": round(
                float(
                    (
                        (1 - part["derate_factor"])
                        * part["unit_capacity_mw"]
                        * part["duration_days"]
                    ).sum()
                ),
                0,
            )
            if len(part)
            else 0,
        },
        "consumer_flags": kw,
        "w1_filter_trace_2025": (
            json.loads(Path(os.environ["MISO209_FILTER_TRACE"]).read_text())
            if os.environ.get("MISO209_FILTER_TRACE")
            else None
        ),
        "w1_filter_trace_note": (
            "the production deriver detected these plateaus and DROPPED every one at "
            "scripts/lib/outage_detect.filter_revealed_outages: clause 1 drops a span in "
            "which the unit RAN (cf >= REAL_RUN_CF 0.05) through >= 24 high-net-load "
            "hours; a partial plateau is a running unit by definition, so it is dropped "
            "whenever it overlaps >= 24 high hours and fails the down/full-stop clauses "
            "otherwise — the partial shape is inert by construction wherever the "
            "EIA-930 net-load file exists"
        ),
        "years": {},
    }
    print(json.dumps(report["w1_extract"]), flush=True)

    for year in YEARS:
        y: dict = {}
        rt = m207.hub_series(zon, year, "rt")
        price_df, demand = keeper_prices(year)
        price_df = price_df.reindex(range(HOURS))
        sysd = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysd = sysd[sysd["pass"] == "P1"]
        num = sysd.assign(pw=sysd["price"] * sysd["demand"]).groupby("hour")["pw"].sum()
        den = sysd.groupby("hour")["demand"].sum()
        price_lw = (num / den).reindex(range(HOURS)).to_numpy()
        ch = m207.keeper_class_hourly(year)
        a = rt[jj]
        rank = (a.argsort().argsort() / len(a)) * 100.0
        thr99 = float(np.nanpercentile(a, 99.0))
        tail = jj[a >= thr99]
        shoulder = jj[(rank >= 75.0) & (a < thr99)]
        other = np.array(sorted(set(jj) - set(shoulder) - set(tail)))
        day_other = other[np.isin(hod[other], range(10, 21))]
        bands = {
            "p75-90": jj[(rank >= 75.0) & (rank < 90.0)],
            "p90-95": jj[(rank >= 90.0) & (rank < 95.0)],
            "p95-99": jj[(rank >= 95.0) & (a < thr99)],
        }
        pops = {"SHOULDER": shoulder, "TAIL": tail}
        gaps = {k: float(price_lw[v].mean() - rt[v].mean()) for k, v in pops.items()}
        y["n1"] = {
            "n_shoulder": int(shoulder.size),
            "n_tail": int(tail.size),
            "gap": {k: round(v, 3) for k, v in gaps.items()},
            "m208_gap": m208rec[str(year)]["populations"]["gap_lw_minus_rt"],
        }
        shoulder_days = np.array(sorted(set((shoulder // 24).tolist())))
        tail_days = np.array(sorted(set((tail // 24).tolist())))
        other_days = np.array(sorted(set((day_other // 24).tolist())))

        # ---- fleet chain ---------------------------------------------------
        cfg = dataclasses.replace(cfg0, weather_year=year, mode="backcast")
        _raw, fleet, arrays, _fp, mc, _zn = build_year(cfg, year)
        mc = np.asarray(mc, dtype=np.float64)
        groups = np.array([str(g.plant_group or "") for g in fleet], dtype=object)
        zones = np.array([str(g.zone) for g in fleet], dtype=object)
        codes = np.array([int(getattr(g, "plant_code", 0) or 0) for g in fleet])
        avail = np.asarray(arrays.availability, dtype=np.float64)
        if avail.ndim == 1:
            avail = np.broadcast_to(avail[:, None], (len(fleet), HOURS))
        pmax = np.asarray(arrays.pmax, dtype=np.float64)
        avail_mw = pmax[:, None] * avail
        coal_sel = groups == "COAL"
        coal_codes = sorted(set(codes[coal_sel].tolist()))
        cap_bin = {c: float(pmax[coal_sel & (codes == c)].sum()) for c in coal_codes}
        avail_bin = {
            c: (avail_mw[coal_sel & (codes == c)].sum(axis=0) / cap_bin[c])
            if cap_bin[c] > 0
            else np.ones(HOURS)
            for c in coal_codes
        }
        zone_of_code = {}
        for c in coal_codes:
            zs = zones[coal_sel & (codes == c)]
            zone_of_code[c] = str(pd.Series(zs).mode().iloc[0]) if len(zs) else ""

        # ---- N-2: production consumer vs own accumulation -------------------
        pf = (
            _unit_outage_factors_from_events(part, year, HOURS, bins_path, "MISO", **kw)
            if len(part)
            else unit_partial_outage_derate_factors(
                year, HOURS, bins_path, iso="MISO", **kw
            )
        )
        pf_coal = {k[0]: v for k, v in pf.items() if k[1] == "COAL"}
        own = {}
        if len(part):
            for code, g in part.groupby("facility_id"):
                rem = np.zeros(HOURS)
                for uid, gu in g.groupby("unit_id"):
                    ucap = float(gu["unit_capacity_mw"].iloc[0])
                    r_u = np.zeros(HOURS)
                    for r in gu.itertuples(index=False):
                        s, e = unit_outage_event_window(r, False)
                        r_u += (
                            _hoy_day_mask(s, e, year)
                            * (1.0 - float(r.derate_factor))
                            * ucap
                        )
                    rem += np.minimum(r_u, ucap)
                pcap = float(g["plant_capacity_mw"].iloc[0])
                own[int(code)] = (
                    1.0 - np.minimum(1.0, rem / pcap) if pcap > 0 else np.ones(HOURS)
                )
        n2 = []
        for c, m_own in own.items():
            m_cons = pf_coal.get(c)
            if m_cons is None:
                n2.append(
                    {
                        "code": c,
                        "consumer_has_bin": False,
                        "own_removed_shoulder_gw": round(
                            float((1 - m_own[shoulder]).mean() * cap_bin.get(c, 0.0))
                            / 1e3,
                            4,
                        ),
                    }
                )
                continue
            n2.append(
                {
                    "code": c,
                    "consumer_has_bin": True,
                    "max_abs_diff_shoulder": round(
                        float(
                            np.abs(m_own[shoulder] - np.asarray(m_cons)[shoulder]).max()
                        ),
                        4,
                    ),
                }
            )
        y["n2_consumer_vs_own"] = {
            "bins_in_extract": len(own),
            "bins_in_consumer": len(pf_coal),
            "max_abs_diff": round(
                max([r.get("max_abs_diff_shoulder", 0.0) for r in n2] or [0.0]), 4
            ),
            "bins_missing_from_consumer": [
                r["code"] for r in n2 if not r["consumer_has_bin"]
            ],
            "PASS": bool(
                max([r.get("max_abs_diff_shoulder", 0.0) for r in n2] or [0.0]) <= 0.01
            ),
        }

        # ---- window layers (armed) and the statistical residual -----------
        std_f = unit_outage_derate_factors(
            year,
            HOURS,
            bins_path,
            iso="MISO",
            mixed_gas_routing=bool(
                getattr(cfg0, "unit_outage_mixed_gas_routing", False)
            ),
            **kw,
        )
        short_f = unit_outage_short_derate_factors(
            year, HOURS, bins_path, iso="MISO", **kw
        )
        mg_f = unit_outage_maxgen_derate_factors(
            year,
            HOURS,
            iso="MISO",
            cc_steam_part_reclass=kw["cc_steam_part_reclass"],
            cc_nameplate_basis=kw["cc_nameplate_basis"],
            mixed_gas_routing=bool(
                getattr(cfg0, "unit_outage_mixed_gas_routing", False)
            ),
        )
        removed_nom = np.zeros(HOURS)
        removed_eff = np.zeros(HOURS)
        removed_by_region = {r: np.zeros(HOURS) for r in ("North", "Central", "South")}
        window_removed = np.zeros(HOURS)
        stat_removed = np.zeros(HOURS)
        coal_capability = np.zeros(HOURS)
        n_active_bins = np.zeros(HOURS)
        for c in coal_codes:
            capc = cap_bin[c]
            if capc <= 0:
                continue
            coal_capability += capc * avail_bin[c]
            w = np.ones(HOURS)
            for layer in (std_f, short_f, mg_f):
                v = layer.get((c, "COAL"))
                if v is not None:
                    w = w * np.asarray(v, float)
            window_removed += capc * (1.0 - w)
            stat_removed += capc * np.maximum(0.0, w - avail_bin[c])
            m = pf_coal.get(c)
            if m is None:
                continue
            m = np.asarray(m, float)
            removed_nom += capc * (1.0 - m)
            removed_eff += capc * avail_bin[c] * (1.0 - m)
            n_active_bins += m < 1.0 - 1e-9
            reg = REGION_OF_ZONE.get(zone_of_code.get(c, ""), "Central")
            removed_by_region[reg] += capc * avail_bin[c] * (1.0 - m)

        def _pop(idx):
            return {
                "removed_nominal_gw_mean": round(
                    float(removed_nom[idx].mean()) / 1e3, 3
                ),
                "removed_effective_gw_mean": round(
                    float(removed_eff[idx].mean()) / 1e3, 3
                ),
                "removed_effective_gw_max": round(
                    float(removed_eff[idx].max()) / 1e3, 3
                ),
                "active_bins_mean": round(float(n_active_bins[idx].mean()), 2),
                "by_region_effective_gw": {
                    r: round(float(v[idx].mean()) / 1e3, 3)
                    for r, v in removed_by_region.items()
                },
                "central_share": round(
                    float(
                        removed_by_region["Central"][idx].sum()
                        / max(1e-9, removed_eff[idx].sum())
                    ),
                    3,
                ),
                "window_layers_removed_gw_mean": round(
                    float(window_removed[idx].mean()) / 1e3, 3
                ),
                "statistical_layer_removed_gw_mean": round(
                    float(stat_removed[idx].mean()) / 1e3, 3
                ),
                "coal_capability_gw_mean": round(
                    float(coal_capability[idx].mean()) / 1e3, 3
                ),
                "coal_nameplate_gw": round(sum(cap_bin.values()) / 1e3, 3),
            }

        y["w2_removed"] = {
            k: _pop(v)
            for k, v in {**pops, "OTHER_JJ_DAYTIME": day_other, **bands}.items()
        }
        y["w2_removed"]["SHOULDER"]["in_bracket"] = bool(
            BRACKET_GW[0]
            <= y["w2_removed"]["SHOULDER"]["removed_effective_gw_mean"]
            <= BRACKET_GW[1]
        )

        # ---- W3 overlap census (unit-hours) --------------------------------
        if len(part):
            p_masks = unit_window_masks(part, year, "outage_start", "outage_end", False)
            armed = {}
            for dfx, sc, ec in (
                (std, "outage_start", "outage_end"),
                (short, "outage_start", "outage_end"),
            ):
                for k, v in unit_window_masks(
                    dfx, year, sc, ec, "outage_start_hour" in dfx.columns
                ).items():
                    armed[k] = armed.get(k, np.zeros(HOURS, bool)) | v
            for k, v in unit_window_masks(
                mg, year, "window_start", "window_end", False
            ).items():
                armed[k] = armed.get(k, np.zeros(HOURS, bool)) | v
            tot = ov = 0
            tot_sh = ov_sh = 0
            for k, pm in p_masks.items():
                am = armed.get(k, np.zeros(HOURS, bool))
                tot += int(pm.sum())
                ov += int((pm & am).sum())
                tot_sh += int(pm[shoulder].sum())
                ov_sh += int((pm & am)[shoulder].sum())
            y["w3_overlap"] = {
                "plateau_unit_hours": tot,
                "overlapping_armed_unit_hours": ov,
                "overlap_share": round(ov / tot, 4) if tot else None,
                "overlap_share_shoulder_hours": round(ov_sh / tot_sh, 4)
                if tot_sh
                else None,
            }
        else:
            y["w3_overlap"] = {"plateau_unit_hours": 0}

        # ---- W4 lift -------------------------------------------------------
        y["w4_lift"] = {
            k: m208.with_share(
                m208.lift(v, mc, avail_mw, zones, price_df, removed_eff[v]), gaps[k]
            )
            for k, v in pops.items()
        }
        y["w4_lift"]["SHOULDER_nominal"] = m208.with_share(
            m208.lift(shoulder, mc, avail_mw, zones, price_df, removed_nom[shoulder]),
            gaps["SHOULDER"],
        )

        # ---- W6 feasibility (miso-208's construction + the layer) ----------
        pop_sel = np.isin(groups, m208.POP_GROUPS) & (pmax > 0)
        c_pop = float(pmax[pop_sel].sum())
        offline_m = (pmax[pop_sel][:, None] * (1.0 - avail[pop_sel])).sum(axis=0)
        ft = pd.read_parquet(RAW_DATA_DIR / "MISO_fueltype.parquet")
        loc = pd.to_datetime(ft["period"], utc=True).dt.tz_convert(
            m208.EST_TZ
        ) - pd.Timedelta(hours=2)
        cg = (
            ft.assign(loc=loc)[ft["fueltype"].isin(["COL", "NG"])]
            .groupby("loc")["value_mwh"]
            .sum()
        )
        cg = cg[cg.index.year == year]
        dmax_meas = cg.groupby(cg.index.normalize()).max()
        dmax_meas = {
            (t.month, t.day): float(v)
            for t, v in dmax_meas.items()
            if not (t.month == 2 and t.day == 29)
        }
        w6 = {}
        for name, days in (
            ("SHOULDER", shoulder_days),
            ("TAIL", tail_days),
            ("OTHER_JJ_DAYTIME", other_days),
        ):
            viol = []
            for d in days:
                stamp = m207._stamp(year, int(d) * 24)[:10]
                gm = dmax_meas.get((int(stamp[5:7]), int(stamp[8:10])))
                if gm is None:
                    continue
                m_d = float(offline_m[d * 24 : (d + 1) * 24].mean())
                r_d = float(removed_eff[d * 24 : (d + 1) * 24].mean())
                capped = c_pop - m_d - r_d
                if capped < gm:
                    viol.append(
                        {
                            "day": stamp,
                            "capped_gw": round(capped / 1e3, 2),
                            "measured_max_gw": round(gm / 1e3, 2),
                            "layer_caused": bool(c_pop - m_d >= gm),
                        }
                    )
            w6[name] = {
                "n_days": int(len(days)),
                "n_violation_days": len(viol),
                "n_layer_caused": int(sum(v["layer_caused"] for v in viol)),
                "days": viol,
            }
        y["w6_feasibility"] = w6

        # ---- R-208 + W2b: CAMPD coal, net-adjusted; shallow sub-ceiling gap ----
        states = campd.states_for_iso("MISO")
        dfu = campd.load_campd_hourly(states, [year], prefer_unit_level=True)
        factors = dtt._parasitic_factor_map()
        cap_np, primary = dtt._fleet_nameplate_and_group("MISO")
        coal_plants = {c for c, g in primary.items() if g == "COAL"}
        dfu = dfu[dfu["plant_id"].astype(int).isin(coal_plants)]
        net_adj = np.zeros(HOURS)
        gross_coal = np.zeros(HOURS)
        n_fac = n_nofac = 0
        for pid, sub in dfu.groupby("plant_id", observed=True):
            s = np.zeros(HOURS)
            hoy = sub["hour_of_year"].to_numpy()
            gross = np.nan_to_num(sub["gross_mw"].to_numpy(), nan=0.0)
            ok = (hoy >= 0) & (hoy < HOURS)
            np.add.at(s, hoy[ok], gross[ok])
            gross_coal += s
            f = factors.get(int(pid))
            if f is None:
                net_adj += s * NET_ADJ_GROSS_ONLY
                n_nofac += 1
            else:
                net_adj += s * float(f)
                n_fac += 1
        e = m208.e930_year(year)
        s930 = m208rec[str(year)]["v_key_930"]["winner"]
        col930 = np.asarray(e["COL"], float)[
            np.clip(np.arange(HOURS) + s930, 0, HOURS - 1)
        ]
        model_coal = (
            ch.loc[COAL_POOL].to_numpy() if COAL_POOL in ch.index else np.zeros(HOURS)
        )
        r208 = {}
        for k, idx in {**pops, "OTHER_JJ_DAYTIME": day_other}.items():
            r208[k] = {
                "model_coal_dispatch_gw": round(float(model_coal[idx].mean()) / 1e3, 3),
                "model_coal_capability_gw": round(
                    float(coal_capability[idx].mean()) / 1e3, 3
                ),
                "capability_minus_partial_layer_gw": round(
                    float((coal_capability[idx] - removed_eff[idx]).mean()) / 1e3, 3
                ),
                "campd_coal_gross_gw": round(float(gross_coal[idx].mean()) / 1e3, 3),
                "campd_coal_net_adjusted_gw": round(
                    float(net_adj[idx].mean()) / 1e3, 3
                ),
                "e930_coal_gw": round(float(np.nanmean(col930[idx])) / 1e3, 3),
                "excess_capability_over_net_adjusted_gw": round(
                    float(
                        (coal_capability[idx] - removed_eff[idx] - net_adj[idx]).mean()
                    )
                    / 1e3,
                    3,
                ),
                "excess_dispatch_over_net_adjusted_gw": round(
                    float((model_coal[idx] - net_adj[idx]).mean()) / 1e3, 3
                ),
                "excess_dispatch_over_e930_gw": round(
                    float(np.nanmean(model_coal[idx] - col930[idx])) / 1e3, 3
                ),
            }
        r208["plants_with_factor"] = n_fac
        r208["plants_gross_only"] = n_nofac
        y["r208_coal_excess_rescored"] = r208

        # W2b — shallow sub-ceiling gap on qualifying coal units
        std_masks = unit_window_masks(
            std[pd.to_datetime(std["outage_end"]).dt.year >= year],
            year,
            "outage_start",
            "outage_end",
            "outage_start_hour" in std.columns,
        )
        armed_all = dict(std_masks)
        for dfx, sc, ec in ((short, "outage_start", "outage_end"),):
            for k2, v in unit_window_masks(
                dfx, year, sc, ec, "outage_start_hour" in dfx.columns
            ).items():
                armed_all[k2] = armed_all.get(k2, np.zeros(HOURS, bool)) | v
        for k2, v in unit_window_masks(
            mg, year, "window_start", "window_end", False
        ).items():
            armed_all[k2] = armed_all.get(k2, np.zeros(HOURS, bool)) | v
        p_masks_all = (
            unit_window_masks(part, year, "outage_start", "outage_end", False)
            if len(part)
            else {}
        )
        gap_excl = np.zeros(HOURS)
        gap_raw = np.zeros(HOURS)
        n_units = n_qual = 0
        dfu_b = dfu[
            dfu["unit_type"]
            .astype(str)
            .str.lower()
            .str.contains("|".join(BOILER_TOKENS))
        ]
        for (pid, uid), sub in dfu_b.groupby(["plant_id", "unit_id"], observed=True):
            n_units += 1
            s = np.zeros(HOURS)
            hoy = sub["hour_of_year"].to_numpy()
            gross = np.nan_to_num(sub["gross_mw"].to_numpy(), nan=0.0)
            ok = (hoy >= 0) & (hoy < HOURS)
            np.add.at(s, hoy[ok], gross[ok])
            cap_u = float(np.percentile(s[s > 0], 99.5)) if (s > 0).sum() > 100 else 0.0
            if cap_u <= 0:
                continue
            key = (int(pid), str(uid))
            oper = ~std_masks.get(key, np.zeros(HOURS, bool))
            if s[oper].mean() / cap_u < BASELOAD_CF:
                continue
            n_qual += 1
            st = _plateau_state(s / cap_u)
            if st is None:
                continue
            dmax, ref, _sm, partial = st
            day_gap = np.maximum(0.0, ref - dmax) * cap_u  # MW per day
            am = armed_all.get(key, np.zeros(HOURS, bool)) | p_masks_all.get(
                key, np.zeros(HOURS, bool)
            )
            for d in range(365):
                g_d = float(day_gap[d]) if d < len(day_gap) else 0.0
                gap_raw[d * 24 : (d + 1) * 24] += g_d
                if not am[d * 24 : (d + 1) * 24].any() and not partial[d]:
                    gap_excl[d * 24 : (d + 1) * 24] += g_d
        y["w2b_shallow_subceiling_gap"] = {
            "coal_boiler_units": n_units,
            "qualifying_units_cf_ge_0.55": n_qual,
            **{
                k: {
                    "gap_excl_armed_and_plateau_gw_mean": round(
                        float(gap_excl[idx].mean()) / 1e3, 3
                    ),
                    "gap_raw_gw_mean": round(float(gap_raw[idx].mean()) / 1e3, 3),
                }
                for k, idx in {**pops, "OTHER_JJ_DAYTIME": day_other, **bands}.items()
            },
            "note": (
                "Σ over qualifying coal boiler units of max(0, ref - dmax_d) x unit capability "
                "(capability = p99.5 of the unit's own hourly gross; ref = the frozen detector's p90 "
                "of running daily maxima). NOT a mechanism: a diagnostic of how much revealed "
                "sub-ceiling running the deep-plateau form cannot see."
            ),
        }
        report["years"][str(year)] = y
        print(
            f"{year}: W2 shoulder eff {y['w2_removed']['SHOULDER']['removed_effective_gw_mean']} GW nom {y['w2_removed']['SHOULDER']['removed_nominal_gw_mean']} | "
            f"stat {y['w2_removed']['SHOULDER']['statistical_layer_removed_gw_mean']} win {y['w2_removed']['SHOULDER']['window_layers_removed_gw_mean']} | "
            f"W4 {y['w4_lift']['SHOULDER']['share_of_gap']} | W6 {w6['SHOULDER']['n_violation_days']} | W2b {y['w2b_shallow_subceiling_gap']['SHOULDER']} | N2 {y['n2_consumer_vs_own']['PASS']}",
            flush=True,
        )
        del mc, avail_mw, avail, arrays, fleet

    d = report["years"]["2025"]
    report["verdict"] = {
        "W1_rows": report["w1_extract"]["rows"],
        "W2_shoulder_effective_gw": d["w2_removed"]["SHOULDER"][
            "removed_effective_gw_mean"
        ],
        "W2_in_bracket": d["w2_removed"]["SHOULDER"]["in_bracket"],
        "W2_central_share": d["w2_removed"]["SHOULDER"]["central_share"],
        "W3_overlap_share": d["w3_overlap"].get("overlap_share"),
        "W3_statistical_gw": d["w2_removed"]["SHOULDER"][
            "statistical_layer_removed_gw_mean"
        ],
        "W4_share_shoulder": d["w4_lift"]["SHOULDER"]["share_of_gap"],
        "W4_share_tail": d["w4_lift"]["TAIL"]["share_of_gap"],
        "W5_2023_2024_shoulder_gw": [
            report["years"]["2023"]["w2_removed"]["SHOULDER"][
                "removed_effective_gw_mean"
            ],
            report["years"]["2024"]["w2_removed"]["SHOULDER"][
                "removed_effective_gw_mean"
            ],
        ],
        "W6_violation_days_shoulder": d["w6_feasibility"]["SHOULDER"][
            "n_violation_days"
        ],
        "R208_excess_capability_net_adjusted_gw": d["r208_coal_excess_rescored"][
            "SHOULDER"
        ]["excess_capability_over_net_adjusted_gw"],
        "W2b_shallow_gap_gw": d["w2b_shallow_subceiling_gap"]["SHOULDER"][
            "gap_excl_armed_and_plateau_gw_mean"
        ],
        "CHARTER": bool(
            d["w2_removed"]["SHOULDER"]["in_bracket"]
            and d["w4_lift"]["SHOULDER"]["reaches_25pct"]
            and d["w6_feasibility"]["SHOULDER"]["n_violation_days"] == 0
        ),
    }
    OUT.write_text(json.dumps(report, indent=1, default=float))
    print(f"wrote {OUT.relative_to(REPO)}")
    print(json.dumps(report["verdict"], indent=1))


if __name__ == "__main__":
    main()
