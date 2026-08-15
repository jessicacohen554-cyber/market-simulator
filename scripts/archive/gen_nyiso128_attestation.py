"""Write the nyiso-128 arms' calibration attestations from committed records.

Both arms inherit the `2026-08-04-nyiso-125-seam-envelope` keeper ledger. The
treatment adds ONE entry for ``nyiso_solar_market_generator_basis`` and keeps
``n_residual`` at 6 — the mechanism introduces no free parameter.

**The one integrity decision here, made deliberately and stated in the artifact
itself: the treatment does NOT carry the 2023 C3c exception.**

The inherited exception's own classification reads *"five-zone representation
**cannot form** the sub-zonal NYC/LI load-pocket scarcity that sets NYISO's real
RT tail"* — an **under-production** story, and that is what it licenses. On the
treatment, 2023 fails the tail gate in the **opposite direction**: 22 h > $300
against a measured 10 h, i.e. **2.20× OVER-produced**. Letting an
over-production ride under an under-production caveat would launder a real miss
into a ledgered one, which is exactly what a ledger exists to prevent. So the
2023 entry is withheld on the treatment and its C3c reads **FAIL**, un-ledgered
and visible.

2024 (3 h vs 12 h, 0.25× — genuine under-production) and 2025 keep the
exception, with magnitudes re-measured on THIS bundle rather than carried
verbatim from the incumbent (the nyiso-125 precedent: an attestation must never
cite a different run's numbers than its own bundle's scorer reports).

Usage::

    python scripts/gen_nyiso128_attestation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

PRIOR_KEEPER = REPO / "results/calibration/nyiso125_seam_A/calibration_attestation.json"
GATES = REPO / "results/calibration/_nyiso128_ab_gates.json"
CONTROL = REPO / "results/calibration/nyiso128_control"
TREATMENT = REPO / "results/calibration/nyiso128_treatment"

# Measured > $300/MWh hours per arm, against the committed RT actual.
TAILS: dict[str, dict[int, tuple[int, int]]] = {
    "control": {2023: (18, 10), 2024: (2, 12), 2025: (21, 42)},
    "treatment": {2023: (22, 10), 2024: (3, 12), 2025: (24, 42)},
}

# Years whose C3c miss the inherited under-production caveat legitimately
# covers, per arm. See the module docstring for why 2023 is withheld on the
# treatment.
LEDGERED_YEARS: dict[str, tuple[int, ...]] = {
    "control": (2023, 2024, 2025),
    "treatment": (2024, 2025),
}

LEDGER_ENTRY = {
    "name": "nyiso_solar_market_generator_basis",
    "value": "True (NYISO-only; solar capacity basis)",
    "identification": (
        "MEASURED, ZERO FREE PARAMETERS — registry membership is an IDENTITY, "
        "not a chosen value. NYISO solar capacity comes from NYISO's own Gold "
        "Book Table III-2a 'NYISO Market Generators' (published load zone, "
        "nameplate MW and in-service date per unit; artifact "
        "data/raw/reference/nyiso-market-solar-capacity.csv, "
        "scripts/data/derive_nyiso_market_solar.py) instead of the EIA-860 "
        "utility-scale operable schedule. THE DEFECT IT CORRECTS IS A DOUBLE "
        "COUNT AGAINST THE LOAD SERIES: EIA-860 lists every NY solar plant "
        ">= 1 MW including ~2 GW of distribution-connected NY-Sun community "
        "solar that is NOT a NYISO market generator, and whose output is "
        "ALREADY NETTED OUT of the EIA-930 NYIS demand series the model uses as "
        "load (NYIS 'NG: SUN' is identically zero in every hour of 2023-2025 — "
        "nyiso-106 measured 8,760/8,760 zero hours). NOTHING IS FREE: the three "
        "columns are published, the A-K -> five-zone crosswalk is the one the "
        "rest of the codebase already uses "
        "(data.nyiso_demand_response._ZONE_TO_MODEL), and the monthly ramp is "
        "the same month-of-commercial-operation construction "
        "renewables._eia860_monthly_capacity already applies to EIA-860. No "
        "percentile, no threshold, no scalar is chosen anywhere. "
        "INDEPENDENTLY LEVEL-CHECKED BEFORE THE CORRECTION WAS BUILT: the "
        "registry's own Net Energy over its own mid-year capacity gives a 12.9 % "
        "(2023) / 13.9 % (2024) capacity factor — physical utility PV, within a "
        "point of the 0.133 the model's (nyiso-75 donor-repaired) NYISO solar "
        "profile already carries, so the SHAPE and CF LEVEL were already right "
        "and only the CAPACITY BASIS was wrong. Rule 13 [R-MEASURED]: an INPUT "
        "(which plants are market generators) that regenerates for a forward "
        "year from the same registry and responds to changed conditions; it is "
        "NOT the measured generation series and NOT a cap at delivered output — "
        "the explicit contrast is caiso_solar_cap_at_delivered, which pins an "
        "outcome and is barred from any keeper. The LP still dispatches and "
        "curtails solar endogenously."
    ),
    "swept": "never",
    "declared_limitation": (
        "STATED IN THE PRE-REGISTRATION BEFORE ANY RESULT EXISTED (PREREG "
        "nyiso-128 section 4) and reported after: this swaps the capacity BASIS "
        "only and keeps the ISO-wide CF normalization (~0.133 realized), while "
        "NYISO's registered fleet is more tracking-heavy (~0.20 CF on the Gold "
        "Book's own Net Energy column). Armed, it delivers 0.21 / 0.52 / 0.75 "
        "TWh against the registry's published 0.23 / 0.50 / 1.08 — within 8 % "
        "and 4 % in 2023/2024 but 0.33 TWh SHORT in 2025, a residual error in "
        "the TIGHTENING direction. On a linear attribution ~0.45 pp of the "
        "+3.8 pp C3a-2025 gain is UNEARNED and only ~3.35 pp is attributable to "
        "the correction. Re-identifying the fleet CF is a SEPARATE object "
        "(rule 19 [R-ONE-MECH]) and is deliberately not bundled here."
    ),
}


def _shared_evidence() -> str:
    """Return the A/B evidence sentence both arms' attestations carry."""
    return (
        "nyiso-128 A/B, arms 2026-08-06-nyiso-128-control / "
        "2026-08-06-nyiso-128-solar-basis, both 2023-2025 in one bundle each "
        "(rule 16), years sequential and invocations concurrent (rule 12). "
        "SIX OF SEVEN PRE-REGISTERED KILL GATES PASS: K1 (exactly one differing "
        "scenario_config field), K2 (zero new unserved energy — both arms zero "
        "slack in all three years), K3 (zero per-class C1 FAILs in either arm), "
        "K4 (LIVE — max zonal |dLMP| 100.5 / 97.3 / 283.0 $/MWh), K5 (the seam "
        "does NOT absorb the correction: import p50 moves +52 / 0 / +42 MW and "
        "import energy +0.076 / -0.000 / +0.027 TWh, so the removed solar is "
        "replaced by IN-STATE THERMAL), K7 (C7 and C8 PASS in both arms). "
        "K6 FIRED AND IS ADJUDICATED, NOT UNEXPLAINED (owner ruling 2026-08-06): "
        "the same-HEAD control reads C3a +6.2 / -1.7 / -7.0 % against the "
        "incumbent's recorded +7.7 / -0.8 / -10.2 % on an identical 680-field "
        "recipe. That is a STALE-BASELINE artifact — main advanced by dozens of "
        "merged fixes since the incumbent's git_sha 49aac023, and nyiso-106's "
        "solar benchmark repair states in its own finding that it 'applies to "
        "the next NYISO solve' — so a baseline that IMPROVED after fixes landed "
        "is the expected behaviour, not a defect owing a deep diagnosis. The "
        "gate assumed a static baseline; that assumption was wrong, not the "
        "result. P1 CONFIRMED: JJA h16-h18 2025 CT_PEAKER +109 MW, ST_GAS "
        "+365 MW, CC_REGULAR +142 MW against solar -1,218 MW."
    )


