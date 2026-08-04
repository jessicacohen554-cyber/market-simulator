"""Derive the CAISO per-zone monthly marginal delivery-factor (loss) surface.

The caiso-164 derive (frozen, CLAUDE.md rule 23 ``[R-FROZEN-DERIVE]`` —
re-derives ONLY when its source data updates), **re-derived at caiso-166
because its SOURCE DATA UPDATED**: caiso-165 intook CAISO's four
``DLAP_*-APND`` load aggregation points into
``data/raw/lmp-data/CAISO/CAISO_dam_hourly_<year>.csv`` (charters
``results/calibration/PRECHECK-caiso164-zonal-loss-surface-2026-08-04.md`` and
``results/calibration/PRECHECK-caiso165-dlap-intake-intra-sp15-2026-08-04.md``
§5.1; the re-derive itself is chartered by
``results/calibration/PRECHECK-caiso166-measured-loss-zones-2026-08-04.md``).
The estimator, the schema and every threshold are UNCHANGED — this commit cites
a data change, exactly as rule 23 requires, and consults no residual.

Reads the committed CAISO day-ahead component record (CAISO OASIS ``PRC_LMP``
DAM rows for the three ``TH_*_GEN-APND`` trading hubs and, since caiso-165, the
``DLAP_*-APND`` load aggregation points) and emits the dimensionless per-zone
(month) marginal delivery-factor deviation surface consumed by the gated
``ScenarioConfig.caiso_zonal_loss_surface`` LP mechanism:

    data/raw/iso-specific-transmission/CAISO_loss_surface.csv
    columns: iso, zone, year, month, df_deviation, n_hours, interpolated

**The physics.** A CAISO LMP decomposes as ``LMP_i = MCE + MCC_i + MCL_i``
(CAISO Tariff §27.1.1 / Business Practice Manual for Market Operations §6),
with the marginal cost of losses ``MCL_i`` the value of losses incurred
delivering a marginal MW to node ``i`` relative to the system reference. This
is the same decomposition PJM writes ``MEC + MCC + MLC`` and MISO writes
``MCC + MLC``, so the derive target is the same dimensionless deviation the
frozen MISO/PJM derives use::

    dev_z,m = sum(MCL_z,t) / sum(MCE_t)   over the month's hours

— the MCE-weighted estimator, chosen so the surface reproduces the measured
total MCL exactly when re-multiplied by the measured MCE series. Nothing here
reads a model output, a residual, or a scoring target: this is a measured
physical network property that regenerates for any year from the same published
feed and responds to changed grid conditions (rule 13 ``[R-MEASURED]``).

**Rule 25 ``[R-ISO-SCOPE]``.** Every number is derived from CAISO's own
published component record and written to CAISO's own file. No value crosses
from the MISO or PJM analogues, whose verdicts are their own (rule 28(d)); the
only thing shared with them is the estimator's algebra.

**Basis: day-ahead.** CAISO's IFM is an hourly, commitment-aware full-network
optimization — the closest real-world analogue of the model's LP — so the
surface derives from the DA component record.

**Zones — FIVE MEASURED since caiso-166, and the two crosswalks are declared.**
The model carries five CAISO load zones. Each takes its deviation from a
published CAISO node:

=============  =====================  ======================================
model zone     source node            disposition
=============  =====================  ======================================
``NP15``       ``TH_NP15_GEN-APND``   its own hub
``ZP26``       ``TH_ZP26_GEN-APND``   its own hub
``SP15_rest``  ``TH_SP15_GEN-APND``   the SP15 generation hub IS the SP15
                                      desert/Kern generation belt this zone
                                      represents
``LA_BASIN``   ``DLAP_SCE-APND``      **RECONCILIATION, not identity** —
                                      SCE's territory covers the LA basin
                                      *and* much of the desert/Kern belt the
                                      model assigns to ``SP15_rest``, so the
                                      DLAP is a load-weighted mix dominated
                                      by, but not coincident with, the model
                                      zone
``SDGE``       ``DLAP_SDGE-APND``     **near-identity** — SDG&E's service
                                      territory *is* the model's San Diego
                                      pocket behind Path 44 / SWPL
=============  =====================  ======================================

``DLAP_PGAE-APND`` is **deliberately NOT** substituted for ``NP15`` or
``ZP26``: PG&E's territory straddles both, so using it would replace two
measured values with one blended one — a downgrade, not an upgrade.
``DLAP_VEA-APND`` (Valley Electric) has no model zone.

**Rule 14 ``[R-ACCURATE]`` disposition, pre-committed by PRECHECK-caiso165
§5.1 before any number was seen.** Both substitutions are measured-over-
reconciled upgrades and are kept REGARDLESS of what they do to the backcast.
The status quo for ``LA_BASIN`` and ``SDGE`` was not a rival measurement — it
was the SP15 *generation* hub's deviation, weighted to where power injects (the
desert belt), standing in for a *load* pocket at the other end of the corridor.
A DLAP is the right KIND of object for a load zone even where its boundary is
imperfect, and rule 14's misalignment clause explicitly prefers a *reconciled
version of the real data* over a stand-in. If the re-derived surface makes the
backcast worse, that is a discovered bug elsewhere (rules 1 / 14), never
grounds to revert.

**Per-(zone, year, month) coverage rule (PRECHECK-caiso165 §2.2, declared
before the data was inspected).** ``PRC_LMP`` retention moves forward with the
calendar, so a DLAP does not print for every historical hour. A
``(zone, year, month)`` cell takes its **own measured DLAP** deviation iff that
DLAP printed in at least :data:`MIN_MONTH_COVERAGE` of the month's usable
hours; otherwise it falls back to ``TH_SP15_GEN-APND`` for that month with
``interpolated=True``, exactly as the whole zone did before caiso-166.

**ZERO new free parameters** (rule 5 ``[R-NO-MAGIC]``, rule 23
``[R-FROZEN-DERIVE]``): the monthly threshold is the EXISTING frozen annual
guard :data:`MIN_HOURS_PER_YEAR` expressed as a ratio of the 8,760-hour year,
not a new number. It regenerates automatically as retention moves, and it
degrades to the pre-caiso-166 behaviour wherever the DLAP record is absent.

**Usable hours, and why the three hubs alone define them.** An hour is usable
iff all three :data:`REFERENCE_NODES` print in it — the pre-caiso-166 rule,
unchanged, so the ``MCE`` denominator and the three hub zones' deviations are
bit-identical to the caiso-164 surface. DLAP presence is NOT part of that
test: requiring it would discard ~96 % of 2023 and destroy the three measured
hub zones the caiso-164 keeper rests on. DLAP presence instead enters per
(zone, month) through the coverage rule above. Each zone-month's numerator and
denominator are taken over the SAME hour set (the hours its own source node
printed), so a partially-covered month is still the measured ratio and never a
numerator/denominator mismatch.

**The WECC nodes carry no row.** ``WECC_import`` and the per-hub intertie nodes
it expands into are fictitious pricing nodes with no location, so they have no
published delivery-factor deviation to derive one from — the same reason PJM's
external star node is excluded. Their links stay lossless.

**Per-year + pooled rows.** Backcast year Y consumes year-Y's own monthly
surface — a same-year measured *physical network property*, the same
admissibility class as same-year plant-specific CEMS emission rates. The
additional pooled rows (``year = 0``, all train years) are the forecast-mode
forward analogue — the stable multi-year network property that regenerates from
rolling history — and are NOT used by the backcast A/B.

**Acceptance mode (run BEFORE any solve).** ``--acceptance`` recomputes, per
benchmarked zone pair-year, the separation the LP's dual ratios would imply at
the typical flow pattern —
``sum_m h_m x MCE_m x ((1+dev_y,m)/(1+dev_x,m) - 1) / sum_m h_m`` — and gates it
against the ``[0.5x, 1.5x]`` band of the measured mean dMCL for that pair-year
(the miso-76 B1 band, applied to CAISO's own measured quantities). The measured
benchmark is taken at **the node the surface actually used for that month**, so
an interpolated month is benchmarked against the node it interpolated from and
a measured month against its own DLAP — like for like, never a measured
benchmark against an interpolated surface.

caiso-166 **adds** ``NP15↔LA_BASIN`` and ``NP15↔SDGE`` to
:data:`ACCEPTANCE_PAIRS`. As written the gate benchmarked only pairs this
re-derive does not change, so it was blind to exactly the two new zones. Every
pair-year must stay in the band; **a new zone failing the band is a
stop-the-line**, not a caveat (PRECHECK-caiso165 §5.1).

This validates the derive -> loss-fraction -> dual-ratio -> $ separation algebra
offline; the LP A/B remains the real test, since flow directions and congestion
interactions are LP-endogenous.

Usage:
    PYTHONPATH=.:src python scripts/data/derive_caiso_loss_surface.py
    PYTHONPATH=.:src python scripts/data/derive_caiso_loss_surface.py --acceptance
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from market_sim.config.paths import ISO_TRANSMISSION_DIR, RAW_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("derive_caiso_loss_surface")

OUT = ISO_TRANSMISSION_DIR / "CAISO_loss_surface.csv"
DAM_DIR = RAW_DATA_DIR / "lmp-data" / "CAISO"

#: Train-window years the surface carries per-year rows for. Rule 22
#: ``[R-HOLDOUT]``: 2023-2025 only — the holdout spend freeze is active and no
#: other year may be read, scored or registered.
YEARS: tuple[int, ...] = (2023, 2024, 2025)

#: Sentinel year for the pooled (forecast-analogue) rows.
POOLED_YEAR = 0

#: The node every zone falls back to when its own source node does not clear
#: the month's coverage rule. The SP15 generation hub — the pre-caiso-166
#: stand-in for both southern load pockets, kept as the fallback so a
#: thin-retention month degrades to the previous behaviour rather than to a
#: gap or an invented number.
FALLBACK_NODE = "TH_SP15_GEN-APND"

#: Model zone -> (source node, fallback node or ``None``). ``None`` means the
#: zone's own node is authoritative in every month (it is a trading hub with
#: full retention); a fallback node means the per-month coverage rule applies.
#: See the module docstring's zone table for each crosswalk's disposition.
ZONE_SOURCE: dict[str, tuple[str, str | None]] = {
    "NP15": ("TH_NP15_GEN-APND", None),
    "ZP26": ("TH_ZP26_GEN-APND", None),
    "SP15_rest": ("TH_SP15_GEN-APND", None),
    "LA_BASIN": ("DLAP_SCE-APND", FALLBACK_NODE),
    "SDGE": ("DLAP_SDGE-APND", FALLBACK_NODE),
}

#: The three trading hubs whose joint presence defines a usable hour. The
#: pre-caiso-166 completeness rule, unchanged: they carry the MCE reference,
#: the three measured hub zones, and the fallback node.
REFERENCE_NODES: tuple[str, ...] = (
    "TH_NP15_GEN-APND",
    "TH_ZP26_GEN-APND",
    "TH_SP15_GEN-APND",
)

#: Acceptance-mode benchmark pairs: (near, far) model zones whose measured
#: delta-MCL the implied dual separation is gated against. The first two are
#: the north-south gradients caiso-164 §0 measured; caiso-166 adds the two
#: southern load pockets it re-sources, because a gate that benchmarks only
#: unchanged pairs cannot see the change it is meant to gate.
ACCEPTANCE_PAIRS: tuple[tuple[str, str], ...] = (
    ("NP15", "ZP26"),
    ("NP15", "SP15_rest"),
    ("NP15", "LA_BASIN"),
    ("NP15", "SDGE"),
)

#: The miso-76 B1 acceptance band, applied to CAISO's own measured quantities.
ACCEPT_BAND = (0.5, 1.5)

#: MCE is published per row and is identical across nodes per interval up to
#: the feed's rounding; above this the identity is broken and the derive must
#: fail rather than average an inconsistent reference. Since caiso-166 this is
#: asserted across the DLAPs too, not only the hubs (PRECHECK-caiso165 §3): if
#: the published system reference is not uniform once load aggregation points
#: are included, the decomposition is not usable as published.
MCE_IDENTITY_TOL = 1e-4

#: A year needs near-full DAM coverage before its rows stand for a month.
MIN_HOURS_PER_YEAR = 8000

#: Per-(zone, month) coverage threshold — :data:`MIN_HOURS_PER_YEAR` expressed
#: as a fraction of the 8,760-hour year. NOT a new parameter (rule 5
#: ``[R-NO-MAGIC]``, rule 23 ``[R-FROZEN-DERIVE]``): it is the existing frozen
#: annual guard re-expressed at monthly resolution, so it moves only when that
#: guard moves.
MIN_MONTH_COVERAGE = MIN_HOURS_PER_YEAR / 8760.0


def _source_nodes() -> set[str]:
    """Return every published node the surface reads (sources + fallbacks)."""
    nodes = set(REFERENCE_NODES)
    for primary, fallback in ZONE_SOURCE.values():
        nodes.add(primary)
        if fallback is not None:
            nodes.add(fallback)
    return nodes


def _load_components(year: int) -> pd.DataFrame:
    """Load one year of CAISO DAM components, keyed on the local month.

    Returns a long frame with columns ``utc``, ``month``, ``node``, ``mcl``,
    ``mce``, ``mcc``, ``lmp``, restricted to the year's **usable** hours (every
    node in :data:`REFERENCE_NODES` printing).

    The month is taken on the **Pacific** clock, not GMT: the file is
    GMT-stamped and a GMT month boundary splits a Pacific month 7-8 hours off,
    which would smear each month's surface into its neighbour.
    """
    path = DAM_DIR / f"CAISO_dam_hourly_{year}.csv"
    if not path.is_file():
        raise SystemExit(f"no CAISO DAM component file at {path}")
    raw = pd.read_csv(path)
    raw = raw[raw["node"].isin(_source_nodes())].copy()
    if raw.empty:
        raise SystemExit(f"{path} carries no CAISO source-node rows")
    raw["utc"] = pd.to_datetime(raw["interval_start_gmt"], utc=True)
    local = raw["utc"].dt.tz_convert("America/Los_Angeles")
    raw = raw[local.dt.year == year].copy()
    raw["month"] = local[local.dt.year == year].dt.month
    raw = raw.rename(columns={"MCL": "mcl", "MCE": "mce", "MCC": "mcc", "LMP": "lmp"})

    missing_hubs = set(REFERENCE_NODES) - set(raw["node"].unique())
    if missing_hubs:
        raise SystemExit(f"{year}: reference hubs absent from the feed: {missing_hubs}")

    # An hour is usable iff every REFERENCE hub prints in it. This is the
    # pre-caiso-166 rule verbatim (the hub set was then the whole node set), so
    # the MCE denominator and the three hub zones stay bit-identical. DLAP
    # presence deliberately does NOT enter here — it enters per (zone, month)
    # through the coverage rule in :func:`_month_sources`.
    hubs = raw[raw["node"].isin(REFERENCE_NODES)]
    complete_hours = hubs.groupby("utc")["node"].nunique() == len(REFERENCE_NODES)
    usable = set(complete_hours[complete_hours].index)
    dropped = int(raw["utc"].nunique() - len(usable))
    if dropped:
        log.warning("%d: dropping %d hours with an incomplete hub set", year, dropped)
    raw = raw[raw["utc"].isin(usable)]

    hours = int(raw["utc"].nunique())
    if hours < MIN_HOURS_PER_YEAR:
        raise SystemExit(
            f"{year}: only {hours} complete DAM hours (< {MIN_HOURS_PER_YEAR}) — "
            "the component record is too sparse to stand for a monthly surface"
        )

    # MCE identity guard: one system reference per interval, asserted across
    # EVERY node read including the DLAPs (fail loud, never average an
    # inconsistent reference).
    spread = raw.groupby("utc")["mce"].agg(lambda s: s.max() - s.min())
    worst = float(spread.max())
    if worst > MCE_IDENTITY_TOL:
        raise SystemExit(
            f"{year}: MCE differs across nodes by up to {worst:.6f} $/MWh "
            f"(> {MCE_IDENTITY_TOL}) — the feed's system reference is not uniform"
        )
    log.info(
        "%d: %d usable DAM hours over %d nodes, MCE identity holds to %.2e",
        year,
        hours,
        raw["node"].nunique(),
        worst,
    )
    return raw


def _wide(frames: dict[int, pd.DataFrame]) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Return ``(mcl_by_utc_node, mce_by_utc, month_by_utc)`` over ``frames``.

    ``mcl`` carries ``NaN`` wherever a node did not print in a usable hour —
    the signal the per-month coverage rule reads.
    """
    joined = pd.concat(frames.values(), ignore_index=True)
    mcl = joined.pivot_table(index="utc", columns="node", values="mcl")
    mce = joined.groupby("utc")["mce"].mean()
    month = joined.groupby("utc")["month"].first()
    return mcl, mce.loc[mcl.index], month.loc[mcl.index]


