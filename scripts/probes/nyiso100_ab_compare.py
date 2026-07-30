"""Score the nyiso-100 simultaneous-import retire against its pre-registered gates.

The single delta is ``ScenarioConfig.nyiso_import_sil_retire``: drop the
``NYISO_simultaneous_import`` ``InterfaceLimit`` from the topology. Its 4,350 MW
is the published **G-J LOCALITY** Bulk Power Transmission Limit for capability
year 2024/2025 — an *internal* New York boundary — installed as the *external*
NYCA seam cap (``docs/FINDING-nyiso100-simultaneous-import-misattribution-2026-07-30.md``).

Both bundles are keeper replays of the SAME recipe (``replay_keeper.py`` reads
the nyiso-99 keeper's own ``meta.json``), so the only difference is the flag.

Gates, from ``docs/PREREG-nyiso100-simultaneous-import-retire-2026-07-30.md`` §3:

* **G0 control identity** — the control bundle must reproduce the keeper
  bit-for-bit (per-class hourly MW, per-zone hourly price, < 1e-6). A miss
  stops the session: nothing below is interpretable.
* **G1 LIVE-mechanism** — the arm's solved topology carries zero import-node
  interface limits, the control's exactly one at 4,350 MW. Checked against the
  bundles' own ``run_config.json`` plus a topology rebuild.
* **G2 mechanism releases** — arm import exceeds 4,350 MW somewhere, and its
  annual max lands in (4,350, 6,800].
* **G3 volume band-held** — monthly model/measured ratio stays in [0.98, 1.02]
  and the upper-edge month count does not fall below the control's. This is
  the check that the arm REALLOCATES a fixed monthly quota rather than
  importing more energy.
* **G4/G5** — C1 / C7 / C8 read from each bundle's scored ``metrics.json``.
* **G6/G7** — C3c tail and the item-9 import statistic, REPORTED, never gates
  (rule 1 ``[R-STRUCT]``).

Usage::

    PYTHONPATH=.:src python scripts/probes/nyiso100_ab_compare.py \\
        --keeper  results/calibration/nyiso99_demandfix \\
        --control results/calibration/nyiso100_control \\
        --arm     results/calibration/nyiso100_silretire
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

YEARS = (2023, 2024, 2025)
SIL_MW = 4350.0
LINK_SUM_MW = 6800.0
IDENTITY_TOL = 1e-6
BAND_LO, BAND_HI = 0.98, 1.02
BAND_EDGE = 1.0195


def class_hourly(bundle: Path, year: int) -> dict[str, np.ndarray]:
    """Model per-class hourly MW from a bundle's P1 class sidecar."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return {
        k: g.sort_values("hour")["mw"].to_numpy(float)[:8760]
        for k, g in df.groupby("klass")
    }


def system_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """Model hourly system frame (price/demand/slack/dump) from a P1 sidecar."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[df["pass"] == "P1"]


def measured_import(year: int) -> np.ndarray:
    """EIA-930 NYIS net import (MW, import-positive) on the model clock."""
    from market_sim.data.eia_loader import nyiso_net_interchange

    return -np.asarray(nyiso_net_interchange(year), dtype=float).reshape(-1)[:8760]


def _r(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson r over the overlapping finite support."""
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    ok = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[ok], b[ok])[0, 1]) if ok.sum() > 2 else float("nan")


def _identity(ref: Path, other: Path) -> tuple[bool, list[str]]:
    """Return (bit-identical, per-year report lines) for two bundles."""
    ok_all, lines = True, []
    for year in YEARS:
        a, c = class_hourly(other, year), class_hourly(ref, year)
        worst, worst_k = 0.0, "-"
        for klass in sorted(set(a) | set(c)):
            d = float(
                np.abs(a.get(klass, np.zeros(8760)) - c.get(klass, np.zeros(8760))).max()
            )
            if d > worst:
                worst, worst_k = d, klass
        key = ["zone", "hour"]
        merged = system_hourly(ref, year)[[*key, "price"]].merge(
            system_hourly(other, year)[[*key, "price"]], on=key, suffixes=("_c", "_a")
        )
        dprice = float((merged["price_a"] - merged["price_c"]).abs().max())
        ok = worst < IDENTITY_TOL and dprice < IDENTITY_TOL
        ok_all &= ok
        lines.append(
            f"  {year}: max |d class MW| {worst:12.6f} ({worst_k})   "
            f"max |d price| {dprice:10.6f} $/MWh   {'PASS' if ok else '**FAIL**'}"
        )
    return ok_all, lines


