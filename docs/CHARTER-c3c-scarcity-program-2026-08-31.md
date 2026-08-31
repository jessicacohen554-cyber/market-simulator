# CHARTER — the C3c scarcity program: scoped and costed before commitment

**Filed:** 2026-08-31, session nyiso-163 (continuation). **Owner ruling being
scoped:** *"Open c3c scarcity question"* — taken in preference to ruling the
nyiso-161 winter-face waiver card, after the owner closed the NYISO AORR access
route permanently. **Zero solve; committed artifacts and public data only.
Nothing is armed, promoted, or adjudicated by this document.**

**Read §4 before §5.** The obvious version of this program is already dead on
the record, and most of what looks like opportunity here has been measured and
closed. What survives is smaller than the ruling implies — but one piece of it
is new, load-bearing, and contradicts a ledger entry currently carried by a
keeper.

---

## 1. WHAT WAS MEASURED (zero solve, all six keepers)

C3c on every ISO's designated keeper, from committed artifacts
(`scripts/calibration_verdict.py --json`; raw scan
`results/calibration/_nyiso163b_c3c_reserve_timing.json` for the NYISO leg):

| ISO | C3c | threshold | 2023 | 2024 | 2025 | determination |
|---|---|---|---|---|---|---|
| **PJM** | **PASS** | >$200 | 4/6 (0.67×) | 10/18 (0.56×) | 32/59 (0.54×) | CALIBRATED |
| ERCOT | CAVEAT | >$200 | 72/181 (0.40×) | 22/53 (0.42×) | 1/31 (0.03×) | NOT-YET |
| MISO | CAVEAT | >$200 | 3/30 (0.10×) | 6/37 (0.16×) | 1/88 (0.01×) | NOT-YET |
| NYISO | **FAIL** | >$300 | 1/10 (0.10×) | 0/13 (0.00×) | 1/42 (0.02×) | NOT-YET |
| CAISO | CAVEAT | >$200 | 0/47 (0.00×) | 0/35 (0.00×) | 0/8 (0.00×) | NOT-YET |
| NEISO | CAVEAT | >$300 | 0/15 (0.00×) | 0/8 (0.00×) | 0/20 (0.00×) | CALIBRATED |

