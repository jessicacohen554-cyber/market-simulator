"""Emit the per-ISO Calibration Status data parts for the backcast dashboard.

The dashboard's "Calibration Status" view (one page, every ISO) renders
client-side from COMMITTED, PER-ISO status parts (sharded 2026-07-19 so
concurrent keeper promotions in different ISOs never touch the same file):

* ``frontend/data/backcast/status/<ISO>.js`` — that ISO's current-keeper
  machine verdict (``window.BC.statusParts[ISO]``), rebuilt on promotion via
  ``--iso <ISO>``. For each ISO's CURRENT keeper (``keepers/<ISO>.json``, via
  ``scripts.lib.keeper_store``) it runs the SAME scorer the gate uses —
  ``scripts/calibration_verdict.py`` — and embeds the full verdict, so the
  page can never disagree with the gate.
* ``frontend/data/backcast/status/shared.js`` — the rubric reference,
  benchmark anchor table and scoring notes (``window.BC.statusShared``).
  Deterministic (no timestamp): its bytes change only when the rubric/scorer
  constants change, so rewriting it from any session is conflict-free.

``docs/codebase-site/js/bc-data.js`` composes the parts back into the legacy
``window.BC.status`` shape (the old monolithic ``status.js`` is retired).

Why COMMITTED files (mirroring ``runs/<id>.js``) rather than a deploy-time
rebuild like manifest.js/benchmark.js: the C6 governance verdict reads each
bundle's ``calibration_attestation.json`` / ``run_config.json`` under
``results/calibration/``, which the GitHub Pages deploy's sparse checkout does
NOT fetch. So verdicts can only be computed where the bundles live — here,
locally — and the results are committed.

Stdlib-only (json, calibration_verdict, keeper_store). Run after a keeper
changes:

    python scripts/build_status.py --iso MISO  # rebuild only MISO's part (+ shared)
    python scripts/build_status.py             # rebuild every ISO part + shared
    python scripts/build_status.py --check     # verify parts in sync, exit 1 if not
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts import calibration_verdict as cv  # noqa: E402  (after sys.path insert)
from scripts.lib import keeper_store  # noqa: E402  (after sys.path insert)

DATA = REPO / "frontend" / "data" / "backcast"
STATUS_DIR = DATA / "status"
SHARED_FILE = STATUS_DIR / "shared.js"
# D-7 statistical-mode fail-count gaps (REPORTED next to each keeper, never
# gating): committed data seeded from docs/statistical-mode-results-2026-07.md,
# refreshed whenever a statmode probe re-measures a keeper.
STATMODE_D7_FILE = DATA / "statmode_d7.json"

# Display order for the ISO card grid (others fall in alphabetically after these,
# so an unlisted region still renders — the list is presentation, not a gate).
# SOCO added 2026-09-16 (lane SOCO-34); it is the ninth registered region and has
# no keeper yet, so its card appears only once lane SOCO-40 registers one. NWPP,
# registered the same day as SOCO, is still unlisted and falls through to the
# alphabetical tail — an NWPP-desk gap, routed by SOCO-34 rather than filled here.
# NWPP added 2026-09-16 (lane NWPP-40, the first NWPP registration) after SOCO,
# the order the two regions registered in (NWPP-20 merged first, SOCO-20
# second, plan §0) — presentation only; nothing is gated on this tuple.
ISO_ORDER = ("ERCOT", "PJM", "CAISO", "NYISO", "NEISO", "MISO", "SPP", "SOCO", "NWPP")


def _tail_note() -> str:
    """Render the per-ISO scarcity-tail thresholds from the scorer's table."""
    by = {}
    for iso, thr in cv.TAIL_THRESHOLD.items():
        by.setdefault(thr, []).append(iso)
    parts = [
        f"${thr:.0f}/MWh ({', '.join(sorted(isos))})"
        for thr, isos in sorted(by.items())
    ]
    return "; ".join(parts)


