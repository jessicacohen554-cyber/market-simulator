# FINDING miso-194 — the MISO winter cold-snap gas derate is REFUTED at phase 0 on LP absorption; and MISO's armed outage envelope is measured COLD- and SCARCITY-INVERTED (2026-08-31)

**Session:** miso-194 (2026-08-31). **Keeper:** `2026-08-30-miso-191-bexit`
(bundle `results/calibration/miso191_bax_B`), **UNCHANGED**. **No LP solved,
nothing armed, no `ScenarioConfig` field added, no run registered** (the
miso-142/…/178/192 no-LP precedent; rule 15 `[R-DASHBOARD]` not engaged).

**Charter.** The miso-192-corrected census queue, lever 2: charter exactly ONE
of `gas_coldsnap_derate` (K@NEISO) or `winter_fuelsec_posture` (K@NEISO) —
never both (rule 19 `[R-ONE-MECH]`) — aimed at the Jan-2025 −1.43 pp winter
component of C3a-2025 named in FINDING-miso178 §1.

Instrument (read-only, idempotent, committed):
`scripts/probes/_miso194_coldsnap_derate_phase0.py` →
`results/calibration/_miso194_coldsnap_derate_phase0.json`. Every number below
reproduces by running that script.

---

## 0. Ask A — the zero-solve validation, reproduced exactly as handed off

| gate | result |
|---|---|
| `calibration_verdict --run-id 2026-08-30-miso-191-bexit` | **NOT-YET** at rubric v3.5 on **{C3a-2025 −12.3%} ALONE** |
| C1 | PASS, 16/16 · free 12/12 (pinned CC_CHP, ST_CHP) |
| C2 / C3b / C4 | PASS |
| C3c | the single **ledgered** caveat (all three years) |
| C6 governance / C8 forced-energy | PASS; C8 carries its two grounded above-budget notes (2023 CT_PEAKER 15.6%, 2025 ST_GAS 34.2%) |
| `audit_keepers --iso MISO` | **PASS, 0 failures / 0 warnings** |
| `build_status --iso MISO --check` | in sync |
| `check_mechanism_matrix.py` | integrity OK; keeper stamps and §5.x headers match |

Nothing drifted. Distance to band is unchanged at **+2.34 pp**.

## 1. Ask B — why `gas_coldsnap_derate`, and why `winter_fuelsec_posture` stays `U`

Chosen from the two NEISO cells' mechanism **shape only** — no parameter and no
verdict transfers (rules 25 `[R-ISO-SCOPE]` / 28(d)); every MISO quantity below
is derived from MISO's own admissible record.

1. **Direction.** The derate REMOVES gas capability in cold hours, so its price
   action is upward — the sign MISO's Jan-2025 −13.8% own-month under-price
   needs. `winter_fuelsec_posture` is a must-run **commitment floor**
   (`neiso_winter_fuel_mustrun` at min-stable + an oil-inventory budget): it
   ADDS forced inframarginal supply, whose price action is downward, i.e.
   adverse by construction on an under-priced target.
2. **It has a MISO object.** The fuel-security posture is an **ISO-NE program** —
   the FERC ER14-2407 Winter Reliability Program's oil-tank inventory, sized in
   barrels — with no MISO counterpart in kind; MISO's winter instruments are its
   cold-weather operating procedures and Maximum Generation Events, not a
   budgeted oil inventory, and MISO's oil-fired steam fleet is trivial. The
   derate's object — winter gas deliverability lost to heating load — is a
   physical driver **MISO's own published record measures** (§3).
3. **Rule 19.** `winter_fuelsec_posture` would stack a second must-run floor on
   ST_GAS, a class already reported **above** its C8 budget on this keeper
   (2025 ST_GAS 34.2% forced, grounded). The derate writes availability, where
   the target population carries no temperature-conditioned mechanism at all
   (§2).

**`winter_fuelsec_posture` therefore stays `U` in MISO's shard — considered and
NOT chartered, which is not a verdict and carries no DO-NOT-REDO.**

