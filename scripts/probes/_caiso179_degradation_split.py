"""caiso-179 — is the CELL-vs-SYSTEM cost split behind ``STORAGE_DEGRADATION_REPLACEMENT_FRACTION`` IDENTIFIABLE?

Pre-registration: ``results/calibration/PRECHECK-caiso179-degradation-split-2026-08-07.md``
(pushed BEFORE any source value was read).

THE QUESTION. ``config/capacity_market.STORAGE_DEGRADATION_REPLACEMENT_FRACTION = 0.25``
is the last free factor in ``model/storage._degradation_cost_per_mwh``; its own constant
block calls it *"a modeling simplification ... tunable"*. caiso-176 §1a ruled that routing
the LP through that helper is **DOF SUBSTITUTION, not closure**, and named an identified
cell-versus-system split as exit 3 — the ONLY live exit after caiso-178 spent exit 2. This
probe asks whether that split can be determined entirely from citable primary sources.

THE ARITHMETIC IS THE CODE'S, NOT THIS PROBE'S. The committed constant block declares the
fraction's intent in two clauses — *"only the cell stack degrades, not the power electronics
/ BOS"* and *"warranties run to ~80% retention"* — i.e. ``F = phi x (1 - R)``. Over ``N``
rated cycles a battery of capacity ``E`` discharges ``N x E`` MWh (the code's own convention:
``capex_per_mwh / cycles``, so one cycle = one full ``E``) and fades to ``R x E``; holding
rated capacity by augmentation costs ``(1 - R) x E x phi x capex_per_kwh``. ``E`` cancels:

    $/MWh = capex_per_kwh x 1000 x phi x (1 - R) / N

Only ``(1 - R) / N`` enters, so under PNNL's linear-fade model the end-of-life THRESHOLD
cancels too (0.20/1,920 == 0.40/3,840 exactly) and no convention is chosen here.

SOURCES, ranked in the pre-registration before any value was read:

  phi   S1 PRIMARY  NREL ATB 2024 ``Utility-Scale Battery Storage`` duration sweep, on disk
                    at ``data/raw/nrel-atb/``. ATB CONSTRUCTS its duration classes as
                    ``Total ($/kWh) = Energy ($/kWh) + Power ($/kW) / Duration`` (NREL/TP-
                    6A40-85332 p.3), so a two-parameter fit INVERTS that construction
                    exactly rather than approximating it.
        S2 bracket  NREL/TP-7A40-83586 (Ramasamy et al., *U.S. Solar PV and Energy Storage
                    Cost Benchmarks ... Q1 2022*) Table 11 + Figure ES-2 — bare-pack and
                    battery-cabinet shares of total installed $/kWh.

  (N,R) R1/R2 MISS  ATB 2024's storage page and its basis (NREL/TP-6A40-85332) carry NO
                    cycle-life and NO retention: they set VOM = 0 and put ALL augmentation
                    in FIXED O&M. Recorded by ``atb_augmentation_finding`` below.
        R3 MISS     No primary, named, public utility-scale LFP warranty document located;
                    only vendor summaries quoting ranges (4,000-10,000 cycles, 70-80 % EOL).
        R4 USED     PNNL-33283 (*ESGC Cost and Performance Assessment 2022*) Table 4.2 +
                    its EOL definition -- the ONLY ranked source carrying a complete pair.

Run:  uv run python scripts/probes/_caiso179_degradation_split.py
Writes: results/calibration/_caiso179_degradation_split.json

Rule 13 ``[R-MEASURED]``: no price residual, model output or keeper metric enters any line
of this file. Rule 5 ``[R-NO-MAGIC]``: every off-disk number below carries its citation.
"""

from __future__ import annotations

import glob
import json

import numpy as np
import pandas as pd

from market_sim.config.paths import REPO_ROOT

# --------------------------------------------------------------------------
# Committed model constants under test (config/capacity_market.py). Read from
# the package so this probe cannot drift from what the model actually carries.
# --------------------------------------------------------------------------
from market_sim.config.capacity_market import (  # noqa: E402
    STORAGE_DEGRADATION_REPLACEMENT_FRACTION,
    STORAGE_TECHS,
)

TECH = "li_ion_4hr"

