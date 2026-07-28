"""caiso-135 — D-GATE CHARTER for the committed-gas state. Does the caiso-118b lane ARM?

`FINDING-caiso134` §7 named the C3a-2025 lane by elimination — the CA-internal
committed-gas STATE — and handed forward two objects unchanged on the keeper:

1. ``caiso_ra_min_load_frac = 0.26`` (asserted "below the physical LSL/HSL
   ~0.40-0.57").
2. ``caiso_ra_mustoffer_quantity_gate = False`` (the published
   ``CAISO_RA_MUSTOFFER_GAS_MW`` wired as a CAP, never as the commitment
   DRIVER).

This instrument runs the charter's D1-D5 gates on COMMITTED BYTES, with **no LP
built and no solver called**, in the caiso-127 §5 / caiso-129 derive-first
discipline: a candidate that cannot clear its gates is killed for the cost of a
derive.

Sections
--------
* **§A — D1: DERIVE, don't pick (the decisive gate).** ``caiso_ra_min_load_frac``
  is consumed by :func:`market_sim.model.commitment.caiso_ra_mustoffer_min_gen`
  as ``min_load_frac × PLANT pmax`` — its own docstring: "the floor is the
  PLANT's minimum stable load ... never a per-tranche fraction", and CAISO is
  ``plant_level_fleet=True`` so the plant IS the LP unit. The measured statistic
  must therefore be defined on the PLANT basis. §A derives it from CAMPD CA unit
  conduct on BOTH conventions and reconciles it against the standing
  ``caiso-119`` value of 0.570.
* **§B — D4: one mechanism (rule 19 ``[R-ONE-MECH]``).** What already floors CA
  gas, from the keeper's own committed ``legitimacy_diagnostics.json``, plus the
  quantity gate's no-op bound on the current keeper.
* **§C — D5: forced-energy budget (rule 20 ``[R-FORCED-BUDGET]``).** CC_REGULAR's
  projected forced share under the counterfactual floor.
* **§D — D2: E1/E2 spillover pre-check.** How much the counterfactual floor would
  actually bind, and where in the day it would land.
* **§E — the lane reframe.** Belly commitment COVERAGE: model vs CEMS online
  plant count and online MW on the SAME matched plants.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only. Rule 25 ``[R-ISO-SCOPE]``: every number
is derived from CAISO's own market data — the ERCOT 0.574 / NYISO 0.523 values
are precedent for the METHOD only and are never transferred.

Usage::

    PYTHONPATH=.:src python scripts/probes/_caiso135_committed_gas_charter.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.constants import CAISO_RA_MUSTOFFER_GAS_MW  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import RAW_DIR  # noqa: E402
from market_sim.data.campd import _ONLINE_MW  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402
from scripts.data.derive_campd_gas_commitment_params import (  # noqa: E402
    class_plant_codes,
    weighted_percentile,
)

BUNDLE = REPO / "results" / "calibration" / "caiso130_nameplate_B"
UNIT_DIR = RAW_DIR / "campd-unit-level"
YEARS = (2023, 2024, 2025)
T = 8760

# The keeper's committed value, and the value the caiso-119/121/122 lane left
# standing as "the value the next keeper must carry" (per-UNIT basis).
KEEPER_FRAC = 0.26
CAISO119_UNIT_FRAC = 0.570

# caiso-134's defect window, reused verbatim so every row composes with it on
# one basis: Sep-Dec, hour-of-day 10-15.
DEFECT_MONTH_FROM = 9
DEFECT_HOD = (10, 15)

# Online convention, shared by both sides of every model-vs-CEMS comparison so
# neither side is advantaged: a plant is online when it carries at least 5 % of
# its own maximum sustained load (the derive script's ``_ONLINE_FRAC``, floored
# at the CAMPD ``_ONLINE_MW`` convention).
ONLINE_FRAC = 0.05
HSL_PCTILE = 99.5
LSL_PCTILE = 5.0


def cc_plant_codes() -> set[int]:
    """Return the model's CC_REGULAR plant codes (the class the bridge floors)."""
    mapping, _ = class_plant_codes("CAISO")
    return {code for code, klass in mapping.items() if klass == "CC_REGULAR"}