def rubric() -> list[dict]:
    """Criterion reference for the "Tests conducted" section.

    Labels and HARD/SOFT come from ``calibration_verdict.CRITERIA``; tolerances are
    formatted from the scorer's own module constants (never re-typed here), so the
    page's tolerances are exactly the gate's. ``measures``/``source`` are the
    plain-language descriptions drawn from docs/calibration-determination-rubric.md.
    """
    L = {cid: lab for cid, (lab, _t) in cv.CRITERIA.items()}
    T = {cid: tier for cid, (_l, tier) in cv.CRITERIA.items()}
    # Criteria removed from the rubric but still computed and shown (v2.9: C5a
    # co2). They keep a reference row on the "Tests conducted" section so the
    # page explains what the reported number is and why it does not gate, but
    # they carry no tier and never render as HARD.
    L.update(cv.REPORTED_ONLY)
    T.update({cid: cv.TIER_REPORT for cid in cv.REPORTED_ONLY})

    def row(cid, measures, source, tol):
        return {
            "id": cid,
            "label": L[cid],
            "tier": T[cid],
            "hard": T[cid] == cv.TIER_PROTECT,  # legacy display key
            "measures": measures,
            "source": source,
            "tol": tol,
        }

    return [
        row(
            "fuelmix",
            "Annual generation by model plant-class, on the grid-delivered basis "
            "(grid LP dispatch, no behind-the-meter CHP add-back), as both a volume "
            "and a share-of-generation check.",
            "EIA-923 Schedule-5 net generation minus that class's behind-the-meter "
            "CHP host supply (btm.parquet) — grid-delivered TWh by class.",
            f"volume miss within ±min({cv.FUELMIX_VOL_LOAD_FRAC * 100:.1f}% of ISO total "
            f"load, {cv.FUELMIX_VOL_CAP_TWH:g} TWh) AND share of total generation "
            f"within ±{cv.FUELMIX_SHARE_PP:g} pp (the universal class gate — scales with "
            f"system size but capped at an absolute {cv.FUELMIX_VOL_CAP_TWH:g} TWh, "
            "applied uniformly across classes and ISOs; loosened 2026-07-02 so "
            "small-class TWh noise no longer hard-fails a structurally faithful run). "
            "In a preliminary current-year EIA-923 vintage "
            f"(≥ {cv.PRELIM_923_FROM_YEAR}) only the (ISO, class) pairs the completeness "
            "audit (scripts/audit_eia923_completeness.py) verifies COMPLETE are gated; "
            "classes with incomplete plant data are SKIPPED (covered by the C2 family "
            "EIA-930 reconcile), never silently passed.",
        ),
        row(
            "sysvol",
            "Total grid-delivered TWh summed over the gas family and the coal family.",
            "EIA-923 − BTM for complete vintages; the EIA-930 grid total for the "
            f"preliminary current-year (≥ {cv.PRELIM_923_FROM_YEAR}) vintage, via the "
            f"{cv.VINTAGE_RECONCILE_FRAC:.2f} reconcile.",
            f"complete vintages defer to the C1 per-class gate; the preliminary-"
            f"vintage EIA-930 family fallback is two-band: ±{cv.SYSVOL_TOL * 100:.1f}% "
            f"target / ±{cv.SYSVOL_COMMERCIAL * 100:.1f}% commercial (NYISO's "
            "benchmark held zonal energy to ~0–4%; the fallback's own benchmark "
            "carries the 923-vs-930 reconciliation uncertainty). Families < "
            f"{cv.SYSVOL_MIN_TWH:.0f} TWh are immaterial → governed by C1.",
        ),
        row(
            "price_mean",
            "System load-weighted mean LMP ($/MWh). The gated benchmark is named "
            "in each record (vs RT / vs DA): the model is a real-time analogue "
            "(perfect-foresight dispatch prices RT physics, not day-ahead risk "
            "premia), so RT gates and the DA comparison appears as a separate "
            "non-gated diagnostic row (the DART premium made visible, never "
            "modeled with offers/adders).",
            "Derived actual hub mean — real-time (avgLMP.rt), falling back to "
            "day-ahead (avgLMP.da) only when no RT actual is committed.",
            f"±{cv.PRICE_MEAN_TOL * 100:.0f}% passes clean (rubric v2.3: the "
            "target band is set to the commercial band, so there is no caveat "
            "range). The band is the demonstrated planning grade (NYISO's "
            "accepted GE MAPS benchmark ran −2% to −17% zonal; the SEM "
            "regulator's ±5% PLEXOS criterion stays a reported reference). "
            "Beyond it → FAIL unless a measured-input limitation is ledgered.",
        ),
        row(
            "price_shape",
            "NRMSE between model and actual monthly load-weighted price vectors.",
            "Actual monthly RT price (avgLMP.rt_mon), falling back to DA.",
            f"NRMSE ≤ {cv.PRICE_SHAPE_NRMSE_MAX:.2f} passes clean (rubric v2.3: "
            "single band, no caveat range; published monthly norms run ~5–15%; "
            "SEM's regulator-accepted backcast carried −9% winter-peak / +11% "
            "off-peak period biases).",
        ),
        row(
            "price_tail",
            "Count of scarcity-tail hours — model vs the ACTUAL RT hourly tail "
            "(hours the real-time market's hourly hub average cleared above the "
            "threshold: the scarcity the market actually realized; rubric v2.7, "
            "owner amendment 2026-07-16, every ISO). The DA count — which "
            "prices scarcity expectations and embeds the day-ahead forecast-risk "
            "premium a realized-weather backcast cannot price (ERCOT 2023: DA "
            "311 vs RT 181 h) — is reported as a non-gated diagnostic row.",
            "Committed tail part frontend/data/backcast/tail/actual_tail.json "
            "(scripts/data/derive_actual_tail.py, from the measured hub RT/DA hourly "
            "series; 2023–2025 only). Thresholds: " + _tail_note() + ".",
            f"model within [{cv.TAIL_LO:g}×, {cv.TAIL_HI:g}×] of the RT actual — a "
            "collapsed tail and an invented tail both FAIL; an RT actual below "
            f"{cv.TAIL_SMALL_COUNT:g} h gates on |model−actual| ≤ "
            f"{cv.TAIL_SMALL_COUNT:g} h instead (ratio degenerate). No commercial "
            "or public model publishes tail-hour accuracy at all — practice "
            "excludes spike hours from scoring; this rubric keeps scoring them.",
        ),
        row(
            "dispatch_corr",
            "Hourly Pearson r and NRMSE of modeled vs actual generation, for the gas "
            "and coal fleets.",
            "EIA-930 hourly net generation by fuel.",
            f"r ≥ {cv.DISP_R_FLOOR:.2f} and NRMSE ≤ {cv.DISP_NRMSE_MAX:.2f} "
            f"(fleets < {cv.DISP_MIN_TWH:.0f} TWh are degenerate → skipped, governed by C1).",
        ),
        row(
            "co2",
            "Annual system CO₂, model vs the eGRID/CAMPD-rate actual, on the "
            "full-plant CHP-inclusive basis (rubric v2.3): eGRID counts each "
            "cogen's whole burn, so the measured behind-the-meter CHP host "
            "supply is added back on BOTH sides before the per-class "
            "intensities are applied.",
            "Committed bench-part co2.egrid — full EIA-923 class totals × "
            "net-gen-weighted eGRID/CAMPD class intensities (full-plant basis).",
            f"±{cv.CO2_TOL * 100:.0f}% target / ±{cv.CO2_COMMERCIAL * 100:.0f}% "
            "commercial (no production-cost model publishes a backcast CO₂ error; "
            "the AEO retrospective's 1–3-year CO₂ error SD is 3.2–4.9% on full "
            "forecasts — the target is stricter than any published requirement).",
        ),
        # (The C5b storage-throughput row was removed with the criterion —
        # rubric v2.7 owner amendment 2026-07-16: EIA-930 storage-dispatch
        # data is not reliable enough to participate in the determination.
        # Storage numbers remain on the run pages as diagnostics.)
        row(
            "governance",
            "Every active lever traces to a measured input; no fit to price residuals; "
            "no pinning to actuals; the outage filter keys on exogenous net load.",
            "run_config.json (machine cross-check) + calibration_attestation.json "
            "(four assertions, all required true).",
            "pass/fail — never graded, never caveatable; an unattested run is NOT-YET.",
        ),
        # (The C7 diurnal-shape row was REMOVED by the v3.1 owner amendment
        # 2026-08-06: C7 is retired from the calibration report and the
        # determination, on the finding that no commercial-grade comparable
        # gates or publishes diurnal-shape accuracy — the comparables row below
        # scores C6/C7/C8 "beyond commercial practice", i.e. with no external
        # anchor at all, and every other graded criterion here is two-band
        # scored against a published one. The D-1 measurement it read is NOT
        # retired: it still backs C8's grounded-above-budget escalation, whose
        # tolerance line names the profile-r / CV-ratio gates.)
        row(
            "forced_share",
            "Share of each class's annual energy dispatched AT a binding min_gen "
            "floor (per-mechanism attribution via the FleetArrays mechanism-id "
            "array) — floors are commitment scaffolding, not the dispatch model "
            "(audit D-2 / CLAUDE.md rule 20). Nuclear, CHP-steam and coal "
            "take-or-pay mechanisms are exempt (structural must-run physics).",
            "The bundle's committed legitimacy_diagnostics.json D-2 per-class "
            "summary (floors from the bundle's floors/*.npz or the "
            "run_year(fleet_only=True) rebuild; rebuilt shares exclude the "
            "P1-dependent RA bridge and are flagged lower-bound).",
            f"forced share < {cv.FORCED_SHARE_PEAKER_MAX * 100:.0f}% for peaker "
            f"classes (raised from 10% by the v2.1 owner amendment 2026-07-06, "
            f"amending CLAUDE.md rule 20), < "
            f"{cv.FORCED_SHARE_MERCHANT_MAX * 100:.0f}% for any merchant class; "
            f"same ≥ {cv.PROTECTIVE_MIN_LOAD_FRAC:.0%}-of-load materiality floor "
            "as C7. The scorer gates the artifact's measured share against the "
            "rubric's caps (calibration_verdict.FORCED_SHARE_*).",
        ),
    ]