## 2. The frozen rule, and W1 — the rule-19 enumeration comes back clean

The full adjudication rule — target population, four bases, witnesses W1–W4,
the charter gate, the directional prereg and the materiality line — was frozen
in the probe docstring and **pushed at `57645d44` before any adjudicating
quantity was computed** (the miso-193 pattern). The mis-freeze lessons are
applied throughout: every witness derives from the same basis the mechanism
would read, the witnesses are **relations** (cold-response *ratios*), never
constants, and satisfiability (W3b) is verified on the control before the
relation is used.

**Target population (frozen ex ante, rule-19 exclusions applied up front):**
`CC_REGULAR`, `CT_PEAKER`, `ST_GAS`, non-dual-fuel, `pmax > 0`. That is the
NEISO group set with **every CHP class removed** — the keeper's armed
`temp_dependent_derate` is scoped to `['CT_CHP','ST_CHP']`, and the miso-192
CHP steam-host clamp class already governs cogen capability, so including them
would stack — and with **`ST_GAS` added**, MISO's gas-steam fleet being material
and carrying no temperature-conditioned mechanism. Dual-fuel rows are excluded
by the mechanism's own design and because the keeper arms `dual_fuel_switching`,
which already re-prices them to oil parity.

**W1 PASS — 0 violations.** Of the eleven availability-writing mechanisms armed
on the keeper, exactly three are temperature-conditioned, and none reaches the
target population: `temp_dependent_derate` is CHP-scoped; `gt_ambient_derate` is
off; `correlated_forced_outage` is off and doubly refused by
`apply_correlated_outage_derate` (`mode='backcast'`, `outage_source='historic'`).
The measured-window overlays (CAMPD unit / short / max-gen / layup), the summer
basis mechanisms and the WEFOR overrides are not temperature-keyed; they are
W2's subject, not W1's. **The lever does not stack.**

## 3. W2 — the documented double-count ground does NOT hold in MISO either

The repo carries an owner-charter ruling that a temperature-keyed cold-event
derate is a double count in a backcast: `apply_correlated_outage_derate` —
whose own docstring calls itself *"the `neiso_gas_coldsnap_derate` pattern,
generalized"* — refuses to fire when `outage_source == "historic"`, commented
*"measured overlays own the events (belt and braces)"* (FF-1B charter D.5).
**pjm-161 phase 0 measured that premise and falsified it for PJM.** W2 is the
same test, re-derived on MISO's own bases:

- **Basis M (model):** the keeper's own armed availability envelope from the
  load-bearing build; offline MW = Σ `pmax·(1 − availability)` over the target.
- **Basis P (published):** `miso_outage_mw_series(Y, "MISO", ("Forced","Derated"))`
  — MISO's own daily Multiday Operating Margin `OUTAGE` record. Rule-13
  admissible measured availability; never a price, never an outcome.
- **Basis T:** `iso_zone_tmax("MISO", …)` daily TMIN, target-MW-weighted across
  model zones — the same loader the armed `temp_dependent_derate` reads.

Cold-response ratio `R_X = mean(X | coldest DECILE of DJF days) / mean(X | mild
HALF)`, measured on each basis:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `R_P` published | 1.132 | 1.441 | **1.284** |
| `R_M` armed model envelope | 0.926 | 0.750 | **0.759** |
| **gap `R_P/R_M`** (line 1.25) | 1.222 | 1.920 | **1.691 → W2a PASS** |
| ρ(offline, TMIN) published | −0.189 | −0.248 | **−0.344** |
| ρ(offline, TMIN) model | +0.228 | +0.590 | **+0.581** |

