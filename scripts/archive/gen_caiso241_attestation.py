"""Write a caiso-241 bundle's attestation (both the A0 control and the B1 arm).

Two bundles are produced this session and BOTH need a C6 attestation — an
unattested C6 makes C3c FAIL instead of reclassifying to a ledgered CAVEAT, and
the whole point of the control is that its scorecard be comparable to the arm's
(``PRECOMMIT-caiso241-ADDENDUM2-owner-ruling-2026-09-03.md`` §B4: every gate is
evaluated on B1 minus A0, so a difference introduced by an un-attested control
would be a measurement artifact).

The ``gen_caisoNNN`` series pattern is unchanged (E10: an attestation is
generated AT the promotion, every premise computed, never typed): the caiso-240
keeper's committed attestation is carried, ``attested_by`` is re-stamped with
the narrative for THIS bundle, and the ``price_tail`` (C3c) exception magnitudes
are RE-MEASURED on this bundle's own committed sidecars. ``free_parameters`` is
not edited here — ``scripts/build_dof_ledger.py`` rebuilds it afterwards.

Usage::

    PYTHONPATH=.:src python scripts/gen_caiso241_attestation.py \
        --bundle results/calibration/caiso241_b1_ctpeaker_committed \
        --arm b1 --still-failing 2023 2024
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

YEARS = (2023, 2024, 2025)
#: Actual RT hours > $200/MWh (C3c basis; caiso-204 finding §C / keeper ledger).
ACTUAL_TAIL = {2023: 47, 2024: 35, 2025: 8}
KEEPER = REPO / "results/calibration/caiso240_b1_stgas_peak_measured"

_SHARED = (
    "caiso-241 session (2026-09-03): the RULE 14 [R-ACCURATE] / RULE 19 "
    "[R-ONE-MECH] / RULE 21 [R-DOF] / RULE 25 [R-ISO-SCOPE] grounding of "
    "CAISO's CT_PEAKER `committed` band on its OWN measured physical "
    "counterpart, and the ADMISSIBILITY RULING that authorised it. THE "
    "OBJECT (FINDING-caiso240-gas-vs-eia930-2026-09-03.md §3-§4): the model "
    "dispatches CAISO peakers at 2.5 / 0.8 / 0.4 % capacity factor against a "
    "measured 7.4 / 7.5 / 4.1 % — a 66 / 89 / 90 % under-run worth "
    "-2.71 / -3.84 / -2.11 TWh, uniform across every zone and month, "
    "worsening, on IDENTICAL nameplate, and passed by C1 only because the "
    "class fits inside the widened +/-8 TWh and +/-3.0 pp bands. THE RULING "
    "(PRECOMMIT-caiso241-ct-peaker-committed-2026-09-03.md §1, pushed to "
    "origin BEFORE any fleet was rebuilt): grounding the band on the "
    "measured PHYSICAL basis is OUTSIDE the caiso-238 F4 / Lever-A refusal, "
    "on five limbs, three of them new and any one sufficient. (1) The "
    "refusal is ROUTE-scoped and caiso-238 §3 said so in the assessment that "
    "issued the F4: it covers the measured BID multiplier (CT bucket 1.166, "
    "STILL UNARMED), while the physical min-load burn is the instrument "
    "Lever A itself used; and 1.350 > 1.166 > 0.991, so the repair's "
    "DIRECTION is invariant to which measurement route one accepts. (2) "
    "Lever A's own stated ground — 'any avoided-startup credit belongs in an "
    "explicit UC layer, not the P1 offer' — refuses 1.35 SYMMETRICALLY, "
    "since _CAISO_OFFER_CURVE itself calls it a 'start-cost hurdle'; reading "
    "the refusal to protect it would preserve an unidentified commitment "
    "adder BECAUSE it is unidentified. (3) RULE 19 DOUBLE-COUNT: the "
    "_committed tranche is the ONLY tranche carrying the bin's start cost "
    "(bins_to_fleet's docstring) and P1 already amortizes it "
    "(BIN_STARTUP_COST_PER_MW['CT_PEAKER'] = $20/MW, NREL/SR-5500-55433, "
    "divided by the P0 run length, with no CT exemption in "
    "compute_monthly_markup and tranche_startup_amortization OFF on this "
    "keeper, so the markup lands on the very band at issue). (4) RULE 25: "
    "committed = 1.35 appears in the CAISO, NYISO and NEISO CT_PEAKER "
    "curves, each comment citing the others ('NYISO-grounded' / "
    "'NYISO/CAISO-grounded') and NONE citing a measurement, while those "
    "ISOs' own CAMPD samples read 0.843 (n=70) / 0.985 (n=18) / 0.991 "
    "(n=75). (5) The merit order is INVERTED — the keeper reads committed "
    "1.350 > peak 1.166 = econ_high 1.166 > econ_low 1.145, i.e. the "
    "min-load block is the class's MOST EXPENSIVE MW — and applying the "
    "refusal to ONE band of four is what inverted it, when caiso-231's "
    "measured static surface re-grounded econ/peak while withholding "
    "committed. THE REPAIR: committed := phys_committed, the value the "
    "band's own dict already carries (avg_committed_p50, "
    "data/raw/reference/caiso_campd_marginal_hr_summary.csv, n = 75, IQR "
    "[0.969, 1.085]) — no new literal, no registry value to pick, ZERO free "
    "parameters. MEASURED PRE-SOLVE, zero LP (_caiso241_gstruct_presolve.json): "
    "exactly 44 rows move in every year, all CAISO CT_PEAKER _committed, at "
    "the exact ratio 0.991/1.350 = 0.734074074074, with offer_markup_hr "
    "driven to exactly 0.0 and ZERO rows moving in any other band, group or "
    "ISO (829.8 MW = 11.0 % of the class). THE DECOMPOSITION IS THE RULE-19 "
    "ARGUMENT: under gas_offer_net_revenue_margin the reformed cost is "
    "phys*base_hr*fuel + (mult-phys)*base_hr*anchor, so grounding leaves the "
    "fuel-scaled physical cost UNTOUCHED and removes ONLY the fuel-invariant "
    "margin — measured capacity-weighted at -18.6197 $/MWh, IDENTICAL TO "
    "FOUR DECIMALS in all three years across gas at 2.54 / 2.19 / 3.52 "
    "$/MMBtu. CORROBORATION FOUND AFTER THE PRECOMMIT PUSH AND LABELLED AS "
    "SUCH: MISO has ALREADY made this repair (CT_PEAKER committed 1.025 = "
    "its own phys_committed 1.025) and _MISO_OFFER_CURVE states limb 3 "
    "verbatim, citing FERC Order 825 / ELMP — so the repair is "
    "precedent-following, not novel in kind; five of six ISOs price the CT "
    "min-load band above their own measured basis, and under rule 25 the "
    "other four are asks for their own lanes with no value transferred. "
    "DIRECTION DISCLOSED BEFORE ANY SOLVE AND NEVER ARGUED FROM (rule 1 "
    "[R-STRUCT]): the direction is FAVOURABLE to the sole failing gate, "
    "which is the session's hazard, not its case — and the pre-solve "
    "two-sided crossing envelope §H' settles that it can never be a C3a "
    "lever, with a price ceiling of 0.880 / 0.380 / 0.198 $/MWh against a "
    "required 0.00 / -0.848 / -1.893 and a VOLUME ceiling of "
    "0.432 / 0.247 / 0.120 TWh against a CT_PEAKER miss of "
    "2.71 / 3.84 / 2.11 TWh, i.e. at most 16 / 6 / 6 % of the gap, so the "
    "caiso-240 CT_PEAKER object SURVIVES this repair. The caiso-230 §H form "
    "is deliberately NOT used as the bound: caiso-240 falsified its "
    "description as a strict upper bound, and this arm sits in the regime "
    "where it under-predicts. HOLDOUT: CAISO holds no `complete` and no "
    "`final` marker, the spend freeze is ACTIVE, and every read and both "
    "solves stayed inside 2023-2025."
)

_A0 = (
    "THIS BUNDLE IS THE A0 CONTROL and is NEVER a promotion candidate: the "
    "caiso-240 keeper recipe replayed at HEAD with NO flag delta. It exists "
    "because the owner AMENDED the caiso-231 'no control arms' directive on "
    "2026-09-03 (PRECOMMIT-caiso241-ADDENDUM2 §B2) for an arm measured LIVE "
    "IN EVERY SOLVED YEAR — this one — for which neither the run_config "
    "field-diff form of G-CTRL nor caiso-240's dispatch-identity form can "
    "bind. G-CTRL form 3 is therefore a HEAD-DRIFT check scored on this "
    "bundle, and every other gate is evaluated on B1 minus A0 rather than "
    "B1 minus the committed keeper. " + _SHARED
)

_B1 = "THIS BUNDLE IS THE B1 ARM (single flag delta). " + _SHARED

_ATTEST = {"a0": _A0, "b1": _B1}


def _tail_counts(bundle: Path) -> dict[int, int]:
    """Model hours > $200 per year on the scorer's max-zonal basis."""
    out: dict[int, int] = {}
    for year in YEARS:
        p = bundle / "hourly" / f"system_{year}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        df = df[(df["year"] == year) & (df["pass"] == "P1")]
        out[year] = int((df.groupby("hour")["price"].max() > 200.0).sum())
    return out


