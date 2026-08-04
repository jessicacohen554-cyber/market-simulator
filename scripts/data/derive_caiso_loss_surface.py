"""Derive the CAISO per-zone monthly marginal delivery-factor (loss) surface.

The caiso-164 derive (frozen, CLAUDE.md rule 23 ``[R-FROZEN-DERIVE]`` —
re-derives ONLY when its source data updates; charter
``results/calibration/PRECHECK-caiso164-zonal-loss-surface-2026-08-04.md``).
Reads the committed CAISO day-ahead hub component record
(``data/raw/lmp-data/CAISO/CAISO_dam_hourly_<year>.csv``, CAISO OASIS
``PRC_LMP`` DAM rows for the three ``TH_*_GEN-APND`` trading hubs) and emits the
dimensionless per-zone (month) marginal delivery-factor deviation surface
consumed by the gated ``ScenarioConfig.caiso_zonal_loss_surface`` LP mechanism:

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

**Zones — three measured, two reconciled, and that is stated not hidden.**
CAISO publishes a component-decomposed price at three trading hubs, and the
model carries five CAISO load zones:

===============  ====================  =============================
model zone       source node           interpolated
===============  ====================  =============================
``NP15``         ``TH_NP15_GEN-APND``  False — its own hub
``ZP26``         ``TH_ZP26_GEN-APND``  False — its own hub
``SP15_rest``    ``TH_SP15_GEN-APND``  False — the SP15 generation hub IS
                                       the SP15 desert/Kern generation belt
                                       this zone represents
``LA_BASIN``     ``TH_SP15_GEN-APND``  **True** — a load pocket inside SP15
``SDGE``         ``TH_SP15_GEN-APND``  **True** — a load pocket inside SP15
===============  ====================  =============================

``LA_BASIN`` and ``SDGE`` are load pockets whose true delivery factors differ
from the SP15 generation hub's; CAISO's nodal/DLAP component record is NOT in
``data/raw``, so there is no measured value for them. Rather than invent one
(which would be a fitted scalar, rule 5 ``[R-NO-MAGIC]``), they inherit the
SP15 hub's measured deviation and are flagged ``interpolated=True`` — the rule
14 ``[R-ACCURATE]`` "reconciled version of the real data" clause for data
defined on a different boundary than our zones, recorded rather than buried.
The quantity under test (the NP15 / ZP26 / SP15 north-south gradient) is
carried entirely by the three measured hubs; the two reconciled zones sit
behind the SP15 gateway. Closing them properly needs a CAISO DLAP component
intake — filed as a data blocker in the caiso-164 finding.

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
(the miso-76 B1 band, applied to CAISO's own measured quantities). This
validates the derive -> loss-fraction -> dual-ratio -> $ separation algebra
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

#: Model zone -> the CAISO trading hub its deviation is measured at, and
#: whether that assignment is a reconciliation rather than the zone's own
#: measured node (see the module docstring's zone table).
ZONE_SOURCE: dict[str, tuple[str, bool]] = {
    "NP15": ("TH_NP15_GEN-APND", False),
    "ZP26": ("TH_ZP26_GEN-APND", False),
    "SP15_rest": ("TH_SP15_GEN-APND", False),
    "LA_BASIN": ("TH_SP15_GEN-APND", True),
    "SDGE": ("TH_SP15_GEN-APND", True),
}

#: Acceptance-mode benchmark pairs: (near, far) model zones whose measured
#: delta-MCL the implied dual separation is gated against. These are the two
#: north-south gradients caiso-164 §0 measured, i.e. the quantity the mechanism
#: is being installed to represent — not a favourable subset.
ACCEPTANCE_PAIRS: tuple[tuple[str, str], ...] = (
    ("NP15", "ZP26"),
    ("NP15", "SP15_rest"),
)

#: The miso-76 B1 acceptance band, applied to CAISO's own measured quantities.
ACCEPT_BAND = (0.5, 1.5)

#: MCE is published per row and is identical across nodes per interval up to
#: the feed's rounding; above this the identity is broken and the derive must
#: fail rather than average an inconsistent reference.
MCE_IDENTITY_TOL = 1e-4

#: A year needs near-full DAM coverage before its rows stand for a month.
MIN_HOURS_PER_YEAR = 8000


def _load_components(year: int) -> pd.DataFrame:
    """Load one year of CAISO DAM hub components, keyed on the local month.

    Returns a long frame with columns ``utc``, ``month``, ``node``, ``mcl``,
    ``mce``, ``mcc``, ``lmp``.

    The month is taken on the **Pacific** clock, not GMT: the file is
    GMT-stamped and a GMT month boundary splits a Pacific month 7-8 hours off,
    which would smear each month's surface into its neighbour.
    """
    path = DAM_DIR / f"CAISO_dam_hourly_{year}.csv"
    if not path.is_file():
        raise SystemExit(f"no CAISO DAM component file at {path}")
    raw = pd.read_csv(path)
    raw = raw[raw["node"].isin({src for src, _ in ZONE_SOURCE.values()})].copy()
    if raw.empty:
        raise SystemExit(f"{path} carries no TH_*_GEN-APND hub rows")
    raw["utc"] = pd.to_datetime(raw["interval_start_gmt"], utc=True)
    local = raw["utc"].dt.tz_convert("America/Los_Angeles")
    raw = raw[local.dt.year == year].copy()
    raw["month"] = local[local.dt.year == year].dt.month
    raw = raw.rename(columns={"MCL": "mcl", "MCE": "mce", "MCC": "mcc", "LMP": "lmp"})

    # Every hub must print in an hour before that hour is usable: a month whose
    # denominator (MCE) came from a different hour set than its numerator
    # (MCL) is not the measured ratio.
    n_nodes = raw["node"].nunique()
    complete = raw.groupby("utc")["node"].transform("nunique") == n_nodes
    dropped = int((~complete).sum())
    if dropped:
        log.warning(
            "%d: dropping %d hub-hours with an incomplete hub set", year, dropped
        )
    raw = raw[complete]

    hours = int(raw["utc"].nunique())
    if hours < MIN_HOURS_PER_YEAR:
        raise SystemExit(
            f"{year}: only {hours} complete DAM hours (< {MIN_HOURS_PER_YEAR}) — "
            "the component record is too sparse to stand for a monthly surface"
        )

    # MCE identity guard: one system reference per interval (fail loud, never
    # average an inconsistent reference).
    spread = raw.groupby("utc")["mce"].agg(lambda s: s.max() - s.min())
    worst = float(spread.max())
    if worst > MCE_IDENTITY_TOL:
        raise SystemExit(
            f"{year}: MCE differs across hubs by up to {worst:.6f} $/MWh "
            f"(> {MCE_IDENTITY_TOL}) — the feed's system reference is not uniform"
        )
    log.info(
        "%d: %d complete DAM hours, MCE identity holds to %.2e", year, hours, worst
    )
    return raw


def _deviation_rows(frames: dict[int, pd.DataFrame], year_label: int) -> list[dict]:
    """``dev = sum(MCL_z) / sum(MCE)`` per (model zone, month) over ``frames``."""
    joined = pd.concat(frames.values(), ignore_index=True)
    # One MCE per interval (the identity guard above proves they agree).
    mce = joined.groupby(["utc", "month"], as_index=False)["mce"].mean()
    mce_sum = mce.groupby("month")["mce"].sum()

    rows: list[dict] = []
    for zone, (node, interpolated) in ZONE_SOURCE.items():
        block = joined[joined["node"] == node]
        for month, part in block.groupby("month"):
            rows.append(
                {
                    "iso": "CAISO",
                    "zone": zone,
                    "year": year_label,
                    "month": int(month),
                    "df_deviation": round(
                        float(part["mcl"].sum()) / float(mce_sum.loc[month]), 8
                    ),
                    "n_hours": int(part["utc"].nunique()),
                    "interpolated": interpolated,
                }
            )
    return rows


def _acceptance(frames: dict[int, pd.DataFrame], surface: pd.DataFrame) -> int:
    """Offline B1-analogue gate: implied $ separation vs measured mean dMCL."""
    print("=" * 82)
    print("caiso-164 derive acceptance — implied dual separation vs measured dMCL")
    print(f"band [{ACCEPT_BAND[0]}x, {ACCEPT_BAND[1]}x]")
    print("=" * 82)
    n_pass = n_total = 0
    for year, frame in frames.items():
        wide = frame.pivot_table(index="utc", columns="node", values="mcl")
        mce = frame.groupby(["utc", "month"], as_index=False)["mce"].mean()
        mce_m = mce.groupby("month")["mce"].mean()
        hours_m = mce.groupby("month")["mce"].size()
        sub = surface[surface["year"] == year]
        dev = sub.pivot(index="month", columns="zone", values="df_deviation")

        for near, far in ACCEPTANCE_PAIRS:
            measured = float(
                (wide[ZONE_SOURCE[near][0]] - wide[ZONE_SOURCE[far][0]]).mean()
            )
            ratio_m = (1.0 + dev[near]) / (1.0 + dev[far]) - 1.0
            implied = float((hours_m * mce_m * ratio_m).sum() / hours_m.sum())
            rel = implied / measured if abs(measured) > 1e-9 else float("nan")
            ok = ACCEPT_BAND[0] <= rel <= ACCEPT_BAND[1]
            n_total += 1
            n_pass += int(ok)
            print(
                f"  {year} {near:>10s} vs {far:<10s} measured dMCL "
                f"{measured:+7.3f}  implied {implied:+7.3f}  ratio {rel:5.2f}x  "
                f"{'PASS' if ok else 'FAIL'}"
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

    if args.acceptance:
        return _acceptance(frames, surface)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