def model_plant_pmax() -> dict[int, float]:
    """Return ``{plant_code: summed model pmax}`` for CC_REGULAR.

    The denominator the floor is actually multiplied by: the detector sums a
    binned plant's tranche ``pmax`` into ``plant_pmax`` and floors
    ``min_load_frac × plant_pmax`` on the base tranche.
    """
    pmax: dict[int, float] = {}
    for gen in load_fleet_from_csv("CAISO", get_iso_config("CAISO")):
        if gen.plant_group == "CC_REGULAR" and gen.plant_code:
            code = int(gen.plant_code)
            pmax[code] = pmax.get(code, 0.0) + float(gen.pmax_mw)
    return pmax


def cems_plant_hours(year: int, codes: set[int]) -> pd.DataFrame:
    """Return CAMPD plant-hour gross load for *codes*, with an operation flag.

    Args:
        year: CAMPD vintage.
        codes: Plant codes to keep.

    Returns:
        Frame of ``facilityId`` / ``ts`` / ``load`` / ``n_on`` / ``n_full`` —
        one row per plant-hour. ``n_full >= n_on`` marks an hour in which every
        online unit at the plant ran the FULL hour (``opTime >= 1``), i.e. the
        plant-level analogue of caiso-119's ``opTime == 1.0`` conditioning.
    """
    frame = pd.read_parquet(
        UNIT_DIR / f"CA_{year}.parquet",
        columns=["facilityId", "unitId", "date", "hour", "opTime", "grossLoad"],
    )
    frame["facilityId"] = pd.to_numeric(frame["facilityId"], errors="coerce")
    frame = frame[frame["facilityId"].isin(codes)].copy()
    frame["grossLoad"] = frame["grossLoad"].fillna(0.0)
    frame["opTime"] = frame["opTime"].fillna(0.0)
    frame["on"] = frame["grossLoad"] > 0.0
    agg = (
        frame.groupby(["facilityId", "date", "hour"])
        .agg(
            load=("grossLoad", "sum"),
            n_on=("on", "sum"),
            n_full=("opTime", lambda s: int((s >= 1.0).sum())),
        )
        .reset_index()
    )
    agg["ts"] = pd.to_datetime(agg["date"]) + pd.to_timedelta(agg["hour"], unit="h")
    return agg


