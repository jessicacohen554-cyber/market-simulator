#!/usr/bin/env python
"""Clear a national CES against a campaign's premium legs — the UNIFORM-PRICE half of G-S2.

Zero-solve. Consumes only committed campaign artifacts; runs no LP and touches
no cache.

WHY THIS EXISTS (plan §2.2 G-S2). Every RPS/clean row in this model lives
inside ONE ISO's LP (``runner.py``, ``policy/rps.py``), so a national
certificate market cannot be cleared inside the dispatch. The national answer
is therefore BRACKETED by two representations, and the gap between them IS the
cross-ISO-trade uncertainty:

* **Uniform price** — one federal EAC premium applies everywhere, and each ISO
  responds with whatever clean share that premium buys it. Equivalent to
  UNCONSTRAINED cross-ISO credit trade: cheap abatement anywhere serves the
  national obligation. **This script computes that half**, from the premium
  ladder the campaign already solved.
* **Uniform share** — every ISO carries the national target as its own LP row
  and clears its own price. Equivalent to NO cross-ISO trade. That half is the
  ``federal_ces_target_by_year`` row (SCN-WS2a); this script reads its result
  in through ``--target-row-results`` and reports the two side by side.

Neither is "the" answer. A real national CES with a functioning certificate
market sits between them, and the spread is the honest uncertainty band on the
question "what does an X %-by-YEAR standard imply per ISO".

WHAT IT SOLVES. For each year, the smallest uniform premium ``p*`` in the
ladder's OBSERVED range at which

    Σ_ISO credited_MWh_ISO(p*)  >=  target(year) × Σ_ISO served_MWh_ISO(p*)

Both sides are interpolated per ISO from that ISO's own solved rungs, so an
ISO whose generation itself moves with the premium is handled correctly rather
than pinned at its BAU volume.

THE DENOMINATOR, STATED PLAINLY. ``served_MWh`` here is the model's TOTAL
MODELED GENERATION INCLUDING IMPORTS — exactly the denominator
``results/export.py::_summarize_year`` uses for ``clean_share``, so the
per-ISO shares this script reports ARE that ``clean_share``, with no re-basing
and no invented factor. A statutory CES obligates RETAIL SALES, which differ
from generation by T&D losses and net exports. No loss factor is applied
(there is no measured one in this repo to apply, and inventing one would be a
free parameter — rule 21 ``[R-DOF]``); the difference is reported as a
disclosure, not silently absorbed.

NO EXTRAPOLATION, EVER. The curve is only defined on the premiums the campaign
actually solved. A target unreachable at the highest solved rung reports
``NOT_REACHED`` with the attainable share; a target already met at the lowest
rung reports ``MET_AT_FLOOR`` and the premium is an UPPER BOUND, not an
estimate. Extending the answer past the ladder would be a fitted number
(rule 1 ``[R-STRUCT]``).

NEVER CALLED "NATIONAL" ON PARTIAL COVERAGE. The aggregate is labelled by the
ISOs actually present ("modeled system, N ISOs: ..."), the same rule
``scripts/collate_scenario_campaign.py`` follows for the six-ISO CO2 rollup
(G-E2). Two ISOs are two ISOs.

INPUT. One or more ``<iso>_clean_share_vs_premium.csv`` files written by
``scripts/report_ces_campaign.py`` (the campaign's committed headline frame).
Required columns: ``case``, ``year``, ``premium_usd_per_mwh``, ``clean_share``,
``generation_twh``.

Usage::

    python scripts/ces_national_clearing.py \\
        --headline results/scn-ws2-ladder/ercot/ces_report/ercot_clean_share_vs_premium.csv \\
        --headline results/scn-ws2-ladder/neiso/ces_report/neiso_clean_share_vs_premium.csv \\
        --target 0.80 \\
        --out-dir results/scn-ws2-ladder/national_clearing

    # with the uniform-share half once SCN-WS2a's target-row probe has landed:
    #   --target-row-results <csv with iso,year,clean_share[,premium_usd_per_mwh]>
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass, field
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

#: Columns a headline frame must carry for this script to read it.
REQUIRED_HEADLINE_COLUMNS = (
    "case",
    "year",
    "premium_usd_per_mwh",
    "clean_share",
    "generation_twh",
)

#: Tolerance on the clearing identity, as a fraction of the year's obligation.
#: Purely a floating-point guard on an exact piecewise-linear root — not a
#: tunable (rule 5 ``[R-NO-MAGIC]``: it exists so a root computed in double
#: precision is not reported as a miss by its own last bit).
CLEARING_TOLERANCE = 1e-9

#: Status vocabulary. ``CLEARED`` — the obligation is first met strictly inside
#: the solved ladder. ``MET_AT_FLOOR`` — already met at the lowest solved rung,
#: so that rung is an UPPER BOUND on the clearing premium. ``NOT_REACHED`` —
#: not met at the highest solved rung; no premium is reported.
STATUS_CLEARED = "CLEARED"
STATUS_MET_AT_FLOOR = "MET_AT_FLOOR"
STATUS_NOT_REACHED = "NOT_REACHED"


@dataclass(frozen=True)
class Rung:
    """One solved ladder point for one ISO-year.

    Attributes:
        premium: The leg's flat real premium in $/MWh.
        credited_mwh: Credit-weighted generation, ``clean_share × generation``.
        served_mwh: Total modeled generation including imports (the
            ``clean_share`` denominator; see the module docstring).
        case: The campaign case name the rung came from.
    """

    premium: float
    credited_mwh: float
    served_mwh: float
    case: str

    @property
    def share(self) -> float:
        """Return the rung's credited share (0.0 on a zero-generation year)."""
        return self.credited_mwh / self.served_mwh if self.served_mwh > 0.0 else 0.0