def benchmark() -> dict:
    """The commercial-grade benchmark comparison table (rubric v2 §8).

    Rendered on the Calibration Status page next to the live keeper scores —
    the scrutiny-survival artifact: each graded band is anchored to the best
    published external comparable, and the rows where we score STRICTER than
    any published practice say so. Full survey with evidence grades:
    docs/rubric-v2-benchmark-memo-2026-07.md §2.
    """
    rows = [
        {
            "criterion": "C3a mean LMP",
            "target": f"±{cv.PRICE_MEAN_TOL * 100:.0f}% (v2.3: single band, passes clean)",
            "commercial": f"±{cv.PRICE_MEAN_COMMERCIAL * 100:.0f}% (coincident)",
            "published": (
                "SEM (Ireland) regulator criterion for its official PLEXOS model: "
                "±5% aggregate vs 3–5 yrs of actuals (ECA SEM-20-004); NERA's 2025 "
                "SEM backcast: +0.1% on the 4-yr mean; NYISO's accepted GE MAPS "
                "benchmark: −2% to −17% zonal LBMP; market monitors' competitive "
                "re-simulations sit 0–4% from actual prices (CAISO DMM 2021–24, "
                "MISO SOM 2023) — the market-conduct noise floor no cost-based "
                "model should chase."
            ),
        },
        {
            "criterion": "C3b monthly price shape (NRMSE)",
            "target": f"≤{cv.PRICE_SHAPE_NRMSE_MAX:.2f} (v2.3: single band, passes clean)",
            "commercial": f"≤{cv.PRICE_SHAPE_NRMSE_COMMERCIAL:.2f} (coincident)",
            "published": (
                "SEM regulator-accepted backcast period biases: −9% winter-peak / "
                "+11% off-peak; published monthly norms ~5–15% with correct "
                "seasonality; PyPSA-Eur 2020–24 hindcast weekly SMAPE 20–26% "
                "(academic state of the art for the model class)."
            ),
        },
        {
            "criterion": "C3c scarcity tail (RT hourly hours, v2.7)",
            "target": f"[{cv.TAIL_LO:g}×, {cv.TAIL_HI:g}×] of the RT actual",
            "commercial": "no published comparable",
            "published": (
                "NO commercial or public model publishes tail-hour or "
                "duration-curve accuracy as a fitness criterion. Documented "
                "practice goes the other way: ECA excluded ~50–100 h/month of "
                "price-spike events from its scoring; NYISO absorbed the residual "
                "into tuned hurdle rates; PyPSA-Eur reports spikes 'not captured "
                "well' in every configuration. This rubric keeps scoring the tail "
                "— stricter than practice — on the actual RT hourly basis (the "
                "scarcity the market realized; DA is the reported diagnostic)."
            ),
        },
        {
            "criterion": "C1 per-class fuel mix",
            "target": (
                f"±min({cv.FUELMIX_VOL_LOAD_FRAC * 100:.0f}% load, "
                f"{cv.FUELMIX_VOL_CAP_TWH:g} TWh) & ±{cv.FUELMIX_SHARE_PP:g} pp share"
            ),
            "commercial": "no published comparable (single-band)",
            "published": (
                "No external validation publishes per-class volumes — NYISO's "
                "benchmark stops at zonal energy (~0–4%) and NREL practice at "
                "annual generation by type/state. Scored anyway because the "
                "intended uses consume the class mix (deliberately stricter than "
                "commercial practice)."
            ),
        },
        {
            "criterion": "C2 family volume (preliminary-vintage fallback)",
            "target": f"±{cv.SYSVOL_TOL * 100:.1f}%",
            "commercial": f"±{cv.SYSVOL_COMMERCIAL * 100:.1f}%",
            "published": (
                "NYISO GE MAPS benchmark: NYCA energy −0.03% (load is an input), "
                "zonal energy ~0–4%; AEO retrospective 1–3-yr generation error SD: "
                "gas 5.7–9.6%, coal 6.1–13.2% (forecast-mode upper bounds)."
            ),
        },
        {
            "criterion": "C5a system CO₂ (full-plant basis, v2.3)",
            "target": f"±{cv.CO2_TOL * 100:.0f}%",
            "commercial": f"±{cv.CO2_COMMERCIAL * 100:.0f}%",
            "published": (
                "Thinnest external evidence: no PCM publishes a backcast CO₂ "
                "error. AEO retrospective energy-CO₂ error SD 3.2–4.9% at 1–3-yr "
                "horizons (full forecasts), 14.6% pooled all-horizon."
            ),
        },
        {
            "criterion": "C4 hourly fleet dispatch correlation",
            "target": f"r ≥ {cv.DISP_R_FLOOR:.2f}, NRMSE ≤ {cv.DISP_NRMSE_MAX:.2f}",
            "commercial": "no published comparable (single-band)",
            "published": (
                "Nobody commercial publishes hourly fleet correlation; NREL "
                "guidance (TP-581-42305) is that hour-by-hour comparison to "
                "actuals is not a valid PCM test at all. Kept — stricter than "
                "practice — because dispatch timing feeds storage and scarcity "
                "coincidence in the intended uses."
            ),
        },
        {
            "criterion": "C6/C7/C8 protective gates",
            "target": "pass/fail (unchanged from rubric v1)",
            "commercial": "beyond commercial practice",
            "published": (
                "Published practice openly tunes to residuals — NYISO closed its "
                "benchmark gap with tuned hurdle rates; SEM tunes generator "
                "markups. Our C6 forbids exactly that (no residual-fitted "
                "parameter, no pinning, exogenous outages), and C7/C8 gate the "
                "diurnal shape and forced-energy share no external model reports."
            ),
        },
    ]
    return {
        "note": (
            "Rubric v2 (2026-07-06): graded load-bearing criteria are two-band — "
            "inside the TARGET band = target-grade PASS; between target and the "
            "evidence-anchored COMMERCIAL band = auto caveat (within commercial "
            "grade, listed with magnitude, unbudgeted); beyond = FAIL unless a "
            "measured-input limitation is ledgered (budgeted, ≤3; protective ≤1). "
            "CALIBRATED-WITH-CAVEATS certifies intended-use delivery at or above "
            "the demonstrated commercial-model grade. Where our keepers sit below "
            "commercial grade the verdict stays NOT-YET — the benchmark is an "
            "anchor, never a curve. Sources and evidence grades: "
            "docs/rubric-v2-benchmark-memo-2026-07.md."
        ),
        "rows": rows,
    }


