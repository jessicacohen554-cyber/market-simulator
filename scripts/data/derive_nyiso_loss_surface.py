"""Derive the NYISO per-zone monthly marginal delivery-factor (loss) surface.

The nyiso-159 derive (frozen on filing, CLAUDE.md rule 23 ``[R-FROZEN-DERIVE]``
— re-derives ONLY when its source data updates), chartered by
``results/calibration/PREREG-nyiso159-zonal-loss-surface-2026-08-30.md`` §2 on
the phase-0 MATERIAL verdict
(``results/calibration/FINDING-nyiso159-loss-surface-phase0-2026-08-30.md``).

Reads the curated NYISO real-time zonal LBMP component record
(``data/clean/lmp/NYISO/RTM/lmp_<year>.parquet`` — NYISO MIS P-24A 5-minute RT
zonal LBMPs, hourly means, curated by the frozen ``scripts/data/curate_lmp.py``
contract; regeneration = ``scripts/data/fetch_nyiso_zonal_lmp.py --kind rt`` →
``curate_lmp.py`` → this script) and emits the dimensionless per-zone (month)
marginal delivery-factor deviation surface consumed by the gated
``ScenarioConfig.nyiso_zonal_loss_surface`` LP mechanism::

    data/raw/iso-specific-transmission/NYISO_loss_surface.csv
    columns: iso, zone, year, month, df_deviation, n_hours, interpolated

**The physics.** A NYISO LBMP decomposes as ``LBMP_z = E + MCL_z - MCC_z``
(NYISO MST §17.1 / Manual 12: losses ADD, congestion SUBTRACTS — NYISO's
posted sign convention), with the marginal cost of losses ``MCL_z`` the value
of losses incurred delivering a marginal MW to zone ``z`` relative to the
system reference. Same decomposition PJM writes ``MEC + MCC + MLC`` and CAISO
writes ``MCE + MCC + MCL``, so the derive target is the same dimensionless
deviation the frozen MISO/PJM/CAISO derives use::

    dev_z,m = sum(MCL_z,t) / sum(E_t)   over the month's hours

— the reference-energy-weighted estimator, chosen so the surface reproduces
the measured total MCL exactly when re-multiplied by the measured E series.
Nothing here reads a model output, a residual, or a scoring target: this is a
measured physical network property that regenerates for any year from the same
published feed and responds to changed grid conditions (rule 13
``[R-MEASURED]``).

**Rule 25 ``[R-ISO-SCOPE]``.** Every number is derived from NYISO's own posted
component record and written to NYISO's own file. Nothing crosses from the
MISO/PJM/CAISO analogues, whose verdicts are their own (rule 28(d)); the only
thing shared with them is the estimator's algebra.

**Basis: REAL-TIME — a declared, deliberate divergence from CAISO's DA basis**
(PREREG-nyiso159 §2). NYISO's scored C3a/C3b target is the RT load-weighted
price; the committed component contract series is RT; and NYISO's RTD/RTC is a
full-network optimization whose posted MCL is the marginal-loss object itself.
PJM/CAISO derive from their DA records for their own stated reasons — per-ISO
identification is per-ISO (rule 25).

**Zone aggregation: model zone = SIMPLE MEAN of member A–K zones** — the
``derive_actual_lmp.NYISO_ZONE_MAP`` / ``nyiso_zone_hourly`` convention the
scoring actuals themselves use, so the surface and the scored target measure
one representation. Unlike CAISO there is no fallback/coverage machinery: the
NYISO MIS grid posts every zone in every interval, so every cell is measured
(``interpolated`` is always ``False``; the column is kept for the shared
loader/schema contract).

**The reference E is recovered, not read.** NYISO's zone files post LBMP, MCL
and MCC; the reference energy price is recovered per zone-hour as
``E = LBMP - MCL + MCC`` and asserted uniform across the eleven internal zones
to :data:`E_IDENTITY_MAX` — the publication-rounding class bound (components
post to $0.01, so the recovered identity can carry up to ~1.5 cents of
stacked rounding; phase-0 §1 measured max $0.015, p99 $0.0075). Above the
bound the decomposition is not usable as published and the derive fails loud.

**Per-year + pooled rows.** Backcast year Y consumes year-Y's own monthly
surface — a same-year measured *physical network property*, the CEMS-rate
admissibility class (rule 13). The pooled rows (``year = 0``, all train years)
are the forecast-mode forward analogue — the stable multi-year network
property that regenerates from rolling history — and are NOT used by the
backcast A/B.

**Acceptance mode (run BEFORE any solve — PREREG-nyiso159 §3).**
``--acceptance`` recomputes, per adjacent chain pair-year, the separation the
LP's dual ratios would imply at the measured E —
``sum_m h_m x E_m x ((1+dev_y,m)/(1+dev_x,m) - 1) / sum_m h_m`` — and gates it
against the ``[0.5x, 1.5x]`` band of the measured mean dMCL for that pair-year
(the miso-76 B1 band, applied to NYISO's own measured quantities). The four
pairs are the four internal chain links the mechanism would split
(UW→CH, CH→LH, LH→NYC, NYC→LI); **all 12 pair-years in band is the
precondition to solve; any miss is a stop-the-line** — file the finding, spend
no solve. This validates the derive → loss-fraction → dual-ratio → $
separation algebra offline; the LP A/B remains the real test.

Usage:
    PYTHONPATH=.:src python scripts/data/derive_nyiso_loss_surface.py
    PYTHONPATH=.:src python scripts/data/derive_nyiso_loss_surface.py --acceptance
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from market_sim.config.paths import CLEAN_DIR, ISO_TRANSMISSION_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("derive_nyiso_loss_surface")

OUT = ISO_TRANSMISSION_DIR / "NYISO_loss_surface.csv"
RTM_DIR = CLEAN_DIR / "lmp" / "NYISO" / "RTM"

#: Train-window years the surface carries per-year rows for. Rule 22
#: ``[R-HOLDOUT]``: 2023-2025 only — the holdout spend freeze is active and no
#: other year may be read, scored or registered.
YEARS: tuple[int, ...] = (2023, 2024, 2025)

#: Sentinel year for the pooled (forecast-analogue) rows.
POOLED_YEAR = 0

#: Model zone -> member NYISO load zones (A-K), the scoring crosswalk
#: ``derive_actual_lmp.NYISO_ZONE_MAP`` verbatim; aggregation is the SIMPLE
#: MEAN of members, the ``nyiso_zone_hourly`` convention the scored actuals
#: use, so the surface measures the same representation the rubric scores.
ZONE_MAP: dict[str, tuple[str, ...]] = {
    "Upstate_West": ("WEST", "GENESE", "CENTRL", "NORTH", "MHK VL"),
    "Capital_Hudson": ("CAPITL",),
    "Lower_Hudson": ("HUD VL", "MILLWD", "DUNWOD"),
    "NYC": ("N.Y.C.",),
    "Long_Island": ("LONGIL",),
}

#: Acceptance-mode benchmark pairs: the four adjacent (near, far) chain pairs
#: — exactly the four internal links ``apply_nyiso_zonal_loss_links`` would
#: split, so the gate benchmarks precisely the separations the mechanism
#: creates (PREREG-nyiso159 §3).
ACCEPTANCE_PAIRS: tuple[tuple[str, str], ...] = (
    ("Upstate_West", "Capital_Hudson"),
    ("Capital_Hudson", "Lower_Hudson"),
    ("Lower_Hudson", "NYC"),
    ("NYC", "Long_Island"),
)

#: The miso-76 B1 acceptance band, applied to NYISO's own measured quantities.
ACCEPT_BAND = (0.5, 1.5)

#: Cross-zone spread bound on the recovered reference energy price E — the
#: publication-rounding class (rule 5 ``[R-NO-MAGIC]``: components post to
#: $0.01, so the three-term identity stacks to ~1.5 cents worst-case; phase-0
#: §1 measured max $0.015, p99 $0.0075 across all 36 months). NOT a tunable:
#: above this the posted decomposition is internally inconsistent and the
#: derive must fail rather than average an inconsistent reference.
E_IDENTITY_MAX = 0.02

#: A year needs near-full RT coverage before its rows stand for a month —
#: the frozen annual guard shared with the MISO/PJM/CAISO derives.
MIN_HOURS_PER_YEAR = 8000

_MEMBERS: tuple[str, ...] = tuple(m for ms in ZONE_MAP.values() for m in ms)


def _zone_frames(year: int) -> dict[str, pd.DataFrame | pd.Series]:
    """Load one year of NYISO RT components aggregated to model zones.

    Returns ``{"mcl": DataFrame[zone], "e": Series, "month": Series}`` indexed
    by UTC hour, restricted to the year's usable hours (all eleven internal
    A-K zones printing). ``e`` is the recovered reference energy price
    (cross-zone mean of ``LBMP - MCL + MCC``), asserted uniform to
    :data:`E_IDENTITY_MAX`. The month is taken on the LOCAL (Eastern) clock —
    the posted ``interval_start_local`` — because a UTC month boundary would
    smear 4-5 hours of each month's surface into its neighbour.
    """
    path = RTM_DIR / f"lmp_{year}.parquet"
    if not path.is_file():
        raise SystemExit(
            f"no curated NYISO RT record at {path} — regenerate with "
            "scripts/data/fetch_nyiso_zonal_lmp.py --kind rt + "
            "scripts/data/curate_lmp.py"
        )
    df = pd.read_parquet(path)
    df = df[df["zone"].isin(_MEMBERS)].copy()
    if df.empty:
        raise SystemExit(f"{path} carries no internal A-K zone rows")

    piv = {
        c: df.pivot_table(index="interval_start_utc", columns="zone", values=c)
        for c in ("lmp_usd_per_mwh", "loss_usd_per_mwh", "congestion_usd_per_mwh")
    }
    # Usable hour = every member zone printing (the CAISO reference-set rule,
    # with NYISO's full grid as the reference set).
    complete = piv["lmp_usd_per_mwh"].notna().all(axis=1)
    for name in piv:
        piv[name] = piv[name][complete]
    dropped = int((~complete).sum())
    if dropped:
        log.warning("%d: dropping %d hours with an incomplete zone set", year, dropped)

    hours = int(len(piv["lmp_usd_per_mwh"]))
    if hours < MIN_HOURS_PER_YEAR:
        raise SystemExit(
            f"{year}: only {hours} complete RT hours (< {MIN_HOURS_PER_YEAR}) — "
            "the component record is too sparse to stand for a monthly surface"
        )

    # Recovered reference: E = LBMP - MCL + MCC per zone-hour, uniform across
    # zones up to publication rounding (fail loud past the rounding class).
    e_by_zone = (
        piv["lmp_usd_per_mwh"] - piv["loss_usd_per_mwh"] + piv["congestion_usd_per_mwh"]
    )
    spread = e_by_zone.max(axis=1) - e_by_zone.min(axis=1)
    worst = float(spread.max())
    if worst > E_IDENTITY_MAX:
        raise SystemExit(
            f"{year}: recovered reference E differs across zones by up to "
            f"${worst:.4f} (> {E_IDENTITY_MAX}) — the posted decomposition is "
            "not usable as published"
        )

    month = (
        df.drop_duplicates("interval_start_utc")
        .set_index("interval_start_utc")["interval_start_local"]
        .dt.month.reindex(piv["lmp_usd_per_mwh"].index)
        .astype(int)
    )
    mcl = pd.DataFrame(
        {
            z: piv["loss_usd_per_mwh"][list(ms)].mean(axis=1)
            for z, ms in ZONE_MAP.items()
        }
    )
    log.info(
        "%d: %d usable RT hours, E identity holds to $%.4f (bound $%.2f)",
        year,
        hours,
        worst,
        E_IDENTITY_MAX,
    )
    return {"mcl": mcl, "e": e_by_zone.mean(axis=1), "month": month}


def _deviation_rows(
    frames: dict[int, dict[str, pd.DataFrame | pd.Series]], year_label: int
) -> list[dict]:
    """``dev = sum(MCL_z) / sum(E)`` per (model zone, month) over ``frames``."""
    mcl = pd.concat([f["mcl"] for f in frames.values()])
    e = pd.concat([f["e"] for f in frames.values()])
    month = pd.concat([f["month"] for f in frames.values()])
    rows: list[dict] = []
    for m in range(1, 13):
        sel = (month == m).to_numpy()
        e_sum = float(e[sel].sum())
        if e_sum <= 0.0:
            raise SystemExit(
                f"month {m} (label {year_label}): non-positive reference-energy "
                f"sum {e_sum:.2f} — the estimator's denominator is unusable"
            )
        for zone in ZONE_MAP:
            rows.append(
                {
                    "iso": "NYISO",
                    "zone": zone,
                    "year": year_label,
                    "month": m,
                    "df_deviation": round(float(mcl.loc[sel, zone].sum()) / e_sum, 8),
                    "n_hours": int(sel.sum()),
                    "interpolated": False,
                }
            )
    return rows


def _acceptance(
    frames: dict[int, dict[str, pd.DataFrame | pd.Series]], surface: pd.DataFrame
) -> int:
    """Offline B1-analogue gate: implied dual separation vs measured dMCL.

    PREREG-nyiso159 §3: all 12 pair-years (4 adjacent chain pairs x 3 years)
    must sit in the band; ANY miss is a stop-the-line — file the finding,
    spend no solve.
    """
    print("=" * 88)
    print("nyiso-159 derive acceptance — implied dual separation vs measured dMCL")
    print(f"band [{ACCEPT_BAND[0]}x, {ACCEPT_BAND[1]}x] of measured mean dMCL")
    print("=" * 88)
    n_pass = n_total = 0
    for year, f in frames.items():
        mcl, e, month = f["mcl"], f["e"], f["month"]
        dev = surface[surface["year"] == year].pivot(
            index="month", columns="zone", values="df_deviation"
        )
        for near, far in ACCEPTANCE_PAIRS:
            num_impl = denom = 0.0
            for m in range(1, 13):
                sel = (month == m).to_numpy()
                h = float(sel.sum())
                ratio = (1.0 + dev.at[m, far]) / (1.0 + dev.at[m, near]) - 1.0
                num_impl += h * float(e[sel].mean()) * ratio
                denom += h
            measured = float((mcl[far] - mcl[near]).mean())
            implied = num_impl / denom
            rel = implied / measured if abs(measured) > 1e-9 else float("nan")
            ok = ACCEPT_BAND[0] <= rel <= ACCEPT_BAND[1]
            n_total += 1
            n_pass += int(ok)
            print(
                f"  {year} {near:>14s} -> {far:<14s} measured dMCL "
                f"{measured:+7.3f}  implied {implied:+7.3f}  ratio {rel:5.2f}x  "
                f"{'PASS' if ok else 'FAIL'}"
            )
    print(f"\nacceptance: {n_pass}/{n_total} pair-years in band")
    return 0 if n_pass == n_total else 1


def main(argv: list[str] | None = None) -> int:
    """Derive and write the NYISO loss surface; return 0 on success."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--acceptance", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)

    frames = {year: _zone_frames(year) for year in YEARS}

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
        .reindex(list(ZONE_MAP))
    )
    print("\nmean monthly df_deviation by zone-year (dimensionless):")
    print(annual.round(5).to_string())

    if args.acceptance:
        return _acceptance(frames, surface)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
