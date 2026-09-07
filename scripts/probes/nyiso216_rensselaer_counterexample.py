"""nyiso-216 phase 0 — is 54034 Rensselaer Cogen's sign flip a ZONE, a COST, or
a fleet-representation effect, and does it belong in the ``cc_reserve_duty_split``
cohort?

Measures the five bars pre-registered in
``results/calibration/PREREG-nyiso216-rensselaer-counterexample.md`` (committed
and pushed before any number below was read):

* **P1** reproduction — per-plant ``mc_peak`` hour-mean and implied economic
  on-share for all seven cohort plants in all three years, against nyiso-215's
  committed ``_nyiso215_reserve_duty_census.json``. Carries a declared VOID, and
  is what discharges the one LIVE G-DRIFT hunk by execution.
* **P2** the swap decomposition — ``S(cost, zone)`` on the 2x2 of
  {54034, the capacity-weighted six} x {Capital_Hudson, Upstate_West}, over the
  keeper's own committed P1 LMP. The price leg and the cost leg sum to the
  observed gap identically, so the partition has no residual.
* **P3** the cost driver — the ``mc = HR * F + VOM + ER * C`` identity split into
  a heat-rate term, a fuel term, an OTHER term and the cross-plant covariance the
  capacity weighting introduces. The PREREG declared a VOID if these four do not
  close to $0.01/MWh; ``assemble_mc``'s nox term and the post-assembly offer
  adjusters are NOT in the declared four, so the residual is measured and
  reported rather than absorbed.
* **P4** membership on the rule — 54034's CAMPD plant-summed online share on
  ``derive_reserve_duty_cc``'s OWN construction, per year as well as pooled.
  ``derive_reserve_duty_cc.py`` is AUDITED, never re-derived (rule 23
  ``[R-FROZEN-DERIVE]``): this probe writes no derive artifact.
* **P5** behavioural coherence — intensity-when-on and mean run length over
  CAMPD 2023-2025 for the six cohort plants that have a CEMS record (7784
  Allegany has none and is excluded, stated not silent).

Three POST-HOC DIAGNOSTICS are computed alongside and are labelled as such
throughout -- they are NOT pre-registered gates, they moved no gate, and none of
them is used to restate one:

* **D2** the protection identity — the out-of-merit distance the class peak
  multiplier buys, ``(2.25 - 1) * HR_base * F``, per plant, and the numerical
  check that its 54034/cohort ratio equals the fuel-price ratio times the
  base-heat-rate ratio.
* **D3** per-year membership on the rule for EVERY CEMS cohort member, beyond
  P4's declared 54034-only scope.
* **D4** the ``gas_cc`` fuel-price census by zone, which identifies the object
  P3 lands on.

ZERO LP: every fleet rebuild is ``fleet_only=True`` and every price is read from
the keeper's committed sidecars (rule 29(b) form 4 -- no control solve).

Usage::

    uv run python scripts/probes/nyiso216_rensselaer_counterexample.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.lib.bundle_fleet import (  # noqa: E402
    bundle_gas_price,
    clear_fleet_caches,
    ensure_probe_path,
    full_run_year_kwargs,
)

BUNDLE = ROOT / "results/calibration/nyiso213_summer_seam"
PRIOR = ROOT / "results/calibration/_nyiso215_reserve_duty_census.json"
OUT = ROOT / "results/calibration/_nyiso216_rensselaer_counterexample.json"
YEARS = (2023, 2024, 2025)

CLASS = "CC_REGULAR"
A = 54034  # Rensselaer Cogen, Capital_Hudson -- the counter-example
SIX = (7784, 10620, 10621, 50744, 54592, 54593)  # the rest of the cohort
SEVEN = frozenset({A, *SIX})
ZONE_A = "Capital_Hudson"
ZONE_B = "Upstate_West"

# The class curve's peak multiplier, in heat-rate space (nyiso-194/-195 closed it
# in both directions; phys_peak == peak). Used ONLY to report the implied BASE
# heat rate alongside the tranche heat rate -- never to move anything.
PEAK_MULT = 2.25


def _build(year: int, meta: dict, **over: object) -> dict:
    """Rebuild the keeper's fleet for ``year`` (no LP), with optional overrides."""
    import scripts.run_calibration as rc

    kwargs = full_run_year_kwargs(meta)
    kwargs.update(over)
    clear_fleet_caches()
    return rc.run_year(year, "NYISO", 8760, bundle_gas_price(meta, year), **kwargs)


