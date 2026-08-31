"""miso-195 phase-0 census: the remove-only measured cap on the CAMPD outage
envelope, fed by MISO's own published Forced+Derated+Unplanned record
(zero-solve).

Charter: FINDING-miso194 §7's named successor — repair the envelope rather than
stack a mechanism on an inverted one. Keeper at session start and throughout:
``2026-08-30-miso-191-bexit`` (bundle ``results/calibration/miso191_bax_B``),
Ask-A reproduced this session: NOT-YET on {C3a-2025 −12.3%} ALONE, C1 16/16 /
12/12 free, C3c the single ledgered caveat, C6 attested, C8 PASS (two grounded
notes); ``audit_keepers --iso MISO`` PASS 0/0; ``build_status --iso MISO
--check`` in sync; ``check_mechanism_matrix`` integrity OK. Distance to band
+2.34 pp.

THE MECHANISM UNDER CENSUS (nothing is armed here; phase 0 decides whether an
A/B is chartered). The existing gate ``ScenarioConfig.miso_native_outage_source``
(default off, armed in ZERO bundles) currently carries SUBSTITUTION semantics —
refuted on grain at miso-85/86. The charter fixes the only admissible form,
which is exactly the composition decision ``market_sim.data.miso_outages``'s own
docstring defers to "a future MISO calibration session":

  A FLEET-GRAIN, REMOVE-ONLY measured cap, composed WITH the armed envelope,
  never substituting it. Hourly deficit
      deficit(t) = max(0, P(t) − M(t))
  where M(t) is the keeper's own TOTAL armed offline MW over the thermal
  population and P(t) is MISO's published unplanned offline record. An arm
  would deepen every population row's availability by the fleet-uniform
  multiplier mu(t) = 1 − deficit(t) / max(available(t), eps), clip [0, 1] —
  the pjm-161 event-cap shape. It can NEVER restore (mu ≤ 1 by construction),
  so the pjm-145 structural-zero-resurrection channel (66–68% of that arm's
  measured lift) and the miso-85 coal-resurrection C1 failure are unreachable
  by construction; and it invents NO apportionment (the deficit is applied
  fleet-uniformly, the miso-176 K-2 / charter-forced form — the record has no
  unit or fuel identity, ``_SOURCE.md``).

PRIOR-CLOSURE CONFRONTATIONS (each named ex ante; none of this is a silent
re-test — the DO-NOT-REDO discipline requires new evidence, which is stated):

  * miso-85/86 (``dam_availability_rebasis`` R): the uniform daily envelope
    SUBSTITUTION. Its two measured failure modes were (i) resurrection of ~5 GW
    of coal the per-unit record holds out (C1 COAL_PRB +28.3 TWh) and (ii) the
    year-round uniform strip of ~4–5 GW from a 22.4 GW CT fleet nothing says
    was out (C3a-2025 +43.5%, 138 manufactured tail hours). The remove-only
    cap composed with the CAMPD envelope keeps the per-unit attribution intact
    — (i) is unreachable by construction; (ii) is bounded to the measured
    deficit in deficit hours (measured below, W3/W4), not a level rebasis.
    NOT a re-test of the substitution: a different composition, the one the
    module docstring left open.
  * miso-85's "residual composition is inert" note: adjudicated on the 2023
    ANNUAL MEAN (CAMPD 27.9 GW vs record 21.8 GW unplanned — the residual is
    zero on average in 2023). The DAILY-grain residual in 2025 was not
    measured there; miso-87 ground 1 then measured the like-for-like level gap
    FLIP SIGN in 2025 (published implies 4.5–6 GW MORE thermal offline than
    CAMPD) and read it as "the aggregate record's resolution limit, not a
    forward-reproducible signal". THE NEW EVIDENCE that re-opens exactly that
    reading: miso-194 W2b/W6 measured the armed envelope COLD-INVERTED
    (rho(offline, TMIN) +0.581 vs published −0.344, 2025) and
    SCARCITY-INVERTED (rho(offline, net load) −0.61..−0.70; top-1% net-load
    hours carry 0.63/0.70/0.78x the annual-mean derate), with the root cause
    named (the CAMPD detector infers unavailability from ZERO GENERATION, so
    it cannot see an outage at a unit that would not have run anyway, and a
    unit in layup RUNS when prices spike). A detector blind exactly where the
    fleet is in-merit predicts a published-over-CAMPD excess that GROWS with
    tightness — the 2025 flip is the predicted signature of a root-caused
    defect, not record noise. That mechanism finding post-dates miso-87 by
    five weeks and is the charter's stated ground.
  * miso-87 (cross-fuel attribution REFUTED AT CHARTER): no admissible per-fuel
    key exists. The cap invents none — fleet-uniform on the increment is the
    form that refusal forces, not a violation of it.
  * miso-161 / the miso-178 §8 anti-list line "MOM daily-grain outage shape
    (≲0.11 pp)": that measurement is the RECORD-INTERNAL peak increment — MOM
    unplanned offline at the top-200 demand hours vs its own Jun–Sep mean
    (ratio 1.022, +0.69 GW in 2025) — i.e. what the record's daily grain adds
    BEYOND the armed flat seasonal share. The cap acts on a DIFFERENT quantity:
    the MODEL-vs-RECORD deficit, which is (record's S-increment) + (Jun–Sep
    level gap P−M) + (the model envelope's own sag below its seasonal mean at
    the peak — the miso-194 W6 inversion term the record-internal measurement
    cannot contain). R2 below decomposes the measured deficit into exactly
    those three terms so the two objects can never be conflated: if the level
    and sag terms turn out ~0, the deficit IS the miso-161 quantity and the
    lever refutes on the same materiality it already carries.
  * miso-160 (``summer_wefor_share_override = 1.0599``, K): the keeper already
    consumes THIS SAME RECORD's Jun–Sep/annual RATIO through the WEFOR share.
    The cap consumes its DAILY LEVEL net of the full armed envelope —
    deficit(t) is computed against M(t) INCLUSIVE of the armed share, so every
    MW the share already removed shrinks the cap's own removal one-for-one.
    Double-count is impossible by construction (rule 19); W1 records the
    composition census.
  * pjm-161 (the shape source, rules 25/28(d): no parameter, no verdict
    transfers): PJM's remove-only TOTAL-basis cap was adjudicated NOT-a-keeper
    because PJM's model asserts MORE outage on the fossil fleet alone (41–43
    GW) than PJM publishes for the whole system (33–36 GW), so the cap
    deepened an already-too-deep level in mid-load hours and left the top-1%
    unchanged. W2 below is that level test on MISO's own bases, frozen as a
    load-bearing gate: if MISO's armed envelope is already deeper than the
    whole-fleet all-cause record, the same refutation transfers and the lever
    dies here.

THE CAUSE-TYPE BASIS, SETTLED EX ANTE (the charter's named decision: does the
cap read TOTAL outage or unplanned-only?). FROZEN: the cap reads the UNPLANNED
components, ``("Derated", "Forced", "Unplanned")`` — the record's additive GADS
buckets minus ``Planned`` — on three grounds, none of them a residual:

  1. The with-Planned (all-cause) form is ALREADY REFUTED for this exact
     application by owner-adjudicated physical feasibility (miso-85: EIA-930
     daily-max coal+gas generation exceeds the all-cause envelope's available
     capacity on 12/15/61 days of 2023/2024/2025, worst +12.7 GW; wiring doc
     §Composition: "must not be re-armed"). In every hour the cap binds, the
     capped availability equals the substitution's availability, so the
     refutation applies to the cap's with-Planned form verbatim.
  2. Congruence where the mechanism lives. The charter aims the cap at the
     summer scarce set (the net-load channel, miso-194 W6; Jun+Jul own −6.97
     pp of C3a-2025). ``Planned`` is at its annual minimum in July (7.9 GW vs
     36.4 GW April, and mostly non-thermal even then — nuclear refuel, hydro),
     and the model's own planned-window component (CAMPD spring windows,
     maintenance shape) is likewise out of the peak. The Planned-mismatch
     between the two bases is smallest exactly in the window that matters, and
     everywhere else its sign (M carries planned windows P lacks) makes the
     cap strictly CONSERVATIVE — it under-binds in the shoulder, the direction
     that protects the over-priced 2023/2024 body (miso-178 §4's constraint)
     by construction.
  3. Lineage continuity: unplanned is the settled composition of this record
     on this keeper's lineage — the substitution (miso-85), the armed summer
     share (miso-160) and the miso-161 peak-shape measurement all read
     ``("Derated","Forced","Unplanned")``. (miso-194's winter witness read
     Forced+Derated only; that was a winter-event scoping of ITS witness, not
     a composition ruling on this mechanism.)

  Named against interest: the unplanned basis biases the cap toward INERTNESS
  (the pjm-161 "definitional mismatch → never binds" arm: M carries planned
  windows the basis-P side excludes, so M is overstated relative to P in
  maintenance season). W3 measures exactly where that leaves the cap binding;
  if the answer is "nowhere, even in JJA", the honest outcome is refutation
  (charter F), never a switch to the feasibility-refuted basis.

FROZEN ADJUDICATION RULE (ex ante, pushed before any adjudicating quantity —
the miso-193/194 pattern; mis-freeze lessons applied: every witness derives
from the SAME basis the mechanism would read, witnesses are RELATIONS never
constants, and mechanical satisfiability of every basis was verified on the
control BEFORE this rule was frozen — record present 365 days x 3 years both
cause sets, committed actual RT hourly present for 2023–2025, sidecar classes
present, bench present; no adjudicating value was computed in that check):

  POPULATION (frozen): the built loader's own thermal set,
  ``market_sim.data.miso_outages._THERMAL_GROUPS`` = {COAL, CC_REGULAR,
  CC_CHP, ST_GAS, ST_CHP, CT_PEAKER, CT_CHP}, pmax > 0 — the exact population
  ``miso_native_outage_derate_factors`` applies to, so the census and any arm
  share one boundary (118.3 GW on the keeper build). Dual-fuel rows are
  INCLUDED (the cap writes availability, not fuel pricing; physical outages
  reach dual-fuel steel too — ``dual_fuel_switching`` re-prices, it does not
  write availability). Nuclear is excluded (own measured overlay; outside the
  loader's population).

  BASES (each the exact object the mechanism or its witness would read):
    M (model, armed envelope): the load-bearing build
      ``load_fleet_from_csv → generators_to_fleet_arrays(config=<keeper cfg>,
      iso="MISO", year=Y)``; offline MW at hour t = Σ over population rows of
      ``pmax·(1 − availability)``. This is the TOTAL armed envelope —
      statistical WEFOR/POF (with the armed 1.0599 summer share and the 0.10
      ST_GAS base) x CAMPD unit windows x short windows x maxgen events x
      fleet-status scope x layup mask x CHP temp derate x summer basis — i.e.
      everything an arm would compose against.
    P_U (published, the cap's feed): ``miso_outage_mw_series(Y, "MISO",
      ("Derated","Forced","Unplanned"))`` — rule-13 admissible measured
      availability; never a price, never an outcome.
    P_ALL (published, W2's comparator only, NEVER the cap basis):
      all four buckets including Planned.
    S (the scarce set, gate year 2025): the 200 highest ISO-demand hours of
      the keeper's own committed P1 solve, six carry zones — the miso-153/161
      window, reused verbatim. (Top-1% net-load reported for miso-194 W6
      continuity; never gated.)
    H (headroom): Σ over population classes of (capability − P1 dispatch),
      capability = Σ pmax·availability from basis M, dispatch from
      ``hourly/class_hourly_<Y>.parquet`` (klass → group map: COAL_BIT +
      COAL_LIGNITE + COAL_PRB → COAL).
    idleCT (the past-the-peakers denominator): the same difference restricted
      to {CT_PEAKER, ST_GAS} — the expensive end of MISO's thermal stack, the
      classes whose idleness at the peak is the marginal-identity defect
      (miso-178 §5: 8.2 GW CT_PEAKER idle in the 2025 tail; Δ₁ = 197%).
    A (actual price): committed ``data/raw/_validation-source/
      actual_lmp_hourly_MISO.parquet`` RT hourly, filtered to 2023–2025 ONLY
      (the file carries 2022/2026 rows; this probe never reads them — rule 22).
    G (measured thermal output): EIA-930 MISO COL+NG hourly (market clock,
      Etc/GMT+5), daily max — the miso-85 feasibility instrument.
    bench: ``frontend/data/backcast/bench/MISO/<Y>.json.gz`` ``rt_lw`` — the
      C3a scorer's own basis.

  deficit(t) = max(0, P_U(t) − M(t)), hourly, per year. The cap's removal.

  W1 COMPOSITION CENSUS (load-bearing, boolean). Enumerate every armed
    availability-writing mechanism on the keeper over the population. PASS iff
    NO armed mechanism already consumes the published record's DAILY LEVEL
    (which would double-count the cap's quantity). The one same-source armed
    mechanism — ``summer_wefor_share_override``, consuming the record's
    SEASONAL RATIO — is named and reported; it is not a violation because the
    cap's deficit is computed net of the full armed envelope (any MW it
    removed already shrinks the deficit one-for-one).

  W2 LEVEL CONGRUENCE (load-bearing — the pjm-161 transfer test). PASS iff
    annual-mean M(2025) < annual-mean P_ALL(2025). If the armed envelope
    already asserts more offline on the thermal population alone than MISO
    publishes for the whole registered fleet all causes, a remove-only cap
    moves the level AWAY from the operator's record and the pjm-161
    refutation transfers verbatim. (Reported, never gated: all three years;
    monthly profiles of M, P_U, P_ALL; M vs P_U per year — the miso-85/87
    level-continuity numbers.)

  W3 BIND EXISTENCE IN THE TARGET WINDOW (load-bearing). PASS iff
    deficit(t) > 0 in ≥ 25% of the 2025 S hours. The charter's case for the
    lever lives in the summer scarce set; a cap that is silent there cannot
    reach the target whatever it does elsewhere. (Reported: binding share of
    all hours per year, monthly binding profile, removed GWh per year, the
    2023 "residual is inert" confrontation, the top-1% net-load binding
    share.)

  W4 CONVERSION vs THE KEEPER'S OWN SURPLUS (load-bearing — the charter's
    named gate, the miso-194 W4 analogue on the summer scarce set). Among the
    2025 S hours where the cap binds, an hour CONVERTS iff
        deficit(t) > H(t)        (leg A — full exhaustion, the scarcity
                                  channel; the strict miso-194 relation), OR
        deficit(t) > idleCT(t)   (leg B — the removal exceeds the ENTIRE idle
                                  peaking mass, forcing replacement beyond the
                                  peaking stack: a marginal-identity jump no
                                  intra-class flatness can absorb).
    PASS iff ≥ 25% of binding S hours convert. Leg B under-credits walks
    WITHIN the peaking stack (a removal smaller than idleCT that still climbs
    the CT tranche ladder is counted as absorbed) — against interest,
    disclosed; the $-conditioned cushion walk is not reconstructible without
    the offer surface, and this probe stays zero-solve.

  W5 REACH CEILING AT ACTUALS (load-bearing materiality). In the scorer's own
    basis: over every 2025 hour where the cap binds, the ceiling of ANY
    availability-removal lever confined to those hours is pricing them AT the
    measured actual (never above):
        pp_ceiling = Σ_binding dem(t)·max(0, rt(t) − p_model(t))
                     / Σ_year dem(t) / rt_lw x 100
    with p_model(t) the demand-weighted carry-zone model price (the C3a
    aggregation). PASS iff pp_ceiling ≥ +0.30 pp. (Reported, against
    interest: the same ceiling restricted to S; the ADVERSE exposure
    Σ_binding dem·max(0, p_model − rt) — binding hours the cap can only push
    FURTHER ABOVE actual; and the miso-160 measured-slope linear projection
    of the cap's total removal, context only — that episode moved C3a-2025
    +0.60 pp per 3.67 GW x Jun–Sep.)

  W6 PHYSICAL FEASIBILITY OF THE CAPPED ENVELOPE (load-bearing). On the
    unplanned basis, for each year: days where the capped available capacity
    ``C_pop − max(daily M, daily P_U)`` falls below the measured EIA-930
    daily-max coal+gas generation. PASS iff ≤ 3 violation days in every year
    of 2023–2025 (the miso-85 instrument read the substitution feasible on
    every day but one, 2025-05, −1.6 GW; the cap equals the substitution in
    binding hours and the keeper's own envelope elsewhere, so more than a
    handful of violation days means the composed basis is broken, not noisy).

  CHARTER GATE: an LP A/B (charter E: PREREG, replay control, single delta,
  years 2023 2024 2025, both legs registered) is chartered iff
  W1 ∧ W2 ∧ W3 ∧ W4 ∧ W5 ∧ W6. ANY load-bearing miss ⇒ REFUTE: stamp the
  MISO ``campd_outage_windows`` cell with the citation, write the FINDING,
  STOP (one lever per session, charter F).

  DIRECTIONAL PREREG (ex ante, with confidence). IF chartered, the arm raises
  summer scarce-hour prices and moves C3a-2025 UP (less negative). CONFIDENCE
  that it delivers ≥ +0.30 pp on annual C3a-2025: **0.40**. FOR: (i) miso-87's
  like-for-like reconciliation flips sign in 2025 — published implies 4.5–6 GW
  MORE thermal offline than CAMPD measures, in the one year the target needs;
  (ii) the deficit at the peak is level-gap + record-increment + model-sag,
  and miso-194 W6 measured the sag real (top-1% at 0.78x the annual mean)
  while miso-161 measured the record holding level at the peak (1.022); (iii)
  this LP's demonstrated response to availability removal at the expensive end
  (miso-85 manufactured a 138-hour tail from ~4–5 GW; miso-160 moved +0.60 pp
  with 3.67 GW of shoulder-cushioned removal). AGAINST, stated in full: (a)
  the ARMED M is deeper than the CAMPD component alone (the WEFOR stack
  multiplies in), so the 2025 level gap may close or invert at the armed
  envelope — W2/W3's subject; (b) the keeper idles 8.2 GW of CT_PEAKER in the
  2025 tail with total thermal headroom above that — W4's subject, and the
  exact relation that killed miso-194; (c) if R2's level and sag terms read
  ~0, the deficit collapses to the miso-161 record-internal increment already
  adjudicated ≲0.11 pp; (d) MISO's inversion is materially milder than PJM's
  (0.78x vs 0.22–0.38x). Whatever the outcome, every number is reported at
  full magnitude.

  MATERIALITY LINE, declared: a lever that cannot plausibly reach +0.30 pp of
  annual C3a-2025 is not worth a two-leg solve at this frontier (distance to
  band +2.34 pp; the miso-193 lineage's adverse-face bound for
  self-promotion vs owner escalation remains 1.5 pp).

Rule 21 [R-DOF]: this probe adds ZERO solve inputs and has zero free
parameters; the 25% / 25% / 0.30 pp / ≤3-day / top-200 lines are ex-ante
adjudication thresholds of the census, not model parameters. Rule 13
[R-MEASURED]: the MISO OUTAGE record and the EIA-930 metered series are
physical availability/output quantities that regenerate for a forward year and
respond to changed conditions; the committed actual RT series enters ONLY the
W5 materiality ceiling (an adjudication bound on whether to spend a solve),
never any solve input, never a parameter. Rule 22 [R-HOLDOUT]: 2023–2025 only;
MISO holds neither marker; the 2022/2026 rows of the actual parquet and any
out-of-train record days are never read.

Read-only and idempotent. Output:
``results/calibration/_miso195_outage_envelope_phase0.json``.
"""