def methodology() -> list[dict]:
    """Best-practice notes for the page footer (energy-modeling grounding)."""
    return [
        {
            "head": "Grid-delivered basis (model-grid vs actual-grid)",
            "body": "The model is scored on the grid-delivered basis — grid LP "
            "dispatch with no behind-the-meter CHP add-back — against EIA-923 net "
            "generation minus the per-class BTM CHP host steam (btm.parquet), with "
            "EIA-930 as the grid total. Both sides exclude the behind-the-meter steam "
            "the LP never saw, so a class error is a genuine merit-order signal, not a "
            "boundary-of-accounting artefact.",
        },
        {
            "head": "Solar & wind benchmarked to EIA-930, not 923",
            "body": "Distributed and utility VRE volumes are checked against EIA-930 "
            "(923 under-counts distributed VRE and collapses in the incomplete "
            "current-year vintage). VRE is report-only context (±10% advisory): a "
            "backcast feeds measured VRE potential, so a VRE volume miss is an "
            "input/curtailment-accounting issue, not a dispatch-mechanism defect.",
        },
        {
            "head": "Two-band price scoring (rubric v2, 2026-07-06)",
            "body": "Mean LMP is scored against a ±5% TARGET band — the criterion "
            "the SEM (Ireland) regulator states for its official PLEXOS model — "
            "and a ±10% COMMERCIAL band (the demonstrated planning grade; NYISO's "
            "accepted GE MAPS benchmark ran −2% to −17% zonal). A miss between the "
            "bands is recorded as 'within commercial grade, target missed', never "
            "silently absorbed and never hard-failed at a standard no external "
            "model demonstrates. The energy-only LP dual structurally under-shoots "
            "the actual LMP; that gap is closed by real reserve/scarcity "
            "mechanisms — never by an adder tuned to the residual (C6). Market "
            "monitors' own competitive re-simulations sit 0–4% from actual prices "
            "(the conduct wedge): residuals below ~3% are identification noise, "
            "not skill to chase.",
        },
        {
            "head": "Intended-use tiers (rubric v2 §0)",
            "body": "Criteria are tiered by what the model is asked to deliver "
            "(multi-ISO 2026–2050 price/dispatch/emissions forecasting, capacity "
            "evolution, policy analysis, probability bands): LOAD-BEARING "
            "(price level & seasonal shape, generation mix, CO₂) carry the "
            "two-band commercial anchors; SUPPORTING (hourly correlation, "
            "tail-hour counts) carry wide gross-defect bands; PROTECTIVE "
            "(governance, diurnal shape, forced-energy share) are unchanged from "
            "v1 — they are what make the accuracy rows believable. The DA−RT "
            "risk premium is out of representation for a realized-weather LP: "
            "DA price comparisons are reported as diagnostics, never gated "
            "(the tail criterion judges the actual RT hourly tail since v2.7; "
            "storage cycling left the rubric the same day — EIA-930 storage "
            "data is not yet a calibration judgment).",
        },
        {
            "head": "Preliminary-vintage reconcile (0.97) + per-class completeness gate",
            "body": f"The current-year ({cv.PRELIM_923_FROM_YEAR}+) EIA-923 release is a "
            "preliminary survey that under-counts thermal generation because plants are "
            "still reporting (2025: ~43% of plants nationally at audit time). A per-(ISO, "
            "class) completeness audit (scripts/audit_eia923_completeness.py) marks each "
            "class COMPLETE only when its prior-year plants all report and its whole "
            "fossil family reported; the C1 fuel-mix gate then scores only those classes "
            "(e.g. ERCOT coal 2025) and SKIPS the rest. At the family level, when the "
            f"grid-delivered 923 family total falls below {cv.VINTAGE_RECONCILE_FRAC:.2f}× "
            "the complete EIA-930 grid series, C2 scales the classes up to the EIA-930 "
            "total (split and monthly shape preserved) so the model is compared against a "
            "complete benchmark, not a partial survey.",
        },
        {
            "head": "Keeper = most structurally faithful, not lowest error",
            "body": "A run is a keeper because its mechanisms most faithfully reproduce "
            "the market (claude.md #1/#11/#12), not because it has the lowest residual. "
            '"Calibrated" is a claim that the model\'s mechanisms reproduce the market '
            "— not that residuals were tuned to zero. Accordingly the rubric is built "
            "to FAIL a keeper: any out-of-tolerance criterion that is not an explicit, "
            "ledgered ACCEPTED MEASURED-INPUT LIMITATION forces NOT-YET. See "
            "docs/calibration-determination-rubric.md and "
            "docs/multi-iso/05-backcast-playbook.md.",
        },
    ]


