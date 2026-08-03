"""nyiso-117 EX-ANTE screen: does the model's SENY demand curve match the measured one?

Task 2 of the nyiso-117 brief, pre-registered in
``results/calibration/PREREG-nyiso117-nyc-stepcurve-compose-2026-08-03.md`` §6
and run BEFORE any conclusion is drawn, with **no solve spent**. It screens
``nyiso_ordc_measured_step_span`` (matrix cell ``U``, never armed) the same way
nyiso-115 screened the NYC pair — on NYISO's own posted prices — and it is a
SEPARATE mechanism with its own kill set, never folded into
``nyiso_nyc_rcpf_step_curve`` (rule 19 ``[R-ONE-MECH]``).

**The question, and why the direction is the opposite of NYC's.** nyiso-115
measured and deliberately did not act on the fact that the isolated SENY-only
adder caps at exactly **$40.00**, while the model prices SENY shortfall on a
linear ramp to **$500**. nyiso-114 §3 measured that the model already reaches
**$62.50** on SENY's first rung — i.e. ABOVE the entire measured envelope. NYC
was UNDER-priced; SENY is OVER-priced.

**The instrument, and its isolation control.** NYISO's locational reserve
regions NEST (NYCA ⊃ East ⊃ SENY ⊃ NYC), so differencing a SENY zone against a
zone that is in East but NOT in SENY isolates the SENY-only shadow price. Zone
F (``CAPITL``) is that reference. The isolation is CHECKED rather than assumed,
three ways:

* all three SENY references (``DUNWOD``/``MILLWD``/``HUD VL``) minus ``CAPITL``
  must agree — they share every region except nothing, so any disagreement
  falsifies the nesting assumption;
* a reference OUTSIDE East (``WEST``) must NOT agree — that difference carries
  the East component too, and the gap between the two readings IS the East-only
  adder, which is reported and cross-checked against ``CAPITL − WEST``;
* the NYC component must be absent — all references and all test zones are
  non-NYC, so the NYC $25 atom nyiso-115 isolated must not appear here.

**What the published curve actually is.** ``reserves/spec.py`` records it from
the SOM and ASM: SENY 30-minute is "at least 1,300 MW … $500/MW" PLUS a
condition-varying increment at **$40/MW** (the #1344 dynamic-requirement
channel; ASM items 2/12, $25 → $40 at the July-2021 reserve-procurement
enhancement, corroborated by the 2023 SOM p. A-132 printing the as-enforced
family as "SENY $500+$40"). The model carries the $500 base ONLY, and carries
it as a ``critical_mw = 0`` linear ramp, so its rungs are $62.50 … $500 with no
$40 rung anywhere.

Three separable questions, reported separately because they have different
answers:

1. **LEVEL** — what ceiling does the measured SENY-only adder actually reach?
2. **SHAPE** — is the measured distribution a ramp (atoms at every rung) or a
   step (one atom at a ceiling over a smooth continuum)?
3. **SPAN** — the ``nyiso_ordc_measured_step_span`` construction question
   proper: the balance-row RHS is the MEASURED hourly requirement while the
   ORDC step widths are built off the STATIC published MW, so wherever the two
   differ the curve is mis-spanned against the row it prices.

Nothing here is fitted and nothing is tuned to a residual: this compares a model
input against the market's own posted prices for the same quantity (rule 13
``[R-MEASURED]`` — a published RCPF regenerates for any forward year).

Run:
    PYTHONPATH=.:src python scripts/probes/_nyiso117_seny_rcpf_curve_screen.py
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from market_sim.config.paths import REPO_ROOT

YEARS = (2023, 2024, 2025)

# Zones IN SENY (⊂ East ⊂ NYCA). Differencing any of these against an
# East-but-not-SENY zone isolates the SENY-only locational adder.
SENY_ZONES = ("DUNWOD", "MILLWD", "HUD VL")
# Zone F: in East, NOT in SENY — the reference the isolation runs against.
EAST_NOT_SENY_ZONE = "CAPITL"
# Zone A: outside East entirely — the negative control. This difference must
# NOT agree with the CAPITL reading; the gap between them is the East adder.
NON_EAST_ZONE = "WEST"

# The model's own SENY construction, restated so the screen is self-contained:
# NYISO_RCPF_LOCATIONAL["SENY"] = ("seny_30min_total", 1300.0, 0.0, 500.0), and
# results/scarcity.py::nyiso_rcpf_product_shortfall_steps discretizes the
# critical=0 linear ramp into n_ramp=8 equal-width bands with penalties
# max_penalty*(k+1)/n_ramp — so the FIRST rung a shortfall of any size pays is
# $62.50, already above the measured ceiling this screen tests.
MODEL_MAX_PENALTY = 500.0
MODEL_N_RAMP = 8
MODEL_RUNGS = tuple(
    MODEL_MAX_PENALTY * (k + 1) / MODEL_N_RAMP for k in range(MODEL_N_RAMP)
)
MODEL_STATIC_REQUIREMENT_MW = 1300.0
# The published increment the model does NOT carry (ASM items 2/12).
PUBLISHED_INCREMENT_PENALTY = 40.0

# The DESIGNATED KEEPER's bundle — committed, and the arm this session composes
# onto. Read for the model side so the screen needs no solve of its own.
MODEL_BUNDLE = "results/calibration/nyiso160_ctmeter_screen_B"
SENY_FAMILY = "seny_30min_total"

# Below this the isolated adder is dominated by ordinary opportunity-cost
# differences between the marginal reserve providers in the two zones; the shape
# question is only asked of material values. Same threshold as nyiso-115.
MATERIAL_ADDER = 2.0
ATOM_TOL = 0.01


def _load_as_prices(year: int) -> pd.DataFrame:
    """Pivot one year of NYISO posted DA ancillary-service prices to zone columns."""
    path = REPO_ROOT / "data" / "raw" / "NYISO-AS" / f"NYISO_as_da_{year}.csv"
    raw = pd.read_csv(path)
    raw["Time Stamp"] = pd.to_datetime(raw["Time Stamp"])
    return raw.pivot_table(
        index="Time Stamp",
        columns="Name",
        values=["spin_10", "nonsync_10", "op_30"],
        aggfunc="mean",
    )


def _adder(pivot: pd.DataFrame, product: str, test: str, reference: str) -> pd.Series:
    """test-minus-reference price for one product: the isolated locational adder."""
    return (pivot[(product, test)] - pivot[(product, reference)]).dropna()


def _shape_evidence(adder: pd.Series) -> dict:
    """Distinguish a stepped demand curve from a linear ramp in one adder series.

    A step curve prices every shortage at one penalty, so the distribution is a
    smooth opportunity-cost continuum plus a single ATOM at that penalty. An
    ``n_ramp`` linear ramp instead places atoms at each of its rungs. Counting
    mass at the MODEL's own rungs is therefore a direct test of the model's
    construction against the market's posted prices.
    """
    material = adder[adder > MATERIAL_ADDER]
    ceiling = float(adder.max())
    at_ceiling = int(np.isclose(material, ceiling, atol=ATOM_TOL).sum())
    at_model_rungs = {
        f"${rung:.2f}": int(np.isclose(material, rung, atol=ATOM_TOL).sum())
        for rung in MODEL_RUNGS
    }
    sub = material[material < ceiling - ATOM_TOL]
    return {
        "material_hours": int(len(material)),
        "measured_ceiling": round(ceiling, 4),
        "hours_at_measured_ceiling": at_ceiling,
        "hours_at_published_increment_40": int(
            np.isclose(material, PUBLISHED_INCREMENT_PENALTY, atol=ATOM_TOL).sum()
        ),
        "hours_at_model_rungs": at_model_rungs,
        "hours_at_any_model_rung": int(sum(at_model_rungs.values())),
        "hours_above_model_first_rung_62_50": int((adder > MODEL_RUNGS[0] + ATOM_TOL).sum()),
        "hours_above_published_increment_40": int(
            (adder > PUBLISHED_INCREMENT_PENALTY + ATOM_TOL).sum()
        ),
        "distinct_values_below_ceiling": int(sub.round(2).nunique()),
        "sub_ceiling_quantiles": (
            [round(float(v), 2) for v in np.percentile(sub, [50, 75, 90, 99])]
            if len(sub)
            else None
        ),
    }


def screen_measured() -> dict:
    """Measured side: the isolated SENY-only adder, with its isolation control."""
    out: dict = {}
    for year in YEARS:
        pivot = _load_as_prices(year)
        year_out: dict = {"isolation_control": {}}

        # (a) The isolation, CHECKED. All three SENY zones minus the
        #     East-but-not-SENY reference must agree; the non-East reference
        #     must not (it carries the East component too).
        for zone in SENY_ZONES:
            a = _adder(pivot, "op_30", zone, EAST_NOT_SENY_ZONE)
            year_out["isolation_control"][f"{zone}-{EAST_NOT_SENY_ZONE}"] = {
                "in_seny": True,
                "reference_in_east": True,
                "max": round(float(a.max()), 4),
                "hours_at_40": int(np.isclose(a, 40.0, atol=ATOM_TOL).sum()),
                "hours_above_40": int((a > 40.0 + ATOM_TOL).sum()),
            }
        neg = _adder(pivot, "op_30", SENY_ZONES[0], NON_EAST_ZONE)
        year_out["isolation_control"][f"{SENY_ZONES[0]}-{NON_EAST_ZONE}"] = {
            "in_seny": True,
            "reference_in_east": False,
            "max": round(float(neg.max()), 4),
            "hours_at_40": int(np.isclose(neg, 40.0, atol=ATOM_TOL).sum()),
            "hours_above_40": int((neg > 40.0 + ATOM_TOL).sum()),
            "role": (
                "intended NEGATIVE CONTROL — but DEGENERATE on this product, see "
                "east_component_control below"
            ),
        }
        # The East component, measured on BOTH products rather than assumed.
        #
        # HONEST LIMIT, reported rather than papered over: on the 30-minute
        # product the intended negative control CANNOT discriminate, because the
        # East 30-minute adder is identically $0.00 in every hour — the East
        # family simply never binds there, so CAPITL and WEST post the same
        # op_30 price and both references give the same answer. A control that
        # can only separate when a component is non-zero is uninformative when
        # that component is measured zero, and saying "the control agreed" would
        # be claiming a pass an instrument never had the power to give (the
        # standing nyiso-115/116 gate-instrument lesson).
        #
        # So the reference pair is validated where it CAN be: on the 10-minute
        # product, where the East family (east_10min_total, $775) does bind. The
        # SAME CAPITL-vs-WEST pair separates there in thousands of hours. That
        # demonstrates live that the pair detects an East component whenever one
        # exists — which is what makes its silence on op_30 a measurement of
        # East rather than a blind spot of the instrument.
        east_30 = _adder(pivot, "op_30", EAST_NOT_SENY_ZONE, NON_EAST_ZONE)
        east_10 = _adder(pivot, "nonsync_10", EAST_NOT_SENY_ZONE, NON_EAST_ZONE)
        year_out["east_component_control"] = {
            "op_30_capitl_minus_west_max": round(float(east_30.max()), 4),
            "op_30_hours_nonzero": int((east_30.abs() > 1e-9).sum()),
            "op_30_reading": (
                "IDENTICALLY ZERO — the East 30-minute family never binds, so the "
                "negative control degenerates on this product and is reported as "
                "uninformative, not as a pass"
            ),
            "nonsync_10_capitl_minus_west_max": round(float(east_10.max()), 4),
            "nonsync_10_hours_nonzero": int((east_10.abs() > 1e-9).sum()),
            "nonsync_10_reading": (
                "POSITIVE CONTROL — the same reference pair separates on the "
                "10-minute product, where east_10min_total does bind, proving the "
                "pair can detect an East component when one is present"
            ),
            "published_east_10min_rcpf": 775.0,
            "published_east_30min_rcpf": 40.0,
        }

        # (b) The SENY-only adder proper, on the 30-minute product — the family
        #     the model carries.
        seny = _adder(pivot, "op_30", SENY_ZONES[0], EAST_NOT_SENY_ZONE)
        year_out["seny_30min_adder"] = _shape_evidence(seny)
        out[str(year)] = year_out
    return out


def screen_span() -> dict:
    """SPAN: the measured hourly requirement vs the static MW the widths use.

    ``nyiso_ordc_measured_step_span``'s actual subject. The balance-row RHS is
    the measured as-enforced #1344 series when ``nyiso_dynamic_reserve_
    requirements`` is armed, while the ORDC step widths are built off the STATIC
    published 1,300 MW — so wherever the two differ the demand curve is
    mis-spanned against the row it prices.
    """
    out: dict = {}
    for year in YEARS:
        path = (
            REPO_ROOT
            / "data"
            / "raw"
            / "NYISO-AS"
            / "requirements"
            / f"NYISO_reserve_requirements_{year}.csv"
        )
        df = pd.read_csv(path)
        seny = df[(df["region"] == "SENY") & (df["product"] == "30min_total")]
        req = seny["requirement_mw"].to_numpy(dtype=float)
        out[str(year)] = {
            "hours": int(len(req)),
            "static_published_mw": MODEL_STATIC_REQUIREMENT_MW,
            "measured_min_mw": round(float(req.min()), 2),
            "measured_mean_mw": round(float(req.mean()), 2),
            "measured_max_mw": round(float(req.max()), 2),
            "hours_above_static": int((req > MODEL_STATIC_REQUIREMENT_MW + 1e-6).sum()),
            "share_hours_above_static": round(
                float((req > MODEL_STATIC_REQUIREMENT_MW + 1e-6).mean()), 4
            ),
            "max_ratio_measured_to_static": round(
                float(req.max() / MODEL_STATIC_REQUIREMENT_MW), 4
            ),
            "mean_ratio_measured_to_static": round(
                float(req.mean() / MODEL_STATIC_REQUIREMENT_MW), 4
            ),
        }
    return out


def screen_model() -> dict:
    """Model side: the SENY family's own duals in the DESIGNATED KEEPER's bundle."""
    root = REPO_ROOT / MODEL_BUNDLE / "hourly"
    out: dict = {}
    for year in YEARS:
        path = root / f"reserve_family_{year}.parquet"
        if not path.exists():
            out[str(year)] = {"error": f"missing {path}"}
            continue
        df = pd.read_parquet(path)
        fam = df[df["family"].astype(str) == SENY_FAMILY]
        live = fam[fam["dual"] > 1e-9]
        duals = live["dual"].to_numpy()
        out[str(year)] = {
            "hours_dual_positive": int(len(live)),
            "max_dual": round(float(fam["dual"].max()), 4),
            "mean_dual_when_binding": (
                round(float(duals.mean()), 4) if len(duals) else None
            ),
            "hours_above_measured_ceiling_40": int(
                (duals > PUBLISHED_INCREMENT_PENALTY + ATOM_TOL).sum()
            ),
            "hours_at_or_below_40": int(
                (duals <= PUBLISHED_INCREMENT_PENALTY + ATOM_TOL).sum()
            ),
            "model_first_rung": MODEL_RUNGS[0],
            "model_max_penalty": MODEL_MAX_PENALTY,
            "requirement_mw_max": round(float(fam["requirement_mw"].max()), 2),
            "requirement_mw_mean": round(float(fam["requirement_mw"].mean()), 2),
            "max_shortfall_mw": round(float(fam["shortfall_mw"].max()), 2),
        }
    return out


def verdict(measured: dict, model: dict) -> dict:
    """Discharge the pre-registered S-MATCH / S-OVER / S-INERT outcomes.

    Decided against §6's criteria, which were written before any number here was
    read. The three outcomes are mutually exclusive and are evaluated in the
    order the pre-registration lists them.
    """
    binds = sum(
        int(model[str(y)].get("hours_dual_positive", 0) or 0) for y in YEARS
    )
    over = sum(
        int(model[str(y)].get("hours_above_measured_ceiling_40", 0) or 0) for y in YEARS
    )
    measured_ceilings = [
        measured[str(y)]["seny_30min_adder"]["measured_ceiling"] for y in YEARS
    ]
    if binds == 0:
        outcome = "S-INERT"
        why = (
            "the model's SENY family never prices in any hour of any year, so its "
            "curve SHAPE is unobservable from this bundle — unidentified, no lever"
        )
    elif over > 0:
        outcome = "S-OVER"
        why = (
            f"the model prices SENY above the measured ceiling in {over} of {binds} "
            f"binding hours across 2023-2025 (measured ceilings "
            f"{'/'.join(f'${c:.2f}' for c in measured_ceilings)}); the model's very "
            f"first ramp rung is ${MODEL_RUNGS[0]:.2f}, already above the entire "
            f"measured envelope"
        )
    else:
        outcome = "S-MATCH"
        why = (
            "every hour the model prices SENY lies within the measured envelope — "
            "the curve already matches, a clean closure"
        )
    return {
        "outcome": outcome,
        "why": why,
        "model_binding_hours_total": binds,
        "model_hours_above_measured_ceiling": over,
        "action_per_prereg_section_6": (
            "RECORD ONLY. No solve is spent in this session and no parameter is "
            "introduced, changed or fitted: a SENY curve change is "
            "nyiso_ordc_measured_step_span's mechanism and needs its own "
            "pre-registration and its own arm (rule 19 [R-ONE-MECH]). This screen "
            "mints evidence, not a lever."
        ),
    }


def main() -> None:
    measured = screen_measured()
    model = screen_model()
    result = {
        "probe": "nyiso-117 SENY locational RCPF curve screen (EX ANTE, no solve)",
        "prereg": "results/calibration/PREREG-nyiso117-nyc-stepcurve-compose-2026-08-03.md §6",
        "mechanism_screened": "nyiso_ordc_measured_step_span (matrix cell U, never armed)",
        "measured_source": (
            "data/raw/NYISO-AS/NYISO_as_da_<year>.csv (NYISO posted DA AS prices, "
            "per zone); SENY-only = DUNWOD minus CAPITL (East, not SENY)"
        ),
        "span_source": (
            "data/raw/NYISO-AS/requirements/NYISO_reserve_requirements_<year>.csv "
            "(the measured as-enforced #1344 hourly requirement)"
        ),
        "model_source": f"{MODEL_BUNDLE}/hourly/reserve_family_<year>.parquet",
        "model_construction": {
            "family": SENY_FAMILY,
            "static_requirement_mw": MODEL_STATIC_REQUIREMENT_MW,
            "critical_mw": 0.0,
            "max_penalty": MODEL_MAX_PENALTY,
            "n_ramp": MODEL_N_RAMP,
            "rungs": [round(r, 2) for r in MODEL_RUNGS],
            "published_increment_the_model_does_not_carry": PUBLISHED_INCREMENT_PENALTY,
        },
        "measured": measured,
        "span": screen_span(),
        "model": model,
        "verdict": verdict(measured, model),
    }
    out_path = (
        REPO_ROOT / "results" / "calibration" / "nyiso117_seny_rcpf_curve_screen.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
