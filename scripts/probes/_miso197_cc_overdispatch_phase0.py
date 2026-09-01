"""miso-197 phase-0 census: the CC_REGULAR over-dispatch root cause (zero-solve).

Charter: the FINDING-miso196 §7a/§8.1 named successor — a ROOT-CAUSE
investigation, not a lever. The keeper `2026-08-30-miso-191-bexit`
(`results/calibration/miso191_bax_B`) reads CC_REGULAR-2024 **+6.664 TWh over**
on C1 while ST_GAS-2024 is −7.553 under, and miso-196 established that the
pro-rata outage application was MASKING the CC excess (arming the
structurally-faithful `cc_outage_derate_from_top` exposed it at full size:
+12.013, K-1 kill). The question this census answers with committed artifacts
and measured data only, NO SOLVE: **where does the CC excess sit, whose energy
is it, what does it displace, and does it survive at family grain?**

DISCLOSED PRE-FREEZE READS (all of them the keeper's PUBLISHED state, none a
new quantity about this question; the miso-196 B4 discipline):
  * The C1 class table (payload ``gmModel`` vs bench ``classFull``), which the
    charter itself quotes. It shows the sign pattern this census must explain:
    CC_REGULAR −3.674 / **+6.664** / −2.456 across 2023/2024/2025, ST_GAS
    −3.729 / −7.553 / −6.548, i.e. the model's CC energy JUMPS +11.995 TWh
    2023→2024 while the actual moves +1.657 — the excess is 2024-specific, not
    a standing level offset.
  * The committed D-1 rows: CC_REGULAR profile_r 0.995/0.993/0.970, cv_ratio
    0.739/0.587/0.665 — the diurnal SHAPE is already known near-perfect and
    slightly too flat; W1c below is the independent re-measurement, not news.
  * ``meta.json.gas_prices`` {2023: 2.54, 2024: 2.19, 2025: 3.52} $/MMBtu and
    the keeper's armed-mechanism list (``run_config.json``): ST_GAS carries
    armed mustrun mechanisms (`st_gas_mustrun_per_plant`, `_p25_level`,
    `_p25_measured_level`) and the C8 grounded note says 2025 ST_GAS forced
    share is 34.2% — ST_GAS is a floored class; CC_REGULAR carries NO floor
    (miso-196 §5a).
  * Mechanical satisfiability of every basis below, verified before this rule
    was frozen (payload blob decode identity on plant 991: recon 5.2413 vs
    m_ann 5.2407 TWh; bench campd blob identity: 5.3538 vs c_ann 5.3559; B1
    build resolves 341 CC_REGULAR / 131 ST_GAS rows for 2024; volErr carries
    CC_REGULAR × 6 zones × 12 months, src=eia923). No witness aggregate was
    computed pre-freeze.
  * BASIS CORRECTION, DISCLOSED (made by the satisfiability pass BEFORE this
    rule was frozen or pushed — the miso-196 §1 pattern): the bench carries 8
    CC_REGULAR and 10 ST_GAS SLICE keys (``code:CLASS`` at multi-class
    plants), so an early draft's plant-keyed ceiling table would have (a)
    skipped those plants' CC portion from the class ceiling and (b) mixed
    other classes into per-plant ceilings. Corrected: the CLASS ceiling is
    computed from B1 rows directly (Σ pmax×availability over
    plant_group==CC_REGULAR — the LP's own class bound), and per-plant
    ceilings are keyed (plant_code, group) so a slice key reads its own
    class's ceiling. No witness aggregate was computed on the wrong basis.

BASES (every quantity below derives from these, nothing else)
  B1  The load-bearing TRANCHE fleet build under the keeper's reconstructed
      ``ScenarioConfig`` — the exact miso-196 B1 path:
      ``load_retired_within_window`` → ``load_or_synthesize_bins`` →
      ``bins_to_fleet`` → ``generators_to_fleet_arrays(config=cfg, iso="MISO",
      year=y)`` for y in {2023, 2024, 2025}. Supplies per-row ``pmax``,
      ``availability`` (n×8760), ``heat_rate``, ``plant_code``,
      ``plant_group``. Class availability CEILING for a plant-year =
      Σ_rows pmax×availability / 1e6 TWh.
  B2  The keeper's committed P1 sidecars: ``hourly/class_hourly_<y>.parquet``
      (model class-hour MW, grid LP).
  B3  The keeper's committed dashboard artifacts: run payload
      ``frontend/data/backcast/runs/2026-08-30-miso-191-bexit.js`` (per-plant
      ``m_ann``/``m_mon`` exact, hourly ``m`` blob at 1%-of-nameplate
      resolution; ``volErr`` class×zone×month grid-delivered model vs EIA-923;
      ``gmModel``; ``fuelRows``; ``nonfossilHr`` incl. the import panel) and
      bench ``frontend/data/backcast/bench/MISO/<y>.json.gz`` (``classFull``,
      ``e930``, per-plant ``c_ann``/``c_mon`` CEMS-net, ``e_ann``/``e_mon``
      EIA-923, ``campd`` hourly blob, ``npl``, ``zone``, ``group``).
      BASIS NOTES, frozen: per-plant levels compare m_ann (grid LP, whole
      plant for the CHP-free CC_REGULAR/ST_GAS) against c_ann (CEMS net);
      hourly blobs are quantized to 1% of nameplate and are used for SHAPE
      and CONDUCT only, never for level adjudication; class-grain levels use
      the C1 basis (gmModel vs classFull) exactly.
  B4  MISO's own measured heat-input record: ``data/raw/campd-unit-level/
      *_<y>.parquet`` filtered to the bench CC_REGULAR/ST_GAS facilities —
      per-facility Σ heatInput / Σ grossLoad = the measured heat rate.
      GUARD, frozen ex ante: a facility enters the measured-HR population
      only if |c_ann/e_ann − 1| ≤ 0.10 AND c_ann ≥ 0.2 TWh (CEMS covers the
      whole plant — excludes CT-only CC reporters whose steam output CEMS
      misses, which would bias measured CC HR high).
  B5  The duct-flag map the miso-193 census used:
      ``data.fleet.campd_bins.cc_duct_peaking_pct()`` — a CC plant is
      duct-flagged iff its map value > 0.

POPULATIONS. CC = payload/bench plant slices whose class resolves to
CC_REGULAR (bench ``group`` where present, else B1 ``plant_group`` via plant
code); ST = same for ST_GAS. Slice keys (``code:CLASS``) resolve to their own
slice class.

FROZEN ADJUDICATION RULE (ex ante; every line is stated with its witness and
every quantity is reported at full magnitude whichever way it falls; where a
line cannot fire cleanly the amendment is disclosed, never silently applied —
the miso-191/193 discipline):

  W1 WHERE (year 2024 unless stated; Δ = model − actual).
    W1a ZONAL. Δ by volErr zone (annual sum). LINE: ZONALLY CONCENTRATED iff
        the top-2 zones by positive Δ carry ≥ 70% of total positive Δ.
    W1b MONTHLY. Δ by month (volErr zones summed). LINE: LEVEL-LIKE iff ≥ 9
        of 12 months have Δ > 0 AND no single month carries > 25% of Σ|Δ|;
        else SEASONAL/EVENT-LIKE (name the top months).
    W1c HOUR-OF-DAY. Model class HOD profile (B2, /its own mean) minus actual
        class HOD profile (Σ B3 campd blobs, /its own mean). LINE:
        SHAPE-NEUTRAL iff max_h |p_m − p_a| ≤ 0.10; else the excess has a
        diurnal signature (name the window). Cross-checked against the
        committed D-1 row, which is disclosed above and already says shape is
        near-perfect — this witness can only confirm or surprise.
  W2 WHOSE.
    W2a PLANT CONCENTRATION. Per-plant Δ2024 = m_ann − c_ann over CC, ranked.
        LINE: CONCENTRATED iff the top-5 plants by positive Δ carry ≥ 60% of
        Σ positive Δ; else SPREAD.
    W2b DUCT POPULATION. Share of Σ positive Δ carried by duct-flagged
        plants vs their share of CC bench capacity (npl). LINE: the duct
        population is IMPLICATED iff its positive-Δ share ≥ capacity share
        + 20 pp.
    W2c THE JUMP. Per-plant (m_ann24 − m_ann23) vs (c_ann24 − c_ann23),
        ranked by model jump; the top-10 carriers reported with both faces
        and their B1 ceilings both years. DESCRIPTIVE (no line) — it names
        the plants that carry the model's +11.995 TWh jump.
    W2d CEILINGS. Per year: class ceiling TWh (B1), model class energy (C1
        gmModel), actual (classFull), headroom = ceiling − model. LINES:
        (i) model CC is CEILING-LIMITED in year y iff gmModel ≥ 97% of
        ceiling — fires the availability basis as the owner of that year's
        UNDER; (ii) plants where c_ann > 1.02 × plant ceiling are a basis
        defect list (actual exceeds modeled availability), reported.
    W2e AVAILABILITY COMPOSITION. Class-mean availability (pmax-weighted, B1)
        per year. LINE: 2024-AVAILABILITY-IMPLICATED iff mean_avail_2024 −
        mean(mean_avail_2023, mean_avail_2025) ≥ +0.02 (2 pp ≈ 4.9 TWh at
        class scale — the excess's order of magnitude).
  W3 WHAT IT DISPLACES.
    W3a SUBSTITUTION IDENTITY. Monthly Δ vectors (volErr, zones summed) for
        CC and ST_GAS, 2024: Pearson corr and the cancellation ratio
        |ΣΔcc + ΣΔst| / (|ΣΔcc| + |ΣΔst|). LINE: SINGLE SUBSTITUTION DEFECT
        iff corr ≤ −0.5 AND cancellation ≤ 0.4. 2023/2025 reported for
        contrast (the public table already says they do NOT pair there).
    W3b CONDUCT (whose behaviour is un-modeled). Hours where ACTUAL ST_GAS
        class output ≥ its own p75: the ACTUAL CC class's simultaneous
        utilization u = cc_actual[t] / p99.5(cc_actual). LINES: median u ≤
        0.90 → reality runs ST_GAS while CC has headroom = ST_GAS's real
        dispatch is NOT strict-merit against CC (out-of-merit/must-run
        conduct the LP lacks owns the pair); median u ≥ 0.97 → reality's CC
        is effectively maxed in exactly those hours = the model's CC
        ceiling/level is implicated instead; between → MIXED (both faces
        reported). Model CC utilization in the same hours reported alongside.
    W3c PHYSICS CROSSING (same-fuel, so the gas price cancels). Model
        HR(ST_GAS)/HR(CC) — pmax-weighted medians, B1 — vs measured
        HR(ST_GAS)/HR(CC) from B4 under its guard. LINE: HR INPUTS NOT
        IMPLICATED iff the model ratio is within ±15% of the measured ratio;
        outside → the class heat-rate inputs are implicated in the
        mis-ordering.
    W3d THE ABSORBER TABLE. Per year: Δ for every C1 gas/coal class, the
        family sums, the nonfossilHr import panel (mTwh − aTwh), and
        nonfossil deltas where the payload carries an actual. LINE: IMPORTS
        IMPLICATED in year y iff import (m − a) ≥ +2 TWh. (miso-178 §5
        already indicts phantom imports in the 2025 tail; this is the annual
        face.)
  W4 FAMILY GRAIN.
    W4a LINE: the 2024 CC excess is INTRA-FAMILY REALLOCATION iff
        |Σ gas-family Δ| < |Δ_CC| (the family miss is smaller than the class
        miss — the excess is an allocation error inside gas, not a gas-level
        error). Family = the C1-scored gas classes (benchmark_semantics
        GAS_CLASSES minus FUELMIX_EXCLUDED), the C2 complete-vintage basis.
    W4b REPORTED, NOT GATED: the classFull-sum vs e930 gas wedge per year
        (the 923-vs-930 basis gap), so no reader mistakes it for model error.

OUT OF SCOPE, frozen: no lever is proposed here; no offer-curve level adder
(family closed R/I at miso-179/180); no `cc_outage_derate_from_top` re-test
(adjudicated for this keeper, re-offered only after the repair); no
nameplate-basis switch (miso-141 §11, owner court); C3a is reported nowhere —
this is a C1 quantity census. The census record is
``results/calibration/_miso197_cc_overdispatch_phase0.json``; the finding doc
interprets, this probe only measures.

Reproduction:
    python3 scripts/probes/_miso197_cc_overdispatch_phase0.py --satisfiability
    python3 scripts/probes/_miso197_cc_overdispatch_phase0.py
"""

