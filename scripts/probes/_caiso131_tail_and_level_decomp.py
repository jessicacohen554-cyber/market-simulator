"""caiso-131: the C3c scarcity-tail deficit and the C3a-2025 level residual, decomposed.

Measurement-only instrument for FINDING-caiso131. **No LP is built or solved.**
Every number in the FINDING is reproducible from:

  * the keeper bundle's COMMITTED hourly sidecars
    (``hourly/system_<y>.parquet``, ``class_hourly_<y>.parquet``,
    ``storage_<y>.parquet``) — never a replay;
  * the committed actual hourly LMP reference
    (``data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet``);
  * the committed benchmark parts (``frontend/data/backcast/bench/CAISO/<y>.json.gz``)
    and the committed actual-tail part (``frontend/data/backcast/tail/actual_tail.json``);
  * the committed CA citygate daily gas print
    (``data/raw/gas-prices/caiso_citygate_daily.csv``);
  * a ``run_year(fleet_only=True)`` fleet reconstruction (section C/D only) —
    the caiso-105/121/127 recipe, which assembles the P0 objective (``mc_base``)
    and the exact availability caps ``pmax x availability`` **without building
    a matrix or calling HiGHS**.

Sections
--------
A. C3a on the RUBRIC basis, reproduced digit-for-digit, plus the per-year
   margin to the +-10 % band and the per-year C3c band.
B. The C3a residual decomposed by actual-price regime and by month, on ONE
   common weight vector (the rubric's own ``rt_lw`` weights,
   ``eia_loader.load_demand``), so the bin contributions sum to the gap.
C. The C3c tail deficit: what the model prices in the hours the measured RT
   market cleared above the threshold, the model's own dispatchable headroom
   in those hours, and the top of its own offer stack. This is the
   (a) surplus / (b) reserve-dual / (c) offer-ceiling discriminator.
D. The steepening requirement: the capability sitting in the band
   ``(lambda, threshold]`` in the measured tail hours, decomposed by fuel
   group — the MW that would have to be removed or re-priced for the energy
   dual to reach the threshold.
E. What drives the measured tail hours (net load, net-load ramp, CA citygate
   gas), against the year's own distribution.

Usage
-----
    PYTHONPATH=.:src:scripts .venv/bin/python \\
        scripts/probes/_caiso131_tail_and_level_decomp.py \\
        results/calibration/caiso130_nameplate_B [--years 2023 2024 2025] \\
        [--sections ABCDE] [--recon-cache DIR]

Section C/D need the fleet reconstruction, which takes a few minutes per year;
``--recon-cache`` persists it as an npz so re-runs are instant. Sections A/B/E
need only committed artifacts and run in seconds.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

ISO = "CAISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
THRESHOLD = 200.0  # rubric §5 per-ISO C3c threshold for CAISO
TAIL_LO, TAIL_HI, TAIL_SMALL = 0.5, 2.0, 10  # scripts/calibration_verdict.py
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
BENCH = REPO / "frontend/data/backcast/bench/CAISO"
TAIL_PART = REPO / "frontend/data/backcast/tail/actual_tail.json"
CITYGATE = REPO / "data/raw/gas-prices/caiso_citygate_daily.csv"

# meta.json key -> run_year kwarg (the caiso-105 _META_RENAME, verbatim).
_META_RENAME = {
    "coal_prb_passthrough_sigmoid": "prb_sigmoid",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
GAS_GROUPS = ("gas_cc", "gas_ct", "gas_st")
GAS_KLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")


# ---------------------------------------------------------------------------
# committed-artifact readers
# ---------------------------------------------------------------------------
def actual_rt(year: int) -> np.ndarray:
    """Committed hourly actual RT price ($/MWh), NaN where uncovered."""
    a = pd.read_parquet(ACTUAL_LMP)
    return a[a["year"] == year].set_index("hour")["rt"].reindex(range(HOURS)).to_numpy()


def bench_avg_lmp(year: int) -> dict:
    """The committed benchmark ``avgLMP`` block (carries the C3a actual)."""
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        return json.load(fh)["bench"]["avgLMP"]


def actual_tail_counts(year: int) -> dict:
    """The committed actual-tail part row for this ISO-year."""
    return json.loads(TAIL_PART.read_text())["isos"][ISO][str(year)]


def system_frame(bundle: Path, year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """P1 per-zone hourly (price, demand) pivots from the committed sidecar."""
    d = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    price = d.pivot_table(index="hour", columns="zone", values="price")
    demand = d.pivot_table(index="hour", columns="zone", values="demand")
    return price, demand


def ca_zones(price: pd.DataFrame) -> list[str]:
    """The in-CA model zones (the WECC_* nodes are import nodes, not load)."""
    return [z for z in price.columns if not str(z).startswith("WECC")]


def model_system_price(bundle: Path, year: int) -> tuple[np.ndarray, np.ndarray]:
    """Hourly CA demand-weighted model lambda, and hourly CA demand (MW)."""
    price, demand = system_frame(bundle, year)
    ca = ca_zones(price)
    p = (price[ca] * demand[ca]).sum(axis=1) / demand[ca].sum(axis=1)
    return p.to_numpy(), demand[ca].sum(axis=1).to_numpy()


def model_c3a(bundle: Path, year: int) -> float:
    """C3a model metric: zonal demand-weighted mean LMP over the CA zones.

    The rubric's construction (``lmp[zone].p`` weighted by ``lmp[zone].d``),
    which is what ``render_calibration_html`` emits and the scorer reads.
    """
    price, demand = system_frame(bundle, year)
    ca = ca_zones(price)
    num = float((price[ca] * demand[ca]).to_numpy().sum())
    den = float(demand[ca].to_numpy().sum())
    return num / den


def class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """P1 per-class hourly MW pivot from the committed sidecar."""
    c = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return c[c["pass"] == "P1"].pivot_table(index="hour", columns="klass", values="mw")


def storage_discharge(bundle: Path, year: int) -> np.ndarray:
    """P1 fleet-total hourly storage discharge (MW) from the committed sidecar."""
    s = pd.read_parquet(bundle / "hourly" / f"storage_{year}.parquet")
    s = s[s["pass"] == "P1"]
    return (
        s.pivot_table(index="hour", columns="tech", values="discharge_mw")
        .sum(axis=1)
        .to_numpy()
    )


def rubric_weights(year: int) -> np.ndarray:
    """The rubric's ``rt_lw`` weights: measured system load (eia_loader)."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia_loader import load_demand

    return np.asarray(load_demand(ISO, year, get_iso_config(ISO))).sum(axis=0)[:HOURS]


