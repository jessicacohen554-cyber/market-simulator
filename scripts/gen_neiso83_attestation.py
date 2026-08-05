"""Write the calibration attestations for the neiso-83 ``cc_steam_part_reclass`` arms.

Both arms are ``replay_keeper`` re-solves of the
``2026-08-04-neiso81-chpheatrate`` keeper's own ``meta.json`` at this session's
HEAD. Arm **A** is a ZERO-DELTA control; arm **B** carries exactly one delta,
``cc_steam_part_reclass=true``. The governance posture, the standing
measured-input ledger entries (NEISO's single ledgered C3c caveat) and the DOF
ledger are therefore the keeper's — carried forward verbatim in *classification
and reason*, with each run's **own** measured magnitudes substituted from its own
scored verdict, so no number in an attestation describes a different run (the
miso-116 §7 basis discipline).

**BOTH arms need an attestation, and that is not cosmetic.** neiso-70 §4 measured
it: without one, a probe bundle reads ``NOT-YET / governance UNATTESTED`` and C3c
degrades from a ledgered CAVEAT to a raw FAIL, because a caveat can only be
*ledgered* by an attestation. That is a scoring artifact of probe bundles and it
must apply identically to control and arm, or the A/B is not like-for-like.

Arm B carries one new DOF entry, ``cc_steam_part_reclass``, adding **zero free
parameters**: the capacity is EIA-860's published net-summer figure and the heat
rate is the incumbent eGRID plant rate. No coefficient is chosen, fitted or
swept, and no residual is consulted in either direction.

Run AFTER each bundle is registered and its legitimacy diagnostics are written,
and BEFORE the final ``calibration_verdict.py --write-metrics`` pass, since C6
reads the attestation and the ledger entries reclassify C3c.

Usage::

    uv run python scripts/gen_neiso83_attestation.py --arm A
    uv run python scripts/gen_neiso83_attestation.py --arm B
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

ISO = "NEISO"
KEEPER = REPO / "results/calibration/neiso81_chpheatrate_B"
PHASE0_JSON = REPO / "results/calibration/_neiso83_stonybrook_ca1_phase0.json"
AB_JSON = REPO / "results/calibration/_neiso83_ca1reclass_ab.json"

ARMS = {
    "A": {
        "bundle": REPO / "results/calibration/neiso83_control_A",
        "run_id": "2026-08-05-neiso-83-control-zerodelta",
        "armed": False,
    },
    "B": {
        "bundle": REPO / "results/calibration/neiso83_ca1reclass_B",
        "run_id": "2026-08-05-neiso-83-ca1-reclass",
        "armed": True,
    },
}

_COMMON = (
    "neiso-83, 2026-08-05. A replay_keeper re-solve of the "
    "2026-08-04-neiso81-chpheatrate keeper's own meta.json at this session's "
    "HEAD, --years 2023 2024 2025 in ONE invocation (rules 12 / 16 "
    "[R-ALLYEARS]), years sequential inside the invocation. "
    "PRE-REGISTRATION: results/calibration/"
    "PREREG-neiso83-stonybrook-ca1-2026-08-05.md, pushed BEFORE either arm "
    "solved — every construction property, threshold, falsifier, stop trigger "
    "and verdict branch was fixed in advance, including the disclosure that the "
    "charter's own '< 0.15 % of CC_REGULAR' magnitude expectation was measured "
    "wrong before the solve rather than after it. "
)

_ATTEST_A = _COMMON + (
    "THIS IS THE ZERO-DELTA CONTROL (arm A). No --set; a programmatic diff of "
    "its scenario block against arm B's returns exactly one differing key. It "
    "exists because miso-124's DO-NOT-MISREAD is that price response is NOT "
    "stable across keepers, so every arm-B delta is quoted against THIS bundle "
    "and never against the committed keeper. It arms NOTHING and claims "
    "NOTHING: it is scored, registered (rule 15 [R-DASHBOARD]) and attested "
    "only so the comparison is like-for-like."
)

_ATTEST_B = _COMMON + (
    "EXACTLY ONE DELTA against that keeper, cc_steam_part_reclass=true, applied "
    "through replay_keeper --set and recorded in run_config.json (rule 24 "
    "[R-REGISTRY]); it is scored against a SAME-HEAD ZERO-DELTA CONTROL "
    "(neiso83_control_A), never against the committed keeper. "
    "WHAT THE MECHANISM IS. NEISO 6081 Stony Brook CA1 is the STEAM half of a "
    "3x1 combined-cycle block. The LP carried it as a 96.0 MW standalone `oil` "
    "generator — VOM $4.50, 1.0 t-CO2/MWh, EFORd 0.10 — while its three "
    "combustion-turbine siblings sat in CC_REGULAR/gas_cc at VOM $2.00, 0.43 "
    "and 0.05, sharing its heat rate exactly. A combined-cycle steam turbine has "
    "no combustion path: it runs on HRSG exhaust, reports no CEMS stack, and "
    "every MMBtu the block burns is already metered at those siblings. So the "
    "model was burning distillate in a machine that has no fuel of its own. "
    "The re-class moves the row onto the block it is half of. Capacity is "
    "UNCHANGED (24,209.58 MW both arms); class, fuel, VOM, CO2 rate and EFORd "
    "move. "
    "WHY IT IS NOT DOUBLE-COUNTING THE BLOCK'S FUEL. The incumbent heat rate is "
    "the eGRID PLANT-AVERAGE, whose PLNGENAN denominator already counts the "
    "steam part's own generation — it is a BLOCK rate. Applying it uniformly to "
    "every block MW reproduces the block's total fuel burn by construction. "
    "The UNARMED state is the inconsistent one: it charges a block-denominated "
    "rate to 209.1 MW of a 305.1 MW block and prices the missing 96 MW off the "
    "distillate curve. "
    "WHY IT IS A NEW FLAG AND NOT cc_steam_part_capacity. That mechanism only "
    "RESTORES rows the fuel map DROPS (BFG/OG -> None); a CARRIED row is outside "
    "its population entirely, which is why neiso-80 measured a byte-identical "
    "armed fleet and stamped it `I`. Its `fuel_type is None` gate is "
    "load-bearing (miso-125 s6: it is what keeps MISO 1004 Edwardsport's real "
    "555 MW IGCC machine in COAL), so re-classing gets its own flag and its own "
    "ISO registry rather than widening the repair's. cc_steam_part_capacity is "
    "NOT re-armed and its `I` is NOT re-stamped (rule 28a). "
    "THE OUTAGE-DENOMINATOR LEG IS PART OF THIS MECHANISM, NOT A SECOND ONE, "
    "AND WAS DISCLOSED BEFORE THE SOLVE. The CAMPD unit-outage overlay derates "
    "(plant_code, plant_group) by removed_mw / plant_capacity_mw, and that "
    "denominator is read off the same fleet, so it moves with the flag "
    "(209.1 -> 305.1 MW at 6081). Left un-forwarded it would remove the wrong "
    "ABSOLUTE MW — a 152 MW 2024 outage against the un-armed denominator "
    "removes 72.7 % of an armed 305.1 MW bin = 221.8 MW, 46 % more than went "
    "out. Rule 23 [R-FROZEN-DERIVE] is NOT engaged: the deriver's own inputs at "
    "6081 are identical under both arms, so the committed extract would "
    "re-derive byte-for-byte, and nothing was regenerated."
)


def _verdict(run_id: str) -> dict:
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
        for rec in crit.get("rows", []) + crit.get("records", []):
            year = rec.get("year")
            if year is None or rec.get("key") == "da_diagnostic":
                continue
            mag = rec.get("magnitude") or rec.get("detail")
            if mag:
                out[(name, int(year))] = str(mag)
    return out


def _json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def _dof_entry() -> dict:
    """The ``cc_steam_part_reclass`` DOF entry — zero free parameters."""
    p0 = _json(PHASE0_JSON)
    cap = p0.get("q1_capacity_basis", {})
    direct = p0.get("q3_direct", {})
    ab = _json(AB_JSON)
    live = ""
    p4 = ((ab.get("construction_properties") or {}).get("p4") or {}).get("per_year", {})
    if p4:
        live = (
            "Measured effect on THIS keeper, against a same-HEAD zero-delta "
            "control: oil energy delta "
            + " / ".join(f"{p4[y]['oil_energy_delta_twh']:+.5f}" for y in sorted(p4))
            + " TWh and CC_REGULAR "
            + " / ".join(
                f"{p4[y]['cc_regular_energy_delta_twh']:+.5f}" for y in sorted(p4)
            )
            + " TWh (2023/2024/2025). "
        )
    return {
        "name": "cc_steam_part_reclass",
        "identification": "measured",
        "classification": (
            "EIA-860 published generator attributes, zero free parameters "
            "(rule 14 [R-ACCURATE] classification-correctness fix)"
        ),
        "value": True,
        "free_parameters_added": 0,
        "source": (
            "EIA-860 operable generator sheet. The predicate "
            "(fleet.eia860.cc_steam_part_generators, miso-125 R4 verbatim): "
            "prime mover CA, own Energy Source 1 != NG, non-empty Unit Code, at "
            "least one sibling at the same plant sharing that Unit Code with "
            "prime mover CT and Energy Source 1 NG, and the steam part not older "
            "than the oldest such sibling. NEISO's ENTIRE population is one row: "
            f"6081 Stony Brook CA1, pmax "
            f"{cap.get('fleet_pmax_mw')} MW = EIA-860 net summer "
            f"{cap.get('eia860_summer_mw')} (nameplate "
            f"{cap.get('eia860_nameplate_mw')}; the fleet pmax rule is "
            "net-summer-else-nameplate, so the 96-vs-105 'mismatch' is a basis "
            "difference, not a discrepancy). The heat rate is UNCHANGED at the "
            "incumbent eGRID plant rate 10.60617891, which its three CT siblings "
            f"already carry exactly. {live}"
            "Phase-0 identification record: "
            "results/calibration/_neiso83_stonybrook_ca1_phase0.json + "
            "scripts/probes/_neiso83_stonybrook_ca1_phase0.py."
        ),
        "why_zero": (
            "Nothing is chosen, tuned or swept. The capacity is EIA-860's "
            "published net-summer figure and the heat rate is the incumbent one; "
            "the flag selects a CLASS, and every downstream attribute (VOM, CO2 "
            "rate, NOx rate, EFORd, efficiency bin) follows from the existing "
            "per-fuel constants with no new value introduced. "
            "THE STEAM SHARE IS EVIDENCE, NOT A PARAMETER: EIA-923 Page 1 "
            "reports the CA row's own net generation at "
            + " / ".join(
                f"{(direct.get('years') or {})[y]['steam_share_of_block']:.4f}"
                for y in sorted(direct.get("years") or {})
            )
            + f" of block output (mean {direct.get('mean_steam_share')}, sd "
            f"{direct.get('sd')}), and the CA row's own FUEL split tracks its CT "
            "siblings' fuel split year by year across a 0.004 -> 0.468 swing in "
            "the block's oil share — proof the steam part has no fuel of its own "
            "and that EIA-860's DFO label is a duct / legacy code. Corroborated "
            "independently for 2024-2025, where EIA-923's CT NET generation "
            "EXCEEDS the CAMPD CT GROSS (ratios 1.343 / 1.338), which is "
            "impossible for a CT-only row and therefore proves a reporting-"
            "convention change rather than a retired steam turbine; the two "
            "routes reconcile at a 0.96 auxiliary-load ratio. NONE of these "
            "numbers enters the LP. "
            "Rule 13 [R-MEASURED]: a generator's prime mover, unit code, vintage "
            "and net-summer capacity are published INPUTS that regenerate for "
            "any forward year and respond to changed conditions (a retirement or "
            "re-rate moves them) — not a measured outcome fed back to close a "
            "residual. No residual was consulted, in either direction. "
            "Rule 25 [R-ISO-SCOPE]: ISO-gated on "
            "plant_taxonomy.CC_STEAM_PART_RECLASS_ISOS = {NEISO}, proven by "
            "RUNNING the armed loader per ISO — ERCOT, CAISO, PJM, MISO and "
            "NYISO fleets are byte-identical, and MISO 1004 Edwardsport (the one "
            "other member of the national re-class population, and a real 555 MW "
            "IGCC machine) stays COAL. n_residual is unchanged."
        ),
    }


def _disclosures(arm: str) -> str:
    """Disclosures, with THIS run's own measured magnitudes substituted in."""
    p0 = _json(PHASE0_JSON)
    ab = _json(AB_JSON)
    avail = (p0.get("arm_outage_availability") or {}).get("by_year", {})
    p4 = ((ab.get("construction_properties") or {}).get("p4") or {}).get("per_year", {})
    parts = [
        f"neiso-83 arm {arm} disclosures, reported rather than patched. ",
        "(a) THE CHARTER'S MAGNITUDE EXPECTATION WAS CORRECTED BEFORE THE SOLVE, "
        "NOT AFTER. The lane was chartered expecting '< 0.15 % of CC_REGULAR'. "
        "Phase 0 measured the block's effective available capacity moving "
        + " / ".join(
            f"{avail[y]['effective_avail_mw_off']:.1f} -> "
            f"{avail[y]['effective_avail_mw_armed']:.1f} MW"
            for y in sorted(avail)
        )
        + " (2023/2024/2025), materially more headroom than that expectation "
        "implies, and the prereg said so in advance so the finding could not be "
        "read as retrofitting the expectation. ",
        "(b) THE DENOMINATOR LEG DOMINATES THE HEADROOM, AND IT IS DISCLOSED AS "
        "SUCH. Decomposed at Phase 0: capacity leg "
        + " / ".join(f"{avail[y]['capacity_leg_mw']:+.1f}" for y in sorted(avail))
        + " MW against denominator leg "
        + " / ".join(f"{avail[y]['denominator_leg_mw']:+.1f}" for y in sorted(avail))
        + " MW. The arm is NOT simply '+96 MW of CC'. ",
        "(c) 2023 CANNOT MOVE THROUGH THIS PLANT AT ALL. The block is derated to "
        "zero in all 8,760 hours in BOTH arms, so any 2023 CC_REGULAR change is "
        "system re-dispatch displacing the 96 MW that left `oil`, never 6081 "
        "output — pre-registered, and the measured 2023 deltas are consistent "
        "with it. ",
        "(d) THE ROOT CAUSE THE DENOMINATOR LEG EXPOSES IS NAMED AND NOT FIXED "
        "(rules 19 / 21 / 25). campd-unit-outages-NEISO.csv carries plant 6081's "
        "DIESEL peakers (CAMPD units 004/005 = EIA-860 generators 1 and 2) with "
        "plant_group=CC_REGULAR, because `oil` carries no plant_group at all and "
        "the overlay cannot represent an oil unit's outage. In 2024 and 2025 "
        "those two units are the ONLY source of 6081 outage rows while the CC "
        "block's own units 001/002/003 have none — so the model derates a "
        "fully-available CC block to 29.5 % / 19.4 %. That is a pre-existing, "
        "ISO-agnostic defect in a DIFFERENT mechanism, needing a fleet-taxonomy "
        "change with six-ISO blast radius. The armed denominator moves the block "
        "TOWARD physical truth rather than away from it, which is why rule 14 "
        "[R-ACCURATE] says take the consistent basis and open the root cause "
        "rather than bury it in an inconsistent one. Filed as an open "
        "root-cause issue for a successor lane. ",
        "(e) THE BENCHMARK SIDE IS NOT SYMMETRICALLY CORRECTED, AND THE GAP IS "
        "MEASURED, NOT ASSUMED. The EIA-923 benchmark buckets Page-1 rows "
        "through the same classify_plant registry but at NATIONAL scope with no "
        "ISO gate, so re-classing there would reach MISO's Edwardsport (rule "
        "25). The un-corrected residue is the 6081 CA/DFO row: 2,165 MWh in 2023 "
        "and ZERO in 2024 and 2025 — 0.0022 TWh against a +/-1.955 TWh C1 band, "
        "0.11 % of it. Disclosed rather than fixed; cc_steam_part_capacity's own "
        "MISO keeper does not touch the benchmark side either. ",
    ]
    if p4:
        parts.append(
            "(f) FIRING WAS PROVEN AT THE ENERGY GRAIN, NOT THE LOADER GRAIN "
            "(the miso-126 wiring gap). Per-class energy delta against the "
            "control: oil "
            + " / ".join(f"{p4[y]['oil_energy_delta_twh']:+.5f}" for y in sorted(p4))
            + " TWh, CC_REGULAR "
            + " / ".join(
                f"{p4[y]['cc_regular_energy_delta_twh']:+.5f}" for y in sorted(p4)
            )
            + " TWh. A loader-level check alone would NOT have been accepted as "
            "proof, and a byte-identical arm would have scored INVALID rather "
            "than inert. "
        )
    if arm == "A":
        parts.append(
            "(g) THIS BUNDLE ARMS NOTHING. It is the zero-delta control and "
            "makes no claim of its own; it exists so arm B's deltas are "
            "attributable to the mechanism rather than to code or environment "
            "drift, and it is attested only so both arms score on the same basis "
            "(neiso-70 §4: an unattested probe bundle reads NOT-YET / governance "
            "UNATTESTED and its C3c degrades from a ledgered CAVEAT to a raw "
            "FAIL)."
        )
    return "".join(parts)


