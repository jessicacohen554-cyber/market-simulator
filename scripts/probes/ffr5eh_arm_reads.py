"""FFR-5E-H — extract the pre-registered R1-R4 reads from the paired arms.

Probe script for the FFR-5E hindcast-arm measurement (owner decision D-18(a)
lineage). Reads the two committed bundles produced by
``scripts/run_capacity_hindcast.py`` and prints the reads exactly as
``docs/handoffs/ffr-5e-hindcast-arm-prereg-2026-08-09.md`` §2 pre-registered
them:

* **R1** pool reconciliation — per-year procured injection (``source ==
  "procured"`` ledger rows) named against the EIA-860 vintage sheet, plus the
  ``wind_cap_mw``/``solar_cap_mw`` pool trajectory that shows it is additive.
* **R2** the base-year under-count, restated against the measured vintage
  year-end fleet (stated in the score, never absorbed).
* **R3** the T1-FF posture arm-vs-control: VRE energy, curtailment, prices.
* **R4** in-window exit/entry deltas, REPORTED (never targeted).
* **R5** runtime cache-key hygiene.

Read-only: opens committed bundle artifacts and ``data/raw`` only. Solves
nothing and writes nothing.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

_SRC = Path(__file__).resolve().parents[2] / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from market_sim.model.lp import DispatchResult  # noqa: E402
from market_sim.results.outputs import read_demand  # noqa: E402

YEARS = (2021, 2022, 2023, 2024, 2025)


def run_dir(bundle: Path, iso: str = "MISO") -> Path:
    """Return the single ``<bundle>/<ISO>/<cache_key>/`` scenario-cache dir.

    Args:
        bundle: The ``--out-dir`` a hindcast invocation was given.
        iso: The run's ISO.

    Returns:
        The one runtime-key directory inside the bundle.

    Raises:
        SystemExit: Zero or several key directories are present.
    """
    cands = sorted(p for p in (bundle / iso).iterdir() if p.is_dir())
    if len(cands) != 1:
        raise SystemExit(f"{bundle}: expected 1 runtime-key dir, found {cands}")
    return cands[0]


def ledgers(rd: Path) -> dict[int, dict]:
    """Load every ``evolution_<year>.json`` in a scenario-cache dir."""
    out = {}
    for p in sorted(rd.glob("evolution_*.json")):
        out[int(p.stem.split("_")[1])] = json.loads(p.read_text())
    return out


def procured_rows(led: dict) -> list[dict]:
    """Return a ledger year's ``source == "procured"`` VRE additions.

    The attribution rows live under ``vre_additions`` — the source-tagged,
    per-generator record ``evolve_fleet`` step 4b emits (design §3.5, the rule
    13 attribution requirement). ``renewable_additions`` in the same ledger is
    the AGGREGATED pool delta (zone/tech/mw only, no ``source`` and no EIA-860
    ids), so reading it for provenance silently finds nothing.
    """
    return [
        r for r in (led.get("vre_additions") or []) if r.get("source") == "procured"
    ]


def energy_and_price(rd: Path, year: int) -> dict | None:
    """Compute a solve year's VRE energy, curtailment and prices.

    Args:
        rd: The scenario-cache directory.
        year: Solve year.

    Returns:
        A dict of TWh / $/MWh reads, or ``None`` when the year's dispatch
        parquet is absent (a bridged year solves no LP).
    """
    pq = rd / f"year_{year}.parquet"
    if not pq.exists():
        return None
    res = DispatchResult.from_parquet(pq)
    demand = read_demand(pq)
    wind = float(np.asarray(res.wind_dispatched).sum())
    solar = float(np.asarray(res.solar_dispatched).sum())
    dump = float(np.asarray(res.dump).sum())
    load = float(np.asarray(demand).sum())
    prices = np.asarray(res.prices)
    dem = np.asarray(demand)
    lw = float((prices * dem).sum() / dem.sum()) if dem.sum() else float("nan")
    return {
        "wind_twh": wind / 1e6,
        "solar_twh": solar / 1e6,
        "vre_twh": (wind + solar) / 1e6,
        "dump_twh": dump / 1e6,
        "load_twh": load / 1e6,
        "vre_share": (wind + solar) / load if load else float("nan"),
        "price_load_wtd": lw,
        "price_zone_mean": float(prices.mean()),
    }


def fmt(x: float | None, nd: int = 3) -> str:
    """Format a float for the report tables, or ``-`` when absent."""
    return "-" if x is None else f"{x:,.{nd}f}"


def main(argv: list[str] | None = None) -> int:
    """Print the R1-R5 reads for the control/armed pair."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print(__doc__)
        print("usage: ffr5eh_arm_reads.py <control-bundle> <armed-bundle>")
        return 2
    ctl_b, arm_b = Path(argv[0]), Path(argv[1])
    ctl, arm = run_dir(ctl_b), run_dir(arm_b)
    lc, la = ledgers(ctl), ledgers(arm)

    print("=" * 78)
    print("R5 — runtime cache keys (must be DISTINCT; the FFR-4D hazard)")
    print("=" * 78)
    print(f"  control : {ctl.name}")
    print(f"  armed   : {arm.name}")
    print(f"  distinct: {ctl.name != arm.name}")

    print()
    print("=" * 78)
    print("R1 — pool reconciliation: procured injection vs the vintage seed")
    print("=" * 78)
    print(
        f"{'year':>6} {'ctl wind':>10} {'ctl solar':>10} "
        f"{'arm wind':>10} {'arm solar':>10} {'procured MW':>12} {'rows':>5}"
    )
    tot_proc = 0.0
    proc_detail: list[tuple] = []
    for y in YEARS:
        cw = lc.get(y, {}).get("wind_cap_mw")
        cs = lc.get(y, {}).get("solar_cap_mw")
        aw = la.get(y, {}).get("wind_cap_mw")
        as_ = la.get(y, {}).get("solar_cap_mw")
        rows = procured_rows(la.get(y, {}))
        mw = sum(float(r["mw"]) for r in rows)
        tot_proc += mw
        for r in rows:
            proc_detail.append(
                (y, r.get("tech"), r.get("mw"), r.get("zone"),
                 r.get("eia860_id"), r.get("generator_id"))
            )
        print(
            f"{y:>6} {fmt(cw, 1):>10} {fmt(cs, 1):>10} "
            f"{fmt(aw, 1):>10} {fmt(as_, 1):>10} {fmt(mw, 1):>12} {len(rows):>5}"
        )
    print(f"\n  total procured MW injected across the window: {tot_proc:,.1f}")
    print("  per-row provenance (rule 13 attribution — design §3.5):")
    for y, tech, mw, zone, pid, gid in proc_detail:
        print(f"    {y}  {tech:<5} {float(mw):8.1f} MW  {zone:<16} "
              f"plant {pid} gen {gid}")
    if not proc_detail:
        print("    (none)")

    # Additivity: the armed pool must exceed the control pool by exactly the
    # cumulative procured MW, which is what "additive on the vintage seed"
    # means operationally (FFR-3V §6's promise).
    print("\n  ADDITIVITY CHECK (armed pool − control pool vs cumulative procured):")
    cum = 0.0
    for y in YEARS:
        rows = procured_rows(la.get(y, {}))
        cum += sum(float(r["mw"]) for r in rows)
        for tech, key in (("wind", "wind_cap_mw"), ("solar", "solar_cap_mw")):
            c, a = lc.get(y, {}).get(key), la.get(y, {}).get(key)
            if c is None or a is None:
                continue
            cum_tech = sum(
                float(r["mw"])
                for yy in YEARS
                if yy <= y
                for r in procured_rows(la.get(yy, {}))
                if r.get("tech") == tech
            )
            delta = a - c
            flag = "OK" if abs(delta - cum_tech) < 0.05 else "MISMATCH"
            if abs(delta) > 1e-9 or abs(cum_tech) > 1e-9:
                print(
                    f"    {y} {tech:<5} pool Δ={delta:+10.1f}  "
                    f"cumulative procured={cum_tech:10.1f}  {flag}"
                )

    print()
    print("=" * 78)
    print("R3 — T1-FF posture: VRE energy, curtailment, prices (arm vs control)")
    print("=" * 78)
    hdr = (
        f"{'year':>6} {'metric':<16} {'control':>12} {'armed':>12} "
        f"{'delta':>12} {'pct':>9}"
    )
    print(hdr)
    for y in YEARS:
        ec, ea = energy_and_price(ctl, y), energy_and_price(arm, y)
        if ec is None and ea is None:
            print(f"{y:>6} {'(bridged — no LP)':<16}")
            continue
        for m in (
            "wind_twh", "solar_twh", "vre_twh", "dump_twh",
            "vre_share", "price_load_wtd", "price_zone_mean",
        ):
            c = None if ec is None else ec[m]
            a = None if ea is None else ea[m]
            if c is None or a is None:
                print(f"{y:>6} {m:<16} {fmt(c):>12} {fmt(a):>12}")
                continue
            d = a - c
            pct = (d / c * 100.0) if c else float("nan")
            print(
                f"{y:>6} {m:<16} {fmt(c):>12} {fmt(a):>12} "
                f"{d:>+12.4f} {pct:>+8.3f}%"
            )

    print()
    print("=" * 78)
    print("R4 — in-window exit/entry deltas (REPORTED, never targeted)")
    print("=" * 78)
    for label, key in (
        ("additions (thermal)", "thermal_additions"),
        ("retirements", "retirements"),
        ("storage additions", "storage_additions"),
        ("renewable additions", "renewable_additions"),
    ):
        print(f"\n  -- {label} --")
        any_row = False
        for y in YEARS:
            def agg(led: dict) -> dict:
                out: dict[str, float] = defaultdict(float)
                for r in (led.get(key) or []):
                    k = r.get("fuel") or r.get("tech") or "?"
                    if key == "renewable_additions":
                        k = f"{k}/{r.get('source', '?')}"
                    out[k] += float(r.get("mw") or 0.0)
                return dict(out)

            ac, aa = agg(lc.get(y, {})), agg(la.get(y, {}))
            if not ac and not aa:
                continue
            any_row = True
            keys = sorted(set(ac) | set(aa))
            for k in keys:
                c, a = ac.get(k, 0.0), aa.get(k, 0.0)
                mark = "" if abs(a - c) < 0.05 else "   <-- DELTA"
                print(f"    {y} {k:<22} control {c:10.1f}  armed {a:10.1f}{mark}")
        if not any_row:
            print("    (none in either arm, any year)")

    print("\n  -- reserve margin / peak --")
    for y in YEARS:
        rc, ra = lc.get(y, {}), la.get(y, {})
        if not rc and not ra:
            continue
        print(
            f"    {y} reserve_margin control {fmt(rc.get('reserve_margin'), 6):>10}"
            f"  armed {fmt(ra.get('reserve_margin'), 6):>10}"
            f"   peak_mw {fmt(rc.get('peak_demand_mw'), 1):>10}"
            f" / {fmt(ra.get('peak_demand_mw'), 1):>10}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