def citygate_daily(year: int) -> np.ndarray:
    """CA composite citygate ($/MMBtu) broadcast onto the year's 8760 hours."""
    g = pd.read_csv(CITYGATE, parse_dates=["date"]).set_index("date")[
        "ca_composite_usd_mmbtu"
    ]
    cal = pd.date_range("2023-01-01", "2025-12-31", freq="D")
    g = g.reindex(cal.union(g.index)).sort_index().ffill().bfill().reindex(cal)
    stamps = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(np.arange(HOURS), unit="h")
    return g.reindex(stamps.normalize()).to_numpy()


# ---------------------------------------------------------------------------
# fleet reconstruction (no LP) — sections C/D
# ---------------------------------------------------------------------------
def fleet_state(bundle: Path, year: int) -> dict:
    """``run_year(fleet_only=True)`` with the bundle's own meta flags.

    The caiso-105/121/127 reconstruction: meta.json keys renamed onto the
    ``run_year`` signature. Assembles the fleet, the availability overlay and
    the P0 objective; builds no matrix and calls no solver.
    """
    import inspect

    from run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {
        _META_RENAME.get(k, k): v
        for k, v in meta.items()
        if _META_RENAME.get(k, k) in params and _META_RENAME.get(k, k) not in skip
    }
    gp = meta["gas_prices"]
    gas = float(gp.get(str(year), gp.get(year, 0.0)))
    return run_year(
        year,
        meta["iso"],
        int(meta.get("hours", HOURS)),
        gas,
        {},
        fleet_only=True,
        **kwargs,
    )


