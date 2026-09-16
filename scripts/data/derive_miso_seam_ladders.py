#!/usr/bin/env python3
"""Derive MISO's per-seam measured band-price ladders (Q-Q duration coupling).

Fixes the MISO 2025 import starvation (gap register G-23 residual; audit box 5
of ``docs/multi-iso/miso-cc-overrun-rootcause-2026-07.md``): the reference-
price seam clears on the hourly spot spread, but the measured PJM+IESO seam
flow is a firm/scheduled base — it imports in 97.5-99.5% of ALL hours
(p10 0.9-1.7 GW), its hourly flow is uncorrelated with the RT LMP spread
(r = +0.06), and in 2025 the annual RT spread is $0.00 while 28.0 TWh flowed.
46-56% of the measured import MWh moves at spreads inside/below the $2
hurdle, so a hurdle-gated arbitrage seam structurally deletes the flow in a
zero-spread year (model 2025 gross imports 3.4 TWh vs actual net 19.0).

This derives the same replacement NEISO's audit C-6 closure used
(``scripts/data/derive_neiso_import_tranches.py``): the seam's *revealed supply
curve*, built by Q-Q duration coupling of two measured series —

1. **Per-seam flows** — EIA-930 BA-to-BA net interchange for MISO
   (``data/raw/eia-930-interchange/MISO interchange hourly.parquet``),
   pooled onto the model's three priced seams by
   ``interchange_config.MISO_SEAM_DIBA`` (PJM+IESO / SWPP+SPA /
   SOCO+TVA+AECI+LGEE+SIKE). Hour-ending local -> hour-beginning fixed
   non-leap calendar (Feb 29 dropped), the LP's clock.
2. **Internal clearing price** — the measured MISO Day-Ahead hub LMP
   (``data/raw/_validation-source/actual_lmp_hourly_MISO.parquet``, ``da``).
   External transactions schedule in the DA market, so DA is the price the
   seam supply curve is revealed against (same convention as NEISO).

Methodology — per-band Q-Q duration coupling
--------------------------------------------
The reference-price node already splits each seam into
``neighbor_price.SEAM_FLOW_TRANCHES`` (8) equal flow bands per direction
(``transmission.build_reference_price_node``); band ``k`` clears fully
whenever the internal price exceeds its offer. The measured counterpart of
that offer is the DA price whose exceedance duration equals the measured
duration of the seam flow exceeding the band's midpoint depth:

    import band k:  pi_k    = Quantile_DA(1 - P[flow >  L_k])
    export band k:  sigma_k = Quantile_DA(    P[flow < -L_k])
    L_k = (k - 0.5) x interface_limit / 8   (the band's midpoint depth)

i.e. the DA price duration curve and the seam flow duration curve are paired
quantile-by-quantile, per seam and per direction. A band deeper than the
measured record's deepest flow gets the sample extreme (an effectively
never-clearing scarcity/floor rung). Band CAPACITIES are untouched — the
existing 8 x interface_limit/8 structure and the measured per-seam
(month x hour-of-day) deliverability envelopes
(``eia_loader.measured_seam_import_envelope``) keep carrying the measured
capability; ONLY the price ladder changes.

Why this is the right market structure (rule #1): the MISO<->PJM interchange
is dominated by firm PTP transmission service, grandfathered agreements and
JOA firm flow entitlements — energy scheduled around the clock at prices
revealed only statistically, not a spot-spread arbitrage. The ladder encodes
that revealed willingness-to-flow as a rising supply curve the LP still
clears *economically* every hour against its own internal price: nothing is
forced (contrast the rejected ``miso_firm_import_floor`` min_gen pin), flows
respond to changed model conditions, and the pooled multi-year ladder is the
forward story (a persistent seam structure that regenerates as the measured
record extends — the NEISO static-entry pattern).

Identification (CLAUDE.md rule 23): measured-behaviour, frozen formula — the
ladders re-derive ONLY when the source data updates (a new EIA-930 /
settlement year), never because a backcast residual moved. Zero fitted
parameters: every number is a quantile of a measured series at a structurally
fixed depth grid.

Boundary reconciliations (rule 14), documented here and in
``interchange_config.MISO_SEAM_LADDER_BY_YEAR``:

* The PJM seam pools the Ontario (IESO) tie per ``MISO_SEAM_DIBA`` — the
  model has one eastern seam. IESO is +7.4/+5.2/+3.4 TWh of the seam's
  +40.9/+32.3/+28.0 TWh (2023/24/25); its surplus-baseload economics are
  absorbed into the pooled ladder's cheap base bands.
* The coupling anchor is the MISO hub-mean DA LMP (the in-repo canonical
  internal price), not the border-zone LMPs the seam physically clears
  against; the PJM-side western border anchor
  (``pjm_border_lmp_hourly_MISO.parquet``, CHICAGO GEN/AEP GEN/ATSI GEN) is
  reported per band as a diagnostic so each threshold stays interpretable as
  border price +/- premium.
* Same-seam no-wash: each seam's export ladder must sit strictly below its
  import ladder at every band (a seam cannot deeply import and export at
  once); asserted per year, with a clamp note if it ever binds. CROSS-seam
  simultaneous counterflow (import PJM while exporting South) is real
  wheel-through the multi-link external node carries physically, bounded by
  the measured per-seam envelopes.

Usage:
    python scripts/data/derive_miso_seam_ladders.py            # all years + pooled
    python scripts/data/derive_miso_seam_ladders.py --years 2025

Output is hand-rounded (prices to cents) into
``interchange_config.MISO_SEAM_LADDER_BY_YEAR``, its neighbour-anchored overlay
``MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR`` (:func:`derive_pjm_neighbour`) and the
hourly OFFSET overlay ``MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR``
(:func:`derive_pjm_neighbour_hourly`), with this script cited as the derivation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

RAW = RAW_DATA_DIR
INTERCHANGE_PARQUET = RAW / "eia-930-interchange" / "MISO interchange hourly.parquet"
ACTUAL_LMP_PARQUET = RAW / "_validation-source" / "actual_lmp_hourly_MISO.parquet"
PJM_BORDER_PARQUET = RAW / "_validation-source" / "pjm_border_lmp_hourly_MISO.parquet"

YEARS = (2023, 2024, 2025)

# No-wash ordering margin ($/MWh): a seam's export sinks sit at least this far
# below its cheapest import band (same-seam reconciliation, module docstring).
NO_WASH_EPS = 0.01

# Fixed non-leap calendar helpers (identical to derive_neiso_import_tranches).
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_MONTH_START_HOUR = (np.cumsum([0, *_DAYS[:-1]]) * 24).tolist()
_HOURS_PER_YEAR = 8760


def load_joined() -> pd.DataFrame:
    """Return the dense (year, hour) frame joining seam flows and the DA LMP.

    Columns: one import-positive MW series per seam in
    :data:`~market_sim.config.interchange_config.MISO_SEAM_DIBA` (``PJM`` /
    ``SPP`` / ``South``), plus ``da``/``rt`` ($/MWh MISO hub) and
    ``pjm_border`` ($/MWh, diagnostic anchor). Isolated gaps (DST)
    interpolated (limit=3).
    """
    from market_sim.config.interchange_config import MISO_SEAM_DIBA

    ix = pd.read_parquet(INTERCHANGE_PARQUET)
    # Hour-ending local -> hour-beginning fixed non-leap hour-of-year.
    t = pd.to_datetime(ix["local_time"]) - pd.Timedelta(hours=1)
    base = np.asarray([_MONTH_START_HOUR[m - 1] for m in t.dt.month])
    hr = base + (t.dt.day.to_numpy() - 1) * 24 + t.dt.hour.to_numpy()
    ix = ix.assign(year=t.dt.year.to_numpy(), hour=hr)
    ix.loc[(t.dt.month == 2) & (t.dt.day == 29), "hour"] = -1
    ix = ix[(ix["hour"] >= 0) & (ix["hour"] < _HOURS_PER_YEAR)]
    diba_to_seam = {d: s for s, dibas in MISO_SEAM_DIBA.items() for d in dibas}
    ix = ix.assign(seam=ix["diba"].astype(str).map(diba_to_seam))
    ix = ix.dropna(subset=["seam"])
    # Import-positive per seam: EIA sign is + = MISO exports to the DIBA.
    flows = -ix.pivot_table(
        index=["year", "hour"],
        columns="seam",
        values="mw",
        aggfunc="sum",
        observed=True,
    )
    lmp = pd.read_parquet(ACTUAL_LMP_PARQUET).set_index(["year", "hour"])
    border = (
        pd.read_parquet(PJM_BORDER_PARQUET)
        .groupby(["year", "hour"])["price"]
        .mean()
        .rename("pjm_border")
    )
    years = sorted(set(flows.index.get_level_values("year")))
    full = pd.MultiIndex.from_product(
        [years, range(_HOURS_PER_YEAR)], names=["year", "hour"]
    )
    df = flows.reindex(full).join(lmp).join(border)
    return df.interpolate(limit=3)


def qq_import(price: np.ndarray, flow: np.ndarray, level: float) -> float:
    """Import-band price: DA quantile matching the depth's exceedance duration."""
    exceed = float((flow > level).mean())
    return float(np.quantile(price, 1.0 - exceed))


