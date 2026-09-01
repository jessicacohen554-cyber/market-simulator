"""miso-196 phase-0 census: ``cc_outage_derate_from_top`` in MISO (zero-solve).

Charter: the FINDING-miso195 §6 named successor — the APPLICATION-SHAPE leg of
the outage-overlay family, registered as a literal sub-scalar on the
``campd_outage_windows`` matrix row (mechanism-matrix.js row def, xiso-3
sub-scalar convention). NO new ``ScenarioConfig`` field, NO new matrix row.
``cc_outage_derate_from_top`` (``scenarios.py:11908``, bool, default False) is
ARMED on the CAISO and PJM designated keepers and FALSE on MISO's
(``results/calibration/miso191_bax_B/run_config.json``). Seam:
``src/market_sim/data/fleet/arrays.py::_apply_outage_overlays`` (:1050, the
reallocation block at :2251).

WHAT THE SEAM DOES (read from the shipped code before this rule froze, no
census quantity computed): for every ``plant_group == "CC_REGULAR"`` plant with
>= 2 LP tranches, the plant's hourly available MW — UNCHANGED IN TOTAL — is
re-stacked bottom-up in heat-rate order (``bounds_i = clip(avail_mw -
cum_below_i, 0, caps_i)``), so the cheap committed block keeps its level and
the expensive duct-fire / high-econ end is truncated first. The default
(False) scales every tranche by the same factor. CC_CHP is NOT in the
population (the loop gates on ``CC_REGULAR``); single-tranche plants are a
no-op by construction.

DECLARED ADVERSE FACE (stated in the charter, restated here BEFORE any
measurement): the reallocation makes MORE cheap and LESS expensive CC
capability available in exactly the hours it fires. miso-193 measured that
shrinking the expensive CC top band moves C3a-2025 DOWN (-12.3405 ->
-13.3304); that transfers as SHAPE evidence only (miso-193 REMOVED MW, this
lever REALLOCATES them), but the direction is the same and C3a-2025 is the
keeper's SOLE failing criterion. This is a rule-1 [R-STRUCT] case: the lever is
adjudicated on STRUCTURE (conduct witness, marginal identity, D-1 shape, the
C8 legs) and NEVER on whether it improves the residual.

FROZEN ADJUDICATION RULE (ex ante; the miso-191/193/195 mis-freeze lessons
applied — every witness reads the EXACT basis the seam reads, every line is a
RELATION rather than a level constant wherever the data can supply one, and
mechanical satisfiability of every basis was verified on the control build
before this rule was pushed):

BASES
  B1  The load-bearing TRANCHE fleet build under the keeper's reconstructed
      ``ScenarioConfig``, using the SHIPPED functions rather than a
      re-assembly: ``load_retired_within_window`` (the keeper arms
      ``partial_plant_exit_carry`` and ``retiree_vintage_status_scope``) ->
      ``load_or_synthesize_bins`` -> ``bins_to_fleet`` ->
      ``generators_to_fleet_arrays(config=cfg, iso="MISO", year=y)`` — for
      y in {2023, 2024, 2025}, run TWO ways: DEFAULT
      (``cc_outage_derate_from_top=False``, the keeper as recorded) and FROMTOP
      (``=True``, the single delta, nothing else changed). Yields
      ``availability`` (n_gen x 8760), ``min_gen``, ``pmax``, ``plant_code``,
      ``plant_group``, ``heat_rate`` and the tranche band, which is the LAST
      space-separated token of the generator's ``name`` (``... committed`` /
      ``... econ<N>`` / ``... peak``), the miso-193 §2 band basis. A THIRD
      build, STATBASE (``outage_source="statistical"``, 2025 only, declared),
      supplies the W1 decomposition counterfactual.
      BASIS CORRECTION, DISCLOSED (made BEFORE this rule was frozen or pushed,
      by the ``--satisfiability`` pass this probe exists to run): an earlier
      draft read the RAW per-unit fleet (``load_fleet_from_csv`` straight into
      ``generators_to_fleet_arrays``), whose MISO CC_REGULAR rows are physical
      SIBLING UNITS sharing one heat rate — not the offer-curve tranches the
      solve builds under ``use_campd_bins=True`` / ``plant_level_fleet=True``.
      The satisfiability pass surfaced it (no band suffix resolved) and the
      basis is the shipped tranche path above. NO adjudicating quantity was
      computed on the wrong basis.
  B2  The keeper's committed P1 hourly sidecars ``hourly/system_<y>.parquet``
      (carry-zone demand; the scarce set S = the top-200 demand hours, the
      miso-195 S definition, reused verbatim) and
      ``hourly/class_hourly_<y>.parquet`` (CC_REGULAR model dispatch).
  B3  MISO's own measured record: the committed unit-outage extract the armed
      overlay reads, ``data/raw/campd-unit-outages-MISO.csv`` (carries
      ``peer_units_online`` / ``total_units_at_plant``, so a PARTIAL plant
      outage is identifiable without inventing one), joined to the hourly CAMPD
      unit-level parquets ``data/raw/campd-unit-level/*_<y>.parquet``, scanned
      per file and filtered to the facilities the MISO extract names (rule 25:
      MISO's numbers from MISO's record; no CAISO/PJM parameter or verdict
      transfers).
  B4  The keeper's committed verdict scorecard
      (``calibration_verdict.py --run-id 2026-08-30-miso-191-bexit --json``),
      C1 ``fuelmix`` records. DISCLOSED: the C1 CC_REGULAR / ST_GAS records
      were read during Ask A, BEFORE this freeze — they are the KEEPER's
      published state (the charter itself quotes them), not a quantity about
      this lever. What is frozen here is the RELATION, never the number.
      Also disclosed from the same pre-freeze read: the 2025 CC_REGULAR C1
      record is SKIPPED (preliminary EIA-923 vintage), so 2025 carries no C1
      band; W4 reports N/A for it rather than a spurious pass, and 2023/2024
      are the banded years the kill can fire in.

POPULATION P = CC_REGULAR LP rows at plants carrying >= 2 tranches — exactly
the rows the seam's ``cc_by_plant`` loop reallocates.

WITNESSES (all reported at full magnitude whichever way they fall)

  W1 LIVENESS AND SCOPE. Per year: the share of P plant-hours in which the
     DEFAULT and FROMTOP tranche-availability vectors differ (max abs diff >
     1e-9), over the full year and within S.
     LINE: LIVE iff differing plant-hours >= 25% of P plant-hours WITHIN S, in
     every year. NOT LIVE => the mechanism is inert on MISO's fleet: mint the
     cell from the census, zero-solve, STOP.
     REPORTED, NOT GATED — the provenance split: the share of the reallocated
     capability attributable to the MEASURED CAMPD overlay vs the STATISTICAL
     WEFOR/POF/maintenance base (DEFAULT vs STATBASE plant available MW, 2025).
     Its purpose is honesty about the row def's own justification, which is
     stated as a partial-OUTAGE conduct rule ("a 2x1 CC with one train out").
     It is NOT a kill: an expected-availability derate also loads the cheap
     tranches first in expectation, so the split cuts both ways, and this
     session will not invent a bar for a question its own evidence cannot
     settle. If the measured share is small the finding SAYS SO, at full
     magnitude, on the record.

  W2 THE DRAG (the C1/C8 exposure, in MW). Per year over P: the DEFAULT ->
     FROMTOP change in available MW by tranche band (band read from the generator
     ``name`` suffix: ``mustrun`` / ``committed`` / ``econ<N>`` / ``peak``,
     the miso-193 §2 band basis), as a year mean and an S mean; and the change in ``min_gen``
     (the hard forced floor), as MW and TWh.
     LINE: MATERIAL iff the mean over S of the summed positive band movement
     is >= 1% of the CC_REGULAR class pmax, in every year. Below => the lever
     is provably ~inert in MISO: mint I for this cell's application leg
     zero-solve (the miso-179 precedent), stamp the cell, STOP.

  W3 THE CONDUCT WITNESS, on MISO's own record (rule 25). The mechanism's
     justification is that a partially-out CC plant runs its SURVIVING
     capability near full load instead of backing down proportionally. Test:
     over 2023-2025, for CC plants in the model's own CC_REGULAR population,
     take the B3 extract's PARTIAL windows (``peer_units_online`` >= 1, i.e. at
     least one unit out and at least one still online) and measure the
     surviving units' own capacity factor (``grossLoad`` / that unit's
     ``unit_capacity_mw``) inside those windows, against the SAME units'
     capacity factor in that plant's fully-available hours (no unit of the
     plant inside any window of the extract).
     LINE (RELATIONAL, derived from the data itself, no level constant): the
     two forms make opposite predictions — FROMTOP predicts the surviving
     units are unaffected (ratio ~ 1.0); strict pro-rata predicts the plant's
     loading scales with its availability fraction (ratio ~ f, the measured
     mean surviving-capacity share of plant capacity in those windows). The
     bar is the MIDPOINT: the conduct holds iff
     mean CF_surv(PARTIAL) / mean CF_same-units(FULL) >= (1.0 + f) / 2.
     FAILS => MISO's own record contradicts the mechanism's conduct premise
     HERE; the arm is not chartered on that justification, the cell is stamped
     with the contradiction, STOP.

  W4 THE C1 HEADROOM ARITHMETIC, ex ante (the miso-193 K-1 precedent, spent
     BEFORE the solve rather than after it). From B4, per year:
     headroom_TWh = tol_TWh - (model - actual) for CC_REGULAR. From B1/B2:
     the STRICT LOWER BOUND on the arm's CC_REGULAR energy increase through
     the forced-floor channel — sum over hours in which the keeper's own
     CC_REGULAR class dispatch equals its class-aggregate ``min_gen`` (within
     0.5 MW) of the positive part of the min_gen change. In such an hour every
     plant sits exactly at its floor, so a floor increase is realised 1:1;
     outside them it may or may not be, which is why only the binding hours
     enter the bound.
     LINE (pre-registered kill): if that lower bound >= headroom_TWh in ANY of
     2023/2024/2025, the K-1 C1 PASS->FAIL flip is ARITHMETICALLY GUARANTEED
     before a solve is spent — REFUTE at phase 0, no A/B.
     REPORTED, NOT GATED: the same ladder for ST_GAS 2024 (the adjacent second
     kill pair, -8.08 at miso-193's arm), and the floor channel's MAXIMUM
     (the unrestricted positive min_gen change), which is an upper bound on
     that channel and is NOT a bound on the economic channel.

  W5 SINGLE-DELTA IDENTITY (control check). The FROMTOP build must differ from
     DEFAULT ONLY on P rows (zero non-P rows move), and each P plant's total
     available MW must be preserved hour by hour to 1e-6 relative — the seam
     claims a REALLOCATION, and a violation would make it a removal.
     A violation is a stop-the-line BUG finding, not a lever adjudication.

  CHARTER_AB = W1(live) AND W2(material) AND W3(conduct) AND W4(clear) AND
  W5(clean). Any one failing refutes the charter at phase 0.

DIRECTIONAL PREREG (declared before any adjudicating quantity was computed)
  - C3a-2025 moves DOWN (more negative than -12.3405%), confidence 0.75.
    Mechanism: FROMTOP strictly raises cheap CC capability and strictly lowers
    expensive CC capability in every hour it fires, softening the top of the
    supply curve exactly where 2025's scarce hours clear.
  - MATERIALITY, honest to the lever's STRUCTURAL justification: this lever's
    yardstick is the marginal-unit identity (FINDING-miso178 Delta-1), the D-1
    diurnal shape and the C8 legs — NOT pp of C3a. NO pp threshold is
    pre-registered as a success criterion and no C3a improvement would ever be
    claimed as its justification (rule 1 [R-STRUCT]). The pp face is reported
    at full magnitude and routed by the posture below.

ADJUDICATION POSTURE, PRE-COMMITTED (rule 1; the miso-193 precedent)
  - Clean structural gates + an adverse C3a face => OWNER ESCALATION. Never
    self-promotion, never silent rejection on fit. The miso-193 standing owner
    posture directive ("structural-integrity gain may carry a keeper even where
    gates regress") is NOT assumed to carry here: miso-193 measured that it did
    not carry its own cap leg, and this session does not extend it.
  - PRE-REGISTERED KILLS on the A/B, if chartered: any criterion PASS->FAIL
    flip (C1 2024 CC_REGULAR named ex ante; C1 2024 ST_GAS the adjacent
    second), C3b NRMSE through 0.20, any NEW D-4 off-window binding, or a DOF
    n_residual increase.

Rule 21 [R-DOF]: this probe has ZERO free parameters. The 25% / 1% / 1e-9 /
0.5 MW lines and the (1+f)/2 midpoint are ex-ante census adjudication
thresholds, not solve inputs. Rule 22: 2023-2025 only — MISO holds neither a
``complete`` nor a ``final`` marker and the holdout freeze is active; no
out-of-training year is read by any basis.

AMENDMENT 1 (post-freeze, DISCLOSED — the miso-191 precedent: a frozen witness
that cannot fire clean is amended in the open, never silently). W5 fired BUG on
2023 ALONE (6 non-P rows moved, worst relative total-MW error 0.100) while 2024
and 2025 read CLEAN at 6e-16. Diagnosis: THE LEVER IS NOT THE CAUSE. A control
identity — the SAME config built twice — shows the FIRST fleet build in a
process differs from every later one on 58 rows, so the frozen W5 compared a
cold DEFAULT build against a warm FROMTOP build and attributed the difference
to the single delta.

  ROOT CAUSE, in shipped code: ``_CC_PMAX_RECONCILED_PLANTS``
  (``data/fleet/eia860.py:776``, written at :875) is a MODULE-LEVEL,
  LAST-WRITER-WINS global keyed only by ISO. Every fleet-record load writes it
  from its own record set, including narrow auxiliary loads whose record set
  legitimately reconciles nothing: the trace shows ``_iso_plant_capacity`` ->
  ``load_retired_within_window`` writing ``MISO=[]`` AFTER the main
  ``load_fleet_from_csv`` wrote the correct seven plants. ``_iso_plant_capacity``
  is cached, so that clobbering call happens on the FIRST build only. The set is
  then read by ``_basis_aware_suppresses`` (``arrays.py:463``) under the armed
  ``summer_derate_basis_aware``, which decides which plants KEEP the flat summer
  ambient derate — so whether seven MISO CC plants are derated depends on
  lru_cache warm-up order rather than on data.

  THE AMENDMENT: ``main()`` and ``satisfiability()`` perform one WARM-UP build
  before any witness is measured, so every arm is compared on the settled state
  and each witness reads the LEVER ALONE. No frozen line, basis, population or
  prereg is changed. The defect itself is measured and recorded in its own
  ``W5_defect`` block (cold build vs warm build, same config) rather than left
  as an unexplained W5 failure — it is reported at full magnitude as this
  session's incidental finding, and it is NOT this session's to fix (a
  solve-affecting core change that would re-base a designated keeper needs its
  own charter).

Output: ``results/calibration/_miso196_outage_derate_from_top_phase0.json``.
Reproduce: ``python3 scripts/probes/_miso196_outage_derate_from_top_phase0.py``
(``--satisfiability`` runs the pre-freeze basis-reachability check only, which
prints shapes and booleans and NO adjudicating quantity).
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import re
import subprocess
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

ISO = "MISO"
YEARS = (2023, 2024, 2025)
KEEPER = _REPO / "results" / "calibration" / "miso191_bax_B"
RUN_ID = "2026-08-30-miso-191-bexit"
OUT = _REPO / "results" / "calibration" / "_miso196_outage_derate_from_top_phase0.json"
EXTRACT = _REPO / "data" / "raw" / "campd-unit-outages-MISO.csv"
CAMPD_DIR = _REPO / "data" / "raw" / "campd-unit-level"

# The miso-195 carry-zone set and scarce-set definition, reused verbatim.
CARRY = ("MISO-Central", "MISO-North", "MISO-WestNorth", "MISO-East", "MISO-South")
S_TOP_HOURS = 200

# Ex-ante census adjudication thresholds (docstring; not solve inputs, rule 21).
W1_LIVE_LINE = 0.25
W2_MATERIAL_LINE = 0.01
DIFF_EPS = 1e-9
BIND_TOL_MW = 0.5


# ---------------------------------------------------------------- keeper config
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


def build(year: int, **overrides: object):
    """Load the keeper's load-bearing TRANCHE fleet for ``year`` (basis B1).

    The shipped path the backcast itself takes:
    ``load_retired_within_window`` -> ``load_or_synthesize_bins`` ->
    ``bins_to_fleet`` -> ``generators_to_fleet_arrays``. Non-thermal rows are
    irrelevant to the seam by construction (its loop gates on CC_REGULAR and
    reallocates only within a plant), so the thermal tranche fleet is the
    exact and complete basis for every witness below.
    """
    cfg = keeper_config(year, **overrides)
    iso_cfg = get_iso_config(ISO)
    _scoped = bool(getattr(cfg, "retiree_vintage_status_scope", False)) or bool(
        getattr(cfg, "partial_plant_exit_carry", False)
    )
    retired = load_retired_within_window(
        ISO,
        iso_cfg,
        year=int(cfg.weather_year) if _scoped else None,
        vintage_status_scope=bool(getattr(cfg, "retiree_vintage_status_scope", False)),
        partial_plant_exit_carry=bool(getattr(cfg, "partial_plant_exit_carry", False)),
    )
    bins = load_or_synthesize_bins(cfg, ISO, iso_cfg, retired)
    assert bins is not None and not bins.empty, "premise: MISO takes the bins path"
    zones = [z.name for z in iso_cfg.zones]
    gens, _ = bins_to_fleet(bins, zones, cfg)
    fa = generators_to_fleet_arrays(gens, zones, 8760, iso=ISO, config=cfg, year=year)
    return gens, fa


def band_of(name: str) -> str:
    """Map an LP row's ``name`` suffix to its offer-curve tranche band."""
    suffix = str(name).rsplit(" ", 1)[-1]
    if suffix.startswith("peak"):
        return "peak"
    if suffix.startswith("econ"):
        return "econ"
    if suffix.startswith("committed"):
        return "committed"
    if suffix.startswith("mustrun"):
        return "mustrun"
    return "other"