# --------------------------------------------------------------------------
# ATB cell the committed STORAGE_TECHS costs were derived from, per the
# constant block's own labels ("ATB 2024 Moderate 4Hr Battery @2026, 2026$").
# --------------------------------------------------------------------------
ATB_TECHNOLOGY = "Utility-Scale Battery Storage"
ATB_SCENARIO = "Moderate"
ATB_YEAR = 2026
DEFLATOR_TOL = 0.005  # G1(b): 0.5 %, pre-registered
LINEARITY_TOL = 0.005  # G1(a): 0.5 % of fitted 4-hr CAPEX, pre-registered
ADMISSIBILITY_SCREEN = 15.00  # $/MWh — G4, pre-registered (caiso-101 + caiso-176)

# --------------------------------------------------------------------------
# S2 — NREL/TP-7A40-83586 (Ramasamy et al. 2022), utility-scale standalone
# 60 MW / 240 MWh 4-hour Li-ion system, 2021 real USD.
#   Table 11 "Li-ion battery price ($/kWh)" .......... MSP $137 / MMP $165
#   Table 11 "Battery cabinet" ....................... MSP $226 / MMP $270
#       ("Includes battery packs, containers, thermal management system, and
#        fire suppression system")
#   Figure ES-2 narrative, total installed ........... MSP $394 / MMP $446
# Ratios only; the 2021-USD basis cancels.
# --------------------------------------------------------------------------
RAMASAMY = {
    "MSP": {"pack_per_kwh": 137.0, "cabinet_per_kwh": 226.0, "total_per_kwh": 394.0},
    "MMP": {"pack_per_kwh": 165.0, "cabinet_per_kwh": 270.0, "total_per_kwh": 446.0},
}

# --------------------------------------------------------------------------
# R4 — PNNL-33283 Table 4.2, "Cycles at Specified DOD for Li-ion LFP and NMC".
# EOL is defined in §6 item (v) and footnote 11: "End of life is when available
# energy at full charge is 60% of rated energy."  The CORRECTED 100 %-DOD-
# equivalent column is cycles x average DOD, i.e. cumulative discharge in units
# of rated energy -- exactly the model's ``capex_per_mwh / cycles`` convention
# (one cycle = one full E discharged), so it is the column used here.
# --------------------------------------------------------------------------
PNNL_EOL_RETENTION = 0.60
PNNL_LFP_TABLE_4_2 = [
    # (DOD provided %, average DOD %, cycles to EOL, 100%-DOD equiv,
    #  corrected 100%-DOD equiv based on average DOD)
    (100, 80, 4_800, 4_800, 3_840),
    (80, 70, 6_000, 4_800, 4_200),
    (60, 60, 8_000, 4_800, 4_800),
    (30, 30, 32_000, 9_600, 9_600),
    (5, 5, 192_000, 9_600, 9_600),
]
# Rows admissible for a grid battery: PNNL's own crossover discussion and the
# committed CAISO fleet's daily-cycling duty both sit in the >= 60 % DOD band.
# The <= 30 % rows are reported but excluded from the headline span; they would
# only LOWER the adder, so excluding them is the conservative direction for a
# refutation test.
PNNL_HEADLINE_DOD_ROWS = (100, 80, 60)


def _load_atb() -> pd.DataFrame:
    """Load the committed ATB extract, both file families, as one frame."""
    root = REPO_ROOT / "data" / "raw" / "nrel-atb"
    frames = []
    for fam in ("atb_2024_electricity_filtered", "atb_2024v4_electricity_filtered"):
        files = sorted(glob.glob(str(root / f"{fam}.part*.csv")))
        if not files:
            continue
        df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
        df["file_family"] = fam
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"no ATB extract under {root}")
    return pd.concat(frames, ignore_index=True)