from __future__ import annotations

import argparse
import base64
import dataclasses
import gzip
import json
import re
import sys
import typing
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    bins_to_fleet,
    generators_to_fleet_arrays,
    load_or_synthesize_bins,
    load_retired_within_window,
)
from market_sim.data.fleet.campd_bins import cc_duct_peaking_pct  # noqa: E402
from scripts.lib.benchmark_semantics import GAS_CLASSES  # noqa: E402

ISO = "MISO"
YEARS = (2023, 2024, 2025)
FOCUS_YEAR = 2024
KEEPER = _REPO / "results" / "calibration" / "miso191_bax_B"
RUN_ID = "2026-08-30-miso-191-bexit"
PAYLOAD = _REPO / "frontend" / "data" / "backcast" / "runs" / f"{RUN_ID}.js"
BENCH_DIR = _REPO / "frontend" / "data" / "backcast" / "bench" / "MISO"
CAMPD_DIR = _REPO / "data" / "raw" / "campd-unit-level"
OUT = _REPO / "results" / "calibration" / "_miso197_cc_overdispatch_phase0.json"

# C1-scored gas classes (the C2 complete-vintage family basis).
FUELMIX_EXCLUDED = frozenset({"CT_CHP", "OTHER", "OTHER_FOSSIL"})
GAS_SCORED = tuple(c for c in GAS_CLASSES if c not in FUELMIX_EXCLUDED)

