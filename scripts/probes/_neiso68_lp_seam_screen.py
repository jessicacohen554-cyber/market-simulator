"""neiso-68 — the LANE-A LP-side seam question: would the LP DECLINE the seam
population on its own commitment economics, as neiso-66 §5b argues it should?

`FINDING-neiso66-overcount-rootcause-2026-07-26.md` §5b argues on rule 1
[R-STRUCT] grounds that the seam units (available-but-not-committed capacity the
detector books as outage) belong in the availability envelope as AVAILABLE, with
the LP declining them on its own commitment economics. `FINDING-neiso67-...` §6
settled only that the DETECTOR cannot identify them from admissible inputs; it
explicitly did not settle whether the LP would decline them. That is this
probe's question, on a DIFFERENT instrument: the keeper's own solved clearing
prices, read from the committed hourly sidecars of the fix-in-place replay
bundle (`neiso64_meritguard_a1`) — no LP solve, no re-tune, no keeper change.

Why the neiso-67 null does NOT transfer: neiso-67 scored the seam against the
CEMS-revealed clearing cost RCC (the p90 of running units' SRMC — the best
reference the DETECTOR is allowed). The LP's clearing price is a different
object: the dual of the model's own energy balance, carrying the keeper's offer
multipliers, VOM, RGGI carbon cost, fast-start markup and scarcity adders of
whatever unit the MODEL has on the margin. The seam being in merit against RCC
(neiso-67 §4: 89-93 % of seam days repay the start) says nothing about whether
it clears against the model's price surface.

The structural fact that frames the reading (measured from the keeper's own
config, `run_config.json`): the NEISO keeper's ONLY commitment device on the CC
main blocks is the offer-multiplier level. `tranche_startup_amortization`
scopes to fast-start tranches (CT econ/peak + the CC duct-burner PEAK band
only — see the ScenarioConfig docstring: "a big CC's econ blocks are
deliberately excluded"), and every commitment bridge is off. So for the class
that carries the seam (CC, 12.7-14.4 GW), "the LP's own commitment economics"
means: dispatch in exactly the hours where price >= offer, with no start cost,
no min-run and no min-down. The LP-decline prediction for a day is therefore
"NO hour of the day clears" — the strictest available form.

FALSIFIERS, stated before measurement (both directions live):

* The §5b operational claim ("restored to the envelope, the LP declines them")
  is FALSIFIED if the seam unit-days are predominantly IN merit against the
  keeper's own clearing prices at the keeper's own offer multipliers — then
  restoring the envelope makes the LP dispatch capacity the real system held
  idle (or depress its calibrated price level until it stops), i.e. the LP
  does NOT reproduce the uncommitted population without a new commitment
  mechanism (which rule 19 [R-ONE-MECH] says must replace/reconcile with the
  existing owners, never stack).
* The opposite claim ("the LP cannot own this population") is FALSIFIED if the
  seam days are predominantly OUT of merit at LP prices AND the LP-price
  decline split meets the D1 identification standard against ISO-NE's
  published columns (predicted-uncommitted tracks UNCOMMITTED, sign-stable,
  above placebo) — then the detector's deletion is doing work the LP would do
  by itself and the envelope can be restored.

Measured-bias directions, all stated up front:

* On seam days the keeper solved WITHOUT the seam capacity (it is deleted from
  the envelope), so its price there is weakly HIGHER than a restored
  counterfactual would be. In-merit shares at keeper prices are an UPPER bound
  on post-restoration in-merit — conservative for a "LP declines" reading.
* The probe's SRMC (charter D1: measured CAMPD heat rate x delivered fuel
  price) omits VOM and RGGI carbon cost, understating the unit's true offer by
  a few $/MWh — same direction: biases TOWARD in-merit, conservative for a
  "LP declines" reading. The keeper's own offer multipliers (read from
  `run_config.json`, never hardcoded) are the sensitivity that bounds this.
* Day-grain, perfect-foresight best block, energy-only margin: carried over
  from neiso-67 unchanged, same direction notes.

Rule-13 note: the LP price is a MODEL output, not a measured actual — nothing
here feeds it back into any input. The probe is a diagnostic measurement of
what the solved keeper would do with restored capacity, scored against a
published instrument; it changes no extract, no default, no keeper.

Usage::

    PYTHONPATH=. python scripts/probes/_neiso68_lp_seam_screen.py
    PYTHONPATH=. python scripts/probes/_neiso68_lp_seam_screen.py \
        --bundle results/calibration/neiso64_meritguard_a1 --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _neiso67_startcost_recovery import (  # noqa: E402
    MIN_PRICED_SHARE,
    auc,
    best_block_margin,
    booked_out_days,
    build_extended_panel,
)
from market_sim.config.constants import DA_COMMITMENT_HORIZON_HOURS  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.zone_assignment import build_zone_lookup  # noqa: E402
from scripts.lib.outage_detect import MERIT_RCC_PCTL  # noqa: E402

DEFAULT_BUNDLE = REPO / "results" / "calibration" / "neiso64_meritguard_a1"
NEISO_PUBLISHED = REPO / "data" / "raw" / "neiso-operable-capacity"

# Offer-group routing for the multiplier sensitivity: the unit's PHYSICAL
# commitment class (from its CAMPD-reported unitType, via the neiso-67 panel)
# -> the keeper's offer group whose econ_high/committed multipliers bound its
# offer level. Routing only — every multiplier VALUE comes from the bundle's
# own run_config.json (rule 5 [R-NO-MAGIC]).
_CLASS_TO_OFFER_GROUP = {"CC": "CC_REGULAR", "CT": "CT_PEAKER", "ST": "ST_GAS"}


def scored_pass_label(bundle: Path) -> str:
    """The bundle's scored solve pass — the LAST entry of ``meta.json`` passes.

    Bundle files use the legacy pass naming ("P1" = pre-commitment base-cost,
    "P2" = the committed bid-cost result when present); the scorer reads
    ``meta["passes"][-1]`` (run_calibration_full), so this probe prices
    against exactly the pass the keeper is scored on.
    """
    meta = json.loads((bundle / "meta.json").read_text())
    return str(meta["passes"][-1])


def offer_multipliers(bundle: Path) -> dict[str, tuple[float, float]]:
    """Per offer group ``(econ_high, committed)`` from the bundle's run_config."""
    rc = json.loads((bundle / "run_config.json").read_text())
    curves = rc["scenario_config"]["offer_curve_by_group"]
    out: dict[str, tuple[float, float]] = {}
    for grp in set(_CLASS_TO_OFFER_GROUP.values()):
        c = curves.get(grp, {})
        out[grp] = (float(c.get("econ_high", 1.0)), float(c.get("committed", 1.0)))
    return out