def _iso_sort_key(iso: str) -> tuple[int, str]:
    return (ISO_ORDER.index(iso) if iso in ISO_ORDER else len(ISO_ORDER), iso)


def build_shared() -> dict:
    """The ISO-independent status payload (``window.BC.statusShared``).

    Deliberately carries NO timestamp: its bytes are a pure function of the
    scorer/rubric constants, so any session can rewrite it and get identical
    bytes unless the rubric itself changed — conflict-free by construction.
    """
    return {
        "rubric_version": cv.RUBRIC_VERSION,
        "iso_order": list(ISO_ORDER),
        "rubric": rubric(),
        "benchmark": benchmark(),
        "methodology": methodology(),
    }


def _src_tag(run_id: str) -> str:
    """Short per-run label for the year table and the record ``src`` column.

    Just the run id with its leading ``YYYY-MM-DD-`` date stripped — mechanical,
    so it stays stable and needs no hand-maintained nickname table.
    """
    parts = run_id.split("-", 3)
    return parts[3] if len(parts) == 4 and parts[0].isdigit() else run_id


def _holdout_companions(iso: str, keeper_run_id: str) -> list[dict]:
    """Registry sidecars whose ``holdout.keeper`` folds them onto this keeper.

    A rule-22 validation touchpoint is the designated keeper's OWN frozen recipe
    replayed on a year it was never tuned on (rule 30 [R-TOUCHPOINT-FOLD]), so
    it is found the same way the Run Explorer folds it — never hand-authored.
    """
    out = []
    for sidecar in sorted(cv.REGISTRY_DIR.glob("*.json")):
        try:
            reg = json.loads(sidecar.read_text())
        except (OSError, ValueError):
            continue
        if reg.get("iso") != iso or reg.get("id") == keeper_run_id:
            continue
        if (reg.get("holdout") or {}).get("keeper") != keeper_run_id:
            continue
        out.append(reg)
    return out