@dataclass
class ClearingResult:
    """The uniform-price clearing outcome for one year.

    Attributes:
        year: Solve year.
        target: The national clean-share target applied to that year.
        status: One of :data:`STATUS_CLEARED` / :data:`STATUS_MET_AT_FLOOR` /
            :data:`STATUS_NOT_REACHED`.
        premium: The clearing premium ($/MWh), or ``None`` when not reached.
        isos: The ISOs that contributed, sorted.
        system_share: Aggregate credited/served share at ``premium``.
        iso_shares: Per-ISO credited share at ``premium``.
        iso_credited_mwh: Per-ISO credited MWh at ``premium``.
        iso_served_mwh: Per-ISO served MWh at ``premium``.
        notes: Human-readable caveats attached to this year.
    """

    year: int
    target: float
    status: str
    premium: float | None
    isos: list[str]
    system_share: float
    iso_shares: dict[str, float]
    iso_credited_mwh: dict[str, float] = field(default_factory=dict)
    iso_served_mwh: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def share_spread_pp(self) -> float:
        """Return max−min per-ISO share in percentage points at ``premium``.

        The cross-ISO dispersion a UNIFORM PRICE produces. Under a uniform
        SHARE it is zero by construction, so this number is one direct reading
        of how much the two bracketing representations differ.
        """
        if not self.iso_shares:
            return 0.0
        return 100.0 * (max(self.iso_shares.values()) - min(self.iso_shares.values()))


def read_headline(path: Path) -> tuple[str, dict[int, list[Rung]]]:
    """Read one ``<iso>_clean_share_vs_premium.csv`` into per-year rungs.

    The ISO is taken from the filename stem's leading token (the ``prefix``
    ``report_ces_campaign.py`` writes with), upper-cased.

    Args:
        path: Path to the headline CSV.

    Returns:
        ``(iso, {year: [Rung, ...]})`` with each year's rungs sorted by premium.

    Raises:
        SystemExit: If a required column is missing, or two cases in the same
            ISO-year declare the same premium with different credited energy
            (an ambiguous ladder this script refuses to average away).
    """
    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit(f"{path}: no rows")
    missing = [c for c in REQUIRED_HEADLINE_COLUMNS if c not in rows[0]]
    if missing:
        raise SystemExit(
            f"{path}: missing required column(s) {missing}. This script reads the "
            f"headline frame written by scripts/report_ces_campaign.py."
        )
    iso = path.stem.split("_", 1)[0].upper()
    by_year: dict[int, dict[float, Rung]] = {}
    for row in rows:
        year = int(float(row["year"]))
        premium = float(row["premium_usd_per_mwh"])
        served = float(row["generation_twh"]) * 1e6  # TWh → MWh
        rung = Rung(
            premium=premium,
            credited_mwh=float(row["clean_share"]) * served,
            served_mwh=served,
            case=row["case"],
        )
        seen = by_year.setdefault(year, {})
        prior = seen.get(premium)
        if prior is not None and not _close(prior.credited_mwh, rung.credited_mwh):
            raise SystemExit(
                f"{path}: {iso} {year} has two cases at premium ${premium:g}/MWh "
                f"({prior.case!r}, {rung.case!r}) with different credited energy. "
                f"The ladder is ambiguous at that premium; this script will not "
                f"average them."
            )
        seen[premium] = rung
    return iso, {
        y: sorted(r.values(), key=lambda x: x.premium) for y, r in by_year.items()
    }


