"""xiso-6: what WOULD a diurnal-amplitude criterion do to the six determinations?

xiso-1 established that diurnal price-amplitude compression is SYSTEMIC — 36/36
ISO x year x benchmark cells compress, mean ~41 % of measured amplitude, while
the annual LEVEL is right to ~7 % and the PHASE is right in 34/36 rows
(``results/calibration/FINDING-xiso1-diurnal-price-amplitude-is-systemic-2026-08-01.md``).
It filed the question "should the rubric gain a diurnal-amplitude criterion?" as
an OWNER CALL and did not act on it. neiso-74 had filed the same call first. It
has never been answered, and NEISO's lever queue carries a DO-NOT-REDO on every
storage-side PS lever until the defect closes.

**Nobody has ever measured what the answer WOULD DO.** That is this probe's
entire job: it takes a RANGE of candidate bands for a hypothetical amplitude
criterion and reports, per band, which keepers would pass, which would fail, and
what each ISO's DETERMINATION would become. A card that says "amplitude is 41 %
of measured, should we gate it?" already exists twice over; a card that says "at
band X, PJM and NEISO stop being CALIBRATED and CAISO does not" is a decision the
owner can actually take.

WHAT THIS PROBE DOES NOT DO
---------------------------
**The scorer is NOT changed.** ``scripts/calibration_verdict.py`` is imported
read-only for (a) each keeper's ACTUAL determination at HEAD and (b) the rubric
constants and aggregation rules, which are re-applied HERE with the hypothetical
criterion injected. No criterion is added to ``CRITERIA``; ``LEDGERABLE_CRITERIA``
and ``MAX_LEDGERED_CAVEATS`` are untouched; ``rubric-consts.js`` is untouched.
Nothing this probe prints is a determination of record. No keeper moves, no
dashboard status regenerates, no LP is solved (rule 22 ``[R-HOLDOUT]``: committed
artifacts only, 2023-2025 only, nothing spent).

Rule 25 ``[R-ISO-SCOPE]``: every number is that ISO's own. The cross-ISO table
answers "what would one band do to six determinations", never "does ISO X inherit
ISO Y's number".

Rule 26 ``[R-MECH-MATRIX]``: no mechanism is tested, so no cell verdict moves.

CONSTRUCTION
------------
* **Amplitude** — re-taken at HEAD by importing xiso-1's own audit module
  (``_xiso1_diurnal_amplitude_audit``) rather than re-deriving it, honouring that
  finding's DO-NOT-REDO. Hour-of-day mean range, model P1 load-weighted system
  price / measured hub price. All six CURRENT keepers, read from the live keeper
  store.
* **Benchmark** — **RT** is primary, because that is what the rubric already
  gates the price level on: ``score_price_mean`` names RT the honest benchmark
  ("a perfect-foresight dispatch LP prices RT physics, not day-ahead risk
  premia") and falls back to DA only where no RT actual is committed. DA is
  reported alongside so the choice is visible, not assumed.
* **Criterion form** — two-band on ``err = |amplitude_ratio - 1|``, the same
  shape every other magnitude criterion in the rubric uses
  (``calibration_verdict._band_result``): PASS inside the target band, auto
  COMMERCIAL_BAND caveat between target and commercial, FAIL beyond. Per-year
  records aggregate worst-year-wins (``_agg_status``), as every criterion does.
* **Determination** — re-derived from the base verdict's own per-criterion
  statuses plus the injected criterion, replaying the aggregation of
  ``determine_from_artifacts`` (governance -> FAIL -> budgets -> downgrading
  caveats). The tier choice is swept, because it changes the answer: a
  protective-tier caveat is instantly NOT-YET (``MAX_PROTECTIVE_CAVEATS`` = 0),
  a load-bearing or supporting caveat downgrades to CALIBRATED-WITH-CAVEATS, and
  a FAIL forces NOT-YET **at every tier**.

Run:  uv run python scripts/probes/_xiso6_amplitude_criterion_band_probe.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import scripts.calibration_verdict as CV  # noqa: E402  (read-only import)

# xiso-1's audit module is a leading-underscore file, so import it by path
# rather than by name. Reusing it is the point: the amplitude statistic is not
# re-derived here (xiso-1 DO-NOT-REDO).
_spec = importlib.util.spec_from_file_location(
    "_xiso1_audit", Path(__file__).with_name("_xiso1_diurnal_amplitude_audit.py")
)
X1 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(X1)

YEARS = X1.YEARS

# Candidate bands, as (target, commercial) tolerances on |amplitude_ratio - 1|.
# Read them either way: a target of 0.20 is "amplitude within +/-20 % of
# measured", i.e. an amplitude floor of 80 %. The grid deliberately spans from
# bands no keeper could meet to bands every keeper meets, so the owner sees
# where the answer actually turns rather than being handed one number.
BANDS = (
    (0.20, 0.35),
    (0.30, 0.45),
    (0.40, 0.55),
    (0.50, 0.65),
    (0.55, 0.70),
    (0.60, 0.75),
    (0.65, 0.80),
    (0.70, 0.85),
    (0.75, 0.90),
    (0.80, 0.90),
)

TIERS = (CV.TIER_LOAD, CV.TIER_SUPPORT, CV.TIER_PROTECT)


def hdr(text: str) -> None:
    print(f"\n{'=' * 78}\n{text}\n{'=' * 78}")


# --------------------------------------------------------------- amplitude
def amplitude_table() -> dict[tuple[str, int, str], float]:
    """(iso, year, kind) -> amplitude ratio (model hod range / measured), 0-1.

    Re-taken at HEAD against whatever each ISO's keeper currently is. A cell
    whose inputs have moved out from under the audit is REPORTED MISSING rather
    than carried forward stale.
    """
    out: dict[tuple[str, int, str], float] = {}
    for iso, (_kid, bundle) in X1.keepers().items():
        for year in YEARS:
            pm = X1.model_price(bundle, year)
            if pm is None:
                print(f"  !! {iso} {year}: no model system hourly — cell NOT reported")
                continue
            rm = X1.stats(pm)["hod_range"]
            for kind in ("da", "rt"):
                pa = X1.measured_price(iso, year, kind)
                if pa is None:
                    print(f"  !! {iso} {year} {kind.upper()}: no committed actual")
                    continue
                ra = X1.stats(pa)["hod_range"]
                out[(iso, year, kind)] = rm / ra if ra else float("nan")
    return out


# ------------------------------------------------------ hypothetical scoring
def criterion_status(ratios: list[float], target: float, commercial: float) -> str:
    """Worst-year status for the hypothetical criterion at one band.

    ``_band_result`` on ``|ratio - 1|`` per year, aggregated worst-year-wins by
    ``_agg_status`` — exactly how every existing multi-year criterion scores.
    """
    recs = [
        {"status": CV._band_result(abs(r - 1.0), target, commercial)[0]}
        for r in ratios
        if not np.isnan(r)
    ]
    return CV._agg_status(recs) if recs else CV.SKIPPED


def determination_with(base: dict, amp_status: str, tier: str) -> str:
    """Replay ``determine_from_artifacts``'s aggregation with one extra criterion.

    Mirrors the scorer's order exactly: governance -> any FAIL -> caveat budgets
    -> downgrading caveats (protective + commercial-band) plus skips and
    data-blocked years. A LEDGERED caveat does not downgrade (rubric v3.3), and
    the injected criterion is never ledgered — ``LEDGERABLE_CRITERIA`` is
    ``{price_tail}`` and this probe does not change it, which is itself part of
    the answer.
    """
    crit = base["criteria"]
    gov = crit["governance"]["status"]
    if gov != CV.PASS:
        return CV.NOT_YET

    fails = [
        cid for cid, c in crit.items() if c["status"] == CV.FAIL
    ] + ([" amplitude"] if amp_status == CV.FAIL else [])
    if fails:
        return CV.NOT_YET

    protective = [
        c
        for cid, c in crit.items()
        if c["tier"] == CV.TIER_PROTECT
        and cid != "governance"
        and c["status"] == CV.CAVEAT
    ]
    ledgered = [
        c
        for cid, c in crit.items()
        if c["tier"] != CV.TIER_PROTECT
        and c["status"] == CV.CAVEAT
        and c["caveat_kind"] == "ledgered"
    ]
    band = [
        c
        for cid, c in crit.items()
        if c["tier"] != CV.TIER_PROTECT
        and c["status"] == CV.CAVEAT
        and c["caveat_kind"] == "commercial-band"
    ]
    if amp_status == CV.CAVEAT:
        # The injected caveat is a COMMERCIAL_BAND caveat (auto, unbudgeted but
        # downgrading) at load-bearing/supporting tier, and a protective caveat
        # at protective tier — which is instantly over budget (max 0).
        (protective if tier == CV.TIER_PROTECT else band).append({"label": "amplitude"})

    if (
        len(protective) > CV.MAX_PROTECTIVE_CAVEATS
        or len(ledgered) > CV.MAX_LEDGERED_CAVEATS
    ):
        return CV.NOT_YET

    skipped = [
        cid for cid, c in crit.items() if cid != "governance" and c["status"] == CV.SKIPPED
    ]
    if len(protective) + len(band) == 0 and not skipped and not base["data_blocked_years"]:
        return CV.CALIBRATED
    return CV.CALIBRATED_CAVEATS


# ----------------------------------------------------------- the C3a coupling
def cancellation_decomposition(iso: str, bundle: Path, year: int, kind: str) -> dict | None:
    """How much of the level is trough-excess cancelling peak-deficit, and what
    a one-sided amplitude repair would do to the C3a level error.

    Accounting only — NOT a mechanism and NOT a prediction. The hour-of-day
    profile is split into the 12 hours the MEASURED profile ranks highest (the
    "peak half") and the 12 it ranks lowest. Three counterfactual levels:

      * ``peak_only``  — model peak-half hours replaced by measured, trough half
        left alone: the level a successor lands on if it lifts the peak and does
        not touch the trough.
      * ``trough_only`` — the mirror: trough repaired, peak left alone.
      * ``both`` — sanity check; lands on the measured level by construction.

    Any successor that closes amplitude lands BETWEEN the two one-sided numbers
    (or outside them if it overshoots). That is the bracket the owner needs
    before adopting a criterion, not after.
    """
    pm = X1.model_price(bundle, year)
    pa = X1.measured_price(iso, year, kind)
    if pm is None or pa is None:
        return None
    m = X1.stats(pm)["hod"]
    a = X1.stats(pa)["hod"]
    peak_h = np.argsort(a)[12:]  # the 12 highest MEASURED hours
    trough_h = np.argsort(a)[:12]
    lvl_m, lvl_a = float(np.nanmean(m)), float(np.nanmean(a))
    rep_peak = m.copy()
    rep_peak[peak_h] = a[peak_h]
    rep_trough = m.copy()
    rep_trough[trough_h] = a[trough_h]
    return {
        "level_model": lvl_m,
        "level_actual": lvl_a,
        "level_err": 100.0 * (lvl_m / lvl_a - 1.0),
        "peak_err": 100.0 * (float(m[peak_h].mean()) / float(a[peak_h].mean()) - 1.0),
        "trough_err": 100.0
        * (float(m[trough_h].mean()) / float(a[trough_h].mean()) - 1.0),
        "err_peak_only": 100.0 * (float(np.nanmean(rep_peak)) / lvl_a - 1.0),
        "err_trough_only": 100.0 * (float(np.nanmean(rep_trough)) / lvl_a - 1.0),
    }


def main() -> int:
    hdr("xiso-6 — what a diurnal-amplitude criterion WOULD do to six determinations")
    ks = X1.keepers()
    print("keepers scored (live keeper store at HEAD):")
    for iso, (kid, b) in ks.items():
        print(f"  {iso:<6} {kid:<44} {b.relative_to(REPO)}")
    print(
        f"\nrubric at HEAD: v{CV.RUBRIC_VERSION}   "
        f"MAX_PROTECTIVE_CAVEATS={CV.MAX_PROTECTIVE_CAVEATS}   "
        f"MAX_LEDGERED_CAVEATS={CV.MAX_LEDGERED_CAVEATS}   "
        f"LEDGERABLE_CRITERIA={set(CV.LEDGERABLE_CRITERIA)}"
    )
    print("SCORER NOT CHANGED — imported read-only; every hypothetical is re-derived here.")

    # ------------------------------------------------------------------ part A
    hdr("A. amplitude re-taken at HEAD (all six CURRENT keepers)")
    amp = amplitude_table()
    for kind in ("da", "rt"):
        print(f"\n  vs measured {kind.upper()}  (hour-of-day range, model as % of actual)")
        print(f"  {'ISO':<6} " + "  ".join(f"{y:>7d}" for y in YEARS) + "    worst")
        for iso in ks:
            cells, vals = [], []
            for y in YEARS:
                v = amp.get((iso, y, kind))
                cells.append(f"{100 * v:6.1f}%" if v is not None else "      -")
                if v is not None:
                    vals.append(v)
            worst = f"{100 * min(vals, key=lambda r: -abs(r - 1)):6.1f}%" if vals else "   -"
            print(f"  {iso:<6} " + "  ".join(cells) + f"   {worst}")
        allv = [v for (i, y, k), v in amp.items() if k == kind]
        print(
            f"  {'ALL':<6} mean {100 * float(np.mean(allv)):5.1f}%   "
            f"min {100 * min(allv):5.1f}%   max {100 * max(allv):5.1f}%"
        )

    # ------------------------------------------------------------------ part B
    hdr("B. base determinations at HEAD (the scorer's own, unmodified)")
    base: dict[str, dict] = {}
    for iso, (kid, _b) in ks.items():
        v = CV.determine(kid)
        base[iso] = v
        gs = v["grade_summary"]
        print(
            f"  {iso:<6} {v['determination']:<24} "
            f"(target {gs['target_grade']}/{gs['scored']}, band {gs['commercial_grade']}, "
            f"ledgered {gs['ledgered']}, fails {gs['fails']})   {kid}"
        )
        for cid, c in v["criteria"].items():
            if c["status"] != CV.PASS:
                print(
                    f"           {cid:<14} {c['status']:<8} "
                    f"{c.get('caveat_kind') or ''}"
                )

    # ------------------------------------------------------------------ part C
    hdr("C. THE DECISIVE TABLE — band x ISO -> criterion status -> determination")
    for kind in ("rt", "da"):
        print(
            f"\n  ### benchmark: measured {kind.upper()}"
            + ("   (PRIMARY — the basis C3a gates on)" if kind == "rt" else "   (reported alongside)")
        )
        for tier in TIERS:
            print(
                f"\n  --- hypothetical criterion at {tier.upper()} tier "
                f"{'(protective caveat budget is 0 -> a caveat is NOT-YET)' if tier == CV.TIER_PROTECT else ''}"
            )
            print(
                f"  {'target/comm':<13} {'amp floor':<10} "
                + "  ".join(f"{iso:<9}" for iso in ks)
                + "   CALIBRATED lost"
            )
            for target, commercial in BANDS:
                cells, lost = [], 0
                for iso in ks:
                    ratios = [
                        amp[(iso, y, kind)] for y in YEARS if (iso, y, kind) in amp
                    ]
                    st = criterion_status(ratios, target, commercial)
                    det = determination_with(base[iso], st, tier)
                    if (
                        base[iso]["determination"] == CV.CALIBRATED
                        and det != CV.CALIBRATED
                    ):
                        lost += 1
                    tag = {
                        CV.CALIBRATED: "CAL",
                        CV.CALIBRATED_CAVEATS: "CWC",
                        CV.NOT_YET: "NOT-YET",
                    }[det]
                    cells.append(f"{st[:4]}/{tag:<7}"[:9].ljust(9))
                print(
                    f"  ±{target:.2f}/±{commercial:.2f}  "
                    f"≥{100 * (1 - target):3.0f}%/≥{100 * (1 - commercial):3.0f}%  "
                    + "  ".join(cells)
                    + f"   {lost}/3"
                )
            print(
                "    (cell = criterion status / resulting determination; "
                "'CALIBRATED lost' counts how many of the 3 currently-CALIBRATED "
                "ISOs stop being CALIBRATED)"
            )

    hdr("C2. option (B) REPORTED-ONLY — the same criterion contributing no status")
    print(
        "  A REPORTED_ONLY criterion is scored and published but is not aggregated into\n"
        "  the determination and consumes no caveat budget (calibration_verdict.REPORTED_ONLY,\n"
        "  the posture C5a `co2` already holds). By construction every determination below is\n"
        "  the base determination, at EVERY band:"
    )
    for iso in ks:
        print(f"    {iso:<6} {base[iso]['determination']}  (unchanged at all 10 bands)")

    # ------------------------------------------------------------------ part D
    hdr("D. THE CANCELLATION TRAP — what an amplitude repair does to C3a")
    print(
        "  Accounting decomposition, NOT a mechanism. Hour-of-day profile split into the 12\n"
        "  hours the MEASURED profile ranks highest / lowest. 'peak-only' repairs the peak half\n"
        "  to measured and leaves the trough; 'trough-only' is the mirror. Any successor that\n"
        "  closes amplitude lands BETWEEN these two level errors (or outside, if it overshoots).\n"
        "  C3a band at HEAD: PASS iff |level err| <= "
        f"{100 * CV.PRICE_MEAN_TOL:.0f}% (target and commercial are COINCIDENT, so\n"
        "  there is no commercial-band caveat for C3a — it is PASS or FAIL)."
    )
    print(
        f"\n  {'ISO':<6} {'yr':<5} {'level':<9} {'peak half':<11} {'trough half':<12} "
        f"{'peak-only':<11} {'trough-only':<12} C3a@repair"
    )
    for iso, (_kid, bundle) in ks.items():
        for year in YEARS:
            d = cancellation_decomposition(iso, bundle, year, "rt")
            if d is None:
                continue
            po, to = d["err_peak_only"], d["err_trough_only"]
            verdict = (
                "peak-only "
                + ("PASS" if abs(po) <= 100 * CV.PRICE_MEAN_TOL else "FAIL")
                + " / trough-only "
                + ("PASS" if abs(to) <= 100 * CV.PRICE_MEAN_TOL else "FAIL")
            )
            print(
                f"  {iso:<6} {year:<5} {d['level_err']:+7.1f}%  "
                f"{d['peak_err']:+9.1f}%  {d['trough_err']:+10.1f}%  "
                f"{po:+9.1f}%  {to:+10.1f}%   {verdict}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
