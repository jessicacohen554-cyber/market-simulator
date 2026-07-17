"""Derive the CAISO UNCONDITIONAL overnight (hod 0-5) south-corridor clean depth — gate check.

Companion to ``derive_caiso_overnight_wedge.py`` (the pre-registered no-wedge
admissibility gate). That gate PASSED — but its ON/OFF contrast showed the
measured overnight no-wedge state is UNCONDITIONAL: the CAISO−PaloVerde spread
sits at delivery parity (med −4.5…−5.2 $/MWh DA) in trigger-OFF overnight
hours too — 96-99 % of 2024/2025 overnight hours, where the caiso-87
hub-below-gas-floor trigger never fires (ON share 1.2 %/3.6 %; 26.4 % in
high-gas 2023). A caiso-87-trigger-conditioned overnight extension is
therefore coverage-starved by construction (27/78 ON hours in 2024/25 against
a 2,190-hour, +1.4/+2.1/+2.6 TWh over-run window): the conditional variant
cannot carry the phenomenon, whatever its depth gates say.

DISCLOSED SEQUENCING (honesty, caiso-86b prohibition): this unconditional
construction was identified AFTER the ON/OFF contrast was seen — it is not
pre-registered. What is frozen: the estimation-gate thresholds (CV <= 0.20,
LOYO <= 25 %, the caiso-81/86/87/88 standard), the depth statistic (p95, the
caiso-87 statistic), the corridor series (EIA-930 CISO DIBAs via
``corridor_net_import``), and the hod 0-5 window (the FINDING-caiso91c/92b
overnight definition, set before any spread was measured). Nothing here is
iterated against the gates; a FAIL files a FINDING and the lane stops.

Derived quantity:

  depth[y] = p95 of measured WECC_DSW corridor net import over ALL overnight
             (hod 0-5) hours of year y — no hub-state conditioning, because
             the measured no-wedge state overnight IS unconditional in-sample.

Forward story (rule 13): the depth is the same WEIM/EDAM clean-transfer
capability the caiso-87 mechanism carries (CARB EIM GHG attribution assigns
surplus non-emitting resources to CAISO transfers; overnight the West carries
NW hydro + wind surplus — the PNW hub's negative overnight prints), read at a
persistent hod window rather than a hub-price state. A forecast year carries
the pooled static entry exactly as ``CAISO_DSW_SURPLUS_CLEAN_DEPTH_STATIC``
does (persistent market structure), and the quantity would regenerate from a
future year's measured corridor flows.

Usage: .venv/bin/python scripts/derive_caiso_overnight_clean_depth.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from derive_caiso_import_tranches import (  # noqa: E402
    YEARS,
    corridor_net_import,
)

HOURS = 8760
OVERNIGHT_HOD_MAX = 5  # hod 0-5 inclusive — FINDING-caiso91c/92b window
CV_MAX = 0.20
LOYO_MAX = 0.25


def main() -> None:
    """Derive per-year unconditional overnight depths; exit 0 PASS / 2 FAIL."""
    net = corridor_net_import()
    hod = np.arange(HOURS) % 24
    overnight = hod <= OVERNIGHT_HOD_MAX

    depths: dict[int, float] = {}
    print("=== CAISO unconditional overnight (hod 0-5) WECC_DSW clean depth ===")
    for yr in YEARS:
        flow = net.loc[yr]["WECC_DSW"].to_numpy()
        m = overnight & np.isfinite(flow)
        depths[yr] = float(np.percentile(flow[m], 95))
        print(
            f"  {yr}: n={int(m.sum())} overnight hours -> mean "
            f"{flow[m].mean():,.0f} / p50 {np.percentile(flow[m], 50):,.0f} / "
            f"p95 {depths[yr]:,.0f} MW"
        )

    vals = np.array([depths[y] for y in YEARS])
    cv = float(vals.std() / vals.mean())
    g_cv = cv <= CV_MAX
    print(
        f"\n  year-stability CV = {cv:.3f} (gate <= {CV_MAX}): {'PASS' if g_cv else 'FAIL'}"
    )

    g_loyo = True
    for held in YEARS:
        pred = float(np.mean([depths[y] for y in YEARS if y != held]))
        err = abs(pred - depths[held]) / depths[held]
        ok = err <= LOYO_MAX
        g_loyo = g_loyo and ok
        print(
            f"  LOYO held-out {held}: mean-of-others {pred:,.0f} vs "
            f"{depths[held]:,.0f} -> {err:.1%} (gate <= {LOYO_MAX:.0%}): "
            f"{'PASS' if ok else 'FAIL'}"
        )

    passed = g_cv and g_loyo
    print(
        f"\n  OVERALL: "
        f"{'PASS — depth admissible; build/solve needs owner authorization' if passed else 'FAIL — file FINDING, do NOT build'}"
    )
    sys.exit(0 if passed else 2)


if __name__ == "__main__":
    main()