def recon(bundle: Path, year: int, cache: Path | None) -> dict:
    """Per-unit ``cap = pmax x availability``, ``mc_base`` and the fuel group.

    Cached as an npz when ``cache`` is given — the reconstruction is
    deterministic in the bundle's meta, so the cache is a pure speed-up.
    """
    if cache is not None:
        p = cache / f"caiso131_recon_{year}.npz"
        if p.exists():
            z = np.load(p, allow_pickle=True)
            return {"cap": z["cap"], "mc": z["mc"], "fuel": z["fuel"]}
    from market_sim.data.fleet import FUEL_TYPE_MAP

    inv = {v: k for k, v in FUEL_TYPE_MAP.items()}
    state = fleet_state(bundle, year)
    fa = state["fleet_arrays"]
    cap = (fa.pmax[:, None] * np.asarray(fa.availability, dtype=float)).astype(
        np.float32
    )
    mc = np.asarray(state["mc_base"], dtype=np.float32)
    fuel = np.array([inv.get(int(i), str(i)) for i in np.asarray(fa.fuel_type_idx)])
    if cache is not None:
        cache.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            cache / f"caiso131_recon_{year}.npz", cap=cap, mc=mc, fuel=fuel
        )
    return {"cap": cap, "mc": mc, "fuel": fuel}


# ---------------------------------------------------------------------------
# A. the two gates, on the rubric's own basis
# ---------------------------------------------------------------------------
def section_a(bundle: Path, years: tuple[int, ...]) -> None:
    """C3a on the rubric basis + the per-year band margins, and the C3c band."""
    print("\n=== A. the two failing criteria, on the rubric's own basis ===")
    print(
        "  C3a: model = zonal demand-weighted mean LMP over the CA zones; "
        "actual = committed bench avgLMP.rt_lw; band +-10 % (clean PASS/FAIL)"
    )
    for year in years:
        m = model_c3a(bundle, year)
        a = float(bench_avg_lmp(year)["rt_lw"])
        pct = 100.0 * (m / a - 1.0)
        edge = 1.10 * a
        print(
            f"    {year}: model {m:6.2f}  actual {a:6.2f}  {pct:+6.2f} %  "
            f"[{'FAIL' if abs(pct) > 10 else 'PASS'}]  band edge {edge:6.2f} "
            f"-> margin {edge - m:+5.2f} $/MWh"
        )
    print(
        f"\n  C3c: model tail hours (max zonal LMP > ${THRESHOLD:.0f}) vs the "
        f"committed RT actual; band [{TAIL_LO}x, {TAIL_HI}x], "
        f"|delta| <= {TAIL_SMALL} h when the actual is < {TAIL_SMALL} h"
    )
    for year in years:
        price, _ = system_frame(bundle, year)
        mx = price.max(axis=1).to_numpy()
        model_h = int((mx > THRESHOLD).sum())
        rec = actual_tail_counts(year)
        rt = float(rec["rt_gt"])
        if rt < TAIL_SMALL:
            ok = abs(model_h - rt) <= TAIL_SMALL
            band = f"|delta| <= {TAIL_SMALL} h (small-count)"
        else:
            ok = TAIL_LO <= (model_h / rt if rt else 0) <= TAIL_HI
            band = f"[{TAIL_LO * rt:.1f}, {TAIL_HI * rt:.0f}] h"
        print(
            f"    {year}: model {model_h:3d} h  actual RT {rt:5.0f} h  "
            f"required {band:28s} [{'PASS' if ok else 'FAIL'}]   "
            f"(model max zonal LMP over the year ${mx.max():.1f})"
        )