def _peak_rows(built: dict) -> pd.DataFrame:
    """One row per cohort plant's ``_peak`` tranche, with its cost components."""
    fa = built["fleet_arrays"]
    gens = built["fleet"]
    if len(gens) != len(fa.unit_ids):
        raise SystemExit("fleet / fleet_arrays misalignment -- instrument invalid")
    mc = np.asarray(built["mc_base"], dtype=float)
    fp = np.asarray(built["fuel_prices"], dtype=float)
    n = len(fa.unit_ids)
    frame = pd.DataFrame(
        {
            "uid": list(fa.unit_ids),
            "plant": np.asarray(fa.plant_code, dtype=int),
            "group": list(fa.plant_group),
            "zone": [g.zone for g in gens],
            "pmax": np.asarray(fa.pmax, dtype=float),
            "heat_rate": np.asarray(fa.heat_rate, dtype=float),
            "vom": np.asarray(fa.vom, dtype=float),
            "emission_rate": np.asarray(fa.emission_rate, dtype=float),
            "nox_rate": np.asarray(getattr(fa, "nox_rate", np.zeros(n)), dtype=float),
            "row": np.arange(n),
        }
    )
    frame = frame[
        (frame["group"] == CLASS)
        & frame["plant"].isin(SEVEN)
        & frame["uid"].str.endswith("_peak")
    ].reset_index(drop=True)
    frame.attrs["mc"] = mc
    frame.attrs["fp"] = fp
    return frame


def _gas_cc_zone_fuel_census(built: dict) -> dict:
    """D4 (post-hoc) — mean delivered fuel price of every ``gas_cc`` unit, by zone.

    Identifies the object P3's FUEL term lands on: whether 54034's fuel price is
    idiosyncratic to the plant or is simply its zone's.
    """
    fa, gens = built["fleet_arrays"], built["fleet"]
    fp = np.asarray(built["fuel_prices"], dtype=float)
    T = fp.shape[1] if fp.ndim == 2 else 8760
    by_zone: dict[str, list[float]] = {}
    for i, g in enumerate(gens):
        if str(getattr(g, "fuel_type", getattr(g, "fuel", ""))) != "gas_cc":
            continue
        by_zone.setdefault(str(g.zone), []).append(
            float(np.mean(_row_series(fp, i, T)))
        )
    _ = fa
    return {
        z: {
            "n_units": len(v),
            "mean": round(float(np.mean(v)), 4),
            "min": round(float(np.min(v)), 4),
            "max": round(float(np.max(v)), 4),
        }
        for z, v in sorted(by_zone.items())
    }


def _row_series(arr: np.ndarray, row: int, T: int) -> np.ndarray:
    """Return the (T,) series for LP row ``row`` from a scalar/1-D/2-D array."""
    a = np.asarray(arr, dtype=float)
    if a.ndim == 0:
        return np.full(T, float(a))
    if a.ndim == 1:
        # (n_gen,) per-generator, or (T,) hourly broadcast to every generator.
        if a.shape[0] == T and T != a.shape[0] - 1:
            return a.astype(float)
        return np.full(T, float(a[row]))
    return a[row, :T].astype(float)


def _zone_price(year: int) -> dict[str, np.ndarray]:
    """Committed keeper P1 hourly LMP per zone -- the control (rule 29(b) form 4)."""
    df = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return {
        str(z): g.sort_values("hour")["price"].to_numpy(dtype=float)
        for z, g in df.groupby("zone", observed=True)
    }


