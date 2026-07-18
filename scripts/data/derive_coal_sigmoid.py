"""Derive the per-(ISO, supply) coal-vs-gas passthrough sigmoid from measured
coal-commodity price data — the region f.o.b.-mine price (EIA Annual Coal
Report) and coal-mining PPI (BLS) intaked in #1803.

WHY THIS SCRIPT EXISTS (CLAUDE.md rule 23 — freeze against residuals): the
gas-keyed coal passthrough sigmoid (``COAL_SIGMOID_DEFAULTS`` in
``config/scenarios.py``) was hand-tuned per (ISO, supply) with no coal
commodity price behind it, and MISO's ``gas_mid``/``gas_slope`` were literal
byte-copies of ERCOT's (issue #1347 / gap G-26; rule-24 wart — a fit must not
cross ISO boundaries). The #1803 intake added the region f.o.b. + PPI series
that a real re-derivation needs (data/raw/coal-prices/,
docs/handoffs/coal-price-data-intake-2026-07.md). A source-data update is the
ONLY admissible re-derivation trigger, so this re-derive is keyed to that
intake, not to any moved residual (CLAUDE.md rules 10/11/23).

THE MECHANISM (kept, only its numbers re-grounded — G-26 disposition R6
DOCUMENT-AND-KEEP): a take-or-pay / mine-mouth / rail coal contract makes a
plant's delivered fuel cost mostly fixed and NOT gas-indexed, so its above-
must-run tranche should bid toward its OWN delivered cost, discounting only
enough to hold merit order against cheap gas-CC — never chasing the gas index
up past full cost. The passthrough multiplies the coal fuel term and is a
logistic in the monthly delivered gas price::

    passthrough(gas) = floor + (ceil - floor) / (1 + exp(-slope * (gas - gas_mid)))

This script grounds each of the four parameters in the measured coal price:

  gas_mid  — the coal-vs-gas-CC MERIT CROSSOVER in gas-price space: the gas
             $/MMBtu at which a gas-CC's fuel cost equals the coal plant's
             delivered fuel cost, ``deliv$/MMBtu * COAL_HR / CC_HR``. The
             region f.o.b. price (lifted to delivered by the delivery-mode
             commodity share) sets where the crossover sits — cheap PRB
             crosses at low gas, dear Appalachian bituminous at high gas. This
             is the parameter the ERCOT byte-copy got wrong for MISO.
  ceil     — 1.0 for every supply: coal's delivered cost does not follow the
             gas index (mine-mouth/rail commodity), so at dear gas the bid is
             its full measured delivered cost, never a markup past it (rule-10
             cost-tracking; retires the inconsistent ceil>1.0 opportunity-cost
             story the D-8 audit flagged).
  floor    — the deepest cheap-gas discount: the fraction that pulls coal to
             merit-order parity with the CHEAPEST gas it competes against,
             ``gas_min / gas_mid`` (clipped to [FLOOR_MIN, ceil]). gas_min is
             the observed backcast-window gas trough — a market fact, not a
             residual.
  gas_slope — the crossover sharpness: 1 / (crossover dispersion in gas
             space), where the dispersion is the capacity-weighted spread of
             delivered coal cost ACROSS the supply group's producing regions
             (real, e.g. MISO bituminous spanning IL/IN/KY/ENC) combined with
             the PPI intra-year variability. A single-region group (MISO's
             all-PRB) resolves no cross-region spread, so it falls back to the
             documented baseline slope (COAL_SIGMOID_BASELINE_SLOPE).

Every number traces to: region f.o.b. (EIA ACR), PPI CV (BLS), coal heat
content (EIA MER A5), representative/fleet heat rates (EIA Table 8), the
delivery-mode commodity share (EIA coal transportation), the observed gas
trough (EIA-923), and the model's per-plant fleet capacities — NONE to any
ISO price/volume residual (the honesty gate).

GRANULARITY CAVEAT: the f.o.b. is annual (latest ACR = 2024; 2025 has no ACR
yet, PPI-proxied) and region-level, so it resolves the LEVEL of the crossover
but not daily basin-spot movement (S&P/Argus-paywalled). If the re-derived
MISO sigmoid does not move the coal-vs-gas residual, the residual is genuinely
daily-basin-spot-gapped, not something to force (do not tune to it).

OUTPUT: prints a per-(ISO, supply) table and writes a provenance artifact
``data/raw/_processed-legacy/coal_sigmoid_params.csv`` (all ISOs, for the
record). The MISO rows are transcribed into ``COAL_SIGMOID_DEFAULTS`` as the
registry-resident literals (rule 24); other ISOs' rows are delivered but their
live literals are left unchanged (their re-solves are separate owner lanes).

Usage:
    python scripts/data/derive_coal_sigmoid.py                 # all ISOs
    python scripts/data/derive_coal_sigmoid.py --iso MISO
"""