# ---------------------------------------------------------------------------
# B. where the C3a residual lives
# ---------------------------------------------------------------------------
def section_b(bundle: Path, years: tuple[int, ...]) -> None:
    """Decompose the C3a residual by actual-price regime and by month.

    Both sides carry the SAME weights (the rubric's ``rt_lw`` measured-load
    weights) so the per-bin contributions sum exactly to the printed gap. The
    printed gap is therefore slightly smaller than section A's, whose model
    side is weighted by the model's own demand; the difference is a
    weight-basis term, reported at the foot of each year.
    """
    print("\n=== B. where the C3a residual lives (common rt_lw weights) ===")
    bins = [-1e9, 0, 20, 40, 60, 100, 200, 1e9]
    lbl = ["<0", "0-20", "20-40", "40-60", "60-100", "100-200", ">200"]
    for year in years:
        p, _ = model_system_price(bundle, year)
        a = actual_rt(year)
        w0 = rubric_weights(year)
        v = ~np.isnan(a) & (w0 > 0)
        w = np.where(v, w0, 0.0)
        w = w / w.sum()
        mm = float((p * w).sum())
        aa = float((np.nan_to_num(a) * w).sum())
        gap = mm - aa
        print(
            f"\n  {year}: model {mm:6.2f}  actual {aa:6.2f}  "
            f"gap {gap:+5.2f} $/MWh ({100 * (mm / aa - 1):+.2f} %)"
        )
        grp = pd.cut(pd.Series(a), bins, labels=lbl).to_numpy()
        print("    by ACTUAL price regime")
        print(
            f"      {'bin':>8}  {'hrs':>5} {'weight':>7} {'model':>8} "
            f"{'actual':>8} {'contrib$':>9} {'share':>7}"
        )
        for k in lbl:
            sel = (grp == k) & v
            if w[sel].sum() <= 0:
                continue
            con = float(((p - np.nan_to_num(a))[sel] * w[sel]).sum())
            print(
                f"      {k:>8}  {int(sel.sum()):5d} {w[sel].sum():7.3f} "
                f"{float((p * w)[sel].sum() / w[sel].sum()):8.2f} "
                f"{float((a * w)[sel].sum() / w[sel].sum()):8.2f} "
                f"{con:+9.3f} {con / gap:7.2f}"
            )
        mon = (
            pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(np.arange(HOURS), unit="h")
        ).month
        print("    by MONTH")
        row = []
        for k in range(1, 13):
            sel = (mon == k) & v
            con = float(((p - np.nan_to_num(a))[sel] * w[sel]).sum())
            row.append(f"{k:02d}:{con:+.2f}")
        print("      " + "  ".join(row))
        mc3a = model_c3a(bundle, year)
        print(
            f"    weight-basis term: model {mc3a:.2f} on its OWN demand weights "
            f"vs {mm:.2f} on the rt_lw weights = {mc3a - mm:+.2f} $/MWh "
            "(extract basis is frozen — reported, not actionable)"
        )


# ---------------------------------------------------------------------------
# C. the tail deficit and the three-way discriminator
# ---------------------------------------------------------------------------
def section_c(bundle: Path, years: tuple[int, ...], cache: Path | None) -> None:
    """What the model prices, and how much slack it holds, in the tail hours."""
    print(
        "\n=== C. the C3c tail deficit: (a) surplus / (b) reserve dual / "
        "(c) offer ceiling ==="
    )
    for year in years:
        p, _ = model_system_price(bundle, year)
        price, _ = system_frame(bundle, year)
        a = actual_rt(year)
        tail = np.where(a > THRESHOLD)[0]
        r = recon(bundle, year, cache)
        cap, mc, fuel = r["cap"], r["mc"], r["fuel"]
        cls = class_hourly(bundle, year)
        gas_d = cls[[k for k in GAS_KLASSES if k in cls]].sum(axis=1).to_numpy()
        gas_c = cap[np.isin(fuel, GAS_GROUPS)].sum(axis=0)
        imp_d = cls["import"].to_numpy() if "import" in cls else np.zeros(HOURS)
        imp_c = cap[fuel == "import"].sum(axis=0)
        hyd_d = cls["hydro"].to_numpy() if "hydro" in cls else np.zeros(HOURS)
        hyd_c = cap[fuel == "hydro"].sum(axis=0)
        head = (gas_c - gas_d) + (imp_c - imp_d) + (hyd_c - hyd_d)
        top = np.argsort(-p)[:50]
        sd = storage_discharge(bundle, year)
        print(f"\n  {year}  ({len(tail)} measured RT tail hours)")
        print(
            f"    (b) reserve dual: nonzero reserve_price hours "
            f"{int((pd.read_parquet(bundle / 'hourly' / f'system_{year}.parquet')['reserve_price'] != 0).sum())}"
            f" of {HOURS * price.shape[1]} zone-hours; "
            f"unserved-energy (slack) hours "
            f"{int((pd.read_parquet(bundle / 'hourly' / f'system_{year}.parquet')['slack'] > 1e-6).sum())}"
        )
        print(
            f"    (c) offer stack top: max unit offer over the year "
            f"${float(np.nanmax(mc)):.0f}/MWh; capability offered above "
            f"${THRESHOLD:.0f} averages "
            f"{float(np.where(mc > THRESHOLD, cap, 0).sum(axis=0).mean()):.0f} MW/h"
        )
        print(
            f"    (a) dispatchable headroom (gas+import+hydro, "
            f"cap - dispatch): median {np.median(head):6.0f} MW | "
            f"model top-50 lambda hours {np.median(head[top]):6.0f} | "
            f"MIN over the year {head.min():6.0f} MW"
        )
        if len(tail):
            print(
                f"    in the {len(tail)} measured tail hours: model lambda "
                f"${p[tail].mean():6.1f} vs actual ${np.nanmean(a[tail]):6.1f}; "
                f"headroom {np.median(head[tail]):.0f} MW; storage discharging "
                f"{sd[tail].mean():.0f} MW"
            )