def population(gens) -> tuple[np.ndarray, dict[int, list[int]]]:
    """P = CC_REGULAR rows at plants with >= 2 tranches (the seam's own gate)."""
    by_plant: dict[int, list[int]] = {}
    for i, g in enumerate(gens):
        if g.plant_group == "CC_REGULAR" and int(g.plant_code) > 0:
            by_plant.setdefault(int(g.plant_code), []).append(i)
    multi = {p: ix for p, ix in by_plant.items() if len(ix) >= 2}
    mask = np.zeros(len(gens), dtype=bool)
    for ix in multi.values():
        mask[ix] = True
    return mask, multi


def scarce_hours(year: int) -> np.ndarray:
    """S = the top-200 carry-zone demand hours of the keeper's own P1 sidecar."""
    sysdf = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
    sysdf = sysdf[sysdf["pass"].astype(str).str.upper() == "P1"]
    sysdf = sysdf[sysdf["zone"].isin(CARRY)]
    dem = (
        sysdf.pivot_table(index="hour", columns="zone", values="demand", aggfunc="sum")
        .reindex(range(8760))
        .fillna(0.0)
        .to_numpy()
        .sum(axis=1)
    )
    return np.argsort(dem)[-S_TOP_HOURS:]


def cc_class_dispatch(year: int) -> np.ndarray | None:
    """CC_REGULAR P1 hourly MW from the keeper's committed class sidecar."""
    p = KEEPER / "hourly" / f"class_hourly_{year}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    if "pass" in df.columns:
        df = df[df["pass"].astype(str).str.upper() == "P1"]
    col = next(c for c in ("klass", "plant_group", "class") if c in df.columns)
    df = df[df[col].astype(str) == "CC_REGULAR"]
    val = next(c for c in ("mw", "generation_mwh", "mwh") if c in df.columns)
    return (
        df.groupby("hour")[val].sum().reindex(range(8760)).fillna(0.0).to_numpy()
    )


