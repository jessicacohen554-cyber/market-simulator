# DECISION CARD — L-SCAR-SCREEN-1: a screen-side scarcity-revenue mechanism for ERCOT retirement/entry

> Status: RECORD — S1/S2/S3 SIGNED at the owner sitting, 2026-08-13 (see RESOLUTIONS at the foot). Assembled by session
> l-scar-screen-1, 2026-08-13, HEAD `9c52ea8`. **PLANNING ONLY: no LP was
> solved, no derive was run, no `ScenarioConfig` field was added, no matrix
> cell was minted, no run was registered, and no default moved.** Every number
> below is read off committed artifacts, each cited where quoted.

**The owner's concern, verbatim:** *"I refuse to believe there is no way to
address high scarcity years like 2023 adequately in my model as it will yield
retirements that are not realistic in forecast."*

**The object:** `program-status.json` open_frontier **rank 2** — "ERCOT screen
revenue level + in-year scarcity" (lane L-SCAR / G-20/G-22, residual
≈ 56–66 $/kW-yr to SOM). This charter is for the **retirement/entry screen
only** (capacity-evolution steps 3/5). The dispatch-side route is **CLOSED and
stays closed**: card Q ran to its checkpoint, the licence read FAILED at
ercot-191, and **(Q-B) is automatic and final** — no further ERCOT C3a-2023
backcast spend. The price tail is an accepted model-class limitation,
quantified at DECISION-CARD-ercot189 §2 and disclosed at ercot-190
(`readiness_limits`: up to −$14/MWh, −22 % of level, in a 2023-like
scarcity-concentration year, concentrated in ~2 % of hours). Nothing in this
charter re-opens any of that; the charter exists because the **same accepted
limitation propagates into the screen**, where — unlike the scored price
series — the program is still allowed, and obliged, to act.

---

## 0. THE BOARD

| card | decision | blocking? | recommendation |
|---|---|---|---|
| **S1** | Is the tightness-conditioned residual scarcity-rent term (§2, option L-1) rule-13-admissible for the screen, or does FFR-6A verdict row 4's refusal reach it? | blocks the whole lane | **ADMISSIBLE as chartered — with the §2.6 distinction owner-signed, not assumed** |
| **S2** | Which option runs: L-0 do-nothing / L-1 residual rent term / L-2 E1-dispersion first / L-3 co-opt-only? | sequencing + budget | **L-1, with L-2 named as its structural complement, never its substitute** |
| **S3** | Does the implementing A/B run now at the armed stage-B posture (control re-solved at HEAD), or wait behind OVERRIDE-FIX? | timing only | **Run now; PROMOTION (if ever) waits for OVERRIDE-FIX** (§5.3) |

One sitting, three signatures. §§1–6 are the evidence.

---

## 1. THE DEFECT, SIZED FROM COMMITTED ARTIFACTS

### 1.1 The residual, in the gate's own units

The screen values a merchant thermal unit's year as
`net_revenue = Σ_t max(0, price − mc, r) × pmax × availability` against a
FOM-only going-forward bar (`retirements.py::apply_economic_retirements`;
CLAUDE.md step 3). The price/reserve object it consumes systematically misses
the scarcity/AS rent the real market paid:

| instrument | measured value | source |
|---|---|---|
| CT screen net revenue vs Potomac SOM CT anchor (≈68 $/kW-yr, 2024) | screen 1.8–11.9 $/kW-yr → **residual ≈ 56 $/kW-yr (event year) / ≈ 66 (event-free), co-opt off; ≈ 51 co-opt-on** | `ff-1b-correlated-availability-2026-07-17.md` §2.2/§4; `ercot-retirement-composition-2026-07-16.md` §C |
| Per-fuel replica margins at MEASURED prices vs the screen's own margins, 2024 screen | replica coal 75.4 / cc 86.7 / ct 65.6 / st 65.6 $/kW-yr; screen (FFR-8A repair arm) 0.05 / 8.94 / 0.69 / 0.01 | `ffr-8a-scarcity-restoration-2026-08-08.md` §4.1 |
| — same, 2025 screen | replica 97.2 / 76.4 / 47.0 / 47.0; screen 16.96 / 20.53 / 19.37 / 17.13 (18–41 % of replica) | same |
| The dispatch-side view of the same object (convergent sizing) | top-50 gap hours: model clears $468 vs measured $1,922 — a $1,454/MWh mean miss over 50 h ≈ **$73/kW-yr** for a unit capturing those hours | `DIAGNOSIS-ercot177…` §3, carried at DECISION-CARD-ercot189 §1.2/§2.3 |
| SOM anchors themselves (the identification source) | new-CT net revenue 224–257 (2023) / **68** (2024) / 52.6 (2025); new-CC 228–272 / 89 / 83; PNM ~264 / ~99 / ~79 $/kW-yr | `cross-model-corridor-2026-07-13.md` §2.1; PDFs on disk `data/raw/ERCOT/`, transcription `data/raw/som-competitive-conduct/` |

