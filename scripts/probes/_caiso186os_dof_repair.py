"""caiso-186 (OWNER SITTING) — the CAISO DOF-ledger REPAIR audit.

NO LP, NO SOLVE, NO NETWORK. Reads only committed bytes: the six ISOs' current
keeper attestations, the CAISO keeper's ``run_config.json``, and the committed
config/spec modules the surviving CAISO rows point at.

The object. ``ASSESSMENT-caiso171-frontier-2026-08-04.md`` §3 measured CAISO at
**4 ISO-specific residual DOF entries — the most of any ISO** (NEISO 0, PJM 1,
NYISO 2), of which *"two are superseded on the binding path and one rests on a
closure route that does not check out."* That census is a **2026-08-04
measurement on the caiso-170-era keeper** and is quoted forward as if current.
This probe re-derives it at HEAD and audits each surviving CAISO row's WIRING
against the keeper's own ``run_config`` — because a row's ledger text can say
"superseded on the binding path" while the config that would supersede it is
off, or while only one of its limbs is actually superseded.

Three checks:

* **R1 CENSUS** — the caiso-171 F2 statistic recomputed on today's six keeper
  attestations, same ``CORE_RESIDUAL`` partition, so the comparison is
  like-for-like.
* **R2 WIRING** — for each surviving CAISO ISO-specific residual row, the
  keeper ``run_config`` flags that determine whether the row is on the LP's
  binding path, read from the bundle rather than assumed.
* **R3 LIMB SPLIT** — ``IMPORT_TRANCHES``/``IMPORT_TRANCHES_BY_YEAR`` for CAISO
  split into its four limbs (firm capacity / firm price / spot capacity / spot
  price), each with its own identification, because the single ledger row
  currently carries one verdict for all four.

Every verdict below is a statement about **wiring and provenance**, never about
fit. No scored criterion is read and no residual is consulted (rule 1
``[R-STRUCT]``, rule 13 ``[R-MEASURED]``).

Usage::

    uv run python scripts/probes/_caiso186os_dof_repair.py

Writes ``results/calibration/_caiso186os_dof_repair.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CAL = REPO / "results/calibration"
OUT = CAL / "_caiso186os_dof_repair.json"

# Current designated keeper of every ISO, read from the committed keeper shards
# at HEAD (frontend/data/backcast/keepers/<ISO>.json → registry sidecar bundle).
KEEPERS = {
    "CAISO": ("2026-08-09-caiso-184-c1-lpbasis", "caiso184_c1_lpbasis"),
    "ERCOT": ("2026-08-09-run181-position-tail", "ercot181_positiontail_B"),
    "MISO": ("2026-08-05-miso-132b-cc-committed", "miso132_ccmin_B"),
    "NEISO": ("2026-08-06-neiso-87-control", "neiso87_control_A"),
    "NYISO": ("2026-08-08-nyiso-132-cf-arm", "nyiso132_cf_arm"),
    "PJM": ("2026-08-04-pjm-152-collapse", "pjm152_collapse_A"),
}

# The five residual rows every ISO carries — shared machinery, not an ISO
# property. Verbatim from caiso171_frontier_assessment.CORE_RESIDUAL so the
# statistic composes with the caiso-171 measurement (rule 28 DO-NOT-REDO).
CORE_RESIDUAL = {
    "offer_curve_by_group",
    "offer_curve_committed_below_floor",
    "offer_curve_smoothing",
    "COAL_SIGMOID_DEFAULTS",
    "wefor_multiplier",
}

# ISOs holding a `complete` marker. CAISO's was WITHDRAWN by the owner
# 2026-08-06 (corrected at caiso-178) — it is not "held".
COMPLETE_MARKER_ISOS = {"PJM", "NYISO", "NEISO"}

# The keeper-config flags that decide whether each surviving CAISO row is on
# the LP's binding path. Read from the bundle, never assumed.
WIRING_FLAGS = (
    "capacity_deliverability_limits",
    "caiso_per_hub_intertie",
    "caiso_perhub_firm_base",
    "caiso_per_year_import_caps",
    "caiso_firm_import_selfschedule",
    "caiso_firm_import_selfsched_clip",
    "caiso_firm_import_shape",
    "caiso_firm_import_envelope_clip",
    "caiso_import_hub_prices",
    "caiso_bidir_intertie",
    "battery_dispatch_adder",
    "pumped_storage_dispatch_adder",
)


def _strip_key(name: str) -> str:
    """Return a DOF entry name with its ``[ISO]`` / ``['key']`` subscript removed."""
    return name.split("[", 1)[0].split(".", 1)[0].strip()


def attestation(bundle: str) -> dict:
    return json.loads((CAL / bundle / "calibration_attestation.json").read_text())


def run_config(bundle: str) -> dict:
    d = json.loads((CAL / bundle / "run_config.json").read_text())
    return d.get("scenario_config", d)


def r1_census() -> dict:
    rows = {}
    for iso, (run_id, bundle) in KEEPERS.items():
        fp = attestation(bundle)["free_parameters"]
        entries = fp.get("entries", [])
        residual = [e["name"] for e in entries if e.get("identification") == "residual"]
        specific = [n for n in residual if _strip_key(n) not in CORE_RESIDUAL]
        rows[iso] = {
            "keeper": run_id,
            "n_entries": fp.get("n_entries"),
            "n_residual_declared": fp.get("n_residual"),
            "n_residual_counted": len(residual),
            "n_core_residual": len(residual) - len(specific),
            "n_iso_specific_residual": len(specific),
            "iso_specific": specific,
            "holds_complete_marker": iso in COMPLETE_MARKER_ISOS,
        }
    return rows


def r2_wiring() -> dict:
    cfg = run_config(KEEPERS["CAISO"][1])
    flags = {k: cfg.get(k, "<absent>") for k in WIRING_FLAGS}
    ledger = {e["name"]: e for e in attestation(KEEPERS["CAISO"][1])["free_parameters"]["entries"]}

    verdicts = {}

    # --- row: WECC_import_simultaneous.cap_mw -----------------------------
    on_binding = not bool(cfg.get("capacity_deliverability_limits"))
    verdicts["WECC_import_simultaneous.cap_mw"] = {
        "ledger_says": ledger["WECC_import_simultaneous.cap_mw"]["source"][:160],
        "decided_by": "capacity_deliverability_limits",
        "keeper_value": cfg.get("capacity_deliverability_limits"),
        "on_backcast_binding_path": on_binding,
        "verdict": (
            "SUPERSEDED on the keeper's binding path — the published branch-group MIC seam "
            "limit replaces it; the row survives as a FORECAST-PATH residual only "
            "(capacity_deliverability_limits is GATED default-off, issue #1373). "
            "The ledger text already says this and it CHECKS OUT."
            if not on_binding
            else "LIVE on the binding path — the ledger text does NOT check out."
        ),
    }

    # --- row: battery_dispatch_adder ---------------------------------------
    verdicts["battery_dispatch_adder"] = {
        "ledger_says": ledger["battery_dispatch_adder"]["root_cause"][:200],
        "keeper_value": cfg.get("battery_dispatch_adder"),
        "on_backcast_binding_path": True,
        "verdict": (
            "LIVE and residual. The ledger's NAMED forward-valid replacement is SPENT on both "
            "halves — the measured AS power reservation was probe-adjudicated INERT (caiso-74) "
            "and refuted by arithmetic (caiso-127/129); the ATB degradation cost was built, "
            "A/B-solved and REJECTED on a pre-registered throughput guard (caiso-100/101), and "
            "on today's constants the same formula returns $22.63 rather than $14.25, i.e. "
            "FURTHER in the rejected direction. The ledger's root_cause therefore points at a "
            "closed route and is STALE. NEW identification evidence exists and is not in the "
            "ledger: FINDING-caiso176 read CAISO's OWN Daily Energy Storage Report bid_stack "
            "and bounded the fleet discharge reservation price at <= $15/MWh in all three "
            "years — a model-free UPPER bound that refutes $22.63 and admits $5.00. It BOUNDS "
            "but does not IDENTIFY: every value in (0, 15] survives, so the row stays residual."
        ),
    }

    # --- row: IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO] ------------------------
    per_hub = bool(cfg.get("caiso_per_hub_intertie"))
    firm_base = bool(cfg.get("caiso_perhub_firm_base"))
    clip = bool(cfg.get("caiso_firm_import_selfsched_clip"))
    selfsched = bool(cfg.get("caiso_firm_import_selfschedule"))
    verdicts["IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]"] = {
        "ledger_says": ledger["IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]"]["source"][:220],
        "decided_by": {
            "caiso_per_hub_intertie": per_hub,
            "caiso_perhub_firm_base": firm_base,
            "caiso_firm_import_selfschedule": selfsched,
            "caiso_firm_import_selfsched_clip": clip,
            "caiso_per_year_import_caps": cfg.get("caiso_per_year_import_caps"),
        },
        "verdict": (
            "THE LEDGER TEXT DOES NOT CHECK OUT. It reads 'CAISO's keeper supersedes the fitted "
            "ladder with measured hub prices on the binding path but the static ladder remains "
            "the fallback', which is true of ONE of the row's four limbs. "
            "inject_caiso_per_hub_intertie_prices writes mc[row, :] ONLY — it repriced nothing "
            "else — and its firm_base branch EXPLICITLY skips CAISO_FIRM_IMPORT_TRANCHES "
            "('keeps its static ladder price'). See R3 for the limb split: two limbs are "
            "closed, TWO ARE LIVE AND FITTED, and one of the two live limbs is the object "
            "FINDING-caiso140 §C measures as the thing pinning the belly lambda."
        ),
    }

    return {"keeper_flags": flags, "rows": verdicts}


def r3_limb_split() -> dict:
    """Split the CAISO import-ladder row into its four independently-identified limbs."""
    import sys

    sys.path.insert(0, str(REPO / "src"))
    from market_sim.model.interchange.spec import IMPORT_TRANCHES, IMPORT_TRANCHES_BY_YEAR
    from market_sim.model.interchange.caiso import CAISO_FIRM_IMPORT_TRANCHES

    firm = set(CAISO_FIRM_IMPORT_TRANCHES)
    static = IMPORT_TRANCHES["CAISO"]
    by_year = IMPORT_TRANCHES_BY_YEAR["CAISO"]

    caps = {name: {y: None for y in by_year} for name, _, _ in static}
    prices = {name: {y: None for y in by_year} for name, _, _ in static}
    for y, rungs in by_year.items():
        for name, mw, price in rungs:
            caps[name][y] = mw
            prices[name][y] = price

    limbs = {
        "firm_capacity": {
            "tranches": sorted(firm),
            "values_by_year": {n: caps[n] for n in sorted(firm)},
            "varies_by_year": True,
            "identification": "MEASURED",
            "source": (
                "DMM Annual Report system RA capacity 'Imports' row (2023 2,323 MW; 2024 3,371 MW; "
                "2025 carries 2024 — OPEN DATA GAP until the DMM 2025 annual report lands) x the "
                "published Maximum Import Capability per branch group (data/raw/capacity-"
                "deliverability/caiso/caiso.csv), north/south of Path 15."
            ),
            "verdict": "CLOSED — measured, per-year, cited to two published primary sources.",
        },
        "firm_price": {
            "tranches": sorted(firm),
            "values_by_year": {n: prices[n] for n in sorted(firm)},
            "varies_by_year": False,
            "identification": "RESIDUAL (static-fitted-pending-measured, audit C-6 / issue #1350)",
            "source": (
                "Tier-3 contract-cost proxies, identical in all three years, labelled "
                "STATIC-FITTED-PENDING-MEASURED in interchange spec.py itself."
            ),
            "verdict": (
                "LIVE ON THE BINDING PATH, and NOT for the reason the ledger gives. The per-hub "
                "injector's firm_base branch deliberately does NOT reprice these two. caiso-77's "
                "retirement argument was that caiso_firm_import_selfschedule sets pmin = pmax so "
                "'the tranche can never set the margin' and 'the two G-26 static-fitted-pending-"
                "measured firm prices stop influencing dispatch'. THAT ARGUMENT NO LONGER HOLDS "
                "IN FULL: caiso-151's caiso_firm_import_selfsched_clip — ARMED in this keeper — "
                "caps the FLOOR at CAISO's measured price-insensitive intertie ceiling, so above "
                "the ceiling the block is offered to the LP as ECONOMIC capability at exactly "
                "these static prices. FINDING-caiso150 §C/§F measures the un-floored volume at "
                "0.969 / 4.634 / 5.705 TWh in 23.9 / 47.2 / 48.9 % of hours (2023/24/25). "
                "The exposure GROWS with the DMM RA level. PRIOR ART: a measured Q-Q price "
                "derivation WAS attempted for this rung (derive_caiso_import_tranches.py, "
                "caiso-83) and FAILED its pre-registered LOYO honesty gate at 30.5 % against "
                "a 25 % bar (caiso-86b), so there is no currently-viable named replacement — "
                "which is precisely what rule 20 calls an open root-cause issue."
            ),
        },
        "spot_capacity": {
            "tranches": sorted(n for n, _, _ in static if n not in firm),
            "values_by_year": {n: caps[n] for n, _, _ in static if n not in firm},
            "varies_by_year": False,
            "identification": "RESIDUAL (static, no cited primary source)",
            "source": (
                "No primary source is cited for these four depths anywhere in the "
                "IMPORT_TRANCHES provenance block; the by-year comment states plainly that "
                "'only the two firm-block capacities vary by year. Spot tranches and all prices "
                "are identical to the static ladder.' FINDING-caiso82 §3 names these four MW "
                "VERBATIM as the registered G-26 / issue #1350 / audit C-6 gap "
                "('STATIC-FITTED-PENDING-MEASURED'); the measured south-corridor "
                "depth-in-surplus p95 4.7/5.4/5.5 GW banked there is SUPPORTING STABILITY "
                "evidence, not the derivation. No derive script has ever produced these "
                "numbers: derive_caiso_import_tranches.py re-derives PRICES ONLY, by its own "
                "docstring."
            ),
            "verdict": (
                "LIVE, FITTED, AND ON THE BINDING PATH — and this is the limb that matters most. "
                "The hub-price injector never touches a capacity. FINDING-caiso140 §C measures "
                "the Sep-Dec belly lambda as PINNED by a 2.7-3.0 GW economic-import plateau on "
                "which 51-61 % of defect hours never move; economic (non-firm) import in those "
                "hours is mean 2,705 MW / p50 3,038 MW. That plateau IS this depth ladder. "
                "A fitted scalar sitting exactly where the load-bearing criterion's residual is "
                "pinned is the single most consequential unclosed DOF CAISO carries."
            ),
        },
        "spot_price": {
            "tranches": sorted(n for n, _, _ in static if n not in firm),
            "values_by_year": {n: prices[n] for n, _, _ in static if n not in firm},
            "varies_by_year": False,
            "identification": "SUPERSEDED on the backcast binding path",
            "source": (
                "inject_caiso_per_hub_intertie_prices overwrites each spot leg's mc row with its "
                "OWN measured hub series (Malin / Palo Verde) + the OATT wheel + the CARB border "
                "adder, hour by hour."
            ),
            "verdict": (
                "CLOSED on the backcast binding path (this is the limb the ledger text describes) "
                "— with two disclosed conditions: the injector returns False and leaves the "
                "static placeholders in place when CAISO has NO measured hub series for the year "
                "(e.g. the 2023 OASIS gap), and the forecast path has no measured hub series at "
                "all, so the fitted prices are live there."
            ),
        },
    }
    return limbs


def main() -> None:
    rec = {
        "probe": "_caiso186os_dof_repair",
        "session": "caiso-186 owner sitting (dispatched label)",
        "lp_solved": False,
        "network": False,
        "r1_census": r1_census(),
        "r2_wiring": r2_wiring(),
        "r3_limb_split": r3_limb_split(),
    }

    print("=" * 92)
    print("R1  ISO-specific residual DOF census, recomputed at HEAD on today's six keepers")
    print("=" * 92)
    print(f"{'ISO':7}{'entries':>8}{'resid':>7}{'core':>6}{'ISO-SPEC':>9}  marker  entries")
    for iso, r in rec["r1_census"].items():
        mark = "yes" if r["holds_complete_marker"] else "NO "
        print(
            f"{iso:7}{r['n_entries']:>8}{r['n_residual_counted']:>7}{r['n_core_residual']:>6}"
            f"{r['n_iso_specific_residual']:>9}  {mark}     {', '.join(r['iso_specific']) or '-'}"
        )

    print()
    print("=" * 92)
    print("R2  keeper wiring for each surviving CAISO ISO-specific residual row")
    print("=" * 92)
    for k, v in rec["r2_wiring"]["keeper_flags"].items():
        print(f"  {k:38} = {v}")
    print()
    for name, v in rec["r2_wiring"]["rows"].items():
        print(f"* {name}\n    {v['verdict']}\n")

    print("=" * 92)
    print("R3  the import-ladder row, split into its four limbs")
    print("=" * 92)
    for limb, v in rec["r3_limb_split"].items():
        print(f"* {limb:15} [{v['identification']}]  tranches={v['tranches']}")
        print(f"    {v['verdict']}\n")

    OUT.write_text(json.dumps(rec, indent=1))
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
