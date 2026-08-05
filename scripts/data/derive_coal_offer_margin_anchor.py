"""Derive the coal-offer net-revenue margin ANCHOR + LEVEL for an ISO.

The identification constants of the ``coal_offer_net_revenue_margin``
mechanism (ERCOT-137, the gas net-revenue margin's coal analogue —
``constants.COAL_OFFER_MARGIN_ANCHOR_BY_ISO`` /
``COAL_OFFER_MARGIN_LEVEL_BY_ISO``; gas design doc
``docs/handoffs/gas-offer-net-revenue-margin-design-2026-07.md``). Two
constants, both read from COMMITTED measured artifacts — nothing is re-run,
nothing touches a residual:

* **ANCHOR ($/MMBtu)** — the training-window (2023–2025) capacity-weighted
  mean of the model's own delivered coal price at the LP seam, from the
  committed ERCOT-135 seam capture
  ``results/calibration/ercot135_coal_merit_order.json``
  (``A_model_offer.<year>.per_plant``: ``fuel_price_mmbtu`` × ``pmax_mw``).
  That series is per-plant EIA-923 receipts where published (Fayette /
  J K Spruce / San Miguel — the only ERCOT reporters, ercot135 §3) and the
  measured coal supply trajectories elsewhere — the exact fuel basis the
  dispatch prices coal on, so at ``fuel == anchor`` the reformed bid reduces
  exactly to the measured level (the identification point, not a tunable).

* **LEVEL ($/MWh)** — the real fleet's RT supply-curve bottom: 60-Day SCED
  ``Submitted TPO-Price1`` capacity-weighted p50 at 98.8–100 % coverage,
  pooled res-hours-weighted across the four 2024–2025 disclosure subsets,
  from the committed ERCOT-136 artifact
  ``results/calibration/ercot136_coal_headroom_conduct.json``
  (``B1_curve_bottom``, COAL rows — the ERCOT-136 §3 decisive measurement).
  ``Min Gen Cost`` (28–31 % coverage, coal p25 $18.00 every subset) is
  printed as corroboration only — that coverage regime is what invalidated
  the pooled econ_high (ercot122 §1) and it is NEVER the anchor.

The margin itself is the derived identity, never a registered scalar::

    margin($/MWh) = LEVEL − HR_capwtd × ANCHOR

applied per-tranche at the tranche's own heat rate in
:func:`market_sim.data.fleet.legacy_bins.apply_coal_tranches`, so the
resolved ``_mustrun`` bid at anchor fuel is exactly LEVEL (basis-consistent
by construction — the ercot132-leg-B basis-mismatch failure mode cannot
recur at the identification point).

Rule-23 frozen derive: re-run ONLY when a source artifact is regenerated
from new disclosure data (a new SCED intake, a coal-price source revision),
and cite that data change in the re-derivation commit. NEVER because a
residual moved.

It is a REPORTING / derivation tool only — default-off in every solve path.
The model artifacts it informs are the hand-set
``COAL_OFFER_MARGIN_ANCHOR_BY_ISO`` / ``COAL_OFFER_MARGIN_LEVEL_BY_ISO``
entries in ``config/constants.py`` (cited back to this script), consumed by
the harness only under ``--coal-offer-margin``.

Usage::

    python scripts/data/derive_coal_offer_margin_anchor.py --iso ERCOT
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

# Committed measured artifacts (the ONLY inputs — rule 23):
ERCOT135_SEAM_CAPTURE = REPO / "results/calibration/ercot135_coal_merit_order.json"
ERCOT136_CONDUCT = REPO / "results/calibration/ercot136_coal_headroom_conduct.json"

# Training window (CLAUDE.md rule 22: 2023–2025 is the ONLY tuned-against span).
TRAIN_YEARS = ("2023", "2024", "2025")


def derive_ercot() -> dict:
    """Return the ERCOT anchor/level/margin identification block."""
    e135 = json.loads(ERCOT135_SEAM_CAPTURE.read_text())
    e136 = json.loads(ERCOT136_CONDUCT.read_text())

    # ANCHOR: capacity-weighted delivered coal price at the LP seam, per
    # training year, then the plain window mean (mirrors the gas anchor's
    # window-mean construction).
    year_fp: dict[str, float] = {}
    year_hr: dict[str, float] = {}
    for y in TRAIN_YEARS:
        pp = e135["A_model_offer"][y]["per_plant"]
        cap = sum(p["pmax_mw"] for p in pp)
        year_fp[y] = sum(p["pmax_mw"] * p["fuel_price_mmbtu"] for p in pp) / cap
        year_hr[y] = sum(p["pmax_mw"] * p["heat_rate_capwtd"] for p in pp) / cap
    anchor = sum(year_fp.values()) / len(year_fp)
    hr_capwtd = sum(year_hr.values()) / len(year_hr)

    # LEVEL: pooled res-hours-weighted cap-wtd p50 of Submitted TPO-Price1
    # over the four COAL subsets (2024 tail/control, 2025 control/tail).
    rows = [r for r in e136["B1_curve_bottom"] if r["class"] == "COAL"]
    tot_h = sum(r["res_hours"] for r in rows)
    level = sum(r["res_hours"] * r["bot_p50"] for r in rows) / tot_h

    # Corroboration print-outs (documentation only, never the anchor).
    mgc = [r for r in e136.get("C_min_gen_cost", []) if r.get("class") == "COAL"]
    margin = level - hr_capwtd * anchor
    return {
        "iso": "ERCOT",
        "anchor_usd_mmbtu": round(anchor, 4),
        "level_usd_mwh": round(level, 4),
        "hr_capwtd": round(hr_capwtd, 4),
        "margin_usd_mwh": round(margin, 4),
        "year_fuel_capwtd": {y: round(v, 4) for y, v in year_fp.items()},
        "level_subsets": [
            (r["year"], r["family"], r["res_hours"], r["bot_p50"]) for r in rows
        ],
        "min_gen_cost_corroboration": [
            (r.get("year"), r.get("family"), r.get("mingen_p25")) for r in mgc
        ],
    }


def _verify_year_mode(year: int, limb_key: str, constant_name: str) -> int:
    """ercot-169 ``--year`` mode: TEST this identification's fuel-invariance claim.

    Rule-23 re-run cite: the ercot-157 delivery-{year} SCED corpus landing, which
    dissolves this constant's declared "no 2023 SCED disclosure exists"
    extrapolation premise. Because this is a MARGIN form, the corpus does not
    merely enable re-derivation — it tests the invariance claim itself:
    ``level_year = measured_instrument_year - HR x (fuel_year - anchor)`` is
    compared against the armed constant inside the identification's OWN cited
    cross-subset dispersion band. Decision rule pre-registered in
    ``docs/PRECOMMIT-ercot169-margin-fuel-invariance-2026-08-05.md``; this mode
    applies it, it does not choose it. Nothing is written and no residual is
    consulted — a REFUTED or NOT-IDENTIFIABLE outcome is reported, never repaired
    here (rules 13/23).
    """
    sys.path.insert(0, str(REPO))
    from market_sim.config import constants as _C

    from scripts.lib.sced_corpus_instruments import verify_year

    armed = float(getattr(_C, constant_name)["ERCOT"])
    out = verify_year(limb_key, year, armed)
    print(json.dumps(out, indent=2, default=float))
    v = out.get("T1_gating", out)
    print()
    print(
        f"ercot-169 fuel-invariance test, limb {v.get('limb', '?')} "
        f"({constant_name}['ERCOT'] = {armed}):\n"
        f"  delivery-{year} measured   = {v.get('measured_usd_mwh')} $/MWh "
        f"({v.get('instrument')}, {v.get('window')})\n"
        f"  fuel response removed     = {v.get('fuel_response_removed_usd_mwh')} $/MWh\n"
        f"  level_{year}                = {v.get('level_year_usd_mwh')} $/MWh "
        f"(delta {v.get('delta_usd_mwh')}, band +/-{v.get('band_usd_mwh')})\n"
        f"  curve coverage            = {v.get('curve_share')} "
        f"(licence >= {v.get('licence_threshold')})\n"
        f"  VERDICT                   = {v.get('verdict')}"
    )
    return 0


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--iso", default="ERCOT")
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="ercot-169 verification mode (matrix §5.1 item 13): TEST this "
        "identification's fuel-invariance claim on the delivery-year SCED "
        "corpus instead of re-printing the 2024-2025 identification. "
        "Training years only (rule 22).",
    )
    args = parser.parse_args()
    if args.iso.upper() != "ERCOT":
        raise SystemExit(
            f"--iso {args.iso}: only ERCOT has the measured SCED conduct "
            "artifacts this identification requires (ercot135/ercot136). "
            "Another ISO derives its own pair from its own market's data in "
            "its own lane (rule 25 — never transferred)."
        )
    if args.year is not None:
        raise SystemExit(
            _verify_year_mode(
                args.year, "coal_mustrun", "COAL_OFFER_MARGIN_LEVEL_BY_ISO"
            )
        )
    out = derive_ercot()
    print(json.dumps(out, indent=2))
    print()
    print(
        f"register in config/constants.py:\n"
        f"  COAL_OFFER_MARGIN_ANCHOR_BY_ISO['ERCOT'] = {out['anchor_usd_mmbtu']}\n"
        f"  COAL_OFFER_MARGIN_LEVEL_BY_ISO['ERCOT']  = {out['level_usd_mwh']}\n"
        f"derived fleet margin (identity, applied per-tranche at its own HR): "
        f"{out['margin_usd_mwh']} $/MWh vs full fuel at anchor"
    )


if __name__ == "__main__":
    main()
