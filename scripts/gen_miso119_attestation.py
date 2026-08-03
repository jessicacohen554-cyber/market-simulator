"""Write the calibration attestations for the miso-119 A/B arms.

Both arms are ``replay_keeper`` re-solves of the ``2026-08-03-miso-117b-ct-heat``
keeper's own ``meta.json`` at this session's HEAD, so the governance posture,
the standing measured-input ledger entries and the DOF ledger are the keeper's
— carried forward verbatim in *classification and reason*, with each arm's
**own** measured magnitudes substituted from its own scored verdict so no
number in an attestation describes a different run (the miso-116 §7 basis
discipline, applied at miso-117 and again here).

Arm B additionally carries the one new DOF entry,
``gas_offer_margin_anchor_by_zone (MISO)`` — the *already-registered*
``gas_offer_net_revenue_margin`` mechanism's identification point evaluated at
the grain its own definition requires. It adds **zero free parameters**: the
zone anchors are the same measurement as the ISO anchor, produced by the same
rule-23-frozen derive over the same 2023–2025 training window.

Arm B is **NOT promoted** — the pre-registration's own K3 liveness rule
adjudicates the mechanism ``I`` (inert) at MISO. The attestation is written
anyway because both arms are registered runs (rule 15) and C6 reads it.

Run AFTER both bundles are registered and their legitimacy diagnostics are
written, and BEFORE the final ``calibration_verdict.py --write-metrics`` pass,
since C6 reads the attestation and the ledger entries reclassify C3a/C3c.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/gen_miso119_attestation.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

KEEPER = REPO / "results/calibration/miso117_ctheatrate_B"
AB_JSON = REPO / "results/calibration/_miso119_zonal_anchor_ab.json"

ARMS = {
    "A": (
        REPO / "results/calibration/miso119_control_A",
        "2026-08-03-miso-119a-control",
    ),
    "B": (
        REPO / "results/calibration/miso119_zonalanchor_B",
        "2026-08-03-miso-119b-zonal-anchor",
    ),
}

YEARS = ("2023", "2024", "2025")

_SHARED_ATTEST = (
    "miso-119, 2026-08-03. Both arms are replay_keeper re-solves of the "
    "2026-08-03-miso-117b-ct-heat keeper's own meta.json at this session's "
    "HEAD, --year 2023 2024 2025 in ONE invocation each, years sequential "
    "inside the invocation (rules 12 / 16), chains run one at a time. The "
    "pre-registration results/calibration/PREREG-miso119-zonal-anchor-screen-"
    "2026-08-03.md was written, committed and PUSHED before either arm solved; "
    "its §5 fixed every construction gate (K1-K5), every kill (P1-P5) and the "
    "promotion/inertness rule in advance, and its §3 Phase-0 screen (no LP) "
    "returned LIVE on both pre-declared routes, which is what authorized these "
    "two solves at all. Rule 22 [R-HOLDOUT]: 2023-2025 only — MISO holds no "
    "calibration-complete marker, so no validation or locked-test year was "
    "solved, scored or read. "
)

ATTEST_BY = {
    "A": _SHARED_ATTEST
    + "THIS ARM IS THE ZERO-DELTA CONTROL: no --set, no override, no mechanism "
    "armed or disarmed. It exists so the treatment arm is measured against a "
    "same-HEAD twin rather than against the committed keeper, which would "
    "confound the flag with whatever drifted on main since that keeper solved "
    "(the neiso-69 drift-control precedent). It REPRODUCES the committed "
    "miso-117b keeper on the STRICT BYTE basis — max |delta MW| = 0.000000 on "
    "every class-hour in all three years — so the A/B is unconfounded and the "
    "miso-117 §6 drift disclosure does not recur here. It is NOT a candidate "
    "and must never be promoted.",
    "B": _SHARED_ATTEST
    + "THIS ARM IS THE TREATMENT: exactly ONE delta against the control, "
    "gas_offer_margin_zonal_anchor=true, applied through replay_keeper --set "
    "and recorded in run_config.json together with the fully resolved six-zone "
    "anchor map (rule 26 [R-REGISTRY]: run_config carries the values the solve "
    "used, never a lookup indirection). Nothing is stacked (rule 19 "
    "[R-ONE-MECH]): the zonal anchor RESOLVES the identification point of the "
    "gas_offer_net_revenue_margin mechanism the keeper already arms — that "
    "mechanism is armed and unchanged (anchor 3.0492) in BOTH arms. CHARTER: "
    "the mechanism's own identity — apply_gas_offer_margin adds markup_hr x "
    "(anchor - fuel) and states that at fuel == anchor the reformed offer "
    "reduces EXACTLY to the registered band multiplier — is a statement about "
    "a unit's OWN delivered fuel, but MISO's keeper also arms "
    "miso_zonal_gas_basis, so marked-up tranches priced their markup at an "
    "ISO-level fuel their zone never pays. Rule 25 [R-ISO-SCOPE]: MISO's own "
    "anchors from MISO's own basis data and MISO's own keeper fleet weights; "
    "the NYISO keeper verdict, the PJM inert verdict and the ERCOT keeper "
    "verdict on this mechanism transfer nothing, and no parameter is imported "
    "from any of them. THIS ARM IS NOT PROMOTED: the pre-registration's own K3 "
    "liveness rule adjudicates the mechanism INERT at MISO on the price grain "
    "the rubric scores, and the keeper is unchanged.",
}

DISCLOSURES = {
    "A": (
        "miso-119 arm A disclosures. (a) This bundle is a CONTROL and carries "
        "no finding of its own. (b) IT REPRODUCES THE COMMITTED KEEPER "
        "EXACTLY. On the strict-byte basis — class-hour for class-hour, all "
        "three years — this same-HEAD zero-delta replay differs from the "
        "committed 2026-08-03-miso-117b-ct-heat sidecars by 0.000000 MW. The "
        "prereg §5 K2 gate is the SCORECARD basis (same determination, same "
        "nine criterion statuses) and it also passes; the byte basis is "
        "reported because it is what surfaces drift, and here there is none. "
        "This is a stronger control than miso-117's own (which carried real "
        "3.7 GW drift) and it is what lets the miso-119 A/B be read as the "
        "flag alone."
    ),
    "B": (
        "miso-119 arm B disclosures, reported rather than patched. "
        "(a) THE MECHANISM IS DISPATCH-LIVE AND PRICE-INERT, AND THAT IS THE "
        "RESULT. K3's dispatch leg passes with room to spare (max class-hour "
        "delta 912.5 / 912.5 / 912.5 MW against a 50 MW bar) while its ZONAL "
        "PRICE leg fails in every year (max zonal |dLMP| 0.027 / 0.030 / 0.050 "
        "$/MWh against the 0.10 bar). Under the prereg's pre-committed rule "
        "that is `I`, registered, keeper unchanged — the same disposition PJM "
        "reached at pjm-144 under the same mean-zero applier convention. "
        "(b) THE PHASE-0 SCREEN'S OWN LIVENESS ARGUMENT IS THE THING THAT "
        "FAILED, and it failed in the direction that costs the session a "
        "solve, not one that flatters it. Route B reasoned that a max "
        "|delta offer| of 11.54 $/MWh could not be ruled out ex ante as "
        "unable to move a zonal annual mean by 0.10 $/MWh. The measured answer "
        "is that it moves it by 0.03-0.05 — the bound was correct and loose by "
        "two orders of magnitude, because the large per-tranche deltas sit on "
        "peaking tranches (markup_hr to 75.8) that are marginal in very few "
        "hours. The screen's arithmetic was sound; its implicit assumption "
        "that a large offer perturbation implies a comparable price "
        "perturbation was not, and no future screen in this row should treat "
        "max |delta offer| as a price-side lower bound. (c) THE FALSIFIED "
        "'COUPLED TOPOLOGY' PRIOR DID NOT RESCUE THE PRICE LEG, and the two "
        "facts are not in contradiction. MISO's keeper zones genuinely do "
        "decouple — cross-zone range > $1/MWh in 21.3 / 24.4 / 50.1 % of hours "
        "— so PJM's stated mechanism for inertness (price-coupled zones absorb "
        "the mean-zero redistribution) is NOT MISO's. MISO is inert for a "
        "different, measured reason: the mean-zero convention removes a "
        "capacity-weighted mean of exactly zero (verified to 4e-16 $/MMBtu at "
        "Phase 0), the surviving zone spread is small (max |anchor_z - ISO| = "
        "0.1799 $/MMBtu, against PJM's 1.483 raw window spread), and the "
        "tranches it repositions are not the ones setting zonal prices. Two "
        "ISOs, two conventions, two DIFFERENT routes to the same `I` — recorded "
        "so neither is quoted as evidence for the other (rule 25). (d) THE "
        "DIRECTION IS EXACTLY AS PRE-REGISTERED, which is reported and is NOT "
        "offered as a reason to promote. Prereg §6 declared a two-sided "
        "geometry: premium-basis zones under-marked today should rise, "
        "discount zones should fall. Sign agreement is 6/6 in all three years "
        "(premium-zone mean dLMP +0.0137 / +0.0051 / +0.0117, discount-zone "
        "mean -0.0275 / -0.0302 / -0.0504 $/MWh). A correct sign at an "
        "inert magnitude is a correct sign at an inert magnitude. (e) NO "
        "CRITERION MOVES AND NOTHING IS BANKED. Both arms score the identical "
        "nine criterion statuses and the identical NOT-YET determination; the "
        "system load-weighted lambda moves -0.016 / -0.021 / -0.035 $/MWh "
        "(about -0.06 %), which is not a C3a result and is not quoted as one. "
        "C7 COAL_PRB remains the sole FAIL in both arms, as pre-declared: this "
        "lever was never offered as a C7 instrument and did not become one. "
        "(f) P5 HOLDS: no parameter was moved to 'finish' this result. The "
        "zone anchor table is the derive script's own output, was never swept, "
        "and is NOT re-derived against this outcome (rule 23 "
        "[R-FROZEN-DERIVE]). The table stays registered in constants and the "
        "flag stays default-off — one CLI switch away should a zone-grain "
        "scored criterion, a zone-decoupling mechanism under its own charter, "
        "or an owner override of the K3 rule ever supply NEW evidence."
    ),
}


def _new_dof_entry(ab: dict | None) -> dict:
    """Arm B's single new DOF entry — zero free parameters added."""
    from market_sim.config.constants import (
        GAS_OFFER_MARGIN_ANCHOR_BY_ISO,
        GAS_OFFER_MARGIN_ANCHOR_BY_ZONE,
    )

    table = {
        z: round(float(a), 4)
        for z, a in GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["MISO"].items()
    }
    iso_anchor = GAS_OFFER_MARGIN_ANCHOR_BY_ISO["MISO"]
    measured = (
        f"Anchors span {min(table.values()):.4f} (Illinois/Indiana/East, the "
        f"Chicago-citygate zones) to {max(table.values()):.4f} (South) around "
        f"the unchanged ISO anchor {iso_anchor}; max |anchor_z - ISO| = "
        f"{max(abs(a - iso_anchor) for a in table.values()):.4f} $/MMBtu."
    )
    if ab is not None:
        k3 = ab["construction_gates"]["K3_liveness"]["by_year"]
        measured += (
            " Measured A/B effect: max class-hour dispatch delta "
            + " / ".join(f"{k3[y]['max_abs_class_hour_mw']:.0f}" for y in YEARS)
            + " MW, max zonal |dLMP| "
            + " / ".join(f"{k3[y]['max_abs_zone_price_delta']:.3f}" for y in YEARS)
            + " $/MWh (against the 0.10 K3 bar — FAILS, hence the `I` verdict), "
            "system load-weighted dLMP "
            + " / ".join(
                f"{k3[y]['delta_system_lw_price_REPORTED']:+.4f}" for y in YEARS
            )
            + " $/MWh (2023/24/25; committed results/calibration/"
            "_miso119_zonal_anchor_ab.json)."
        )
    return {
        "name": (
            "gas_offer_margin_anchor_by_zone (MISO) — the gas-offer "
            "net-revenue margin's identification anchor resolved PER ZONE, so "
            "the mechanism's own identity (at fuel == anchor the reformed "
            "offer reduces exactly to the registered band multiplier) holds in "
            "every zone rather than only at the ISO-series level, which "
            "carries the hub overlay but NOT the per-zone basis "
            "miso_zonal_gas_basis applies afterwards"
        ),
        "where": (
            "run_config.scenario_config.gas_offer_margin_zonal_anchor + "
            "gas_offer_margin_anchor_by_zone; "
            "constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE['MISO']"
        ),
        "identification": "measured/published",
        "lineage_solves": (
            "1 (miso-119 arm B, against a same-HEAD zero-delta control; "
            "adjudicated INERT — the arm is NOT a keeper)"
        ),
        "value": table,
        "free_parameters_added": 0,
        "source": (
            "scripts/data/derive_gas_offer_margin_anchor.py --iso MISO "
            "--by-zone --weights-bundle results/calibration/"
            "miso117_ctheatrate_B, which applies the RUNTIME zonal-basis "
            "transform (data.fuel.basis.meanzero, the capacity-weighted "
            "mean-zero core apply_miso_zonal_gas_basis delegates to) to the "
            "same delivered series the ISO anchor is measured on, weighted by "
            "the KEEPER'S OWN per-year per-zone gas capacity from "
            "scripts.lib.bundle_fleet.reconstruct_bundle_fleet (no LP). "
            f"{measured} The Phase-0 construction record — S1 keeper-config "
            "fidelity, S2 ISO-anchor invariance (3.0492 unmoved by the "
            "registry extension), S3 the mean-zero invariant closing to "
            "4.4e-16 $/MMBtu, S4 the marked-up-tranche census (558/564/562 "
            "tranches, ~21.7 GW, 0 band-scoped anchors), S5 the zone-coupling "
            "census and S6 hub-table coverage — is committed in "
            "results/calibration/PROBE-miso119-zonal-anchor-screen-"
            "2026-08-03.txt."
        ),
        "why_zero": (
            "Not a new constant, not a new mechanism and not a re-tune: it is "
            "the already-registered identification point evaluated at the "
            "grain the mechanism's own definition requires. The zone anchors "
            "are the SAME measurement as the ISO anchor, by the SAME derive, "
            "over the SAME 2023-2025 training window; nothing is chosen, "
            "nothing is swept, n_residual is unchanged. Rule 23 "
            "[R-FROZEN-DERIVE]: re-derived only on a source-data change, never "
            "because a residual moved — and expressly NOT re-derived against "
            "this arm's inert outcome. Rule 19 [R-ONE-MECH]: a band-scoped "
            "rebasis anchor (offer_margin_anchor on the tranche) keeps "
            "precedence, so the two identification channels never stack; the "
            "MISO census finds 0 band-scoped tranches, so the question is "
            "moot here. Rule 25 [R-ISO-SCOPE]: the registry carries a MISO "
            "table derived from MISO data only."
        ),
    }