# ---------------------------------------------------------------------------
# D. the steepening requirement
# ---------------------------------------------------------------------------
def section_d(bundle: Path, years: tuple[int, ...], cache: Path | None) -> None:
    """Capability in the band ``(lambda, threshold]`` during the tail hours."""
    print(
        f"\n=== D. the steepening requirement: MW in the band "
        f"(lambda, ${THRESHOLD:.0f}] that must be removed or re-priced ==="
    )
    for year in years:
        p, _ = model_system_price(bundle, year)
        a = actual_rt(year)
        tail = np.where(a > THRESHOLD)[0]
        if not len(tail):
            continue
        r = recon(bundle, year, cache)
        cap, mc, fuel = r["cap"], r["mc"], r["fuel"]
        groups = {
            "gas_cc": fuel == "gas_cc",
            "gas_ct": fuel == "gas_ct",
            "gas_st": fuel == "gas_st",
            "import": fuel == "import",
            "hydro": fuel == "hydro",
            "other": ~np.isin(fuel, [*GAS_GROUPS, "import", "hydro"]),
        }
        print(f"\n  {year}  (model lambda ${p[tail].mean():.0f} in the tail hours)")
        total = 0.0
        for name, mask in groups.items():
            mw = float(
                np.mean(
                    [
                        cap[mask & (mc[:, h] > p[h]) & (mc[:, h] <= THRESHOLD), h].sum()
                        for h in tail
                    ]
                )
            )
            total += mw
            print(f"    {name:>8}  {mw:8.0f} MW")
        print(f"    {'TOTAL':>8}  {total:8.0f} MW")


# ---------------------------------------------------------------------------
# E. what drives the measured tail hours
# ---------------------------------------------------------------------------
def section_e(bundle: Path, years: tuple[int, ...]) -> None:
    """Net load, net-load ramp and CA citygate gas in the measured tail hours."""
    print(
        "\n=== E. what drives the measured tail hours (vs the year's own "
        "distribution) ==="
    )
    for year in years:
        a = actual_rt(year)
        tail = np.where(a > THRESHOLD)[0]
        if not len(tail):
            continue
        _, dem = model_system_price(bundle, year)
        cls = class_hourly(bundle, year)
        ren = sum(cls[k].to_numpy() for k in ("solar", "wind") if k in cls)
        nl = dem - ren
        ramp = np.r_[0.0, np.diff(nl)]
        gas = citygate_daily(year)
        stamps = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(
            np.arange(HOURS), unit="h"
        )

        def pctile(x: np.ndarray, idx: np.ndarray) -> float:
            return float((x < x[idx].mean()).mean())

        hod = pd.Series(stamps[tail].hour).value_counts().sort_index().to_dict()
        mons = pd.Series(stamps[tail].month).value_counts().sort_index().to_dict()
        print(
            f"\n  {year}  ({len(tail)} tail hours, "
            f"{len(set(stamps[tail].date))} distinct days)"
        )
        print(f"    hour-of-day: {hod}")
        print(f"    month      : {mons}")
        print(
            f"    net load    {nl[tail].mean():7.0f} MW (pctile "
            f"{pctile(nl, tail):.3f})   1-h ramp {ramp[tail].mean():+7.0f} MW "
            f"(pctile {pctile(ramp, tail):.3f})"
        )
        print(
            f"    CA citygate {gas[tail].mean():7.2f} $/MMBtu (pctile "
            f"{pctile(gas, tail):.3f}; year mean {gas.mean():.2f}, "
            f"max {gas.max():.2f})"
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path, help="results/calibration/<keeper bundle>")
    ap.add_argument("--years", type=int, nargs="*", default=list(YEARS))
    ap.add_argument("--sections", default="ABCDE")
    ap.add_argument("--recon-cache", type=Path, default=None)
    args = ap.parse_args()
    years = tuple(args.years)
    sec = args.sections.upper()
    print(f"caiso-131 tail / level decomposition on {args.bundle}")
    if "A" in sec:
        section_a(args.bundle, years)
    if "B" in sec:
        section_b(args.bundle, years)
    if "C" in sec:
        section_c(args.bundle, years, args.recon_cache)
    if "D" in sec:
        section_d(args.bundle, years, args.recon_cache)
    if "E" in sec:
        section_e(args.bundle, years)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