from __future__ import annotations

import dataclasses
import gzip
import json
import sys
import typing
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))  # probe hygiene, miso-140b §6
sys.path.insert(0, str(REPO / "src"))

import pandas as pd  # noqa: E402

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    generators_to_fleet_arrays,
    load_fleet_from_csv,
)
from market_sim.data.miso_outages import (  # noqa: E402
    _THERMAL_GROUPS,
    miso_outage_mw_series,
)

ISO = "MISO"
YEARS = (2023, 2024, 2025)
GATE_YEAR = 2025
KEEPER = REPO / "results/calibration/miso191_bax_B"
OUT = REPO / "results/calibration/_miso195_outage_envelope_phase0.json"

# The cap's feed (frozen basis, docstring "THE CAUSE-TYPE BASIS") and W2's
# whole-record comparator.
UNPLANNED = ("Derated", "Forced", "Unplanned")
ALL_CAUSES = ("Derated", "Forced", "Planned", "Unplanned")

# Population = the built loader's own set (docstring "POPULATION").
POP_GROUPS = tuple(sorted(_THERMAL_GROUPS))
# class_hourly klass values for the population (COAL is split in the sidecar).
POP_KLASSES = (
    "CC_CHP",
    "CC_REGULAR",
    "COAL_BIT",
    "COAL_LIGNITE",
    "COAL_PRB",
    "CT_CHP",
    "CT_PEAKER",
    "ST_CHP",
    "ST_GAS",
)
CT_KLASSES = ("CT_PEAKER", "ST_GAS")
CARRY = (
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
    "MISO-South",
)