def qq_export(price: np.ndarray, flow: np.ndarray, level: float) -> float:
    """Export-band price: DA quantile matching the export-depth duration."""
    depth = float((flow < -level).mean())
    return float(np.quantile(price, depth))


def _derive_one(da: np.ndarray, flow: np.ndarray, spec, notes: list[str]) -> dict:
    """Derive one seam's ``{"import": [...], "export": [...]}`` ladder."""
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES

    step = spec.interface_limit_mw / SEAM_FLOW_TRANCHES
    mids = (np.arange(SEAM_FLOW_TRANCHES) + 0.5) * step
    imp = [qq_import(da, flow, m) for m in mids]
    exp = [qq_export(da, flow, m) for m in mids]
    # Same-seam no-wash: every export band strictly below the cheapest import
    # band (rule 14 single-seam reconciliation).
    lim = min(imp) - NO_WASH_EPS
    for k, s in enumerate(exp):
        if s > lim:
            notes.append(
                f"{spec.name} export band {k + 1}: sink ${s:.2f} clamped "
                f"to ${lim:.2f} (same-seam no-wash vs cheapest import band)"
            )
            exp[k] = lim
    return {
        "import": [round(p, 2) for p in imp],
        "export": [round(p, 2) for p in exp],
    }


def derive(g: pd.DataFrame) -> tuple[dict, list[str]]:
    """Derive ``{seam: {"import": [...], "export": [...]}}`` from sample ``g``.

    ``g`` is one year of :func:`load_joined` (or the pooled multi-year frame
    for the static forward ladder). Prices are per band 1..SEAM_FLOW_TRANCHES
    at the midpoint-depth grid of each seam's interface limit. ``notes``
    carries no-wash clamp diagnostics (expected empty — the measured record
    orders every seam naturally).

    The three registry seams (PJM/SPP/South) derive on their SHARED non-NaN row
    set; the Manitoba (MHEB) two-way seam (miso-74) derives INDEPENDENTLY on its
    own ``da``+MHEB row set, so the three registry ladders are byte-identical to
    the pre-Manitoba derivation (rule 23 — no unrelated ladder moves).
    """
    from market_sim.config.interchange_config import (
        INTERFACE_NEIGHBORS,
        MISO_MANITOBA_SEAM_SPEC,
    )

    out: dict[str, dict[str, list[float]]] = {}
    notes: list[str] = []
    g3 = g.dropna(subset=["da"] + [n.name for n in INTERFACE_NEIGHBORS["MISO"]])
    da3 = g3["da"].to_numpy(dtype=float)
    for spec in INTERFACE_NEIGHBORS["MISO"]:
        out[spec.name] = _derive_one(
            da3, g3[spec.name].to_numpy(dtype=float), spec, notes
        )
    gm = g.dropna(subset=["da", MISO_MANITOBA_SEAM_SPEC.name])
    out[MISO_MANITOBA_SEAM_SPEC.name] = _derive_one(
        gm["da"].to_numpy(dtype=float),
        gm[MISO_MANITOBA_SEAM_SPEC.name].to_numpy(dtype=float),
        MISO_MANITOBA_SEAM_SPEC,
        notes,
    )
    return out, notes


