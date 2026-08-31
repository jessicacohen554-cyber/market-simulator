"""miso-194 phase-0 census: a MISO winter cold-snap gas derate (zero-solve).

Charter: the miso-192-corrected census queue, lever 2 — CHARTER exactly ONE of
matrix rows ``gas_coldsnap_derate`` (K@NEISO) or ``winter_fuelsec_posture``
(K@NEISO), never both (rule 19 [R-ONE-MECH]) — aimed at the Jan-2025 −1.43 pp
winter component of C3a-2025 named in FINDING-miso178 §1. Keeper at session
start and throughout: ``2026-08-30-miso-191-bexit`` (bundle
``results/calibration/miso191_bax_B``), Ask-A reproduced NOT-YET on
{C3a-2025 −12.3405%} ALONE, C1 16/16 / 12/12 free, C3c the single ledgered
caveat, C6 attested, C8 PASS (two grounded notes); ``audit_keepers --iso MISO``
PASS 0/0; ``build_status --iso MISO --check`` in sync; ``check_mechanism_matrix``
integrity OK.

THE CHOICE (Ask B), made from the two NEISO cells' mechanism SHAPE only — no
parameter and no verdict transfers (rules 25 [R-ISO-SCOPE] / 28(d)); MISO's own
numbers are derived below from MISO's own admissible record:

  CHARTERED: ``gas_coldsnap_derate``. (1) DIRECTION. It REMOVES gas capability
  in cold hours, so its price action is upward — the sign MISO's Jan-2025
  −13.8% own-month under-price needs. ``winter_fuelsec_posture`` is a must-run
  COMMITMENT floor (neiso_winter_fuel_mustrun at min-stable + an oil-inventory
  budget): it ADDS forced inframarginal supply, whose price action is downward,
  i.e. adverse by construction on an under-priced target. (2) IT HAS A MISO
  OBJECT. The fuel-security posture is an ISO-NE PROGRAM — the FERC ER14-2407
  Winter Reliability Program's oil-tank inventory, sized in barrels — with no
  MISO counterpart in kind; MISO's winter instruments are its cold-weather
  operating procedures and Maximum Generation Events, not a budgeted oil
  inventory, and MISO's oil-fired steam fleet is trivial. The cold-snap gas
  derate's object — winter gas deliverability lost to heating load — is a
  physical driver MISO's own published record measures (below). (3) RULE 19.
  ``winter_fuelsec_posture`` would stack a second must-run floor on ST_GAS, a
  class already reported ABOVE its C8 budget on this keeper (2025 ST_GAS 34.2%
  forced, grounded); the derate writes availability, where the target
  population currently carries no temperature-conditioned mechanism at all
  (W1 below tests exactly that). ``winter_fuelsec_posture`` therefore stays
  **U** in MISO's shard, untested and un-transferred.

WIRING NOTE (stated ex ante, not an adjudicating quantity): the implementing
function ``model.interchange.neiso.inject_neiso_gas_coldsnap_derate`` hard-gates
``if iso != "NEISO": return False`` and reads a NEISO-only temperature wrapper,
so an arm would require a generalization + a MISO-scoped ``ScenarioConfig``
field (rule 28(c): a new row + a cell line in every shard, same PR). Phase 0 is
what decides whether that code is worth writing. NOTHING IS ARMED HERE.

THE DOCUMENTED SUPERSEDING-MECHANISM PROBLEM, named before it is tested
(the charter's "anticipate documented superseding mechanisms"): this repo
already carries an owner-charter ruling that a temperature-keyed cold-event
forced-outage derate is a DOUBLE COUNT in backcast mode.
``data.outages.apply_correlated_outage_derate`` — whose own docstring calls
itself "the neiso_gas_coldsnap_derate pattern, generalized" — refuses to fire
when ``mode != forecast`` and again when ``outage_source == "historic"``, with
the comment "measured overlays own the events (belt and braces)" (FF-1B charter
D.5). The MISO keeper is a backcast with ``outage_source='historic'`` and the
CAMPD unit-outage overlay armed, so that ruling points straight at this lever.
It is NOT, however, a settled bar: pjm-161 phase 0 MEASURED the ruling's
premise and falsified it for PJM (the CAMPD detector infers unavailability from
ZERO GENERATION, so it cannot see an outage at a unit that would not have run
anyway; corr(derated MW, net load) −0.68..−0.77 in every year, and during Winter
Storm Elliott the envelope asserted its LOWEST outage level of the year against
PJM's published 40.7 GW forced). W2 below is that same test, re-derived on
MISO's own bases. Read for shape; every MISO number is MISO's own.

FROZEN ADJUDICATION RULE (ex ante, pushed before any adjudicating quantity —
the miso-193 pattern; the miso-191 mis-freeze lessons applied: every witness
derives from the SAME basis the mechanism would read, the witnesses are
RELATIONS not constants, and satisfiability is verified on the control before
the relation is frozen):

  TARGET POPULATION (frozen; rule-19 exclusions applied up front). MISO plant
  groups ``CC_REGULAR``, ``CT_PEAKER``, ``ST_GAS``, restricted to non-dual-fuel
  rows with ``pmax > 0``. This is the NEISO group set with EVERY CHP class
  removed — the keeper's armed ``temp_dependent_derate`` is scoped to
  ``['CT_CHP','ST_CHP']`` and the miso-192 CHP steam-host clamp class already
  governs cogen capability, so including them would stack (rule 19) — and with
  ``ST_GAS`` added, MISO's gas-steam fleet being material and carrying no
  temperature-conditioned mechanism. Dual-fuel rows are excluded by the
  mechanism's own design and because the keeper arms ``dual_fuel_switching``,
  which already re-prices them to oil parity.

  BASES (each the exact object the mechanism or its witness would read):
    M (model, armed envelope): the load-bearing build
      ``load_fleet_from_csv → fleet_to_bins → bins_to_fleet →
      generators_to_fleet_arrays(config=<keeper cfg>, iso="MISO", year=Y)``.
      Offline MW at hour t = Σ over target rows of ``pmax·(1 − availability)``.
    P (published, measured): ``data.miso_outages.miso_outage_mw_series(Y,
      region="MISO", cause_types=("Forced","Derated"))`` — MISO's own daily
      Multiday Operating Margin OUTAGE record (``_SOURCE.md``; rule-13
      admissible measured availability, never a price and never an outcome).
      Forced+Derated only: ``Planned`` is not weather-driven and ``Unplanned``
      is a superset that would double-count ``Forced``.
    T (temperature): ``data.eia930.weather.iso_zone_tmax("MISO", Y, 8760,
      zone=z)`` daily TMIN — the SAME loader the armed ``temp_dependent_derate``
      reads — aggregated across model zones weighted by each zone's target-
      population MW.

  W1 RULE-19 EXCLUSIVITY (load-bearing, boolean). Enumerate every mechanism
  armed on the keeper's ``run_config.json`` that writes a TEMPERATURE-
  CONDITIONED availability change onto the target population. PASS iff the
  count is 0. (Measured-window overlays — the CAMPD unit/short/maxgen/layup
  derates, the summer-basis and WEFOR mechanisms — are not temperature-
  conditioned and are reported, not gated; they are W2's subject, not W1's.)
  FAIL ⇒ the lever stacks and is refuted here.

  W2 THE DOUBLE-COUNT TEST (load-bearing; pjm-161 shape, MISO bases). Define,
  for a basis X and year Y, the COLD-RESPONSE RATIO
      R_X(Y) = mean(X over the coldest DECILE of DJF days by T)
             / mean(X over the MILD HALF of DJF days by T).
    W2a (GATED, 2025): the armed model envelope leaves a real gap iff
        R_P(2025) / R_M(2025) ≥ 1.25,
      i.e. basis M reproduces LESS THAN 80% of the published relative cold
      response. RATIOS, never levels: M covers the modeled thermal fleet and P
      covers all MISO capacity of every fuel, so a level comparison is
      basis-misaligned (the miso-141 basis lesson). R_X is reported for 2023
      and 2024 as well; the gate reads 2025, the charter's target year.
    W2b (REPORTED, never gated, against interest either way): Spearman
      corr(daily offline MW, daily T) over DJF for both bases. Basis M with
      corr ≥ 0 while basis P has corr < 0 is the pjm-161 inversion signature.

  W3 POPULATION & SATISFIABILITY (load-bearing).
    W3a: target-population MW ≥ 20% of MISO total gas-class MW on the keeper
      build. Below ⇒ the mechanism cannot be material whatever its curve.
    W3b (satisfiability on the control, verified BEFORE any relation is
      frozen): ``iso_zone_tmax`` must return a non-None TMIN for model zones
      covering ≥ 50% of target-population MW, in ALL of 2023/2024/2025. A
      missing TMIN makes the mechanism a silent no-op and the A/B impossible.

  W4 LP ABSORPTION (load-bearing; "would it move price at all", read from the
  keeper's OWN committed hourly sidecars — zero-solve).
    Onset ``t0`` is MISO-DERIVED, never transferred: the 10th percentile of the
      2023–2025 DJF daily T series of basis T (a distributional definition of
      deep cold). BINDING HOURS = DJF hours with T < t0.
    The removal magnitude is MEASURED, not assumed: cold-excess
      ``E(t) = max(0, P(t) − mean(P over the MILD HALF of DJF days))``, scaled
      to the target population by its share of MISO thermal capacity.
    HEADROOM ``H(t)`` = Σ over target classes of the keeper's own unused
      capability = (Σ target-row ``pmax·availability`` from basis M) − the
      P1 dispatch of those classes in ``hourly/class_hourly_<Y>.parquet``
      (the class sidecar carries dispatch only; this difference is exactly the
      LP's own unused bound).
    FROZEN RELATION: the removal is NOT absorbed at t iff ``E(t) > H(t)``.
      PASS iff that holds in ≥ 25% of 2025 binding hours. Below the line the LP
      absorbs the derate against standing surplus and the lever is inert on
      price whatever its magnitude.

  CHARTER GATE: an LP A/B is chartered iff W1 ∧ W2a ∧ W3a ∧ W3b ∧ W4. ANY
  load-bearing miss ⇒ REFUTE: stamp the MISO ``gas_coldsnap_derate`` cell with
  the citation, write the FINDING, STOP (one lever per session, charter E).

  DIRECTIONAL PREREG (ex ante, with confidence, per the charter): IF chartered,
  the arm raises MISO mean LMP and moves C3a-2025 UP (less negative).
  CONFIDENCE that it delivers ≥ +0.30 pp on annual C3a-2025: **0.35** — stated
  low and against interest, because (a) Jan-2025 carries only −1.43 pp of the
  −12.34 pp miss (FINDING-miso178 §1) and (b) miso-178 §5 measures the model
  already leaving 5+ GW of REAL gas idle in the stress hours, a
  surplus-headroom regime in which removing availability is absorbed rather
  than priced. W4 is the pre-registered test of exactly that failure mode.
  Whatever the sign, it is reported at full magnitude.

  MATERIALITY LINE, declared: a lever that cannot plausibly reach +0.30 pp of
  annual C3a-2025 is not worth a two-leg solve at this frontier (the distance
  to band is +2.34 pp; miso-193's bands carried ~1.0–1.3 pp/yr for comparison).

Rule 21 [R-DOF]: this probe adds ZERO solve inputs and has zero free
parameters; the 1.25× / 20% / 50% / 25% / p10 / decile / mild-half lines are
ex-ante adjudication thresholds of the census, not model parameters. Rule 13
[R-MEASURED]: both measured inputs (the MISO OUTAGE record, the curated MISO
weather series) are physical availability/weather quantities that regenerate
for a forward year and respond to changed conditions; no price, no residual and
no measured outcome enters any witness.

Read-only and idempotent. Output:
``results/calibration/_miso194_coldsnap_derate_phase0.json``.
"""
