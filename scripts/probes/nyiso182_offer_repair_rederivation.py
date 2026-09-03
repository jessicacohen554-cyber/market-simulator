"""nyiso-182 phase 0 — the REPAIRED ST_GAS offer, and what rested on the broken one.

Discharges every gate of
``results/calibration/PREREG-nyiso182-offer-repair-rederivation.md``, committed
with this file and with the ``build_year`` repair BEFORE any of them ran.
**Zero non-control solves.**

THE OBJECT. nyiso-181 proved on an exact identity that
``nyiso179_st_gas_offer_position.build_year`` reconstructed the ST_GAS offer
OUTSIDE the solve and omitted two armed, keeper-registered terms (the measured
RGGI allowance price and ``apply_gas_offer_margin``), and it deliberately did
NOT edit that probe because doing so would silently rewrite the published
nyiso-179 record. This session repairs it non-silently (explicit
``legacy_defective_offer`` opt-in, ``main()`` pinned to it) and re-derives the
three results that read the defective ``mc``:

* **G-3R** — nyiso-179's G3 ``peak`` exoneration, its own gate run unmodified
  on a repaired state. Both bars inherited verbatim (0.40 / 0.90).
* **G-4R** — the between-year channel decomposition, on a 2x2 basis-x-method
  grid. The repair introduces a channel the published three-channel form could
  not have: RGGI is ``emission_rate x carbon_price`` and BOTH factors move
  between years.
* **G-S** — the 62.4 / 24.6 / 13.0 split of the 2025 top-decile deficit. THE
  LOAD-BEARING ONE: it is the sole basis for "the ST_GAS C1 lane and the
  C3a-2025 lane are ONE OBJECT" and for the standing DO-NOT-OPEN on ST_GAS
  offer levers.

Instrument gates I1 / I2 / I2b / I3 are read FIRST and any failure fires stop
condition S1 (every re-derived verdict WITHHELD). I2 is the gate nyiso-180's
P-c could not be: it compares the RECONSTRUCTION to the LP, not the LP to
itself.

``R = mo / itm`` is RETIRED (nyiso-181 §5) and is neither computed nor repaired
anywhere below, on either basis.

Traps honoured: LP band suffixes are single tokens (a); most LP columns are not
tranches, so the class is selected by ``plant_group`` on the fleet arrays (b);
zones are mapped by NAME (c); ``class_hourly``'s ST_GAS row under-reports the
class by the dual-fuel oil-switched energy, so the gated dispatch anchor comes
from the per-unit ``unit_hourly`` sum (j).

Usage:
    PYTHONPATH=.:src python scripts/probes/nyiso182_offer_repair_rederivation.py \
        <replay-bundle> [--out FILE]
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes import nyiso179_st_gas_offer_position as p179  # noqa: E402
from scripts.probes.nyiso178_offer_side_idling import (  # noqa: E402
    HOURS,
    ISO,
    KLASS,
    YEARS,
    measured_hourly,
    model_hourly,
)

OUT = REPO / "results/calibration/_nyiso182_offer_repair_rederivation.json"
PUBLISHED = REPO / "results/calibration/_nyiso179_st_gas_offer_position.json"

# ---------------------------------------------------------------------------
# Bars — ALL inherited, NONE chosen here (PREREG §0.1). Not movable.
# ---------------------------------------------------------------------------
#: I2 — nyiso181_offer_reconstruction_repair.py's own ``EXACT`` criterion.
I2_TOL_USD = 1e-4
#: I2b — the published rounding precision of the field it reproduces (0.1 MW).
I2B_TOL_MW = 0.05
#: I3 — the published rounding of _nyiso179_st_gas_offer_position.json.
I3_TOL_MW, I3_TOL_SHARE = 0.05, 0.0005
#: G-3R — nyiso179_st_gas_offer_position.G3_OOM_SHARE_BAR / G3_OOM_HOURS_BAR.
G3_SHARE_BAR, G3_HOURS_BAR = p179.G3_OOM_SHARE_BAR, p179.G3_OOM_HOURS_BAR
#: G-4R and G-S1 — nyiso179_st_gas_offer_position.G4_CARRIER_BAR.
CARRIER_BAR = p179.G4_CARRIER_BAR

SPLIT_YEAR = 2025
Y0, Y1 = p179.Y0, p179.Y1
CHANNELS = ("FUEL", "PRICE", "AVAIL", "CARBON")


def _f(x, nd: int = 4):
    if x is None:
        return None
    v = float(x)
    return None if not np.isfinite(v) else round(v, nd)


# ---------------------------------------------------------------------------
# The LP's own per-unit frame (the instrument PR #4650 added).
# ---------------------------------------------------------------------------
def lp_unit_frame(bundle: Path, year: int) -> pd.DataFrame:
    """P1 ST_GAS rows of ``unit_hourly_<year>.parquet``, the LP's own offer."""
    u = pd.read_parquet(bundle / "hourly" / f"unit_hourly_{year}.parquet")
    if "pass" in u.columns:
        u = u[u["pass"].astype(str) == "P1"]
    return u[u["plant_group"].astype(str) == KLASS]