from __future__ import annotations

import argparse
import glob
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import (  # noqa: E402
    COAL_DELIVERY_COMMODITY_SHARE,
    COAL_HEAT_CONTENT_MMBTU_PER_TON,
    COAL_SIGMOID_BACKCAST_GAS_MIN_MMBTU,
    COAL_SIGMOID_BASELINE_SLOPE,
    COAL_SIGMOID_FLOOR_MIN,
    COAL_SIGMOID_FOLLOWER_DISCOUNT,
    COAL_SIGMOID_REP_HR_COAL,
    COAL_SIGMOID_REP_HR_GAS_CC,
    COAL_SIGMOID_SLOPE_MAX,
    COAL_SIGMOID_SLOPE_MIN,
)
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import COAL_PRICES_DIR, PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("derive_coal_sigmoid")

# Latest ACR annual f.o.b. vintages to average for the delivered-cost level
# (the two most recent published years; 2025 has no ACR yet — PPI-proxied, so
# it is not used for the level). Re-derivation extends this window when the
# ACR-2025 vintage lands (~Oct 2026), not before (rule 23).
_FOB_YEARS: tuple[int, ...] = (2023, 2024)

# The coal supply tags that carry a passthrough sigmoid, mapped to the ACR rank
# whose f.o.b. price sets their commodity cost. "waste" reclamation coal is not
# an ACR-priced commodity (no region), so it is omitted here (its sigmoid, when
# on, keeps its measured near-free floor separately).
_SUPPLY_TO_RANK: dict[str, str] = {
    "prb": "SUB",
    "subbituminous": "SUB",
    "bituminous": "BIT",
    "lignite": "LIG",
}


def _rank_price_table() -> pd.DataFrame:
    """Return the concatenated EIA ACR price-by-rank table (region x rank x year)."""
    parts = sorted(glob.glob(str(COAL_PRICES_DIR / "eia_coal_price_by_rank.part*.csv")))
    if not parts:
        raise SystemExit(
            f"no eia_coal_price_by_rank.part*.csv under {COAL_PRICES_DIR} — run "
            "scripts/data/fetch_eia_coal_prices.py (the #1803 intake)."
        )
    df = pd.concat([pd.read_csv(p) for p in parts], ignore_index=True)
    df["region_id"] = df["region_id"].astype(str)
    df["coal_rank_id"] = df["coal_rank_id"].astype(str)
    return df


def _ppi_intra_year_cv() -> float:
    """Return the coal-mining PPI intra-year coefficient of variation.

    The mean over the f.o.b. window of each year's (std / mean) of the monthly
    PPI level — how much coal's OWN price wobbles within a year. A small CV
    (~2%) confirms coal cost is intra-year-stable, so it only lightly fuzzes
    the merit-crossover dispersion. Averages the two published PPI series
    (WPU051 commodity, PCU2121 industry).
    """
    ppi = pd.read_csv(COAL_PRICES_DIR / "bls_coal_ppi.csv")
    ppi = ppi[ppi["year"].isin(_FOB_YEARS)]
    if ppi.empty:
        return 0.0
    cvs = ppi.groupby(["series_id", "year"])["index_value"].agg(
        lambda s: float(s.std(ddof=0) / s.mean()) if s.mean() else 0.0
    )
    return float(cvs.mean())