Read the two ρ rows together. MISO's published record says what physics says:
**colder ⇒ more capacity offline** (ρ < 0, every year). The armed model envelope
says the opposite, and says it strongly: **ρ = +0.581 in 2025**, and `R_M = 0.759`
means the model asserts the target gas fleet is **24% MORE available on the
coldest DJF decile than on mild DJF days.** The mechanism behind it is the one
pjm-161 named: the CAMPD detector infers unavailability from **zero generation**,
so it cannot see an outage at a unit that would not have run anyway, and a unit
in layup **runs** when it is cold and prices rise — the envelope's error is
largest exactly where it matters. **The FF-1B D.5 double-count ground does not
hold for MISO.** There is a real gap; W2a passes at 1.691.

**W3 PASS both legs:** target population 45,283 MW = **62.4%** of MISO's gas
class (line 20%), 3,000+ rows; `iso_zone_tmax` returns a usable TMIN for zones
covering the population in all of 2023/2024/2025, so the mechanism is
satisfiable on the control rather than a silent no-op.

## 4. W4 — the LP absorbs it. This is what refutes the lever

Onset is **MISO-derived, never transferred**: `t0 = −7.31 °C`, the 10th
percentile of the pooled 2023–25 DJF daily target-weighted TMIN — a
distributional definition of deep cold, not NEISO's shipped −7.0. (That the two
land within 0.31 °C is a coincidence worth naming and is *not* how t0 was
obtained.) Binding hours = **408** DJF hours below it.

The removal magnitude is **measured, not assumed**: cold-excess
`E(t) = max(0, P(t) − mean(P | mild half of DJF))`, scaled to the target
population by its 39.3% share of MISO thermal capacity. Headroom `H(t)` is the
keeper's own unused capability — the target classes' LP bound
(`Σ pmax·availability`) minus their P1 dispatch in the committed
`class_hourly_2025.parquet`.

| W4, 2025 | value |
|---|---:|
| binding hours | 408 |
| median cold-excess `E` to remove | **1,219 MW** |
| median headroom `H` in those hours | **12,861 MW** |
| median DJF headroom (all hours) | 15,324 MW |
| hours with `E > H` (not absorbed) | **5 / 408 = 1.2%** |
| frozen line | **≥ 25%** |

**W4 FAILS by a factor of twenty.** The model sits on **10.5×** the surplus
needed to swallow the entire measured cold-event derate; in 98.8% of the hours
the mechanism could bind, removing the capacity changes no bound that is
binding. `CHARTER_AB = false`.

**This is exactly the failure mode the directional prereg named.** The frozen
prediction was "raises Jan-2025 price, C3a-2025 up", at **confidence 0.35** for
≥ +0.30 pp, and the two reasons stated against interest were (a) Jan-2025
carries only −1.43 of the −12.34 pp and (b) miso-178 §5 measures the model
already leaving 5+ GW of **real** gas idle in the stress hours — a
surplus-headroom regime in which removing availability is absorbed rather than
priced. W4 was the pre-registered test of (b), and (b) is what killed it.

## 5. Reported-only, added AFTER the gate resolved (disclosed; gates nothing)

**W5 — the reach ceiling for the whole winter-lever family**, in the scorer's
own basis (C3a reads the load-weighted model mean against bench `rt_lw`
= $45.46). The 408 binding hours are 4.66% of hours and **5.49% of annual
demand**, so a uniform +$1/MWh across every one of them moves C3a-2025 by
**+0.121 pp**. Clearing the declared **+0.30 pp materiality line needs +$2.48/MWh
in every binding hour**; reaching the band (+2.34 pp) needs **+$19.36/MWh**. For
scale, the model already prices those hours at **$57.81** — well above its own
annual load-weighted mean of $39.72 — and prices January at $43.15 against the
$51.52 actual. The winter hole is real but small, and W4 says the LP will not
convert this mechanism into price anyway.

**W6 — the pjm-161 NET-LOAD inversion, reproduced on MISO.** W2 asked whether
the envelope tracks temperature. pjm-161's original quantity asks whether it
hands the LP the most capacity in the **tightest** hours — a year-round question
that lands on the summer target owning 60% of C3a-2025 (miso-178 §1: Jun −3.28
+ Jul −3.69 pp):

