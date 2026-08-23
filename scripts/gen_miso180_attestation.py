"""Generate miso180_anch_B's calibration attestation from the keeper's.

The arm is the miso-177 keeper recipe plus exactly one zero-residual-DOF
mechanism (the gen_miso169_attestation pattern), so its attestation is the
keeper's with: two MEASURED-identified ledger entries for the anchored
spread graft (the committed miso-179 vector and the ex-ante-identified
anchor rank), a rewritten ``governance.attested_by`` for the miso-180 A/B,
and this session's disclosures appended. ``n_residual`` is UNCHANGED at 2
(PREREG-miso180 §5 G-6). Exceptions carry unchanged.
"""

import json

SRC = "results/calibration/miso177_rho_B/calibration_attestation.json"
DST = "results/calibration/miso180_anch_B/calibration_attestation.json"

d = json.load(open(SRC))

d["free_parameters"]["entries"].append(
    {
        "name": "miso_offer_spread vector (miso_offer_spread_anchored)",
        "where": (
            "data/raw/_validation-source/miso_offer_level_dispersion.json "
            "(sha256 b4e723127de63806..., pinned in "
            "constants.MISO_OFFER_SPREAD_ARTIFACT_SHA256) -> "
            "data.offer_curves.apply_miso_offer_spread_anchored"
        ),
        "identification": "measured",
        "lineage_solves": (
            "0 (the committed miso-179 pooled JJA 2023-2025 DA BOOK-ELIG "
            "identification, derived BEFORE this mechanism existed; never "
            "touched a residual — zero LMP/award columns in the path)"
        ),
        "value": (
            "199-point capacity-weighted implied-offer-heat-rate quantile "
            "vector (p10/p50/p90/p95/p99 = 1.10/5.33/15.11/24.46/72.61 "
            "MMBtu/MWh; 881 units, 4.08M unit-hours). Only the above-anchor "
            "RISE Q(r) - Q(a) is consumed (the level-replacement form is R, "
            "miso-179)."
        ),
    }
)
d["free_parameters"]["entries"].append(
    {
        "name": "miso_offer_spread anchor rank (MISO_OFFER_SPREAD_ANCHOR_RANK)",
        "where": "config.constants.MISO_OFFER_SPREAD_ANCHOR_RANK = 0.875",
        "identification": "measured",
        "lineage_solves": (
            "0 (identified ONCE by the PREREG-miso180 §2 frozen rule — the "
            "model/book distribution crossing rank on the frozen miso-179 H* "
            "constructions, an inputs-only path: demand-side hour set, input "
            "offer surface mc_base, measured book; no LMP, no residual, no "
            "solve output anywhere. Anti-sweep clause: computed once, no "
            "variant ever tried; record "
            "_miso180_anchored_spread_precheck.json)"
        ),
        "value": (
            "r = 0.875 (single crossing, model $56.55 vs eligible book "
            "$55.54 at the anchor, zero under-gridpoints below it; guards "
            "0.50 < r <= 0.975 clear)"
        ),
    }
)
d["free_parameters"]["n_entries"] = len(d["free_parameters"]["entries"])

d["governance"]["attested_by"] = (
    "ARM - EXACTLY ONE MECHANISM CHANGES: miso_offer_spread_anchored=true. "
    "miso-180, 2026-08-23. PREREG "
    "results/calibration/PREREG-miso180-anchored-spread-2026-08-23.md was "
    "committed and pushed (14ea321) BEFORE the anchor identification, the "
    "pre-check probe, or any new hour-set-conditioned quantity existed; the "
    "one open design question (the anchor rank) was adjudicated ex ante in "
    "writing among the three chartered candidates, and the anchor was "
    "computed ONCE by the frozen rule (anti-sweep clause honoured). Phase A "
    "cleared every pre-registered kill (K-a 0.387 vs >=0.5; K-b 2023 "
    "predicted +1.77% vs +/-10; K-c 2025 predicted +0.592 pp vs >=+0.5). "
    "Both arms are replay_keeper re-solves of the "
    "2026-08-22-miso-177-rho-measured keeper's own meta.json at this "
    "session's HEAD, --year 2023 2024 2025 in ONE invocation each, years "
    "sequential (rules 12/16); the arm's single delta rode the sanctioned "
    "replay_keeper --set channel. CONTROL BIT-IDENTITY: "
    "2026-08-23-miso-180-control reproduces the committed keeper with "
    "numeric max|diff|=0 on every scored sidecar of every year (G-0 12/12). "
    "The mechanism adds ZERO residual-identified parameters (n_residual "
    "unchanged at 2): the vector is the committed miso-179 measured "
    "identification and the anchor is the pre-registered inputs-only "
    "crossing-rank identification — see their ledger entries. Rule 22: no "
    "year outside 2023-2025 was solved, scored or registered; MISO holds "
    "neither complete nor final and the holdout spend freeze is untouched."
)

d["disclosures"]["miso180_ab"] = (
    "A/B verdict record: results/calibration/_miso180_ab_gates.json "
    "(G-0..G-7 + the ungated report cuts); structural reports "
    "_miso180_structural_reports.json (South dipole / buckets / "
    "delta-channels); Phase A record _miso180_anchored_spread_precheck.json."
)

json.dump(d, open(DST, "w"), indent=1)
print(
    f"wrote {DST} (n_entries={d['free_parameters']['n_entries']}, "
    f"n_residual={d['free_parameters']['n_residual']})"
)
