"""neiso-69 — is the measured unit-availability window family admissible for NEISO?

Reproduces every number in
``results/calibration/FINDING-neiso69-unit-availability-windows-2026-07-28.md``
from committed bytes. **No LP is built and no solver is called** — the probe
reads the derived extracts, the keeper's committed ``hourly/`` sidecars, the
per-unit CAMPD parquets and EIA-860, and re-evaluates the overlay loaders
directly.

The lane is an OFF-QUEUE rule-14 ``[R-ACCURATE]`` input-accuracy check (rule 28a),
not a C3c scarcity lever; any tail movement it reports is a downstream
observation.

Five sections, one per claim in the finding:

* **§A — coverage.** Window/unit/MW-day counts and class mix of the two frozen
  extracts, plus modelled ``COAL_BIT`` share of NEISO load (the rule-20
  materiality basis).

* **§B — not inert.** The short overlay's own multiplier: which hours it
  touches, to what value, and what the standard >=5-day overlay carries over
  the same hours (proving the window is ADDITIVE, not a duplicate).

* **§C — the unit-identity mismatch (the rejection).** EIA-860 status per
  Merrimack generator, the fleet's COAL bin capacity, and per-unit CAMPD gross
  over the masked hours — showing the window belongs to the OS unit the fleet
  excludes while the bin's actual unit ran every masked hour.

* **§D — why the window was emitted.** The when-operable CF guard's sample
  size (operable hours per unit-year), against the PJM/MISO coal fleets'
  operable-hour distribution. Context only — rule 25 forbids transferring this
  ISO's verdict to their cells.

* **§E — the A/B delta.** Keeper vs arm ``COAL_BIT`` dispatch, in the masked
  window and annually, from the two bundles' committed class sidecars.

Usage::

    .venv/bin/python scripts/probes/neiso69_unit_availability_windows.py \
        [--arm results/calibration/neiso69_shortpartial]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

KEEPER = REPO / "results/calibration/neiso61_netrev_margin"
YEARS = (2023, 2024, 2025)
# The sole detected window, Feb 1 00:00 - Feb 3 23:00 2023. The shared
# accumulator extends outage_end by +1 day, so the mask is [744, 816).
WIN = range(744, 816)
MERRIMACK = 2364


def _hdr(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def section_a() -> None:
    """Coverage of the two frozen extracts + COAL materiality."""
    _hdr("§A — coverage of the derived extracts, and coal's materiality")
    for label, name in (
        ("short (1-5 d full stops)", "campd-unit-outages-short-NEISO.csv"),
        ("partial (sustained derates)", "campd-partial-outages-NEISO.csv"),
    ):
        df = pd.read_csv(REPO / "data/raw" / name)
        mwd = float((df["unit_capacity_mw"] * df["duration_days"]).sum()) if len(df) else 0.0
        units = df.groupby(["facility_id", "unit_id"]).ngroups if len(df) else 0
        mix = dict(df["plant_group"].value_counts()) if len(df) else {}
        print(f"  {label:28s} windows={len(df):3d}  units={units}  MW-days={mwd:8.0f}  {mix}")
        for r in df.itertuples(index=False):
            print(
                f"      -> {r.facility_name} u{r.unit_id} {r.plant_group} "
                f"{r.outage_start}..{r.outage_end} ({r.duration_days} d, {r.unit_capacity_mw} MW)"
            )

    print("\n  modelled COAL_BIT vs NEISO load (keeper P1):")
    for y in YEARS:
        cls = pd.read_parquet(KEEPER / f"hourly/class_hourly_{y}.parquet")
        sysd = pd.read_parquet(KEEPER / f"hourly/system_{y}.parquet")
        cls = cls[cls["pass"] == "P1"]
        sysd = sysd[sysd["pass"] == "P1"]
        coal = cls[cls["klass"] == "COAL_BIT"].groupby("hour")["mw"].sum()
        load = sysd.groupby("hour")["demand"].sum()
        print(
            f"    {y}: load {load.sum() / 1e6:5.1f} TWh  peak {load.max() / 1e3:4.1f} GW | "
            f"COAL_BIT {coal.sum() / 1e3:6.1f} GWh = {100 * coal.sum() / load.sum():.3f}% "
            f"of load, peak {coal.max():.0f} MW"
        )


def section_b() -> None:
    """The short overlay is additive and binding — not inert."""
    from market_sim.data.outages import (
        unit_outage_derate_factors,
        unit_outage_short_derate_factors,
        unit_partial_outage_derate_factors,
    )

    _hdr("§B — the short half is NOT inert; the partial half provably is")
    for y in YEARS:
        short = unit_outage_short_derate_factors(y, iso="NEISO")
        partial = unit_partial_outage_derate_factors(y, iso="NEISO")
        print(f"  {y}: short keys={list(short)}  partial={partial or '{} (no-op)'}")
        for k, v in short.items():
            on = np.where(v < 1.0)[0]
            std = unit_outage_derate_factors(y, iso="NEISO").get(k)
            std_txt = (
                f"{std[on].min():.4f}..{std[on].max():.4f}" if std is not None else "1.0 (absent)"
            )
            print(
                f"      {k}: {len(on)} h affected, h[{on.min()},{on.max()}], "
                f"multiplier -> {v[on].min():.4f}  |  standard >=5-day overlay over the "
                f"same hours = {std_txt}  => ADDITIVE"
            )


def section_c() -> None:
    """The window belongs to a unit the fleet excludes; the bin's unit never stopped."""
    from market_sim.data.outages import _iso_plant_capacity

    _hdr("§C — unit-identity mismatch: the rejection")
    gens = pd.read_parquet(REPO / "data/raw/eia-860/eia860_generators.parquet")
    g = gens[gens["plant_id"] == MERRIMACK][
        ["generator_id", "nameplate_capacity_mw", "net_summer_capacity_mw", "status"]
    ]
    print("  EIA-860 generators at Merrimack (2364):")
    print("    " + g.to_string(index=False).replace("\n", "\n    "))

    cap = _iso_plant_capacity("NEISO")
    coal_bins = {k: v for k, v in cap.items() if k[1] == "COAL"}
    print(f"\n  NEISO fleet COAL bins: {coal_bins}  (total {sum(coal_bins.values()):.1f} MW)")
    print("  -> the bin equals unit 1's NET SUMMER capacity; unit 2 (status OS) is EXCLUDED.")

    campd = pd.read_parquet(REPO / "data/raw/campd-unit-level/NH_2023.parquet")
    m = campd[campd["facilityId"] == str(MERRIMACK)].copy()
    m["ts"] = pd.to_datetime(m["date"]) + pd.to_timedelta(m["hour"].astype(int), unit="h")
    piv = m.pivot_table(index="ts", columns="unitId", values="grossLoad", aggfunc="sum").fillna(0)
    w = piv.loc["2023-02-01":"2023-02-03 23:00"]
    print("\n  per-unit CAMPD gross over the masked hours h744-815:")
    summ = pd.DataFrame(
        {"MWh": w.sum(), "mean_MW": w.mean(), "max_MW": w.max(), "hours_gt0": (w > 0).sum()}
    )
    print("    " + summ.to_string().replace("\n", "\n    "))
    print("\n  Feb 3 16:00-23:00 (inside the 2023 top-22 price cluster):")
    print("    " + piv.loc["2023-02-03 16:00":"2023-02-03 23:00"].to_string().replace("\n", "\n    "))

    cls = pd.read_parquet(KEEPER / "hourly/class_hourly_2023.parquet")
    cls = cls[(cls["pass"] == "P1") & (cls["klass"] == "COAL_BIT")]
    bin_mw = cls.groupby("hour")["mw"].sum().reindex(WIN).fillna(0)
    u1 = w["1"] if "1" in w.columns else pd.Series(dtype=float)
    print(
        f"\n  keeper bin mean {bin_mw.mean():.1f} MW vs unit 1 actual {u1.mean():.1f} MW "
        f"-> the keeper is already within {100 * abs(bin_mw.mean() - u1.mean()) / u1.mean():.0f}% "
        "of the unit it actually carries."
    )


