"""Derive the coal `_peak`-tranche offer LEVEL + gas slope for an ISO (ERCOT-140).

The identification constants of the ``coal_peak_offer_margin`` mechanism
(``constants.COAL_PEAK_OFFER_LEVEL_BY_ISO`` /
``COAL_PEAK_OFFER_GAS_HR_BY_ISO``) — the coal offer-curve UPPER-TAIL
successor ERCOT-123 §7.2 chartered, executed as the ERCOT-140 lane
(``docs/PRECOMMIT-ercot140-coal-peak-offer-2026-07-30.md``).

ERCOT-138 §5.6 measured the defect this level repairs: at p90 the model's
COAL curve runs **$9.6–15.5/MWh UNDER** its own fleet's measured SCED TPO
conduct in all four 2024–2025 disclosure subsets — the model's coal stack is
fully offered by $32–34 while the real fleet's top decile is priced $35–48
and its last MW needs $500 (ERCOT-123 §5). The p90 finding is OPPOSITE in
sign to the ERCOT-138/139 crossing-band finding, which is why no single
level lever serves both and this lane prices only the top tranche.

Two registered constants plus a reused anchor, all read from COMMITTED
measured artifacts — nothing is re-run, nothing touches a residual:

* **ANCHOR ($/MMBtu)** — NOT derived here. The shared
  ``GAS_OFFER_MARGIN_ANCHOR_BY_ISO`` entry (ERCOT 2.2494): one gas
  identification point for the whole offer surface, never a second anchor
  that could drift against the first (rule 19 ``[R-ONE-MECH]``).

* **GAS_HR (MMBtu/MWh)** — the corpus's own measured GAS response of the
  coal top: ``(p90_2025 − p90_2024) / (gas_2025 − gas_2024)`` on the
  res-hours-pooled per-year p90s. The slope basis is GAS, not coal, because
  the measured top ROSE $34.82 → $45.43 while delivered coal FELL
  ($1.748 → $1.630 — a coal-fuel form has slope −89.9, wrong sign,
  physically absurd). Its falsifier: the gas slope lands within ~5 % of the
  coal fleet's own measured cap-weighted offer heat rate (10.905, ERCOT-138
  §J) — gas-parity opportunity pricing of the marginal coal MW.

* **LEVEL ($/MWh)** — the real coal fleet's top-decile boundary price
  (60-Day SCED ``Submitted TPO-Price1`` capacity-weighted p90 of
  above-min-load capability, ERCOT-138 ``E_bid_detail`` COAL rows) expressed
  AT the anchor by removing the corpus's own measured gas response::

      level_i = p90_i - GAS_HR x (gas_i - anchor)
      LEVEL   = res-hours-weighted mean of level_i over the four subsets

The identification-quality statistic prints with the result: cross-subset
dispersion falls ±18.74 % raw → ±7.12 % anchored (the form earns its keep
only if it shrinks), and the refuted coal-fuel slope is printed beside it.

Known limits (precommit §2.1/§2.2, declared there ex ante): the p90 is the
top-decile *boundary* applied to a tranche spanning the top ~6.9 % of
above-mustrun capability (an understatement, direction-safe), and the
ERCOT-138 §H same-plants 2025 p90 runs OPPOSITE the fleet-wide 2025 rise
(compositional-risk falsifier pre-registered as the per-year gates).

Rule-23 frozen derive: re-run ONLY when a source artifact is regenerated
from new disclosure data, and cite that data change in the re-derivation
commit. NEVER because a residual moved.

It is a REPORTING / derivation tool only — default-off in every solve path.
The model artifacts it informs are the hand-set
``COAL_PEAK_OFFER_LEVEL_BY_ISO`` / ``COAL_PEAK_OFFER_GAS_HR_BY_ISO`` entries
in ``config/constants.py`` (cited back to this script), consumed by the
harness only under ``--coal-peak-offer-margin``.

Usage::

    python scripts/data/derive_coal_peak_offer_margin.py --iso ERCOT
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

# Committed measured artifacts (the ONLY inputs — rule 23):
ERCOT138_RANKING = REPO / "results/calibration/ercot138_coal_gas_ranking.json"

#: The measured class whose conduct identifies the constants. ERCOT-138's
#: measured COAL side is the full CLLIG fleet at ~100 % RT curve coverage
#: (ERCOT-123 §2: 99.4–100.0 % of RT-dispatchable headroom offered) — the
#: population the model's 10-plant CAMPD coal fleet represents.
MEAS_CLASS = "COAL"

#: The identifying quantile: the top-decile boundary of above-min-load
#: capability — the committed statistic closest to the `_peak` tranche's
#: span (top ~6.9 % of above-mustrun capability; precommit §2.1).
MEAS_Q = "p90"


def _pooled(rows: list[dict], value_key: str, weight_key: str) -> float:
    """Return the ``weight_key``-weighted mean of ``value_key`` over ``rows``."""
    tot = sum(float(r[weight_key]) for r in rows)
    return sum(float(r[weight_key]) * float(r[value_key]) for r in rows) / tot


def derive_ercot() -> dict:
    """Return the ERCOT coal `_peak`-tranche identification block."""
    from market_sim.config.constants import GAS_OFFER_MARGIN_ANCHOR_BY_ISO

    e138 = json.loads(ERCOT138_RANKING.read_text())

    # ANCHOR: the committed shared gas identification point, reused (rule 19).
    anchor = float(GAS_OFFER_MARGIN_ANCHOR_BY_ISO["ERCOT"])

    # Delivered fuel per year on the corpus's own matched hours (ERCOT-138 §J
    # — the LP-seam basis): GAS from the CC rows (the slope basis), COAL from
    # the COAL rows (printed only to refute the coal-fuel form).
    gas_by_year: dict[int, float] = {}
    coal_by_year: dict[int, float] = {}
    for r in e138["J_physical_vs_markup"]:
        y = int(r["year"])
        if r["class"] == "CC":
            gas_by_year.setdefault(y, float(r["fuel_capwtd"]))
        elif r["class"] == MEAS_CLASS:
            coal_by_year.setdefault(y, float(r["fuel_capwtd"]))

    # The measured top-decile boundary per subset (E_bid_detail COAL p90),
    # weighted by the same corpus's COAL resource-hours (B_measured).
    weights = {
        (int(r["year"]), r["family"]): float(r["res_hours"])
        for r in e138["B_measured"]
        if r["class"] == MEAS_CLASS
    }
    rows = [
        {
            "year": int(r["year"]),
            "family": r["family"],
            "res_hours": weights[(int(r["year"]), r["family"])],
            "p90": float(r["measured"]),
            "model_p90": float(r["model_all"]),
        }
        for r in e138["E_bid_detail"]
        if r["class"] == MEAS_CLASS and r["q"] == MEAS_Q
    ]
    years = sorted({r["year"] for r in rows})
    if len(years) != 2:
        raise SystemExit(
            f"identification needs exactly two fuel-distinct years to measure "
            f"the corpus's own gas response; got {years} (rule 13 — a one-year "
            "corpus would make the slope a fitted parameter)."
        )
    y_lo, y_hi = years
    p90_by_year = {
        y: _pooled([r for r in rows if r["year"] == y], "p90", "res_hours")
        for y in years
    }
    d_gas = gas_by_year[y_hi] - gas_by_year[y_lo]
    gas_hr = (p90_by_year[y_hi] - p90_by_year[y_lo]) / d_gas
    # The refuted alternative, printed for the record (precommit §0.1).
    d_coal = coal_by_year[y_hi] - coal_by_year[y_lo]
    coal_hr_refuted = (p90_by_year[y_hi] - p90_by_year[y_lo]) / d_coal

    levels = [
        {
            **r,
            "gas": round(gas_by_year[r["year"]], 4),
            "level": round(r["p90"] - gas_hr * (gas_by_year[r["year"]] - anchor), 4),
        }
        for r in rows
    ]
    level = _pooled(levels, "level", "res_hours")
    raw = [r["p90"] for r in rows]
    adj = [r["level"] for r in levels]

    return {
        "iso": "ERCOT",
        "measured_class": MEAS_CLASS,
        "quantile": MEAS_Q,
        "anchor_usd_mmbtu": anchor,
        "anchor_source": "constants.GAS_OFFER_MARGIN_ANCHOR_BY_ISO['ERCOT'] "
        "(reused, not re-derived — rule 19)",
        "gas_hr_mmbtu_per_mwh": round(gas_hr, 4),
        "gas_hr_falsifier": {
            "measured_coal_offer_hr_capwtd": 10.905,
            "note": "ERCOT-138 §J offer_hr_capwtd COAL — the gas slope lands "
            "within ~5 % of the fleet's own offer heat rate (gas-parity "
            "opportunity pricing); a non-fuel-responsive top would not do this",
        },
        "coal_fuel_form_refuted": {
            "implied_slope_mmbtu_per_mwh": round(coal_hr_refuted, 2),
            "coal_fuel_by_year": {str(y): coal_by_year[y] for y in years},
            "note": "delivered coal FELL while the measured top ROSE — wrong "
            "sign, physically absurd; the existing multiplier x coal-fuel "
            "composition is this form and is what leaves the top short",
        },
        "level_usd_mwh": round(level, 4),
        "year_p90_pooled": {str(y): round(v, 4) for y, v in p90_by_year.items()},
        "subsets": levels,
        "dispersion_raw_pct": round(100.0 * (max(raw) - min(raw)) / (2 * level), 2),
        "dispersion_anchored_pct": round(
            100.0 * (max(adj) - min(adj)) / (2 * level), 2
        ),
        "model_side_defect": {
            "model_p90_by_subset": [
                (r["year"], r["family"], r["model_p90"]) for r in rows
            ],
            "note": "the model coal top the level repairs; its deficit vs "
            "measured is the ERCOT-138 §5.6 finding this lane executes",
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
            "artifact this identification requires (ercot138). Another ISO "
            "derives its own constants from its own market's data in its own "
            "lane (rule 25 — never transferred)."
        )
    if args.year is not None:
        raise SystemExit(
            _verify_year_mode(args.year, "coal_peak", "COAL_PEAK_OFFER_LEVEL_BY_ISO")
        )
    out = derive_ercot()
    print(json.dumps(out, indent=2))
    print()
    print(
        f"register in config/constants.py:\n"
        f"  COAL_PEAK_OFFER_LEVEL_BY_ISO['ERCOT'] = {out['level_usd_mwh']}\n"
        f"  COAL_PEAK_OFFER_GAS_HR_BY_ISO['ERCOT'] = "
        f"{out['gas_hr_mmbtu_per_mwh']}\n"
        f"anchor reused: GAS_OFFER_MARGIN_ANCHOR_BY_ISO['ERCOT'] = "
        f"{out['anchor_usd_mmbtu']}"
    )


if __name__ == "__main__":
    main()