def _month_sources(
    mcl: pd.DataFrame, month: pd.Series, zone: str
) -> dict[int, tuple[str, bool]]:
    """Resolve, per month, the node ``zone``'s deviation is measured at.

    Applies the PRECHECK-caiso165 §2.2 coverage rule: the zone's own source
    node is used iff it printed in at least :data:`MIN_MONTH_COVERAGE` of the
    month's usable hours; otherwise the month falls back to
    :data:`FALLBACK_NODE` and is flagged interpolated.

    **Source homogeneity within a year label** (PRECHECK-caiso166 §5, declared
    before the solve). A zone's 12 months within one year label must ALL come
    from the same node: if any month fails the coverage rule, every month of
    that zone-label falls back. A vector whose January is measured at
    ``DLAP_SCE`` and whose February is measured at ``TH_SP15_GEN`` is not one
    zone's seasonal shape — it is two different locations stitched together,
    and the LP would read the source switch as a real seasonal loss signal
    (a corridor lossy in January and lossless the rest of the year, driven by
    the report's retention boundary rather than by physics). This is rule 14
    ``[R-ACCURATE]``'s misalignment clause: the January value is genuine, but
    used *literally* alongside eleven months of another node it makes the
    result LESS reflective of reality, so the coherent reconciled vector is
    preferred. It self-heals — once retention covers every month the whole
    label becomes measured with no edit here — and it consults no model output.

    On the caiso-166 data this binds on the pooled (``year = 0``) forecast-
    analogue rows ONLY: the per-year backcast rows are already homogeneous
    (2023 fully interpolated, 2024 and 2025 fully measured), so the backcast
    A/B sees exactly zero bytes of it.

    Args:
        mcl: Usable-hour x node MCL frame (``NaN`` where a node is absent).
        month: Usable-hour -> Pacific month.
        zone: Model zone name, a key of :data:`ZONE_SOURCE`.

    Returns:
        Mapping ``month -> (node, interpolated)``.
    """
    primary, fallback = ZONE_SOURCE[zone]
    out: dict[int, tuple[str, bool]] = {}
    for m, idx in month.groupby(month).groups.items():
        if fallback is None:
            out[int(m)] = (primary, False)
            continue
        if primary not in mcl.columns:
            out[int(m)] = (fallback, True)
            continue
        coverage = float(mcl.loc[idx, primary].notna().mean())
        measured = coverage >= MIN_MONTH_COVERAGE
        out[int(m)] = (primary if measured else fallback, not measured)
    if fallback is not None and any(interp for _, interp in out.values()):
        out = {m: (fallback, True) for m in out}
    return out