def _verdict(run_id: str) -> dict:
    """Score a registered run and return its JSON verdict."""
    out = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/calibration_verdict.py"),
            "--run-id",
            run_id,
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    if out.returncode not in (0, 1) or not out.stdout.strip():
        raise SystemExit(
            f"calibration_verdict failed for {run_id}: {out.stderr[-800:]}"
        )
    return json.loads(out.stdout)


def _magnitudes(verdict: dict) -> dict[tuple[str, int], str]:
    """(criterion, year) -> this run's OWN measured magnitude string."""
    out: dict[tuple[str, int], str] = {}
    for name, crit in verdict["criteria"].items():
        for rec in crit.get("records", []):
            year = rec.get("year")
            if year is None or rec.get("key") == "da_diagnostic":
                continue
            mag = rec.get("magnitude") or rec.get("detail")
            if mag:
                out[(name, int(year))] = str(mag)
    return out


def build(arm: str, ab: dict | None) -> Path:
    """Write one arm's attestation; return its path."""
    bundle, run_id = ARMS[arm]
    base = json.loads((KEEPER / "calibration_attestation.json").read_text())
    mags = _magnitudes(_verdict(run_id))

    att = {
        "schema": base["schema"],
        # free_parameters is re-seeded from THIS bundle's run_config by
        # scripts/build_dof_ledger.py immediately after this write; the
        # keeper's section is carried only as the starting shape.
        "free_parameters": base["free_parameters"],
        "governance": {
            **{
                k: base["governance"][k]
                for k in (
                    "levers_trace_to_measured_input",
                    "no_fit_to_price_residuals",
                    "no_pinning_to_actuals",
                    "outage_filter_exogenous_net_load",
                )
            },
            "attested_by": ATTEST_BY[arm],
        },
        "disclosures": {"note": DISCLOSURES[arm]},
        "exceptions": [],
    }
    for exc in base["exceptions"]:
        new = dict(exc)
        key = (str(exc.get("criterion")), int(exc.get("year")))
        if key in mags:
            new["magnitude"] = mags[key]
            new["magnitude_basis"] = (
                "this run's own scored value (miso-119); the classification "
                "and reason are the standing MISO adjudication carried forward"
            )
        att["exceptions"].append(new)

    if arm == "B":
        entry = _new_dof_entry(ab)
        entries = [
            e
            for e in att["free_parameters"].get("entries", [])
            if e.get("name") != entry["name"]
        ]
        entries.append(entry)
        att["free_parameters"]["entries"] = entries

    path = bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1) + "\n")
    return path