def build_years(iso: str, keeper_run_id: str, configs: list[dict]) -> list[dict]:
    """Score EVERY year of this keeper — training and held-out — one row each.

    One uniform table replaces the former three bespoke blocks (config
    partition, holdout touchpoint, holdout ladder): a year is a year, scored
    individually with the same scorer the gate uses, whichever tier it sits in.
    Per-year scoring is the load-bearing detail on both sides — a multi-year
    bundle carries ONE run-level determination that can hide a year which passed
    on its own (NEISO 2020+2021 reads NOT-YET as a bundle; 2021 alone is
    CALIBRATED), and a partitioned keeper's designated config differs per year.

    Held-out rows NEVER gate: the ISO determination is the train-tier
    (2023-2025) verdict — rule 22 as amended 2026-09-05, an ISO stays CALIBRATED
    even when a held-out year degrades, because a validation-tier score is
    iterable model-SELECTION evidence and not a certification.

    Args:
        iso: ISO id, used to scope the registry scan for folded companions.
        keeper_run_id: The ISO's current designated keeper run id.
        configs: Designated partition configs (``role``/``run_id``/``years``),
            empty for a single-config keeper.

    Returns:
        One row per (year, source run), oldest year first: tier, determination,
        the run it was scored from and that run's short ``src`` tag.
    """
    rows: list[dict] = []

    def add(run_id: str, year: int, tier: str, role: str | None) -> None:
        try:
            v = cv.determine(run_id, years=[year])
        except Exception as exc:  # a companion must never abort the lane
            print(f"  {iso}: {year} unscorable from {run_id} ({exc})", file=sys.stderr)
            return
        rows.append(
            {
                "year": year,
                "tier": tier,
                "role": role,
                "determination": v.get("determination"),
                "reasons": v.get("reasons") or [],
                "run_id": run_id,
                "src": _src_tag(run_id),
            }
        )

    if configs:
        for cfg in configs:
            for year in sorted(int(y) for y in cfg.get("years", [])):
                add(cfg["run_id"], year, "training", cfg.get("role"))
    else:
        sidecar = json.loads((cv.REGISTRY_DIR / f"{keeper_run_id}.json").read_text())
        for year in sorted(int(y) for y in (sidecar.get("years") or [])):
            add(keeper_run_id, year, "training", None)

    for reg in _holdout_companions(iso, keeper_run_id):
        tier = (reg.get("holdout") or {}).get("tier") or "validation"
        for year in sorted(int(y) for y in (reg.get("years") or [])):
            add(reg["id"], year, tier, None)

    rows.sort(key=lambda r: (r["year"], r["src"]))
    return rows


def merge_holdout_records(iso: str, keeper_run_id: str, verdict: dict) -> None:
    """Fold every held-out year's criterion records into the keeper's own tables.

    Rule 30 [R-TOUCHPOINT-FOLD]: a touchpoint IS the keeper on another year, so
    its numbers belong in the SAME per-criterion table as the training years,
    in the same columns, rather than in a parallel block with its own layout.

    Records only — the criterion-level ``status`` badges and ``grade_summary``
    are the train-tier verdict and are left untouched, so folding a held-out
    year in can never move the ISO's determination (rule 22).
    """
    for reg in _holdout_companions(iso, keeper_run_id):
        try:
            v = cv.determine(reg["id"])
        except Exception as exc:
            print(f"  {iso}: holdout {reg['id']} unscorable ({exc})", file=sys.stderr)
            continue
        src = _src_tag(reg["id"])
        for block in ("criteria", "reported"):
            for key, crit in (v.get(block) or {}).items():
                dest = (verdict.get(block) or {}).get(key)
                if dest is None:
                    continue
                for rec in crit.get("records") or []:
                    dest.setdefault("records", []).append({**rec, "src": src})
    keeper_src = _src_tag(keeper_run_id)
    for block in ("criteria", "reported"):
        for crit in (verdict.get(block) or {}).values():
            for rec in crit.get("records") or []:
                rec.setdefault("src", keeper_src)
            crit["records"] = sorted(
                crit.get("records") or [],
                key=lambda r: (r.get("year") or 0, r.get("src") or ""),
            )


