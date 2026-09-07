"""Derive the CAISO SOUTH-corridor (WECC_DSW) surplus-clean import depth — gate check.

The missing producer for
``model.interchange.spec.CAISO_DSW_SURPLUS_CLEAN_DEPTH_BY_YEAR`` (caiso-87,
``ScenarioConfig.caiso_dsw_surplus_clean``). Its two siblings —
``derive_caiso_overnight_clean_depth.py`` (caiso-93) and
``derive_caiso_daytime_clean_depth.py`` (caiso-94) — have carried committed
producers since they landed; the caiso-87 south surplus depth never did. The
spec's own comment records it as a *scratch* derivation in FINDING-caiso86b,
which means the one measured depth of the three that a re-run could not
reproduce. This script closes that gap (rule 23 [R-FROZEN-DERIVE]: a
measured-behaviour parameter re-derives from its source, and a re-derivation
must be possible before it can be checked).

**NOTHING HERE IS NEW.** The construction is transcribed from the spec block it
reproduces, and it is verified against the committed values before it is
trusted (caiso-262, 2026-09-07)::

    2023  5,312 MW      2024  4,792 MW      2025  5,472 MW
    ^ committed         ^ committed         ^ committed
    = derived           = derived           = derived        (exact, to the MW)

Construction (identical to the two siblings, south inputs, all hours):

  trigger[t] = PALOVRDE hub DA LMP[t] < HR_CCGT x SoCal_citygate_weekly[t]
               + remote VOM
               (HR_CCGT = 6.97, ``transmission._CAISO_IMPORT_COUPLE_HR``;
               VOM = ``CAISO_DSW_SURPLUS_REMOTE_VOM`` = $2.5; gas = the
               measured SoCal citygate weekly print — the documented rule-14
               LDC-citygate proxy for the desert-SW border hubs). The hub's own
               price below the remote gas-CCGT floor means gas is NOT the hub's
               marginal resource, so the surplus is clean. AZ/NV are
               uncarbonized, hence no carbon term.
  depth[y]   = p95 of measured WECC_DSW corridor net import (EIA-930 CISO
               DIBAs, model clock) over trigger-ON hours of year y.

Unlike the daytime sibling this is UNCONDITIONAL on hour-of-day: the caiso-87
surplus tranche arms in any hour whose trigger is on, and the daytime and
overnight legs are scoped to be DISJOINT from it (their windows subtract this
tranche, so no hour double-carries clean depth).

Frozen (NOT iterated against the gates — the caiso-86b prohibition): the gate
thresholds (CV <= 0.20, LOYO <= 25 %, the caiso-81/86/87/88/93 standard), the
depth statistic (p95), the corridor series, and the trigger. A FAIL files a
FINDING and the lane stops.

``--extra-years Y [Y ...]`` reports additional years' depths WITHOUT touching
the pooled static or the gates, which stay computed over the committed
2023-2025 sample (see ``derive_caiso_import_tranches.extra_years``). caiso-262
uses it for the rule-22 2022 validation touchpoint.

Usage: python scripts/data/derive_caiso_dsw_surplus_depth.py [--extra-years 2022]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(
    0, str(REPO)
)  # repo root: canonical scripts.data.* sibling imports on direct run
sys.path.insert(0, str(REPO / "src"))

from scripts.data.derive_caiso_import_tranches import (  # noqa: E402
    YEARS,
    corridor_net_import,
    hub_prices,
)
from scripts.data.derive_caiso_import_tranches import (  # noqa: E402
    extra_years as _extra_years,
)
from market_sim.config.interchange_config import (  # noqa: E402
    CAISO_DSW_SURPLUS_REMOTE_VOM,
)
from market_sim.data.fuel import socal_citygate_weekly_hourly  # noqa: E402

HOURS = 8760
HR_CCGT = 0.37 / 0.0531  # ~6.97, the committed caiso-87 coupling
CV_MAX = 0.20
LOYO_MAX = 0.25
#: The committed spec values this producer must reproduce before it is trusted.
COMMITTED = {2023: 5312.0, 2024: 4792.0, 2025: 5472.0}


def main() -> None:
    """Derive per-year south surplus depths; exit 0 PASS / 2 FAIL."""
    extra = _extra_years(sys.argv[1:])
    net = corridor_net_import(years=(*YEARS, *extra))
    hub = hub_prices(years=(*YEARS, *extra))

    depths: dict[int, float] = {}
    print("=== CAISO south-corridor (WECC_DSW) surplus-clean depth ===")
    print(
        f"trigger: PALOVRDE < {HR_CCGT:.2f} x SoCal_citygate + {CAISO_DSW_SURPLUS_REMOTE_VOM}"
    )
    for yr in (*YEARS, *extra):
        pv = hub.loc[yr]["PALOVRDE"].to_numpy()
        flow = net.loc[yr]["WECC_DSW"].to_numpy()
        gas = np.asarray(socal_citygate_weekly_hourly(yr, HOURS))
        floor = HR_CCGT * gas + CAISO_DSW_SURPLUS_REMOTE_VOM
        measured = np.isfinite(pv)
        on = measured & np.isfinite(floor) & (pv < floor)
        m = on & np.isfinite(flow)
        depths[yr] = float(np.percentile(flow[m], 95))
        tag = "  [report-only, outside the gated sample]" if yr in extra else ""
        print(
            f"  {yr}: trigger-ON {on.mean():5.1%} of hours "
            f"({int(m.sum())} measured) -> p95 depth {depths[yr]:,.0f} MW{tag}"
        )

    # Producer re-proof: the committed spec values must come back to the MW,
    # else this script is not the construction that produced them and its
    # extra-year output means nothing.
    # The spec stores each depth ROUNDED TO THE MW, so the re-proof compares at
    # that grain and prints the unrounded value beside it — a sub-MW difference
    # is the rounding the spec itself applied, not a construction mismatch.
    print("\n  re-proof vs the committed spec values:")
    reproduced = True
    for yr, want in COMMITTED.items():
        got = depths[yr]
        ok = round(got) == round(want)
        reproduced = reproduced and ok
        print(
            f"    {yr}: derived {got:,.3f} vs committed {want:,.0f} -> "
            f"{'MATCH' if ok else f'DIFFERS by {got - want:+,.1f}'}"
        )

    # Gates over the COMMITTED sample only — see extra_years' docstring.
    vals = np.array([depths[y] for y in YEARS])
    cv = float(vals.std() / vals.mean())
    stability_ok = cv <= CV_MAX
    print(f"\n  pooled mean (static entry): {vals.mean():,.0f} MW")
    print(
        f"  year-stability CV = {cv:.3f}  (gate <= {CV_MAX}): "
        f"{'PASS' if stability_ok else 'FAIL'}"
    )

    loyo_ok = True
    for held in YEARS:
        pred = float(np.mean([depths[y] for y in YEARS if y != held]))
        err = abs(pred - depths[held]) / depths[held]
        ok = err <= LOYO_MAX
        loyo_ok = loyo_ok and ok
        print(
            f"  LOYO held-out {held}: mean-of-others {pred:,.0f} vs "
            f"{depths[held]:,.0f} -> {err:.1%}  (gate <= {LOYO_MAX:.0%}): "
            f"{'PASS' if ok else 'FAIL'}"
        )

    passed = reproduced and stability_ok and loyo_ok
    print(
        f"\n  OVERALL: "
        f"{'PASS — construction reproduces and depth admissible' if passed else 'FAIL — file FINDING, do NOT solve'}"
    )
    sys.exit(0 if passed else 2)


if __name__ == "__main__":
    main()