Three independent instruments (screen diagnostic, measured-price replica,
dispatch tail read) land on the same **≈ 50–70 $/kW-yr-class-year** hole, and
the anchors say why it is scarcity-shaped: the market's CT rent tripled in the
2023 scarcity year (224–257 vs 52–68 in quiet years) while the model's screen
object barely moves.

### 1.2 Why the structural repairs cannot close it (measured, not asserted)

The design-faithful repair of the screen's price object has already been built
and measured (FFR-8A, `capacity_screen_unified_lookahead` +
`capacity_screen_scarcity_restoration`, armed for ERCOT since a71fc84):

- The measured 2024/2025 scarcity content is **λ-led, not adder-led**: of
  2024's 184 λ>$100 hours, 149 had ORDC adders ≤ $10; the adder proper
  contributed >$100 in 5 h (2024) / 1 h (2025) (`ffr-8a` §2.3).
- The full pre-registered repair chain (committed reserves + AS hold +
  outage-uncertainty quadrature) restores **~1–21 $/kW-yr against a
  47–97 $/kW-yr replica gap**, leaves the 2024 screen at zero scarcity-hour
  content, and by its own pre-registered statement *"prices fundamentals plus
  design scarcity, not real-time offer conduct"* (`ffr-8a` §2.5/§4.1).
- The correlated-outage availability model (FF-1B) moved the event-year screen
  6.4 → 11.9 $/kW-yr — ~17.5 % of the SOM anchor — and cannot reach event-free
  years at all (`ff-1b` §2.2).
- The G-20/G-22 co-opt increment is measured at **+~15 $/kW-yr** (CT 1.9 →
  17.1), leaving **~51** (`ercot-retirement-composition` §C).

This is the same conclusion the backcast lane reached from the other side and
the owner has already signed (C3c ledger; ercot-190): **an LP on
competitive/measured-cost offers under-forms the real-time scarcity tail as a
model-class property.** The screen consumes that under-formed object; the
residual is the accepted limitation's measured complement, not an unfinished
structural lane.

### 1.3 Which unit classes flip retire/stay at that error

Read off the FFR-8A paired arms (control = unified lookahead; repair = +
restoration, the posture now armed):

| class | screen says (repair arm) | bar | at measured replica | consequence of the error |
|---|---|---|---|---|
| **gas_st** | decided **27 units / 6,500.6 MW** at net $24.85 (control: 45 / 10,942.9 MW at $17.90) | 35.0 | 47.0–65.6 → **clears, stays** | a 6.5–10.9 GW false exit wave of a fuel whose real in-window economic exits were ≈ 0 (actual total incl. all channels 2.294 GW); err +183 % even post-repair |
| **coal** | 2025-ledger decision **23 units / 7,040.2 MW** at net $16.65 (control 11 / 1,482.1) | 58.5 | 75.4–97.2 → **clears, stays** | a ~7 GW pipeline decision the measured market revenue refutes |
| **gas_ct / gas_cc** | entry_capped census **fleet-wide**: 523–578 units / 56.5–67.0 GW fail their bars every screen year | 21.0 / 30.0 | 47.0–86.7 → **clear, stay** | the whole merchant fleet is loss-making on paper; retention survives ONLY through the adequacy admission cap |
| nuclear | clears (§45U path) | 130 | clears | no flip — T-R7 guard unaffected |

