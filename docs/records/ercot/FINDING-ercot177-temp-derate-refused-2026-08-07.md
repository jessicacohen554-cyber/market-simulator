# FINDING — ercot-177: `temp_dependent_derate` at ERCOT is **REFUSED EX-ANTE**; the matrix cell was **STALE at `U`** and is corrected to `R` against a dated owner closure; a second, independent rule-19 ground is established; the `cc_nameplate_summer_derate` declared cell split is **DECIDED**

**Session ercot-177, 2026-08-07.** Charter: arm `temp_dependent_derate` at
ERCOT — matrix cell `U`, `K` at CAISO/MISO/NEISO, `R` at PJM, `G` at NYISO —
against **C3a-2023** (−32.4 % scorer) + **C3b** {2023 0.602, 2024 0.205}, the
fail set on keeper `2026-08-07-run176-control-offline-increment` (NOT-YET).

**NO PRECOMMIT WAS PUSHED, NO SLOPE WAS DERIVED, NO MEASUREMENT OF THE ARM WAS
TAKEN, NO LP WAS RUN, NO `ScenarioConfig` FIELD WAS ADDED, NO RUN IS
REGISTERED, AND THE KEEPER IS UNCHANGED.** The rule-28(a) `[R-MECH-MATRIX]`
DO-NOT-REDO check that must *precede* pre-registration **failed**, so the lever
never reached the precommit stage. Stated explicitly so the absence of a
registered run is not read as a skipped rule-15/16 registration (the ercot-175
§0 / ercot-176 Amendment 3 precedent), and the absence of a precommit is not
read as a lapse of the precommit-first discipline — the discipline is what
produced this outcome, one step earlier in the sequence than usual.

---

## 0. Verdict

| | |
|---|---|
| **Lever** | `temp_dependent_derate` (+ `temp_derate_hourly_grain`, `temp_derate_mean_anchored`, `temp_derate_classes`) at ERCOT |
| **Verdict** | **REFUSED EX-ANTE — DO-NOT-REDO breach.** The cell is not `U`; ERCOT tested this mechanism in full-keeper LP A/B solves and the owner closed it **REJECTED WITH CAUSE on 2026-07-09** |
| **Ground 1 (dispositive, prior record)** | ERCOT's own CEMS conduct refutes the mechanism at ERCOT: scarcity-hour capability slope **≈ 0 or NEGATIVE for every gas class**; measured hot-hour envelope **flat at 40–46 °C** |
| **Ground 2 (new, independent)** | Rule 19 `[R-ONE-MECH]` — the phenomenon is **already owned by an armed keeper mechanism** that did not exist in July: `ercot_thermal_dam_availability_hourly` (+`_plant`), whose docstring claims the hourly ambient-derate shape verbatim. A pre-overlay derate on any DAM-covered class is **arithmetically erased** by its water-fill (§3) |
| **Ground 3 (new)** | The ONE scope that would have been rule-19-clean — the **CHP classes**, 11.2 GW / 14.5 % of the ERCOT fleet and deliberately DAM-excluded — is where ERCOT's own measurement is **most strongly inverted**: CC_CHP **−1.41 %/°C** (§4) |
| **Matrix** | `temp_dependent_derate` ERCOT `U → R`, with the missing `E:` evidence key added and the stale "ERCOT/NYISO untested" sentence corrected |
| **Also delivered** | The `cc_nameplate_summer_derate` **DECLARED CELL SPLIT**, filed to this lane, is **DECIDED: two rows** (§5) |
| **Keeper** | **UNCHANGED** — `2026-08-07-run176-control-offline-increment`, NOT-YET, fail set {C3a, C3b} |

## 1. The charter premise, and why the check that refuses it runs first

The handoff's rule-1 case was stated honestly and is physically sound *in
general*:

> A thermal unit's output falls with ambient temperature; the ERCOT model
> carries no such physics, so it holds summer capability the real fleet did not
> have — in exactly the August evening hours that dominate the 2023 missed
> >$200 set.

Both of its factual premises are false **at ERCOT specifically**, and each was
already on the record before this session opened:

1. *"The ERCOT model carries no such physics."* It does — see §3. The keeper
   arms a measured, per-plant, per-delivery-hour capability overlay whose own
   docstring says it **owns the hourly ambient-derate shape**.