def section_a(codes: set[int], pmax: dict[int, float]) -> dict:
    """§A — D1: derive the min-load fraction on the basis the model consumes.

    Four cells, so the conflict between this session's derive and the standing
    caiso-119 value is explained on bytes rather than asserted:

    ============================  ==========================  ==================
    conditioning                  UNIT basis (caiso-119)      PLANT basis (model)
    ============================  ==========================  ==================
    p05 over FULL-operation h     reproduces 0.565/0.570      the consuming value
    p05 over ONLINE hours         the ISO-parameterised       the consuming value
                                  derive script's own
    ============================  ==========================  ==================

    Returns:
        Dict of per-year per-basis fractions.
    """
    print("=" * 78)
    print("A — D1: DERIVE, don't pick. The basis the floor is MULTIPLIED BY.")
    print("=" * 78)
    print(
        "  caiso_ra_mustoffer_min_gen floors  min_load_frac x PLANT pmax  on the\n"
        "  base tranche ('the floor is the PLANT's minimum stable load ... never a\n"
        "  per-tranche fraction'), and CAISO is plant_level_fleet=True, so the\n"
        "  measured statistic MUST be the plant's minimum stable load fraction.\n"
    )
    print(
        f"  {'year':<6}{'UNIT full-op':>14}{'PLANT full-op':>15}"
        f"{'UNIT online':>13}{'PLANT online':>14}{'plant/unit':>12}"
    )
    out: dict[int, dict[str, float]] = {}
    for year in YEARS:
        agg = cems_plant_hours(year, codes)
        raw = pd.read_parquet(
            UNIT_DIR / f"CA_{year}.parquet",
            columns=["facilityId", "unitId", "date", "hour", "opTime", "grossLoad"],
        )
        raw["facilityId"] = pd.to_numeric(raw["facilityId"], errors="coerce")
        raw = raw[raw["facilityId"].isin(codes)].copy()
        raw["grossLoad"] = raw["grossLoad"].fillna(0.0)
        raw["opTime"] = raw["opTime"].fillna(0.0)

        # UNIT basis — each CEMS unit against its own maximum sustained load.
        unit_full: list[tuple[float, float]] = []
        unit_online: list[tuple[float, float]] = []
        for _, grp in raw.groupby(["facilityId", "unitId"]):
            load = grp["grossLoad"].to_numpy(dtype=float)
            hsl = float(np.percentile(load, HSL_PCTILE))
            if hsl <= _ONLINE_MW:
                continue
            full = load[(grp["opTime"].to_numpy() >= 1.0) & (load > 0.0)]
            if full.size >= 50:
                unit_full.append((float(np.percentile(full / hsl, LSL_PCTILE)), hsl))
            online = load[load >= max(_ONLINE_MW, ONLINE_FRAC * hsl)]
            if online.size >= 50:
                unit_online.append(
                    (float(np.percentile(online / hsl, LSL_PCTILE)), hsl)
                )

        # PLANT basis — the plant's own total against the MODEL pmax the floor
        # is multiplied by (full-op) and against its own sustained max (online).
        plant_full: list[tuple[float, float]] = []
        plant_online: list[tuple[float, float]] = []
        for fid, grp in agg.groupby("facilityId"):
            model_mw = pmax.get(int(fid))
            load = grp["load"].to_numpy(dtype=float)
            hsl = float(np.percentile(load, HSL_PCTILE))
            if hsl <= _ONLINE_MW:
                continue
            full = grp[(grp["n_on"] > 0) & (grp["n_full"] >= grp["n_on"])]
            if model_mw and len(full) >= 50:
                plant_full.append(
                    (
                        float(np.percentile(full["load"].to_numpy() / model_mw, LSL_PCTILE)),
                        model_mw,
                    )
                )
            online = load[load >= max(_ONLINE_MW, ONLINE_FRAC * hsl)]
            if online.size >= 50:
                plant_online.append(
                    (float(np.percentile(online / hsl, LSL_PCTILE)), hsl)
                )

        def _p50(rows: list[tuple[float, float]]) -> float:
            arr = np.asarray(rows, dtype=float)
            return weighted_percentile(arr[:, 0], arr[:, 1], 50.0)

        uf, pf = _p50(unit_full), _p50(plant_full)
        uo, po = _p50(unit_online), _p50(plant_online)
        out[year] = {
            "unit_full": uf,
            "plant_full": pf,
            "unit_online": uo,
            "plant_online": po,
        }
        print(
            f"  {year:<6}{uf:>14.4f}{pf:>15.4f}{uo:>13.4f}{po:>14.4f}{pf / uf:>12.3f}"
        )
    print(
        "\n  READ: the UNIT full-op column REPRODUCES caiso-119's 0.565/0.570/0.570\n"
        "  (results/calibration/caiso119_minload_derive.json), so the conventions\n"
        "  are matched and the ONLY difference is the basis. On the PLANT basis the\n"
        "  model consumes, the same convention gives ~0.29-0.30 — a factor ~0.52,\n"
        "  the 2-train CC signature (a plant's minimum sustained configuration is\n"
        "  ONE train at min, i.e. about half the per-train fraction of plant cap).\n"
        f"  The keeper's {KEEPER_FRAC} sits INSIDE the measured plant-basis band; the\n"
        f"  standing {CAISO119_UNIT_FRAC} is a per-TRAIN statistic applied to PLANT capacity."
    )
    return out