def _fob_mmbtu(rank_df: pd.DataFrame, region_id: str, rank: str) -> float | None:
    """Return a region+rank's f.o.b.-mine price in $/MMBtu, averaged over the
    ACR window, or None when the region publishes no such rank."""
    hc = COAL_HEAT_CONTENT_MMBTU_PER_TON.get(rank)
    if hc is None:
        return None
    sub = rank_df[
        (rank_df["region_id"] == region_id)
        & (rank_df["coal_rank_id"] == rank)
        & (rank_df["year"].isin(_FOB_YEARS))
    ]
    if sub.empty:
        # Fall back to the region's TOT (all-rank) price, then to the national
        # rank price — coarser, logged, so a region missing the exact rank
        # (e.g. a bituminous plant sited in a lignite-only ACR region) is still
        # priced from real data rather than dropped.
        sub = rank_df[
            (rank_df["region_id"] == region_id)
            & (rank_df["coal_rank_id"] == "TOT")
            & (rank_df["year"].isin(_FOB_YEARS))
        ]
    if sub.empty:
        sub = rank_df[
            (rank_df["region_id"] == "US")
            & (rank_df["coal_rank_id"] == rank)
            & (rank_df["year"].isin(_FOB_YEARS))
        ]
    if sub.empty:
        return None
    return float(sub["price_usd_per_ton"].mean()) / hc


def _plant_regions(iso: str) -> pd.DataFrame:
    """Return ``[plant_code, region_id, coal_supply_class]`` for ``iso`` from the
    #1803 coal-region crosswalk (data/raw/reference/coal_region_crosswalk.csv)."""
    cw = pd.read_csv(RAW_DIR / "reference" / "coal_region_crosswalk.csv")
    cw = cw[cw["iso"].astype(str).str.upper() == iso.upper()].copy()
    cw["plant_code"] = pd.to_numeric(cw["plant_code"], errors="coerce")
    cw = cw.dropna(subset=["plant_code"])
    cw["plant_code"] = cw["plant_code"].astype(int)
    return cw[["plant_code", "region_id", "coal_supply_class"]]


def _plant_capacity_hr(iso: str) -> pd.DataFrame:
    """Return ``[plant_code, pmax_mw, heat_rate]`` per coal plant for ``iso``.

    Capacity is summed across the plant's per-plant CAMPD bin tranches; the
    heat rate is the capacity-weighted mean of its coal bins. Used to
    capacity-weight the region f.o.b. blend and to place the merit crossover at
    the fleet's own coal heat rate rather than a flat representative.
    """
    gens = [
        g
        for g in load_fleet_from_csv(iso, get_iso_config(iso))
        if g.fuel_type == "coal" and int(g.plant_code) > 0 and (g.pmax_mw or 0) > 0
    ]
    rows: dict[int, list[tuple[float, float]]] = {}
    for g in gens:
        rows.setdefault(int(g.plant_code), []).append(
            (float(g.pmax_mw), float(g.heat_rate or COAL_SIGMOID_REP_HR_COAL))
        )
    out = []
    for code, pairs in rows.items():
        cap = sum(p for p, _ in pairs)
        hr = sum(p * h for p, h in pairs) / cap if cap else COAL_SIGMOID_REP_HR_COAL
        out.append({"plant_code": code, "pmax_mw": cap, "heat_rate": hr})
    return pd.DataFrame(out)


def _sigmoid_supply(coal_supply_class: str) -> str | None:
    """Map a crosswalk ``coal_supply_class`` to its sigmoid supply key."""
    key = str(coal_supply_class).strip().lower()
    return key if key in _SUPPLY_TO_RANK else None