def lp_pivots(bundle: Path, year: int, unit_ids: list[str]) -> dict:
    """(mc, cap_mw, mw) pivoted unit x hour, aligned to ``unit_ids`` by NAME."""
    lp = lp_unit_frame(bundle, year)
    out = {}
    for col in ("mc", "cap_mw", "mw"):
        piv = lp.pivot_table(index="unit_id", columns="hour", values=col, aggfunc="first")
        out[col] = piv
    common = [u for u in unit_ids if u in out["mc"].index]
    sel = np.asarray([unit_ids.index(u) for u in common])
    return {
        "common": common,
        "sel": sel,
        **{k: v.loc[common].reindex(columns=range(HOURS)).to_numpy(dtype=float)
           for k, v in out.items()},
    }


# ---------------------------------------------------------------------------
# I2 / I2b — does the REPAIRED reconstruction equal the LP's installed offer?
# ---------------------------------------------------------------------------
def gate_i2(bundle: Path, states_rep: dict, states_leg: dict) -> dict:
    per_year, ok = {}, True
    for y in YEARS:
        st = states_rep[y]
        lp = lp_pivots(bundle, y, list(st["unit_id"]))
        sel = lp["sel"]
        d_rep = st["mc"][sel] - lp["mc"]
        d_leg = states_leg[y]["mc"][sel] - lp["mc"]
        cap_rec = (st["pmax"][:, None] * st["avail"])[sel]
        row = {
            "units_matched": len(lp["common"]),
            "units_in_reconstruction": len(st["unit_id"]),
            "repaired_max_abs_delta_usd": _f(np.abs(d_rep).max(), 8),
            "repaired_median_delta_usd": _f(np.median(d_rep), 8),
            "legacy_max_abs_delta_usd": _f(np.abs(d_leg).max(), 4),
            "legacy_median_delta_usd": _f(np.median(d_leg), 4),
            "capacity_basis_max_abs_delta_mw": _f(np.abs(cap_rec - lp["cap_mw"]).max(), 8),
            "PASS": bool(np.abs(d_rep).max() <= I2_TOL_USD),
        }
        ok &= row["PASS"]
        per_year[y] = row
    return {"bar_usd": I2_TOL_USD, "per_year": per_year,
            "verdict": "PASS" if ok else "FAIL"}


def gate_i2b(bundle: Path, states_rep: dict) -> dict:
    """The 2025 top-decile ITM@actual anchor by two independent routes."""
    per_year, ok = {}, True
    for y in YEARS:
        st = states_rep[y]
        px = p179.price_rt(y)
        top = p179._decile_idx(px)[-1]
        lp = lp_pivots(bundle, y, list(st["unit_id"]))
        sel = lp["sel"]
        cap_rec = (st["pmax"][:, None] * st["avail"])[sel]
        a_rec = np.where(st["mc"][sel] <= px[None, :], cap_rec, 0.0).sum(axis=0)[top].mean()
        a_lp = np.where(lp["mc"] <= px[None, :], lp["cap_mw"], 0.0).sum(axis=0)[top].mean()
        row = {
            "itm_at_actual_reconstruction_mw": _f(a_rec, 3),
            "itm_at_actual_lp_frame_mw": _f(a_lp, 3),
            "abs_delta_mw": _f(abs(a_rec - a_lp), 6),
            "PASS": bool(abs(a_rec - a_lp) <= I2B_TOL_MW),
        }
        ok &= row["PASS"]
        per_year[y] = row
    return {"bar_mw": I2B_TOL_MW, "per_year": per_year,
            "verdict": "PASS" if ok else "FAIL"}