# Ex-ante adjudication thresholds (docstring; not solve inputs, rule 21).
W3_BIND_LINE = 0.25
W4_CONVERT_LINE = 0.25
W5_CEILING_PP = 0.30
W6_MAX_VIOLATION_DAYS = 3
S_TOP_HOURS = 200
# miso-160's measured response scale (FINDING-miso160 §4; context only, W5
# reported): +0.60 pp on C3a-2025 per 3.67 GW removed across Jun-Sep.
M160_PP = 0.60
M160_GW = 3.67
M160_HOURS = 2928.0


def keeper_config(year: int) -> ScenarioConfig:
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
    return ScenarioConfig(**out)  # type: ignore[arg-type]


def build_arrays(year: int):
    """Load the keeper's load-bearing fleet build for ``year`` (basis M)."""
    cfg = keeper_config(year)
    iso_cfg = get_iso_config(ISO)
    gens = load_fleet_from_csv(
        ISO,
        iso_cfg,
        year=year,
        measured_ct_heat_rates=bool(getattr(cfg, "measured_ct_heat_rates", False)),
        measured_chp_heat_rates=bool(getattr(cfg, "measured_chp_heat_rates", False)),
        egrid_identity_heat_rates=bool(
            getattr(cfg, "egrid_identity_heat_rates", False)
        ),
        cc_steam_part_capacity=bool(getattr(cfg, "cc_steam_part_capacity", False)),
        cc_steam_part_reclass=bool(getattr(cfg, "cc_steam_part_reclass", False)),
    )
    zones = [z.name for z in iso_cfg.zones]
    fa = generators_to_fleet_arrays(gens, zones, 8760, iso=ISO, config=cfg, year=year)
    return cfg, gens, zones, fa