# --------------------------------------------------------------------------
# CAMPD -- P4 and P5. derive_reserve_duty_cc's OWN construction, audited only.
# --------------------------------------------------------------------------
def _campd_plant_hours() -> dict[int, dict[int, np.ndarray]]:
    """Plant-summed hourly ``grossLoad`` per cohort plant per year, chronological."""
    sys.path.insert(0, str(ROOT / "scripts" / "data"))
    import derive_reserve_duty_cc as drd

    from market_sim.data.campd import states_for_iso

    out: dict[int, dict[int, list[np.ndarray]]] = {}
    for state in states_for_iso("NYISO"):
        for year in YEARS:
            path = drd.UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            df = pd.read_parquet(
                path, columns=["facilityId", "unitId", "date", "hour", "grossLoad"]
            )
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df[df["facilityId"].isin(SEVEN)]
            if df.empty:
                continue
            df = df.sort_values(["facilityId", "unitId", "date", "hour"])
            for (fid, _uid), g in df.groupby(["facilityId", "unitId"], sort=False):
                out.setdefault(int(fid), {}).setdefault(year, []).append(
                    g["grossLoad"].fillna(0.0).to_numpy(dtype=float)
                )
    summed: dict[int, dict[int, np.ndarray]] = {}
    for code, by_year in out.items():
        for year, chunks in by_year.items():
            n = min(c.size for c in chunks)
            summed.setdefault(code, {})[year] = np.sum(
                [c[:n] for c in chunks], axis=0
            )
    return summed


def _mean_run_length(online: np.ndarray) -> float:
    """Mean length in hours of a contiguous online block."""
    if not online.any():
        return 0.0
    edges = np.diff(np.concatenate(([0], online.astype(int), [0])))
    starts = np.flatnonzero(edges == 1)
    ends = np.flatnonzero(edges == -1)
    return float(np.mean(ends - starts))