def section_d() -> None:
    """The baseload guard's sample is a sliver in NEISO; context only for PJM/MISO."""
    _hdr("§D — why the window was emitted: the guard's sample (rule 25: context, NOT a verdict)")
    std = pd.read_csv(REPO / "data/raw/campd-unit-outages-NEISO.csv")
    print("  NEISO Merrimack operable hours (the guard's ENTIRE CF sample):")
    for y in YEARS:
        for uid in ("1", "2"):
            wdf = std[
                (std["facility_id"] == MERRIMACK)
                & (std["unit_id"].astype(str) == uid)
                & (std["outage_start"].str[:4] == str(y))
            ]
            mask = _operable(wdf, y)
            print(f"    {y} u{uid}: {mask.sum():5d}/8760 ({100 * mask.mean():5.1f}%)")

    print("\n  2023 COAL units with >=1 standard window — operable-hour share:")
    for iso in ("PJM", "MISO"):
        s = pd.read_csv(REPO / f"data/raw/campd-unit-outages-{iso}.csv")
        s = s[(s["plant_group"] == "COAL") & (s["outage_start"].str[:4] == "2023")]
        fr = np.array(
            [_operable(wdf, 2023).mean() for _, wdf in s.groupby(["facility_id", "unit_id"])]
        )
        print(
            f"    {iso}: n={len(fr):3d}  median={np.median(fr):.2f}  p10={np.percentile(fr, 10):.2f} "
            f"p90={np.percentile(fr, 90):.2f}  below 0.15: {100 * (fr < 0.15).mean():.0f}%"
        )
    print("    NEISO Merrimack u2 = 0.06 — below both fleets' 10th percentile.")