def c1_records() -> list[dict]:
    """B4: the keeper's committed C1 fuelmix records (verdict --json)."""
    res = subprocess.run(
        [sys.executable, str(_REPO / "scripts" / "calibration_verdict.py"),
         "--run-id", RUN_ID, "--json"],
        capture_output=True, text=True, cwd=str(_REPO), check=False,
    )
    # A non-zero exit encodes the NOT-YET determination, not a failure.
    assert res.stdout.strip(), res.stderr[-2000:]
    return json.loads(res.stdout)["criteria"]["fuelmix"]["records"]


def tol_twh(rec: dict) -> float | None:
    """Parse the C1 band width in TWh out of the record's own tol string.

    ``None`` where the record carries no band — the 2025 CC_REGULAR record is
    SKIPPED on the preliminary EIA-923 vintage, so that year has no C1 band to
    blow and W4 reports N/A there rather than a spurious pass.
    """
    m = re.search(r"=\s*±\s*([0-9.]+)\s*TWh", str(rec.get("tol") or ""))
    return float(m.group(1)) if m else None


# ------------------------------------------------------------------ W3 conduct
def w3_conduct() -> dict:
    """MISO's own CAMPD record: surviving-unit loading in PARTIAL windows."""
    ex = pd.read_csv(EXTRACT, parse_dates=["outage_start", "outage_end"])
    ex = ex[ex["plant_group"].astype(str).str.startswith("CC")]
    ex = ex[
        (ex["outage_start"].dt.year >= min(YEARS))
        & (ex["outage_start"].dt.year <= max(YEARS))
    ]
    want = {int(f) for f in ex["facility_id"].unique()}
    frames = []
    for y in YEARS:
        for path in sorted(CAMPD_DIR.glob(f"*_{y}.parquet")):
            df = pd.read_parquet(
                path, columns=["facilityId", "unitId", "date", "hour", "grossLoad"]
            )
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df.dropna(subset=["facilityId"])
            df["facilityId"] = df["facilityId"].astype(int)
            df = df[df["facilityId"].isin(want)]
            if not df.empty:
                frames.append(df)
    if not frames or ex.empty:
        return {"status": "NO-DATA", "n_windows": int(len(ex))}
    cems = pd.concat(frames, ignore_index=True)
    cems["unitId"] = cems["unitId"].astype(str)
    cems["ts"] = pd.to_datetime(cems["date"]) + pd.to_timedelta(cems["hour"], unit="h")

    cap = (
        ex.groupby(["facility_id", "unit_id"])["unit_capacity_mw"].max().to_dict()
    )
    plants = sorted({int(f) for f in ex["facility_id"].unique()})
    cems = cems[cems["facilityId"].isin(plants)]
    if cems.empty:
        return {"status": "NO-DATA", "n_windows": int(len(ex))}

    # Per plant: PARTIAL hours (>=1 unit inside a window with peers online) and
    # FULL hours (no unit of the plant inside any window).
    part_num = part_den = full_num = full_den = 0.0
    part_hours = full_hours = 0
    surv_cap = plant_cap = 0.0
    n_part_windows = 0
    for pid, grp in ex.groupby("facility_id"):
        pid = int(pid)
        c = cems[cems["facilityId"] == pid]
        if c.empty:
            continue
        units = sorted(c["unitId"].unique())
        idx = pd.DatetimeIndex(sorted(c["ts"].unique()))
        if idx.empty:
            continue
        out = pd.DataFrame(False, index=idx, columns=units)
        for _, r in grp.iterrows():
            u = str(r["unit_id"])
            if u not in out.columns:
                continue
            out.loc[
                (out.index >= r["outage_start"]) & (out.index <= r["outage_end"]), u
            ] = True
        n_out = out.sum(axis=1)
        partial = (n_out >= 1) & (n_out < len(units))
        full = n_out == 0
        if not partial.any():
            continue
        n_part_windows += int((grp["peer_units_online"] > 0).sum())
        wide = c.pivot_table(
            index="ts", columns="unitId", values="grossLoad", aggfunc="sum"
        ).reindex(idx)
        caps = np.array(
            [float(cap.get((pid, u), np.nan)) for u in wide.columns], dtype=float
        )
        ok = np.isfinite(caps) & (caps > 0)
        if not ok.any():
            continue
        wide = wide.loc[:, wide.columns[ok]]
        caps = caps[ok]
        outw = out.reindex(columns=wide.columns, fill_value=False)
        surv = (~outw) & partial.to_numpy()[:, None]
        cf = wide.to_numpy() / caps[None, :]
        cf = np.where(np.isfinite(cf), cf, np.nan)
        sm = surv.to_numpy()
        if sm.any():
            part_num += float(np.nansum(np.where(sm, cf, 0.0)))
            part_den += float(np.sum(sm & np.isfinite(cf)))
            part_hours += int(partial.sum())
            # f = surviving share of plant capacity in those windows
            surv_cap += float((sm * caps[None, :]).sum())
            plant_cap += float(sm.any(axis=1).sum() * caps.sum())
        fm = full.to_numpy()[:, None] & np.ones_like(sm, dtype=bool)
        # same units, restricted to those that ever survive a partial window
        keep = sm.any(axis=0)
        fm = fm & keep[None, :]
        if fm.any():
            full_num += float(np.nansum(np.where(fm, cf, 0.0)))
            full_den += float(np.sum(fm & np.isfinite(cf)))
            full_hours += int(full.sum())
    if part_den == 0 or full_den == 0:
        return {"status": "NO-DATA", "n_windows": int(len(ex))}
    cf_part = part_num / part_den
    cf_full = full_num / full_den
    f = surv_cap / plant_cap if plant_cap > 0 else float("nan")
    bar = (1.0 + f) / 2.0
    ratio = cf_part / cf_full if cf_full > 0 else float("nan")
    return {
        "status": "PASS" if ratio >= bar else "FAIL",
        "cf_surviving_partial": cf_part,
        "cf_same_units_full": cf_full,
        "ratio": ratio,
        "f_surviving_capacity_share": f,
        "bar_midpoint": bar,
        "partial_hours": part_hours,
        "full_hours": full_hours,
        "n_partial_windows": n_part_windows,
        "n_windows_cc": int(len(ex)),
    }