# ---------------------------------------------------------------------------
# I3 — does the LEGACY path still reproduce the published record EXACTLY?
# ---------------------------------------------------------------------------
def gate_i3(g3_leg: dict, g4_leg: dict) -> dict:
    if not PUBLISHED.exists():
        return {"verdict": "FAIL", "reason": f"missing {PUBLISHED}"}
    pub = json.load(open(PUBLISHED))
    diffs, worst_mw, worst_share = [], 0.0, 0.0

    def _cmp(path: str, a, b, share: bool) -> None:
        nonlocal worst_mw, worst_share
        if a is None or b is None:
            diffs.append({"field": path, "published": b, "recomputed": a,
                          "note": "absent on one side"})
            return
        d = abs(float(a) - float(b))
        if share:
            worst_share = max(worst_share, d)
            bad = d > I3_TOL_SHARE
        else:
            worst_mw = max(worst_mw, d)
            bad = d > I3_TOL_MW
        if bad:
            diffs.append({"field": path, "published": b, "recomputed": a,
                          "abs_delta": _f(d, 6)})

    share_keys = {"peak_share_of_oom", "share_top_decile_hours_oom"}
    for y in YEARS:
        pg = pub["G3"]["per_year"][str(y)]
        rg = g3_leg["per_year"][y]
        for k, v in rg.items():
            if k == "by_band":
                for band, bv in v.items():
                    for bk, bvv in bv.items():
                        _cmp(f"G3.{y}.by_band.{band}.{bk}", bvv,
                             pg.get("by_band", {}).get(band, {}).get(bk),
                             bk in share_keys)
            else:
                _cmp(f"G3.{y}.{k}", v, pg.get(k), k in share_keys)
    p4 = pub["G4"]
    for k in ("itm_actual_mean_mw_2023", "itm_actual_mean_mw_2025",
              "delta_itm_actual_mw"):
        _cmp(f"G4.{k}", g4_leg.get(k), p4.get(k), False)
    for ch, v in g4_leg["channel_contribution_mw"].items():
        _cmp(f"G4.contribution.{ch}", v, p4["channel_contribution_mw"].get(ch), False)
    for ch, v in g4_leg["channel_share_of_abs_delta"].items():
        _cmp(f"G4.share.{ch}", v, p4["channel_share_of_abs_delta"].get(ch), True)
    _cmp("G4.band_heat_rate_max_drift", g4_leg["band_heat_rate_max_drift"],
         p4["band_heat_rate_max_drift"], True)
    return {
        "bars": {"mw": I3_TOL_MW, "share": I3_TOL_SHARE},
        "published_verdicts": {"G3": pub["G3"]["verdict"], "G4": pub["G4"]["verdict"]},
        "recomputed_verdicts": {"G3": g3_leg["verdict"], "G4": g4_leg["verdict"]},
        "max_abs_delta_mw": _f(worst_mw, 6),
        "max_abs_delta_share": _f(worst_share, 6),
        "n_fields_outside_bar": len(diffs),
        "fields_outside_bar": diffs[:40],
        "verdict": "PASS" if not diffs else "FAIL",
    }