Two committed findings sharpen the risk: (a) **the admission cap is doing all
the retention work** (the D-20(a) defect, cause measured at FFR-6A §4: the
price object, not the margin construction — the replica matches SOM 0.89–0.97 —
and not the bars, which are externally consistent within ~5 %); (b) **the
exit side responds to the price object through the cap NON-monotonically**
(`ffr-8a` §4.2.4: raising the object shrank the gas_st wave AND enlarged the
coal decision by 5.6 GW, because a longer surviving fleet admits more of the
always-failing cohort). A screen whose every merchant unit fails economically,
held back only by a non-monotone cap, is exactly the machine that will
**manufacture unrealistic retirements in a high-scarcity forward year**: the
moment the fleet thins (or load grows) enough to loosen the cap, the backlog
of paper-loss-making units exits en masse — and it is precisely the
scarcity-concentration years, where real merchant revenue is 3–4× the quiet
level, in which the model's screen misses the MOST revenue (the 2023 anchor
224–257 vs a screen that cannot exceed ~20). The owner's concern is the
measured record, not an intuition.

---

## 2. THE MECHANISM SHAPE (option L-1) — the residual scarcity-rent term

### 2.1 One sentence

A **default-off, ERCOT-only, forecast/hindcast-only** revenue-stack term in the
economic screen — never in any LP, price series, or scored output — equal to
the *measured market scarcity-rent function of system tightness, minus whatever
scarcity content the model's own price object already forms*, identified from
multi-year Potomac SOM net-revenue anchors against measured tightness, and
evaluated in each screen year at the **model's own simulated tightness**.

### 2.2 Definition

Per screen year `y`, per merchant thermal class `f`:

```
term_f(y) = max(0, R_f(τ_model(y)) − S_f(y))        [$ /kW-yr]
```

- **τ_model(y) — the conditioning variable (model state, regenerates
  forward).** A tightness statistic computed from the screen's own price/fleet
  object for year `y` — candidate forms, one to be selected AT IDENTIFICATION
  and frozen: (i) the entering fleet's reserve margin; (ii) a simulated
  peaker-net-margin analogue `Σ_t max(0, λ̂_t − mc_CT)` on the screen object;
  (iii) the screen object's tight-hour count. The selection criterion is
  pre-registered (§3, V0): the form with the best leave-one-vintage-out
  reproduction of the anchors — chosen against measured data only, never
  against a model run.
- **R_f(τ) — the measured rent function (identification source).** Fitted on
  pairs of *(measured tightness of year v, SOM net-revenue anchor of year v)*
  across all published SOM vintages — **both coordinates measured; no model
  quantity and no model residual anywhere in the fit** (rule 23: frozen;
  re-derives only when a new SOM vintage or reserve-telemetry vintage lands).
  Measured tightness for the fit comes from the committed NP6-905-CD
  reserve telemetry / published reserve margins for each anchor year. On-disk
  anchors today are 2023–2025 (`som-competitive-conduct`, seeded FFR-6A); the
  2018–2022 history columns of the same reports are intakable now — under the
  2026-08-06 rule-22 clarification **data intake is unrestricted; only
  solving/scoring an out-of-training year is a spend**. The identification
  wants those points (they include the 2019 and 2021 tightness extremes) and
  the derive must NOT proceed on 3 points alone (§3 V0 sets the floor).
  Per-class levels: CT and CC directly from the SOM new-unit tables;
  coal/gas_st via the SOM existing-unit net-revenue tables where published,
  else via the frozen measured capture-ratio shape (replica_f / replica_CT
  from the standing FFR-6A replica construction — a measured, year-indexed
  ratio, not a free parameter).
- **S_f(y) — the rule-19 subtraction (the reconciliation, §2.4).** The
  scarcity/reserve content the screen's own object ALREADY carries for class
  `f` in year `y`: the hourly reserve-signal uplift
  (`screen_reserve_value_enabled` → `reserve_uplift_usd`, already a logged
  ledger field), the FFR-8A restored tail's adder content, any in-year ORDC
  formation, and — if G-20/G-22 ever arms in the screen — the co-opt annual
  rate. All are already computed or logged by the existing diagnostic
  decomposition (`margin_detail`: `reserve_uplift_usd`, adder means).