| ρ(model offline MW, net load) | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| MISO (this session) | −0.607 | −0.698 | **−0.666** |
| PJM (pjm-161, for shape) | −0.68 … −0.77 in every year 2022–25 | | |
| top-1% net-load hours ÷ annual-mean derate — MISO | 0.63× | 0.70× | **0.78×** |
| — PJM (for shape) | 0.22–0.38× | | |

**The defect is the same defect, same sign, in MISO, in all three years**: the
armed envelope asserts 13.0 GW out on the average 2025 hour and only 10.2 GW in
the tightest 1% of hours. MISO's inversion is materially **milder** than PJM's
(0.78× vs 0.22–0.38×), which is a real difference and is reported as such — it
bounds how much a repair could be worth here.

## 6. Verdict, cell stamp, and what this session did NOT touch

**`gas_coldsnap_derate` in MISO: `U` → `I` (inert), adjudicated ZERO-SOLVE**
(the miso-179 / miso-193-cap-leg precedent for a zero-solve inertness mint).
The mechanism is admissible, unstacked (W1), addresses a real measured gap
(W2), and reaches a large satisfiable population (W3) — and the LP absorbs it
in 98.8% of the hours it could bind (W4), inside a family whose entire reach
needs +$2.48/MWh per binding hour to clear materiality (W5). It is not
rejected on the residual and not refused on governance: it is **measured
inert against this keeper's target**.

Honest limit on the stamp: W4 establishes absorption, not a formal proof of
zero price response — a multiplicative derate across the target stack can still
reshuffle which unit is marginal even with headroom. What is bounded is the
**magnitude**: any such reshuffle is confined below the marginal-unit spread in
5 of 408 hours, far under the +0.30 pp line.

**Not stamped, deliberately.** The outage-envelope rows — `campd_outage_windows`
(K), `historic_outage_overlay` (U), `miso_native_outage_source` (absent from the
keeper, default off) — are a **different object** this session did not test. W2b
and W6 are evidence about them, not verdicts on them.

**Not touched** (charter "not yours to decide"): the D-4 posture ruling, the
miso-141 §11 nameplate-basis switch, the C8 provenance-materiality floor, the
RHO_CLIP band, the miso-189 §7.3 residue. No holdout year: MISO holds no
`complete`/`final` marker and the holdout freeze is active.

## 7. The successor this hands the queue (named, not chartered — one lever per session)

**Repair the envelope; do not add a second mechanism on top of an inverted one.**
The coherent object W2b/W6 point at is a **remove-only measured cap on the CAMPD
outage envelope**, the pjm-161 shape, fed by MISO's own published Forced+Derated
record — which is already built (`data/miso_outages.py`,
`data/raw/miso-generation-outages/`, 2023-01-01 onward), already rule-13
argued, already gated behind `miso_native_outage_source` (default off), and has
a paste-ready wiring doc (`docs/handoffs/miso-native-outage-wiring-2026-07.md`).

Its case must come from the **net-load** channel (W6), not the temperature one:
the summer hours own 60% of C3a-2025, and W4 has already measured that the
winter channel is absorbed. Two things a future session must confront before
charter, stated now so they are not rediscovered: (a) MISO's inversion is
**milder** than PJM's, so the reach is correspondingly smaller and must be
bounded ex ante; (b) the published record is **aggregate** — region × cause,
with no unit or fuel identity (`_SOURCE.md`) — so the apportionment question
that refused a seam-grain entitlement cap at miso-176 (K-2) applies here too,
and the honest form is a fleet-grain remove-only cap, never an invented
per-unit split. `miso_native_outage_source`'s own module docstring already
flags that composition choice as "a calibration decision to be made and
validated in a future MISO calibration session."

Queue after this session, unchanged otherwise: `egrid_identity_heat_rates`
(K@NYISO), `tac_load_coverage` (K@CAISO), `lcr_tsl_published` (K@CAISO+NYISO).