# ---------------------------------------------------------------------------
# G-4R — the between-year decomposition on the repaired offer.
# ---------------------------------------------------------------------------
def g4_repaired(states: dict, n_channels: int, orders: str) -> dict:
    """ITM(2023->2025) decomposition carrying the CARBON channel explicitly.

    ``mc(f, c) = hr x fuel[f] + vom + co2_rate[c] x carbon[c]
                 + markup_hr x (anchor - fuel[f])``

    The offer-margin term is a function of ``fuel[g, t]``, so it rides the FUEL
    channel BY CONSTRUCTION — a partition choice, declared in the PREREG in
    advance. ``n_channels=3`` collapses CARBON into the base (the published
    form); ``orders="shapley"`` averages over every permutation, ``"pair"``
    over nyiso-179's own complementary order pair.
    """
    a, b = states[Y0], states[Y1]
    ia = {u: i for i, u in enumerate(a["unit_id"])}
    ib = {u: i for i, u in enumerate(b["unit_id"])}
    common = sorted(set(ia) & set(ib))
    sa = np.asarray([ia[u] for u in common])
    sb = np.asarray([ib[u] for u in common])

    hr = {Y0: a["hr"][sa], Y1: b["hr"][sb]}
    vom = {Y0: a["vom"][sa], Y1: b["vom"][sb]}
    fuel = {Y0: a["fuel"][sa], Y1: b["fuel"][sb]}
    avail = {Y0: a["avail"][sa], Y1: b["avail"][sb]}
    pmax = {Y0: a["pmax"][sa], Y1: b["pmax"][sb]}
    mkup = {Y0: a["markup_hr"][sa], Y1: b["markup_hr"][sb]}
    co2 = {Y0: a["co2_rate"][sa], Y1: b["co2_rate"][sb]}
    cprice = {Y0: a["carbon_price"], Y1: b["carbon_price"]}
    anchor = a["margin_anchor"]
    price = {Y0: p179.price_rt(Y0), Y1: p179.price_rt(Y1)}

    drift = {
        "heat_rate": float(np.abs(hr[Y1] - hr[Y0]).max()),
        "vom": float(np.abs(vom[Y1] - vom[Y0]).max()),
        "markup_hr": float(np.abs(mkup[Y1] - mkup[Y0]).max()),
        "co2_rate": float(np.abs(co2[Y1] - co2[Y0]).max()),
    }

    def itm(f_y: int, a_y: int, p_y: int, c_y: int) -> float:
        mc = hr[Y0][:, None] * fuel[f_y] + vom[Y0][:, None]
        if anchor is not None:
            mc = mc + mkup[Y0][:, None] * (anchor - fuel[f_y])
        if n_channels == 4:
            mc = mc + (co2[c_y] * cprice[c_y])[:, None]
        else:
            # 3-channel form: carbon held at its Y0 value throughout, so the
            # channel cannot appear. On the legacy basis it is 0 either way.
            mc = mc + (co2[Y0] * cprice[Y0])[:, None]
        cap = pmax[a_y][:, None] * avail[a_y]
        return float(np.where(mc <= price[p_y][None, :], cap, 0.0).sum(axis=0).mean())

    chans = list(CHANNELS[:3]) if n_channels == 3 else list(CHANNELS)
    base = itm(Y0, Y0, Y0, Y0)
    full = itm(Y1, Y1, Y1, Y1) if n_channels == 4 else itm(Y1, Y1, Y1, Y0)
    d_total = full - base

    if orders == "shapley":
        perms = list(itertools.permutations(chans))
    else:
        perms = [tuple(chans), tuple(reversed(chans))]
    contrib: dict[str, list[float]] = {c: [] for c in chans}
    for order in perms:
        cur = dict.fromkeys(CHANNELS, Y0)
        prev = itm(cur["FUEL"], cur["AVAIL"], cur["PRICE"], cur["CARBON"])
        for ch in order:
            cur[ch] = Y1
            now = itm(cur["FUEL"], cur["AVAIL"], cur["PRICE"], cur["CARBON"])
            contrib[ch].append(now - prev)
            prev = now
    mws = {c: round(float(np.mean(v)), 1) for c, v in contrib.items()}
    shares = {c: _f(float(np.mean(v)) / max(abs(d_total), 1e-9))
              for c, v in contrib.items()}
    top = max(shares, key=lambda c: abs(shares[c]))
    return {
        "n_channels": n_channels,
        "orderings": orders,
        "n_orderings": len(perms),
        "n_common_bins": len(common),
        "structural_drift_max": {k: round(v, 9) for k, v in drift.items()},
        "carbon_price": {Y0: cprice[Y0], Y1: cprice[Y1]},
        "itm_actual_mean_mw_2023": round(base, 1),
        "itm_actual_mean_mw_2025": round(full, 1),
        "delta_itm_actual_mw": round(d_total, 1),
        "channel_contribution_mw": mws,
        "channel_share_of_abs_delta": shares,
        "carrier": top,
        "verdict": ("CARRIER IDENTIFIED" if abs(shares[top]) >= CARRIER_BAR
                    else "DIFFUSE"),
        "share_denominator_is_small": bool(
            abs(d_total) < 0.5 * max(abs(v) for v in mws.values())
        ),
    }