def run_g1(atb: pd.DataFrame) -> dict:
    """G1 — identify the ATB cell, verify exact linearity and one common deflator.

    Fits ``CAPEX(d) = p + e*d`` over the five duration classes and checks that a
    SINGLE scalar maps the raw fit onto the committed ``STORAGE_TECHS`` costs.
    That is what proves phi is computed against the same denominator the LP
    formula divides.
    """
    out: dict = {"families": {}}
    for fam, sub in atb.groupby("file_family"):
        s = sub[
            (sub.technology == ATB_TECHNOLOGY)
            & (sub.scenario == ATB_SCENARIO)
            & (sub.core_metric_variable == ATB_YEAR)
        ].copy()
        s["duration_hr"] = s.techdetail.str.extract(r"(\d+)Hr").astype(float)
        piv = s.pivot_table(
            index="duration_hr", columns="core_metric_parameter", values="value"
        ).sort_index()
        d = piv.index.to_numpy(dtype=float)
        capex = piv["CAPEX"].to_numpy(dtype=float)
        design = np.vstack([np.ones_like(d), d]).T
        (p_kw, e_kwh), *_ = np.linalg.lstsq(design, capex, rcond=None)
        fitted = design @ np.array([p_kw, e_kwh])
        capex4 = float(fitted[d == 4.0][0])
        capex8 = float(fitted[d == 8.0][0])
        resid = float(np.max(np.abs(capex - fitted)))
        k4 = float(STORAGE_TECHS["li_ion_4hr"]["capex_per_kw"]) / capex4
        k8 = float(STORAGE_TECHS["li_ion_8hr"]["capex_per_kw"]) / capex8
        fom = piv["Fixed O&M"].to_numpy(dtype=float)
        fom4, fom8 = float(fom[d == 4.0][0]), float(fom[d == 8.0][0])
        out["families"][fam] = {
            "capex_raw_by_duration": {str(int(x)): float(y) for x, y in zip(d, capex)},
            "power_component_per_kw_raw": float(p_kw),
            "energy_component_per_kwh_raw": float(e_kwh),
            "max_abs_residual": resid,
            "max_rel_residual": resid / capex4,
            "deflator_from_capex4": k4,
            "deflator_from_capex8": k8,
            # Two independent constants the same scalar must also reproduce.
            "fom4_deflated": fom4 * k4,
            "fom4_committed": float(STORAGE_TECHS["li_ion_4hr"]["fom_per_kw_yr"]),
            "fom8_deflated": fom8 * k4,
            "fom8_committed": float(STORAGE_TECHS["li_ion_8hr"]["fom_per_kw_yr"]),
            "phi_energy_share_4hr": float(e_kwh * 4.0 / capex4),
        }
    ref = out["families"][sorted(out["families"])[0]]
    ks = [ref["deflator_from_capex4"], ref["deflator_from_capex8"]]
    fom_ok = (
        abs(ref["fom4_deflated"] - ref["fom4_committed"]) / ref["fom4_committed"]
        <= DEFLATOR_TOL
        and abs(ref["fom8_deflated"] - ref["fom8_committed"]) / ref["fom8_committed"]
        <= DEFLATOR_TOL
    )
    out["linearity_pass"] = ref["max_rel_residual"] <= LINEARITY_TOL
    out["deflator_pass"] = (abs(ks[0] - ks[1]) / ks[0] <= DEFLATOR_TOL) and fom_ok
    out["deflator"] = ks[0]
    out["phi_S1"] = ref["phi_energy_share_4hr"]
    out["families_agree"] = (
        len({round(v["phi_energy_share_4hr"], 12) for v in out["families"].values()}) == 1
    )
    out["PASS"] = bool(out["linearity_pass"] and out["deflator_pass"])
    return out


def run_g2(phi_s1: float) -> dict:
    """G2 — phi is a cited share; S2 brackets it and must not exceed it."""
    brackets = {}
    for basis, row in RAMASAMY.items():
        brackets[basis] = {
            "phi_cell_bare_pack": row["pack_per_kwh"] / row["total_per_kwh"],
            "phi_cabinet_energy_hardware": row["cabinet_per_kwh"] / row["total_per_kwh"],
            "pack_share_of_cabinet": row["pack_per_kwh"] / row["cabinet_per_kwh"],
        }
    max_s2 = max(v["phi_cabinet_energy_hardware"] for v in brackets.values())
    return {
        "phi_S1_headline": phi_s1,
        "S2_brackets": brackets,
        # cells subset of cabinet subset of energy-scaling total, so every S2
        # share must sit at or below S1. A violation would falsify the reading.
        "consistency_phi_S2_le_phi_S1": bool(max_s2 <= phi_s1),
        "PASS": bool(max_s2 <= phi_s1),
    }