def build(arm: str) -> Path:
    """Write the arm's attestation; return its path."""
    spec = ARMS[arm]
    bundle: Path = spec["bundle"]
    base = json.loads((KEEPER / "calibration_attestation.json").read_text())
    mags = _magnitudes(_verdict(spec["run_id"]))

    att = {
        "schema": base["schema"],
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
            "attested_by": _ATTEST_A if arm == "A" else _ATTEST_B,
        },
        "disclosures": {"note": _disclosures(arm)},
        "exceptions": [],
    }
    for exc in base["exceptions"]:
        new = dict(exc)
        year = exc.get("year")
        key = (str(exc.get("criterion")), int(year)) if year is not None else None
        if key is not None and key in mags:
            new["magnitude"] = mags[key]
            new["magnitude_basis"] = (
                f"this run's own scored value (neiso-83 arm {arm}); the "
                "classification and reason are the standing NEISO adjudication "
                "carried forward"
            )
        att["exceptions"].append(new)

    path = bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1) + "\n")
    return path


def main() -> int:
    """Write one arm's attestation and rebuild + top up its DOF ledger."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=sorted(ARMS), required=True)
    args = ap.parse_args()
    arm = args.arm
    spec = ARMS[arm]
    bundle: Path = spec["bundle"]

    path = build(arm)
    print(f"wrote {path.relative_to(REPO)}")

    out = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/build_dof_ledger.py"),
            str(bundle),
            "--iso",
            ISO,
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    print(f"  build_dof_ledger rc={out.returncode} {out.stdout.strip()[-300:]}")
    if out.returncode != 0:
        print(f"  stderr: {out.stderr[-500:]}")

    # build_dof_ledger replaces the whole section and regenerates only the
    # entries it can derive from run_config.json. The keeper carries more that
    # earlier promoting sessions hand-attached; BOTH arms must carry them or the
    # ledger would silently shrink and read as though this session retired
    # parameters it never touched. The armed arm adds its own entry on top.
    att = json.loads(path.read_text())
    derived = att["free_parameters"].get("entries", [])
    derived_names = {e.get("name") for e in derived}
    carried = [
        e
        for e in json.loads((KEEPER / "calibration_attestation.json").read_text())[
            "free_parameters"
        ].get("entries", [])
        if e.get("name") not in derived_names
    ]
    entries = list(derived) + carried
    added = 0
    if spec["armed"]:
        new = _dof_entry()
        entries = [e for e in entries if e.get("name") != new["name"]]
        entries.append(new)
        added = 1
    att["free_parameters"]["entries"] = entries
    att["free_parameters"]["n_entries"] = len(entries)
    att["free_parameters"]["n_residual"] = sum(
        1 for e in entries if e.get("identification") == "residual"
    )
    path.write_text(json.dumps(att, indent=1) + "\n")
    print(
        f"  re-attached {len(carried)} carried + {added} new DOF entry "
        f"({len(entries)} total, n_residual "
        f"{att['free_parameters']['n_residual']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
