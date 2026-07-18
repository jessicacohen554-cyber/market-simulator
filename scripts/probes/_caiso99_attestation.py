"""Write the caiso-99 bundle attestation (Mechanism B measured shape envelope).

Derives ``caiso99_shape_B/calibration_attestation.json`` from the caiso-97
KEEPER attestation already committed in the repo (same lever set), swapping the
``attested_by`` line, appending the single-delta note, and appending ONE new
DOF-ledger entry for the envelope's anchor statistic — identification
"measured" (the p95-of-days convention fixed a priori from the EIA-930/EIA-860
derivation, rule 23/25; never swept against a residual), so ``n_entries``
increments while ``n_residual`` does not. Deterministic from repo state
(the _caiso80/82/84/87_attestation.py pattern).

Usage: python scripts/probes/_caiso99_attestation.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
BASE = ROOT / "caiso97_hodtrim_B" / "calibration_attestation.json"
OUT = ROOT / "caiso99_shape_B" / "calibration_attestation.json"

DELTA99 = (
    " PLUS the single caiso-99 delta: caiso_storage_shape_anchor=True "
    "(FINDING-caiso98 §7B Mechanism B, owner-authorized; "
    "FINDING-caiso99-storage-shape-2026-07-18). The keeper already dispatches "
    "the measured EIA-860 per-vintage COD-ramped battery fleet (the caiso-99 "
    "discovery: storage_vintage_ramp=True rides the backcast_config CAISO "
    "base; FINDING-caiso98 §11's dead-flag root cause is falsified and "
    "corrected in place), but the energy-only LP charge-arbitrages that fleet "
    "at up to nameplate in the midday belly — the C3a belly over-price "
    "(+10.9/+9.0/+8.4) sits ENTIRELY in model-charging hours — and "
    "over-discharges the 2023/24 evening. The delta caps battery Chg/Dis[s,t] "
    "at env_p95[year, hod] × power_cap[s,t]: the measured fleet-normalized "
    "diurnal capability envelope (EIA-930 CISO NG:OTH ÷ EIA-860 monthly "
    "battery MW, p95-of-days per hour-of-day per year — belly charge "
    "0.428/0.517/0.510, evening discharge 0.475/0.576/0.547; the fleet-wide "
    "max-ever hod rate is ~0.67-0.76, so nameplate fleet-wide operation is "
    "unobserved). AS holdback, DA-bid conservatism and commissioning ramps "
    "are the physics the envelope embeds (rule 19: mutually exclusive with "
    "the probe-inert caiso-74 AS power reservation, validator-enforced). "
    "Committed rule-23 derivation data/raw/reference/"
    "caiso-storage-shape-envelope.csv (scripts/derive_caiso_storage_shape.py; "
    "re-derives only on an EIA-930/EIA-860 source update); p95 is the "
    "repo-standard measured-capability statistic (corridor measured-p95 ATC / "
    "GTC p95 convention), fixed a priori, p90/p99 emitted for transparency "
    "and never solved (rule 25). Forward story (rule 13): per-MW-of-fleet "
    "market-behavior shape × the projected fleet MW — regenerates from its "
    "sources and responds to fleet growth; the LP keeps full economic choice "
    "of when/how much to cycle INSIDE the envelope (48 hod statistics/year, "
    "never the measured 8760 — nothing pins dispatch to actuals)."
)

DOF_ENTRY = {
    "name": "caiso_storage_shape_envelope_p95",
    "where": "data/raw/reference/caiso-storage-shape-envelope.csv "
    "(chg_frac_p95/dis_frac_p95 per year × hod)",
    "identification": "measured",
    "source": "EIA-930 CISO 'NG: OTH' hourly ÷ EIA-860 energy-storage "
    "operable monthly fleet MW; p95-of-days per (year, hod) — the "
    "repo-standard measured-capability statistic, fixed a priori "
    "(scripts/derive_caiso_storage_shape.py, rule 23; no quantile sweep, "
    "rule 25)",
    "lineage_solves": "0 residual-driven solves (single pre-registered "
    "A/B leg caiso99_shape_B; FINDING-caiso99 §5 gates committed first)",
}


def main() -> None:
    att = json.loads(BASE.read_text())
    att["governance"]["attested_by"] = (
        "caiso-99 storage-charter session 2026-07-18 (Mechanism B measured "
        "shape envelope, single-delta A/B vs same-machine caiso99_repro_A; "
        "carries the caiso-97 keeper attestation + lever set)"
    )
    att["governance"]["note"] = att["governance"]["note"] + DELTA99
    fp = att["free_parameters"]
    fp["entries"].append(DOF_ENTRY)
    fp["n_entries"] = int(fp["n_entries"]) + 1
    # identification "measured" — n_residual unchanged by construction.
    OUT.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