def derive_pjm_neighbour(g: pd.DataFrame) -> tuple[dict[str, list[float]], list[str]]:
    """Derive the PJM seam's ladder anchored on the NEIGHBOUR's own border price.

    The miso-225 owner ruling (2026-09-06) on the D-2 5(i) seam object: an
    import's merit position must depend on the EXPORTING market's supply cost,
    not on MISO's own price.  The construction is byte-for-byte the incumbent
    one — the same Q-Q duration coupling, the same midpoint-depth grid, the same
    measured seam flows, the same no-wash reconciliation — with the price series
    swapped from the MISO hub DA to the PJM western-border DA
    (``pjm_border_lmp_hourly_MISO.parquet``, already loaded here as the
    incumbent derivation's own interpretability anchor).  Nothing is fitted: the
    only change is WHICH measured price the duration coupling reads.

    PJM ONLY, and that is a DATA boundary rather than a choice (rule 14
    ``[R-ACCURATE]``): no measured SPP or SOCO/TVA price series is held under
    ``data/raw``, so those two seams keep the incumbent anchor and the gap is
    stated here rather than papered over with a proxy.

    Phase-0 evidence that the swap does what it claims
    (``scripts/probes/_miso225_seam_neighbour_phase0.py``): the neighbour anchor
    lowers every import band in every year (bands 1-4 mean -$3.81 / -$3.03 /
    -$2.32 for 2023/2024/2025), and in the MISO sub-$20 hours the PJM border
    price is the cheaper of the two in 85 / 80 / 74 % of hours while the MEASURED
    import in exactly those hours is 6,021 MW against a 4,674 MW all-hours mean
    -- MISO imports MOST when it is cheapest, which a ladder anchored on MISO's
    own falling price cannot represent.  The two series correlate 0.81-0.88, so
    the repricing is neither cosmetic nor a second copy of the same signal.
    """
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS

    spec = {n.name: n for n in INTERFACE_NEIGHBORS["MISO"]}["PJM"]
    notes: list[str] = []
    g = g.dropna(subset=["pjm_border", spec.name])
    return (
        _derive_one(
            g["pjm_border"].to_numpy(dtype=float),
            g[spec.name].to_numpy(dtype=float),
            spec,
            notes,
        ),
        notes,
    )