# ----------------------------------------------------------------------- driver
def satisfiability() -> None:
    """Pre-freeze basis-reachability check: shapes and booleans only."""
    build(2025)  # Amendment 1 warm-up (see the docstring)
    gens, fa = build(2025)
    mask, multi = population(gens)
    print("SAT B1 availability shape", fa.availability.shape)
    print("SAT B1 min_gen present", fa.min_gen is not None)
    print("SAT P non-empty", bool(mask.any()), "| multi-tranche plants exist",
          len(multi) > 0)
    bands = sorted({band_of(g.name) for g, m in zip(gens, mask) if m})
    print("SAT band suffixes resolvable", bands, "| unresolved 'other' present",
          "other" in bands)
    print("SAT B2 system sidecar", (KEEPER / "hourly" / "system_2025.parquet").exists(),
          "| class sidecar",
          (KEEPER / "hourly" / "class_hourly_2025.parquet").exists())
    print("SAT B2 scarce set size", len(scarce_hours(2025)))
    print("SAT B2 class dispatch reachable", cc_class_dispatch(2025) is not None)
    print("SAT B3 extract exists", EXTRACT.exists(), "| campd dir", CAMPD_DIR.exists())
    print("SAT B3 unit-level parquets in span",
          sum(len(list(CAMPD_DIR.glob(f"*_{y}.parquet"))) for y in YEARS))
    _ex = pd.read_csv(EXTRACT, parse_dates=["outage_start", "outage_end"])
    _cc = _ex[_ex["plant_group"].astype(str).str.startswith("CC")]
    print("SAT B3 CC windows present", not _cc.empty,
          "| partial windows present", bool((_cc["peer_units_online"] > 0).any()))
    recs = c1_records()
    ccr = [r for r in recs if r["key"] == "CC_REGULAR"]
    print("SAT B4 C1 CC_REGULAR records", len(ccr),
          "| banded years", sorted(r["year"] for r in ccr if tol_twh(r)),
          "| unbanded (SKIPPED) years",
          sorted(r["year"] for r in ccr if not tol_twh(r)))
    print("SAT ALL BASES REACHABLE — no adjudicating quantity computed.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--satisfiability", action="store_true")
    args = ap.parse_args()
    if args.satisfiability:
        satisfiability()
        return

    rec: dict = {
        "session": "miso-196",
        "keeper": RUN_ID,
        "bundle": str(KEEPER.relative_to(_REPO)),
        "mechanism": "cc_outage_derate_from_top",
        "years": list(YEARS),
        "lines": {
            "W1_live": W1_LIVE_LINE,
            "W2_material": W2_MATERIAL_LINE,
            "W4": ("floor-channel lower bound >= C1 headroom in any BANDED "
                   "year => refute; an unbanded (SKIPPED) C1 record has no "
                   "band to blow and reports N/A"),
        },
        "W1": {}, "W2": {}, "W4": {}, "W5": {},
    }
    c1 = c1_records()

    # Amendment 1: one warm-up build, then measure the defect it exposes
    # (cold build vs warm build, SAME config — the lever is not involved).
    import market_sim.data.fleet.eia860 as _e860

    _g_cold, _fa_cold = build(2023)
    _recon_cold = sorted(_e860._CC_PMAX_RECONCILED_PLANTS.get(ISO, ()))
    _g_warm, _fa_warm = build(2023)
    _recon_warm = sorted(_e860._CC_PMAX_RECONCILED_PLANTS.get(ISO, ()))
    _ac, _aw = _fa_cold.availability, _fa_warm.availability
    _rows = np.where(np.abs(_ac - _aw).max(axis=1) > DIFF_EPS)[0]
    _hrs = np.where(np.abs(_ac - _aw).max(axis=0) > DIFF_EPS)[0]
    _dmw = (_ac - _aw) * _fa_warm.pmax[:, None]
    _pl = sorted({int(_g_warm[i].plant_code) for i in _rows})
    rec["W5_defect"] = {
        "what": (
            "_CC_PMAX_RECONCILED_PLANTS (data/fleet/eia860.py:776, written "
            ":875) is a last-writer-wins module global; a cached auxiliary "
            "load (_iso_plant_capacity -> load_retired_within_window) "
            "clobbers it to empty on the FIRST build only, and "
            "_basis_aware_suppresses (arrays.py:463) then suppresses the flat "
            "summer ambient derate for plants that should KEEP it"
        ),
        "reconciled_set_after_cold_build": _recon_cold,
        "reconciled_set_after_warm_build": _recon_warm,
        "rows_affected": int(len(_rows)),
        "plants_affected": _pl,
        "classes_affected": sorted({_g_warm[i].plant_group for i in _rows}),
        "hours_affected": int(len(_hrs)),
        "hour_span": [int(_hrs.min()), int(_hrs.max())] if len(_hrs) else None,
        "pmax_identical": bool(
            np.abs(_fa_cold.pmax - _fa_warm.pmax).max() < DIFF_EPS
        ),
        "max_availability_delta": float(np.abs(_ac - _aw).max()),
        "cold_minus_warm_capability_GWh": float(_dmw[_rows].sum() / 1e3),
        "cold_minus_warm_mean_MW_over_affected_hours": (
            float(_dmw[_rows][:, _hrs].sum(axis=0).mean()) if len(_hrs) else 0.0
        ),
        "affected_plant_pmax_MW": float(
            sum(
                _fa_warm.pmax[i]
                for i in range(len(_g_warm))
                if int(_g_warm[i].plant_code) in _pl
            )
        ),
        "note": (
            "incidental finding, reported at full magnitude; NOT this "
            "session's to fix (solve-affecting core change, own charter)"
        ),
    }
    del _fa_cold, _fa_warm, _ac, _aw, _dmw

    for year in YEARS:
        gens, fa_def = build(year)
        _, fa_top = build(year, cc_outage_derate_from_top=True)
        mask, multi = population(gens)
        S = scarce_hours(year)
        pmax = fa_def.pmax
        a_def, a_top = fa_def.availability, fa_top.availability

        # W5 single-delta identity
        moved = np.abs(a_def - a_top).max(axis=1) > DIFF_EPS
        non_p_movers = int((moved & ~mask).sum())
        mw_def = a_def * pmax[:, None]
        mw_top = a_top * pmax[:, None]
        worst_rel = 0.0
        for ix in multi.values():
            d = mw_def[ix].sum(axis=0)
            t = mw_top[ix].sum(axis=0)
            denom = np.maximum(np.abs(d), 1.0)
            worst_rel = max(worst_rel, float((np.abs(d - t) / denom).max()))
        rec["W5"][str(year)] = {
            "non_P_rows_moved": non_p_movers,
            "worst_relative_total_MW_error": worst_rel,
            "status": "CLEAN" if non_p_movers == 0 and worst_rel <= 1e-6 else "BUG",
        }

        # W1 liveness
        plant_diff = np.zeros((len(multi), 8760), dtype=bool)
        for k, ix in enumerate(multi.values()):
            plant_diff[k] = np.abs(a_def[ix] - a_top[ix]).max(axis=0) > DIFF_EPS
        share_year = float(plant_diff.mean())
        share_S = float(plant_diff[:, S].mean())
        rec["W1"][str(year)] = {
            "n_plants_P": len(multi),
            "n_rows_P": int(mask.sum()),
            "differing_plant_hours_share_year": share_year,
            "differing_plant_hours_share_S": share_S,
            "status": "LIVE" if share_S >= W1_LIVE_LINE else "INERT",
        }

        # W2 drag by band + min_gen
        bands = np.array([band_of(g.name) for g in gens])
        d_mw = mw_top - mw_def
        by_band = {}
        for b in ("mustrun", "committed", "econ", "peak", "other"):
            sel = mask & (bands == b)
            if not sel.any():
                continue
            v = d_mw[sel].sum(axis=0)
            by_band[b] = {
                "mean_MW_year": float(v.mean()),
                "mean_MW_S": float(v[S].mean()),
            }
        pos_S = float(np.maximum(d_mw[mask], 0.0).sum(axis=0)[S].mean())
        cc_cap = float(pmax[mask].sum())
        mg_def = fa_def.min_gen if fa_def.min_gen is not None else np.zeros_like(a_def)
        mg_top = fa_top.min_gen if fa_top.min_gen is not None else np.zeros_like(a_def)
        d_mg = (mg_top - mg_def)[mask].sum(axis=0)
        rec["W2"][str(year)] = {
            "cc_regular_P_pmax_MW": cc_cap,
            "by_band": by_band,
            "mean_positive_movement_MW_S": pos_S,
            "positive_movement_share_of_class_pmax_S": pos_S / cc_cap,
            "d_min_gen_TWh_max": float(np.maximum(d_mg, 0.0).sum() / 1e6),
            "d_min_gen_peak_MW": float(d_mg.max()),
            "status": "MATERIAL" if pos_S / cc_cap >= W2_MATERIAL_LINE else "INERT",
        }

        # W4 headroom
        disp = cc_class_dispatch(year)
        floor_cls = mg_def[mask].sum(axis=0)
        if disp is not None:
            binding = (disp - floor_cls) <= BIND_TOL_MW
        else:
            binding = np.zeros(8760, dtype=bool)
        lb_twh = float(np.maximum(d_mg, 0.0)[binding].sum() / 1e6)
        row = next(
            (r for r in c1 if r["key"] == "CC_REGULAR" and r["year"] == year), None
        )
        head = None
        if row is not None and tol_twh(row) is not None:
            head = tol_twh(row) - (float(row["model"]) - float(row["actual"]))
        rec["W4"][str(year)] = {
            "binding_hours": int(binding.sum()),
            "floor_channel_lower_bound_TWh": lb_twh,
            "floor_channel_max_TWh": float(np.maximum(d_mg, 0.0).sum() / 1e6),
            "c1_cc_regular_headroom_TWh": head,
            "c1_status": (row or {}).get("status"),
            "cc_regular_class_min_gen_MW_default": float(mg_def[mask].sum()),
            "disclosure": (
                "CC_REGULAR carries NO min_gen floor on this keeper "
                "(cc_mustrun_per_plant=False; no D-2 row in any year), so the "
                "floor channel is identically zero and this witness CANNOT "
                "bite. The arm's real C1 exposure runs through the ECONOMIC "
                "channel, which phase 0 cannot bound without a solve — see the "
                "PREREG's named kill."
            ),
            "status": (
                "N/A-UNBANDED" if head is None
                else ("GUARANTEED-FLIP" if lb_twh >= head else "CLEAR")
            ),
        }
        del fa_def, fa_top, a_def, a_top, mw_def, mw_top, d_mw

    # W1 provenance split (2025 only, declared)
    _, fa_def25 = build(2025)
    gens25, fa_stat25 = build(2025, outage_source="statistical")
    m25, multi25 = population(gens25)
    tot_def = (fa_def25.availability * fa_def25.pmax[:, None])[m25].sum(axis=0)
    tot_stat = (fa_stat25.availability * fa_stat25.pmax[:, None])[m25].sum(axis=0)
    cap25 = float(fa_def25.pmax[m25].sum())
    short_total = cap25 - tot_def.mean()
    short_stat = cap25 - tot_stat.mean()
    rec["W1"]["provenance_2025"] = {
        "P_capacity_MW": cap25,
        "mean_shortfall_total_MW": float(short_total),
        "mean_shortfall_statistical_only_MW": float(short_stat),
        "measured_overlay_share": float(
            (short_total - short_stat) / short_total
        ) if short_total > 0 else None,
        "note": "reported, NOT gated (frozen rule W1)",
    }

    rec["W3"] = w3_conduct()

    ok = (
        all(v["status"] == "LIVE" for k, v in rec["W1"].items() if k != "provenance_2025")
        and all(v["status"] == "MATERIAL" for v in rec["W2"].values())
        and all(v["status"] != "GUARANTEED-FLIP" for v in rec["W4"].values())
        and all(v["status"] == "CLEAN" for v in rec["W5"].values())
        and rec["W3"].get("status") == "PASS"
    )
    rec["CHARTER_AB"] = bool(ok)
    OUT.write_text(json.dumps(rec, indent=2, default=float))
    print(json.dumps(rec, indent=2, default=float))


if __name__ == "__main__":
    main()
