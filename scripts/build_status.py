"""Emit the all-ISO Calibration Status data file for the backcast dashboard.

The dashboard's "Calibration Status" view (one page, every ISO) renders entirely
client-side from ``frontend/data/backcast/status.js`` — a committed
``window.BC.status`` payload this script produces. For each ISO's CURRENT keeper
(listed in ``frontend/data/backcast/keepers.json``) it runs the SAME scorer the
gate uses — ``scripts/calibration_verdict.py`` — and embeds the full machine
verdict, so the page can never disagree with ``calibration_verdict.py``. It also
emits the rubric reference (what each criterion measures, its authoritative actual
source, and its tolerance — the tolerances read straight off the scorer's module
constants, never re-typed) and the best-practice methodology notes.

Why a COMMITTED file (mirroring ``runs/<id>.js``) rather than a deploy-time
rebuild like manifest.js/benchmark.js: the C6 governance verdict reads each
bundle's ``calibration_attestation.json`` / ``run_config.json`` under
``results/calibration/``, which the GitHub Pages deploy's sparse checkout does
NOT fetch. So the verdict can only be computed where the bundles live — here,
locally — and the result is committed. ``build_manifest.py`` merely wires the
committed ``status.js`` into the shell (it does not regenerate it).

Stdlib-only (json, calibration_verdict). Run after a keeper changes:

    python scripts/build_status.py            # refresh frontend/data/backcast/status.js
    python scripts/build_status.py --check     # verify status.js is in sync, exit 1 if not
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

DATA = REPO / "frontend" / "data" / "backcast"
KEEPERS_FILE = DATA / "keepers.json"
STATUS_FILE = DATA / "status.js"
# D-7 statistical-mode fail-count gaps (REPORTED next to each keeper, never
# gating): committed data seeded from docs/statistical-mode-results-2026-07.md,
# refreshed whenever a statmode probe re-measures a keeper.
STATMODE_D7_FILE = DATA / "statmode_d7.json"

# Display order for the ISO card grid (others fall in alphabetically after these).
ISO_ORDER = ("ERCOT", "PJM", "CAISO", "NYISO", "NEISO", "MISO")


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
            f"±{cv.PRICE_MEAN_TOL * 100:.0f}% target / "
            f"±{cv.PRICE_MEAN_COMMERCIAL * 100:.0f}% commercial. The target is the "
            "SEM (Ireland) regulator's stated criterion for its official PLEXOS "
            "model; the commercial band is the demonstrated planning grade (NYISO's "
            "accepted GE MAPS benchmark ran −2% to −17% zonal). Between the bands "
            "→ auto caveat (within commercial grade, target missed); beyond → FAIL "
            "unless a measured-input limitation is ledgered.",
        ),
        row(
            "price_shape",
            "NRMSE between model and actual monthly load-weighted price vectors.",
            "Actual monthly RT price (avgLMP.rt_mon), falling back to DA.",
            f"NRMSE ≤ {cv.PRICE_SHAPE_NRMSE_MAX:.2f} target / "
            f"≤ {cv.PRICE_SHAPE_NRMSE_COMMERCIAL:.2f} commercial (published monthly "
            "norms run ~5–15%; SEM's regulator-accepted backcast carried −9% "
            "winter-peak / +11% off-peak period biases).",
        ),
        row(
            "price_tail",
            "Count of scarcity-tail hours — model vs the DA-EXPRESSIBLE actual "
            "(the hourly, commitment-aware day-ahead market's own count above the "
            "threshold: the same temporal resolution as the model LP). The RT "
            "count — which folds in sub-hourly ramp/re-dispatch transients an "
            "hourly deterministic LP cannot see — is reported as a non-gated "
            "diagnostic row. The DA basis is not a leniency device: ERCOT's DA "
            "tail is LARGER than its RT tail (2023: 311 vs 181 h).",
            "Committed tail part frontend/data/backcast/tail/actual_tail.json "
            "(scripts/derive_actual_tail.py, from the measured hub RT/DA hourly "
            "series; 2023–2025 only). Thresholds: " + _tail_note() + ".",
            f"model within [{cv.TAIL_LO:g}×, {cv.TAIL_HI:g}×] of the DA actual — a "
            "collapsed tail and an invented tail both FAIL; a DA actual below "
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
            "Annual system CO₂, model vs eGRID ISO total.",
            "eGRID ISO-year total (committed in the bundle's emissions summary).",
            f"±{cv.CO2_TOL * 100:.0f}% target / ±{cv.CO2_COMMERCIAL * 100:.0f}% "
            "commercial (no production-cost model publishes a backcast CO₂ error; "
            "the AEO retrospective's 1–3-year CO₂ error SD is 3.2–4.9% on full "
            "forecasts — the target is stricter than any published requirement).",
        ),
        row(
            "storage",
            "Annual storage (battery + pumped-storage) discharge throughput (TWh) — "
            "cycling realism, not arbitrage perfection.",
            "EIA-923 / ISO battery-report throughput.",
            f"±{cv.STORAGE_TOL * 100:.0f}%.",
        ),
        row(
            "governance",
            "Every active lever traces to a measured input; no fit to price residuals; "
            "no pinning to actuals; the outage filter keys on exogenous net load.",
            "run_config.json (machine cross-check) + calibration_attestation.json "
            "(four assertions, all required true).",
            "pass/fail — never graded, never caveatable; an unattested run is NOT-YET.",
        ),
        row(
            "shape",
            "Per-class hour-of-day mean dispatch profile, model vs CAMPD, for the "
            "peaker/intermediate duty classes (CT_PEAKER, ST_GAS) — the diurnal-shape "
            "check a flat forced floor cannot pass (audit D-1; the caiso-42 signature "
            "was model off-peak CV 0.000 vs actual 0.35–0.45). Added 2026-07-04: the "
            "statistical-mode study showed the C1 volume band absorbed a >6× ERCOT "
            "CT_PEAKER miss — annual volume bands cannot see class-shape failure.",
            "The bundle's committed legitimacy_diagnostics.json (written by "
            "scripts/legitimacy_diagnostics.py --json-out; model payload vs the "
            "committed CAMPD bench series). SKIPPED — capping the determination — "
            "when the artifact is absent.",
            "profile r ≥ 0.8 AND off-peak (h0–14) CV ratio ≥ 0.5, per gated class "
            "(thresholds live in scripts/legitimacy_diagnostics.py D1_*, embedded in "
            "the artifact's gates block — re-stated here, never re-typed by the "
            "scorer). Materiality floor (v2.1, owner amendment 2026-07-06): gated "
            f"only for classes ≥ {cv.PROTECTIVE_MIN_LOAD_FRAC:.0%} of total ISO load "
            "(max of model/actual energy, so forcing can't hide a class below the "
            "line); smaller classes are reported by the diagnostics, never gated.",
        ),
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
            "target": f"±{cv.PRICE_MEAN_TOL * 100:.0f}%",
            "commercial": f"±{cv.PRICE_MEAN_COMMERCIAL * 100:.0f}%",
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
            "target": f"≤{cv.PRICE_SHAPE_NRMSE_MAX:.2f}",
            "commercial": f"≤{cv.PRICE_SHAPE_NRMSE_COMMERCIAL:.2f}",
            "published": (
                "SEM regulator-accepted backcast period biases: −9% winter-peak / "
                "+11% off-peak; published monthly norms ~5–15% with correct "
                "seasonality; PyPSA-Eur 2020–24 hindcast weekly SMAPE 20–26% "
                "(academic state of the art for the model class)."
            ),
        },
        {
            "criterion": "C3c scarcity tail (DA-expressible hours)",
            "target": f"[{cv.TAIL_LO:g}×, {cv.TAIL_HI:g}×] of the DA actual",
            "commercial": "no published comparable",
            "published": (
                "NO commercial or public model publishes tail-hour or "
                "duration-curve accuracy as a fitness criterion. Documented "
                "practice goes the other way: ECA excluded ~50–100 h/month of "
                "price-spike events from its scoring; NYISO absorbed the residual "
                "into tuned hurdle rates; PyPSA-Eur reports spikes 'not captured "
                "well' in every configuration. This rubric keeps scoring the tail "
                "— stricter than practice — on the scope-consistent DA basis."
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
            "criterion": "C5a system CO₂",
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
            "two-band commercial anchors; SUPPORTING (hourly correlation, storage "
            "cycling, tail-hour counts) carry wide gross-defect bands; PROTECTIVE "
            "(governance, diurnal shape, forced-energy share) are unchanged from "
            "v1 — they are what make the accuracy rows believable. RT sub-hourly "
            "transients and the DA−RT risk premium are out of representation for "
            "an hourly DA-analogue LP and are reported as diagnostics, never "
            "gated.",
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


def build() -> dict:
    """Score every current keeper and assemble the status payload."""
    if not KEEPERS_FILE.exists():
        raise SystemExit(f"no keeper list at {KEEPERS_FILE} — cannot build status.")
    spec = json.loads(KEEPERS_FILE.read_text())
    statmode = (
        json.loads(STATMODE_D7_FILE.read_text()) if STATMODE_D7_FILE.exists() else {}
    )
    keepers = []
    for run_id in spec.get("keepers", []):
        if not (cv.REGISTRY_DIR / f"{run_id}.json").exists():
            print(f"  skip {run_id}: no registry sidecar", file=sys.stderr)
            continue
        verdict = cv.determine(run_id)
        d7 = statmode.get("isos", {}).get(verdict["iso"])
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
        keepers.append(verdict)
    keepers.sort(key=lambda v: _iso_sort_key(v["iso"]))
    if not keepers:
        raise SystemExit(
            "no scorable keepers found; refusing to write an empty status."
        )
    return {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "rubric_version": cv.RUBRIC_VERSION,
        "rubric": rubric(),
        "benchmark": benchmark(),
        "methodology": methodology(),
        "keepers": keepers,
    }


def serialize(payload: dict) -> str:
    """Render the ``window.BC.status`` data file (compact, deterministic)."""
    return (
        "window.BC=window.BC||{};window.BC.status="
        + json.dumps(payload, sort_keys=True, separators=(",", ":"))
        + ";"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check",
        action="store_true",
        help="verify status.js matches the current verdicts (ignoring the timestamp); "
        "exit 1 if it is stale.",
    )
    args = ap.parse_args()
    payload = build()
    text = serialize(payload)
    if args.check:
        if not STATUS_FILE.exists():
            sys.exit(f"{STATUS_FILE} missing — run: python scripts/build_status.py")
        cur = STATUS_FILE.read_text()

        def _strip_gen(s: str) -> str:
            obj = json.loads(s.split("window.BC.status=", 1)[1].rstrip().rstrip(";"))
            obj.pop("generated", None)
            return json.dumps(obj, sort_keys=True)

        if _strip_gen(cur) != _strip_gen(text):
            sys.exit(
                f"{STATUS_FILE} is stale vs the current verdicts — "
                "re-run: python scripts/build_status.py"
            )
        print(f"{STATUS_FILE.name} is in sync ({len(payload['keepers'])} keepers).")
        return
    STATUS_FILE.write_text(text)
    dets = ", ".join(f"{v['iso']}:{v['determination']}" for v in payload["keepers"])
    print(f"wrote {STATUS_FILE} — {len(payload['keepers'])} keepers [{dets}]")


if __name__ == "__main__":
    main()