def build_part(iso: str) -> dict | None:
    """Score one ISO's current keeper into its status part payload.

    Returns None (with a stderr note) when the ISO has no scorable keeper —
    a missing shard or sidecar must never abort the other lanes.
    """
    rec = keeper_store.load_shard(iso) or {}
    run_id = rec.get("keeper")
    if not run_id:
        print(f"  skip {iso}: no keeper in keepers/{iso}.json", file=sys.stderr)
        return None
    if not (cv.REGISTRY_DIR / f"{run_id}.json").exists():
        print(f"  skip {iso}: keeper {run_id} has no registry sidecar", file=sys.stderr)
        return None
    statmode = (
        json.loads(STATMODE_D7_FILE.read_text()) if STATMODE_D7_FILE.exists() else {}
    )
    verdict = cv.determine(run_id)
    # Owner-declared "frontier achieved" designation (the shard's "frontier"
    # block): every named admissible mechanism for the ISO's residual caveats
    # has been tried on record, and what remains is either inadmissible
    # (residual-fitting, rule 26) or blocked on data that does not exist
    # publicly. Rendered as a badge + note on the Calibration Status page;
    # purely declarative — never gating, never touching the verdict.
    if rec.get("frontier"):
        verdict["frontier"] = rec["frontier"]
    # Owner-signed STANDING NOTE (the shard's "standing_note" block): a durable
    # statement about what the ISO's remaining misses ARE — e.g. several scored
    # criteria that are one adjudicated object rather than independent defects.
    # Same contract as "frontier" above: purely declarative, never gating, never
    # touching the verdict, and it never restates or softens a magnitude — every
    # criterion keeps reporting its own number from the scorer. Added by
    # ercot-210 for the ERCOT card-X item X-2 signature (Door C of
    # docs/ASSESSMENT-ercot209-2023-scarcity-calibration-path-2026-08-15.md).
    if rec.get("standing_note"):
        verdict["standing_note"] = rec["standing_note"]
    # Owner-declared TOUCHPOINT designation (the shard's "frontier_touchpoint"
    # block): a statement that the ISO's folded held-out rungs (rule 30
    # [R-TOUCHPOINT-FOLD]) score CALIBRATED in their own right, which is the
    # strictly stronger claim than rule 30(c)'s "a held-out year never
    # downgrades the ISO". Same contract as "frontier" and "standing_note"
    # above: purely declarative, attached AFTER determine(), never gating,
    # never touching a verdict, grade, caveat budget or magnitude. It is NOT a
    # skill claim -- since [R-HOLDOUT] was removed (2026-09-09) no year is
    # protected from being iterated against, so a passing rung is model-
    # SELECTION evidence and the block's own note says so.
    if rec.get("frontier_touchpoint"):
        verdict["frontier_touchpoint"] = rec["frontier_touchpoint"]
    # Owner-declared CONFIG PARTITION (the shard's "config_partition" block —
    # the two-config keeper structure, owner ruling 2026-08-26): the ISO's
    # training window is covered by more than one designated config (e.g.
    # ERCOT's 2023 ECRS-regime carve-out vs the 2024/2025 forward keeper).
    # Each config is scored LIVE here, twice: on its designated span (the
    # partition read) and on its full registered span (so a NOT-YET half can
    # never be laundered out of view by the partition). The page renders BOTH
    # configs with year spans and their own determinations — never only the
    # more flattering one. The ISO-LEVEL determination of a partitioned
    # keeper is the WORST config determination over the DESIGNATED spans
    # (owner ruling 2026-08-31, session ercot-246 — the same conservative
    # ordering the status page's partition accent already used; it
    # supersedes the ercot-238 "primary verdict stays the forward keeper's
    # registered full-span determination" convention). The registered
    # full-span read is preserved at full magnitude in
    # `registered_determination`/`registered_reasons` and per config below,
    # and every criterion record keeps reporting its own number — the
    # ruling moves the headline, never the magnitudes.
    if rec.get("config_partition"):
        cp = rec["config_partition"]
        scored_configs = []
        for cfg in cp.get("configs", []):
            span = [int(y) for y in cfg.get("years", [])]
            span_v = cv.determine(cfg["run_id"], years=span)
            full_v = cv.determine(cfg["run_id"])
            # RULE 30(c) [R-TOUCHPOINT-FOLD]: "The ISO's calibration
            # determination is the train-tier (2023-2025) verdict and nothing
            # else. A validation-tier score is iterable model-SELECTION evidence
            # ... it cannot certify and it cannot decertify." A partition may
            # now designate a HELD-OUT span (ERCOT 2021/2022 since ercot-255),
            # so such a config is scored and RENDERED exactly like any other but
            # is excluded from the ISO-level worst-over-spans fold below.
            # Absent/`train` keeps every pre-existing ISO byte-identical.
            cfg_tier = str(cfg.get("tier") or "train").lower()
            scored_configs.append(
                {
                    "role": cfg.get("role"),
                    "label": cfg.get("label"),
                    "run_id": cfg["run_id"],
                    "years": span,
                    "tier": cfg_tier,
                    "gating": cfg_tier == "train",
                    "determination": span_v["determination"],
                    "reasons": span_v.get("reasons", []),
                    "grade_summary": span_v.get("grade_summary"),
                    "registered_determination": full_v["determination"],
                    "registered_reasons": full_v.get("reasons", []),
                    "registered_years": full_v.get("target_years", []),
                }
            )

        def _det_rank(det: str) -> int:
            # Worst-first ordering, mirroring the renderer's partition accent.
            d = (det or "").upper()
            if "NOT" in d:
                return 0
            if "CAVEAT" in d:
                return 1
            return 2

        # Rule 30(c): fold over the TRAIN-tier configs only. Held-out configs
        # stay in scored_configs (so the page renders them at full magnitude)
        # but never move the ISO headline in either direction.
        partition_det = min(
            (c["determination"] for c in scored_configs if c["gating"]),
            key=_det_rank,
            default=verdict["determination"],
        )
        verdict["registered_determination"] = verdict["determination"]
        verdict["registered_reasons"] = verdict.get("reasons", [])
        verdict["determination"] = partition_det
        verdict["reasons"] = [
            r for c in scored_configs if c["gating"] for r in c["reasons"]
        ]
        verdict["determination_basis"] = (
            "config-partition: worst config determination over the DESIGNATED "
            "spans (owner ruling 2026-08-31, session ercot-246). The forward "
            "keeper's registered full-span determination is preserved in "
            "registered_determination and per config, at full magnitude."
        )
        verdict["config_partition"] = {
            "declared": cp.get("declared"),
            "ruling": cp.get("ruling"),
            "iso_determination": partition_det,
            "iso_determination_ruling": cp.get("iso_determination_ruling"),
            "coverage_invariant": cp.get("coverage_invariant"),
            "configs": scored_configs,
        }
    d7 = statmode.get("isos", {}).get(iso)
    if d7:
        # REPORTED line, never gating: the overlay-vs-statistical fail
        # gap (audit D-7). ``stale`` marks a gap measured against a
        # since-replaced keeper — re-measure with run_statmode_probe.py.
        verdict["statmode_d7"] = {
            **d7,
            "measured": statmode.get("measured"),
            "source": statmode.get("source"),
            "stale": d7.get("measured_against") != run_id,
        }
    # ONE uniform per-year table — training years (per designated config) and
    # rule-22 held-out years in the same rows, scored the same way, and every
    # held-out year's criterion records folded into the SAME per-criterion
    # tables (rule 30 [R-TOUCHPOINT-FOLD]). Held-out rows report; they never
    # gate — the ISO determination above is the train-tier verdict (rule 22).
    verdict["years"] = build_years(
        iso, run_id, (verdict.get("config_partition") or {}).get("configs") or []
    )
    merge_holdout_records(iso, run_id, verdict)
    return {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "keeper": verdict,
    }