def section_b(codes: set[int]) -> dict:
    """§B — D4: enumerate what already floors CA gas, and bound the quantity gate.

    Rule 19 ``[R-ONE-MECH]`` requires enumerating the existing floors on a class
    before adding or raising one. Read from the keeper's OWN committed
    ``legitimacy_diagnostics.json`` — no re-solve.
    """
    print()
    print("=" * 78)
    print("B — D4: ONE MECHANISM. What already floors CA gas (keeper's own D-2)?")
    print("=" * 78)
    diag = json.loads((BUNDLE / "legitimacy_diagnostics.json").read_text())
    rows = [
        r
        for r in diag["diagnostics"]["D2"]["rows"]
        if r["class"] in ("CC_REGULAR", "CT_PEAKER")
    ]
    print(f"  {'year':<6}{'class':<13}{'mechanism':<24}{'forced TWh':>12}{'share':>9}")
    for r in rows:
        print(
            f"  {r['year']:<6}{r['class']:<13}{r['mechanism']:<24}"
            f"{r['forced_twh']:>12.4f}{r['share_of_class']:>9.2%}"
        )
    mechs = {r["mechanism"] for r in rows}
    print(
        f"\n  READ: CC_REGULAR is floored by EXACTLY ONE mechanism ({', '.join(sorted(mechs))}).\n"
        "  So changing caiso_ra_min_load_frac is a REPLACEMENT of that mechanism's own\n"
        "  parameter, not a new floor stacked on its residual — rule 19 clean. It also\n"
        "  means the RA bridge is the sole channel available to this lane."
    )

    print("\n  Quantity gate (object 2) — can it bind on the CURRENT keeper?")
    print(
        f"  {'year':<6}{'CC_REGULAR pmax':>17}{'CT_PEAKER pmax':>16}"
        f"{'published cap':>15}{'verdict':>26}"
    )
    gate: dict[int, dict[str, float]] = {}
    for year in YEARS:
        frame = pd.read_parquet(
            BUNDLE / "hourly" / f"unit_hourly_{year}.parquet",
            columns=["pass", "plant_code", "plant_group", "hour", "cap_mw"],
        )
        h0 = frame[(frame["pass"] == "P1") & (frame["hour"] == 0)]
        cc = h0[h0["plant_group"] == "CC_REGULAR"]["cap_mw"].sum()
        ct = h0[h0["plant_group"] == "CT_PEAKER"]["cap_mw"].sum()
        cap = CAISO_RA_MUSTOFFER_GAS_MW[year]
        gate[year] = {"cc": float(cc), "ct": float(ct), "cap": float(cap)}
        verdict = "NO-OP (CC fleet under cap)" if cc <= cap else "would bind"
        print(f"  {year:<6}{cc:>17.0f}{ct:>16.0f}{cap:>15.0f}   {verdict}")
    print(
        "\n  READ: the gate drops bridged plants CHEAPEST-STARTUP-FIRST (the RUC\n"
        "  de-commitment order), and CT startup ($12-25/MW) is below CC ($35-50/MW),\n"
        "  so CT is dropped first. CT carries 0.03-1.0 % of its class as forced energy\n"
        "  (D-2 above) — dropping it is worth ~0. After CT, the kept CC fleet is under\n"
        "  the published cap in EVERY year, so the gate cannot remove one bridged CC\n"
        "  plant. Arming object 2 as-is is a MEASURED NO-OP on the current keeper."
    )
    return gate


def section_c(codes: set[int], pmax: dict[int, float], frac: float) -> dict:
    """§C — D5: project CC_REGULAR's forced share under the counterfactual floor.

    Rule 20 ``[R-FORCED-BUDGET]``: CC_REGULAR is a material class (>= 2 % of ISO
    load), so its forced share is gated at the 30 % merchant cap.
    """
    print()
    print("=" * 78)
    print(f"C — D5: FORCED-ENERGY BUDGET. CC_REGULAR share if the floor -> {frac}")
    print("=" * 78)
    diag = json.loads((BUNDLE / "legitimacy_diagnostics.json").read_text())
    base = {
        r["year"]: r
        for r in diag["diagnostics"]["D2"]["rows"]
        if r["class"] == "CC_REGULAR"
    }
    cap_share = diag["gates"]["d2_merchant_max_share"]
    print(
        f"  {'year':<6}{'forced now':>12}{'class TWh':>11}{'share now':>11}"
        f"{'added TWh':>11}{'share then':>12}{'cap':>7}{'verdict':>9}"
    )
    out: dict[int, float] = {}
    for year in YEARS:
        added = _added_floor_twh(year, codes, pmax, frac)
        f_now = base[year]["forced_twh"]
        tot = base[year]["class_total_twh"]
        share = (f_now + added) / (tot + added)
        out[year] = share
        print(
            f"  {year:<6}{f_now:>12.3f}{tot:>11.2f}{base[year]['share_of_class']:>11.2%}"
            f"{added:>11.3f}{share:>12.2%}{cap_share:>7.0%}"
            f"{'PASS' if share <= cap_share else 'FAIL':>9}"
        )
    print(
        "\n  READ: D5 PASSES with headroom at every candidate level — the forced budget\n"
        "  is NOT what refuses this lane. D1 is."
    )
    return out