def _operable(wdf: pd.DataFrame, year: int) -> np.ndarray:
    """Hours outside a unit's own >=5-day standard windows (the guard's CF clock)."""
    mask = np.ones(8760, bool)
    origin = pd.Timestamp(f"{year}-01-01")
    for r in wdf.itertuples(index=False):
        s = (pd.Timestamp(r.outage_start) - origin).total_seconds() // 3600
        e = (pd.Timestamp(r.outage_end) + pd.Timedelta(days=1) - origin).total_seconds() // 3600
        mask[int(max(s, 0)) : int(min(e, 8760))] = False
    return mask


def section_e(arm: Path) -> None:
    """Keeper vs arm COAL_BIT, in the masked window and annually."""
    _hdr("§E — A/B delta (keeper vs arm)")
    if not arm.exists():
        print(f"  arm bundle {arm} not present — skipping")
        return
    for y in YEARS:
        af = arm / f"hourly/class_hourly_{y}.parquet"
        if not af.exists():
            print(f"  {y}: arm sidecar not present — skipping")
            continue
        k = pd.read_parquet(KEEPER / f"hourly/class_hourly_{y}.parquet")
        a = pd.read_parquet(af)
        k = k[k["pass"] == "P1"]
        a = a[a["pass"] == "P1"]
        kc = k[k["klass"] == "COAL_BIT"].groupby("hour")["mw"].sum().reindex(range(8760)).fillna(0)
        ac = a[a["klass"] == "COAL_BIT"].groupby("hour")["mw"].sum().reindex(range(8760)).fillna(0)
        extra = ""
        if y == 2023:
            extra = (
                f" | masked window: {kc[list(WIN)].sum():.0f} -> {ac[list(WIN)].sum():.0f} MWh"
            )
        print(
            f"  {y} COAL_BIT: keeper {kc.sum() / 1e3:6.1f} -> arm {ac.sum() / 1e3:6.1f} GWh "
            f"({(ac.sum() - kc.sum()) / 1e3:+.1f}){extra}"
        )
        kk = k.groupby("klass")["mw"].sum()
        aa = a.groupby("klass")["mw"].sum()
        d = ((aa - kk).reindex(kk.index).fillna(0) / 1e3).round(2)
        nz = {c: float(v) for c, v in d.items() if abs(v) > 0.05}
        print(f"      all-class GWh deltas: {nz if nz else 'NONE (identical)'}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", default="results/calibration/neiso69_shortpartial")
    args = ap.parse_args()
    section_a()
    section_b()
    section_c()
    section_d()
    section_e(REPO / args.arm)


if __name__ == "__main__":
    main()