def _p4_p5(plant_hours: dict[int, dict[int, np.ndarray]]) -> tuple[dict, dict]:
    """Membership on the rule (P4) and behavioural coherence in the meter (P5)."""
    from derive_campd_gas_commitment_params import _HSL_PCTILE, _ONLINE_FRAC

    from market_sim.data.campd import _ONLINE_MW

    stats: dict[int, dict] = {}
    for code, by_year in sorted(plant_hours.items()):
        years = sorted(by_year)
        pooled = np.concatenate([by_year[y] for y in years])
        hsl = float(np.percentile(pooled, _HSL_PCTILE))
        if hsl <= _ONLINE_MW:
            continue
        # The derive's threshold: pooled HSL, so a per-year share varies only in
        # the year's own hours -- the same rule, one year at a time.
        thresh = max(_ONLINE_MW, _ONLINE_FRAC * hsl)
        on_pooled = pooled >= thresh
        per_year = {}
        for y in years:
            s = by_year[y]
            on = s >= thresh
            hsl_y = float(np.percentile(s, _HSL_PCTILE))
            th_y = max(_ONLINE_MW, _ONLINE_FRAC * hsl_y)
            per_year[str(y)] = {
                "online_share_pooled_hsl": round(float(on.mean()), 5),
                "online_share_own_year_hsl": round(float((s >= th_y).mean()), 5),
                "hours": int(s.size),
                "intensity_when_on": (
                    round(float(s[on].mean() / hsl), 5) if on.any() else None
                ),
                "mean_run_length_h": round(_mean_run_length(on), 3),
            }
        stats[code] = {
            "plant_code": code,
            "pooled_hsl_mw": round(hsl, 3),
            "online_threshold_mw": round(thresh, 4),
            "pooled_online_share": round(float(on_pooled.mean()), 5),
            "pooled_intensity_when_on": (
                round(float(pooled[on_pooled].mean() / hsl), 5)
                if on_pooled.any()
                else None
            ),
            "pooled_mean_run_length_h": round(_mean_run_length(on_pooled), 3),
            "by_year": per_year,
        }

    # ---- P4: membership on the rule, at 54034 ----------------------------
    a = stats.get(A)
    if a is None:
        p4 = {"error": "54034 has no CAMPD record -- P4 not computable"}
    else:
        pooled = a["pooled_online_share"]
        yearly = [v["online_share_pooled_hsl"] for v in a["by_year"].values()]
        if pooled >= 0.10:
            verdict = "FAILS"
        elif any(v >= 0.10 for v in yearly):
            verdict = "MARGINAL"
        else:
            verdict = "ROBUST"
        p4 = {
            "pooled_online_share": pooled,
            "per_year_online_share_pooled_hsl": {
                k: v["online_share_pooled_hsl"] for k, v in a["by_year"].items()
            },
            "per_year_online_share_own_year_hsl": {
                k: v["online_share_own_year_hsl"] for k, v in a["by_year"].items()
            },
            "threshold": 0.10,
            "verdict": verdict,
            "prediction": "ROBUST",
            "hurts_limb_MARGINAL_fired": verdict == "MARGINAL",
        }

    # ---- P5: behavioural coherence, 54034 vs the other CEMS members ------
    others = {c: s for c, s in stats.items() if c != A}
    if a is None or not others:
        p5 = {"error": "insufficient CAMPD coverage for P5"}
    else:
        inten = [s["pooled_intensity_when_on"] for s in others.values()]
        runs = [s["pooled_mean_run_length_h"] for s in others.values()]
        i_in = min(inten) <= a["pooled_intensity_when_on"] <= max(inten)
        r_in = min(runs) <= a["pooled_mean_run_length_h"] <= max(runs)
        verdict = {
            (True, True): "COHERENT",
            (False, True): "OUTLIER-INTENSITY",
            (True, False): "OUTLIER-DURATION",
            (False, False): "OUTLIER-BOTH",
        }[(i_in, r_in)]
        p5 = {
            "n_cems_members_compared_against": len(others),
            "excluded_no_cems": sorted(SEVEN - set(stats)),
            "a_intensity_when_on": a["pooled_intensity_when_on"],
            "others_intensity_range": [round(min(inten), 5), round(max(inten), 5)],
            "a_mean_run_length_h": a["pooled_mean_run_length_h"],
            "others_run_length_range": [round(min(runs), 3), round(max(runs), 3)],
            "a_pooled_online_share": a["pooled_online_share"],
            "others_online_share_range": [
                round(min(s["pooled_online_share"] for s in others.values()), 5),
                round(max(s["pooled_online_share"] for s in others.values()), 5),
            ],
            "verdict": verdict,
            "prediction": "COHERENT",
            "hurts_limb_fired": verdict in ("OUTLIER-INTENSITY", "OUTLIER-BOTH"),
        }
    return p4, {"p5": p5, "per_plant": stats}