def _close(a: float, b: float) -> bool:
    """Return True when two energies agree to within the clearing tolerance."""
    scale = max(abs(a), abs(b), 1.0)
    return abs(a - b) <= CLEARING_TOLERANCE * scale


def interpolate(rungs: list[Rung], premium: float) -> tuple[float, float]:
    """Return ``(credited_mwh, served_mwh)`` at ``premium`` by linear interpolation.

    Both quantities are interpolated as ENERGIES, not as a ratio, so the
    aggregate constraint stays linear between rungs and its root is exact.

    Args:
        rungs: That ISO-year's rungs, sorted by premium (>= 1).
        premium: The premium to evaluate at. Must lie within the rungs' range —
            this function never extrapolates.

    Returns:
        ``(credited_mwh, served_mwh)``.

    Raises:
        ValueError: If ``premium`` is outside the solved range, or ``rungs`` is
            empty.
    """
    if not rungs:
        raise ValueError("no rungs to interpolate")
    lo, hi = rungs[0].premium, rungs[-1].premium
    if premium < lo - CLEARING_TOLERANCE or premium > hi + CLEARING_TOLERANCE:
        raise ValueError(
            f"premium ${premium:g}/MWh is outside the solved ladder "
            f"[${lo:g}, ${hi:g}] — this script does not extrapolate"
        )
    for left, right in zip(rungs, rungs[1:], strict=False):
        if left.premium <= premium <= right.premium:
            span = right.premium - left.premium
            w = 0.0 if span <= 0.0 else (premium - left.premium) / span
            return (
                left.credited_mwh + w * (right.credited_mwh - left.credited_mwh),
                left.served_mwh + w * (right.served_mwh - left.served_mwh),
            )
    # Single-rung ladder, or exactly at an endpoint of a degenerate range.
    nearest = rungs[0] if premium <= lo else rungs[-1]
    return nearest.credited_mwh, nearest.served_mwh


def _residual(
    year_rungs: dict[str, list[Rung]], premium: float, target: float
) -> float:
    """Return ``Σ credited − target × Σ served`` at ``premium`` (MWh).

    Non-negative means the uniform premium meets the obligation.
    """
    credited = served = 0.0
    for rungs in year_rungs.values():
        c, s = interpolate(rungs, premium)
        credited += c
        served += s
    return credited - target * served


def clear_year(
    year: int,
    year_rungs: dict[str, list[Rung]],
    target: float,
) -> ClearingResult:
    """Solve for the smallest uniform premium meeting ``target`` in one year.

    The aggregate residual is piecewise-linear in the premium with breakpoints
    at the union of the ISOs' rung premiums, so the root is found exactly by
    scanning breakpoints left to right and interpolating the first
    negative→non-negative crossing. Left to right, so the SMALLEST clearing
    premium is returned even if the residual is non-monotone (it can be: an
    ISO's served energy may itself rise with the premium).

    Args:
        year: The solve year.
        year_rungs: ``{iso: [Rung, ...]}`` for that year, each sorted.
        target: National clean-share target for that year, in [0, 1].

    Returns:
        The :class:`ClearingResult`, whose ``status`` says whether a premium
        was found inside the solved ladder.
    """
    isos = sorted(year_rungs)
    # Common support: no ISO is extrapolated, so the searchable range is the
    # intersection of the ladders.
    lo = max(r[0].premium for r in year_rungs.values())
    hi = min(r[-1].premium for r in year_rungs.values())
    notes: list[str] = []
    ladders = {iso: (r[0].premium, r[-1].premium) for iso, r in year_rungs.items()}
    if len({v for v in ladders.values()}) > 1:
        notes.append(
            "ISO ladders do not span the same premium range "
            + ", ".join(f"{i}=[${a:g},${b:g}]" for i, (a, b) in sorted(ladders.items()))
            + f"; the search is confined to their intersection [${lo:g}, ${hi:g}]."
        )
    if lo > hi:
        return ClearingResult(
            year=year,
            target=target,
            status=STATUS_NOT_REACHED,
            premium=None,
            isos=isos,
            system_share=0.0,
            iso_shares={},
            notes=notes
            + ["The ISO ladders share no common premium; nothing can be cleared."],
        )

    breakpoints = sorted(
        {
            p
            for rungs in year_rungs.values()
            for r in rungs
            if lo <= (p := r.premium) <= hi
        }
        | {lo, hi}
    )
    if _residual(year_rungs, lo, target) >= -CLEARING_TOLERANCE:
        return _result_at(
            year,
            year_rungs,
            target,
            lo,
            STATUS_MET_AT_FLOOR,
            isos,
            notes
            + [
                f"The obligation is already met at the ladder's lowest common rung "
                f"(${lo:g}/MWh), so that premium is an UPPER BOUND on the clearing "
                f"price, not an estimate of it. The true clearing premium is below "
                f"the solved range and this script does not extrapolate to find it."
            ],
        )
    for left, right in zip(breakpoints, breakpoints[1:], strict=False):
        f_left = _residual(year_rungs, left, target)
        f_right = _residual(year_rungs, right, target)
        if f_left < 0.0 <= f_right:
            span = f_right - f_left
            root = right if span <= 0.0 else left + (right - left) * (-f_left / span)
            return _result_at(
                year, year_rungs, target, root, STATUS_CLEARED, isos, notes
            )
    attainable = _share_at(year_rungs, hi)
    return ClearingResult(
        year=year,
        target=target,
        status=STATUS_NOT_REACHED,
        premium=None,
        isos=isos,
        system_share=attainable,
        iso_shares={
            iso: _iso_share(rungs, hi) for iso, rungs in sorted(year_rungs.items())
        },
        notes=notes
        + [
            f"Not met at the ladder's highest common rung (${hi:g}/MWh), where the "
            f"modeled-system share reaches {attainable:.4f} against a target of "
            f"{target:.4f}. No premium is reported: extrapolating past the solved "
            f"ladder would be a fitted number."
        ],
    )