def derive_pjm_neighbour_hourly(
    g: pd.DataFrame,
) -> tuple[dict[str, list[float]], list[str]]:
    """Derive the PJM seam's HOURLY neighbour-anchored ladder as OFFSETS.

    miso-226 measured what the annual neighbour anchor of
    :func:`derive_pjm_neighbour` does and does not do: it repairs the ladder's
    LEVEL and not its RESPONSIVENESS.  ``corr(imports, own price)`` moved
    +0.750 -> +0.725 against a MEASURED -0.101 — 3 % of the distance — because
    a FIXED price ladder is cleared by the LP against its OWN internal price,
    so re-anchoring changes where the bands sit and not when they clear.  The
    bands still leave merit exactly when MISO's price falls, which is when MISO
    actually imports most.

    This is the successor miso-226 named.  Band ``k``'s offer becomes hourly::

        pi_k(t) = pjm_border(t) + delta_k

    so band ``k`` clears in hour ``t`` iff ``spread(t) > delta_k``, with
    ``spread = MISO hub DA - PJM western-border DA``.  The returned ladder holds
    the OFFSETS ``delta_k``, not prices; the applied price is assembled at solve
    time against the measured hourly border series
    (:func:`market_sim.data.eia_loader.measured_miso_pjm_border_prices`, the
    same series ``miso_pjm_lmp_import_pricing`` already reads hourly into the
    solve).

    The estimator is byte-for-byte the incumbent one — the same
    :func:`_derive_one` / :func:`qq_import` / :func:`qq_export` Q-Q duration
    coupling, the same midpoint-depth grid on the same ``SEAM_FLOW_TRANCHES``,
    the same measured seam flows, the same no-wash reconciliation.  The ONLY
    change is which measured series the coupling reads, which is the same single
    degree of freedom :func:`derive_pjm_neighbour` exercised:

    ======================  ==================================================
    incumbent               MISO hub DA
    annual neighbour        PJM western-border DA
    **this**                **DA - border SPREAD**
    ======================  ==================================================

    Nothing is fitted.  The no-wash reconciliation carries through unchanged:
    both directions share the same ``pjm_border(t)``, so an ordering constraint
    on the offsets is the same constraint on the applied hourly prices.

    WHY THIS IS NOT THE REFUTED SPREAD HURDLE (this module's own docstring
    records the seam being moved OFF a spread basis because the measured flow
    "is uncorrelated with the RT LMP spread (r = +0.06)"), both legs measured in
    ``scripts/probes/_miso231_hourly_seam_phase0.py``:

    1. That statistic is the **RT** spread against MISO's hub.  The **DA**
       spread against the **PJM western border** correlates with measured flow
       at +0.240 / +0.265 / +0.194 (2023/24/25), against ``corr(flow, MISO DA)``
       of -0.136 / -0.039 / -0.059.  The spread carries the sign the seam needs.
    2. A hurdle is ONE threshold; this is the same 8-band ladder, and the Q-Q
       coupling puts the shallow bands at NEGATIVE offsets (band 1 at -$29.17 in
       2023), so they clear even when MISO is far below PJM — which is exactly
       the "46-56 % of measured import MWh moves at spreads inside/below the $2
       hurdle" a hurdle deletes.  Nothing is gated away, and the measured annual
       volume is reproduced within 0.5 % in all three years.

    PJM ONLY, the same DATA boundary :func:`derive_pjm_neighbour` states (rule
    14 ``[R-ACCURATE]``): no measured SPP or SOCO/TVA price series is held under
    ``data/raw``, so those seams keep the incumbent anchor.
    """
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS

    spec = {n.name: n for n in INTERFACE_NEIGHBORS["MISO"]}["PJM"]
    notes: list[str] = []
    g = g.dropna(subset=["pjm_border", "da", spec.name])
    spread = (g["da"] - g["pjm_border"]).to_numpy(dtype=float)
    return (
        _derive_one(spread, g[spec.name].to_numpy(dtype=float), spec, notes),
        notes,
    )