- **Placement.** A fourth labelled revenue line in
  `retirements.py::apply_economic_retirements`, exactly parallel to the
  existing `capacity_revenue_usd` / `as_annual_credit_usd` lines, logged in
  `margin_detail` and the evolution ledger per unit per year. The entry screen
  (step 5) shares the same starved signal (BLK-8 term (a)); its application is
  a NAMED FOLLOW-ON with its own A/B, not bundled here.

### 2.3 The forward regeneration story (rule 13's test, answered)

*Could this quantity be produced for a forward year from forward drivers, and
would it respond to changed conditions?* **Yes, by construction:** in 2035 the
model computes τ_model(2035) from its own simulated fleet and load, evaluates
the frozen R_f, and subtracts its own formed content. A long fleet → low
tightness → the term collapses toward the quiet-year anchor level; a thin
fleet or a cold-weather-derated year (FF-1B) → high tightness → the term
rises the way the measured market's rent rose in 2023; a future structural
mechanism that forms real scarcity in-model → S_f grows → the term shrinks,
automatically, to zero. This is the same admissibility pattern as the
forecast emission-rate lane (CLAUDE.md rule 13's worked example): a measured
multi-year relation, conditioned on model-simulated state, applied forward.
What rule 13 forbids — pinning a year's outcome, an offset tuned to the
residual, rescaling an input so the output lands on actuals — appears nowhere:
the term never sees a model residual, never references a specific year's
actual, and moves with conditions.

### 2.4 Rule-19 reconciliation with the ORDC screen leg (and everything else)

CLAUDE.md step 3: *"`screen_reserve_value_enabled` … when present it is the
SOLE thermal AS pricing."* The screen's existing precedence stack
(`retirements.py:2065–2090`) is: (1) hourly reserve-price signal folded as
`max(energy, reserve)`; (2) else co-opt annual rate; (3) else exogenous flat
rate. The term does **not** join that stack as a fourth alternative — it is
defined as the **residual above whatever the stack forms**, via the S_f
subtraction. One phenomenon (scarcity/AS rent in the screen's pro-forma), one
mechanism (the model's own formation), one measured remainder that shrinks as
formation improves. Concretely: arming the co-opt later does not stack — it
raises S_f and the term gives way; in-year ORDC formation (FF-1B event years)
raises S_f likewise; the FFR-8A tail's 2025-screen content (17–21 $/kW-yr) is
subtracted from day one. The `__post_init__` validator enforces the term's
gates (ERCOT-only, forecast/hindcast-only, requires the diagnostic
decomposition it subtracts from).

### 2.5 RTC+B (2026+) as a forward driver

ERCOT's Real-Time Co-optimization + Batteries went live 2025-12-05 and retired
the ORDC adders; forecast years ≥ 2026 are the RTC+B design
(`results/scarcity.py::ercot_market_regime`, `_RTCB_FIRST_FULL_YEAR = 2026`;
the go-live boundary and the read adapter are already in the codebase —
rtcb-adapter-1, card D/D1). Consequences the mechanism must carry, stated now:

- **R_f is identified on the ORDC+RTORDPA regime** (every published SOM anchor
  through the 2025 vintage is pre-RTC+B). Forward years apply it across the
  regime boundary with a NAMED transfer caveat: RTC+B replaces the ORDC with
  co-optimized AS demand curves keyed to the same VOLL/PBPC family — the
  design intent is more efficient scarcity pricing at similar tightness, not a
  different rent level — but no measured RTC+B-era anchor exists until the
  2026 SOM publishes (~mid-2027).
- **Rule-23 re-derive trigger, pre-registered:** the first RTC+B-era SOM
  vintage re-derives R_f with a regime term (or a post-2026 segment); the
  citation is the new vintage, never a residual.
- The term rides the existing `ercot_market_regime` seam for any
  design-date-gated behaviour; it introduces no second regime gate (rule 19).

### 2.6 The FFR-6A row-3/row-4 boundary — why this is not the refused knob (card S1)

FFR-6A refused by name: (row 3) any bar/FOM re-level toward the residual;
(row 4) *"scalar uplift/offset/multiplier on the lookahead signal (any 'add
$X', 'scale to SOM/actuals')"* — rule 13's forbidden branch, no forward
analogue. The chartered term differs on four checkable properties:

1. **It never touches the price object** — no price series, hourly or annual,
   is uplifted; the term is a separate revenue-stack line in the screen only,
   like the capacity payment already is.
2. **It is conditioned** on a model-state variable and regenerates forward;
   the refused knob was a constant with no driver.
3. **Its identification is measured-vs-measured** (SOM rent vs measured
   tightness, cross-year); the refused knob was scaled to make a model output
   land on actuals.
4. **It is subtraction-reconciled** — structurally forced to zero as real
   formation improves; the refused knob would stack forever.

The honest counter-argument is also stated: SOM net revenue is an equilibrium
*outcome* (conduct-formed λ rent), and importing any outcome-derived quantity
as an input is the pattern rule 13 exists to police. The defense is the C3c
precedent the owner has already signed: the program has formally accepted that
this content is un-formable by the model class (ledgered in every keeper year;
disclosed at ercot-190), so the choice is not "form it structurally vs import
it" — that fork was measured shut (§1.2) — but "carry the accepted
limitation's measured complement in the screen, or let the screen decide
retirements on revenue the program knows is understated by ~50–70 $/kW-yr."
**This adjacency is exactly why S1 is an owner signature and not a lane-level
call.** A signed S1 should quote this section, so the distinction is owned,
not assumed.

---

## 3. PRE-REGISTERED VALIDATION — none of it is the residual

The promotion criterion is NEVER the 22.8/12.7/6.3 GW over-retirement residual,
any thermal-level band, or any price score. Registered now, before any derive
or solve:

- **V0 — identification gate (no LP).** Leave-one-vintage-out across the SOM
  anchor years: fit R_f on N−1 vintages, predict the held-out vintage's anchor.
  PASS bar: within ±25 % or ±15 $/kW-yr (whichever is larger) on CT and CC, on
  every fold. **Floor: ≥ 5 anchor vintages** (requires the 2018–2022 intake;
  with only the 3 on-disk vintages the lane STOPS at V0 and reports — no
  3-point fit proceeds). The conditioning-variable form (§2.2) is chosen by
  this gate alone.
- **V1 — the A/B, unit grain, observed retire/stay 2023–2025.** ERCOT
  2021→2025 T1-FF hindcast, control (HEAD posture) vs term arm, both solved
  cold at one HEAD (the FFR-2B one-tree discipline). Scored against the
  FFR-7C-corrected actuals (Deely/Braunig/OS-status hygiene): the window's
  true economic-exit total is ≈ 0 GW, so the pre-registered expectations are:
  (a) gas_st economic decisions collapse **6.5 GW → ≤ 1 GW** with the
  survivors' margins clearing on economics, not on the cap; (b) the coal
  2025-ledger decision shrinks toward 0 (control 23 / 7,040 MW); (c) the
  entry_capped census collapses from fleet-wide (56.5–67.0 GW) to **< 20 % of
  the control's MW** — retention moves from the admission cap to economics,
  the D-20(a) defect's direct measure; (d) T-R10a/b PASS; (e) zero economic
  nuclear exits (T-R7); (f) I6 improves or holds; no NEW invariant failure
  beyond the disclosed adequacy rows. **LOYO within 2023–2025, scorer-side:
  every verdict flip holds ≥ 2/3 folds** (rule 22).
- **V2 — negative controls (the "must not move" set).** Backcast keepers
  byte-identical (the flag is unreachable in backcast — validator + test); the
  A/B arms' own LP inputs byte-identical between arms (test asserts the term
  touches no LP bound, objective, or price series); C3a/C3b/C3c and every
  scored series untouched by construction; additions reported, not targeted.
- **V3 — the tightness-response check (condition-responsiveness, rule 13).**
  Within the term arm, the per-year term must co-move with the model's own
  tightness (2023-screen term > quiet-screen terms) and must be visibly
  smaller wherever S_f is nonzero (the FF-1B event year) — evaluated
  directionally, reported at full magnitude.

A V1 miss routes to diagnosis (which component — conditioning form, capture
ratios, subtraction — failed), never to widening a band or re-fitting R_f
against the miss.

---

## 4. WHAT THE MECHANISM MUST NOT DO

1. **Never touch dispatch prices, LP objectives, bounds, or any scored
   series.** It lives entirely in `capacity_evolution/retirements.py` (and,
   under its own later charter, the entry screen). Backcast mode cannot reach
   it (validator-enforced); C3a-2023 stays a MODEL MISS at −32.8 % and the
   C3c ledger entry stays exactly as signed. No backcast keeper, dashboard
   file, or bench artifact changes by construction.
2. **Never double-count the ORDC / reserve-value / co-opt legs** — the S_f
   subtraction (§2.4) is load-bearing, tested, and applies to every present
   and future formation channel (rule 19).
3. **Never re-open the refused channels:** no bar/FOM re-level (FFR-6A row 3),
   no scalar uplift on the lookahead signal (row 4), no outcome pin, no
   per-year fitted value, no re-tuning of `retirement_execution_lag_*` or the
   pipeline rule (D-1 is signed and stands).
4. **Never spend a holdout year** — identification uses published SOM tables
   and measured telemetry (data intake, unrestricted); every solve/score stays
   in {2021 hindcast seed, 2023–2025}; 2022 bridged, never solved.
5. **Never repair the FFR-9C arming mess** (§5.3) — not the override-precedence
   seam, not stage B's missing matrix cells, not its undeclared epoch. Those
   are OVERRIDE-FIX / FFR-9C-PROMOTE-completion property.
6. **Never cross an ISO boundary** (rule 25): ERCOT-identified, ERCOT-gated;
   other ISOs enter the matrix as `U`. The MISO gas_ct/gas_cc/oil
   under-retirement and PJM coal-depth residuals (FFR-2B §5) are the same
   revenue-lane family — each ISO derives from its own monitor's tables under
   its own charter if this pattern proves out.

---

## 5. COST + BLAST RADIUS

### 5.1 Build cost

| stage | content | est. cost |
|---|---|---|
| Intake | SOM 2018–2022 net-revenue history columns (PDF transcription into `som-competitive-conduct`, same schema) + reserve-margin/tightness series per anchor year | 1 session, no solve |
| Derive + wire | `derive_screen_scarcity_rent.py` (frozen, cited), `ScenarioConfig` field (default-off, registered in `_CACHE_KEY_OPTIONAL_FIELDS` + defaults ledger + matrix row in the SAME commit, rule 28c), the S_f subtraction seam, validator, tests (trivial-first: 1 gen / synthetic anchors) | 1 session (Opus/Fable — rule 27 lane order), no solve |
| V0 gate | leave-one-vintage-out on the anchors | in the derive session, no LP |
| A/B + V1–V3 | 2 arms × 4 LP years, ERCOT T1-FF (measured: ~12 min–1.5 h/leg at 4 CPU depending on fleet fullness), + scorer-side LOYO | 1 session |

Default-off landing moves **no** cache key and re-bases **nothing**.

### 5.2 If promoted (which forecast runs re-gate)

Promotion is its own later sitting, on the V1 record, and is an ERCOT
**cache-key epoch — declared in the promoting PR** (the PREREG-ffr-9c §3
pattern; the a71fc84 undeclared epoch is the counterexample, not the
precedent). Re-gated: ERCOT **T1-F 2026–2030** and **T1-X 2023–2027** re-solve
(~2×5 solve-years, ≈ 2–3 h each per the §2.1b cost rows); the FF gate-board
rank-2 frontier row and ERCOT's FC-1 I3 reading re-measured; FH-4/FH-5 ERCOT
legs are already pre-epoch record (stage B re-based them at a71fc84) and are
NOT re-run. Zero backcast contact: no keeper, no bench, no backcast CI gate
sees the field. Matrix duties: the ERCOT cell verdict lands in the same
session as the A/B (rule 28b); the new-mechanism row + a `U`/`·` cell line in
every shard lands with the field's PR (28c).

### 5.3 Sequencing around the FFR-9C stage-B state (stated, not fixed)

The record: D-30 signed stage B as ONE five-flag unit; the arming commit
`a71fc84d` — subject *"[INCOMPLETE - do not push]"* — was merged anyway
(PR #3888, on main at `ac07b129`), so ERCOT's `default_scenario_overrides` now
arms all five rows with (i) the promised same-commit matrix cells absent,
(ii) the cache epoch fired but never declared, and (iii) the AP.2
override-precedence defect making a control arm for those five flags
inexpressible through the config path (sitting addenda AP/AQ). This charter
sequences around that as follows:

- **The lane's own A/B is expressible today**: the new field defaults OFF and
  is NOT in the override table, so control (absent) vs arm (CLI-armed) is a
  clean pair at the armed stage-B baseline. It does not wait for OVERRIDE-FIX.
- **The control is re-solved at HEAD, never quoted**: every pre-a71fc84 ERCOT
  hindcast bundle (FFR-8A's arms included) is pre-epoch record; the FFR-2B
  §0c-9 duty applies verbatim. The §1 sizing above is therefore the charter's
  motivation, and the implementing lane's **Phase 0 re-sizes the residual at
  the live posture** before building anything — if stage B has materially
  moved the screen margins, the re-sized number is the one the derive's
  documentation cites.
- **The term must NOT be added to `default_scenario_overrides` until
  OVERRIDE-FIX lands** — promoting through the defective seam would make the
  term's own control arm inexpressible (the AP.2 class, third instance).
  Hence S3's recommendation: A/B now, promotion behind OVERRIDE-FIX.
- **This lane fixes none of the a71fc84 gaps** — if the FFR-9C completion or
  OVERRIDE-FIX lands mid-lane, rebase, re-verify the control reproduces
  (tree-hash technique, PREREG §0 pattern), and continue.

---

## 6. OPTIONS — card S2

- **L-0 — DO NOTHING (the honest baseline).** No spend; the screen keeps
  deciding on a revenue signal measured at ~3–40 % of the market's level.
  **The bias it accepts, stated measurably:** every merchant thermal class
  reads loss-making in every screen year (entry_capped 56.5–67 GW,
  fleet-wide); retention rests entirely on the adequacy admission cap, which
  is measured non-monotone (§1.3); the forecast will therefore over-retire
  exactly when the cap loosens — thinning fleets, high-load years, post-2030
  horizons where no confirmed-exit registry reaches (readiness_limits already
  says 2031–2050 retirements are entirely the economic screen's). In
  scarcity-concentration forward years the screen's revenue miss is LARGEST
  (the 2023 anchor is 3–4× quiet years), so the retire signal is most wrong
  precisely in the years the owner names. What L-0 has going for it: in the
  2021–2025 window the cap held (in-window economic executions = 0 in both
  FFR-8A arms), the pipeline rule's T-R10 guards are PASS, and every
  known-false wave currently executes only in the unscored 2022 bridge. L-0
  is coherent as "the cap is the retention model" — but that is a fitted-shape
  defense of a mechanism the record calls a defect (D-20(a)), and it leaves
  frontier rank 2 open indefinitely.
- **L-1 — THE RESIDUAL RENT TERM (§2). RECOMMENDED.** The only option that
  puts the measured market level into the DECISION while the accepted
  model-class limitation stands, with zero contact with scored series and a
  built-in sunset (the subtraction) as structural formation improves. Risks,
  named: identification thinness (V0's ≥5-vintage floor guards it); the
  regime-transfer caveat across RTC+B (§2.5); and the §2.6 adjacency — which
  is why S1 is a signature, not a footnote.
- **L-2 — E1 DISPERSION REPAIR FIRST.** FFR-8A's own named candidate surface:
  the forward committed-capability formula under-disperses vs measured RTOLCAP
  (p1 13.3 vs 7.9 GW), so the tail under-visits the knee. Design-faithful and
  worth doing eventually — but its ceiling is bounded by the same measured
  fact that bounds all of §1.2: the missing content is λ-led, and the ORDC
  tail is the wrong instrument for it (149/184 of 2024's λ>$100 hours carried
  adders ≤$10). Expected reach: another single-digit-to-~20 $/kW-yr of the
  ~50–70 gap. **Complement, not substitute**: under L-1 it simply grows
  S_f and shrinks the term.
- **L-3 — CO-OPT-ONLY (wait for G-20/G-22).** Measured increment +~15
  $/kW-yr; measured remainder ~51. Does not answer the owner's concern; the
  co-opt's own arming (if it comes) reconciles through S_f under L-1 anyway.
- **Not on the menu** (standing decisions honored): bar re-levels (FFR-6A row
  3), scalar signal uplift (row 4), outcome pins (rule 13), re-opening the
  dispatch-side C3a lane (card Q, Q-B final), re-tuning the pipeline rule or
  its lags (D-1), a capacity-payment surrogate for energy-only ERCOT
  (MARKET_DESIGN: no capacity market exists to pay it).

**Recommendation: sign S1 as chartered (the §2.6 distinction owned), S2 = L-1
with L-2 named as follow-on structural work, S3 = A/B now / promotion behind
OVERRIDE-FIX.** If the owner reads §2.6 and judges the term row-4-forbidden,
the honest fallback is L-0 with the bias statement above entered beside the
ercot-190 price-tail disclaimer as a second `readiness_limits` row
("retirement/entry calls in scarcity-concentration forward years carry the
screen's measured ~50–70 $/kW-yr merchant-revenue understatement") — the
program then owns the limitation in the forecast documentation instead of the
mechanism, and frontier rank 2 is re-classified from "open lane" to "accepted
limit," which is itself a decision only the owner can sign.

---

## GOVERNANCE — what this session did and did not do

- **Rule 1 `[R-STRUCT]`:** no mechanism built or tuned; the charter grades the
  structural routes on their measured record (§1.2) and proposes the level
  term only where the structure is measured out of reach — the same
  structure-first ordering the rule commands, with the level lever explicitly
  screen-scoped and owner-gated.
- **Rule 13 `[R-MEASURED]`:** nothing was fed to any model input; the
  admissibility argument is §2.3/§2.6 and its adjudication is S1's, not this
  session's.
- **Rules 15/28:** no run produced, nothing registered; **no matrix cell
  minted and no verdict written** — a chartering/governance card with reads,
  not a mechanism test (precedent: ercot-182/189 sittings). The implementing
  lane owes the matrix row + cells (28c) and the tested-cell update (28b); it
  goes off-queue by charter (the ERCOT §5.1 queue is the closed backcast C3a
  ladder; this is forecast-frontier rank 2, and this paragraph is the
  stated off-queue justification the matrix protocol requires).
- **Rule 22 `[R-HOLDOUT]`:** no year solved or scored; the SOM 2018–2022
  intake named in §2.2/§5.1 is data intake, unrestricted by the 2026-08-06
  clarification; every planned solve stays in {2021 seed, 2023–2025}.
- **Rule 25 `[R-ISO-SCOPE]`:** ERCOT only, throughout.
- **Rule 27 `[R-PUSH]`:** new files only; no source file ≥300 lines modified.
- **Sequencing honesty (§5.3):** the FFR-9C stage-B arming mess is described
  and routed, not touched.

**Artifacts this session commits:** this card + a session entry in
`docs/calibration-log/ercot.md`. Nothing else.

---

## RESOLUTIONS — ALL THREE SIGNED BY THE OWNER, 2026-08-13

The sitting was held on 2026-08-13; the card body above is preserved AS PUT,
unedited by the outcome.

| card | decision | **SIGNED** | vs. recommendation |
|---|---|---|---|
| **S1** | rule-13 admissibility of the residual scarcity-rent term | **ADMISSIBLE AS CHARTERED — the §2.6 distinction is OWNER-SIGNED**: a measured, tightness-conditioned residual rent with the §2 sunset is not FFR-6A verdict row 4's refused scalar signal uplift | As recommended |
| **S2** | which option runs | **L-1**, with L-2 named as follow-on structural complement — never its substitute | As recommended |
| **S3** | timing vs OVERRIDE-FIX | **A/B NOW, against a control re-solved at HEAD; any PROMOTION waits behind OVERRIDE-FIX** (§5.3) | As recommended |

### What these signatures do NOT do

* No `ScenarioConfig` field exists yet — the implementing session adds it
  default-off with its matrix row + a cell line in every shard (rule 28c).
* No run, no registration, no promotion is performed by this signature; S3
  explicitly holds promotion behind OVERRIDE-FIX.
* No scored series, dispatch price, or backcast artifact is touched — the §4
  must-nots bind the implementing session verbatim.
* The L-0 fallback's second `readiness_limits` row is NOT entered — L-1 is
  chartered instead.
* Card Q (Q-B, final) and every closed dispatch-side face stay closed.