2. *"The real fleet did not have that summer capability."* ERCOT measured the
   opposite on its own fleet in July 2026: the TX fleet **hits its summer
   maxima on the hottest hours** (§2).

The handoff also correctly instructed that rule 25 `[R-ISO-SCOPE]` "is the whole
game here" and that no slope may be transferred. That instruction is right, and
following it to its conclusion is what closes the lever: ERCOT's own slope has
**already been measured**, and it is ≈ 0 or negative.

## 2. Ground 1 — the prior ERCOT record (dispositive)

The handoff's premise that the cell reads `U` is a **matrix defect**, not a fact
about the record. Verified directly in `docs/calibration-log.md`:

**The closure** (`docs/calibration-log.md:9752`):

> **Closure (owner decision, 2026-07-09) — temp-derate line REJECTED WITH CAUSE
> for ERCOT; keeper stays `2026-07-08-ercot46-clock-steamgas`.** … All four
> dashboard entries of the line (ercot48 pair, ercot49 pair) carry the rejection
> in their definitions.

**It was tested with LP solves, not by desk analysis.** Four dashboard
registrations: the `ercot48` full-keeper A/B (`scripts/probes/
_ercot48_tempderate_full.py` — the `ercot46_clock_steamgas` keeper's exact
`solve_and_persist` call with **only** `temp_dependent_derate=True`, all three
train years in one bundle) and the `ercot49` offer-retune pair
(`2026-07-09-ercot49-offer-retune-tempderate`, `…-retune-tempderate-ablation`).
The four sidecars were **retention-pruned on 2026-07-10** under the
top-15-per-ISO rule (`calibration-log.md:10745`) and the bundle dirs are gone
from disk. *The absence of artifacts is a retention artifact, not evidence of no
test* — which is very likely how the cell came to be misread as `U`.

**What the solves did to the object.** C3a **+269 / +161 / +42 %**
(`calibration-log.md:9603`) — the arm did not close a −32 % gap, it overshot by
up to +269 %, and its C3c "improvement" was adjudicated
**right-number-wrong-mechanism**: it manufactured the tail through physical
shortage (65 load-shed hours at VOLL) that both system telemetry and unit-level
CEMS refute.

**Three independent measured instruments, any one decisive**
(`calibration-log.md:9654`, `:9739`):

| instrument | measurement |
|---|---|
| Scarcity-hour p90 capability slope (RT > $200 hours, 30–46 °C) | CC_REGULAR **−0.27 %/°C**, CT_PEAKER **−0.04**, ST_GAS **−0.29**, **CC_CHP −1.41** — vs the model's +0.76/+1.26/+0.54 |
| Hot-hour capability envelope (CAMPD × zone TMAX, 2023+2024, 108 CC / 88 CT / 40 ST units) | at 40–46 °C: CC **1.00–1.01**, CT **1.08–1.09**, ST_GAS **1.00** — the fleet hits its summer maxima ON the hottest hours; the literature curves predict 0.77–0.93 |
| Telemetered RTOLCAP in the derated model's deep hours | **6.9–8.3 GW spare online** — the modelled shortage did not exist |

**The physical reason is ERCOT-specific and documented**
(`calibration-log.md:9690`): *"the TX fleet is equipped for TX summers (inlet
evaporative cooling/chillers), so net-summer capability already IS its hot-day
rating."* This is precisely a rule-1 `[R-STRUCT]` finding — the correct
structure for **this** fleet is that there is no material incremental hot-hour
derate below net-summer, and the model already represents that. The refusal is
therefore **not** a fit judgement, and rule 1's "a real market behaviour stays in
even if it makes the fit worse" does not apply: the behaviour is measured absent
in this ISO.

**The closure is load-bearing in two live ERCOT handoffs**, both under
do-not-relitigate headings:

* `docs/handoffs/ercot-offer-surface-conditional-2026-07.md:109` — "Physical
  scarcity (temp-derate) is CLOSED (owner 2026-07-09)", under **"Settled context
  (do not relitigate)"**.
* `docs/handoffs/ercot-ordc-capdual-adder-2026-07.md:126` — "Temp-derate
  CLOSED.", under **"6. Settled context (do not relitigate)"**.