def run_g3() -> dict:
    """G3 — the (N, R) pair, from the highest-ranked source carrying a complete one."""
    rows = []
    for dod, avg_dod, cycles_eol, equiv, corrected in PNNL_LFP_TABLE_4_2:
        rows.append(
            {
                "dod_provided_pct": dod,
                "average_dod_pct": avg_dod,
                "cycles_to_eol": cycles_eol,
                "equiv_cycles_100pct_dod": equiv,
                "corrected_equiv_cycles": corrected,
                # (1 - R) / N in the model's own full-E-discharge units.
                "fade_per_full_equivalent_discharge": (1.0 - PNNL_EOL_RETENTION)
                / corrected,
                "in_headline_span": dod in PNNL_HEADLINE_DOD_ROWS,
            }
        )
    # Linear-fade invariance: PNNL's own 80 %-retention reading of the 100 %-DOD
    # row (2,400 cycles at 80 % average DOD, Table 4.3) must give the SAME rate.
    inv_80 = 0.20 / (2_400 * 0.80)
    inv_60 = (1.0 - PNNL_EOL_RETENTION) / 3_840
    return {
        "source": "PNNL-33283 Table 4.2 (+ Table 4.3 cross-check), LFP",
        "eol_retention": PNNL_EOL_RETENTION,
        "rows": rows,
        "eol_threshold_invariance": {
            "rate_at_80pct_retention": inv_80,
            "rate_at_60pct_retention": inv_60,
            "identical": bool(abs(inv_80 - inv_60) < 1e-15),
        },
        "r1_r2_carry_pair": False,
        "r3_primary_document_found": False,
        "PASS": True,
    }