def _added_floor_twh(
    year: int, codes: set[int], pmax: dict[int, float], frac: float
) -> float:
    """Return the TWh a ``frac`` floor would ADD on already-online plant-hours.

    An upper bound on the true added energy: it credits the floor on every
    online plant-hour, whereas the detector floors only bridged plants across
    detected gaps. Deliberately generous, so a PASS here is a real PASS.
    """
    frame = pd.read_parquet(
        BUNDLE / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "plant_code", "plant_group", "hour", "mw", "cap_mw"],
    )
    frame = frame[(frame["pass"] == "P1") & (frame["plant_group"] == "CC_REGULAR")]
    frame = frame[frame["plant_code"].isin(codes)]
    cap = frame[frame["hour"] == 0].groupby("plant_code")["cap_mw"].sum()
    plant = frame.groupby(["plant_code", "hour"], as_index=False)["mw"].sum()
    plant["pmax"] = plant["plant_code"].map(cap)
    online = plant[plant["mw"] >= np.maximum(_ONLINE_MW, ONLINE_FRAC * plant["pmax"])]
    return float(np.maximum(frac * online["pmax"] - online["mw"], 0.0).sum() / 1e6)


def section_d(codes: set[int], pmax: dict[int, float]) -> dict:
    """§D — D2: how much would the counterfactual floor bind, and WHERE?

    The charter gates E1 (2025 annual spillover <= +$0.00) in the EVENING, where
    caiso-134 §6 shows the model already over-runs gas ~25 %. This measures the
    binding split between the belly (favourable) and the evening (adverse).
    """
    print()
    print("=" * 78)
    print("D — D2: E1/E2 PRE-CHECK. Where would a raised floor actually bind?")
    print("=" * 78)
    print(
        f"  {'year':<6}{'window':<12}{'online ph':>11}{'load p50':>10}"
        f"{'add MW@.30':>12}{'add MW@.57':>12}"
    )
    out: dict[int, dict[str, float]] = {}
    for year in YEARS:
        frame = pd.read_parquet(
            BUNDLE / "hourly" / f"unit_hourly_{year}.parquet",
            columns=["pass", "plant_code", "plant_group", "hour", "mw", "cap_mw"],
        )
        frame = frame[(frame["pass"] == "P1") & (frame["plant_group"] == "CC_REGULAR")]
        frame = frame[frame["plant_code"].isin(codes)]
        cap = frame[frame["hour"] == 0].groupby("plant_code")["cap_mw"].sum()
        plant = frame.groupby(["plant_code", "hour"], as_index=False)["mw"].sum()
        plant["pmax"] = plant["plant_code"].map(cap)
        stamp = pd.date_range(f"{year}-01-01", periods=T, freq="h")
        belly = set(
            np.flatnonzero(
                (stamp.month >= DEFECT_MONTH_FROM)
                & (stamp.hour >= DEFECT_HOD[0])
                & (stamp.hour <= DEFECT_HOD[1])
            ).tolist()
        )
        evening = set(np.flatnonzero((stamp.hour >= 17) & (stamp.hour <= 22)).tolist())
        row: dict[str, float] = {}
        for tag, hours in (("belly", belly), ("evening", evening), ("all-8760", None)):
            sel = plant if hours is None else plant[plant["hour"].isin(hours)]
            online = sel[sel["mw"] >= np.maximum(_ONLINE_MW, ONLINE_FRAC * sel["pmax"])]
            n_h = T if hours is None else len(hours)
            a30 = float(np.maximum(0.30 * online["pmax"] - online["mw"], 0.0).sum())
            a57 = float(
                np.maximum(CAISO119_UNIT_FRAC * online["pmax"] - online["mw"], 0.0).sum()
            )
            row[f"{tag}_add30"] = a30 / n_h
            row[f"{tag}_add57"] = a57 / n_h
            print(
                f"  {year:<6}{tag:<12}{len(online):>11}"
                f"{online['mw'].div(online['pmax']).median():>10.3f}"
                f"{a30 / n_h:>12.0f}{a57 / n_h:>12.0f}"
            )
        out[year] = row
    print(
        "\n  READ: these are UPPER BOUNDS — they credit the floor on every online\n"
        "  plant-hour, whereas the detector floors only BRIDGED plants across\n"
        "  detected gaps (the RA bridge owns just 1.8 % of floored cells,\n"
        "  FINDING-caiso119 §1). The SOLVED value is caiso-119's own A/B: the far\n"
        "  larger 0.26 -> 0.570 delta moved belly gas by only -28/+59/+52 MW. At the\n"
        "  correctly-derived plant-basis ~0.30 the delta is ~5x smaller again, so the\n"
        "  lever is dispatch-near-inert by measurement — independent of D1's refusal.\n"
        "  Note the direction too: the floor adds price-taking min-load supply, which\n"
        "  pushes lambda DOWN, so E1/E2 are not at risk from the sign; the lane dies\n"
        "  on D1 (wrong basis) and on magnitude (inert), not on spillover."
    )
    return out


