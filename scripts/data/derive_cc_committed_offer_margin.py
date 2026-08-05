"""Derive the CC committed-block offer LEVEL for an ISO (ERCOT-139).

The identification constant of the ``cc_committed_offer_margin`` mechanism
(``constants.CC_COMMITTED_OFFER_LEVEL_BY_ISO``) — the gas-CC analogue of the
coal min-load net-revenue margin ERCOT-137 promoted
(``scripts/data/derive_coal_offer_margin_anchor.py``), chartered by
``docs/DIAGNOSIS-ercot138-coal-gas-ranking-2026-07-29.md`` §6.

ERCOT-138 measured the defect this level repairs: against ERCOT's own SCED
TPO conduct the model's CC committed/econ bands bid **+$2.8–6.6 /MWh too
dear** through the crossing band (coal's sit at −1.6..+3.9 and are
exonerated), and §2.5 located the residual in a **missing below-cost
committed-CC block** — the model's cheapest CC band bottoms out at $13.3
while the real fleet's median incremental MW is offered at $12.10 and its p25
at $8.38, below its own fuel cost. Coal has that block and it is measured;
gas does not have one.

Two constants, both read from COMMITTED measured artifacts — nothing is
re-run, nothing touches a residual:

* **ANCHOR ($/MMBtu)** — NOT derived here. The mechanism reuses the
  already-committed ``GAS_OFFER_MARGIN_ANCHOR_BY_ISO`` entry (ERCOT 2.2494 —
  the training-window 2023–2025 mean of the model's own delivered-gas series
  at the LP seam). One gas identification point for the whole gas offer
  surface, never a second anchor that could drift against the first
  (rule 19 ``[R-ONE-MECH]`` bookkeeping).

* **LEVEL ($/MWh)** — the real CC fleet's RT supply-curve bottom, expressed
  AT the anchor: 60-Day SCED ``Submitted TPO-Price1`` capacity-weighted p50,
  pooled res-hours-weighted across the four 2024–2025 disclosure subsets,
  from the committed ERCOT-136 artifact
  ``results/calibration/ercot136_coal_headroom_conduct.json``
  (``B1_curve_bottom``, **CC** rows — the same measurement, same instrument,
  same construction and same loader that supplied coal's promoted level, read
  off its COAL twin). Curve coverage on those rows is 95.1–98.0 % of
  RT-dispatchable headroom (``A_ercot123_reproduced.curve_share``), so the
  CC class passes the same RT-instrument licensing test coal passed
  (ERCOT-138 §3.4).

The raw subset bottoms are NOT year-invariant (2024 ≈ $10.1, 2025 ≈ $18.1)
because delivered gas moved $2.213 → $3.232/MMBtu. The margin form's whole
claim is that the *residual above fuel* is what is invariant, so the level is
identified by removing the corpus's OWN measured fuel response::

    HR_implied = (bottom_2025 - bottom_2024) / (fuel_2025 - fuel_2024)
    level_i    = bottom_i - HR_implied x (fuel_i - anchor)
    LEVEL      = res-hours-weighted mean of level_i over the four subsets

``HR_implied`` is measured from the disclosure itself — no model heat rate,
no fitted slope — and its value is the identification's own falsifier: a
physically implausible slope would mean the bottoms do not move with fuel and
the fuel-invariant form is the wrong functional form for CC.
``fuel_i`` is the model's cap-weighted delivered gas on the corpus's OWN
matched hours, read from the committed ERCOT-138 artifact
(``J_physical_vs_markup``, CC rows ``fuel_capwtd``) — the same LP-seam basis
the coal anchor was derived on, so the level is basis-consistent with the
dispatch that consumes it (the ercot132-leg-B basis-mismatch failure mode
cannot recur at the identification point).

The margin itself is the derived identity, never a registered scalar::

    margin($/MWh) = LEVEL - HR_tranche x ANCHOR

applied per-tranche at the tranche's OWN heat rate in
:func:`market_sim.data.offer_curves.apply_cc_committed_offer_margin`, so the
resolved ``_committed`` bid at anchor fuel is exactly LEVEL.

**Independent corroboration** (printed, never the anchor): the CC min-load
block's own declared ``Min Gen Cost`` p50 at 70.0–82.0 % coverage
(``C_min_gen_cost``, CC rows) runs within ~$1/MWh of the TPO bottom in every
one of the four subsets, and the same construction on that second instrument
lands the level within a few percent. Coal's corroborating instrument sat at
28–31 % coverage; CC's sits at 70–82 %, so this level is the better-attested
of the two.

Rule-23 frozen derive: re-run ONLY when a source artifact is regenerated from
new disclosure data (a new SCED intake, a gas-price source revision), and
cite that data change in the re-derivation commit. NEVER because a residual
moved.

It is a REPORTING / derivation tool only — default-off in every solve path.
The model artifact it informs is the hand-set
``CC_COMMITTED_OFFER_LEVEL_BY_ISO`` entry in ``config/constants.py`` (cited
back to this script), consumed by the harness only under
``--cc-committed-offer-margin``.

Usage::

    python scripts/data/derive_cc_committed_offer_margin.py --iso ERCOT
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

# Committed measured artifacts (the ONLY inputs — rule 23):
ERCOT136_CONDUCT = REPO / "results/calibration/ercot136_coal_headroom_conduct.json"
ERCOT138_RANKING = REPO / "results/calibration/ercot138_coal_gas_ranking.json"

#: The measured class whose conduct identifies the level. ERCOT-138's
#: ``MODEL_CC_GROUPS`` is ``("CC_REGULAR",)`` — CC_CHP is reported there as a
#: sensitivity and never pooled into the CC control (its committed state is
#: owned by its steam host, rule 19), so the mechanism's scope matches the
#: measurement's population exactly.
MEAS_CLASS = "CC"


def _pooled(rows: list[dict], value_key: str, weight_key: str = "res_hours") -> float:
    """Return the ``weight_key``-weighted mean of ``value_key`` over ``rows``."""
    tot = sum(float(r[weight_key]) for r in rows)
    return sum(float(r[weight_key]) * float(r[value_key]) for r in rows) / tot


def _level_from_instrument(
    rows: list[dict],
    price_key: str,
    weight_key: str,
    fuel_by_year: dict[int, float],
    anchor: float,
) -> dict:
    """Identify the anchored level from one measured price instrument.

    Args:
        rows: The instrument's per-subset rows (``year``, ``family``, the
            weight and the price key).
        price_key: The subset price statistic (a capacity-weighted p50).
        weight_key: The row weight (``res_hours`` for the TPO bottom, ``n``
            for the Min-Gen-Cost corroboration — each instrument's own
            observation count).
        fuel_by_year: Model cap-weighted delivered gas on the corpus's own
            matched hours, per year.
        anchor: The delivered-gas identification point ($/MMBtu).

    Returns:
        The identification block: the implied heat rate, the per-subset
        anchored levels, the pooled level, and the subset dispersion before
        and after the fuel response is removed (the identification-quality
        statistic — the form earns its keep only if it shrinks).
    """
    years = sorted({int(r["year"]) for r in rows})
    if len(years) != 2:
        raise SystemExit(
            f"level identification needs exactly two fuel-distinct years to "
            f"measure the corpus's own fuel response; got {years}. A one-year "
            "corpus cannot separate the level from the slope (rule 13 — the "
            "slope would become a fitted parameter)."
        )
    y_lo, y_hi = years
    bot_by_year = {
        y: _pooled([r for r in rows if int(r["year"]) == y], price_key, weight_key)
        for y in years
    }
    d_fuel = fuel_by_year[y_hi] - fuel_by_year[y_lo]
    hr_implied = (bot_by_year[y_hi] - bot_by_year[y_lo]) / d_fuel
    levels = [
        {
            "year": int(r["year"]),
            "family": r["family"],
            "weight": float(r[weight_key]),
            "bottom": round(float(r[price_key]), 4),
            "fuel": round(fuel_by_year[int(r["year"])], 4),
            "level": round(
                float(r[price_key])
                - hr_implied * (fuel_by_year[int(r["year"])] - anchor),
                4,
            ),
        }
        for r in rows
    ]
    level = _pooled(levels, "level", "weight")
    raw = [float(r[price_key]) for r in rows]
    adj = [r["level"] for r in levels]
    return {
        "instrument": price_key,
        "hr_implied_mmbtu_per_mwh": round(hr_implied, 4),
        "year_bottom_pooled": {str(y): round(v, 4) for y, v in bot_by_year.items()},
        "level_usd_mwh": round(level, 4),
        "subsets": levels,
        "dispersion_raw_pct": round(100.0 * (max(raw) - min(raw)) / (2 * level), 2),
        "dispersion_anchored_pct": round(
            100.0 * (max(adj) - min(adj)) / (2 * level), 2
        ),
    }


def derive_ercot() -> dict:
    """Return the ERCOT CC committed-block level identification block."""
    from market_sim.config.constants import GAS_OFFER_MARGIN_ANCHOR_BY_ISO

    e136 = json.loads(ERCOT136_CONDUCT.read_text())
    e138 = json.loads(ERCOT138_RANKING.read_text())

    # ANCHOR: the committed gas identification point, reused (never re-derived
    # here — rule 19: one anchor for the whole gas offer surface).
    anchor = float(GAS_OFFER_MARGIN_ANCHOR_BY_ISO["ERCOT"])

    # Model cap-weighted delivered gas on the corpus's OWN matched hours, per
    # year (ERCOT-138 §J — the LP-seam basis, one value per year across the
    # two day families by construction of that capture).
    fuel_by_year: dict[int, float] = {}
    for r in e138["J_physical_vs_markup"]:
        if r["class"] != MEAS_CLASS:
            continue
        fuel_by_year.setdefault(int(r["year"]), float(r["fuel_capwtd"]))

    # LEVEL: the RT SCED TPO curve bottom, anchored.
    bot_rows = [r for r in e136["B1_curve_bottom"] if r["class"] == MEAS_CLASS]
    primary = _level_from_instrument(
        bot_rows, "bot_p50", "res_hours", fuel_by_year, anchor
    )

    # CORROBORATION: the min-load block's own declared cost, same construction.
    mgc_rows = [r for r in e136["C_min_gen_cost"] if r.get("class") == MEAS_CLASS]
    corroboration = _level_from_instrument(
        mgc_rows, "mingen_p50", "n", fuel_by_year, anchor
    )

    # Curve coverage on the identifying rows (the RT-instrument licensing test
    # coal passed — ERCOT-138 §3.4).
    cov = [
        {
            "year": r["year"],
            "family": r["family"],
            "curve_share": round(float(r["curve_share"]), 4),
            "selfsched": round(float(r["b_selfsched"]), 4),
            "residual": round(float(r["e_residual"]), 4),
            "lsl_over_hsl": round(float(r["lsl_over_hsl"]), 4),
        }
        for r in e136["A_ercot123_reproduced"]
        if r.get("class") == MEAS_CLASS
    ]

    return {
        "iso": "ERCOT",
        "measured_class": MEAS_CLASS,
        "anchor_usd_mmbtu": anchor,
        "anchor_source": "constants.GAS_OFFER_MARGIN_ANCHOR_BY_ISO['ERCOT'] "
        "(reused, not re-derived — rule 19)",
        "level_usd_mwh": primary["level_usd_mwh"],
        "primary": primary,
        "corroboration_min_gen_cost": corroboration,
        "corroboration_spread_pct": round(
            100.0
            * abs(corroboration["level_usd_mwh"] - primary["level_usd_mwh"])
            / primary["level_usd_mwh"],
            2,
        ),
        "curve_coverage": cov,
        "model_side_defect": {
            "committed_bid_p50_by_subset": [
                (r["year"], r["family"], r["by_role"]["committed"]["bid_capwtd_p50"])
                for r in e138["C_model"]
                if r["class"] == MEAS_CLASS
            ],
            "note": "the model committed-tranche bid the level REPLACES; its "
            "excess over the measured bottom is the defect ERCOT-138 sized",
        },
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
            "artifacts this identification requires (ercot136/ercot138). "
            "Another ISO derives its own level from its own market's data in "
            "its own lane (rule 25 — never transferred)."
        )
    if args.year is not None:
        raise SystemExit(
            _verify_year_mode(
                args.year, "cc_committed", "CC_COMMITTED_OFFER_LEVEL_BY_ISO"
            )
        )
    out = derive_ercot()
    print(json.dumps(out, indent=2))
    print()
    print(
        f"register in config/constants.py:\n"
        f"  CC_COMMITTED_OFFER_LEVEL_BY_ISO['ERCOT'] = {out['level_usd_mwh']}\n"
        f"anchor reused: GAS_OFFER_MARGIN_ANCHOR_BY_ISO['ERCOT'] = "
        f"{out['anchor_usd_mmbtu']}\n"
        f"corroborating instrument (Min Gen Cost p50): "
        f"{out['corroboration_min_gen_cost']['level_usd_mwh']} $/MWh "
        f"({out['corroboration_spread_pct']}% from the TPO bottom)"
    )


if __name__ == "__main__":
    main()