def serialize_shared(payload: dict) -> str:
    """Render ``status/shared.js`` (compact, deterministic — no timestamp)."""
    return (
        "window.BC=window.BC||{};window.BC.statusShared="
        + json.dumps(payload, sort_keys=True, separators=(",", ":"))
        + ";"
    )


def serialize_part(iso: str, payload: dict) -> str:
    """Render one ``status/<ISO>.js`` part (compact, deterministic)."""
    return (
        "window.BC=window.BC||{};window.BC.statusParts=window.BC.statusParts||{};"
        + f"window.BC.statusParts[{json.dumps(iso)}]="
        + json.dumps(payload, sort_keys=True, separators=(",", ":"))
        + ";"
    )


def _strip_gen(js_text: str, marker: str) -> str:
    """Canonical JSON of a part/shared file with the timestamp removed."""
    obj = json.loads(js_text.split(marker, 1)[1].rstrip().rstrip(";"))
    if isinstance(obj, dict):
        obj.pop("generated", None)
    return json.dumps(obj, sort_keys=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--iso",
        nargs="+",
        metavar="ISO",
        help="rebuild only these ISOs' status parts (default: every ISO). "
        "shared.js is always (re)written — deterministic, byte-identical "
        "unless the rubric changed.",
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="verify the status parts match the current verdicts (ignoring "
        "timestamps); exit 1 if any is stale.",
    )
    args = ap.parse_args()
    all_isos = keeper_store.iso_list()
    if not all_isos:
        raise SystemExit("no ISOs in the keeper store — cannot build status.")
    targets = [i.upper() for i in args.iso] if args.iso else list(all_isos)
    unknown = [i for i in targets if i not in all_isos]
    if unknown:
        raise SystemExit(f"unknown ISO(s) {unknown} — known: {all_isos}")

    shared_text = serialize_shared(build_shared())
    parts = {iso: build_part(iso) for iso in targets}
    built = {iso: p for iso, p in parts.items() if p is not None}
    if not built:
        raise SystemExit("no scorable keepers found; refusing to write empty parts.")

    if args.check:
        stale: list[str] = []
        if not SHARED_FILE.exists() or _strip_gen(
            SHARED_FILE.read_text(), "window.BC.statusShared="
        ) != _strip_gen(shared_text, "window.BC.statusShared="):
            stale.append(str(SHARED_FILE))
        for iso, part in built.items():
            path = STATUS_DIR / f"{iso}.js"
            marker = f"window.BC.statusParts[{json.dumps(iso)}]="
            if not path.exists() or _strip_gen(path.read_text(), marker) != _strip_gen(
                serialize_part(iso, part), marker
            ):
                stale.append(str(path))
        if stale:
            sys.exit(
                "stale vs the current verdicts: "
                + ", ".join(stale)
                + " — re-run: python scripts/build_status.py"
                + (" --iso " + " ".join(targets) if args.iso else "")
            )
        print(f"status parts in sync ({len(built)} keepers: {', '.join(built)}).")
        return

    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    SHARED_FILE.write_text(shared_text)
    for iso, part in built.items():
        (STATUS_DIR / f"{iso}.js").write_text(serialize_part(iso, part))
    dets = ", ".join(f"{i}:{p['keeper']['determination']}" for i, p in built.items())
    print(
        f"wrote {SHARED_FILE.relative_to(REPO)} + {len(built)} part(s) under "
        f"{STATUS_DIR.relative_to(REPO)}/ [{dets}]"
    )


if __name__ == "__main__":
    main()