# Frozen ex-ante lines (docstring is the authority; these mirror it).
W1A_TOP2_SHARE = 0.70
W1B_POS_MONTHS = 9
W1B_MAX_MONTH_SHARE = 0.25
W1C_SHAPE_TOL = 0.10
W2A_TOP5_SHARE = 0.60
W2B_DUCT_MARGIN_PP = 20.0
W2D_CEILING_FRAC = 0.97
W2D_PLANT_CEIL_TOL = 1.02
W2E_AVAIL_PP = 0.02
W3A_CORR_LINE = -0.5
W3A_CANCEL_LINE = 0.4
W3B_HEADROOM_U = 0.90
W3B_MAXED_U = 0.97
W3B_ST_PCTL = 75.0
W3B_CC_REF_PCTL = 99.5
W3C_RATIO_TOL = 0.15
W3D_IMPORT_TWH = 2.0
W4B_HR_GUARD_DEV = 0.10
W4B_HR_GUARD_TWH = 0.2


# ------------------------------------------------------------------ artifacts
def load_payload() -> dict:
    """Decode the keeper's committed run payload (B3)."""
    txt = PAYLOAD.read_text()
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', txt)
    if not m:
        raise SystemExit(f"no runGz blob in {PAYLOAD}")
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def load_bench(year: int) -> dict:
    """Load the committed MISO bench part for ``year`` (B3)."""
    with gzip.open(BENCH_DIR / f"{year}.json.gz") as fh:
        return json.load(fh)["bench"]


def blob_mw(b64: str, npl: float) -> np.ndarray:
    """Decode a payload/bench uint8 CF blob to hourly MW (1%-of-npl steps)."""
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8)
    return raw.astype(float) / 100.0 * float(npl)


# ------------------------------------------------------------- keeper config
def keeper_config(year: int, **overrides: object) -> ScenarioConfig:
    """Rebuild the keeper's ScenarioConfig from its committed run_config dump."""
    dump = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    hints = typing.get_type_hints(ScenarioConfig)
    out: dict[str, object] = {}
    for f in dataclasses.fields(ScenarioConfig):
        if f.name not in dump:
            continue
        val = dump[f.name]
        ann = str(hints.get(f.name, ""))
        if val is None:
            out[f.name] = None
        elif "frozenset" in ann and isinstance(val, list):
            out[f.name] = frozenset(val)
        elif "tuple" in ann and isinstance(val, list):
            out[f.name] = tuple(val)
        elif "Path" in ann and isinstance(val, str):
            out[f.name] = Path(val)
        else:
            out[f.name] = val
    out["mode"] = "backcast"
    out["weather_year"] = year
    out.update(overrides)
    return ScenarioConfig(**out)  # type: ignore[arg-type]


