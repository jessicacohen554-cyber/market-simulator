"""Derive the CAISO DAYTIME (hod-block x season) south-corridor no-wedge admissibility gate.

The derive-first precondition for the C3a-2025 daytime lane — the daytime
analogue of the promoted caiso-93 OVERNIGHT clean-import depth. caiso-93 closed
the overnight (hod 0-5) leg: the measured overnight CAISO-PaloVerde spread
carries NO carbon wedge unconditionally, and an hod-scoped clean depth flips
C1 12/12 + C3a-2024 PASS. The remaining C3a-2025 mass (+13.3 %) lives in the
DAYTIME hours the overnight mechanism does not touch, named by the 2026-07-16
autumn-2025 diagnosis:

  (a) autumn Sep-Dec-2025 over-price (+7.5/+10.6/+7.2/+7.9 monthly resid), and
  (b) the BELLY hod 10-14 over-price, all years (+11.6/+10.2/+8.9).

The diagnosis named two distinct daytime mechanisms: the south-corridor
UNWEDGED-PARITY import regime OUTSIDE the caiso-87 midday trigger window (the
daytime analogue of what caiso-93 fixed overnight), and a distinct midday
BATTERY-CHARGE-MARGINAL sub-regime (the model prices the belly at its in-state
CC floor ~$38 while reality clears at the battery-charge bid ~$15-26). This
script asks the measured record, per daytime regime, which mechanism is in
play — WITHOUT running any LP (the caiso-86b/88/93 derive-first discipline):

    per daytime regime (hod block x season), does the MEASURED CAISO-hub
    spread show NO carbon wedge (clean attribution) in the hours the caiso-87
    trigger does NOT cover — and is the actual price clearing at HUB PARITY
    (an import-at-hub is the margin -> import-lever admissible) or FAR BELOW
    the raw hub (a battery/storage floor -> NOT an import lever, its own
    charter) or at HUB + WEDGE (reality's marginal IS a carbon-paying import
    -> the model's wedge is CORRECT, leave those hours alone, rule 1)?

Regimes (hod blocks; the autumn diagnosis' named daytime bands):
  morning_ramp   hod 6-9
  belly          hod 10-14   (the caiso-87 midday-trigger overlap band; the
                              handoff scopes it to trigger-OFF hours so the
                              new tranche stays distinct from caiso-87)
  afternoon_eve  hod 15-21
Seasons: autumn = Sep-Dec (months 9-12); non_autumn = the rest.

Construction — every leg inherited verbatim from a COMMITTED construction (the
caiso-93 template, sliced to the daytime blocks); nothing is re-fit to this
gate (the caiso-86b "don't tune the method to the gate" prohibition):

  trigger[t]  (caiso-87, ``transmission.inject_caiso_dsw_surplus_clean``):
      PALOVRDE DA hub LMP[t] < HR_CCGT x SoCal_citygate_weekly[t] + $2.5
      (HR_CCGT = 0.37/0.0531 ~= 6.97; measured-hub hours only — the 2023
      Jan-Feb OASIS-gap fill is NaN in the raw parquet and never classifies).
      To stay DISTINCT from the caiso-87 midday mechanism (which already
      covers trigger-ON hours), the no-wedge gate and the depth are scored on
      the trigger-OFF slice of each regime; trigger-ON stats are reported for
      context (the netting principle, at the derivation stage).
  spread[t]   (caiso-82 §1 parity, south delivery basis
      ``CAISO_IMPORT_DELIVERY_BASIS["DSW_CCGT"]`` = x1.03 + $4):
      delivered-basis spread  = actual_CAISO[t] - (PALOVRDE[t] x 1.03 + 4)
      raw-hub spread          = actual_CAISO[t] -  PALOVRDE[t]        (no wheel)
      DA actual is the gated basis (basis-matched to the DA hub series); RT is
      reported alongside. Wedge reference = CARB_UNSPECIFIED_IMPORT_EF x the
      year's CARB allowance (0.428 x 33.03/35.23/28.06 = $14.1/$15.1/$12.0).
  depth[y]    (caiso-88/93 template): p95 of measured WECC_DSW corridor net
      import (EIA-930 CISO DIBAs, model clock) over the regime's trigger-OFF
      hours of year y.

Pre-registered gates (set BEFORE results were seen; the caiso-93 thresholds):

  G1 no-wedge:   per-year regime trigger-OFF median delivered-basis DA spread
                 <= +$4 (top of the caiso-82 §1 measured parity band) — the
                 actual clears at hub parity, not hub + wedge. All 2023-2025.
  G2 depth CV:   per-year trigger-OFF depth CV <= 0.20 (caiso-81/86/87/88/93).
  G3 depth LOYO: mean-of-other-two predicts the held-out year's depth <= 25 %.

Report-only discriminator (no gate) — the caiso-93 §3 axis, sharpened for
daytime where the battery floor is live: the RAW-HUB spread (actual - PALOVRDE)
median. ~0 => actual clears at the raw hub => a no-wheel clean import IS the
margin => import-lever admissible (the caiso-93 overnight situation). Strongly
negative => actual clears BELOW the raw hub => no import (even no-wheel) can be
marginal => a battery-charge / storage floor sets the price => NOT an import
lever, its own charter (do NOT fold in). >= wedge => reality's marginal is a
carbon-paying import => the wedge is correct, leave alone (rule 1).

This is a DIAGNOSTIC report across six regime cells (not one pass/fail gate):
it prints each cell's gate verdicts + the discriminator and a SUMMARY
classifying each regime. NO LP is run; a build/solve needs OWNER authorization
after this evidence (the caiso-93 sequence).

Usage: .venv/bin/python scripts/data/derive_caiso_daytime_wedge.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))
sys.path.insert(0, str(REPO / "src"))

from derive_caiso_import_tranches import (  # noqa: E402
    YEARS,
    corridor_net_import,
    hub_prices,
)
from market_sim.config.constants import STATE_CARBON_PRICE_BY_ISO  # noqa: E402
from market_sim.config.interchange_config import (  # noqa: E402
    CAISO_DSW_SURPLUS_REMOTE_VOM,
    CAISO_IMPORT_DELIVERY_BASIS,
    CARB_UNSPECIFIED_IMPORT_EF,
)
from market_sim.data.fuel import socal_citygate_weekly_hourly  # noqa: E402

ACTUAL_LMP = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_CAISO.parquet"
)

HOURS = 8760
# Same coupling as the committed caiso-87 trigger
# (transmission._CAISO_IMPORT_COUPLE_HR["DSW_CCGT"]).
HR_CCGT = 0.37 / 0.0531  # ~6.97
PARITY_BAND_TOP = 4.0  # $/MWh, caiso-82 §1 measured parity band top (G1)
CV_MAX = 0.20
LOYO_MAX = 0.25

# Daytime regimes (hod block, inclusive) — the 2026-07-16 autumn-diagnosis bands.
REGIMES: dict[str, tuple[int, int]] = {
    "morning_ramp": (6, 9),
    "belly": (10, 14),
    "afternoon_eve": (15, 21),
}
# Autumn = Sep-Dec (the C3a-2025 amplified window); non_autumn = the rest.
AUTUMN_MONTHS = (9, 10, 11, 12)
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTH_OF_HOUR = np.repeat(np.arange(1, 13), [d * 24 for d in _DAYS])  # len 8760


def actual_prices() -> pd.DataFrame:
    """Dense (year, hour) actual CAISO DA/RT price on the model clock."""
    df = pd.read_parquet(ACTUAL_LMP).set_index(["year", "hour"])
    full = pd.MultiIndex.from_product([YEARS, range(HOURS)], names=["year", "hour"])
    return df.reindex(full)


def _stats(x: np.ndarray, mask: np.ndarray) -> tuple[float, float, float, int]:
    """(median, p25, p75, n) of ``x`` over finite ``mask`` hours (nan if empty)."""
    s = x[mask & np.isfinite(x)]
    if s.size == 0:
        return float("nan"), float("nan"), float("nan"), 0
    return (
        float(np.median(s)),
        float(np.percentile(s, 25)),
        float(np.percentile(s, 75)),
        int(s.size),
    )


def main() -> None:  # noqa: C901 — a linear diagnostic report, one block per cell
    """Run the daytime no-wedge diagnostic across regime x season cells."""
    wheel_mult, wheel_add = CAISO_IMPORT_DELIVERY_BASIS["DSW_CCGT"]
    net = corridor_net_import()
    hub = hub_prices()
    act = actual_prices()
    hod = np.arange(HOURS) % 24
    autumn = np.isin(MONTH_OF_HOUR, AUTUMN_MONTHS)

    # Pre-load per-year arrays once.
    pv = {y: hub.loc[y]["PALOVRDE"].to_numpy() for y in YEARS}
    flow = {y: net.loc[y]["WECC_DSW"].to_numpy() for y in YEARS}
    da = {y: act.loc[y]["da"].to_numpy() for y in YEARS}
    rt = {y: act.loc[y]["rt"].to_numpy() for y in YEARS}
    gas = {y: np.asarray(socal_citygate_weekly_hourly(y, HOURS)) for y in YEARS}
    wedge = {
        y: CARB_UNSPECIFIED_IMPORT_EF * STATE_CARBON_PRICE_BY_ISO["CAISO"][y]
        for y in YEARS
    }
    measured = {y: np.isfinite(pv[y]) for y in YEARS}
    trig_on = {
        y: measured[y] & (pv[y] < HR_CCGT * gas[y] + CAISO_DSW_SURPLUS_REMOTE_VOM)
        for y in YEARS
    }
    # Delivered-basis parity spread (G1) and raw-hub spread (discriminator).
    sp_da = {y: da[y] - (pv[y] * (1.0 + wheel_mult) + wheel_add) for y in YEARS}
    sp_rt = {y: rt[y] - (pv[y] * (1.0 + wheel_mult) + wheel_add) for y in YEARS}
    raw_da = {y: da[y] - pv[y] for y in YEARS}  # actual - RAW hub (no wheel)

    print(
        "=== CAISO DAYTIME (hod-block x season) south-corridor no-wedge diagnostic ==="
    )
    print(
        f"trigger : PALOVRDE < {HR_CCGT:.2f} x SoCal_citygate + {CAISO_DSW_SURPLUS_REMOTE_VOM} (caiso-87)"
    )
    print(
        f"parity  : PALOVRDE x {1 + wheel_mult} + {wheel_add}  (DSW_CCGT delivered basis)"
    )
    print("raw-hub : PALOVRDE  (no wheel — the caiso-93 WEIM-transfer basis)")
    print(
        "gates   : G1 OFF-median delivered DA <= +$4 ; G2 depth CV <= 0.20 ; G3 LOYO <= 25%"
    )
    print(
        "scope   : gates on the caiso-87 trigger-OFF slice (distinct from caiso-87 midday)\n"
    )

    summary: list[tuple[str, str, dict]] = []

    for rname, (h0, h1) in REGIMES.items():
        regime = (hod >= h0) & (hod <= h1)
        for sname, smask in (("autumn", autumn), ("non_autumn", ~autumn)):
            cell = regime & smask
            print(f"--- {rname} (hod {h0}-{h1}) x {sname} ---")
            g1_ok = True
            depths_off: dict[int, float] = {}
            off_med_da: dict[int, float] = {}
            rawhub_med: dict[int, float] = {}
            parity_sh: dict[int, float] = {}
            wedge_sh: dict[int, float] = {}
            for y in YEARS:
                meas_cell = cell & measured[y]
                on_cell = meas_cell & trig_on[y]
                off_cell = meas_cell & ~trig_on[y]
                n_meas = int(meas_cell.sum())
                on_share = on_cell.sum() / max(n_meas, 1)

                med_off, p25_off, p75_off, n_off = _stats(sp_da[y], off_cell)
                med_on, _, _, n_on = _stats(sp_da[y], on_cell)
                rmed_off, _, _, _ = _stats(raw_da[y], off_cell)
                rtmed_off, _, _, _ = _stats(sp_rt[y], off_cell)
                off_med_da[y] = med_off
                rawhub_med[y] = rmed_off

                sda_off = sp_da[y][off_cell & np.isfinite(sp_da[y])]
                if sda_off.size:
                    parity_sh[y] = float((sda_off <= PARITY_BAND_TOP).mean())
                    wedge_sh[y] = float((sda_off >= wedge[y] - 2.0).mean())
                else:
                    parity_sh[y] = float("nan")
                    wedge_sh[y] = float("nan")

                fm = off_cell & np.isfinite(flow[y])
                depths_off[y] = (
                    float(np.percentile(flow[y][fm], 95)) if fm.any() else float("nan")
                )
                dsw_off_mean = (
                    float(np.nanmean(flow[y][fm])) if fm.any() else float("nan")
                )

                g1_cell = np.isfinite(med_off) and med_off <= PARITY_BAND_TOP
                g1_ok = g1_ok and g1_cell
                print(
                    f"  {y} (wedge {wedge[y]:+.1f}): n_meas={n_meas:4d} trigON={on_share:5.1%} "
                    f"({n_on}h) | OFF delivered-DA med {med_off:+6.1f} [{p25_off:+.1f},{p75_off:+.1f}] "
                    f"n={n_off} | RT med {rtmed_off:+6.1f}"
                )
                print(
                    f"        OFF raw-hub(da-PV) med {rmed_off:+6.1f} | "
                    f"parity(<=+4) {parity_sh[y]:5.1%} | wedge(>={wedge[y] - 2:.0f}) {wedge_sh[y]:5.1%} | "
                    f"DSW OFF p95 {depths_off[y]:,.0f} / mean {dsw_off_mean:,.0f} MW | "
                    f"G1 {'PASS' if g1_cell else 'FAIL'}"
                )

            vals = np.array([depths_off[y] for y in YEARS], dtype=float)
            cv = (
                float(np.nanstd(vals) / np.nanmean(vals))
                if np.isfinite(vals).all() and np.nanmean(vals)
                else float("nan")
            )
            g2_ok = bool(np.isfinite(cv) and cv <= CV_MAX)
            g3_ok = True
            loyo_worst = 0.0
            for held in YEARS:
                others = [depths_off[y] for y in YEARS if y != held]
                if (
                    not all(np.isfinite(o) for o in others)
                    or not np.isfinite(depths_off[held])
                    or depths_off[held] == 0
                ):
                    g3_ok = False
                    continue
                pred = float(np.mean(others))
                err = abs(pred - depths_off[held]) / depths_off[held]
                loyo_worst = max(loyo_worst, err)
                g3_ok = g3_ok and (err <= LOYO_MAX)
            print(
                f"  DEPTH OFF p95 (MW): {' / '.join(f'{depths_off[y]:,.0f}' for y in YEARS)}"
                f"  | G2 CV {cv:.3f} {'PASS' if g2_ok else 'FAIL'}"
                f"  | G3 LOYO worst {loyo_worst:.1%} {'PASS' if g3_ok else 'FAIL'}"
            )

            # --- classification (report-only, from the frozen numbers) ---
            med_off_all = np.array([off_med_da[y] for y in YEARS], dtype=float)
            rawhub_all = np.array([rawhub_med[y] for y in YEARS], dtype=float)
            wedge_sh_all = np.array([wedge_sh[y] for y in YEARS], dtype=float)
            klass = _classify(
                med_off_all, rawhub_all, wedge_sh_all, g1_ok, g2_ok, g3_ok
            )
            print(f"  => {klass}\n")
            summary.append(
                (
                    f"{rname} x {sname}",
                    klass,
                    {
                        "g1": g1_ok,
                        "g2": g2_ok,
                        "g3": g3_ok,
                        "off_med_da": med_off_all.tolist(),
                        "rawhub_med": rawhub_all.tolist(),
                        "wedge_share": wedge_sh_all.tolist(),
                    },
                )
            )

    print("=== SUMMARY (per regime cell) ===")
    for name, klass, _ in summary:
        print(f"  {name:28s} {klass}")
    print(
        "\nDisposition legend: IMPORT-LEVER = measured parity holds + actual "
        "clears at raw hub + depth year-stable (a caiso-93-style clean-depth "
        "extension is admissible); WEDGE-REAL = actual clears at hub+wedge, "
        "leave alone (rule 1); BATTERY/STORAGE = actual clears far below raw "
        "hub, imports exonerated, separate storage charter (do NOT fold in); "
        "MIXED = signals disagree, needs judgment.\n"
        "NO LP run. A build/solve needs OWNER authorization (the caiso-93 sequence)."
    )
    sys.exit(0)


def _classify(
    off_med_da: np.ndarray,
    rawhub_med: np.ndarray,
    wedge_share: np.ndarray,
    g1_ok: bool,
    g2_ok: bool,
    g3_ok: bool,
) -> str:
    """Classify a regime cell from its frozen spread numbers (report-only).

    IMPORT-LEVER : G1 (no wedge) holds AND actual clears near/above the raw hub
                   (raw-hub median >= -$4, i.e. an import-at-hub can be the
                   margin) AND the depth is year-stable (G2+G3). The caiso-93
                   overnight situation, applied to the daytime block.
    WEDGE-REAL   : a material share of hours clears at hub+wedge (wedge-share
                   >= 25% in a majority of years) — reality's marginal IS a
                   carbon-paying import, the model's wedge is CORRECT there.
    BATTERY/STORAGE : actual clears far below the raw hub (raw-hub median
                   <= -$8 in a majority of years) — no import (even no-wheel)
                   can set that price; a battery-charge / storage floor does.
    MIXED        : none of the above cleanly.
    """
    yrs = off_med_da.size
    below_hub = int(np.sum(rawhub_med <= -8.0))
    near_hub = int(np.sum(rawhub_med >= -4.0))
    wedge_material = int(np.sum(wedge_share >= 0.25))
    if wedge_material > yrs // 2:
        return "WEDGE-REAL (leave alone, rule 1)"
    if below_hub > yrs // 2:
        return "BATTERY/STORAGE (imports exonerated — separate storage charter)"
    if g1_ok and g2_ok and g3_ok and near_hub == yrs:
        return "IMPORT-LEVER admissible (caiso-93-style clean-depth extension)"
    if g1_ok and near_hub >= yrs - 1:
        return (
            "IMPORT-LEVER candidate (G1 holds, depth gates: "
            + f"{'ok' if g2_ok and g3_ok else 'CHECK'})"
        )
    return "MIXED (needs judgment — see cell numbers)"


if __name__ == "__main__":
    main()