def main() -> int:
    """Write both arms' attestations and re-seed each DOF ledger."""
    ab = json.loads(AB_JSON.read_text()) if AB_JSON.exists() else None
    if ab is None:
        print(
            "NOTE: A/B JSON absent — the DOF entry's measured-effect prose "
            "is omitted; re-run this script after the scorer to enrich it."
        )
    for arm in ("A", "B"):
        path = build(arm, ab)
        print(f"wrote {path.relative_to(REPO)}")
        out = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts/build_dof_ledger.py"),
                str(ARMS[arm][0]),
                "--iso",
                "MISO",
            ],
            capture_output=True,
            text=True,
            cwd=REPO,
        )
        print(
            f"  build_dof_ledger[{arm}] rc={out.returncode} {out.stdout.strip()[-300:]}"
        )
        if out.returncode != 0:
            print(f"  stderr: {out.stderr[-500:]}")
        if arm == "B":
            # build_dof_ledger replaces the whole section, so re-attach the
            # new entry after it runs (it only knows the curated per-ISO
            # table).
            att_path = ARMS[arm][0] / "calibration_attestation.json"
            att = json.loads(att_path.read_text())
            entry = _new_dof_entry(ab)
            entries = [
                e
                for e in att["free_parameters"].get("entries", [])
                if e.get("name") != entry["name"]
            ]
            entries.append(entry)
            att["free_parameters"]["entries"] = entries
            att["free_parameters"]["n_entries"] = len(entries)
            att["free_parameters"]["n_residual"] = sum(
                1 for e in entries if e.get("identification") == "residual"
            )
            att_path.write_text(json.dumps(att, indent=1) + "\n")
            print(f"  re-attached the zonal-anchor DOF entry ({len(entries)} total)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