def _pivot_hour(df: pd.DataFrame, value: str, columns: str) -> pd.DataFrame:
    p = df.pivot_table(index="hour", columns=columns, values=value, aggfunc="sum")
    return p.reindex(range(8760)).fillna(0.0)


def load_sidecars(year: int) -> dict:
    """Committed P1 sidecars: demand, model price (C3a aggregation), dispatch."""
    sysdf = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
    sysdf = sysdf[sysdf["pass"].astype(str).str.upper() == "P1"]
    sysdf = sysdf[sysdf["zone"].isin(CARRY)]
    dem_z = _pivot_hour(sysdf, "demand", "zone")
    prc_z = sysdf.pivot_table(
        index="hour", columns="zone", values="price", aggfunc="mean"
    ).reindex(range(8760))
    dem = dem_z.to_numpy().sum(axis=1)
    # Demand-weighted carry-zone model price — the C3a aggregation.
    w = dem_z.to_numpy()
    p = prc_z.to_numpy()
    with np.errstate(invalid="ignore"):
        p_model = np.where(w.sum(axis=1) > 0, (w * p).sum(axis=1) / w.sum(axis=1), np.nan)

    dfh = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
    dfh = dfh[dfh["pass"].astype(str).str.upper() == "P1"]
    piv = _pivot_hour(dfh, "mw", "klass")
    missing = [c for c in POP_KLASSES if c not in piv.columns]
    assert not missing, f"population class absent from sidecar: {missing}"
    disp_pop = piv[list(POP_KLASSES)].to_numpy().sum(axis=1)
    disp_ct = piv[list(CT_KLASSES)].to_numpy().sum(axis=1)
    vre = sum(piv[c].to_numpy() for c in ("wind", "solar") if c in piv.columns)
    return {
        "dem": dem,
        "p_model": p_model,
        "disp_pop": disp_pop,
        "disp_ct": disp_ct,
        "netload": dem - vre,
    }