# ---------------------------------------------------------------------------
# G-S — the 2025 top-decile split (PREREG §2.4). THE LOAD-BEARING GATE.
# ---------------------------------------------------------------------------
def gate_gs(bundle: Path, states: dict, year: int = SPLIT_YEAR) -> dict:
    st = states[year]
    px = p179.price_rt(year)
    top = p179._decile_idx(px)[-1]
    lp = lp_pivots(bundle, year, list(st["unit_id"]))
    sel = lp["sel"]

    zones = [z.name for z in _iso_zones()]
    zprice = p179._model_zone_price(year, zones)
    zone_of = np.asarray(st["zone"])[sel]
    p_model = np.vstack([zprice[str(z)] for z in zone_of])

    mc, cap, mw = lp["mc"], lp["cap_mw"], np.nan_to_num(lp["mw"])
    itm_actual = mc <= px[None, :]
    itm_model = mc <= p_model

    def top_mean(v: np.ndarray) -> float:
        return float(v[top].mean())

    M = top_mean(measured_hourly(year, KLASS))
    A = top_mean(np.where(itm_actual, cap, 0.0).sum(axis=0))
    P = top_mean(np.where(itm_model, cap, 0.0).sum(axis=0))
    D_unit = top_mean(mw.sum(axis=0))
    D_class = top_mean(model_hourly(year, KLASS))

    T3a = top_mean(np.where(itm_model, np.maximum(cap - mw, 0.0), 0.0).sum(axis=0))
    T3b = -top_mean(np.where(~itm_model, mw, 0.0).sum(axis=0))

    def split(D: float) -> dict:
        G = M - D
        T2, T1, T3 = M - A, A - P, P - D
        return {
            "anchors_mw": {"measured_M": _f(M, 1), "itm_at_actual_A": _f(A, 1),
                           "itm_at_model_P": _f(P, 1), "dispatch_D": _f(D, 1)},
            "gap_G_mw": _f(G, 1),
            "terms_mw": {"offer_position_T2": _f(T2, 1),
                         "price_level_T1": _f(T1, 1),
                         "own_signal_T3": _f(T3, 1)},
            "shares_of_gap": {"offer_position_T2": _f(T2 / G),
                              "price_level_T1": _f(T1 / G),
                              "own_signal_T3": _f(T3 / G)},
            "closes": _f(abs((T1 + T2 + T3) - G), 6),
        }

    corrected, like_for_like = split(D_unit), split(D_class)
    T1, T2 = A - P, M - A  # price level, offer position (PREREG §2.4)
    T3 = P - D_unit
    G = M - D_unit
    s1 = (T1 / G) >= CARRIER_BAR
    s2 = abs(T1) > abs(T2) and abs(T1) > abs(T3)
    verdict = ("PREMISE-CONFIRMED" if (s1 and s2)
               else "PREMISE-WEAKENED" if s2 else "PREMISE-OVERTURNED")
    return {
        "year": year,
        "basis": "LP unit_hourly frame (mc, cap_mw, mw) — the LP's own offer",
        "corrected_D_from_unit_hourly_GATED": corrected,
        "like_for_like_D_from_class_hourly_REPORT": like_for_like,
        "trap_j_dispatch_undercount_mw": _f(D_unit - D_class, 2),
        "third_term_matched_population_repair": {
            "T3a_unrun_in_the_money_mw": _f(T3a, 1),
            "T3b_out_of_money_dispatch_mw": _f(T3b, 1),
            "sum_equals_T3": _f(abs((T3a + T3b) - T3), 6),
        },
        "published_defective_basis_REFERENCE": {
            "T2_offer_position": 0.246, "T1_price_level": 0.624,
            "T3_own_signal": 0.130,
            "source": "docs/FINDING-nyiso179-st-gas-offer-position-2026-09-03.md §7",
        },
        "G_S1_dominance": {"bar": CARRIER_BAR, "statistic": _f(T1 / G),
                           "verdict": "PRICE-DOMINANT" if s1 else "NOT-DOMINANT"},
        "G_S2_plurality": {"bar": "threshold-free",
                           "verdict": "PRICE-LARGEST" if s2 else "NOT-LARGEST"},
        "LANE_VERDICT": verdict,
    }