def _iso_share(rungs: list[Rung], premium: float) -> float:
    """Return one ISO's credited share at ``premium``."""
    credited, served = interpolate(rungs, premium)
    return credited / served if served > 0.0 else 0.0


def _share_at(year_rungs: dict[str, list[Rung]], premium: float) -> float:
    """Return the aggregate credited share across the ISOs at ``premium``."""
    credited = served = 0.0
    for rungs in year_rungs.values():
        c, s = interpolate(rungs, premium)
        credited += c
        served += s
    return credited / served if served > 0.0 else 0.0


def _result_at(
    year: int,
    year_rungs: dict[str, list[Rung]],
    target: float,
    premium: float,
    status: str,
    isos: list[str],
    notes: list[str],
) -> ClearingResult:
    """Assemble a :class:`ClearingResult` evaluated at ``premium``."""
    credited: dict[str, float] = {}
    served: dict[str, float] = {}
    for iso, rungs in sorted(year_rungs.items()):
        c, s = interpolate(rungs, premium)
        credited[iso], served[iso] = c, s
    total_served = sum(served.values())
    return ClearingResult(
        year=year,
        target=target,
        status=status,
        premium=premium,
        isos=isos,
        system_share=(
            sum(credited.values()) / total_served if total_served > 0 else 0.0
        ),
        iso_shares={
            iso: (credited[iso] / served[iso] if served[iso] > 0 else 0.0)
            for iso in credited
        },
        iso_credited_mwh=credited,
        iso_served_mwh=served,
        notes=notes,
    )


def clear_campaign(
    curves: dict[str, dict[int, list[Rung]]],
    targets: dict[int, float],
) -> list[ClearingResult]:
    """Clear every year for which at least one ISO has rungs.

    An ISO missing from a year is EXCLUDED from that year's aggregate and named
    in the result's notes — never treated as zero credited energy, which would
    silently fabricate a shortfall.

    Args:
        curves: ``{iso: {year: [Rung, ...]}}``.
        targets: ``{year: target share}``.

    Returns:
        One :class:`ClearingResult` per cleared year, ascending.
    """
    all_years = sorted({y for per_year in curves.values() for y in per_year})
    results: list[ClearingResult] = []
    for year in all_years:
        if year not in targets:
            continue
        year_rungs = {
            iso: per_year[year] for iso, per_year in curves.items() if year in per_year
        }
        absent = sorted(set(curves) - set(year_rungs))
        result = clear_year(year, year_rungs, targets[year])
        if absent:
            result.notes.append(
                f"EXCLUDED from this year's aggregate (no solved rungs): "
                f"{', '.join(absent)}. The aggregate covers "
                f"{', '.join(result.isos)} only."
            )
        results.append(result)
    return results