def actual_rt(year: int) -> np.ndarray:
    """Committed measured RT hourly (system hub), 2023-2025 only (rule 22)."""
    assert year in YEARS, f"out-of-train year {year} refused"
    df = pd.read_parquet(RAW_DATA_DIR / "_validation-source" / "actual_lmp_hourly_MISO.parquet")
    df = df[df["year"] == year]
    rt = df.set_index("hour")["rt"].reindex(range(8760)).to_numpy(dtype=float)
    return rt


def measured_thermal_gen_daily_max(year: int) -> dict[tuple[int, int], float]:
    """EIA-930 MISO daily-max coal+gas generation, market clock (miso-85)."""
    df = pd.read_parquet(RAW_DATA_DIR / "MISO_fueltype.parquet")
    per = pd.to_datetime(df["period"], utc=True).dt.tz_convert("Etc/GMT+5")
    ser = df.assign(period=per)
    ser = ser[ser["fueltype"].isin(["COL", "NG"])].groupby("period")["value_mwh"].sum()
    ser = ser[ser.index.year == int(year)]
    daily = ser.groupby(ser.index.normalize()).max()
    return {
        (int(ts.month), int(ts.day)): float(v)
        for ts, v in daily.items()
        if not (ts.month == 2 and ts.day == 29)
    }


