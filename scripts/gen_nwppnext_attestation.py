"""Emit the NWPP-NEXT calibration attestation for ``results/calibration/nwppnext_span``.

NWPP-NEXT (PRECOMMIT ``docs/handoffs/PRECOMMIT-nwpp-next-ferc714-partialcarry-2019-2025-2026-09-25.md``)
is the R-NWPP keeper recipe unchanged, plus two measured-input repairs:

* the pool member gap guard with PSEI's FERC 714 planning-area load as the
  measured substitute (``eia930/frames.py``; not a ``ScenarioConfig`` field, a
  data-path repair that is inert in 2021-2025), and
* ``partial_plant_exit_carry`` (existing gated field), which restores units that
  retired mid-year while a sister unit kept the plant on the operable sheet
  (Centralia 1 and Colstrip 1-2 in 2020, Kennecott in 2019).

It reuses :mod:`gen_rnwpp_attestation` with this lane's deltas applied: the
armed set gains ``partial_plant_exit_carry``, the offer-curve fingerprint is the
keeper's curve with the redundant bare ``COAL`` key removed by the COAL-SUB
translation (identical bands, so an identity), and 2020 joins the year set.
**ZERO NEW FREE PARAMETERS** (rules 21 / 24).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_rnwpp_attestation as base  # noqa: E402

DEFAULT_BUNDLE = REPO / "results/calibration/nwppnext_span"
# Keeper curve (ac3344c3...) minus the bare "COAL" key, whose bands equal every
# COAL_* subclass entry — the COAL-SUB translation is an identity on this curve.
OFFER_CURVE_SHA256 = "6a13731e43c4e60d5ea84fcc08ce0695bb0f5e5287c6568ec7bf2eda75410c61"


def build(bundle: Path = DEFAULT_BUNDLE) -> dict:
    """Return the NWPP-NEXT attestation built on the R-NWPP generator."""
    base.OFFER_CURVE_SHA256 = OFFER_CURVE_SHA256
    base._ARMED = (*base._ARMED, "partial_plant_exit_carry")
    base._SOURCES["partial_plant_exit_carry"] = (
        "EIA-860 Retired-and-Canceled sheet: a unit retiring during the vintage year "
        "whose plant stays on the operable sheet through a sister unit is carried through "
        "its published retirement month (Centralia 1 / Colstrip 1-2 in 2020)"
    )
    att = base.build(bundle)
    att["lane"] = "NWPP-NEXT"
    att["switches"]["hydro_backfill_year"]["value"] = {
        "2019": None,
        "2020": None,
        "2021": None,
        "2022": None,
        "2023": 2024,
        "2024": 2024,
        "2025": 2024,
    }
    att["switches"]["pool_member_gap_guard"] = {
        "value": True,
        "where": "market_sim.data.eia930.frames._pool_hourly_frame (data path, not a ScenarioConfig field)",
        "identification": "measured-physical",
        "source": (
            "FERC Form 714 Part III Schedule 2 PSEI hourly load (PUDL), reconciled to PSEI's "
            "same-year EIA-930 basis by the data's own clock offset and median ratio; net "
            "generation from PSEI's own EIA-930 fuel columns. Fires in 2019 (384 h) and 2020 "
            "(8,659 h) only."
        ),
    }
    att["governance"]["notes"] = (
        "R-NWPP recipe plus two measured-input repairs (rules 13/14): a FERC 714 fill for "
        "PSEI's missing EIA-930 demand and the existing partial-plant exit channel. Offer-curve "
        f"multipliers unchanged (sha256 {OFFER_CURVE_SHA256[:12]}..., the keeper curve after the "
        "COAL-SUB identity); nothing swept, nothing selected on a gate. Short-gas outage "
        "windows still NOT armed."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36). 2020 is solved for the first "
        "time: PSEI's EIA-930 demand is filled from FERC 714 (scale 1.1905, lag -1 h over 101 "
        "overlapping hours)."
    )
    disc["structure_gap_pre_2023"] = (
        "hydro_cascade_coupling is armed but INERT in 2019-2022: the CROHMS-derived cascade "
        "artifact covers 2023-2025 only."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "2023/2024 carry neither repair's energy (zero-LP census + identical fleet arrays), so "
        "they read as a drift check against the keeper; 2021/2025 add zero-availability LP "
        "columns only; 2019 moves by Kennecott + the PSEI fill; 2020 is new."
    )
    disc["psei_2021_august_defect"] = (
        "EIA-930 PSEI demand 2021-08-02..15 sits 1,699 MW below FERC 714 (0.573 TWh) with no "
        "NaN, so the gap guard does not see it. Not repaired; routed."
    )
    return att


def main() -> int:
    """CLI: print or write the attestation."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default=str(DEFAULT_BUNDLE))
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    bundle = Path(args.bundle)
    att = build(bundle)
    out = bundle / "calibration_attestation.json"
    if args.write:
        out.write_text(json.dumps(att, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(json.dumps(att, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