def build(year: int):
    """Load the keeper's load-bearing TRANCHE fleet for ``year`` (basis B1)."""
    cfg = keeper_config(year)
    iso_cfg = get_iso_config(ISO)
    scoped = bool(getattr(cfg, "retiree_vintage_status_scope", False)) or bool(
        getattr(cfg, "partial_plant_exit_carry", False)
    )
    retired = load_retired_within_window(
        ISO,
        iso_cfg,
        year=int(cfg.weather_year) if scoped else None,
        vintage_status_scope=bool(getattr(cfg, "retiree_vintage_status_scope", False)),
        partial_plant_exit_carry=bool(getattr(cfg, "partial_plant_exit_carry", False)),
    )
    bins = load_or_synthesize_bins(cfg, ISO, iso_cfg, retired)
    assert bins is not None and not bins.empty, "premise: MISO takes the bins path"
    zones = [z.name for z in iso_cfg.zones]
    gens, _ = bins_to_fleet(bins, zones, cfg)
    fa = generators_to_fleet_arrays(gens, zones, 8760, iso=ISO, config=cfg, year=year)
    return gens, fa


def plant_tables(
    gens, fa
) -> tuple[dict[tuple[int, str], dict], dict[int, str | None]]:
    """(plant_code, group)-keyed B1 roll-up: ceiling TWh, pmax; plant→group map.

    Keyed per CLASS at each plant (the satisfiability-pass basis correction:
    slice plants must read their own class's ceiling, never a mixed-plant one).
    ``grp[code]`` resolves only single-group plants; a multi-group plant maps
    to ``None`` (its keys resolve through bench group / slice-key class).
    """
    per: dict[tuple[int, str], dict] = {}
    groups_of: dict[int, set] = {}
    avail_e = fa.availability * fa.pmax[:, None]  # (n, T) MW available
    for i, g in enumerate(gens):
        code = int(g.plant_code)
        if code <= 0 or g.plant_group is None:
            continue
        key = (code, str(g.plant_group))
        d = per.setdefault(key, {"pmax": 0.0, "ceiling_twh": 0.0})
        d["pmax"] += float(fa.pmax[i])
        d["ceiling_twh"] += float(avail_e[i].sum()) / 1e6
        groups_of.setdefault(code, set()).add(str(g.plant_group))
    grp: dict[int, str | None] = {
        c: (next(iter(gs)) if len(gs) == 1 else None) for c, gs in groups_of.items()
    }
    return per, grp


def class_rows(gens, fa, klass: str) -> np.ndarray:
    """Boolean mask of B1 rows whose plant_group == ``klass``."""
    return np.asarray([g.plant_group == klass for g in gens], dtype=bool)


def weighted_median(x: np.ndarray, w: np.ndarray) -> float:
    """pmax-weighted median (the frozen class-HR summary)."""
    order = np.argsort(x)
    cw = np.cumsum(w[order])
    return float(x[order][np.searchsorted(cw, 0.5 * cw[-1])])


# ----------------------------------------------------------------- populations
def slice_class(
    key: str, bench_plants: dict, b1_grp: dict[int, str]
) -> str | None:
    """Resolve a payload/bench slice key to its model class."""
    bp = bench_plants.get(key)
    if bp is not None and bp.get("group"):
        return str(bp["group"])
    if ":" in key:
        return key.split(":", 1)[1]
    try:
        return b1_grp.get(int(key))
    except ValueError:
        return None


def population_keys(
    payload_year: dict, bench_plants: dict, b1_grp: dict[int, str], klass: str
) -> list[str]:
    """All plant/slice keys (payload ∪ bench) resolving to ``klass``."""
    keys = set(payload_year.get("plants", {})) | set(bench_plants)
    return sorted(k for k in keys if slice_class(k, bench_plants, b1_grp) == klass)


# ------------------------------------------------------------------ witnesses
def monthly_delta(ypay: dict, klass: str) -> tuple[np.ndarray, np.ndarray]:
    """(model, actual) monthly TWh vectors from volErr (zones summed)."""
    cell = ypay["volErr"].get(klass, {})
    m = np.zeros(12)
    a = np.zeros(12)
    for zc in cell.get("zoneMon", {}).values():
        m += np.asarray(zc["m"], dtype=float)
        a += np.asarray(zc["a"], dtype=float)
    return m, a


def w1_where(ypay: dict, bench: dict, model_hod: np.ndarray, actual_hod: np.ndarray):
    """W1a/b/c on the frozen bases."""
    cell = ypay["volErr"]["CC_REGULAR"]
    zonal = {
        z: round(float(np.sum(zc["m"]) - np.sum(zc["a"])), 4)
        for z, zc in cell["zoneMon"].items()
    }
    pos = {z: d for z, d in zonal.items() if d > 0}
    pos_tot = sum(pos.values())
    top2 = sorted(pos.values(), reverse=True)[:2]
    w1a_share = (sum(top2) / pos_tot) if pos_tot > 0 else 0.0
    m_mon, a_mon = monthly_delta(ypay, "CC_REGULAR")
    d_mon = m_mon - a_mon
    pos_months = int((d_mon > 0).sum())
    abs_tot = float(np.abs(d_mon).sum())
    max_share = float(np.abs(d_mon).max() / abs_tot) if abs_tot > 0 else 0.0
    p_m = model_hod / model_hod.mean()
    p_a = actual_hod / actual_hod.mean()
    hod_gap = p_m - p_a
    return {
        "w1a_zonal_delta_twh": dict(sorted(zonal.items(), key=lambda x: -x[1])),
        "w1a_top2_share_of_positive": round(w1a_share, 4),
        "w1a_line": "ZONALLY CONCENTRATED"
        if w1a_share >= W1A_TOP2_SHARE
        else "NOT CONCENTRATED",
        "w1b_monthly_delta_twh": [round(float(x), 4) for x in d_mon],
        "w1b_pos_months": pos_months,
        "w1b_max_month_share": round(max_share, 4),
        "w1b_line": "LEVEL-LIKE"
        if pos_months >= W1B_POS_MONTHS and max_share <= W1B_MAX_MONTH_SHARE
        else "SEASONAL/EVENT-LIKE",
        "w1b_top_months": [
            int(i) + 1 for i in np.argsort(-np.abs(d_mon))[:3]
        ],
        "w1c_hod_gap": [round(float(x), 4) for x in hod_gap],
        "w1c_max_abs_gap": round(float(np.abs(hod_gap).max()), 4),
        "w1c_line": "SHAPE-NEUTRAL"
        if float(np.abs(hod_gap).max()) <= W1C_SHAPE_TOL
        else "DIURNAL SIGNATURE",
    }