def _deviation_rows(frames: dict[int, pd.DataFrame], year_label: int) -> list[dict]:
    """``dev = sum(MCL_z) / sum(MCE)`` per (model zone, month) over ``frames``.

    Numerator and denominator are taken over the SAME hour set — the hours the
    zone's resolved source node actually printed in — so a partially-covered
    month is the measured ratio rather than a mismatched one.
    """
    mcl, mce, month = _wide(frames)
    rows: list[dict] = []
    for zone in ZONE_SOURCE:
        sources = _month_sources(mcl, month, zone)
        for m, idx in month.groupby(month).groups.items():
            node, interpolated = sources[int(m)]
            series = mcl.loc[idx, node].dropna()
            rows.append(
                {
                    "iso": "CAISO",
                    "zone": zone,
                    "year": year_label,
                    "month": int(m),
                    "df_deviation": round(
                        float(series.sum()) / float(mce.loc[series.index].sum()), 8
                    ),
                    "n_hours": int(len(series)),
                    "interpolated": interpolated,
                }
            )
    return rows


def _acceptance(frames: dict[int, pd.DataFrame], surface: pd.DataFrame) -> int:
    """Offline B1-analogue gate: implied $ separation vs measured dMCL.

    Both sides are computed month by month at the node the surface actually
    used for that month, then hour-weighted — so an interpolated month is
    benchmarked against the node it interpolated from, never against a measured
    DLAP the surface did not read.
    """
    print("=" * 88)
    print("caiso-166 derive acceptance — implied dual separation vs measured dMCL")
    print(f"band [{ACCEPT_BAND[0]}x, {ACCEPT_BAND[1]}x]")
    print("=" * 88)
    n_pass = n_total = 0
    for year, frame in frames.items():
        mcl, mce, month = _wide({year: frame})
        sub = surface[surface["year"] == year]
        dev = sub.pivot(index="month", columns="zone", values="df_deviation")
        groups = month.groupby(month).groups

        for near, far in ACCEPTANCE_PAIRS:
            src_near = _month_sources(mcl, month, near)
            src_far = _month_sources(mcl, month, far)
            num_meas = num_impl = denom = 0.0
            for m, idx in groups.items():
                m = int(m)
                both = mcl.loc[idx, [src_near[m][0], src_far[m][0]]].dropna()
                if both.empty:
                    continue
                d = (both[src_near[m][0]] - both[src_far[m][0]]).to_numpy()
                ratio = (1.0 + dev.at[m, near]) / (1.0 + dev.at[m, far]) - 1.0
                h = float(len(both))
                num_meas += float(d.sum())
                num_impl += h * float(mce.loc[both.index].mean()) * ratio
                denom += h
            measured = num_meas / denom
            implied = num_impl / denom
            rel = implied / measured if abs(measured) > 1e-9 else float("nan")
            ok = ACCEPT_BAND[0] <= rel <= ACCEPT_BAND[1]
            interp = sum(1 for m in groups if src_far[int(m)][1])
            n_total += 1
            n_pass += int(ok)
            print(
                f"  {year} {near:>10s} vs {far:<10s} measured dMCL "
                f"{measured:+7.3f}  implied {implied:+7.3f}  ratio {rel:5.2f}x  "
                f"{'PASS' if ok else 'FAIL'}"
                + (f"   [{interp}/12 far-zone months interpolated]" if interp else "")
            )
    print(f"\nacceptance: {n_pass}/{n_total} pair-years in band")
    return 0 if n_pass == n_total else 1