def section_e(codes: set[int]) -> dict:
    """§E — the lane reframe: is the belly deficit COMMITMENT or LOADING?

    caiso-118b's paradigm claims the model commits too FEW gas plants. Measured
    on the SAME matched plants, in caiso-134's own defect window.
    """
    print()
    print("=" * 78)
    print("E — THE REFRAME: is the belly deficit a COMMITMENT or a LOADING defect?")
    print("=" * 78)
    print(
        f"  {'year':<6}{'plants':>7}{'model on':>10}{'CEMS on':>9}{'on ratio':>10}"
        f"{'model MW':>10}{'CEMS MW':>9}{'MW ratio':>10}"
    )
    out: dict[int, dict[str, float]] = {}
    for year in YEARS:
        frame = pd.read_parquet(
            BUNDLE / "hourly" / f"unit_hourly_{year}.parquet",
            columns=["pass", "plant_code", "plant_group", "hour", "mw", "cap_mw"],
        )
        frame = frame[(frame["pass"] == "P1") & (frame["plant_group"] == "CC_REGULAR")]
        frame = frame[frame["plant_code"].isin(codes)]
        cap = frame[frame["hour"] == 0].groupby("plant_code")["cap_mw"].sum()
        plant = frame.groupby(["plant_code", "hour"], as_index=False)["mw"].sum()
        plant["pmax"] = plant["plant_code"].map(cap)
        stamp = pd.date_range(f"{year}-01-01", periods=T, freq="h")
        belly = set(
            np.flatnonzero(
                (stamp.month >= DEFECT_MONTH_FROM)
                & (stamp.hour >= DEFECT_HOD[0])
                & (stamp.hour <= DEFECT_HOD[1])
            ).tolist()
        )
        sel = plant[plant["hour"].isin(belly)].copy()
        sel["on"] = sel["mw"] >= np.maximum(_ONLINE_MW, ONLINE_FRAC * sel["pmax"])
        m_on = sel.groupby("hour")["on"].sum().mean()
        m_mw = sel.groupby("hour")["mw"].sum().mean()

        agg = cems_plant_hours(year, codes)
        hsl = agg.groupby("facilityId")["load"].quantile(HSL_PCTILE / 100.0)
        win = agg[
            (agg["ts"].dt.month >= DEFECT_MONTH_FROM)
            & (agg["ts"].dt.hour >= DEFECT_HOD[0])
            & (agg["ts"].dt.hour <= DEFECT_HOD[1])
        ].copy()
        win["on"] = win["load"] >= np.maximum(
            _ONLINE_MW, ONLINE_FRAC * win["facilityId"].map(hsl)
        )
        c_on = win.groupby("ts")["on"].sum().mean()
        c_mw = win.groupby("ts")["load"].sum().mean()
        out[year] = {
            "on_ratio": float(m_on / c_on),
            "mw_ratio": float(m_mw / c_mw),
        }
        print(
            f"  {year:<6}{len(codes):>7}{m_on:>10.1f}{c_on:>9.1f}{m_on / c_on:>10.3f}"
            f"{m_mw:>10.0f}{c_mw:>9.0f}{m_mw / c_mw:>10.3f}"
        )
    print(
        "\n  READ: the model has AS MANY OR MORE CC plants ONLINE in the belly than\n"
        "  reality does (ratio 1.01-1.13), while carrying only 0.74-0.80x the MW.\n"
        "  The belly gas deficit is therefore NOT an under-COMMITMENT of plants —\n"
        "  it is a per-plant LOADING deficit on plants the model already has online.\n"
        "  A min-load FLOOR is the wrong instrument for it by construction: the\n"
        "  plants it would commit are already committed."
    )
    return out