(model hours / actual hours above the ISO's threshold; band is [0.5×, 2×].)

**The blanket framing is wrong.** "An hourly LP with $0 reserve offers cannot
form the RT scarcity tail" is carried in several ledgers as though it were
uniform. It is not: PJM forms 54–67 % of its tail *in the same LP, the same
solver, the same code path*, and passes in all three years. The spread from
PJM's 0.54–0.67× down to CAISO/NEISO's flat 0.00× is not a single phenomenon
and must stop being described as one.

## 2. THE RESERVE-BINDING CENSUS (new measurement)

From the `reserve_family_<year>.parquet` sidecars — the only artifact in which
a family's binding is observable (rule 15). P1, 2025:

| ISO | families | hours dual>0 | hours shortfall>0 | max dual | note |
|---|---|---|---|---|---|
| PJM | pjm_primary, _mad | 20 / 29 | **0** | **$187.90** | binds on **opportunity cost**, never short |
| NYISO | 9 families | 38 (nyc_10min) | 24 | **$25.00 cap** | only the **cheap locational** families bind |
| NEISO | 3 families | **0** | **0** | $0.00 | machinery entirely **inert**, all 3 years |
| CAISO | **none** | — | — | — | **no reserve family sidecar at all**; `caiso_reserve_coopt=False` |

Two structural facts fall out:

* **PJM's tail is priced by reserve opportunity cost, not shortage.** It never
  goes short; its dual reaches $187.90 because the marginal reserve MW displaces
  energy. That is real co-optimisation doing real work.
* **NYISO's scarcity channel is capped by construction.** Only
  `nyc_10min_total` / `nyc_30min_total` ($25/MW) and `seny_30min_total` ($40/MW)
  ever bind. The expensive NYCA-level products — `nyca_10min_total` $750,
  `nyca_10min_spin` $775, `east_10min_total` $775 — **never bind in any hour of
  any year**. Maximum total reserve adder available in any single hour: **$90**.

## 3. THE FINDING THAT MATTERS — NYISO's own evidence contradicts the ledger it carries

CAISO's C3c closure rests on a timing argument (caiso-144 §C/§D): in reality's
tail hours the model held **1.6–10.5 GW of reserve slack**, and the LOLP overlay
fired in the wrong hours — overlap with reality's tail **1/47, 0/35, 0/8**. On
that evidence no reserve mechanism could ever price those hours, and the lane
closed correctly.

**NYISO is the opposite case, and nobody has measured it until now:**

| year | actual >$300 | model shortfall hours | **overlap** | share of model shortfall | share of actual tail |
|---|---|---|---|---|---|
| 2023 | 10 | 20 | **5** | 25 % | 50 % |
| 2024 | 13 | 7 | 0 | 0 % | 0 % |
| 2025 | 42 | 24 | **20** | **83 %** | **48 %** |

In 2025 the model goes short in 24 hours and **20 of them are hours reality
priced above $300**. The overlapping hours sit in June–July (2025) and September
(2023) — i.e. **they are the summer scarcity days that make up C3a-2025's summer
face**. The model is short in the right hours. What it cannot do is *price* them:
its entire available reserve adder is $90 against an actual tail mean of
**$505 / $517 / $659**.

**So NYISO's C3c is not the CAISO failure mode.** It is not mis-timed and it is
not obviously the "probabilistic RT premium a deterministic perfect-foresight
hourly LP does not contain" (miso-101's language, which CAISO and NEISO adopt).
NYISO's C3c caveat inherited a cross-ISO diagnosis that its own reserve timing
does not support. That inheritance should be re-examined — **which is a
correction to a ledger entry on a live keeper, not a new mechanism.**

## 4. WHAT IS ALREADY CLOSED — read before proposing anything (rule 26 DO-NOT-REDO)

The naive program ("port PJM's scarcity formation to the others") is dead on
three independent records:

* **CAISO — closed on model state, not mechanism granularity.** `caiso-144`
  proved the completed reserve co-opt is *exactly* inert: family-level slack
  ≥ 854 MW in every one of 26,280 hours, so every optimum carries zero shortfall
  and zero duals. Matrix `energy_reserve_coopt` CAISO = **I**. The backcast lane
  keeps **no** scarcity overlay by measured refusal (caiso-144 §D). CAISO's real
  tail is a winter-morning fuel/cold-snap tail already priced to its input
  ceiling ($150–181 SRMC at measured daily-spot gas vs actual $310 mean).
* **ERCOT — closed on an exhaustion record and one caught phantom.** The tail is
  *conduct-made* on the energy offer stack (GWs offered $500–3,000; measured
  RTORPA p50 ~$1–5 and PRC p50 ~5.8 GW at the missed hours — reality had **no
  reserve scarcity to recover**). Exhaustion: ercot-95/97/102/107/108/155/159/
  161/162/163, then 214/215/216/221–231. **Critically, ercot-213's tail gains
  were later measured to ride an AS-product shortfall-ramp leak — a phantom
  price-formation channel — and were removed at ercot-214/215.**
* **MISO / NEISO — ledgered to the same probabilistic-RT-premium class** (miso-101).

**Adjudicated cells, per ISO — do not re-test without new evidence:**
`energy_reserve_coopt` CAISO **I**, others **K** · `ordc_scarcity_overlay` CAISO
**K**, NEISO **K**, PJM **G**, MISO **G**, ERCOT **R**, NYISO **·** ·
`dynamic_reserve_requirements` NEISO **R** · `reserve_deliverability_scoping`
CAISO/PJM **I**.

## 5. WHAT ACTUALLY SURVIVES — three questions, ranked, with kill gates

### Q1 (do first, cheapest, cuts both ways) — is PJM's reserve dual REAL or the ERCOT-214 phantom?

PJM passes C3c on duals reaching $187.90 with **zero shortfall in every hour**.
ERCOT had a channel that manufactured a tail through a mechanism the market did
not have, and it survived a promotion before being caught. The same audit has
never been run on PJM.

**Test (zero solve):** do PJM's positive-dual hours coincide with hours PJM
reality actually priced reserve scarcity (published PJM reserve penalty /
shortage pricing), on the caiso-144 §D overlap construction?
* **Real** → PJM is a genuine existence proof and Q2 becomes worth asking.
* **Phantom** → **PJM's C3c PASS is not evidence of tail formation, and a
  CALIBRATED keeper is resting on it.** That is a determination-level integrity
  finding and takes priority over everything else in this charter.

**Do not skip this because PJM currently passes.** A passing criterion resting
on a phantom channel is worse than a failing one, and this program's only
existence proof is exactly the thing that most needs auditing.

### Q2 (only if Q1 returns REAL) — is NYISO short on the right PRODUCT, not just the right HOUR?

§3 establishes the timing is right. The open question is *which* requirement
reality was short on. The model goes short only on the $25/$40 locational
families; the $750–775 NYCA-level products never bind. If NYISO reality was
short at the **NYCA level** in those hours, the model understates system-wide
tightness — a **quantity/headroom** question with a measurable answer (published
NYISO reserve shortfall / RCPF activation), not a price knob.

**Kill gate:** if reality's tail hours show no NYCA-level shortage, this closes
exactly as CAISO did, and NYISO's C3c ledger is *confirmed* rather than
corrected. Either way §3's inheritance question is resolved on evidence.

**This must not become "raise the demand curve."** The $25/$40/$750/$775 values
are SOM-published and cited in `model/reserves/spec.py`. Changing a published
penalty to reach a residual is a fitted scarcity adder — rule 13 `[R-MEASURED]`,
rule 1 `[R-STRUCT]`, and precisely the ERCOT-214 failure.

### Q3 (architecture, not a session) — the probabilistic RT premium

Where the residual really is the premium a deterministic, perfect-foresight,
hourly LP does not contain (CAISO, MISO, NEISO, and ERCOT's conduct variant),
crossing it requires a different model class — stochastic or multi-settlement
representation. That collides with rule 4 `[R-DUALS]` (prices are LP duals),
rule 8 `[R-8760]`, and the no-MIP constraint. **This is an architecture decision
for the owner, not a calibration lane**, and it should not be opened as one.

## 6. COST

| | scope | solve | risk |
|---|---|---|---|
| **Q1** | 1 session, zero solve, committed artifacts + published PJM shortage data | none | **May invalidate a CALIBRATED keeper.** That is the point. |
| **Q2** | 1 session zero-solve to measure; a mechanism only if it clears the kill gate and the owner charters it | none to measure | Temptation to tune a published curve — guard in §7 |
| **Q3** | multi-session architecture program | large | Collides with three non-negotiable rules; likely refused |

Honest expected value: **Q1 and Q2 together are two zero-solve sessions.** They
will not, by themselves, close C3c anywhere. What they will do is establish
whether the cross-ISO C3c ledger is telling the truth about NYISO and PJM — and
on current evidence there is reason to doubt it for both, in opposite directions.

## 7. WHAT THIS PROGRAM MUST NEVER BECOME

* No fitted scarcity adder, no tuned VOLL, no raised published demand curve, no
  ORDC offset swept against a residual (the deprecated-offset incident, rule 25
  `[R-DELETE]`).
* No mechanism that manufactures tail hours through a channel the real market
  does not have (ERCOT-214). **Every candidate is timing-checked against reality
  before it is priced**, on the caiso-144 §D construction.
* No cross-ISO transfer of a verdict (rule 25 `[R-ISO-SCOPE]`): a PJM finding
  enters other shards as `U`.
* No holdout spend. Every ISO here is scored on 2023–2025 only; NYISO, CAISO,
  ERCOT and MISO hold no `complete` marker.

## 8. GOVERNANCE

Nothing in this document changes a keeper, shard, marker, determination or
matrix cell. Q1 and Q2 are measurement charters and need the owner's go-ahead
only in the sense that they consume sessions; neither needs a rubric change.
Q3 needs an explicit owner architecture decision and is **not recommended** as a
calibration lane.

*Evidence:* `results/calibration/_nyiso163b_c3c_reserve_timing.json` (§3, this
session) · `results/calibration/FINDING-caiso144-coopt-dormancy-c3c-frontier-2026-07-30.md`
§C/§D/§E · the ERCOT C3c ledger entry on `2026-08-25-234-eastex-identity`
(exhaustion record; ercot-214/215 phantom-channel removal) ·
`src/market_sim/model/reserves/spec.py` (NYISO_RCPF_PRODUCTS,
NYISO_RCPF_LOCATIONAL and their SOM citations) · the six keepers' committed
`reserve_family_<year>.parquet` sidecars · `docs/codebase-site/data/mechanism-matrix/*.js`.