def _iso_zones():
    from market_sim.config.iso_configs import get_iso_config

    return get_iso_config(ISO).zones


# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path, help="the control-replay bundle")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    bundle = args.bundle if args.bundle.is_absolute() else REPO / args.bundle

    cfg = p179._cfg_obj()
    states_rep = {y: p179.build_year(y, cfg) for y in YEARS}
    states_leg = {y: p179.build_year(y, cfg, legacy_defective_offer=True)
                  for y in YEARS}

    rec = {
        "session": "nyiso-182",
        "prereg": "results/calibration/PREREG-nyiso182-offer-repair-rederivation.md",
        "keeper": "2026-09-02-nyiso-177-vintage-matched",
        "control_replay_bundle": str(bundle.relative_to(REPO)),
        "non_control_solves": 0,
        "bars_all_inherited": {
            "I2_usd": I2_TOL_USD, "I2b_mw": I2B_TOL_MW,
            "I3_mw": I3_TOL_MW, "I3_share": I3_TOL_SHARE,
            "G3_share": G3_SHARE_BAR, "G3_hours": G3_HOURS_BAR,
            "carrier": CARRIER_BAR,
        },
        "rggi_allowance_price_usd_per_tco2": {
            y: states_rep[y]["carbon_price"] for y in YEARS
        },
        "gas_offer_margin_anchor": states_rep[YEARS[0]]["margin_anchor"],
    }

    # --- instrument gates first (PREREG §4 S1) ------------------------------
    rec["I2_offer_identity"] = gate_i2(bundle, states_rep, states_leg)
    rec["I2b_anchor_agreement"] = gate_i2b(bundle, states_rep)
    g3_leg = p179.g3_band_attribution(states_leg)
    g4_leg = p179.g4_between_year(states_leg)
    rec["I3_legacy_reproduction"] = gate_i3(g3_leg, g4_leg)

    instrument_ok = all(
        rec[k]["verdict"] == "PASS"
        for k in ("I2_offer_identity", "I2b_anchor_agreement", "I3_legacy_reproduction")
    )
    rec["instrument_gates_pass"] = instrument_ok
    rec["S1_fired"] = not instrument_ok

    if not instrument_ok:
        rec["GATES"] = ("WITHHELD — stop condition S1 fired (PREREG §4). "
                        "No re-derived verdict is adjudicated.")
        _write(rec, args.out)
        return

    # --- the re-derivations -------------------------------------------------
    rec["G3R_peak_attribution"] = {
        "bars": {"oom_share": G3_SHARE_BAR, "oom_hours": G3_HOURS_BAR},
        "legacy_published_basis": g3_leg,
        "repaired_basis": p179.g3_band_attribution(states_rep),
    }
    rec["G4R_between_year"] = {
        "bar": CARRIER_BAR,
        "legacy_published_method": g4_leg,
        "grid": {
            "legacy_offer__published_method_3ch_pair":
                g4_repaired(states_leg, 3, "pair"),
            "legacy_offer__shapley_4ch": g4_repaired(states_leg, 4, "shapley"),
            "repaired_offer__published_method_3ch_pair":
                g4_repaired(states_rep, 3, "pair"),
            "repaired_offer__shapley_4ch_PRIMARY":
                g4_repaired(states_rep, 4, "shapley"),
        },
    }
    rec["GS_2025_split"] = gate_gs(bundle, states_rep)
    _write(rec, args.out)


def _write(rec: dict, out: Path | None) -> None:
    dest = out or OUT
    dest.write_text(json.dumps(rec, indent=2, default=str))
    print(json.dumps(rec, indent=2, default=str)[:12000])
    print(f"\n\nwrote {dest}")


if __name__ == "__main__":
    main()