SPP_HUB_PARQUET = RAW / "_validation-source" / "actual_lmp_hourly_zonal_SPP.parquet"

#: The SPP trading hub the MISO-SPP seam is anchored on (miso-233).
#:
#: The seam our topology carries is ONE collapsed link hosted on the
#: ``MISO_external`` (Midwest) bus, while the measured DIBAs behind it are
#: ``SWPP`` + ``SPA`` and the real boundary is two paths — MISO Midwest <->
#: SPP North and MISO South <-> SPP South. ``SPPNORTH_HUB`` is the anchor on
#: the STRUCTURAL ground that the MISO-facing side of the link our reduced
#: network represents is SPP North (MISO's southern seam has its own external
#: bus, ``split_miso_south_external_node``, and its own SOCO/TVA neighbours).
#: This is rule 14 ``[R-ACCURATE]``'s misalignment clause taken explicitly: the
#: hub is named on topology, before any ladder is derived, and NEVER chosen by
#: which one scores better — ``SPPSOUTH_HUB`` is reported as a sensitivity in
#: ``scripts/probes/_miso233_spp_hourly_phase0.py`` and selects nothing.
SPP_ANCHOR_HUB = "SPPNORTH_HUB"


def load_spp_hub_da(hub: str = SPP_ANCHOR_HUB) -> pd.Series:
    """Return the measured SPP hub DA LMP, indexed ``(year, hour)``.

    Reads ``actual_lmp_hourly_zonal_SPP.parquet`` (landed 2026-09-06 by lane
    SPP-14 from SPP's own ``portal.spp.org`` file-browser API; columns
    ``year``/``hour``/``zone``/``rt``/``da``). The file is already on the
    model's fixed non-leap 8760-hour LOCAL calendar — SPP runs on Central
    Prevailing Time, the same dispatch clock MISO's own
    ``actual_lmp_hourly_MISO.parquet`` uses — so the two series align
    hour-for-hour with no shift (``scripts/data/build_spp_lmp_reference.py``
    module docstring). Isolated gaps (the DST spring-forward hour) are
    interpolated on the same ``limit=3`` rule :func:`load_joined` applies.
    """
    frame = pd.read_parquet(SPP_HUB_PARQUET)
    frame = frame[frame["zone"].astype(str) == hub]
    series = (
        frame.set_index(["year", "hour"])["da"].astype(float).sort_index().rename(hub)
    )
    return series.interpolate(limit=3)