Also carried at `docs/handoffs/ercot-retirement-composition-2026-07-16.md:93`,
`docs/handoffs/miso-89-session-findings-2026-07.md:63`,
`src/market_sim/config/scenarios.py:8915`, and inside the
`cc_nameplate_summer_derate` matrix row's own `def`. Only the **cell** was
never updated.

**Would-the-new-estimator-change-it?** `scripts/data/derive_campd_temp_derate_
params.py` (the within-day plant-day fixed-effects estimator) postdates the
ERCOT closure by nineteen days (written for miso-101, 2026-07-28) and has
**never** been run on ERCOT — there is no `campd_temp_derate_params_ERCOT*.csv`
on disk or in history. That is a genuine methodological difference and the only
colourable case for a re-test. It does not survive §3 and §4: the estimator
would be applied either to classes where the answer is already measured
directly and better (§3), or to the one class where ERCOT's existing
measurement is **most** adverse (§4). No derive was run.

## 3. Ground 2 (NEW, independent) — rule 19 `[R-ONE-MECH]`: an armed keeper mechanism already owns this phenomenon, and arithmetically erases any rival

This ground did not exist on 2026-07-09. The ERCOT-95/96/97 measured-DAM
availability line landed ~2026-07-22, *after* the closure, and it is armed on
the current keeper:

```
ercot_thermal_dam_availability         True
ercot_thermal_dam_availability_hourly  True
ercot_thermal_dam_availability_plant   True
ercot_thermal_dam_availability_coal    True
```

Its own docstring (`scenarios.py:8234-8240`) claims the exact phenomenon this
lever proposes to add:

> **Owns the hourly ambient-derate shape the day mean discards**: the ERCOT-95
> diagnosis … measured the flat block handing the model +216 MW mean (+433 p90,
> +578 max) phantom CC+CT capacity on the 181 actual 2023 RT tail hours — **real
> HSL dips below its day mean exactly in the hod 13-19 afternoon window where
> the missing scarcity tail sits**.

So the model **does** carry an afternoon capability dip, sourced from ERCOT's own
published 60-Day DAM live HSL, per delivery hour, per crosswalked plant. Under
rule 14 `[R-ACCURATE]` a measured per-plant hourly HSL strictly dominates a
class-level regression slope applied to a station-interpolated zone dry-bulb;
under rule 19 a second mechanism for the same phenomenon must **reconcile, never
stack**.

**It does more than dominate — it erases.** The temperature derate is applied in
`_availability_matrix` (`arrays.py:817-878`); the DAM overlay is applied later,
in `_apply_outage_overlays` (`arrays.py:1310-1459`) — call order
`arrays.py:2632` then `:2636`. The class-HOUR water-fill (`arrays.py:1430-1447`)
is:

```
cur = cap-weighted mean availability at hour h        # POST temp derate
restore (t >= cur):  a' = a + lam * (ceil - a),  lam = (t-cur)/(ceil_mean-cur)
remove  (t <  cur):  a' = a * (t/cur)
```

Both branches drive the cap-weighted class-hour mean to **exactly `t`**,
independent of `cur` — hence independent of any pre-overlay derate:

* restore: `mean(a') = cur + lam*(ceil_mean - cur) = cur + (t - cur) = t`
* remove: `mean(a') = cur * (t/cur) = t`
* saturated (`t > ceil_mean`, `lam` clipped to 1): `a' = ceil` for **every**
  unit — the arm and control become bit-identical.

Verified numerically against a verbatim transcription of those lines
(`scripts/probes/ercot177_waterfill_identity.py`): with and without a
temperature derate applied first, the post-overlay class-hour mean matches the
measured target to **5.6e-16**, and the arm-minus-control difference **at the
class-hour mean is 4.2e-16** — zero. *(This is an arithmetic property of the
committed code, established on synthetic arrays. It is NOT a fleet measurement
and no fleet measurement was taken.)*