def w2_whose(
    pay: dict,
    benches: dict[int, dict],
    b1: dict[int, tuple],
    duct: dict[int, float],
):
    """W2a/b/c/d/e on the frozen bases."""
    out: dict = {}
    # Per-plant Δ2024 over CC (m_ann vs c_ann; bench-covered only for Δ —
    # a plant with no CEMS has no measured actual; those are listed apart).
    y = str(FOCUS_YEAR)
    ypay = pay["years"][y]
    bench = benches[FOCUS_YEAR]
    b1_grp24 = b1[FOCUS_YEAR][1]
    cc_keys = population_keys(ypay, bench["plants"], b1_grp24, "CC_REGULAR")
    rows = []
    model_only = []
    bench_only = []
    for k in cc_keys:
        mp = ypay["plants"].get(k)
        bp = bench["plants"].get(k)
        m_ann = float(mp["m_ann"]) if mp else 0.0
        if bp is None:
            if m_ann > 0.2:
                model_only.append({"key": k, "m_ann": round(m_ann, 4)})
            continue
        c_ann = float(bp.get("c_ann", 0.0))
        if mp is None:
            if c_ann > 0.2:
                bench_only.append({"key": k, "c_ann": round(c_ann, 4)})
            continue
        rows.append(
            {
                "key": k,
                "name": bp.get("name"),
                "zone": bp.get("zone"),
                "npl": bp.get("npl"),
                "m_ann": round(m_ann, 4),
                "c_ann": round(c_ann, 4),
                "delta": round(m_ann - c_ann, 4),
                "duct": bool(duct.get(int(k.split(":")[0]), 0.0) > 0.0),
            }
        )
    rows.sort(key=lambda r: -r["delta"])
    pos = [r for r in rows if r["delta"] > 0]
    pos_tot = sum(r["delta"] for r in pos)
    top5 = sum(r["delta"] for r in pos[:5])
    out["w2a_rows"] = rows
    out["w2a_model_only"] = model_only
    out["w2a_bench_only"] = bench_only
    out["w2a_pos_total_twh"] = round(pos_tot, 4)
    out["w2a_top5_share"] = round(top5 / pos_tot, 4) if pos_tot > 0 else None
    out["w2a_line"] = (
        "CONCENTRATED"
        if pos_tot > 0 and top5 / pos_tot >= W2A_TOP5_SHARE
        else "SPREAD"
    )
    # W2b duct split.
    duct_pos = sum(r["delta"] for r in pos if r["duct"])
    npl_tot = sum(float(r["npl"] or 0.0) for r in rows)
    npl_duct = sum(float(r["npl"] or 0.0) for r in rows if r["duct"])
    duct_share = duct_pos / pos_tot if pos_tot > 0 else 0.0
    cap_share = npl_duct / npl_tot if npl_tot > 0 else 0.0
    out["w2b_duct_pos_share"] = round(duct_share, 4)
    out["w2b_duct_cap_share"] = round(cap_share, 4)
    out["w2b_line"] = (
        "DUCT POPULATION IMPLICATED"
        if (duct_share - cap_share) * 100.0 >= W2B_DUCT_MARGIN_PP
        else "NOT DUCT-SPECIFIC"
    )
    # W2c the 2023→2024 jump, per plant (model face vs actual face).
    ypay23 = pay["years"]["2023"]
    bench23 = benches[2023]
    per23_pt = b1[2023][0]
    per24_pt = b1[FOCUS_YEAR][0]
    jumps = []
    for k in cc_keys:
        m24 = float(ypay["plants"].get(k, {}).get("m_ann", 0.0) or 0.0)
        m23 = float(ypay23["plants"].get(k, {}).get("m_ann", 0.0) or 0.0)
        c24 = float(bench["plants"].get(k, {}).get("c_ann", 0.0) or 0.0)
        c23 = float(bench23["plants"].get(k, {}).get("c_ann", 0.0) or 0.0)
        code = int(k.split(":")[0])
        ck = (code, "CC_REGULAR")
        jumps.append(
            {
                "key": k,
                "name": bench["plants"].get(k, {}).get("name"),
                "m_jump": round(m24 - m23, 4),
                "c_jump": round(c24 - c23, 4),
                "ceiling23": round(per23_pt.get(ck, {}).get("ceiling_twh", 0.0), 4),
                "ceiling24": round(per24_pt.get(ck, {}).get("ceiling_twh", 0.0), 4),
            }
        )
    jumps.sort(key=lambda r: -r["m_jump"])
    out["w2c_model_jump_total"] = round(sum(r["m_jump"] for r in jumps), 4)
    out["w2c_actual_jump_total"] = round(sum(r["c_jump"] for r in jumps), 4)
    out["w2c_top10"] = jumps[:10]
    # W2d ceilings per year + plant basis-defect list.
    ceil_face = {}
    defect_list = []
    for yr in YEARS:
        per_pt, b1_grp = b1[yr][0], b1[yr][1]
        gens_y, fa_y = b1[yr][2]
        bench_y = benches[yr]
        ypay_y = pay["years"][str(yr)]
        cc_keys_y = population_keys(
            ypay_y, bench_y["plants"], b1_grp, "CC_REGULAR"
        )
        # Class ceiling from B1 rows directly — the LP's own class bound
        # (satisfiability-pass basis correction; never a plant-key roll-up).
        m_cc = class_rows(gens_y, fa_y, "CC_REGULAR")
        ceiling = float(
            (fa_y.availability[m_cc] * fa_y.pmax[m_cc][:, None]).sum()
        ) / 1e6
        gm = float(ypay_y["gmModel"].get("CC_REGULAR", 0.0))
        cf = float(bench_y["classFull"].get("CC_REGULAR", 0.0))
        ceil_face[yr] = {
            "ceiling_twh": round(ceiling, 3),
            "model_twh": gm,
            "actual_twh": cf,
            "headroom_twh": round(ceiling - gm, 3),
            "ceiling_limited": bool(ceiling > 0 and gm >= W2D_CEILING_FRAC * ceiling),
        }
        for k in cc_keys_y:
            bp = bench_y["plants"].get(k)
            if bp is None:
                continue
            c_ann = float(bp.get("c_ann", 0.0))
            pc = per_pt.get((int(k.split(":")[0]), "CC_REGULAR"), {}).get(
                "ceiling_twh", 0.0
            )
            if pc > 0 and c_ann > W2D_PLANT_CEIL_TOL * pc:
                defect_list.append(
                    {
                        "year": yr,
                        "key": k,
                        "name": bp.get("name"),
                        "c_ann": round(c_ann, 4),
                        "ceiling": round(pc, 4),
                        "ratio": round(c_ann / pc, 3),
                    }
                )
    out["w2d_ceilings"] = ceil_face
    out["w2d_actual_over_ceiling"] = sorted(
        defect_list, key=lambda r: -r["ratio"]
    )
    # W2e availability composition (class pmax-weighted mean availability).
    avail = {}
    for yr in YEARS:
        gens, fa = b1[yr][2]
        m = class_rows(gens, fa, "CC_REGULAR")
        w = fa.pmax[m]
        a = (fa.availability[m] * w[:, None]).sum() / (w.sum() * fa.availability.shape[1])
        avail[yr] = round(float(a), 4)
    bump = avail[2024] - 0.5 * (avail[2023] + avail[2025])
    out["w2e_mean_availability"] = avail
    out["w2e_2024_bump"] = round(float(bump), 4)
    out["w2e_line"] = (
        "2024-AVAILABILITY-IMPLICATED" if bump >= W2E_AVAIL_PP else "NOT AVAILABILITY"
    )
    return out