def read_target_row_results(path: Path) -> dict[tuple[str, int], dict[str, float]]:
    """Read SCN-WS2a's per-ISO target-row results (the uniform-SHARE half).

    Args:
        path: CSV with columns ``iso``, ``year``, ``clean_share`` and optionally
            ``premium_usd_per_mwh`` (the endogenous row dual, i.e. that ISO's
            own federal EAC price under no cross-ISO trade).

    Returns:
        ``{(iso, year): {"clean_share": ..., "premium_usd_per_mwh": ... | None}}``.

    Raises:
        SystemExit: If ``iso``, ``year`` or ``clean_share`` is missing.
    """
    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit(f"{path}: no rows")
    for col in ("iso", "year", "clean_share"):
        if col not in rows[0]:
            raise SystemExit(f"{path}: missing required column {col!r}")
    out: dict[tuple[str, int], dict[str, float]] = {}
    for row in rows:
        raw = row.get("premium_usd_per_mwh")
        out[(row["iso"].upper(), int(float(row["year"])))] = {
            "clean_share": float(row["clean_share"]),
            "premium_usd_per_mwh": float(raw) if raw not in (None, "") else None,
        }
    return out


def parse_targets(spec: str, years: list[int]) -> dict[int, float]:
    """Parse a target spec into a per-year target share.

    Accepts a flat share (``"0.80"``) applied to every year, or sparse knots
    (``"2030:0.6,2035:0.8,2050:1.0"``) linearly interpolated between and held
    flat outside — the same sparse-knot convention
    ``ScenarioConfig.federal_ces_target_by_year`` uses.

    Args:
        spec: The ``--target`` string.
        years: Years to produce targets for.

    Returns:
        ``{year: target}``.

    Raises:
        SystemExit: On a malformed spec or a target outside [0, 1].
    """
    knots: dict[int, float] = {}
    if ":" not in spec:
        try:
            flat = float(spec)
        except ValueError:
            raise SystemExit(
                f"--target {spec!r}: not a number or YEAR:SHARE list"
            ) from None
        knots = {y: flat for y in years}
    else:
        for part in spec.split(","):
            y, _, s = part.partition(":")
            try:
                knots[int(y.strip())] = float(s)
            except ValueError:
                raise SystemExit(f"--target: malformed knot {part!r}") from None
    for value in knots.values():
        if not 0.0 <= value <= 1.0:
            raise SystemExit(f"--target: share {value} is outside [0, 1]")
    if not knots:
        raise SystemExit("--target: no knots parsed")
    xs = sorted(knots)
    out: dict[int, float] = {}
    for year in years:
        if year <= xs[0]:
            out[year] = knots[xs[0]]
        elif year >= xs[-1]:
            out[year] = knots[xs[-1]]
        else:
            hi = next(x for x in xs if x >= year)
            lo = max(x for x in xs if x <= year)
            w = 0.0 if hi == lo else (year - lo) / (hi - lo)
            out[year] = knots[lo] + w * (knots[hi] - knots[lo])
    return out