def main(argv: list[str] | None = None) -> int:
    """Derive and write the CAISO loss surface; return 0 on success."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--acceptance", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)

    frames = {year: _load_components(year) for year in YEARS}

    rows: list[dict] = []
    for year in YEARS:
        rows.extend(_deviation_rows({year: frames[year]}, year))
    rows.extend(_deviation_rows(frames, POOLED_YEAR))
    surface = pd.DataFrame(rows).sort_values(["year", "zone", "month"])

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    surface.to_csv(out_path, index=False)
    log.info(
        "wrote %s (%d rows: %d zones x %d months x %d year labels)",
        out_path,
        len(surface),
        surface["zone"].nunique(),
        surface["month"].nunique(),
        surface["year"].nunique(),
    )

    annual = (
        surface[surface["year"] != POOLED_YEAR]
        .groupby(["year", "zone"])["df_deviation"]
        .mean()
        .unstack(0)
    )
    print("\nmean monthly df_deviation by zone-year (dimensionless):")
    print(annual.round(5).to_string())

    interp = (
        surface[surface["year"] != POOLED_YEAR]
        .groupby(["year", "zone"])["interpolated"]
        .sum()
        .unstack(0)
    )
    print("\ninterpolated month-cells by zone-year (of 12):")
    print(interp.to_string())

    if args.acceptance:
        return _acceptance(frames, surface)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