def w3_displacement(
    pay: dict,
    benches: dict[int, dict],
    b1: dict[int, tuple],
    hod_series: dict[str, np.ndarray],
    hr_meas: dict[str, dict],
):
    """W3a/b/c/d on the frozen bases."""
    out: dict = {}
    # W3a substitution identity, per year.
    sub = {}
    for yr in YEARS:
        ypay = pay["years"][str(yr)]
        mc, ac = monthly_delta(ypay, "CC_REGULAR")
        ms, as_ = monthly_delta(ypay, "ST_GAS")
        dcc = mc - ac
        dst = ms - as_
        corr = float(np.corrcoef(dcc, dst)[0, 1])
        cancel = float(
            abs(dcc.sum() + dst.sum()) / (abs(dcc.sum()) + abs(dst.sum()))
        )
        sub[yr] = {
            "corr": round(corr, 3),
            "cancel": round(cancel, 3),
            "cc_delta_mon": [round(float(x), 4) for x in dcc],
            "st_delta_mon": [round(float(x), 4) for x in dst],
        }
    out["w3a_by_year"] = sub
    f = sub[FOCUS_YEAR]
    out["w3a_line"] = (
        "SINGLE SUBSTITUTION DEFECT (2024)"
        if f["corr"] <= W3A_CORR_LINE and f["cancel"] <= W3A_CANCEL_LINE
        else "NOT A CLEAN SUBSTITUTION PAIR (2024)"
    )
    # W3b conduct: actual CC utilization in high-ST_GAS hours (FOCUS_YEAR).
    cc_a = hod_series["cc_actual_hourly"]
    st_a = hod_series["st_actual_hourly"]
    cc_m = hod_series["cc_model_hourly"]
    st_hi = st_a >= np.percentile(st_a, W3B_ST_PCTL)
    cc_ref = float(np.percentile(cc_a, W3B_CC_REF_PCTL))
    u_act = cc_a[st_hi] / cc_ref
    cc_m_ref = float(np.percentile(cc_m, W3B_CC_REF_PCTL))
    u_mod = cc_m[st_hi] / cc_m_ref
    med = float(np.median(u_act))
    if med <= W3B_HEADROOM_U:
        line = "ST_GAS RUNS WHILE ACTUAL CC HAS HEADROOM (out-of-merit conduct)"
    elif med >= W3B_MAXED_U:
        line = "ACTUAL CC EFFECTIVELY MAXED (model CC ceiling/level implicated)"
    else:
        line = "MIXED"
    out["w3b"] = {
        "n_high_st_hours": int(st_hi.sum()),
        "st_p75_mw": round(float(np.percentile(st_a, W3B_ST_PCTL)), 1),
        "actual_cc_utilization_median": round(med, 4),
        "actual_cc_utilization_p25": round(float(np.percentile(u_act, 25)), 4),
        "actual_cc_utilization_p75": round(float(np.percentile(u_act, 75)), 4),
        "model_cc_utilization_median": round(float(np.median(u_mod)), 4),
        "line": line,
    }
    # W3c physics crossing (HR ratio, model vs measured).
    gens, fa = b1[FOCUS_YEAR][2]
    ratios = {}
    for klass in ("CC_REGULAR", "ST_GAS"):
        m = class_rows(gens, fa, klass)
        ratios[klass] = {
            "model_hr_pw_median": round(
                weighted_median(fa.heat_rate[m], fa.pmax[m]), 3
            ),
            "measured_hr": hr_meas.get(klass, {}).get("hr"),
            "measured_n_plants": hr_meas.get(klass, {}).get("n"),
        }
    model_ratio = (
        ratios["ST_GAS"]["model_hr_pw_median"]
        / ratios["CC_REGULAR"]["model_hr_pw_median"]
    )
    meas_cc = ratios["CC_REGULAR"]["measured_hr"]
    meas_st = ratios["ST_GAS"]["measured_hr"]
    meas_ratio = (meas_st / meas_cc) if (meas_cc and meas_st) else None
    out["w3c"] = {
        "classes": ratios,
        "model_st_over_cc": round(model_ratio, 4),
        "measured_st_over_cc": round(meas_ratio, 4) if meas_ratio else None,
        "line": (
            "HR INPUTS NOT IMPLICATED"
            if meas_ratio and abs(model_ratio / meas_ratio - 1.0) <= W3C_RATIO_TOL
            else ("HR INPUTS IMPLICATED" if meas_ratio else "MEASURED HR UNAVAILABLE")
        ),
    }
    # W3d absorber table per year.
    absorber = {}
    for yr in YEARS:
        ypay = pay["years"][str(yr)]
        bench = benches[yr]
        gm = ypay["gmModel"]
        cf = bench["classFull"]
        cls = {}
        for c in sorted(set(gm) | set(cf)):
            a = cf.get(c)
            if a is None:
                continue
            cls[c] = round(float(gm.get(c, 0.0)) - float(a), 3)
        gas_fam = sum(v for c, v in cls.items() if c in GAS_SCORED)
        coal_fam = sum(v for c, v in cls.items() if c.startswith("COAL"))
        imp = ypay.get("nonfossilHr", {}).get("import", {})
        imp_d = (
            round(float(imp["mTwh"]) - float(imp["aTwh"]), 3)
            if imp.get("aTwh") is not None and imp.get("mTwh") is not None
            else None
        )
        nf = {}
        for panel, e in ypay.get("nonfossilHr", {}).items():
            if panel == "import" or e.get("aTwh") is None:
                continue
            nf[panel] = round(float(e["mTwh"]) - float(e["aTwh"]), 3)
        absorber[yr] = {
            "class_delta": cls,
            "gas_family_delta": round(gas_fam, 3),
            "coal_family_delta": round(coal_fam, 3),
            "import_delta": imp_d,
            "import_m_a": [imp.get("mTwh"), imp.get("aTwh")],
            "nonfossil_delta": nf,
            "import_implicated": bool(imp_d is not None and imp_d >= W3D_IMPORT_TWH),
        }
    out["w3d_by_year"] = absorber
    return out