def derive_spp_neighbour_hourly(
    g: pd.DataFrame, hub: str = SPP_ANCHOR_HUB
) -> tuple[dict[str, list[float]], list[str]]:
    """Derive the SPP seam's HOURLY neighbour-anchored ladder as OFFSETS.

    The miso-233 extension of :func:`derive_pjm_neighbour_hourly` to the SECOND
    seam, on the SAME estimator and the same single degree of freedom — which
    measured series the Q-Q coupling reads. Band ``k``'s offer becomes hourly::

        pi_k(t) = spp_hub(t) + delta_k

    so band ``k`` clears in hour ``t`` iff ``spread(t) > delta_k``, with
    ``spread = MISO hub DA - SPP hub DA``. The returned ladder holds the OFFSETS
    ``delta_k``, not prices; the applied price is assembled at solve time
    against the measured hourly hub series
    (:func:`market_sim.data.eia_loader.measured_miso_spp_hub_prices`).

    WHY THE SECOND SEAM, AND WHY NOW
    --------------------------------
    miso-233's phase 0 decomposed the miso-232 keeper's residual price-decile
    slope from its own committed sidecars and found the defect is NOT on the
    repaired PJM seam: reconstructed PJM slope +2,377 / +2,611 / +2,704 MW
    against a MEASURED PJM seam of +1,319 / +1,052 / +815 — already steeper
    than measured, with the cheapest decile losing only 194-271 MW to the
    deliverability envelope. What cancels it is the two seams still on the
    INCUMBENT fixed MISO-hub ladder: SPP contributes -414 / -481 / -553 MW and
    South -919 / -1,135 / -827 MW, against measured seams of +317 / +466 / -50
    and +72 / +60 / +646. They carry the exact defect miso-226 named — a FIXED
    ladder cleared against the model's OWN price leaves merit when MISO's price
    falls, which is when MISO actually imports most.

    The blocker on record (mechanism-matrix §5.4 lever queue item 3) was that
    no measured hourly SPP price series was held under ``data/raw``. Lane
    SPP-14 landed one on 2026-09-06 (:data:`SPP_HUB_PARQUET`, 8,754 of 8,760
    hours in every year 2023-2025), so the exclusion that kept
    :func:`derive_pjm_neighbour_hourly` PJM-only no longer applies to SPP.
    Rule 14 ``[R-ACCURATE]`` is then directly on point: the incumbent SPP
    anchor is an ESTIMATE standing in for the neighbour's price, the measured
    neighbour price now exists, and the accurate input is preferred whatever it
    does to the residual.

    STATED AT THE GATE, because it is weaker than the PJM case. The
    admissibility statistic miso-231 §1 leaned on does NOT transfer:
    ``corr(measured SPP seam flow, MISO DA - SPP hub DA)`` is +0.041 / -0.020 /
    +0.050 against ``corr(flow, MISO DA)`` of -0.216 / -0.377 / +0.082 — the
    spread is UNINFORMATIVE about the SPP seam's hourly flow where the PJM
    spread was informative (+0.240 / +0.265 / +0.194). What the spread basis
    does is remove the WRONG-SIGNED response rather than supply a right-signed
    one: the simulated flow's correlation with the measured seam moves
    -0.213 / -0.289 / +0.065 -> +0.011 / -0.107 / +0.050. The case for the
    change is structural and rule-14, never the statistic.

    SOUTH IS STILL EXCLUDED, and that is still a DATA boundary rather than a
    choice: SOCO and TVA are not organised markets and publish no nodal or hub
    price, so no measured series exists to anchor that seam on. It keeps the
    incumbent MISO-hub ladder and phase 0 records what that costs.

    The estimator is byte-for-byte the incumbent one — the same
    :func:`_derive_one` / :func:`qq_import` / :func:`qq_export` coupling, the
    same midpoint-depth grid on the same ``SEAM_FLOW_TRANCHES``, the same
    measured seam flows, the same no-wash reconciliation. Nothing is fitted;
    the rule-23 ``[R-FROZEN-DERIVE]`` re-derive trigger is identical (the
    source series extending, never a residual moving).
    """
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS

    spec = {n.name: n for n in INTERFACE_NEIGHBORS["MISO"]}["SPP"]
    notes: list[str] = []
    work = g.join(load_spp_hub_da(hub), how="left")
    # CORRECTNESS PIN (miso-243, rule 23 [R-FROZEN-DERIVE]).  ``load_spp_hub_da``
    # is ``(year, hour)``-MultiIndexed.  A caller that passes ``df.loc[year]``
    # -- whose index is ``hour`` ALONE -- makes pandas PARTIAL-join on the shared
    # level, replicating each of the year's 8,760 rows against ALL THREE hub
    # years, so the Q-Q quantile is drawn from a three-year MIXTURE of the spread
    # instead of the year's own.  (The flow exceedance TARGETS are unaffected:
    # replicating a sample three times does not change a share.  Only the
    # quantile's sample is wrong.)  That defect produced the committed
    # 2023-2025 table and was invisible to every consistency check, including
    # this module's own pin test, because they all invoked the same call --
    # confirmed on three refuting legs plus a PJM no-join control in
    # ADDENDUM-miso242-the-derive-pairs-across-years-2026-09-07.md, repaired in
    # PREREG-miso243-repair-the-spp-ladders-cross-year-pairing-2026-09-07.md.
    # A left join can never legitimately ADD rows, so this is an invariant of the
    # operation rather than a tolerance, and it fails loudly from ANY caller.
    if len(work) != len(g):
        raise ValueError(
            f"SPP hub join changed the row count {len(g)} -> {len(work)}: the "
            f"frame passed in is indexed by {list(g.index.names)} while "
            f"load_spp_hub_da() is (year, hour)-MultiIndexed, so pandas "
            f"partial-joined on the shared level and paired this sample against "
            f"more than one hub year. Pass a frame that still carries the "
            f"'year' level (df.loc[[year]], not df.loc[year])."
        )
    work = work.dropna(subset=[hub, "da", spec.name])
    spread = (work["da"] - work[hub]).to_numpy(dtype=float)
    return (
        _derive_one(spread, work[spec.name].to_numpy(dtype=float), spec, notes),
        notes,
    )


