"""Derive the CAISO OVERNIGHT (hod 0-5) south-corridor no-wedge admissibility gate.

The derive-first precondition for the CC-overnight lane's import-side redirect
(FINDING-caiso92b-overnight-cc-is-import-pricing-2026-07-17 §6): the model
serves the overnight residual with domestic CC at carbon-wedge parity (~$55)
where reality serves it with imports, because the caiso-87 surplus-clean depth
(``caiso_dsw_surplus_clean``) triggers only when the Palo Verde hub sits below
its remote-CCGT gas floor — a mostly-midday state — leaving overnight
incremental imports priced at hub + the +$12-15 unspecified-import CARB wedge.
Before ANY overnight extension is built, this gate asks the measured record:

    does the MEASURED overnight (hod 0-5) CAISO−hub spread show NO carbon
    wedge (clean attribution) in overnight surplus-West hours, specifically
    for the DSW / Palo Verde SOUTH corridor?

If NO — the overnight DSW is fossil-marginal and the wedge is CORRECT
overnight — the redirect is wrong and the lane is an owner checkpoint. No LP
is run here; a FAIL files a FINDING and does NOT solve (the caiso-86b/88
derive-first discipline).

Construction — every leg inherited from a COMMITTED construction, sliced to
hod 0-5; nothing is re-fit to this gate (the caiso-86b "don't tune the method
to the gate" prohibition):

  trigger[t]  (caiso-87, ``transmission.inject_caiso_dsw_surplus_clean``):
      PALOVRDE DA hub LMP[t] < HR_CCGT x SoCal_citygate_weekly[t] + $2.5
      (HR_CCGT = 0.37/0.0531 ~= 6.97; measured hub hours only — the 2023
      Jan-Feb OASIS-gap fill is NaN in the raw parquet and never classifies)
  spread[t]   (caiso-82 §1 parity, south delivery basis
      ``CAISO_IMPORT_DELIVERY_BASIS["DSW_CCGT"]`` = x1.03 + $4):
      actual_CAISO[t] − (PALOVRDE[t] x 1.03 + 4)
      DA actual is the gated basis (basis-matched to the DA hub series);
      RT is reported alongside. The caiso-82 §1 measured parity band in
      below-floor soft-month hours was −9…+4 $/MWh; the wedge reference is
      CARB_UNSPECIFIED_IMPORT_EF x the year's CARB allowance
      (0.428 x 33.03/35.23/28.06 = $14.1/$15.1/$12.0).
  depth[y]    (caiso-88 template = the caiso-87 depth, overnight slice):
      p95 of measured WECC_DSW corridor net import (EIA-930 CISO DIBAs,
      model clock) over OVERNIGHT trigger-ON hours of year y

Pre-registered gates (set BEFORE results were seen; all three must hold):

  G1 no-wedge:      per-year overnight trigger-ON median DA spread <= +$4
                    (the top of the caiso-82 §1 measured parity band) — i.e.
                    the overnight surplus-hour actual clears at hub parity,
                    not at hub + wedge. Every year 2023-2025.
  G2 depth CV:      per-year overnight depth CV <= 0.20 (caiso-81/86/87/88).
  G3 depth LOYO:    mean-of-other-two predicts the held-out year's overnight
                    depth within 25%.

Report-only context (no gate): overnight trigger-ON share per year and by
month (the autumn-lane / belly scoping tension, FINDING-caiso92b §6), the
trigger-OFF spread contrast, the parity-vs-wedge hour composition, and the
measured ON-vs-OFF overnight DSW import levels.

Usage: .venv/bin/python scripts/derive_caiso_overnight_wedge.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
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
OVERNIGHT_HOD_MAX = 5  # hod 0-5 inclusive — the FINDING-caiso91c/92b window
PARITY_BAND_TOP = 4.0  # $/MWh, caiso-82 §1 measured parity band top (G1)
CV_MAX = 0.20
LOYO_MAX = 0.25


def actual_prices() -> pd.DataFrame:
    """Dense (year, hour) actual CAISO DA/RT price on the model clock."""
    df = pd.read_parquet(ACTUAL_LMP).set_index(["year", "hour"])
    full = pd.MultiIndex.from_product([YEARS, range(HOURS)], names=["year", "hour"])
    return df.reindex(full)


def spread_stats(spread: np.ndarray, mask: np.ndarray) -> str:
    """Median [p25, p75] of ``spread`` over ``mask`` hours, formatted."""
    s = spread[mask & np.isfinite(spread)]
    if s.size == 0:
        return "  (no hours)"
    return (
        f"med {np.median(s):+6.1f}  [p25 {np.percentile(s, 25):+6.1f}, "
        f"p75 {np.percentile(s, 75):+6.1f}]  n={s.size}"
    )


def main() -> None:
    """Run the pre-registered overnight no-wedge gates; exit 0 PASS / 2 FAIL."""
    wheel_mult, wheel_add = CAISO_IMPORT_DELIVERY_BASIS["DSW_CCGT"]
    net = corridor_net_import()
    hub = hub_prices()
    act = actual_prices()
    hod = np.arange(HOURS) % 24
    overnight = hod <= OVERNIGHT_HOD_MAX

    print("=== CAISO OVERNIGHT (hod 0-5) south-corridor no-wedge gate ===")
    print(
        f"trigger: PALOVRDE < {HR_CCGT:.2f} x SoCal_citygate_weekly "
        f"+ {CAISO_DSW_SURPLUS_REMOTE_VOM}"
    )
    print(f"parity : PALOVRDE x {1 + wheel_mult} + {wheel_add}   (DSW_CCGT basis)")

    g1_ok = True
    depths: dict[int, float] = {}
    for yr in YEARS:
        pv = hub.loc[yr]["PALOVRDE"].to_numpy()
        flow = net.loc[yr]["WECC_DSW"].to_numpy()
        gas = socal_citygate_weekly_hourly(yr, HOURS)
        da = act.loc[yr]["da"].to_numpy()
        rt = act.loc[yr]["rt"].to_numpy()
        wedge = CARB_UNSPECIFIED_IMPORT_EF * STATE_CARBON_PRICE_BY_ISO["CAISO"][yr]

        floor = HR_CCGT * gas + CAISO_DSW_SURPLUS_REMOTE_VOM
        measured = np.isfinite(pv)
        on = measured & (pv < floor)
        on_ov = on & overnight
        meas_ov = measured & overnight

        # Delivery basis is (loss fraction, adder): hub x (1 + loss) + adder —
        # the caiso-82 §1 "Palo Verde x1.03 + $4" construction.
        parity = pv * (1.0 + wheel_mult) + wheel_add
        spread_da = da - parity
        spread_rt = rt - parity

        print(f"\n--- {yr}  (wedge reference {wedge:+.1f} $/MWh) ---")
        print(
            f"  overnight measured-hub hours {int(meas_ov.sum())} "
            f"of {int(overnight.sum())}; trigger-ON share "
            f"{on_ov.sum() / max(meas_ov.sum(), 1):5.1%} ({int(on_ov.sum())} h)"
        )
        by_month = (
            pd.Series(on_ov.astype(float))
            .groupby(
                np.repeat(
                    np.arange(12),
                    [d * 24 for d in [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]],
                )
            )
            .sum()
            .astype(int)
        )
        print(f"  ON hours by month: {by_month.tolist()}")
        print(f"  DA spread  ON : {spread_stats(spread_da, on_ov)}")
        print(f"  DA spread  OFF: {spread_stats(spread_da, meas_ov & ~on)}")
        print(f"  RT spread  ON : {spread_stats(spread_rt, on_ov)}")
        print(f"  RT spread  OFF: {spread_stats(spread_rt, meas_ov & ~on)}")
        sda = spread_da[on_ov & np.isfinite(spread_da)]
        if sda.size:
            parity_share = float((sda <= PARITY_BAND_TOP).mean())
            wedge_share = float((sda >= wedge - 2.0).mean())
            print(
                f"  ON composition: {parity_share:5.1%} parity-consistent "
                f"(<= +{PARITY_BAND_TOP}), {wedge_share:5.1%} wedge-consistent "
                f"(>= {wedge - 2.0:+.1f})"
            )
        m = on_ov & np.isfinite(flow)
        depths[yr] = float(np.percentile(flow[m], 95)) if m.any() else float("nan")
        off_m = (meas_ov & ~on) & np.isfinite(flow)
        print(
            f"  measured DSW net import overnight: ON mean "
            f"{np.nanmean(flow[m]) if m.any() else float('nan'):,.0f} / p95 "
            f"{depths[yr]:,.0f} MW; OFF mean "
            f"{np.nanmean(flow[off_m]) if off_m.any() else float('nan'):,.0f} MW"
        )

        med_da_on = float(np.median(sda)) if sda.size else float("nan")
        ok = np.isfinite(med_da_on) and med_da_on <= PARITY_BAND_TOP
        g1_ok = g1_ok and ok
        print(
            f"  G1 no-wedge (ON median DA spread <= +{PARITY_BAND_TOP}): "
            f"{med_da_on:+.1f} -> {'PASS' if ok else 'FAIL'}"
        )

    vals = np.array([depths[y] for y in YEARS])
    cv = float(vals.std() / vals.mean())
    g2_ok = bool(np.isfinite(cv) and cv <= CV_MAX)
    print(
        f"\n  overnight ON-depths (p95 MW): "
        f"{' / '.join(f'{depths[y]:,.0f}' for y in YEARS)}"
    )
    print(
        f"  G2 year-stability CV = {cv:.3f} (gate <= {CV_MAX}): {'PASS' if g2_ok else 'FAIL'}"
    )

    g3_ok = True
    for held in YEARS:
        pred = float(np.mean([depths[y] for y in YEARS if y != held]))
        err = abs(pred - depths[held]) / depths[held]
        ok = err <= LOYO_MAX
        g3_ok = g3_ok and ok
        print(
            f"  G3 LOYO held-out {held}: mean-of-others {pred:,.0f} vs "
            f"{depths[held]:,.0f} -> {err:.1%} (gate <= {LOYO_MAX:.0%}): "
            f"{'PASS' if ok else 'FAIL'}"
        )

    passed = g1_ok and g2_ok and g3_ok
    print(
        f"\n  OVERALL: "
        f"{'PASS — overnight no-wedge admissible; mechanism design may proceed (build/solve needs owner authorization)' if passed else 'FAIL — file FINDING, do NOT build (owner checkpoint)'}"
    )
    sys.exit(0 if passed else 2)


if __name__ == "__main__":
    main()