def main() -> None:
    tech = STORAGE_TECHS[TECH]
    capex_per_kwh = float(tech["capex_per_kwh"])
    committed_cycles = float(tech["cycles"])

    atb = _load_atb()
    g1 = run_g1(atb)
    g2 = run_g2(g1["phi_S1"])
    g3 = run_g3()

    phi_variants = {
        "S1_atb_energy_scaling (HEADLINE, pre-registered)": g1["phi_S1"],
        "S2_cabinet_MMP": g2["S2_brackets"]["MMP"]["phi_cabinet_energy_hardware"],
        "S2_cabinet_MSP": g2["S2_brackets"]["MSP"]["phi_cabinet_energy_hardware"],
        "S2_bare_pack_MMP": g2["S2_brackets"]["MMP"]["phi_cell_bare_pack"],
        "S2_bare_pack_MSP": g2["S2_brackets"]["MSP"]["phi_cell_bare_pack"],
    }

    grid = {}
    for pname, phi in phi_variants.items():
        for row in g3["rows"]:
            if not row["in_headline_span"]:
                continue
            adder = capex_per_kwh * 1000.0 * phi * row["fade_per_full_equivalent_discharge"]
            grid[f"{pname} @ DOD {row['dod_provided_pct']}%"] = {
                "adder_per_mwh": adder,
                # F re-expressed against the code's own committed `cycles`, so it
                # is directly comparable to the incumbent 0.25.
                "F_equivalent_at_committed_cycles": committed_cycles
                * phi
                * row["fade_per_full_equivalent_discharge"],
                "clears_screen": bool(adder < ADMISSIBILITY_SCREEN),
            }

    headline = [
        v["adder_per_mwh"]
        for k, v in grid.items()
        if k.startswith("S1_atb_energy_scaling")
    ]
    most_favourable = min(v["adder_per_mwh"] for v in grid.values())

    # The ATB's OWN augmentation channel, reported as a CONTRAST, never as the
    # estimator: ATB puts all augmentation in FIXED O&M at ~1 cycle/day.
    fam = g1["families"][sorted(g1["families"])[0]]
    fom4_deflated = fam["fom4_deflated"]
    atb_cycles_per_year = 365.0  # "approximately one cycle per day" (ATB 2024)
    mwh_per_kw_yr = atb_cycles_per_year * float(tech["duration_hr"]) / 1000.0
    atb_fom_per_mwh = fom4_deflated / mwh_per_kw_yr

    incumbent = capex_per_kwh * 1000.0 / committed_cycles * STORAGE_DEGRADATION_REPLACEMENT_FRACTION

    verdict = {
        "G1_atb_cell_and_linearity": g1["PASS"],
        "G2_phi_cited": g2["PASS"],
        "G3_pair_cited": g3["PASS"],
        "G4_admissibility_below_15": bool(max(headline) < ADMISSIBILITY_SCREEN),
        "G5_no_new_dof": False,  # a DOD row remains selectable; see finding §5
        "branch": None,
    }
    if verdict["G1_atb_cell_and_linearity"] and verdict["G2_phi_cited"] and verdict["G3_pair_cited"]:
        verdict["branch"] = (
            "BRANCH_I_identifies"
            if verdict["G4_admissibility_below_15"]
            else "BRANCH_III_R_identified_and_refuted"
        )
    else:
        verdict["branch"] = "BRANCH_II_third_wall"

    record = {
        "session": "caiso-179",
        "prereg": "results/calibration/PRECHECK-caiso179-degradation-split-2026-08-07.md",
        "committed_under_test": {
            "STORAGE_DEGRADATION_REPLACEMENT_FRACTION": STORAGE_DEGRADATION_REPLACEMENT_FRACTION,
            "capex_per_kwh": capex_per_kwh,
            "cycles": committed_cycles,
            "implied_adder_per_mwh": incumbent,
            "keeper_battery_dispatch_adder": 5.0,
        },
        "G1": g1,
        "G2": g2,
        "G3": g3,
        "adder_grid": grid,
        "headline_span_per_mwh": {"min": min(headline), "max": max(headline)},
        "most_favourable_admissible_reading_per_mwh": most_favourable,
        "atb_augmentation_finding": {
            "atb_2024_page": (
                "assume no variable O&M (VOM) costs. All operating costs are instead "
                "represented using fixed O&M (FOM) costs. The FOM costs include battery "
                "augmentation costs, which enables the system to operate at its rated "
                "capacity throughout its 15-year lifetime. FOM costs are estimated at "
                "2.5% of the capital costs in $/kW."
            ),
            "nrel_85332": (
                "We have allocated all operating costs (at the one-cycle-per-day level) "
                "to the FOM. By putting the operations and maintenance costs in the FOM "
                "rather than the VOM we in essence assume that battery performance has "
                "been guaranteed over the lifetime, such that operating the battery does "
                "not incur any costs to the battery operator."
            ),
            "carries_cycle_life": False,
            "carries_retention": False,
            "fom4_deflated_per_kw_yr": fom4_deflated,
            "atb_fom_per_mwh_at_one_cycle_per_day": atb_fom_per_mwh,
        },
        "verdict": verdict,
        "sources": {
            "ATB_2024_extract": "data/raw/nrel-atb/atb_2024{,v4}_electricity_filtered.part*.csv",
            "ATB_2024_page": "https://atb.nrel.gov/electricity/2024/utility-scale_battery_storage",
            "NREL_TP-6A40-85332": "https://www.osti.gov/servlets/purl/1984976 (sha256 3d351e895dd70c6e86c0d3ee22892fab73cccc040b597e12842d0c36dc46c676)",
            "NREL_TP-7A40-83586": "https://www.osti.gov/servlets/purl/1891204 (sha256 2ee8ed8256f6df8496743b8a67ee248a2848feb2ba8e1653abe63be10c5e5569)",
            "PNNL-33283": "https://www.energy.gov/sites/default/files/2022-09/2022%20Grid%20Energy%20Storage%20Technology%20Cost%20and%20Performance%20Assessment.pdf (sha256 8c15c2fdd30f0452d75e15767fb9128ac866c3e9dd15a03669d92fad1048976d)",
        },
    }

    out = REPO_ROOT / "results" / "calibration" / "_caiso179_degradation_split.json"
    out.write_text(json.dumps(record, indent=2) + "\n")

    print(f"G1 linearity  : max rel residual {g1['families'][sorted(g1['families'])[0]]['max_rel_residual']:.3e}  PASS={g1['linearity_pass']}")
    print(f"G1 deflator   : k={g1['deflator']:.6f}  PASS={g1['deflator_pass']}  families_agree={g1['families_agree']}")
    print(f"G2 phi_S1     : {g1['phi_S1']:.6f}   S2 cabinet {g2['S2_brackets']['MSP']['phi_cabinet_energy_hardware']:.4f}/{g2['S2_brackets']['MMP']['phi_cabinet_energy_hardware']:.4f}  bare pack {g2['S2_brackets']['MSP']['phi_cell_bare_pack']:.4f}/{g2['S2_brackets']['MMP']['phi_cell_bare_pack']:.4f}  PASS={g2['PASS']}")
    print(f"G3 pair       : PNNL EOL R={PNNL_EOL_RETENTION}, threshold-invariant={g3['eol_threshold_invariance']['identical']}  PASS={g3['PASS']}")
    print(f"incumbent     : F=0.25, cycles=5000 -> ${incumbent:.2f}/MWh")
    print(f"HEADLINE      : ${min(headline):.2f} - ${max(headline):.2f}/MWh  (screen ${ADMISSIBILITY_SCREEN:.2f})")
    print(f"most favourable admissible reading: ${most_favourable:.2f}/MWh")
    print(f"ATB FOM contrast @1 cycle/day     : ${atb_fom_per_mwh:.2f}/MWh (whole FOM)")
    print(f"VERDICT       : {verdict['branch']}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