def offline_score(g: pd.DataFrame, ladders: dict) -> dict[str, dict[str, float]]:
    """Score each seam's ladder against its measured flow, driven by actual DA.

    The offline analogue of the NEISO derivation's P9 diagnostic: simulate the
    band clearing ``sum(step x 1[DA > pi_k]) - sum(step x 1[DA < sigma_k])``
    on the measured DA price and compare to the measured seam net flow
    (volume, duration RMSE, import-hour share, hourly correlation). The live
    LP additionally applies the measured per-seam deliverability envelopes and
    its own internal price, so this is the derivation sanity check, not the
    calibration score.
    """
    from market_sim.config.interchange_config import (
        INTERFACE_NEIGHBORS,
        MISO_MANITOBA_SEAM_SPEC,
    )
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES

    def _score_one(da: np.ndarray, act: np.ndarray, lad: dict, step: float) -> dict:
        sim = sum(step * (da > p) for p in lad["import"]) - sum(
            step * (da < p) for p in lad["export"]
        )
        return {
            "sim_twh": sim.sum() / 1e6,
            "act_twh": act.sum() / 1e6,
            "dur_rmse": float(np.sqrt(np.mean((np.sort(sim) - np.sort(act)) ** 2))),
            "imp_hrs_sim": 100.0 * float((sim > 0).mean()),
            "imp_hrs_act": 100.0 * float((act > 0).mean()),
            "hourly_corr": float(np.corrcoef(sim, act)[0, 1]),
        }

    scores: dict[str, dict[str, float]] = {}
    g3 = g.dropna(subset=["da"] + [n.name for n in INTERFACE_NEIGHBORS["MISO"]])
    da3 = g3["da"].to_numpy(dtype=float)
    for spec in INTERFACE_NEIGHBORS["MISO"]:
        scores[spec.name] = _score_one(
            da3,
            g3[spec.name].to_numpy(dtype=float),
            ladders[spec.name],
            spec.interface_limit_mw / SEAM_FLOW_TRANCHES,
        )
    # Manitoba scored on its own da+MHEB row set (miso-74).
    if MISO_MANITOBA_SEAM_SPEC.name in ladders:
        gm = g.dropna(subset=["da", MISO_MANITOBA_SEAM_SPEC.name])
        scores[MISO_MANITOBA_SEAM_SPEC.name] = _score_one(
            gm["da"].to_numpy(dtype=float),
            gm[MISO_MANITOBA_SEAM_SPEC.name].to_numpy(dtype=float),
            ladders[MISO_MANITOBA_SEAM_SPEC.name],
            MISO_MANITOBA_SEAM_SPEC.interface_limit_mw / SEAM_FLOW_TRANCHES,
        )
    return scores