def _derive_iso(iso: str, rank_df: pd.DataFrame, ppi_cv: float) -> list[dict]:
    """Return the derived sigmoid parameter rows for one ISO's coal supplies."""
    regions = _plant_regions(iso)
    if regions.empty:
        logger.info("%s: no coal plants in the crosswalk — skipping", iso)
        return []
    cap = _plant_capacity_hr(iso)
    regions = regions.merge(cap, on="plant_code", how="left")
    # Plants absent from the operable fleet (mid-window retirees) carry no
    # capacity; weight them at the group's mean so they neither vanish nor
    # dominate.
    regions["region_id"] = regions["region_id"].astype(str)

    gas_min = COAL_SIGMOID_BACKCAST_GAS_MIN_MMBTU.get(iso.upper())
    rows: list[dict] = []
    for supply, rank in _SUPPLY_TO_RANK.items():
        grp = regions[regions["coal_supply_class"].map(_sigmoid_supply) == supply]
        if grp.empty:
            continue
        # Per-plant delivered $/MMBtu = region f.o.b. / delivery-mode commodity
        # share. Plants whose region publishes no price are dropped from the
        # blend (logged via n_priced).
        commodity_share = COAL_DELIVERY_COMMODITY_SHARE[supply]
        deliv, weights, hrs = [], [], []
        w_default = (
            float(grp["pmax_mw"].mean()) if grp["pmax_mw"].notna().any() else 1.0
        )
        for _, r in grp.iterrows():
            fob = _fob_mmbtu(rank_df, r["region_id"], rank)
            if fob is None:
                continue
            deliv.append(fob / commodity_share)
            w = float(r["pmax_mw"]) if pd.notna(r["pmax_mw"]) else w_default
            weights.append(max(w, 0.0))
            hrs.append(
                float(r["heat_rate"])
                if pd.notna(r["heat_rate"])
                else COAL_SIGMOID_REP_HR_COAL
            )
        if not deliv:
            logger.warning("%s %s: no region-priced plants — skipped", iso, supply)
            continue
        deliv = np.asarray(deliv, dtype=float)
        weights = np.asarray(weights, dtype=float)
        weights = weights / weights.sum() if weights.sum() > 0 else None
        hrs = np.asarray(hrs, dtype=float)

        deliv_mean = float(np.average(deliv, weights=weights))
        hr_coal = float(np.average(hrs, weights=weights))
        # Merit crossover in gas space (coal fuel cost == gas-CC fuel cost).
        gas_mid = deliv_mean * hr_coal / COAL_SIGMOID_REP_HR_GAS_CC
        ceil = 1.0  # cost-tracking: bid never exceeds full measured delivered cost.
        floor = float(np.clip(gas_min / gas_mid, COAL_SIGMOID_FLOOR_MIN, ceil))

        # Crossover dispersion in gas space: capacity-weighted std of the
        # per-plant delivered cost (the real ACROSS-REGION spread — e.g. MISO
        # bituminous spanning IL/IN/KY/ENC) combined with the small PPI
        # intra-year wobble that fuzzes it, translated to gas via the HR ratio;
        # slope = 1 / dispersion. A single-region group (e.g. MISO's all-PRB)
        # resolves NO cross-region spread — the annual region f.o.b. is one
        # number, so the PPI wobble alone must not manufacture a slope — it
        # falls back to the documented baseline (rule-23 caveat: the coarse
        # annual data can't resolve this group's crossover sharpness).
        n_regions = int(grp["region_id"].nunique())
        var_cross = float(np.average((deliv - deliv_mean) ** 2, weights=weights))
        var_ppi = (ppi_cv * deliv_mean) ** 2
        sigma_gas = np.sqrt(var_cross + var_ppi) * hr_coal / COAL_SIGMOID_REP_HR_GAS_CC
        if n_regions > 1 and sigma_gas > 1e-6:
            slope = float(
                np.clip(1.0 / sigma_gas, COAL_SIGMOID_SLOPE_MIN, COAL_SIGMOID_SLOPE_MAX)
            )
        else:
            slope = COAL_SIGMOID_BASELINE_SLOPE

        rows.append(
            {
                "iso": iso.upper(),
                "supply": supply,
                "n_plants": int(len(grp)),
                "n_priced": int(len(deliv)),
                "fob_mmbtu": round(
                    float(np.average(deliv * commodity_share, weights=weights)), 3
                ),
                "deliv_mmbtu": round(deliv_mean, 3),
                "hr_coal": round(hr_coal, 2),
                "floor": round(floor, 3),
                "ceil": round(ceil, 3),
                "gas_mid": round(gas_mid, 3),
                "gas_slope": round(slope, 3),
                "regions": ",".join(sorted(grp["region_id"].unique())),
            }
        )
        # PRB baseload also spawns the low-must-run follower tier (deeper cheap-
        # gas discount; same basin crossover).
        if supply == "prb":
            f_floor = float(
                np.clip(
                    floor * COAL_SIGMOID_FOLLOWER_DISCOUNT,
                    COAL_SIGMOID_FLOOR_MIN,
                    ceil,
                )
            )
            rows.append(
                {
                    "iso": iso.upper(),
                    "supply": "prb_follower",
                    "n_plants": int(len(grp)),
                    "n_priced": int(len(deliv)),
                    "fob_mmbtu": rows[-1]["fob_mmbtu"],
                    "deliv_mmbtu": round(deliv_mean, 3),
                    "hr_coal": round(hr_coal, 2),
                    "floor": round(f_floor, 3),
                    "ceil": round(ceil, 3),
                    "gas_mid": round(gas_mid, 3),
                    "gas_slope": round(slope, 3),
                    "regions": ",".join(sorted(grp["region_id"].unique())),
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Derive per-(ISO, supply) coal passthrough sigmoid from #1803 "
        "region f.o.b. + PPI coal-price data."
    )
    parser.add_argument(
        "--iso",
        nargs="*",
        default=None,
        help="ISOs to derive (default: every ISO with coal plants in the crosswalk).",
    )
    parser.add_argument(
        "--out",
        default=str(PROCESSED_DIR / "coal_sigmoid_params.csv"),
        help="Provenance artifact path.",
    )
    args = parser.parse_args()

    rank_df = _rank_price_table()
    ppi_cv = _ppi_intra_year_cv()
    logger.info("PPI intra-year CV over %s: %.4f", _FOB_YEARS, ppi_cv)

    cw = pd.read_csv(RAW_DIR / "reference" / "coal_region_crosswalk.csv")
    isos = args.iso or sorted(cw["iso"].astype(str).str.upper().unique())

    all_rows: list[dict] = []
    for iso in isos:
        all_rows.extend(_derive_iso(iso, rank_df, ppi_cv))

    if not all_rows:
        logger.warning("no rows derived")
        return
    table = pd.DataFrame(all_rows)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_path, index=False)

    logger.info("wrote %s (%d rows)", out_path, len(table))
    with pd.option_context("display.width", 160, "display.max_columns", None):
        print(
            table[
                [
                    "iso",
                    "supply",
                    "n_priced",
                    "fob_mmbtu",
                    "deliv_mmbtu",
                    "hr_coal",
                    "floor",
                    "ceil",
                    "gas_mid",
                    "gas_slope",
                    "regions",
                ]
            ].to_string(index=False)
        )
    print("\nCOAL_SIGMOID_DEFAULTS literals (paste MISO rows into scenarios.py):")
    for _, r in table.iterrows():
        print(
            f'    ("{r.iso}", "{r.supply}"): '
            f'{{"floor": {r.floor}, "ceil": {r.ceil}, '
            f'"gas_mid": {r.gas_mid}, "gas_slope": {r.gas_slope}}},'
        )


if __name__ == "__main__":
    main()
