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
    L = {cid: lab for cid, (lab, _h) in cv.CRITERIA.items()}
    H = {cid: hard for cid, (_l, hard) in cv.CRITERIA.items()}

    def row(cid, measures, source, tol):
        return {
            "id": cid,
            "label": L[cid],
            "hard": H[cid],
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
            f"±{cv.SYSVOL_TOL * 100:.1f}% of the family total "
            f"(families < {cv.SYSVOL_MIN_TWH:.0f} TWh are immaterial → governed by C1).",
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
            f"±{cv.PRICE_MEAN_TOL * 100:.0f}% — the tight end of the playbook's 5–10% "
            "band (tightened from 8% in the 2026-07-02 re-balance): price accuracy is "
            "the primary market signal, and the energy-only dual's structural "
            "under-shoot is to be closed by real reserve/scarcity mechanisms, not "
            "absorbed by a wide tolerance.",
        ),
        row(
            "price_shape",
            "NRMSE between model and actual monthly load-weighted price vectors.",
            "Actual monthly RT price (avgLMP.rt_mon), falling back to DA.",
            f"NRMSE ≤ {cv.PRICE_SHAPE_NRMSE_MAX:.2f}.",
        ),
        row(
            "price_tail",
            "Count of scarcity-tail hours (LMP above the per-ISO threshold) — model "
            "vs actual.",
            "ERCOT ORDC reserve-price adder hours (ordc block); otherwise the "
            "committed hourly actual-LMP series. Thresholds: " + _tail_note() + ".",
            f"model within [{cv.TAIL_LO:g}×, {cv.TAIL_HI:g}×] of actual — a collapsed "
            "tail and an over-fired tail both FAIL.",
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
            f"±{cv.CO2_TOL * 100:.0f}%.",
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
            "scorer).",
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
            "forced share < 10% for peaker classes, < 30% for any merchant class "
            "(scripts/legitimacy_diagnostics.py D2_*).",
        ),
    ]


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
            "head": "Why ±5% on mean LMP (2026-07-02 re-balance)",
            "body": "An energy-only LP's dual price structurally under-shoots the true "
            "market LMP, which carries reserve, scarcity and uplift adders the "
            "energy-only price does not model. The mean-price band sits at the tight "
            "end of the backcast playbook's 5–10% tolerance (tightened from ±8% on "
            "2026-07-02, alongside a looser per-class fuel-mix band): the structural "
            "under-shoot is to be closed by real reserve/scarcity mechanisms — never "
            "by an adder tuned to the residual — and a wide price tolerance was "
            "quietly absorbing that gap instead of surfacing it.",
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
        "rubric": rubric(),
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