def write_csv(results: list[ClearingResult], target_row: dict, path: Path) -> None:
    """Write the per-ISO-year clearing table.

    The ``target_row_*`` columns are left EMPTY when SCN-WS2a's uniform-share
    result has not been supplied — never filled with a placeholder, never
    inferred from the uniform-price side (that would be inventing the other
    half of the bracket).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "year",
                "target",
                "status",
                "uniform_premium_usd_per_mwh",
                "system_share",
                "iso",
                "iso_share_uniform_price",
                "iso_credited_twh",
                "iso_served_twh",
                "target_row_share",
                "target_row_premium_usd_per_mwh",
                "share_gap_pp",
                "system_share_spread_pp",
            ]
        )
        for r in results:
            for iso in r.isos:
                tr = target_row.get((iso, r.year), {})
                tr_share = tr.get("clean_share")
                mine = r.iso_shares.get(iso)
                w.writerow(
                    [
                        r.year,
                        f"{r.target:.4f}",
                        r.status,
                        "" if r.premium is None else f"{r.premium:.4f}",
                        f"{r.system_share:.6f}",
                        iso,
                        "" if mine is None else f"{mine:.6f}",
                        f"{r.iso_credited_mwh.get(iso, 0.0) / 1e6:.4f}",
                        f"{r.iso_served_mwh.get(iso, 0.0) / 1e6:.4f}",
                        "" if tr_share is None else f"{tr_share:.6f}",
                        ""
                        if tr.get("premium_usd_per_mwh") is None
                        else f"{tr['premium_usd_per_mwh']:.4f}",
                        ""
                        if (tr_share is None or mine is None)
                        else f"{100.0 * (mine - tr_share):.4f}",
                        f"{r.share_spread_pp:.4f}",
                    ]
                )


def write_markdown(results: list[ClearingResult], target_row: dict, path: Path) -> None:
    """Write the human-readable bracket report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    isos = sorted({i for r in results for i in r.isos})
    lines = [
        "# National CES clearing — the uniform-price half of the G-S2 bracket",
        "",
        f"Coverage: **modeled system, {len(isos)} ISO(s): {', '.join(isos)}**. "
        "This is NOT a national total and is never labelled one.",
        "",
        "Denominator: total modeled generation INCLUDING imports — the same basis "
        "`clean_share` uses. A statutory CES obligates retail sales; no loss or "
        "export factor is applied here (there is no measured one to apply).",
        "",
        "| year | target | status | uniform premium $/MWh | system share | ISO share spread (pp) |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        prem = "—" if r.premium is None else f"{r.premium:.2f}"
        lines.append(
            f"| {r.year} | {r.target:.3f} | {r.status} | {prem} | "
            f"{r.system_share:.4f} | {r.share_spread_pp:.2f} |"
        )
    lines += ["", "## Per-ISO shares at the uniform premium, beside the target row", ""]
    have_target_row = bool(target_row)
    lines += [
        "| year | ISO | uniform-price share | target-row share (WS-2a) | gap (pp) |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        for iso in r.isos:
            tr = target_row.get((iso, r.year), {})
            trs = tr.get("clean_share")
            mine = r.iso_shares.get(iso)
            lines.append(
                f"| {r.year} | {iso} | "
                f"{'—' if mine is None else f'{mine:.4f}'} | "
                f"{'—' if trs is None else f'{trs:.4f}'} | "
                f"{'—' if (trs is None or mine is None) else f'{100.0 * (mine - trs):.2f}'} |"
            )
    if not have_target_row:
        lines += [
            "",
            "**The target-row column is deliberately empty.** SCN-WS2a's "
            "`federal_ces_target_by_year` probe — the uniform-SHARE half of the "
            "bracket — was not supplied to this run. The bracket closes when that "
            "result exists and is passed via `--target-row-results`. The other side "
            "is not estimated, inferred or filled with a placeholder here.",
        ]
    notes = [(r.year, n) for r in results for n in r.notes]
    if notes:
        lines += ["", "## Notes", ""]
        lines += [f"- **{y}** — {n}" for y, n in notes]
    path.write_text("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--headline",
        type=Path,
        action="append",
        required=True,
        help="An <iso>_clean_share_vs_premium.csv from report_ces_campaign.py. "
        "Repeat once per ISO.",
    )
    ap.add_argument(
        "--target",
        required=True,
        help="National clean-share target: a flat share (0.80) or sparse knots "
        "(2030:0.6,2035:0.8,2050:1.0), linearly interpolated, held flat outside.",
    )
    ap.add_argument(
        "--target-row-results",
        type=Path,
        default=None,
        help="Optional CSV of SCN-WS2a per-ISO target-row results "
        "(iso,year,clean_share[,premium_usd_per_mwh]) — the uniform-SHARE half of "
        "the bracket. Omitted leaves that column empty with an explicit note.",
    )
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args(argv)

    curves: dict[str, dict[int, list[Rung]]] = {}
    for path in args.headline:
        iso, per_year = read_headline(path)
        if iso in curves:
            raise SystemExit(f"{iso} supplied twice (second: {path})")
        curves[iso] = per_year
    years = sorted({y for per_year in curves.values() for y in per_year})
    targets = parse_targets(args.target, years)
    results = clear_campaign(curves, targets)
    target_row = (
        read_target_row_results(args.target_row_results)
        if args.target_row_results
        else {}
    )

    write_csv(results, target_row, args.out_dir / "ces_national_clearing.csv")
    write_markdown(results, target_row, args.out_dir / "ces_national_clearing.md")
    for r in results:
        prem = "not reached" if r.premium is None else f"${r.premium:.2f}/MWh"
        print(
            f"[clearing] {r.year} target={r.target:.3f} {r.status:<13} {prem:>16} "
            f"system_share={r.system_share:.4f} spread={r.share_spread_pp:.2f}pp"
        )
    print(f"[clearing] wrote {args.out_dir}/ces_national_clearing.{{csv,md}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