def w4_family(pay: dict, benches: dict[int, dict]):
    """W4a/b on the frozen bases."""
    out = {}
    for yr in YEARS:
        ypay = pay["years"][str(yr)]
        bench = benches[yr]
        gm = ypay["gmModel"]
        cf = bench["classFull"]
        fam_m = sum(float(gm.get(c, 0.0)) for c in GAS_SCORED)
        fam_a = sum(float(cf.get(c, 0.0)) for c in GAS_SCORED if c in cf)
        d_cc = float(gm.get("CC_REGULAR", 0.0)) - float(cf.get("CC_REGULAR", 0.0))
        cf_gas_all = sum(
            float(cf.get(c, 0.0)) for c in (*GAS_CLASSES, "OTHER_FOSSIL") if c in cf
        )
        out[yr] = {
            "gas_family_model": round(fam_m, 3),
            "gas_family_actual": round(fam_a, 3),
            "gas_family_delta": round(fam_m - fam_a, 3),
            "cc_delta": round(d_cc, 3),
            "w4a_intra_family": bool(abs(fam_m - fam_a) < abs(d_cc)),
            "w4b_923sum_vs_930_gas": [
                round(cf_gas_all, 3),
                round(float(bench["e930"].get("gas", 0.0)), 3),
            ],
        }
    return out


# ------------------------------------------------------- measured heat rates
def measured_heat_rates(
    benches: dict[int, dict], b1_grp: dict[int, str]
) -> dict[str, dict]:
    """B4: per-class measured HR from CAMPD heatInput/grossLoad, guarded."""
    bench = benches[FOCUS_YEAR]
    wanted: dict[int, str] = {}
    for k, bp in bench["plants"].items():
        grp = bp.get("group")
        if grp not in ("CC_REGULAR", "ST_GAS"):
            continue
        c_ann = float(bp.get("c_ann", 0.0))
        e_ann = float(bp.get("e_ann", 0.0))
        if c_ann < W4B_HR_GUARD_TWH or e_ann <= 0:
            continue
        if abs(c_ann / e_ann - 1.0) > W4B_HR_GUARD_DEV:
            continue
        wanted[int(k.split(":")[0])] = grp
    heat: dict[int, float] = {}
    gross: dict[int, float] = {}
    for path in sorted(CAMPD_DIR.glob(f"*_{FOCUS_YEAR}.parquet")):
        df = pd.read_parquet(
            path, columns=["facilityId", "grossLoad", "heatInput"]
        )
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[df["facilityId"].isin(wanted)]
        if df.empty:
            continue
        g = df.groupby("facilityId")[["grossLoad", "heatInput"]].sum()
        for fid, row in g.iterrows():
            heat[int(fid)] = heat.get(int(fid), 0.0) + float(row["heatInput"])
            gross[int(fid)] = gross.get(int(fid), 0.0) + float(row["grossLoad"])
    out: dict[str, dict] = {}
    for klass in ("CC_REGULAR", "ST_GAS"):
        hrs = []
        w = []
        for fid, grp in wanted.items():
            if grp != klass:
                continue
            if gross.get(fid, 0.0) > 0 and heat.get(fid, 0.0) > 0:
                hrs.append(heat[fid] / gross[fid])
                w.append(gross[fid])
        if hrs:
            out[klass] = {
                "hr": round(
                    weighted_median(np.asarray(hrs), np.asarray(w)), 3
                ),
                "n": len(hrs),
            }
        else:
            out[klass] = {"hr": None, "n": 0}
    return out