def _daily(x: np.ndarray) -> np.ndarray:
    return np.asarray(x, dtype=float).reshape(365, 24).mean(axis=1)


def _months(hours: int = 8760) -> np.ndarray:
    return pd.date_range("2023-01-01", periods=hours, freq="h").month.to_numpy()


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    if np.std(ra) == 0 or np.std(rb) == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def w1_composition_census(cfg: ScenarioConfig) -> dict:
    """W1: which armed mechanisms write availability on the population, and
    does any already consume the published record's DAILY LEVEL."""
    rows = []

    def add(field, armed, writes_availability, consumes_daily_level, why):
        rows.append(
            {
                "field": field,
                "armed": bool(armed),
                "writes_population_availability": bool(writes_availability),
                "consumes_published_daily_level": bool(consumes_daily_level),
                "why": why,
            }
        )

    add(
        "outage_source",
        str(getattr(cfg, "outage_source", "")) == "historic",
        True,
        False,
        "CAMPD >=5-day unit windows — per-unit measured windows, no published-"
        "record level; the envelope the cap composes WITH",
    )
    for f, why in (
        ("unit_outage_short_windows", "CAMPD 1-5 day coal windows — per-unit"),
        ("unit_outage_maxgen_events", "declared-window revealed derates — per-unit"),
        ("unit_outage_fleet_status_scope", "mothball status scoping — per-unit"),
        ("mustrun_layup_window_mask", "measured layup window mask — per-unit"),
    ):
        add(f, bool(getattr(cfg, f, False)), True, False, why)
    add(
        "summer_wefor_share_override",
        getattr(cfg, "summer_wefor_share_override", None) is not None,
        True,
        False,
        "THE SAME-SOURCE MECHANISM, named per rule 19: consumes this record's "
        "Jun-Sep/annual unplanned RATIO (1.0599, miso-160) as a seasonal WEFOR "
        "share — a seasonal ratio, NOT the daily level; the cap's deficit is "
        "computed net of the armed envelope inclusive of it, so double-count "
        "is impossible by construction",
    )
    for f, why in (
        ("gas_st_wefor_base_override", "flat ST_GAS WEFOR base (0.10) — statistical"),
        ("summer_derate_basis_aware", "summer capability basis — not a record level"),
        ("temp_dependent_derate", "CHP-scoped ambient derate — not a record level"),
        ("coal_drop_pof", "drops coal statistical POF (CAMPD windows own coal "
         "maintenance) — composition fact for the basis settle, no record level"),
    ):
        v = getattr(cfg, f, None)
        add(f, bool(v) if not isinstance(v, str) else True, True, False, why)
    for f, why in (
        ("miso_native_outage_source", "THE GATE UNDER CENSUS — default off, armed "
         "in zero bundles; substitution semantics refuted miso-85/86"),
        ("historic_outage_overlay", "legacy plant-level overlay — off"),
        ("correlated_forced_outage", "off; doubly refused in backcast (FF-1B D.5)"),
        ("unit_partial_outage_windows", "off"),
        ("dam_availability_rebasis_family", "no such field armed; the miso-85/86 "
         "R substitution is not re-tested here"),
    ):
        add(f, bool(getattr(cfg, f, False)), False, False, why)
    add(
        "nuclear_unit_availability",
        bool(getattr(cfg, "nuclear_unit_availability", False)),
        False,
        False,
        "nuclear-only overlay — outside the population",
    )
    violations = [r for r in rows if r["armed"] and r["consumes_published_daily_level"]]
    return {
        "rows": rows,
        "n_violations": len(violations),
        "violations": [r["field"] for r in violations],
        "pass": len(violations) == 0,
    }