def _sil_in_topology(bundle: Path) -> tuple[int, float | None]:
    """Rebuild the solved topology from a bundle's run_config and read its SIL."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.model.interchange.spec import (
        IMPORT_ZONE,
        apply_interchange_topology,
        get_interchange_spec,
    )

    rc = json.loads((bundle / "run_config.json").read_text())
    # The solve records the resolved ScenarioConfig under "scenario_config".
    # A bundle predating the field simply lacks the key -> False, which is the
    # correct reading for the keeper and the control.
    retire = bool((rc.get("scenario_config") or {}).get("nyiso_import_sil_retire"))
    cfg = ScenarioConfig().with_overrides(nyiso_import_sil_retire=retire)
    ic = apply_interchange_topology(
        get_iso_config("NYISO"), get_interchange_spec(cfg, "NYISO", 2024), cfg, year=2024
    )
    zone = IMPORT_ZONE["NYISO"]
    seam = [
        lim
        for lim in ic.interface_limits
        if lim.links and all(p[0] == zone for p in lim.links)
    ]
    return len(seam), (float(seam[0].cap_mw) if seam else None)


def main(argv: list[str] | None = None) -> int:
    """Print the G0-G7 verdicts from the three bundles' committed sidecars."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keeper", type=Path, required=True)
    ap.add_argument("--control", type=Path, required=True)
    ap.add_argument("--arm", type=Path, required=True)
    args = ap.parse_args(argv)
    print(f"keeper  = {args.keeper}\ncontrol = {args.control}\narm     = {args.arm}")

    # ---- G0: control reproduces the keeper bit-for-bit ----
    print("\n=== G0 — control identity vs the nyiso-99 keeper ===")
    g0_ok, lines = _identity(args.keeper, args.control)
    print("\n".join(lines))
    print(f"  G0 = {'PASS' if g0_ok else 'FAIL — everything below is void'}")

    # ---- G1: LIVE-mechanism check (nyiso-89 §4a) ----
    print("\n=== G1 — LIVE-mechanism check (import-node interface limits) ===")
    nc, cc = _sil_in_topology(args.control)
    na, ca = _sil_in_topology(args.arm)
    g1_ok = nc == 1 and cc == SIL_MW and na == 0
    print(f"  control: {nc} seam limit(s), cap {cc}   (expect 1 @ {SIL_MW:.0f})")
    print(f"  arm    : {na} seam limit(s), cap {ca}   (expect 0 — retired)")
    print(f"  G1 = {'PASS' if g1_ok else 'FAIL — arm is a silent no-op'}")

    # ---- G2: the mechanism actually releases ----
    print("\n=== G2 — mechanism releases (arm import above the retired cap) ===")
    g2_any = False
    for year in YEARS:
        ic = class_hourly(args.control, year).get("import", np.zeros(8760))
        ia = class_hourly(args.arm, year).get("import", np.zeros(8760))
        above = int((ia > SIL_MW + 1e-6).sum())
        g2_any |= above > 0 and ia.max() <= LINK_SUM_MW + 1e-6
        print(
            f"  {year}: import max {ic.max():7.1f} -> {ia.max():7.1f} MW   "
            f"h > {SIL_MW:.0f}: {int((ic > SIL_MW + 1e-6).sum()):4d} -> {above:4d}   "
            f"h AT old cap: {int((np.abs(ic - SIL_MW) < 0.5).sum()):4d} -> "
            f"{int((np.abs(ia - SIL_MW) < 0.5).sum()):4d}"
        )
    print(f"  G2 = {'PASS' if g2_any else 'FAIL — inert, report the cell as I'}")

    # ---- G3: volume stays band-held ----
    print("\n=== G3 — volume band-held (monthly reconciliation, +-2%) ===")
    from market_sim.data.fleet import _hour_to_month_index

    g3_ok = True
    for year in YEARS:
        meas = measured_import(year)
        mi = _hour_to_month_index(8760)
        tt = np.bincount(mi, weights=meas)
        row = []
        for name, b in (("control", args.control), ("arm", args.arm)):
            imp = class_hourly(b, year).get("import", np.zeros(8760))
            ratio = np.bincount(mi, weights=imp) / tt
            row.append((ratio.min(), ratio.max(), int((ratio >= BAND_EDGE).sum()),
                        imp.sum() / 1e6))
        (lo_c, hi_c, ec, twh_c), (lo_a, hi_a, ea, twh_a) = row
        ok = BAND_LO - 1e-6 <= lo_a and hi_a <= BAND_HI + 1e-6 and ea >= ec
        g3_ok &= ok
        print(
            f"  {year}: ratio range control [{lo_c:.3f},{hi_c:.3f}] -> arm "
            f"[{lo_a:.3f},{hi_a:.3f}]   months at upper edge {ec} -> {ea}   "
            f"import {twh_c:.4f} -> {twh_a:.4f} TWh   {'PASS' if ok else '**FAIL**'}"
        )
    print(f"  G3 = {'PASS' if g3_ok else 'FAIL — band is not holding volume'}")

    # ---- G4/G5: rubric protective gates ----
    print("\n=== G4/G5 — rubric (C1 / C7 / C8) from each bundle's metrics.json ===")
    g45_ok = True
    for name, b in (("control", args.control), ("arm", args.arm)):
        m = json.loads((b / "metrics.json").read_text())
        cr = m["criteria"]
        fc = m["free_class_score"]
        c1 = cr["fuelmix"]["status"]
        c7 = cr["shape"]["status"]
        c8 = cr["forced_share"]["status"]
        if name == "arm":
            g45_ok = (
                c1 == "PASS"
                and c7 == "PASS"
                and c8 == "PASS"
                and fc["all"]["pass"] == fc["all"]["total"]
                and fc["free"]["pass"] == fc["free"]["total"]
            )
        print(
            f"  {name:<8} determination {m['determination']:<8} C1 {c1} "
            f"({fc['headline']})  C7 {c7}  C8 {c8}  "
            f"fails={m['grade_summary']['fails']}"
        )
    print(f"  G4/G5 = {'PASS' if g45_ok else 'FAIL — protective gate breached'}")

    # ---- G6/G7: reported, never gates ----
    print("\n=== G6/G7 — REPORTED, not gated (C3c tail; item-9 import shape) ===")
    for year in YEARS:
        out = []
        for b in (args.control, args.arm):
            s = system_hourly(b, year)
            over = int((s.groupby("hour")["price"].max() > 300.0).sum())
            imp = class_hourly(b, year).get("import", np.zeros(8760))
            out.append(
                (over, float(s["slack"].sum()), float(s["dump"].sum()),
                 _r(imp, measured_import(year)),
                 float(s.groupby("hour")["price"].mean().mean()))
            )
        (oc, sc, dc, rc, pc), (oa, sa, da, ra, pa) = out
        print(
            f"  {year}: h>$300 {oc} -> {oa}   mean LMP {pc:7.2f} -> {pa:7.2f}   "
            f"import r_hr {rc:.3f} -> {ra:.3f}   slack {sc:.1f} -> {sa:.1f}   "
            f"dump {dc:.1f} -> {da:.1f} MWh"
        )

    promote = g0_ok and g1_ok and g2_any and g3_ok and g45_ok
    print(
        f"\nVERDICT: G0 {'PASS' if g0_ok else 'FAIL'} | G1 "
        f"{'PASS' if g1_ok else 'FAIL'} | G2 {'PASS' if g2_any else 'FAIL'} | "
        f"G3 {'PASS' if g3_ok else 'FAIL'} | G4/G5 "
        f"{'PASS' if g45_ok else 'FAIL'}  ->  "
        f"{'KEEPER-RECOMMENDED' if promote else 'NOT PROMOTED'}"
    )
    return 0 if promote else 1


if __name__ == "__main__":
    raise SystemExit(main())