def _print_ladder(label: str, g: pd.DataFrame) -> None:
    """Derive, score and print one sample's ladders + anchor diagnostics."""
    ladders, notes = derive(g)
    gg = g.dropna(subset=["da"])
    da_mean = float(gg["da"].mean())
    border_mean = float(gg["pjm_border"].mean())
    print(f"\n=== {label} ===")
    print(
        f"  anchors: MISO hub DA mean ${da_mean:.2f}, "
        f"PJM western-border DA mean ${border_mean:.2f}"
    )
    for seam, lad in ladders.items():
        anchor = f"  [PJM border anchor ${border_mean:.2f}]" if seam == "PJM" else ""
        print(f'    "{seam}": {{{anchor}')
        print(f'        "import": {tuple(lad["import"])},')
        print(f'        "export": {tuple(lad["export"])},')
        print("    },")
    for n in notes:
        print(f"  note: {n}")
    # Reproducibility guard (miso-260, 2026-09-16): the three NEIGHBOUR blocks
    # below read anchor series that start in 2023 — the PJM western-border DA
    # (``pjm_border_lmp_hourly_MISO.parquet``) and the SPP hub. On an earlier
    # sample they leave `_derive_one` with an empty flow vector, whose NaN
    # exceedance duration raises out of ``np.quantile``, so the script could
    # not be RUN on 2020-2022 at all even though the PRIMARY ladder above
    # derives cleanly there (that ladder reads only the seam flows and the MISO
    # hub DA). This is a printing guard and NOT a re-derivation: no value
    # produced for any year changes, and the 2023-2025 path is untouched
    # (rule 23 ``[R-FROZEN-DERIVE]`` — the frozen estimator is unmodified).
    if not len(g.dropna(subset=["pjm_border"])):
        print(
            "  note: NO NEIGHBOUR OVERLAY — the PJM western-border DA and SPP "
            "hub anchors do not cover this sample (both series start 2023). "
            "The base ladder above is the whole of this year's entry, which is "
            "the documented degradation of miso_seam_neighbour_* (never an "
            "unpriced seam)."
        )
        for seam, s_ in offline_score(g, ladders).items():
            print(
                f"  offline P9 {seam}: {s_['sim_twh']:+.2f} TWh vs "
                f"{s_['act_twh']:+.2f} actual; duration RMSE {s_['dur_rmse']:.0f} "
                f"MW; import hours {s_['imp_hrs_sim']:.0f}% vs "
                f"{s_['imp_hrs_act']:.0f}%; hourly corr {s_['hourly_corr']:+.2f}"
            )
        return
    nb, nb_notes = derive_pjm_neighbour(g)
    print(
        f'    # miso-225 NEIGHBOUR-ANCHORED "PJM" (PJM western-border DA ${border_mean:.2f}):'
    )
    print(f'        "import": {tuple(nb["import"])},')
    print(f'        "export": {tuple(nb["export"])},')
    for n in nb_notes:
        print(f"  note (neighbour): {n}")
    hb, hb_notes = derive_pjm_neighbour_hourly(g)
    print(
        '    # miso-231 HOURLY NEIGHBOUR-ANCHORED "PJM" '
        "(OFFSETS delta_k; applied price = pjm_border(t) + delta_k):"
    )
    print(f'        "import": {tuple(hb["import"])},')
    print(f'        "export": {tuple(hb["export"])},')
    for n in hb_notes:
        print(f"  note (hourly): {n}")
    sb, sb_notes = derive_spp_neighbour_hourly(g)
    print(
        '    # miso-233 HOURLY NEIGHBOUR-ANCHORED "SPP" '
        "(OFFSETS delta_k; applied price = spp_hub(t) + delta_k):"
    )
    print(f'        "import": {tuple(sb["import"])},')
    print(f'        "export": {tuple(sb["export"])},')
    for n in sb_notes:
        print(f"  note (SPP hourly): {n}")
    for seam, s in offline_score(g, ladders).items():
        print(
            f"  offline P9 {seam}: {s['sim_twh']:+.2f} TWh vs {s['act_twh']:+.2f} "
            f"actual; duration RMSE {s['dur_rmse']:.0f} MW; import hours "
            f"{s['imp_hrs_sim']:.0f}% vs {s['imp_hrs_act']:.0f}%; "
            f"hourly corr {s['hourly_corr']:+.2f}"
        )


def main() -> None:
    """CLI entry point: derive per-year ladders and the pooled forward ladder."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, default=list(YEARS))
    args = ap.parse_args()

    df = load_joined()
    for year in args.years:
        # df.loc[[year]] -- NOT df.loc[year] -- so the (year, hour) MultiIndex
        # survives and derive_spp_neighbour_hourly's hub join pairs within the
        # year (miso-243; the invariant in that function enforces it).
        _print_ladder(str(year), df.loc[[year]])
    if len(args.years) > 1:
        pooled = df.loc[args.years[0] : args.years[-1]]
        _print_ladder(
            f"pooled {args.years[0]}-{args.years[-1]} (static forward ladder)", pooled
        )


if __name__ == "__main__":
    main()