def main() -> dict:
    rec: dict = {
        "probe": "miso-195 phase-0 remove-only measured outage-envelope cap census",
        "keeper": "2026-08-30-miso-191-bexit",
        "bundle": str(KEEPER.relative_to(REPO)),
        "mechanism_gate": "miso_native_outage_source (semantics: remove-only cap)",
        "matrix_cell": "campd_outage_windows (MISO)",
        "cap_basis_cause_types": list(UNPLANNED),
        "population_groups": list(POP_GROUPS),
        "years": list(YEARS),
        "gate_year": GATE_YEAR,
        "thresholds": {
            "W3_bind_line": W3_BIND_LINE,
            "W4_convert_line": W4_CONVERT_LINE,
            "W5_ceiling_pp": W5_CEILING_PP,
            "W6_max_violation_days": W6_MAX_VIOLATION_DAYS,
            "S_top_hours": S_TOP_HOURS,
        },
        "per_year": {},
    }
    mon = _months()

    keep = {}
    for year in YEARS:
        cfg, gens, zones, fa = build_arrays(year)
        groups = np.array([str(getattr(g, "plant_group", "")) for g in gens])
        pop = np.isin(groups, np.asarray(POP_GROUPS)) & (fa.pmax > 0.0)
        ct = np.isin(groups, np.asarray(CT_KLASSES)) & (fa.pmax > 0.0)
        c_pop = float(fa.pmax[pop].sum())

        av = fa.availability[pop]
        offline_m = (fa.pmax[pop][:, None] * (1.0 - av)).sum(axis=0)
        cap_m = (fa.pmax[pop][:, None] * av).sum(axis=0)
        cap_ct = (fa.pmax[ct][:, None] * fa.availability[ct]).sum(axis=0)

        p_u = np.asarray(miso_outage_mw_series(year, "MISO", UNPLANNED), dtype=float)
        p_all = np.asarray(miso_outage_mw_series(year, "MISO", ALL_CAUSES), dtype=float)
        assert p_u.any() and p_all.any(), f"record absent for {year}"

        sc = load_sidecars(year)
        H = np.maximum(0.0, cap_m - sc["disp_pop"])
        idle_ct = np.maximum(0.0, cap_ct - sc["disp_ct"])

        deficit = np.maximum(0.0, p_u - offline_m)
        bind = deficit > 0.0

        y: dict = {
            "population_mw": round(c_pop, 1),
            "n_population_rows": int(pop.sum()),
            "annual_mean": {
                "M_offline_gw": float(offline_m.mean() / 1e3),
                "P_unplanned_gw": float(p_u.mean() / 1e3),
                "P_allcause_gw": float(p_all.mean() / 1e3),
            },
            "monthly_mean_gw": {
                "M": [float(offline_m[mon == m].mean() / 1e3) for m in range(1, 13)],
                "P_U": [float(p_u[mon == m].mean() / 1e3) for m in range(1, 13)],
                "P_ALL": [float(p_all[mon == m].mean() / 1e3) for m in range(1, 13)],
            },
            "bind_share_all_hours": float(bind.mean()),
            "bind_share_by_month": [
                float(bind[mon == m].mean()) for m in range(1, 13)
            ],
            "removed_gwh_year": float(deficit.sum() / 1e3),
            "removed_gw_mean_when_binding": float(deficit[bind].mean() / 1e3)
            if bind.any()
            else 0.0,
        }

        # W6 feasibility: capped daily availability vs measured daily-max output.
        g_meas = measured_thermal_gen_daily_max(year)
        d_m = _daily(offline_m)
        d_pu = _daily(p_u)
        capped_avail_d = c_pop - np.maximum(d_m, d_pu)
        # The model's fixed non-leap 365-day clock (Feb 29 never exists on it),
        # enumerated from any non-leap year; lookups are by (month, day).
        dates = pd.date_range("2025-01-01", periods=365, freq="D")
        viol = []
        for i, ts in enumerate(dates):
            gm = g_meas.get((int(ts.month), int(ts.day)))
            if gm is not None and capped_avail_d[i] < gm:
                viol.append(
                    {
                        "month_day": f"{ts.month:02d}-{ts.day:02d}",
                        "capped_avail_gw": float(capped_avail_d[i] / 1e3),
                        "measured_max_gw": float(gm / 1e3),
                    }
                )
        y["w6_violation_days"] = len(viol)
        y["w6_violations"] = viol[:8]
        y["w6_pass"] = len(viol) <= W6_MAX_VIOLATION_DAYS

        # miso-194 W6 continuity: binding share on the top-1% net-load set.
        top1 = sc["netload"] >= np.quantile(sc["netload"], 0.99)
        y["top1pct_netload_bind_share"] = float(bind[top1].mean())
        y["top1pct_netload_mean_deficit_gw"] = float(deficit[top1].mean() / 1e3)
        y["rho_deficit_netload"] = _spearman(deficit, sc["netload"])

        rec["per_year"][str(year)] = y
        keep[year] = {
            "cfg": cfg,
            "offline_m": offline_m,
            "cap_m": cap_m,
            "p_u": p_u,
            "deficit": deficit,
            "bind": bind,
            "H": H,
            "idle_ct": idle_ct,
            "sc": sc,
            "c_pop": c_pop,
        }

    g = keep[GATE_YEAR]
    rec["w1"] = w1_composition_census(g["cfg"])

    # W2: level congruence, gate year.
    m_mean = float(g["offline_m"].mean())
    pall_mean = float(miso_outage_mw_series(GATE_YEAR, "MISO", ALL_CAUSES).mean())
    rec["w2"] = {
        "M_2025_gw": m_mean / 1e3,
        "P_allcause_2025_gw": pall_mean / 1e3,
        "pass": m_mean < pall_mean,
    }

    # The scarce set S: top-200 ISO-demand hours of the committed 2025 P1.
    dem = g["sc"]["dem"]
    s_mask = np.zeros(8760, bool)
    s_mask[np.argsort(-dem)[:S_TOP_HOURS]] = True
    bind_s = g["bind"] & s_mask
    rec["w3"] = {
        "s_hours": int(s_mask.sum()),
        "bind_hours_in_s": int(bind_s.sum()),
        "bind_share_in_s": float(bind_s.sum() / s_mask.sum()),
        "pass": float(bind_s.sum() / s_mask.sum()) >= W3_BIND_LINE,
    }

    # W4: conversion among binding S hours.
    deficit, H, idle_ct = g["deficit"], g["H"], g["idle_ct"]
    conv_a = bind_s & (deficit > H)
    conv_b = bind_s & (deficit > idle_ct)
    conv = conv_a | conv_b
    nb = int(bind_s.sum())
    rec["w4"] = {
        "n_binding_s_hours": nb,
        "n_convert": int(conv.sum()),
        "n_convert_legA_exhaustion": int(conv_a.sum()),
        "n_convert_legB_past_peakers": int(conv_b.sum()),
        "convert_share": float(conv.sum() / nb) if nb else 0.0,
        "median_deficit_gw_in_binding_s": float(np.median(deficit[bind_s]) / 1e3)
        if nb
        else 0.0,
        "median_H_gw_in_binding_s": float(np.median(H[bind_s]) / 1e3) if nb else 0.0,
        "median_idleCT_gw_in_binding_s": float(np.median(idle_ct[bind_s]) / 1e3)
        if nb
        else 0.0,
        "median_H_gw_in_s": float(np.median(H[s_mask]) / 1e3),
        "median_idleCT_gw_in_s": float(np.median(idle_ct[s_mask]) / 1e3),
        "pass": (float(conv.sum() / nb) if nb else 0.0) >= W4_CONVERT_LINE,
    }

    # W5: reach ceiling at actuals over ALL 2025 binding hours.
    rt = actual_rt(GATE_YEAR)
    p_model = g["sc"]["p_model"]
    bench = json.loads(
        gzip.open(REPO / "frontend/data/backcast/bench/MISO" / f"{GATE_YEAR}.json.gz").read()
    )["bench"]["avgLMP"]
    rt_lw = float(bench["rt_lw"])
    ok = np.isfinite(rt) & np.isfinite(p_model)
    bind_all = g["bind"] & ok
    dem_sum = float(dem[ok].sum())
    up = np.maximum(0.0, rt - p_model)
    dn = np.maximum(0.0, p_model - rt)
    pp_ceiling = float((dem[bind_all] * up[bind_all]).sum() / dem_sum / rt_lw * 100.0)
    bind_s_ok = bind_s & ok
    rec["w5"] = {
        "bench_rt_lw": rt_lw,
        "n_binding_hours_2025": int(bind_all.sum()),
        "binding_share_of_annual_demand": float(dem[bind_all].sum() / dem_sum),
        "pp_ceiling_at_actual_all_binding": pp_ceiling,
        "pp_ceiling_at_actual_binding_S_only": float(
            (dem[bind_s_ok] * up[bind_s_ok]).sum() / dem_sum / rt_lw * 100.0
        ),
        "adverse_pp_exposure_model_above_actual": float(
            (dem[bind_all] * dn[bind_all]).sum() / dem_sum / rt_lw * 100.0
        ),
        "m160_slope_linear_projection_pp": float(
            (g["deficit"].sum() / 1e3) / (M160_GW * M160_HOURS) * M160_PP
        ),
        "pass": pp_ceiling >= W5_CEILING_PP,
    }

    # R2: the miso-161 confrontation — decompose the S-set deficit.
    junsep = np.isin(mon, (6, 7, 8, 9))
    p_u_g = g["p_u"]
    off_m = g["offline_m"]
    rec["r2_deficit_decomposition_2025"] = {
        "P_junsep_mean_gw": float(p_u_g[junsep].mean() / 1e3),
        "M_junsep_mean_gw": float(off_m[junsep].mean() / 1e3),
        "level_term_P_minus_M_junsep_gw": float(
            (p_u_g[junsep].mean() - off_m[junsep].mean()) / 1e3
        ),
        "record_increment_at_S_gw": float(
            (p_u_g[s_mask].mean() - p_u_g[junsep].mean()) / 1e3
        ),
        "model_sag_at_S_gw": float((off_m[junsep].mean() - off_m[s_mask].mean()) / 1e3),
        "deficit_mean_at_S_gw": float(g["deficit"][s_mask].mean() / 1e3),
        "note": (
            "deficit-at-S ~= level + record-increment + model-sag when binding "
            "is dense; the record-increment term alone is the miso-161 "
            "quantity (+0.69 GW, <=0.11 pp)"
        ),
    }

    verdict = {
        "W1_composition": bool(rec["w1"]["pass"]),
        "W2_level_congruence": bool(rec["w2"]["pass"]),
        "W3_bind_in_S": bool(rec["w3"]["pass"]),
        "W4_conversion": bool(rec["w4"]["pass"]),
        "W5_reach_ceiling": bool(rec["w5"]["pass"]),
        "W6_feasibility": all(
            bool(rec["per_year"][str(y)]["w6_pass"]) for y in YEARS
        ),
    }
    verdict["CHARTER_AB"] = all(verdict.values())
    rec["verdict"] = verdict

    OUT.write_text(json.dumps(rec, indent=1, default=float))
    return rec


if __name__ == "__main__":
    r = main()
    print(json.dumps({"verdict": r["verdict"]}, indent=2))
    for y in YEARS:
        s = r["per_year"][str(y)]
        am = s["annual_mean"]
        print(
            f"{y}: M {am['M_offline_gw']:.2f} GW | P_U {am['P_unplanned_gw']:.2f}"
            f" | P_ALL {am['P_allcause_gw']:.2f} | bind {s['bind_share_all_hours']:.1%}"
            f" | removed {s['removed_gwh_year']:,.0f} GWh"
            f" | top1%NL bind {s['top1pct_netload_bind_share']:.1%}"
            f" | W6 viol {s['w6_violation_days']}"
        )
    print("W3", r["w3"])
    print("W4", {k: v for k, v in r["w4"].items() if not k.startswith("_")})
    print("W5", r["w5"])
    print("R2", r["r2_deficit_decomposition_2025"])
