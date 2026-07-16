"""Write the caiso-87 probe attestation.

Derives the bundle's ``calibration_attestation.json`` from the caiso-84 keeper
attestation already committed in the repo (same lever set and DOF ledger — the
probe adds NO free parameter: the single delta is the gated
``caiso_dsw_surplus_clean`` measured-depth capability,
FINDING-caiso82 §3 / FINDING-caiso86b-partial-ladder-gates-2026-07-16),
swapping the ``attested_by`` line and appending the probe's single-delta note.
Deterministic from repo state (_caiso80/82/84_attestation.py pattern).

Usage: python scripts/probes/_caiso87_attestation.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
BASE = ROOT / "caiso84_gas_spot_level" / "calibration_attestation.json"

DELTA87 = (
    " PLUS the single caiso-87 delta: caiso_dsw_surplus_clean=True "
    "(FINDING-caiso82 §3 'measured clean DEPTH' lane; FINDING-caiso86b closed "
    "the measured-ladder-PRICE alternative on its LOYO gates). In surplus-West "
    "hours the marginal import into CAISO is a WEIM/EDAM transfer attributed "
    "to CLEAN surplus resources — the measured CAISO−hub spread in those hours "
    "carries NO unspecified border-carbon wedge — but the model's zero-EF "
    "depth truncates at the firm blocks + PNW_midC (~4.1–5.2 GW), after which "
    "every import MW pays a fossil CARB rung (+$12–18): the A2 attribution "
    "(2026-07-16, caiso-84 replay) shows the model's soft-month λ matching the "
    "carbon-wedged DSW rungs in 43% of May-2023 hours while the actual clears "
    "below every model offer in 69% of them, at parity. The delta arms a "
    "DSW_surplus_clean tranche (EF 0, the same Path-46 wheel, priced at the "
    "measured Palo Verde hub by the per-hub injector) carrying the corridor's "
    "MEASURED depth-in-surplus — p95 of measured WECC_DSW net import (EIA-930 "
    "CISO DIBAs, model clock) over trigger-ON hours: 5,312/4,792/5,472 MW "
    "2023/24/25 (estimation-stage honesty gates: CV 0.056 ≤0.20, LOYO "
    "mean-of-other-two worst 12.5% ≤25%) — net of the shaped firm block, ONLY "
    "in hours whose measured Palo Verde hub price sits below the remote "
    "gas-CCGT floor (the existing coupling heat rate 6.97 = EF 0.37/0.0531 × "
    "the measured SoCal citygate weekly print + $2.5 remote VOM, no carbon — "
    "AZ/NV are uncarbonized; the hub's own price says gas is not marginal, so "
    "the surplus is clean). The trigger evaluates ONLY on measured hub hours "
    "(the 2023 Jan–Feb OASIS retention gap's reference-formula fill is pricing "
    "continuity, not surplus evidence — filled hours stay non-surplus, so the "
    "closed caiso-84 winter lane cannot reopen through the fill). A "
    "CAPABILITY, not a floor (pmin 0, no D-2 row, no forcing); the fossil "
    "rungs are unchanged and price the flow beyond the clean depth (secondary "
    "dispatch — imports past the clean surplus ARE unspecified-attributed); "
    "the corridor ATC envelope still caps delivered flow. ZERO new fitted "
    "scalars: the depth is measured, the trigger reuses the existing coupling "
    "HR and a measured gas print, the wheel is the existing Path-46 basis, EF "
    "0 is the CARB EIM GHG-attribution treatment (market design, not a knob). "
    "Identification: EIA-930 CISO interchange × measured intertie LMP × EIA "
    "NG Weekly SoCal citygate print; re-derives only on source updates (rule "
    "23), never an output pinned back (rule 14 — the depth conditions on the "
    "HUB-side state, not on the CAISO price residual). Forward story: the "
    "trigger regenerates from the reference-price seam hub + gas forwards, "
    "the depth carries the pooled static entry (persistent WEIM market "
    "structure). No residual-tuned adder is armed in this run; the DOF "
    "ledger is identical to the caiso-84 keeper (no scalar added)."
)

TARGETS = [
    (
        "caiso87_dsw_surplus_clean",
        "caiso-87 surplus-clean import depth probe session 2026-07-16",
        DELTA87,
    ),
]


def main() -> None:
    """Derive and write the probe attestation."""
    base = json.loads(BASE.read_text())
    for bundle, attested_by, delta in TARGETS:
        out_dir = ROOT / bundle
        if not out_dir.exists():
            print(f"[skip] {bundle}: bundle dir absent")
            continue
        d = json.loads(json.dumps(base))
        d["governance"]["attested_by"] = attested_by
        d["governance"]["note"] = d["governance"]["note"] + delta
        (out_dir / "calibration_attestation.json").write_text(json.dumps(d, indent=1))
        print(f"[ok  ] {bundle}")


if __name__ == "__main__":
    main()