# ------------------------------------------------------------- hourly series
def hourly_series(pay: dict, benches: dict[int, dict]) -> dict[str, np.ndarray]:
    """Class hourly MW: model from B2 sidecar, actual from B3 campd blobs."""
    disp = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{FOCUS_YEAR}.parquet")
    disp = disp[disp["pass"].astype(str).str.upper() == "P1"]
    cc_m = (
        disp[disp["klass"] == "CC_REGULAR"].sort_values("hour")["mw"].to_numpy()
    )
    bench = benches[FOCUS_YEAR]
    cc_a = np.zeros(8760)
    st_a = np.zeros(8760)
    for k, bp in bench["plants"].items():
        grp = bp.get("group")
        if grp not in ("CC_REGULAR", "ST_GAS"):
            continue
        blob = bp.get("campd")
        npl = float(bp.get("npl") or 0.0)
        if not blob or npl <= 0:
            continue
        mw = blob_mw(blob, npl)
        if grp == "CC_REGULAR":
            cc_a += mw
        else:
            st_a += mw
    return {
        "cc_model_hourly": cc_m,
        "cc_actual_hourly": cc_a,
        "st_actual_hourly": st_a,
    }


def hod_profile(x: np.ndarray) -> np.ndarray:
    """Mean MW by hour-of-day (fixed-standard-time clock, both bases)."""
    return x[: 8760 // 24 * 24].reshape(-1, 24).mean(axis=0)


# ------------------------------------------------------------------- drivers
def satisfiability() -> None:
    """Verify every basis resolves; print counts only, no witness aggregates."""
    pay = load_payload()
    for yr in YEARS:
        assert str(yr) in pay["years"], f"payload missing {yr}"
        b = load_bench(yr)
        assert "CC_REGULAR" in b["classFull"], f"bench {yr} missing CC"
    ypay = pay["years"][str(FOCUS_YEAR)]
    assert "CC_REGULAR" in ypay["volErr"] and "ST_GAS" in ypay["volErr"]
    b = load_bench(FOCUS_YEAR)
    k, bp = next(
        (k, p) for k, p in b["plants"].items() if p.get("group") == "CC_REGULAR"
    )
    mp = ypay["plants"][k]
    recon = blob_mw(mp["m"], float(bp["npl"])).sum() / 1e6
    assert abs(recon - float(mp["m_ann"])) < 0.01, "payload blob decode identity"
    recon_a = blob_mw(bp["campd"], float(bp["npl"])).sum() / 1e6
    assert abs(recon_a - float(bp["c_ann"])) < 0.01, "bench blob decode identity"
    assert cc_duct_peaking_pct(), "duct map resolves"
    files = list(CAMPD_DIR.glob(f"*_{FOCUS_YEAR}.parquet"))
    assert files, "CAMPD hourly parquets present"
    print(
        f"SATISFIABLE: payload years OK, blob identities OK "
        f"(plant {k}: m {recon:.4f}~{mp['m_ann']}, c {recon_a:.4f}~{bp['c_ann']}), "
        f"duct map OK, {len(files)} CAMPD files"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="miso-197 phase-0 census")
    ap.add_argument("--satisfiability", action="store_true")
    args = ap.parse_args()
    if args.satisfiability:
        satisfiability()
        return

    pay = load_payload()
    benches = {yr: load_bench(yr) for yr in YEARS}
    b1: dict[int, tuple] = {}
    for yr in YEARS:
        gens, fa = build(yr)
        per_pt, grp = plant_tables(gens, fa)
        b1[yr] = (per_pt, grp, (gens, fa))

    hod = hourly_series(pay, benches)
    hr_meas = measured_heat_rates(benches, b1[FOCUS_YEAR][1])

    ypay24 = pay["years"][str(FOCUS_YEAR)]
    record = {
        "probe": "miso197_cc_overdispatch_phase0",
        "run_id": RUN_ID,
        "focus_year": FOCUS_YEAR,
        "w1": w1_where(
            ypay24,
            benches[FOCUS_YEAR],
            hod_profile(hod["cc_model_hourly"]),
            hod_profile(hod["cc_actual_hourly"]),
        ),
        "w2": w2_whose(pay, benches, b1, cc_duct_peaking_pct()),
        "w3": w3_displacement(pay, benches, b1, hod, hr_meas),
        "w4": w4_family(pay, benches),
    }
    OUT.write_text(json.dumps(record, indent=1) + "\n")
    print(f"census written -> {OUT}")
    for w in ("w1", "w2", "w3", "w4"):
        sec = record[w]
        lines = {
            k: v
            for k, v in (sec.items() if isinstance(sec, dict) else [])
            if k.endswith("_line") or k.endswith("line")
        }
        print(w, lines if lines else "(tables)")


if __name__ == "__main__":
    main()
