"""Derive per-backcast-year neighbor marginal heat rates from measured LMP.

The reference-price interface (``market_sim.data.neighbor_price``) prices each
seam as ``(henry_hub + gas_basis) x marginal_heat_rate x load_shape``. The
registry carries ONE ``marginal_heat_rate`` per neighbor — a 3-year *mean* of
the neighbor's realized LMP / delivered-gas ratio. Because the real ratio drifts
year to year (MISO 12.5 / 14.1 / 12.2 for 2023-25), the single mean over-prices
the neighbor in the dear-gas year and under-prices it in the cheap-gas year,
opening (closing) a fake export spread on the seam — the root of the PJM 2025
over-export / 2024 under-export.

This script re-anchors the heat rate PER YEAR to the neighbor's OWN measured
annual-mean realized LMP so the constructed seam reference reproduces the
neighbor's realized annual mean each backcast year:

    HR[year] = measured_mean_LMP[year]
               / ((henry_hub[year] + gas_basis) x K[year])

where ``K[year] = mean(load_shape ** exponent)`` is the convexity inflation of
the load-shape multiplier (so the constructed ANNUAL MEAN, not just the
baseload, equals the measured mean). This is a measured neighbor price-formation
input (claude.md rule #12 — measured over estimate; the forward analogue is the
structural ``marginal_heat_rate``, used whenever a year has no measured LMP), it
is NOT tuned to the ISO's net interchange (rule #11) — it never sees the flow.

THE ANCHOR MAP IS PER ISO (lane SPP-51, 2026-09-07, repairing FINDING-spp-33
§2 / §6 R1). It used to be keyed by neighbour NAME alone, globally, which (a)
sent SPP's ``MISO`` seam to the MISO *system* file where the registration
anchors on the West/South zonal rows, and (b) silently ``continue``-d past any
neighbour with no key (SPP's ``AECI`` / ``ERCOT``), printing one wrong-anchor
row and no diagnostic. Now each ISO names, per neighbour, the committed
realized-LMP product and an optional zone filter, exactly as its ``spec.py``
block documents; a neighbour with no anchor (no organized market — PJM's
Carolinas/TVA/LGEE) is PRINTED as such rather than skipped, an ISO with no map
FAILS, and a declared anchor whose file or rows are absent FAILS instead of
being dropped.

A SECOND ANCHOR KIND (lane soco-98, 2026-10-01, repairing FINDING-soco-33 §7
R-2). SOCO's neighbours (TVA, the Carolinas utilities, the Florida BAs) run no
organized market, so no ``actual_lmp`` product exists for them. Each files its
own hourly SYSTEM LAMBDA on FERC Form 714 Part II Sch. 6 — the marginal cost of
its own dispatch, the vertically integrated counterpart of an LMP. An anchor of
kind ``ferc714_lambda`` reads that committed extract
(:func:`market_sim.data.ferc714.load_ferc714_system_lambda`) and takes ONLY its
annual mean; filed zeros are dropped as filing gaps (``data/raw/ferc-714``
README). Rule 13 [R-MEASURED]: the hourly lambda is a measured outcome and is
never a seam price; the annual-mean anchor of ``(HH + basis) x HR x shape`` is
the admissible use, exactly as for an LMP anchor. Run::

    python scripts/data/derive_neighbor_hr_by_year.py --iso PJM

and paste the emitted block into the ISO's ``INTERFACE_NEIGHBORS`` entry.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd

from market_sim.config import paths
from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
from market_sim.data.neighbor_price import neighbor_gas_price, neighbor_load_shape


@dataclass(frozen=True)
class Anchor:
    """One neighbour's measured price anchor.

    Attributes:
        product: The ``actual_lmp_hourly_<product>.parquet`` stem under
            ``paths.CALIBRATION_DIR`` (an ISO code, or ``zonal_<ISO>`` for a
            zonal product).
        zones: For a zonal product, the ``zone`` values to average; ``None``
            takes the whole file (a system product). A multi-zone anchor is
            averaged PER ZONE and then over zones — one price per zone, never a
            hub census (FINDING-spp-33 §2).
        proxy: A declared proxy (the anchor is not the neighbour's own price).
        kind: ``"lmp"`` (``product`` names an ``actual_lmp`` parquet) or
            ``"ferc714_lambda"`` (``product`` is the EIA-930 BA code of a
            :data:`~market_sim.data.ferc714.SOCO_NEIGHBOR_LAMBDA_RESPONDENTS`
            entry whose FERC 714 Sch. 6 system lambda anchors the seam).
    """

    product: str
    zones: tuple[str, ...] | None = None
    proxy: bool = False
    kind: str = "lmp"


# ISO -> neighbour name -> the measured anchor its registry block documents.
# A neighbour absent from its ISO's map (no organized-market LMP, e.g. PJM's
# Carolinas / TVA / LGEE) keeps the structural marginal_heat_rate and gets no
# year table; it is REPORTED, not silently skipped. An ISO absent here fails.
# Other ISOs' entries are the pre-2026-09-07 global map, unchanged (rule 25:
# each ISO's anchors are its own; PJM's "MISO" seam and SPP's "MISO_*" legs
# read different products because they are different physical seams).
NEIGHBOR_LMP_ANCHORS: dict[str, dict[str, Anchor]] = {
    "PJM": {
        "MISO": Anchor("MISO"),
        "NYISO": Anchor("NYISO"),
    },
    "MISO": {
        "PJM": Anchor("PJM"),
        "SPP": Anchor("SPP"),
    },
    # CAISO's corridor seams are anchored by their own per-hub derive
    # (scripts/data/derive_caiso_*); no realized-LMP product is registered here.
    "CAISO": {},
    # SPP (lane SPP-51): the anchors INTERFACE_NEIGHBORS["SPP"] documents block
    # by block — the two MISO legs on their own zonal rows, AECI on the SPP
    # system hub as a DECLARED PROXY (AECI publishes no LMP), ERCOT on its
    # system file.
    "SPP": {
        "MISO_West": Anchor("zonal_MISO", ("MISO-West",)),
        "MISO_South": Anchor("zonal_MISO", ("MISO-South",)),
        "AECI": Anchor("SPP", proxy=True),
        "ERCOT": Anchor("ERCOT"),
    },
    # SOCO (lane soco-98, FINDING-soco-33 §7 R-2 / FINDING-soco-97 §5 step 3).
    # SOCO_MISO reads MISO-South's own zonal LMP (the SPP-51 construction for
    # the same zone; rule 19, one physical seam). The five non-market seams
    # read the neighbour's OWN FERC 714 Sch. 6 system lambda. NOT anchored,
    # and reported as such: SOCO_SCEG (Dominion SC files 0.00 in every hour,
    # not shipped) and SOCO_FPL (its lambda runs ~40 % below its peers on an
    # unresolved basis, ferc-714 README "Flags"). JEA files a lambda but is
    # not a SOCO EIA-930 counterparty, so it has no block to anchor. SOCO's
    # own lambda never enters (G17: each anchor is the neighbour's price on
    # the neighbour's side of the seam). Rule 25: none of these is PJM's
    # ``TVA`` / ``Carolinas`` anchor.
    "SOCO": {
        "SOCO_MISO": Anchor("zonal_MISO", ("MISO-South",)),
        "SOCO_TVA": Anchor("TVA", kind="ferc714_lambda"),
        "SOCO_DUK": Anchor("DUK", kind="ferc714_lambda"),
        "SOCO_SC": Anchor("SC", kind="ferc714_lambda"),
        "SOCO_FPC": Anchor("FPC", kind="ferc714_lambda"),
        "SOCO_TAL": Anchor("TAL", kind="ferc714_lambda"),
    },
}

#: Anchor kinds :func:`_measured_mean_lmp` resolves.
ANCHOR_KINDS: frozenset[str] = frozenset({"lmp", "ferc714_lambda"})

_HOURS = 8760


def _measured_mean_lambda(ba_code: str, year: int) -> float | None:
    """Return a neighbour's annual-mean FERC 714 system lambda ($/MWh), or None.

    The rows of ``report_year == year`` (the filer's own year), filed zeros
    dropped as filing gaps (``data/raw/ferc-714`` README: Tallahassee's 79,
    TVA's one). ``None`` when the respondent is unregistered, the extract is
    absent or the year carries no non-zero row.
    """
    from market_sim.data.ferc714 import (
        SOCO_NEIGHBOR_LAMBDA_RESPONDENTS,
        load_ferc714_system_lambda,
    )

    respondent = SOCO_NEIGHBOR_LAMBDA_RESPONDENTS.get(ba_code)
    if respondent is None:
        return None
    try:
        df = load_ferc714_system_lambda(respondent.respondent_id)
    except FileNotFoundError:
        return None
    vals = df.loc[df["report_year"] == year, "system_lambda_usd_mwh"].to_numpy(
        dtype=float
    )
    vals = vals[np.isfinite(vals) & (vals != 0.0)]
    if vals.size == 0:
        return None
    return float(vals.mean())


def _measured_mean_lmp(anchor: Anchor, year: int, run: str = "rt") -> float | None:
    """Return the anchor's realized annual-mean price ($/MWh), or None if absent.

    A zonal anchor averages per zone and then equal-weight over the listed
    zones; a system anchor is the nan-mean of the file's rows for ``year``. A
    ``ferc714_lambda`` anchor is the neighbour's annual-mean system lambda
    (``run`` does not apply: Sch. 6 files one series).
    """
    if anchor.kind not in ANCHOR_KINDS:
        raise ValueError(f"unknown anchor kind {anchor.kind!r}")
    if anchor.kind == "ferc714_lambda":
        return _measured_mean_lambda(anchor.product, year)
    path = paths.CALIBRATION_DIR / f"actual_lmp_hourly_{anchor.product}.parquet"
    if not path.is_file():
        return None
    df = pd.read_parquet(path)
    rows = df[df["year"] == year]
    if rows.empty or run not in rows.columns:
        return None
    if anchor.zones is not None:
        rows = rows[rows["zone"].isin(anchor.zones)]
        if rows.empty:
            return None
        return float(rows.groupby("zone")[run].mean().mean())
    return float(np.nanmean(rows[run].to_numpy(dtype=float)))


def anchor_source(anchor: Anchor) -> str:
    """Return a human-readable name of the anchor's committed source."""
    if anchor.kind == "ferc714_lambda":
        return f"FERC 714 Sch. 6 system lambda of {anchor.product}"
    return f"actual_lmp_hourly_{anchor.product}.parquet"


def derive(
    iso: str,
    years: list[int],
    run: str = "rt",
    shapeless: dict[str, list[int]] | None = None,
) -> dict[str, dict[int, float]]:
    """Return ``{neighbor_name: {year: hr}}`` anchored to measured neighbor LMP.

    Args:
        iso: The ISO whose registered seams are anchored.
        years: Calendar years to anchor.
        run: ``"rt"`` / ``"da"`` for an LMP anchor (ignored by a lambda anchor).
        shapeless: When given, a (neighbour, year) with no EIA-930 load shape is
            RECORDED here (``{neighbour: [years]}``) and left out of the table
            instead of raising — an armed seam could not price that year either.
            ``None`` (the default) keeps the fail-closed behaviour.

    Raises:
        KeyError: ``iso`` has no anchor map (an unregistered ISO never emits
            a silently-empty table).
        FileNotFoundError: a DECLARED anchor's product file or year rows are
            absent — the former silent ``continue`` (FINDING-spp-33 §2).
    """
    if iso not in NEIGHBOR_LMP_ANCHORS:
        raise KeyError(
            f"{iso}: no neighbour anchor map registered in NEIGHBOR_LMP_ANCHORS"
        )
    anchors = NEIGHBOR_LMP_ANCHORS[iso]
    out: dict[str, dict[int, float]] = {}
    for neighbor in INTERFACE_NEIGHBORS.get(iso, []):
        anchor = anchors.get(neighbor.name)
        if anchor is None:
            continue
        per_year: dict[int, float] = {}
        for year in years:
            measured = _measured_mean_lmp(anchor, year, run)
            if measured is None:
                raise FileNotFoundError(
                    f"{iso}/{neighbor.name}: declared anchor "
                    f"{anchor_source(anchor)} has no "
                    f"{'non-zero' if anchor.kind == 'ferc714_lambda' else run} "
                    f"rows for {year}"
                    + (f" in zones {anchor.zones}" if anchor.zones else "")
                )
            shaped = neighbor_load_shape(neighbor, year, _HOURS)
            if shaped is None and shapeless is not None:
                shapeless.setdefault(neighbor.name, []).append(year)
                continue
            if shaped is None:
                raise FileNotFoundError(
                    f"{iso}/{neighbor.name}: no EIA-930 load shape resolves for "
                    f"{year} (ba_code={neighbor.ba_code}, proxy_ba={neighbor.proxy_ba})"
                )
            k = float(np.nanmean(shaped[0] ** 1.0))  # shape already exponentiated
            gas = neighbor_gas_price(neighbor, year)
            hr = measured / (gas * k)
            per_year[year] = round(hr, 2)
        out[neighbor.name] = per_year
    return out


def unanchored(iso: str) -> list[str]:
    """Return the ISO's registered neighbours that carry no measured anchor."""
    anchors = NEIGHBOR_LMP_ANCHORS.get(iso, {})
    return [n.name for n in INTERFACE_NEIGHBORS.get(iso, []) if n.name not in anchors]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="PJM")
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--run", default="rt", choices=("rt", "da"))
    ap.add_argument(
        "--skip-shapeless",
        action="store_true",
        help="report (do not fail on) a seam-year with no EIA-930 load shape",
    )
    args = ap.parse_args()
    iso = args.iso.upper()
    shapeless: dict[str, list[int]] | None = {} if args.skip_shapeless else None
    try:
        table = derive(iso, args.years, args.run, shapeless)
    except (KeyError, FileNotFoundError) as exc:
        sys.exit(f"derive_neighbor_hr_by_year: {exc}")
    print(f"# Derived measured-anchored neighbor heat rates for {iso} ({args.run})")
    for name, per_year in table.items():
        cur = next(
            n.marginal_heat_rate for n in INTERFACE_NEIGHBORS[iso] if n.name == name
        )
        anchor = NEIGHBOR_LMP_ANCHORS[iso][name]
        tag = (" PROXY anchor" if anchor.proxy else "") + (
            " FERC-714 lambda anchor" if anchor.kind == "ferc714_lambda" else ""
        )
        cells = ", ".join(f"{y}: {hr}" for y, hr in sorted(per_year.items()))
        print(f'    "{name}": {{{cells}}},   # structural HR {cur}{tag}')
    for name in unanchored(iso):
        print(
            f"# {name}: no measured anchor registered — structural "
            "marginal_heat_rate kept (see the ISO's NEIGHBOR_LMP_ANCHORS entry)"
        )
    for name, gap in (shapeless or {}).items():
        print(f"# {name}: no EIA-930 load shape for {sorted(gap)} — not anchored")


if __name__ == "__main__":
    main()