def main() -> None:
    """Carry the caiso-240 keeper attestation onto a caiso-241 bundle."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument("--arm", choices=sorted(_ATTEST), required=True)
    ap.add_argument(
        "--still-failing",
        type=int,
        nargs="*",
        default=[2023, 2024],
        help="years whose C3c still FAILS on this bundle's own scorecard "
        "(the keeper's ledger years are 2023 2024; pass 2025 too if its "
        "C3c flipped on this bundle)",
    )
    args = ap.parse_args()
    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    att = {"schema": "calibration-attestation/v1", **att}
    att["governance"]["attested_by"] = _ATTEST[args.arm]
    counts = _tail_counts(args.bundle)
    tag = "caiso-241 " + ("A0 control" if args.arm == "a0" else "B1 arm")
    kept = []
    seen_tail_years = set()
    for exc in att.get("exceptions", []):
        year = int(exc.get("year", 0))
        if exc.get("criterion") != "price_tail":
            kept.append(exc)
            continue
        seen_tail_years.add(year)
        if year not in args.still_failing:
            continue  # band met on this bundle — a spent caveat is dropped
        exc["magnitude"] = (
            f"model {counts.get(year, '?')} h vs actual RT "
            f"{ACTUAL_TAIL[year]} h > $200/MWh (re-measured on the {tag})"
        )
        kept.append(exc)
    for year in args.still_failing:
        if year in seen_tail_years or year not in ACTUAL_TAIL:
            continue
        kept.append(
            {
                "criterion": "price_tail",
                "year": year,
                "magnitude": (
                    f"model {counts.get(year, '?')} h vs actual RT "
                    f"{ACTUAL_TAIL[year]} h > $200/MWh (NEW on the {tag} — a "
                    "disclosed PASS->FAIL flip vs the caiso-240 keeper, "
                    "reported at full magnitude per the precommit)"
                ),
                "rationale": (
                    "C3c scarcity-tail model-class limitation (the ledgered "
                    "criterion; rubric v3.3 standing rule) — adjudication "
                    "belongs to the scorer"
                ),
            }
        )
    att["exceptions"] = kept
    path = args.bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1))
    print(
        f"wrote {path} ({tag}; tail counts {counts}; ledger years "
        f"{sorted(e['year'] for e in kept if e.get('criterion') == 'price_tail')}; "
        "free_parameters left to build_dof_ledger.py)"
    )


if __name__ == "__main__":
    main()