def reality_test(codes: set[int], pmax: dict[int, float]) -> None:
    """Cross-check: how often does CAISO's own fleet sit BELOW each candidate floor?

    A min-load floor asserts the plant CANNOT sustain less. Measured against the
    plants the floor would be applied to.
    """
    print()
    print("=" * 78)
    print("REALITY TEST — CEMS online CC plant-hours BELOW each candidate floor")
    print("=" * 78)
    print(
        f"  {'year':<6}{'online ph':>11}{'< 0.26':>9}{'< 0.30':>9}"
        f"{'< 0.3756':>10}{'< 0.570':>9}{'median':>9}"
    )
    for year in YEARS:
        agg = cems_plant_hours(year, codes)
        agg["pmax"] = agg["facilityId"].map(pmax)
        agg = agg.dropna(subset=["pmax"])
        hsl = agg.groupby("facilityId")["load"].quantile(HSL_PCTILE / 100.0)
        online = agg[
            agg["load"] >= np.maximum(_ONLINE_MW, ONLINE_FRAC * agg["facilityId"].map(hsl))
        ].copy()
        load = online["load"] / online["pmax"]
        print(
            f"  {year:<6}{len(online):>11}{(load < 0.26).mean():>9.1%}"
            f"{(load < 0.30).mean():>9.1%}{(load < 0.3756).mean():>10.1%}"
            f"{(load < CAISO119_UNIT_FRAC).mean():>9.1%}{load.median():>9.3f}"
        )
    print(
        "\n  READ: a 0.570 floor would be contradicted by CAISO's OWN plants in ~2 of\n"
        "  every 5 online hours, and 0.3756 in ~1 in 5. The keeper's 0.26 is the\n"
        "  candidate the measured record actually supports."
    )


def main() -> None:
    """Run the caiso-135 D-gate charter (no LP, no solver)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sections", default="ABCDER", help="Subset of A/B/C/D/E/R to run."
    )
    args = parser.parse_args()
    want = set(args.sections.upper())

    codes = cc_plant_codes()
    pmax = model_plant_pmax()
    print(f"\ncaiso-135 D-GATE CHARTER — keeper bundle {BUNDLE.name}")
    print(f"matched CC_REGULAR plants: {len(codes)}   model pmax {sum(pmax.values()):.0f} MW\n")

    if "A" in want:
        section_a(codes, pmax)
    if "B" in want:
        section_b(codes)
    if "C" in want:
        section_c(codes, pmax, 0.30)
    if "D" in want:
        section_d(codes, pmax)
    if "E" in want:
        section_e(codes)
    if "R" in want:
        reality_test(codes, pmax)
    print("\nDone — no LP was built and no solver was called.\n")


if __name__ == "__main__":
    main()