def load_lp_prices(
    bundle: Path, year: int, pass_label: str, n_hours_panel: int
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Return ``(zone -> price on the panel clock, demand-weighted price)``.

    The model clock is a strict 8760-hour local year with a leap year's
    Feb 29 dropped (eia930.frames); the CEMS panel clock keeps Feb 29
    (8784 h in 2024). Model prices are expanded onto the panel clock with
    NaN over Feb 29, so that day drops out of every day-grain metric via the
    existing MIN_PRICED_SHARE filter rather than mis-aligning the tail of the
    year by 24 hours.
    """
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == pass_label]

    def _expand(v: np.ndarray) -> np.ndarray:
        if n_hours_panel == v.shape[0]:
            return v.astype(float)
        # Feb 29 = local day index 59 (31 Jan days + 28 Feb days).
        out = np.full(n_hours_panel, np.nan)
        a = 59 * 24
        out[:a] = v[:a]
        out[a + 24 :] = v[a:]
        return out

    prices: dict[str, np.ndarray] = {}
    demand: dict[str, np.ndarray] = {}
    for zone, g in s.groupby("zone"):
        g = g.sort_values("hour")
        prices[zone] = _expand(g["price"].to_numpy(dtype=float))
        demand[zone] = _expand(g["demand"].to_numpy(dtype=float))
    w_sum = np.zeros(n_hours_panel)
    pw_sum = np.zeros(n_hours_panel)
    for zone in prices:
        w = np.nan_to_num(demand[zone])
        pw_sum += np.nan_to_num(prices[zone]) * w
        w_sum += w
    system = np.where(w_sum > 0, pw_sum / np.maximum(w_sum, 1e-9), np.nan)
    return prices, system


def lp_unit_day_table(
    panel,
    prices: dict[str, np.ndarray],
    system_price: np.ndarray,
    zone_of: dict[int, str],
    mults: dict[str, tuple[float, float]],
    horizon_floor: int,
) -> pd.DataFrame:
    """One row per identified unit-day, scored against the LP's own prices.

    ``inm_share_*`` is the share of the DAY's priced hours with
    ``price > SRMC x mult`` — the LP dispatches per hour with no start state,
    so a day with ``inm_share == 0`` is the LP's decline prediction in its
    strictest form. ``R_lp`` is the neiso-67 recovery ratio rebuilt on the LP
    price (best feasible block of >= min_run_hours inside the DA horizon,
    divided by the published start cost) for continuity with the §4 table.
    """
    T = panel.srmc.shape[1]
    n_days = T // 24
    rows = []
    for j, u in enumerate(panel.units):
        zp = prices.get(zone_of.get(u.facility_id, ""), system_price)
        spread_lp = zp - panel.srmc[j]
        run = panel.running[j]
        m_econ, m_comm = mults[_CLASS_TO_OFFER_GROUP.get(u.commit_class, "CC_REGULAR")]
        horizon = max(int(horizon_floor), int(u.min_run_hours))
        for d in range(n_days):
            a = d * 24
            day = slice(a, min(a + 24, T))
            px_d = zp[day]
            sr_d = panel.srmc[j][day]
            fin_d = np.isfinite(px_d) & np.isfinite(sr_d)
            if fin_d.mean() < MIN_PRICED_SHARE:
                continue
            b = min(a + horizon, T)
            if b - a < u.min_run_hours:
                continue
            sp_h = spread_lp[a:b]
            fin_h = np.isfinite(sp_h)
            margin = (
                best_block_margin(np.where(fin_h, sp_h, 0.0), int(u.min_run_hours))
                if fin_h.mean() >= MIN_PRICED_SHARE
                else float("nan")
            )
            rcc_d = panel.rcc[day]
            rows.append(
                {
                    "facility_id": u.facility_id,
                    "unit_id": u.unit_id,
                    "commit_class": u.commit_class,
                    "capacity_mw": u.capacity_mw,
                    "day": d,
                    "inm_share_bare": float((px_d[fin_d] > sr_d[fin_d]).mean()),
                    "inm_share_econ": float(
                        (px_d[fin_d] > sr_d[fin_d] * m_econ).mean()
                    ),
                    "inm_share_comm": float(
                        (px_d[fin_d] > sr_d[fin_d] * m_comm).mean()
                    ),
                    "day_spread_lp": float(np.mean(px_d[fin_d] - sr_d[fin_d])),
                    "R_lp": margin / u.start_cost_per_mw,
                    "price_mean": float(np.mean(px_d[fin_d])),
                    "rcc_mean": (
                        float(np.nanmean(rcc_d)) if np.isfinite(rcc_d).any() else np.nan
                    ),
                    "ran": bool(run[day].any()),
                    "off_at_dawn": bool(a == 0 or not run[a - 1]),
                }
            )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.Timestamp(f"{panel.year}-01-01") + pd.to_timedelta(
            df["day"], "D"
        )
    return df


def report_alignment(df: pd.DataFrame, year: int) -> None:
    """A. Is the LP's price surface the same object as the detector's RCC?"""
    seam = df[df["booked_kept"] & ~df["ran"]]
    print(f"\n  {year}  A. REFERENCE-PRICE ALIGNMENT (LP clearing price vs RCC)")
    print(
        f"      all evaluable unit-days: median LP price {df['price_mean'].median():6.2f}"
        f"  median RCC {df['rcc_mean'].median():6.2f} $/MWh"
        f"   |  seam days only: LP {seam['price_mean'].median():6.2f}"
        f"  RCC {seam['rcc_mean'].median():6.2f}"
        f"  (gap {seam['price_mean'].median() - seam['rcc_mean'].median():+.2f})"
    )


def report_seam(df: pd.DataFrame, year: int) -> None:
    """B. The neiso-67 §4 rematch on the LP instrument: seam days vs the same
    units' running days, at each offer level."""
    out = df[df["booked_kept"] & ~df["ran"]]
    ran = df[~df["booked_any"] & df["ran"]]
    units_out = set(zip(out["facility_id"], out["unit_id"]))
    ran = ran[[k in units_out for k in zip(ran["facility_id"], ran["unit_id"])]]
    print(
        f"\n  {year}  B. SEAM POPULATION vs LP PRICES"
        f" (kept booked-out days vs the same units' running days)"
    )
    if out.empty or ran.empty:
        print("      insufficient population")
        return
    for tag, col in (
        ("bare SRMC (mult 1.00)", "inm_share_bare"),
        ("econ_high offer", "inm_share_econ"),
        ("committed offer", "inm_share_comm"),
    ):
        print(
            f"      {tag:24s} seam days: median in-merit share {out[col].median():5.1%}"
            f"  zero-clear share {float((out[col] == 0).mean()):5.1%}"
            f"   |  running days: {ran[col].median():5.1%} / {float((ran[col] == 0).mean()):5.1%}"
        )
    both = pd.concat([out, ran])
    lab = both["ran"].to_numpy()
    print(
        f"      seam unit-days {len(out):6,}  running {len(ran):6,}"
        f"   |  median R_lp  seam {out['R_lp'].median():6.2f}  running {ran['R_lp'].median():6.2f}"
        f"   share R_lp>=1  seam {float((out['R_lp'] >= 1).mean()):5.1%}"
        f"  running {float((ran['R_lp'] >= 1).mean()):5.1%}"
    )
    print(
        f"      AUC (predicting running):  in-merit share {auc(both['inm_share_bare'].to_numpy(), lab):.3f}"
        f"   R_lp {auc(both['R_lp'].to_numpy(), lab):.3f}"
        "   <- neiso-67 on RCC scored 0.39-0.41 (inverted)"
    )


def report_identification(
    df: pd.DataFrame, year: int, rng: np.random.Generator, draws: int
) -> None:
    """C. The D1-standard identification test with the LP price as reference.

    Idle capacity is split by the LP's own decline prediction (zero in-merit
    hours at the keeper's committed offer level) and each half is scored
    against ISO-NE's two published columns, with the same placebo and
    no-split references the charter's D1 control used.
    """
    pub_path = NEISO_PUBLISHED / f"neiso_operable_capacity_{year}.csv"
    if not pub_path.exists():
        print(f"\n  {year}  C. published control — {pub_path.name} absent, skipped")
        return
    pub = pd.read_csv(pub_path, parse_dates=["report_date"]).set_index("report_date")
    cols = ["gen_outages_reductions_mw", "uncommitted_available_gen_nonfast_mw"]
    idle = df[~df["ran"]].copy()
    print(
        f"\n  {year}  C. LP-DECLINE IDENTIFICATION (idle capacity split by"
        " 'no hour clears at the committed offer')"
    )
    for tag, col in (
        ("bare SRMC", "inm_share_bare"),
        ("committed offer", "inm_share_comm"),
    ):
        idle["declines"] = idle[col] == 0
        g = (
            idle.groupby(["date", "declines"])["capacity_mw"].sum().unstack(
                fill_value=0.0
            )
        )
        pred_unc = g.get(True, pd.Series(0.0, index=g.index))
        pred_mech = g.get(False, pd.Series(0.0, index=g.index))
        j = (
            pd.DataFrame({"unc": pred_unc, "mech": pred_mech})
            .join(pub[cols], how="inner")
            .dropna()
        )
        if j.empty:
            print(f"      {tag}: no overlapping dates")
            continue
        m = j.groupby(j.index.month).mean()
        print(
            f"      [{tag}] LP declines (pred UNCOMMITTED) {j['unc'].mean():6,.0f} MW"
            f"   r vs UNCOMMITTED {m['unc'].corr(m['uncommitted_available_gen_nonfast_mw']):+.2f}"
            f"   r vs OUTAGES {m['unc'].corr(m['gen_outages_reductions_mw']):+.2f}"
        )
        print(
            f"      [{tag}] LP would run (pred MECHANICAL)  {j['mech'].mean():6,.0f} MW"
            f"   r vs UNCOMMITTED {m['mech'].corr(m['uncommitted_available_gen_nonfast_mw']):+.2f}"
            f"   r vs OUTAGES {m['mech'].corr(m['gen_outages_reductions_mw']):+.2f}"
        )
    # References, on the committed-offer split (the keeper's actual offer level).
    idle["declines"] = idle["inm_share_comm"] == 0
    tot = idle.groupby("date")["capacity_mw"].sum()
    jt = pd.DataFrame({"t": tot}).join(pub[cols], how="inner").dropna()
    if not jt.empty:
        mt = jt.groupby(jt.index.month).mean()
        print(
            f"      NO SPLIT total idle capacity        {jt['t'].mean():6,.0f} MW"
            f"   r vs UNCOMMITTED {mt['t'].corr(mt['uncommitted_available_gen_nonfast_mw']):+.2f}"
            f"   r vs OUTAGES {mt['t'].corr(mt['gen_outages_reductions_mw']):+.2f}"
        )
    share = idle.groupby("date")["declines"].mean()
    best = []
    for _ in range(draws):
        idle["_p"] = rng.random(len(idle)) < idle["date"].map(share).to_numpy()
        gp = idle.groupby(["date", "_p"])["capacity_mw"].sum().unstack(fill_value=0.0)
        pu = gp.get(True, pd.Series(0.0, index=gp.index))
        jp = (
            pd.DataFrame({"p": pu})
            .join(pub[["uncommitted_available_gen_nonfast_mw"]], how="inner")
            .dropna()
        )
        if jp.empty:
            continue
        mp = jp.groupby(jp.index.month).mean()
        best.append(mp["p"].corr(mp["uncommitted_available_gen_nonfast_mw"]))
    if best:
        print(
            f"      placebo p95 (same daily idle MW & declining share, {len(best)} draws)"
            f"   vs published UNCOMMITTED {np.nanpercentile(best, 95):+.2f}"
        )


def report_counterfactual(df: pd.DataFrame, year: int) -> None:
    """D. First-order bound on what envelope restoration would dispatch.

    Fixed-price screen: seam capacity x its in-merit hour share = the energy
    the LP would clear from the restored windows at the keeper's own prices.
    Restoration adds supply, which can only LOWER prices, which can only
    SHRINK this — so it is an upper bound on the restored dispatch, and the
    dichotomy is exact: either the restored capacity dispatches (contradicting
    the observed idleness) or it pushes the calibrated price level down until
    it stops (contradicting the keeper's price fit). A large bound means the
    LP fails to reproduce idle-at-current-prices either way.
    """
    seam = df[df["booked_kept"] & ~df["ran"]]
    if seam.empty:
        return
    print(f"\n  {year}  D. RESTORATION BOUND (fixed keeper prices)")
    for tag, col in (
        ("bare SRMC", "inm_share_bare"),
        ("econ_high offer", "inm_share_econ"),
        ("committed offer", "inm_share_comm"),
    ):
        gwh = float((seam["capacity_mw"] * seam[col] * 24).sum()) / 1e3
        w = float(
            (seam["capacity_mw"] * seam[col]).sum() / seam["capacity_mw"].sum()
        )
        print(
            f"      {tag:18s} cap-weighted in-merit share {w:5.1%}"
            f"   -> upper-bound restored dispatch {gwh:8,.1f} GWh over the seam days"
        )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--rcc-pctl", type=float, default=MERIT_RCC_PCTL)
    ap.add_argument("--horizon", type=int, default=DA_COMMITMENT_HORIZON_HOURS)
    ap.add_argument("--placebo-draws", type=int, default=30)
    ap.add_argument("--seed", type=int, default=20260726)
    ap.add_argument("--dump", type=Path, default=None)
    args = ap.parse_args()

    iso = "NEISO"
    rng = np.random.default_rng(args.seed)
    states = campd.states_for_iso(iso)
    pass_label = scored_pass_label(args.bundle)
    mults = offer_multipliers(args.bundle)
    zone_of = build_zone_lookup(iso)
    print(f"===== {iso} — LP-side seam screen (bundle {args.bundle.name}) =====")
    print(
        f"  scored pass '{pass_label}' | offer multipliers (econ_high, committed): "
        + ", ".join(f"{g} {v}" for g, v in sorted(mults.items()))
    )
    dumps = []
    for year in sorted(args.years):
        n_hours = 8784 if pd.Timestamp(f"{year}-12-31").dayofyear == 366 else 8760
        panel = build_extended_panel(iso, year, n_hours, states, args.rcc_pctl)
        if panel is None:
            print(f"\n  {year}: unidentifiable (no priceable CEMS unit) — skipped")
            continue
        prices, system_price = load_lp_prices(
            args.bundle, year, pass_label, n_hours
        )
        df = lp_unit_day_table(
            panel, prices, system_price, zone_of, mults, args.horizon
        )
        if df.empty:
            print(f"\n  {year}: no evaluable unit-days — skipped")
            continue
        every, kept = booked_out_days(iso, year, panel)
        key = list(zip(df["facility_id"], df["unit_id"], df["day"]))
        df["booked_any"] = [k in every for k in key]
        df["booked_kept"] = [k in kept for k in key]
        n_zoned = sum(1 for u in panel.units if u.facility_id in zone_of)
        print(
            f"\n  {year}: {len(panel.units)} identified units, {n_zoned} zone-mapped"
            f" | {len(df):,} evaluable unit-days"
        )
        report_alignment(df, year)
        report_seam(df, year)
        report_identification(df, year, rng, args.placebo_draws)
        report_counterfactual(df, year)
        if args.dump is not None:
            dumps.append(df.assign(iso=iso, year=year))
    if args.dump is not None and dumps:
        args.dump.parent.mkdir(parents=True, exist_ok=True)
        pd.concat(dumps, ignore_index=True).to_parquet(args.dump, index=False)
        print(f"\n  unit-day table -> {args.dump}")


if __name__ == "__main__":
    main()