def main() -> None:
    """Measure P1-P5 and write the machine record."""
    ensure_probe_path()
    meta = json.loads((BUNDLE / "meta.json").read_text())
    prior = json.loads(PRIOR.read_text())["P4_P5_by_year"]

    from market_sim.policy.carbon import resolve_carbon_price

    rec: dict = {
        "session": "nyiso-216",
        "keeper": "2026-09-07-nyiso-213-summer-seam",
        "prereg": "results/calibration/PREREG-nyiso216-rensselaer-counterexample.md",
        "zero_lp": True,
        "control": "rule 29(b) form 4 -- the keeper's committed bundle",
    }

    per_pmax: dict[int, float] = {}
    p1_rows: list[dict] = []
    p2_years: dict[str, dict] = {}
    p3_years: dict[str, dict] = {}

    d4: dict = {}
    for year in YEARS:
        built = _build(year, meta)
        d4[str(year)] = _gas_cc_zone_fuel_census(built)
        pk = _peak_rows(built)
        mc, fp = pk.attrs["mc"], pk.attrs["fp"]
        prices = _zone_price(year)
        pa, pb = prices[ZONE_A], prices[ZONE_B]
        T = min(pa.size, pb.size)
        carbon = float(resolve_carbon_price(built["config"], year))

        per = {}
        for _, r in pk.iterrows():
            code = int(r["plant"])
            row = int(r["row"])
            m = _row_series(mc, row, T)
            f = _row_series(fp, row, T)
            per[code] = {
                "zone": str(r["zone"]),
                "pmax": float(r["pmax"]),
                "heat_rate": float(r["heat_rate"]),
                "implied_base_heat_rate": float(r["heat_rate"]) / PEAK_MULT,
                "vom": float(r["vom"]),
                "emission_rate": float(r["emission_rate"]),
                "nox_rate": float(r["nox_rate"]),
                "mc_mean": float(np.mean(m)),
                "fuel_mean": float(np.mean(f)),
                "mc": m,
                "s_own": float((m <= (pa if str(r["zone"]) == ZONE_A else pb)).mean()),
                "s_ch": float((m <= pa).mean()),
                "s_uw": float((m <= pb).mean()),
            }

        per_pmax.update({c: d["pmax"] for c, d in per.items()})

        # ---- P1 reproduction bar ----------------------------------------
        prev = {int(p["plant_code"]): p for p in prior[str(year)]["plants"]}
        for code, d in sorted(per.items()):
            q = prev[code]
            d_on = abs(d["s_own"] - float(q["implied_on_share"]))
            d_mc = abs(d["mc_mean"] - float(q["mc_peak_mean_usd_mwh"])) / float(
                q["mc_peak_mean_usd_mwh"]
            )
            p1_rows.append(
                {
                    "year": year,
                    "plant_code": code,
                    "zone": d["zone"],
                    "implied_on_share": round(d["s_own"], 5),
                    "nyiso215_implied_on_share": q["implied_on_share"],
                    "abs_diff_on_share": round(d_on, 6),
                    "mc_peak_mean": round(d["mc_mean"], 3),
                    "nyiso215_mc_peak_mean": q["mc_peak_mean_usd_mwh"],
                    "rel_diff_mc_pct": round(d_mc * 100.0, 4),
                    "breach": bool(d_on > 0.005 or d_mc > 0.02),
                }
            )

        # ---- P2 swap decomposition --------------------------------------
        w = np.array([per[c]["pmax"] for c in SIX], dtype=float)
        w = w / w.sum()
        s_b_uw = float(np.average([per[c]["s_uw"] for c in SIX], weights=w))
        s_b_ch = float(np.average([per[c]["s_ch"] for c in SIX], weights=w))
        s_a_ch, s_a_uw = per[A]["s_ch"], per[A]["s_uw"]
        g = s_b_uw - s_a_ch
        price_leg = s_a_uw - s_a_ch
        cost_leg = s_b_uw - s_a_uw
        if g <= 0.0:
            cls, r = "DEGENERATE", None
        else:
            r = cost_leg / g
            cls = "COST" if r >= 0.80 else ("PRICE" if r <= 0.20 else "MIXED")
        p2_years[str(year)] = {
            "S_A_CH": round(s_a_ch, 5),
            "S_A_UW": round(s_a_uw, 5),
            "S_B_CH": round(s_b_ch, 5),
            "S_B_UW": round(s_b_uw, 5),
            "G": round(g, 5),
            "price_leg": round(price_leg, 5),
            "cost_leg": round(cost_leg, 5),
            "legs_sum_minus_G": round(price_leg + cost_leg - g, 12),
            "r_cost_share": round(r, 4) if r is not None else None,
            "class": cls,
            "price_leg_ge_plus_0p10": bool(price_leg >= 0.10),
            "price_leg_le_0": bool(price_leg <= 0.0),
            "lmp_mean_CH": round(float(np.mean(pa[:T])), 3),
            "lmp_mean_UW": round(float(np.mean(pb[:T])), 3),
        }

        # ---- P3 cost-driver identity ------------------------------------
        hr_a, f_a = per[A]["heat_rate"], per[A]["fuel_mean"]
        hr_b = float(np.average([per[c]["heat_rate"] for c in SIX], weights=w))
        f_b = float(np.average([per[c]["fuel_mean"] for c in SIX], weights=w))
        vom_b = float(np.average([per[c]["vom"] for c in SIX], weights=w))
        er_b = float(np.average([per[c]["emission_rate"] for c in SIX], weights=w))
        mc_b = float(np.average([per[c]["mc_mean"] for c in SIX], weights=w))
        delta = per[A]["mc_mean"] - mc_b
        t_hr = (hr_a - hr_b) * (f_a + f_b) / 2.0
        t_fuel = (f_a - f_b) * (hr_a + hr_b) / 2.0
        t_other = (per[A]["vom"] + per[A]["emission_rate"] * carbon) - (
            vom_b + er_b * carbon
        )
        t_cov = (
            float(np.average([per[c]["heat_rate"] * per[c]["fuel_mean"] for c in SIX], weights=w))
            - hr_b * f_b
        )
        resid = delta - (t_hr + t_fuel + t_other + t_cov)
        if delta <= 0.0:
            cls3 = "SIGN-FLIP"
        elif t_hr / delta >= 0.50:
            cls3 = "HEAT-RATE"
        elif t_fuel / delta >= 0.50:
            cls3 = "FUEL"
        elif t_other / delta >= 0.50:
            cls3 = "OTHER"
        elif t_cov / delta >= 0.50:
            cls3 = "COVARIANCE"
        else:
            cls3 = "MIXED"
        p3_years[str(year)] = {
            "carbon_price": round(carbon, 4),
            "mc_A": round(per[A]["mc_mean"], 3),
            "mc_B_capwt": round(mc_b, 3),
            "delta": round(delta, 4),
            "HR_A": round(hr_a, 4),
            "HR_B_capwt": round(hr_b, 4),
            "implied_base_HR_A": round(hr_a / PEAK_MULT, 4),
            "implied_base_HR_B_capwt": round(hr_b / PEAK_MULT, 4),
            "F_A": round(f_a, 4),
            "F_B_capwt": round(f_b, 4),
            "VOM_A": round(per[A]["vom"], 4),
            "VOM_B_capwt": round(vom_b, 4),
            "ER_A": round(per[A]["emission_rate"], 5),
            "ER_B_capwt": round(er_b, 5),
            "NOX_A": round(per[A]["nox_rate"], 5),
            "term_HR": round(t_hr, 4),
            "term_FUEL": round(t_fuel, 4),
            "term_OTHER": round(t_other, 4),
            "term_COV": round(t_cov, 4),
            "residual_declared_four": round(resid, 4),
            "declared_identity_closes": bool(abs(resid) < 0.01),
            "share_HR": round(t_hr / delta, 4) if delta > 0 else None,
            "share_FUEL": round(t_fuel / delta, 4) if delta > 0 else None,
            "share_OTHER": round(t_other / delta, 4) if delta > 0 else None,
            "share_COV": round(t_cov / delta, 4) if delta > 0 else None,
            "class": cls3,
            "fuel_limb_ge_0p25": bool(delta > 0 and t_fuel / delta >= 0.25),
            "per_plant_heat_rate": {
                str(c): round(per[c]["heat_rate"], 4) for c in sorted(SEVEN)
            },
            "per_plant_implied_base_heat_rate": {
                str(c): round(per[c]["heat_rate"] / PEAK_MULT, 4) for c in sorted(SEVEN)
            },
            "per_plant_fuel_mean": {
                str(c): round(per[c]["fuel_mean"], 4) for c in sorted(SEVEN)
            },
        }
        del built, pk, per

    rec["P1"] = {
        "rows": p1_rows,
        "n_breach": sum(1 for r in p1_rows if r["breach"]),
        "max_abs_diff_on_share": max(r["abs_diff_on_share"] for r in p1_rows),
        "max_rel_diff_mc_pct": max(r["rel_diff_mc_pct"] for r in p1_rows),
        "void": any(r["breach"] for r in p1_rows),
    }

    def _verdict(classes: list[str]) -> str:
        counts = {c: classes.count(c) for c in set(classes)}
        top = max(counts.values())
        return next(c for c, n in counts.items() if n == top) if top >= 2 else "NO-MAJORITY"

    c2 = [v["class"] for v in p2_years.values()]
    rec["P2"] = {
        "by_year": p2_years,
        "classes": c2,
        "verdict": _verdict(c2),
        "prediction": "COST in >= 2 of 3",
        "prediction_holds": c2.count("COST") >= 2,
        "hurts_limb_price_leg_le_0_in_ge_2": sum(
            1 for v in p2_years.values() if v["price_leg_le_0"]
        )
        >= 2,
        "hurts_limb_defeat_price_leg_ge_0p10_in_ge_2": sum(
            1 for v in p2_years.values() if v["price_leg_ge_plus_0p10"]
        )
        >= 2,
    }
    c3 = [v["class"] for v in p3_years.values()]
    rec["P3"] = {
        "by_year": p3_years,
        "classes": c3,
        "verdict": _verdict(c3),
        "prediction": "HEAT-RATE in >= 2 of 3",
        "prediction_holds": c3.count("HEAT-RATE") >= 2,
        "declared_identity_closes_all_years": all(
            v["declared_identity_closes"] for v in p3_years.values()
        ),
        "void_on_identity": not all(
            v["declared_identity_closes"] for v in p3_years.values()
        ),
        "hurts_limb_fuel_ge_0p25_any_year": any(
            v["fuel_limb_ge_0p25"] for v in p3_years.values()
        ),
    }

    # ---- D2 (POST-HOC): the protection identity ---------------------------
    wts = np.array([per_pmax[c] for c in SIX], dtype=float)
    wts = wts / wts.sum()
    d2: dict = {}
    for y, v in p3_years.items():
        hb, fm = v["per_plant_implied_base_heat_rate"], v["per_plant_fuel_mean"]
        prot = {c: (PEAK_MULT - 1.0) * hb[str(c)] * fm[str(c)] for c in (*SIX, A)}
        pb = float(np.average([prot[c] for c in SIX], weights=wts))
        f_ratio = v["F_A"] / v["F_B_capwt"]
        hr_ratio = v["implied_base_HR_A"] / v["implied_base_HR_B_capwt"]
        d2[y] = {
            "protection_A": round(prot[A], 3),
            "protection_B_capwt": round(pb, 3),
            "ratio_A_over_B": round(prot[A] / pb, 4),
            "fuel_price_ratio": round(f_ratio, 4),
            "base_heat_rate_ratio": round(hr_ratio, 4),
            "identity_product": round(f_ratio * hr_ratio, 4),
            "identity_abs_err": round(abs(f_ratio * hr_ratio - prot[A] / pb), 6),
            "per_plant_protection": {str(c): round(prot[c], 3) for c in sorted(prot)},
        }
    rec["D2_protection_identity_posthoc"] = d2

    plant_hours = _campd_plant_hours()
    p4, p5blob = _p4_p5(plant_hours)
    rec["P4"] = p4
    rec["P5"] = p5blob["p5"]
    rec["campd_per_plant"] = p5blob["per_plant"]
    # ---- D3 (POST-HOC): per-year membership for EVERY CEMS cohort member ---
    rec["D3_per_year_membership_posthoc"] = {
        str(code): {
            "pooled_online_share": s["pooled_online_share"],
            "per_year": {
                y: v["online_share_pooled_hsl"] for y, v in s["by_year"].items()
            },
            "years_at_or_above_threshold": [
                y
                for y, v in s["by_year"].items()
                if v["online_share_pooled_hsl"] >= 0.10
            ],
        }
        for code, s in sorted(p5blob["per_plant"].items())
    }
    rec["D4_gas_cc_zone_fuel_census_posthoc"] = d4

    OUT.write_text(json.dumps(rec, indent=1, sort_keys=False) + "\n")
    print(json.dumps({k: rec[k] for k in ("P1", "P2", "P3")}, indent=1)[:7000])
    print("P4:", json.dumps(rec["P4"], indent=1))
    print("P5:", json.dumps(rec["P5"], indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
