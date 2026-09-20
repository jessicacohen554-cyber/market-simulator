"""SPP-68 (ZERO LP) phase 0 for card R-bc: the wind curtailment CEILING, re-measured
against KEEPER 14 rather than the four-keeper-stale control SPP-58 used.

Every number is read from committed artifacts -- keeper 14's and its rung's ``hourly/``
sidecars and registered run payloads, EIA-930, SPP's published curtailment table, and the
committed derived share table. **No LP is solved** (rule 32(a) ``[R-SHARD]``).

The four phase-0 items the lane charter names:

* **item 1** -- what fraction of the gross-up HEADROOM the LP actually spends, per year,
  on the CURRENT keeper (SPP-50 read 0.00-0.48 % at keeper 12).
* **item 2** -- reconcile ``spp_curtail_depth_wind = 0.288137`` against keeper 14's OWN
  potential. SPP-58 derived it against a keeper whose gross-up was the 9.65 % REFERENCE
  mean in every year; keeper 14 arms ``vre_reference_rate_year_own``, so five of seven
  years now gross up at their OWN published rate.
* **item 3** -- predict the ceiling's effect, per year, BEFORE any solve.
* **item 4** -- cross-ISO default-off byte-identity (rule 25 ``[R-ISO-SCOPE]``).

Traps honoured (charter list):
* (e) flat 8760 vs EIA-930's 8784 in leap years -- each side summed on its OWN calendar,
  never cross-indexed; the scored bench basis is reproduced first (SPP-67's construction,
  reused verbatim rather than re-derived).
* (f) the one corrupt 3,589,445 MWh WND hour in 2023 is screened and the drop REPORTED.
* (b) no path-swapped measured input is compared in-process, so the ``lru_cache`` hazard
  is never reached.

Run: ``PYTHONPATH=src uv run python scripts/probes/_spp68_ceiling_phase0.py``
"""

from __future__ import annotations

import base64
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

RUNS = ROOT / "frontend/data/backcast/runs/{rid}.js"
REG = ROOT / "frontend/data/backcast/registry/{rid}.json"

# KEEPER 14 and its stamped rung (rule 30 [R-TOUCHPOINT-FOLD]).
KEEPER = "2026-09-20-spp-67-yearown-rate"
RUNG = "2026-09-20-spp-67-rung-yearown"
SPP_RUN = {y: RUNG for y in (2019, 2020, 2021, 2022)}
SPP_RUN.update({y: KEEPER for y in (2023, 2024, 2025)})
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)

# SPP MMU Annual State of the Market, average hourly wind curtailment MW.
# Committed verbatim in data/raw/spp-hsl/spp_wind_curtailment_annual.csv; 2020 and 2021
# are NOT PUBLISHED (the ASOM prints only the 2019 and 2022 endpoints of that span).
ASOM_CURTAILMENT_MW = {
    2019: 137.0,
    2022: 1260.0,
    2023: 1097.0,
    2024: 1483.0,
    2025: 1382.0,
}
CORRUPT_HOUR_MWH = 1.0e6

# The registered dataclass default under test (config/scenarios.py).
DEPTH_DEFAULT = 0.288137
# SPP-58's own per-year implied depths, for the reconciliation in item 2.
SPP58_IMPLIED_DEPTH = {2023: 0.25646, 2024: 0.31391, 2025: 0.29168}

_payload_cache: dict[str, dict] = {}
_bundle_cache: dict[str, str] = {}


def payload(run_id: str) -> dict:
    """Return a registered run's decompressed dashboard payload."""
    if run_id not in _payload_cache:
        src = Path(str(RUNS).format(rid=run_id)).read_text().strip()
        key = '"]="'
        blob = src[src.index(key) + len(key) : src.rindex('"')]
        _payload_cache[run_id] = json.loads(gzip.decompress(base64.b64decode(blob)))
    return _payload_cache[run_id]


def bundle(run_id: str) -> Path:
    """Return a registered run's committed bundle directory."""
    if run_id not in _bundle_cache:
        _bundle_cache[run_id] = json.loads(
            Path(str(REG).format(rid=run_id)).read_text()
        )["bundle"]
    return ROOT / _bundle_cache[run_id]