def main() -> int:
    """Write both arms' attestations."""
    prior = json.loads(PRIOR_KEEPER.read_text())
    if not GATES.exists():
        raise FileNotFoundError(f"gate record missing: {GATES}")
    prior_mag = {int(e["year"]): e.get("magnitude", "") for e in prior["exceptions"]}
    shared = _shared_evidence()

    for arm, dest in (("control", CONTROL), ("treatment", TREATMENT)):
        obj = json.loads(json.dumps(prior))
        obj["governance"] = dict(prior["governance"])
        obj["governance"]["attested_by"] = f"nyiso-128 {arm.upper()} — " + shared

        rebuilt = []
        for e in json.loads(json.dumps(prior["exceptions"])):
            year = int(e["year"])
            if year not in LEDGERED_YEARS[arm]:
                continue
            model, actual = TAILS[arm][year]
            e["magnitude"] = (
                f"RE-MEASURED on this bundle (nyiso-128 {arm}): model {model} h "
                f"> $300/MWh against RT actual {actual} h "
                f"({model / actual:.2f}x). Prior keeper magnitude, lineage only: "
                + str(prior_mag.get(year, "")).split(" PRIOR MAGNITUDE: ")[0]
            )
            rebuilt.append(e)
        obj["exceptions"] = rebuilt

        if arm == "treatment":
            obj["_withheld_exception"] = {
                "criterion": "price_tail",
                "year": 2023,
                "withheld_because": (
                    "THE 2023 C3c MISS IS NOT THE MISS THIS LEDGER LICENSES. The "
                    "inherited exception's own classification reads 'five-zone "
                    "representation CANNOT FORM the sub-zonal NYC/LI load-pocket "
                    "scarcity that sets NYISO's real RT tail' — an "
                    "UNDER-production caveat. On this arm 2023 fails in the "
                    "OPPOSITE direction: 22 h > $300 against a measured 10 h, "
                    "2.20x OVER-produced. Ledgering it would launder a real miss "
                    "into a caveat, which is what a ledger exists to prevent. "
                    "The 2023 exception is therefore WITHHELD and C3c-2023 reads "
                    "FAIL, un-ledgered and visible. This is a REGRESSION against "
                    "the incumbent, which passed 2023 at 1.80x, and it is the "
                    "stated cost of the promotion."
                ),
            }
            fp = json.loads(json.dumps(prior["free_parameters"]))
            n_prev = int(fp["n_entries"])
            fp["entries"] = list(fp["entries"]) + [LEDGER_ENTRY]
            fp["n_entries"] = n_prev + 1
            fp["n_residual"] = int(prior["free_parameters"]["n_residual"])
            fp["seeded"] = (
                "2026-08-06 nyiso-128 treatment — the "
                "2026-08-04-nyiso-125-seam-envelope keeper ledger plus ONE entry "
                "for nyiso_solar_market_generator_basis. n_entries "
                f"{n_prev} -> {n_prev + 1}, n_residual UNCHANGED at "
                f"{fp['n_residual']}: the mechanism introduces no free "
                "parameter. Its capacity is NYISO's own published market-"
                "generator registry, membership in which is an identity, and "
                "its monthly ramp is the construction the EIA-860 path already "
                "applies. The one thing that WOULD have needed a chosen number "
                "— the registered fleet's own capacity factor — was left on the "
                "incumbent ISO-wide basis and its residual error DECLARED "
                "(see the entry's declared_limitation) rather than fitted."
            )
            obj["free_parameters"] = fp

        (dest / "calibration_attestation.json").write_text(json.dumps(obj, indent=1))
        print(
            f"{arm:<10}: ledger {obj['free_parameters']['n_entries']} entries, "
            f"n_residual {obj['free_parameters']['n_residual']}, "
            f"{len(obj['exceptions'])} C3c exception(s) "
            f"({'2023 WITHHELD' if arm == 'treatment' else 'all years'})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