What survives is only a **within-class redistribution** (per-unit max deviation
0.22 in the check), and because the derate is per-class × per-zone, that
redistribution is purely **zonal**. With `ercot_thermal_dam_availability_plant`
armed — as it is — every crosswalked plant is pinned to its **own** measured
site-hour fraction, which removes even that for the mapped population, and
ERCOT-97 already declares within-class redistribution to be *its* object ("a
within-class REDISTRIBUTION (which plant carries the derate), not a level
change").

**Covered classes** (`data/raw/ercot-thermal-dam-availability-hourly.csv`):
`CC_REGULAR`, `COAL`, `CT_PEAKER`, `ST_GAS` — with the coal gate armed, all four
are live. That is **62.1 GW of 77.6 GW** of the ERCOT fleet, i.e. **80 %**, on
which the lever is inert-or-double-counting by construction.

**The coal reconciliation the handoff asked for, enumerated.**
`coal_nameplate_summer_derate` is **armed on this keeper** and is a seasonal
capability derate on the same availability matrix
(`arrays.py:765-768`). It is applied **outside** the `if not _td_covers(gen)`
guard, and COAL is absent from `SUMMER_CLASS_DERATE`, so `_anchor` is `None` for
COAL and the raw temperature curve would be applied **directly on top of** the
net-summer ratio — an unguarded rule-19 **stack**, not a reconciliation. Any
ERCOT arm would therefore have had to exclude COAL by class scope. Moot here,
but recorded: a successor must not discover this at the seam.

## 4. Ground 3 (NEW) — the one rule-19-clean scope is where ERCOT's own data is most adverse

Working the rule-19 enumeration forward before consulting the record, the only
ERCOT scope with no incumbent owner is the **CHP family** — deliberately
DAM-excluded (`scenarios.py:8162-8165`: *"CHP is deliberately NOT DAM-covered
(rule 14: no CHP flag, and the private-use cogens are partly behind-the-meter)"*).
It is not a token scope:

| class | rows | capacity | share of ERCOT fleet | DAM-covered? | floored? |
|---|---|---|---|---|---|
| CC_CHP | 79 | 9,030 MW | 11.64 % | no | no |
| CT_CHP | 51 | 2,056 MW | 2.65 % | no | no |
| ST_CHP | 6 | 128 MW | 0.16 % | no | no |
| **total** | 136 rows / 42 plants | **11,214 MW** | **14.45 %** | — | — |

ERCOT CHP carries **no `chp_grid_pmin_mw` floor and no must-run flag** (0 of 136
rows), unlike MISO's floored cogens — so a capability reshape there would
genuinely bite on dispatch. On paper this was the arm to build, and it is the
same family MISO's `K` covers.

**ERCOT's own measurement refutes it, and by the widest margin of any class.**
The 2026-07-09 scarcity-hour derivation puts **CC_CHP at −1.41 %/°C**
(`calibration-log.md:9739`) — negative, i.e. capability *rising* with
temperature, and the largest magnitude in the ERCOT fleet. That is exactly the
failure that took NYISO from `U` to `G` at nyiso-111: a negative within-day
slope is *"physically impossible for a gas turbine … it is the … DISPATCH shape,
not an ambient capability response"*. Running
`derive_campd_temp_derate_params.py --iso ERCOT` on the cogen pair would be
running a **different estimator against a class whose response ERCOT has already
measured with the wrong sign** — and, per rule 25, the only admissible
remedy (ERCOT's own slope) is the very number that refutes it. No derive was
run, and no ERCOT parameter file was created.

**Two design decisions reached before the check completed, recorded so the work
is not lost to a successor** (neither was implemented; both are moot):

* **`temp_derate_hourly_grain` would have had to be armed.** The day-flat TMAX
  input carries zero hour-of-day signal (miso-100 §4/§5), so a day-flat arm
  cannot address an hour-of-day object at all.
* **The anchor is part of the mechanism, and at ERCOT *neither* convention is
  level-neutral** — the miso-139(a)/(b) dilemma reproduces here with ERCOT's
  numbers. Hinged + summer anchor preserves the summer mean but the
  unconditional `_anchor / mean(raw[summer])` rescale is a **year-round level
  cut** whenever the measured slope is small: at ERCOT summer
  `mean(max(0, T−15)) ≈ 14 °C`, so the rescale is neutral only at
  `s ≈ 0.0071`/°C for CC_CHP, and a MISO-sized `s = 0.00141` would impose a
  **≈ 8 % year-round capability cut**. Mean-anchored is annual-neutral by
  construction but, since ERCOT summer sits ~9–10 °C above the annual mean,
  cuts the summer mean by `s × ΔT` for **every** `s > 0` — miso-139's structural
  result, unchanged by the ISO. Any successor must pre-register a
  level-neutrality counter-measurement on the model's own availability matrix
  and a refusal bar, exactly as miso-139 did.

## 5. The `cc_nameplate_summer_derate` DECLARED CELL SPLIT — DECIDED: **two rows**

That row's `def` filed the decision to this lane verbatim: the coal analogue
`coal_nameplate_summer_derate` was registered **literally inside the CC row**
under rule 28(c) (xiso-3 census), and is **armed on the ERCOT keeper** while the
row's own CC flag is `False` there — so the ERCOT cell reads `U`, correctly for
the row's own flag but misleadingly for the family. The note left open "whether
the family warrants **two rows or one re-scored cell**".

**Decision: two rows.** `coal_nameplate_summer_derate` gets its own row, cells
`K.UU..` (ERCOT `K`; CAISO/NYISO/NEISO `.` on materiality — 2 / 0 / 1 coal fleet
rows respectively; PJM/MISO `U` — 90 / 109 coal rows, plausibly applicable,
untested). Reasons, in order:

1. **A one-character cell cannot represent two booleans with different verdicts
   in the same ISO.** This is a representational impossibility, not a labelling
   preference. Re-scoring the single cell to `K` would assert that the CC leg is
   keeper-armed at ERCOT, which is false; leaving it `U` conceals a keeper-armed
   mechanism. Both options misreport.
2. **Rule 28(c)'s purpose is a verdict-bearing cell, not a string match.** The
   CI gate is explicitly "mention-anywhere … checks registration, not taxonomy"
   (`check_mechanism_matrix.py` docstring). A field registered only inside
   another row's prose satisfies the gate but can never carry a verdict in any
   ISO — the "unregistered tuning channel in spirit" the rule exists to prevent.
   `coal_nameplate_summer_derate` changes availability and is armed in a keeper;
   it needs a cell.
3. **In-file precedent.** `cc_capacity_reconcile` / `cc_capacity_reconcile_path`
   are already split for the same reason — a distinct solve-affecting field gets
   its own row rather than living as prose on a sibling.
4. Rule 28(d) is respected: the split **mints no verdict from another ISO**.
   ERCOT's `K` is read from the ERCOT keeper's own `run_config.json`; every
   other ISO enters at `U` or `.`.

The CC row's literal registration is replaced by a pointer to the new row and
its declared-mismatch paragraph retired as **resolved**; the CC row's own cells
are **unchanged** (`UUUUKU`).

## 6. What this means for the object (C3a-2023), stated without proposing a lever

The numbered ERCOT queue is spent and this session was not chartered to open a
new one, so this is a pointer, not a proposal:

* The handoff's reasoning — "every OFFER-PRICE lane on this ISO is now closed …
  the record has repeatedly re-pointed the 2023 residual to a
  QUANTITY/CAPABILITY object" — is sound in its first half and **does not follow**
  in its second. ercot-175 measured the opposite directly: reality delivered
  51.95 GW of sub-$200 energy against the model's dispatched ~51.9 GW, so *"the
  missed >$200 formation is a MARGINAL-PRICE phenomenon, not a quantity
  phenomenon"*. A capability lever is pointed away from the object by the
  ERCOT record, independently of everything above.
* With the ambient-capability route closed on measurement (§2) and the
  aggregate-quantity route closed at ercot-173/175, the capability family at
  ERCOT is now bounded on both faces. Whoever charters next should not read
  "the offer lanes are closed" as "therefore capability" — that inference has
  now failed twice.

## 7. Owner items

1. **Carried, NOT acted on — the ercot-176 rule-18 grain defect.** Fleet
   assembly records unit physics on the `committed` tranche only, so every
   `econ*`/`peak*` bid row reads `min_down = min_run = 0` and the armed keeper
   mechanism `ercot_faststart_pool_offer` admits every CT bid row regardless of
   physics. In scope for this session **only if the owner authorized it
   in-session**; **no authorization was given**, so it was not touched. It moves
   the keeper and needs its own pre-registered round.
2. **New — how a stale cell mis-chartered a session.** This is the second
   ERCOT charter in three sessions to rest on a premise the record had already
   refuted (ercot-176 §1 withdrew ERCOT-151 §0.2 the same way). Both were caught
   by the pre-registration discipline before any LP time was spent, which is the
   system working. The specific repairable cause here is narrower and worth
   noting: the matrix row had **no `E:` evidence key at all**, and its note still
   carried the pre-2026-07-09 sentence "ERCOT/NYISO untested" through two later
   edits. A cell with no evidence key for an ISO whose lane has a dated closure
   is the detectable signature; a CI leg asserting "every non-`U` cell has an
   `ev` key, and every ISO named in a row's note has one" would have caught it.
   **Filed, not built** — it is a `check_mechanism_matrix.py` change and belongs
   to a governance round, not to this lane.
3. **The ERCOT-148/149 double-count memo** (`docs/handoffs/DECISION-MEMO-ercot-
   148149-doublecount-2026-08-07.md`) stays **PENDING**; the ceiling lane was not
   entered and its recommendation was not acted on.

## 8. Governance

* **Rule 28 `[R-MECH-MATRIX]`:** duty (a) performed and **it is what produced
  this finding**; duty (b) discharged — the `temp_dependent_derate` ERCOT cell
  moves `U → R` with its evidence citation, in this session. Duty (c) n/a (no
  field added). Duty (d) respected in the §5 split. The matrix header keeper
  stamp was re-checked against `frontend/data/backcast/keepers/ERCOT.json`.
* **Rules 15/16 `[R-DASHBOARD]` / `[R-ALLYEARS]`:** no solve was run, so no run
  is registered and no bundle exists — stated explicitly in the header. The
  keeper is untouched, so no re-key, no `build_status.py`, and no
  `calibration-keeper-auditor` run applies.
* **Rule 22 `[R-HOLDOUT]`:** no year was solved, scored, read or registered.
  ERCOT holds no `complete` and no `final` marker; 2022 / 2021 / 2020 / 2019 /
  H1-2026 were not touched, and the out-of-training quarterly files in
  `data/raw/ercot-weather/` were not read. No `calibration-complete.json` re-key
  applies.
* **Rule 23 `[R-FROZEN-DERIVE]`:** no derive was run and no parameter
  re-identified.
* **Rule 24 `[R-REGISTRY]`:** no `ScenarioConfig` field added, removed or
  defaulted differently; no env-var knob; no per-plant dict.
* **Rule 25 `[R-ISO-SCOPE]`:** no slope was transferred into ERCOT from any ISO.
  The instruction to derive ERCOT's own was followed to its conclusion —
  ERCOT's own is already measured, and it refuses the mechanism.
* **Rule 26 `[R-DELETE]`:** nothing deprecated, nothing zeroed. The
  `temp_dependent_derate` fields stay at their defaults and remain live for the
  three ISOs whose keepers arm them.
* **Rule 27 `[R-PUSH]`:** no source file ≥300 lines was rewritten. Every push
  touching one is blob-verified against the **remote** blob before the next
  commit.
* **GitHub Actions:** no workflow added; no CI job used for any task work.

**DO-NOT-REDO honoured in full** — and it is the operative finding rather than a
footnote. Not entered, not re-litigated, not re-tested: the event-cap **ceiling
lane** (FROZEN; its memo stays PENDING and was not acted on); the
offline-increment slow-start tier (`I`); the ERCOT-151 §0.2 premise (REFUTED,
not quoted forward); blanket `min()` (`R`); unit-scoped (`R`); the 2023
depth/excess-cheap-depth premise (REFUTED); the reserve-side family (CLOSED);
no ramp mechanism (`ramp_envelopes` `R`); `ercot_storage_rt_offer_surface`
(`R`); `energy_online_capability_cap` (`R`); the CC-headroom crosswalk
(FILED-UNLICENSED); all coal offer lanes (CLOSED); per-year CT re-identification
(REFUSED); West/Panhandle (CLOSED); ercot-172's C3 (REFUSED, rule 13); no
per-hour telemetered-HSL cap; no aggregate capability cap.

**Next shorthand: ercot-178.**