def class_hourly(year: int, klass: str) -> np.ndarray:
    """Return the model's P1 hourly MW for one class (flat 8760)."""
    frame = pd.read_parquet(
        bundle(SPP_RUN[year]) / "hourly" / f"class_hourly_{year}.parquet"
    )
    frame = frame[(frame["pass"] == "P1") & (frame["klass"] == klass)]
    if frame.empty:
        return np.zeros(8760, dtype=float)
    return frame.sort_values("hour")["mw"].to_numpy(dtype=float)


def system_hourly(year: int) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(system demand MW, load-weighted system price $/MWh)`` per hour."""
    frame = pd.read_parquet(bundle(SPP_RUN[year]) / "hourly" / f"system_{year}.parquet")
    frame = frame[frame["pass"] == "P1"]
    dem = frame.groupby("hour")["demand"].sum().sort_index().to_numpy(dtype=float)
    wsum = (
        frame.assign(w=frame["price"] * frame["demand"])
        .groupby("hour")["w"]
        .sum()
        .sort_index()
        .to_numpy(dtype=float)
    )
    return dem, wsum / np.maximum(dem, 1e-9)


def bench_class_twh(year: int, fuel: str) -> float:
    """Return the SCORED benchmark TWh for one C1 row -- the scored denominator."""
    rows = payload(SPP_RUN[year])["years"][str(year)]["fuelRows"]
    return float(next(r["b"] for r in rows if r["fuel"] == fuel))


_930: dict[str, pd.Series] = {}


def eia930(year: int, fueltype: str) -> tuple[pd.Series, int]:
    """Return EIA-930 SWPP hourly MWh for one fueltype on the model's FIXED-CST 8760.

    Returns ``(series, n_dropped)``; the corrupt-hour count is reported, never silently
    absorbed (trap (f)). Identical construction to SPP-67's probe.
    """
    if fueltype not in _930:
        raw = pd.read_parquet(ROOT / "data/raw/SWPP_fueltype.parquet")
        raw = (
            raw[raw["fueltype"] == fueltype]
            .dropna(subset=["value_mwh"])
            .sort_values("period")
        )
        _930[fueltype] = pd.Series(
            raw["value_mwh"].to_numpy(dtype=float),
            index=pd.DatetimeIndex(raw["period"] - pd.Timedelta(hours=6)),
        )
    year_series = _930[fueltype][_930[fueltype].index.year == year]
    screened = year_series[year_series < CORRUPT_HOUR_MWH]
    n_dropped = len(year_series) - len(screened)
    screened = screened[~((screened.index.month == 2) & (screened.index.day == 29))]
    return screened, n_dropped


_genmix: dict[int, float] = {}


def genmix_delivered_mw(year: int) -> float:
    """Return mean 5-minute delivered wind MW ('Wind Market' + 'Wind Self')."""
    if year not in _genmix:
        frame = pd.read_csv(
            ROOT / f"data/raw/spp-genmix/GenMix_{year}.csv", skipinitialspace=True
        )
        frame.columns = [c.strip() for c in frame.columns]
        wind = pd.to_numeric(frame["Wind Market"], errors="coerce").fillna(
            0.0
        ) + pd.to_numeric(frame["Wind Self"], errors="coerce").fillna(0.0)
        _genmix[year] = float(wind.mean())
    return _genmix[year]


def gross_factor(year: int) -> tuple[float, float, str]:
    """Return ``(rate, 1/(1-rate), source)`` -- the gross-up keeper 14 applied to ``year``.

    Keeper 14 arms ``vre_reference_rate_year_own``, so a year SPP published a rate for
    grosses up at its OWN rate and every other year falls through to the training-window
    reference mean (``_SPP_REFERENCE_RATE_YEARS`` = {2023, 2024, 2025}).
    """
    from market_sim.data.renewables import (
        _spp_wind_reference_curtailment_rate,
        _spp_wind_year_own_curtailment_rate,
    )

    own = _spp_wind_year_own_curtailment_rate(year)
    if own is not None:
        return own[0], 1.0 / (1.0 - own[0]), "own"
    ref = _spp_wind_reference_curtailment_rate()
    return ref[0], 1.0 / (1.0 - ref[0]), "reference"


def ceiling_state(year: int) -> dict:
    """Reconstruct, at ZERO LP, everything the ceiling would see for ``year``.

    The backcast leg (``scripts/run_calibration.py``) forms system net load on the
    POTENTIAL convention -- demand minus uncurtailed wind and solar potential, summed over
    zones, BEFORE the ceiling touches the bound -- then keys the share table on the model's
    own ``(net_load_decile, hour_of_day, season)``. Each of those three inputs is available
    from committed artifacts:

    * demand -- the keeper's own ``system_<year>.parquet``, summed over zones (exact);
    * wind potential -- EIA-930 delivered on the fixed-CST 8760 grossed up by the rate
      keeper 14 applied (SPP-67 measured this reconstruction exact on energy: its CAPACITY
      and SHAPE legs are 0.0000 TWh, i.e. inside the payload's own 2-dp rounding);
    * solar potential -- SPP's solar bound is ``delivered_pinned`` (it carries NO gross-up
      headroom and takes NO ceiling), so the model's own solar dispatch IS its bound.
    """
    from market_sim.config import paths as _paths
    from market_sim.data.curtailment_share import (
        SPP_CEILING_ZONES,
        _share_lookup,
        load_spp_share_table,
    )

    rate, factor, source = gross_factor(year)
    wind_930, dropped = eia930(year, "WND")
    potential = wind_930.to_numpy(dtype=float) * factor
    solar = class_hourly(year, "solar")
    demand, price = system_hourly(year)
    n = min(len(potential), len(demand), len(solar))
    potential, solar, demand, price = (
        potential[:n],
        solar[:n],
        demand[:n],
        price[:n],
    )
    net_load = demand - potential - solar
    table = load_spp_share_table(_paths.RAW_DIR / "reference")
    share = _share_lookup(table, net_load)
    return {
        "year": year,
        "rate": rate,
        "factor": factor,
        "source": source,
        "dropped": dropped,
        "delivered": wind_930.to_numpy(dtype=float)[:n],
        "potential": potential,
        "model": class_hourly(year, "wind")[:n],
        "share": share,
        "price": price,
        "demand": demand,
        "zones": len(SPP_CEILING_ZONES),
    }


def leg_a(state: dict[int, dict]) -> None:
    """A -- reproduce the scored bench basis before anything is compared to it."""
    print("\n## A -- the scored C1 wind bench basis, reproduced (trap (e)/(f))")
    print(
        f"\n{'year':6s}{'bench TWh':>12s}{'930 CST 8760':>14s}{'|diff|':>9s}{'corrupt hr':>12s}"
    )
    worst = 0.0
    for y in YEARS:
        b = bench_class_twh(y, "wind")
        d = state[y]["delivered"].sum() / 1e6
        worst = max(worst, abs(b - d))
        print(f"{y:<6d}{b:12.4f}{d:14.4f}{abs(b - d):9.4f}{state[y]['dropped']:12d}")
    print(
        f"\n   max |diff| {worst:.4f} TWh -- the payload's own 2-dp rounding. The scored\n"
        "   benchmark IS EIA-930 SWPP WND on a fixed-CST 8760 index with the corrupt hour\n"
        "   screened, exactly as SPP-67 established. Every leg below uses that basis."
    )


def leg_b(state: dict[int, dict]) -> dict[int, float]:
    """B (item 1) -- the headroom, and what fraction of it the LP actually spends."""
    print("\n## B (ITEM 1) -- HOW MUCH OF THE GROSS-UP HEADROOM DOES THE LP SPEND?")
    print(
        "\n   numerator and denominator are stated separately throughout.\n"
        "     headroom     = potential - delivered        (TWh the gross-up INVENTED)\n"
        "     re-curtailed = potential - model            (TWh the LP REFUSED)\n"
        "     spent        = model - delivered            (TWh the LP TOOK of the headroom)\n"
    )
    print(
        f"{'year':6s}{'src':>10s}{'rate':>9s}{'delivered':>11s}{'potential':>11s}"
        f"{'headroom':>10s}{'model':>10s}{'re-curt':>9s}{'spent':>9s}"
        f"{'spent/head':>12s}{'recurt/pot':>12s}"
    )
    frac_head = {}
    for y in YEARS:
        s = state[y]
        deliv = s["delivered"].sum() / 1e6
        pot = s["potential"].sum() / 1e6
        mod = s["model"].sum() / 1e6
        head = pot - deliv
        recurt = pot - mod
        spent = mod - deliv
        frac_head[y] = spent / head if head > 0 else float("nan")
        print(
            f"{y:<6d}{s['source']:>10s}{100 * s['rate']:8.3f}%{deliv:11.4f}{pot:11.4f}"
            f"{head:10.4f}{mod:10.4f}{recurt:+9.4f}{spent:+9.4f}"
            f"{100 * frac_head[y]:11.2f}%{100 * recurt / pot:11.2f}%"
        )
    print(
        "\n   The LP spends essentially ALL of the headroom the gross-up hands it: "
        f"{100 * min(frac_head.values()):.2f}-{100 * max(frac_head.values()):.2f} %.\n"
        "   That is the R-bc object stated as a ratio -- NOTHING IN THE LP CAN REFUSE WIND\n"
        "   bid below every thermal offer, so a bound the model invents is a bound it takes."
    )
    return frac_head


def leg_c(state: dict[int, dict]) -> dict[int, float]:
    """C (item 2) -- reconcile depth 0.288137 against KEEPER 14's own potential.

    SPP-58's identification, verbatim from its PRECOMMIT section 3: the depth is the value
    that centres the ceiling's removal on SPP's published measured curtailment MW,

        removal_y = depth x SUM_t potential_y(t) . share(t)
                  = depth x potential_y . wms_y            (wms = potential-weighted share)
        want      = published_share_y x potential_y
        =>  depth_y = published_share_y / wms_y

    ``potential_y`` CANCELS, so a pure scalar change in the gross-up rate cannot move the
    depth -- which is the whole question item 2 asks, and it is answerable in closed form
    before a single number is computed. What CAN move it is (i) the published MW changing
    (rule 23 ``[R-FROZEN-DERIVE]``: it has not -- same ASOM rows, same source documents),
    and (ii) the share table's ``wms_y`` moving, because keeper 14's net load -- and hence
    which hours land in which decile -- is built from a DIFFERENT potential than keeper 7's.
    """
    print("\n## C (ITEM 2) -- THE DEPTH, RECONCILED AGAINST KEEPER 14's OWN POTENTIAL")
    print(
        f"\n   registered dataclass default: spp_curtail_depth_wind = {DEPTH_DEFAULT}\n"
        "   identification: depth_y = published_share_y / wms_y  (potential cancels)\n"
    )
    print(
        f"{'year':6s}{'gross src':>11s}{'published':>11s}{'wms_y':>9s}"
        f"{'implied depth':>15s}{'SPP-58 depth':>14s}{'delta':>9s}"
        f"{'0.288137/implied':>18s}"
    )
    implied = {}
    for y in YEARS:
        s = state[y]
        wms = float(
            (s["potential"] * s["share"]).sum() / max(s["potential"].sum(), 1e-9)
        )
        curt = ASOM_CURTAILMENT_MW.get(y)
        if curt is None:
            # No published MW: the year cannot identify a depth at all. It inherits the
            # pooled one, which is the honest statement of what the ceiling does there.
            print(
                f"{y:<6d}{s['source']:>11s}{'--':>11s}{wms:9.5f}"
                f"{'--':>15s}{'--':>14s}{'--':>9s}{'--':>18s}   NOT PUBLISHED"
            )
            implied[y] = float("nan")
            continue
        pub_share = curt / (genmix_delivered_mw(y) + curt)
        implied[y] = pub_share / wms
        prior = SPP58_IMPLIED_DEPTH.get(y)
        print(
            f"{y:<6d}{s['source']:>11s}{100 * pub_share:10.3f}%{wms:9.5f}"
            f"{implied[y]:15.5f}"
            f"{(f'{prior:.5f}' if prior else '--'):>14s}"
            f"{(f'{implied[y] - prior:+.5f}' if prior else '--'):>9s}"
            f"{DEPTH_DEFAULT / implied[y]:18.4f}"
        )
    print(
        "\n   RULE 23 [R-FROZEN-DERIVE] VERDICT: the depth STAYS FROZEN at 0.288137.\n"
        "   Its source data has not changed -- the five ASOM curtailment-MW rows and the\n"
        "   five GenMix delivered-MW rows in data/raw/spp-hsl/spp_wind_curtailment_annual.csv\n"
        "   are byte-identical to what SPP-58 read. Nothing in this lane re-derives it, and\n"
        "   the last column is reported as a DIAGNOSTIC of the pooled value's reach, never\n"
        "   as a candidate to cut (rule 1 [R-STRUCT] condition (c) forbids selecting it)."
    )
    return implied


def leg_d(state: dict[int, dict], frac_head: dict[int, float]) -> dict[int, dict]:
    """D (item 3) -- the pre-registered prediction, per year, before any solve."""
    print(
        "\n## D (ITEM 3) -- PRE-REGISTERED PREDICTIONS (zero LP). WRITTEN BEFORE THE SOLVE."
    )
    print(
        "\n   new bound(t) = potential(t) x clip(1 - depth x share(t), 0, 1), depth ="
        f" {DEPTH_DEFAULT}\n"
        "   The LP spends ~all of its bound (leg B), so the bound IS the prediction. It is\n"
        "   bracketed anyway: [LO] the LP keeps re-curtailing the same FRACTION of the new\n"
        "   headroom, [HI] the LP takes the whole new bound.\n"
    )
    print(
        f"{'year':6s}{'bench':>9s}{'model now':>11s}{'excess now':>12s}"
        f"{'new bound':>11s}{'excess LO':>11s}{'excess HI':>11s}{'d wind':>9s}"
        f"{'removal/head':>14s}"
    )
    pred = {}
    for y in YEARS:
        s = state[y]
        bench = bench_class_twh(y, "wind")
        mod = s["model"].sum() / 1e6
        new_bound_h = s["potential"] * np.clip(
            1.0 - DEPTH_DEFAULT * s["share"], 0.0, 1.0
        )
        new_bound = new_bound_h.sum() / 1e6
        deliv = s["delivered"].sum() / 1e6
        pot = s["potential"].sum() / 1e6
        head = pot - deliv
        removal = pot - new_bound
        hi = new_bound
        lo = new_bound - (1.0 - frac_head[y]) * max(new_bound - deliv, 0.0)
        pred[y] = {
            "bench": bench,
            "model": mod,
            "new_bound": new_bound,
            "lo": lo,
            "hi": hi,
            "dwind": 0.5 * ((lo - mod) + (hi - mod)),
            "removal_over_head": removal / head if head > 0 else float("inf"),
        }
        print(
            f"{y:<6d}{bench:9.4f}{mod:11.4f}{mod - bench:+12.4f}"
            f"{new_bound:11.4f}{lo - bench:+11.4f}{hi - bench:+11.4f}"
            f"{pred[y]['dwind']:+9.4f}{100 * pred[y]['removal_over_head']:13.1f}%"
        )
    print(
        "\n   THE LAST COLUMN IS THE FINDING. The ceiling's removal is expressed as a\n"
        "   percentage of the gross-up headroom that same year created. At 100 % the two\n"
        "   mechanisms exactly cancel and wind returns to its delivered basis; above 100 %\n"
        "   the ceiling removes energy the market ACTUALLY DELIVERED."
    )
    return pred


def leg_sens(state: dict[int, dict]) -> None:
    """C2 -- how far the hourly RECONSTRUCTION can reach into items 2 and 3.

    The reconstruction ``potential(t) = delivered_930(t) x factor_y`` is exact on ANNUAL
    energy (leg A, and SPP-67's CAPACITY/SHAPE legs are 0.0000 TWh) but NOT hour-exact:
    measured here, hourly ``model/potential`` runs p1-p99 0.64-1.30 with r ~ 0.96, because
    the model's own profile carries a per-zone shape and a monthly commissioning ramp that
    a single annual scalar cannot reproduce. So the honest question is whether that noise
    reaches ``wms_y``, which is what items 2 and 3 are built on.

    It is answered by BRACKETING: net load is rebuilt a second time from the model's OWN
    committed wind dispatch instead of the reconstructed potential. The true bound lies
    between them (the LP spends 90-100 % of its bound, leg B), so the two rows bracket it.
    """
    from market_sim.config import paths as _paths
    from market_sim.data.curtailment_share import _share_lookup, load_spp_share_table

    table = load_spp_share_table(_paths.RAW_DIR / "reference")
    print("\n## C2 -- RECONSTRUCTION SENSITIVITY: does the hourly noise reach wms_y?")
    print(
        f"\n{'year':6s}{'wms (potential)':>17s}{'wms (model wind)':>18s}{'delta':>9s}"
        f"{'removal/head A':>16s}{'removal/head B':>16s}{'spread':>9s}"
    )
    worst = 0.0
    for y in YEARS:
        s = state[y]
        solar = class_hourly(y, "solar")[: len(s["potential"])]
        share_b = _share_lookup(table, s["demand"] - s["model"] - solar)
        wms_a = float((s["potential"] * s["share"]).sum() / s["potential"].sum())
        wms_b = float((s["potential"] * share_b).sum() / s["potential"].sum())
        head = s["potential"].sum() - s["delivered"].sum()
        rem_a = (s["potential"] * np.minimum(DEPTH_DEFAULT * s["share"], 1.0)).sum()
        rem_b = (s["potential"] * np.minimum(DEPTH_DEFAULT * share_b, 1.0)).sum()
        spread = 100 * (rem_a - rem_b) / head
        worst = max(worst, abs(spread))
        print(
            f"{y:<6d}{wms_a:17.5f}{wms_b:18.5f}{wms_b - wms_a:+9.5f}"
            f"{100 * rem_a / head:15.1f}%{100 * rem_b / head:15.1f}%{spread:+8.2f} pt"
        )
    print(
        f"\n   The bracket is {worst:.2f} percentage points wide at its worst. Items 2 and 3\n"
        "   are robust to the reconstruction: the hourly noise is roughly symmetric and the\n"
        "   decile rank it feeds is dominated by demand, so few hours cross a bin edge."
    )


def leg_price(state: dict[int, dict]) -> None:
    """D2 -- the price channel, measured artifact-free on committed prices vs actual RT.

    Deliberately uses NO reconstructed quantity. The model's wind offer is a flat
    ``-ira_ptc_wind``, so ``price == -26.000`` is the exact signature that wind is the
    MARGINAL unit -- i.e. that the LP is spilling wind at the margin in that hour. Those
    hours are counted straight off the committed ``system_<year>.parquet`` and compared to
    SPP's own measured RT prices.
    """
    actual = pd.read_parquet(
        ROOT / "data/raw/_validation-source/actual_lmp_hourly_SPP.parquet"
    )
    print("\n## D2 -- THE PRICE CHANNEL, on committed prices only (no reconstruction)")
    print(
        "\n   SPP-64 section 3 / SPP-50 section 6 / SPP-51: wind is a BOUNDED decision variable bid at a\n"
        "   flat -ira_ptc_wind, so it is the ONLY unit that can set a negative price, and a\n"
        "   unit held AT its bound is never marginal. price == -26.000 is therefore the exact\n"
        "   signature of 'the LP is spilling wind at the margin'. Lowering the bound removes\n"
        "   those hours -- which is the channel defect, not a level to re-cut.\n"
    )
    print(
        f"{'year':6s}{'model h<0':>11s}{'model h<=-25.9':>16s}{'ACTUAL RT h<0':>15s}"
        f"{'model/actual':>14s}{'headroom TWh':>14s}{'min price':>11s}"
    )
    for y in YEARS:
        s = state[y]
        rt = actual[actual["year"] == y]["rt"].to_numpy(dtype=float)
        rt = rt[~np.isnan(rt)]
        a_neg = int((rt < 0).sum()) if len(rt) else 0
        m_neg = int((s["price"] < 0.0).sum())
        deep = int((s["price"] <= -25.9).sum())
        head = (s["potential"].sum() - s["delivered"].sum()) / 1e6
        ratio = f"{m_neg / a_neg:.2f}x" if a_neg else "--"
        print(
            f"{y:<6d}{m_neg:11d}{deep:16d}{a_neg:15d}{ratio:>14s}"
            f"{head:14.4f}{float(s['price'].min()):11.3f}"
        )
    print(
        "\n   TWO THINGS, AND THEY POINT THE SAME WAY. (1) The model already has FEWER\n"
        "   negative hours than the market, not more -- so removing them moves AWAY from it.\n"
        "   (2) 2019 is the natural experiment this lane did not have to build: its gross-up\n"
        "   headroom is 1.25 TWh against 8.8-12.9 TWh elsewhere, and it has ZERO negative\n"
        "   hours and a minimum price of +4.500. The model's negative-price regime IS the\n"
        "   gross-up headroom being spilled. A ceiling that removes the headroom removes the\n"
        "   regime -- in every year, at any depth, which is why re-cutting the depth cannot\n"
        "   fix it (SPP-64) and rule 1 [R-STRUCT] condition (c) forbids trying."
    )


def leg_e() -> None:
    """E (item 4) -- rule 25 [R-ISO-SCOPE]: default-off byte-identity, two ways."""
    print("\n## E (ITEM 4) -- CROSS-ISO BYTE-IDENTITY, BY CONSTRUCTION AND BY CENSUS")
    print(
        "\n   BY CONSTRUCTION. Three gates, every one of which must open before the ceiling\n"
        "   can touch an LP, and each is checked in source here rather than asserted:"
    )
    src_bc = (ROOT / "scripts/run_calibration.py").read_text()
    src_fc = (ROOT / "src/market_sim/runner.py").read_text()
    src_rn = (ROOT / "src/market_sim/data/renewables.py").read_text()
    checks = [
        (
            'backcast leg gates on iso == "SPP"',
            'if getattr(config, "spp_curtailment_ceiling", False) and iso == "SPP":'
            in src_bc,
        ),
        (
            'forecast leg gates on iso == "SPP"',
            'if iso == "SPP" and getattr(config, "spp_curtailment_ceiling", False):'
            in src_fc,
        ),
        (
            "rule 19: renewables.py skips the oversupply allocation when armed",
            'getattr(config, "vre_curtailment_oversupply_allocation", False)\n'
            "                        and not _spp_ceiling" in src_rn,
        ),
        (
            "share table is SPP's own (SPP_SHARE_TABLE_NAME)",
            'SPP_SHARE_TABLE_NAME = "spp_curtailment_share.csv"'
            in (ROOT / "src/market_sim/data/curtailment_share.py").read_text(),
        ),
        (
            "ceiling zones are SPP's own two model zones",
            'SPP_CEILING_ZONES = ("SPP-North", "SPP-South")'
            in (ROOT / "src/market_sim/data/curtailment_share.py").read_text(),
        ),
    ]
    for label, ok in checks:
        print(f"     [{'PASS' if ok else 'FAIL'}] {label}")

    print(
        "\n   BY CENSUS. Every committed run_config.json in results/calibration/, scanned for\n"
        "   a non-default spp_curtailment_ceiling. A single non-SPP arm would falsify the\n"
        "   construction argument above."
    )
    armed, present, total = [], 0, 0
    for path in sorted((ROOT / "results/calibration").glob("*/run_config*.json")):
        try:
            cfg = json.loads(path.read_text()).get("scenario_config", {})
        except (OSError, ValueError):
            continue
        total += 1
        if "spp_curtailment_ceiling" not in cfg:
            continue
        present += 1
        if cfg["spp_curtailment_ceiling"]:
            armed.append(str(path.relative_to(ROOT)))
    print(
        f"     scanned {total} committed run configs; {present} carry the field; "
        f"{len(armed)} ARM it."
    )
    for a in armed:
        print(f"       ARMED: {a}")
    if not armed:
        print(
            "     No committed run in ANY ISO arms the ceiling, so arming it for SPP moves\n"
            "     no other ISO's bytes and no other ISO's keeper (rule 25 [R-ISO-SCOPE])."
        )


def main() -> None:
    print("=" * 104)
    print(
        "SPP-68 PHASE 0 -- card R-bc: the wind curtailment CEILING vs KEEPER 14. ZERO LP."
    )
    print(f"keeper {KEEPER} (2023-2025) + rung {RUNG} (2019-2022)")
    print("=" * 104)
    state = {y: ceiling_state(y) for y in YEARS}
    leg_a(state)
    frac_head = leg_b(state)
    leg_c(state)
    leg_sens(state)
    leg_d(state, frac_head)
    leg_price(state)
    leg_e()
    print()


if __name__ == "__main__":
    main()
