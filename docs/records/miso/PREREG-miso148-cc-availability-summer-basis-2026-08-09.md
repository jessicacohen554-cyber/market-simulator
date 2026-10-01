# PREREG — miso-148: the CC capability-and-availability lane — L2 fleet/rating audit, then ONE armed mechanism repairing the summer flat-derate double count on a measured-capability base

**Session:** miso-148, 2026-08-09, branch `claude/miso-148-cc-availability-l3czbc`.
**Pushed BEFORE any adjudicating statistic.** Nothing below this line has been
measured at the time of writing: every number quoted in §1–§3 is either (a) read
back from a COMMITTED artifact of a prior session, or (b) read from source code
at HEAD. No new statistic — footing, L2 or L1 — has been computed.

**Keeper at entry:** `2026-08-05-miso-132b-cc-committed`
(bundle `results/calibration/miso132_ccmin_B`).

**Concurrent-session check at open:** zero open PRs on the repository, zero
remote MISO branches. Re-checked at close.

---

## 0. §0 re-verification — from committed artifacts, not from the prompt

`scripts/calibration_verdict.py --run-id 2026-08-05-miso-132b-cc-committed` at
HEAD (stdlib, pre-venv; committed artifacts only, no solve). **Rubric 3.2**:

* **determination `NOT-YET`**, scorable years 2023 / 2024 / 2025, reason
  *"undocumented out-of-tolerance (FAIL) criteria: price_mean"*.
* **C3a `price_mean` — the SOLE FAIL.** RT: 2023 **−0.4 %** (32.72 vs 32.85)
  PASS · 2024 **−6.0 %** (30.37 vs 32.30) PASS · 2025 **−14.1 %**
  (39.05 vs 45.46) **FAIL**, tol ±10 %.
* **C3b `price_shape` PASS** — NRMSE **0.075 / 0.112 / 0.191**, tol ≤ 0.20.
* **C3c** ledgered CAVEAT in all three years (model 0 h / 6 h / 0 h vs RT actual
  30 / 37 / 88 h > $200) — **1/1 ledgerable slot SPENT**.
* **C1 PASS** (2025 classes SKIPPED, preliminary EIA-923 vintage), **C2 PASS**
  (2025 SKIPPED: gas −11.2 %, coal +4.2 %), **C4 PASS**, **C6 PASS**,
  **C8 PASS** with ST_GAS *grounded above budget* **31.9 / 33.1 / 45.1 %**.
* **D-10** free-class C1 16/16, free 12/12; pinned CC_CHP, ST_CHP.

The bundle's own `metrics.json` is STALE; the scorer above is authoritative.
**Fail set = {C3a}.** MISO holds **no** `calibration-complete` marker in either
block ⇒ **rule 22: 2023–2025 only**, all three years in one invocation
(rule 16).

---

## 1. The lane, and the two committed findings it stands on

Charter: the miso-147 successor — the **CC capability-and-availability lane**.
Both source findings are committed; **neither is re-derived here** (DO-NOT-REDO):

**miso-147** (`FINDING-miso147-cc-availability-hole-2026-08-09.md`) measured, on
two independent instruments, that the high-price-hour gap is a **standing
~5–6 GW CC under-dispatch** whose identity is an **availability deficit**:

| quantity (S1 stratum, C3a-weighted MW) | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| CC composition delta (model − actual) | −4,959 | −4,743 | −5,616 |
| **AV − A** (model available CC capability − reality's realized CC output) | −1,226 | −1,608 | **−2,614** |

with S1-2025 **AV = 22,276 MW** vs **A = 24,890 MW net**, and reality's
demonstrated CC capability (adding ~3.6 GW of committed headroom) ≈ **28.6 GW**.
**Model availability sitting below reality's observed generation is indefensible
for any outage input** — that, not the price residual, is what this lane repairs
(rule 1 `[R-STRUCT]`, rule 14 `[R-ACCURATE]`).

Month-resolved (2025): `AV_CC − A_CC` is **positive or ~zero Oct–Mar (Jan
+1,318)** and **negative Jun–Sep (−2,506 / −2,647 / −2,374 / −1,783)** — the
deficit is **summer-concentrated**. May: **+1,074 / −50 / −1,201** — May flipped
negative in exactly the year the model's May over-pricing appears (+12.4 %).

**miso-141** (`FINDING-miso141-summer-derate-double-count-confirmed-2026-08-07.md`)
measured the input-side object: MISO's gas `pmax` **is** the EIA-860 net-summer
rating (100.0 % of matched class capacity for CT_PEAKER / CT_CHP / CC_CHP;
83.6 % for CC_REGULAR), and the model removes a **further flat 10 % (CC) /
12.5 % (CT)** on top — the same nameplate→net-summer gap already embedded in
that base (measured clean: CC_REGULAR 11.40 %, CC_CHP 14.34 %, CT_PEAKER
16.35 %, CT_CHP 15.25 %). Scale: **5,933 / 5,853 / 5,686 MW** of summer h12–17
capability removed. The alternative "incremental ambient loss" reading was
**refuted without appeal to provenance** — at MISO's own slopes the honest
incremental is an **uprate** of ~2 % (CC) / ~3.7 % (CT), and the sign is
inverted in **18/18** zone-years.

miso-141 ruled the repair **needs a NEW mechanism** and specified it (§11.2):
class-agnostic (must cover CT as well as CC), a **pure basis correction** with
the POF/age-derate drops kept behind their own flag, and the corrupt-filing
plants handled **explicitly** rather than by silent clamp.
**`cc_nameplate_summer_derate` without a new mechanism is DO-NOT-REDO.**

---

## 2. Rule 19 `[R-ONE-MECH]` — what already derates MISO CC, enumerated from source at HEAD

Read from the keeper's own committed `run_config.json` + `meta.json` and
`src/market_sim/data/fleet/arrays.py` (code reading, not measurement):

| # | mechanism | site | live on this keeper? |
|---|---|---|---|
| 1 | statistical POF (shoulder) + WEFOR, age-escalated | `THERMAL_AVAILABILITY` | **yes** |
| 2 | `wefor_multiplier` / `wefor_residual` / `wefor_residual_groups` | arrays.py | inert (1.0 / None / None) |
| 3 | CAMPD historic outage overlay (+ short windows, maxgen events) | `outage_source="historic"` | **yes** |
| 4 | `BIN_FORCED_DERATE_BY_YEAR` (backcast) | arrays.py | bin-keyed; plant-level path |
| 5 | **flat `_SUMMER_CLASS_DERATE` 0.10 CC / 0.125 CT, summer months** | arrays.py ~782 | **yes — THE OBJECT** |
| 6 | `temp_dependent_derate` | post-loop block | **mean-anchored**, `temp_derate_classes = ['CT_CHP','ST_CHP']` ⇒ reshape only, annual mean 1.0; **does not touch CC** |
| 7 | `gt_ambient_derate` | arrays.py | off (measured PROVABLY INERT for MISO, miso-89 §8) |
| 8 | `cc_capacity_reconcile` — per-plant CAMPD demonstrated-peak **cap** | capacity basis | **yes** (`cc_capacity_reconcile_MISO.csv`, 23 plants, `mode=cap`) |
| 9 | `cc_duct_peaking` | offer curve | on — offer-side, not availability |
| 10 | COD ramp | arrays.py | new units only |

`_SUMMER_CLASS_DERATE`'s other read sites are **ERCOT-gated** and cannot fire
for MISO: `results/scarcity.py:1364` (`ERCOT_RTOLCAP_FWD`) and `:1859`
(`ercot_online_capacity_envelope*`); `campd_bins.py:1454` is a docstring.
The `temp_dependent_derate` **anchor** site (`arrays.py` ~916) reads the flat
derate only when `_td_anchored` is False — it is True on this keeper, so that
site is **inert here**; it is nonetheless made consistent by the mechanism (§4)
so the two sites can never disagree in another configuration.

**No existing field suppresses the flat derate on an already-measured capability
base, class-agnostically, without riders.** `cc_nameplate_summer_derate` is the
nearest and miso-141 §9 refused it: it covers **50.3–52.1 %** of the affected MW
(CC only; the CT half, 2,824–2,841 MW/yr, has **no** mechanism at all) and, on
an `outage_source="historic"` keeper, additionally drops the statistical POF and
the age/performance derate — **four changes in one flag**. So a new mechanism is
warranted, and §4 builds exactly one.

---

## 3. Sequencing — L2 measurement BEFORE the L1 arm, and why

The charter lists L1 first in priority, but miso-147 §8 item 2 and the charter's
own L2 text both require the fleet/rating audit **"BEFORE any further derate
tuning"**. That constraint governs: a derate repair applied on top of a stale or
under-populated CC fleet would be a correction sitting on a wrong base. So:

**L2 (measure) → L1 (identify + arm) → control solve → arm solve.**

**L3 (the all-months commitment residual) is OBSERVATION ONLY this session and
will NOT be armed**, as chartered.

---

## 4. THE MECHANISM — specified in full, before it is built or measured

**New `ScenarioConfig` field: `summer_derate_basis_aware: bool = False`**
(default off ⇒ every other ISO and every existing bundle is byte-inert;
rule 25 `[R-ISO-SCOPE]`).

**Identity, stated as a physical claim rather than as a knob:** the flat class
ambient derate `_SUMMER_CLASS_DERATE` represents the **nameplate → summer-peak
ambient loss**. It is therefore applicable **only to a unit whose LP capacity is
carried on a nameplate basis**. When a unit's capacity is already a *measured,
ambient-inclusive capability* — a published net-summer rating, or a CAMPD
demonstrated peak — the loss is **already inside the base**, and applying it
again is a double count. When True, the flag applies the flat derate **only to
units still on a nameplate basis**, and suppresses it elsewhere.

**Per-unit admission rule (no tolerance parameter, no fitted value):**

* **SUPPRESS** the flat derate where the unit's carried capacity is a measured
  capability basis — i.e. `plant_level_fleet` units whose EIA-860 filing is
  **clean** (`net_summer ≤ nameplate`, so `pmax` is the published net-summer
  rating), **or** units capped by `cc_capacity_reconcile` to their CAMPD
  demonstrated peak.
* **KEEP** the flat derate for (i) units on a nameplate basis (ERCOT's CAMPD-bin
  path — structurally unaffected because the flag is off there anyway), and
  (ii) **corrupt EIA-860 filings** (`net_summer > nameplate`, which the schema
  forbids — 20 CC_REGULAR rows / 12 plants / 3,962 MW nameplate against 6,814 MW
  net-summer, miso-141 §4). Those units carry a `pmax` **above** their own
  nameplate; their base is not a defensible summer rating, so the derate stays.
  **This is miso-141 §11.2(c) discharged explicitly rather than by silent
  clamp**, and it is the reason the mechanism needs no `net_summer/nameplate`
  ratio arithmetic at all — so it inherits none of that quantity's corruption.
* Units absent from EIA-860 **keep** the flat derate (graceful fallback: absence
  of evidence for a measured basis is not evidence of one).

**Scope:** class-agnostic — all four classes carrying a flat derate
(`CC_REGULAR`, `CC_CHP`, `CT_PEAKER`, `CT_CHP`), satisfying miso-141 §11.2(a).
**Purity:** it changes the flat-derate application and **nothing else** — no POF
drop, no age-derate drop, no WEFOR change, no capacity-basis rescale, no
off-summer leg (§4.1), satisfying §11.2(b).

**Degrees of freedom: ZERO continuous parameters (rule 21 `[R-DOF]`).** The flag
is a boolean; the admission rule is a data predicate on committed EIA-860 /
CAMPD tables. **No variant carrying a tunable derate fraction, a per-class
scale, or a sweepable tolerance will be built or solved in this session** — see
Trap T1.

**Forward story (rule 13 `[R-MEASURED]`):** the flag asserts a property of the
capacity basis, which regenerates for any forward year from the same EIA-860 /
CAMPD tables the fleet loader already reads, and responds to changed conditions
(a re-rated or newly-built plant enters with its own published rating). It is an
**availability INPUT**, never a dispatch pin — no CEMS/dispatch bridging
(DO-NOT-REDO), no measured outcome enters the LP.

### 4.1 What is deliberately EXCLUDED, and why (rule 19)

miso-141 §11.2 phrased the successor as *"nameplate base + per-plant measured
`net_summer/nameplate` multiplier in summer"*. In **summer** that is
arithmetically identical to this mechanism (`nameplate × ns/np = ns = pmax`).
It differs only **off-summer**, where it would raise capability to nameplate.
That off-summer leg is a **second, distinct defect** (the model carries the
summer rating year-round; the published winter rating is higher) with its own
existing CC-only mechanism, `cc_winter_capability_basis` (caiso-186).

**It is excluded here for a measured reason, not for convenience:** miso-147's
`AV_CC − A_CC` is **positive Oct–Mar (Jan +1,318 MW)** — the evidence shows no
off-summer availability deficit to repair. Arming both would be two mechanisms
in one arm (rule 19) and would move capability where no evidence asks for it.
**L1 is the summer leg alone.**

---

## 5. Gates — pre-registered, with pre-committed branches

### G-F — footing (reproduce-before-extend; must PASS before any reading)

* **G-F1** the six committed miso-147 window deficits reproduce to ≤ $0.001
  (−4.750 / −8.333 / −10.676 / −10.671 / −30.999 / −30.435).
* **G-F2** 2025 RT > $200 count = **88** (footing only — the tail motivates
  nothing, C3c 1/1 SPENT).
* **G-F3** `AV_CC − A_CC` × 12 months reproduces `_miso147_january.json`, and
  S1 AV/A reproduce `_miso147_headroom.json` (AV 22,276 / A 24,890 for 2025).
* **Branch on FAIL:** the instrument is not reproducing the committed record —
  **STOP**, report the discrepancy, arm nothing.

### G-L2 — the CC fleet/rating audit (GATING for whether L1 sits on a valid base)

Decompose model CC `pmax` **31.9 GW** against CAMPD demonstrated ratings
**35.4 GW gross** (Σ unit p99, pf 0.993) into named components, universes
registered before any subtraction:

* **G-L2a POPULATION** — CC plants in CAMPD MISO with no model counterpart, and
  vice versa, in MW and unit count.
* **G-L2b BASIS** — the gross↔net and nameplate↔net-summer conversions, applied
  and reported explicitly (never assumed away).
* **G-L2c VINTAGE** — the EIA-860 release the fleet loads vs the newest on disk;
  any plant whose rating differs materially between them.
* **G-L2d RECONCILE** — the MW `cc_capacity_reconcile` removes (23 plants,
  `mode=cap`), reported as a **deliberate measured cap**, not as a defect.

**Pre-committed branches:**
* **B-1 `basis_explained`** — population gap < 1 GW and the residual is covered
  by G-L2b + G-L2d ⇒ **no data correction is warranted**; L1 proceeds on the
  current fleet. *(This is the prediction I expect to lose least often; see §6.)*
* **B-2 `population_defect`** — ≥ 1 GW of CC plants missing from the model fleet
  ⇒ **L1 is SUSPENDED**; the data correction is the session's deliverable and is
  reported without an arm (a derate repair on an under-populated fleet is a
  correction on a wrong base, §3).
* **B-3 `vintage_defect`** — a materially stale EIA-860 release ⇒ same as B-2.

### G-L1 — identification (GATING for the arm)

* **G-L1a** the per-unit admission rule is measured on the ACTUAL solve fleet:
  MW and unit counts admitted (measured basis) vs kept (nameplate / corrupt /
  absent), per class, per year. **Reported before the arm is solved.**
* **G-L1b** the restored summer capability reproduces miso-141 G-4 to within
  10 % (**5,933 / 5,853 / 5,686 MW** h12–17), *conditioned on* the admission
  rule excluding the corrupt rows — a **lower** figure is the expected and
  correct consequence of §4's explicit corrupt-filing treatment, and is reported
  as such rather than as a miss.
* **G-L1c THE STRUCTURAL TEST — the one this lane exists to pass.** After the
  arm, `AV_CC − A_CC` in S1 and in the Jun–Sep months must **rise** (become less
  negative). **The mechanism's success criterion is that model available CC
  capability is no longer below reality's demonstrated CC output — NOT that C3a
  moves.**
* **Branch on FAIL of G-L1c:** the mechanism does not do what it claims ⇒ report
  as a REJECTED arm, register it (rule 15), arm nothing further.

### K — solve-integrity gates (A/B discipline)

* **K0 bit-perfect control** — the zero-delta control reproduces the keeper's
  class-hour sidecars to 0.0 MW in all three years and the scorecard is
  identical. **Branch on FAIL: STOP** (the replay is not faithful; nothing
  downstream is quotable).
* **K1 single delta** — arm `run_config.json` differs from control in exactly
  the one new field.
* **K2 span** — both arms `--year 2023 2024 2025`, one invocation, years
  sequential (rule 12).
* **K3 balance** — energy balance closes; `d_demand` exactly 0.
* **K4 live** — the arm actually moves CC dispatch (a null delta means the flag
  never reached the read site).

---

## 6. My prior — two-sided, numeric, falsifiable, scored against interest in the finding

| # | prediction | P |
|---|---|---:|
| **P1** | **G-L2 returns B-1 `basis_explained`**: the CC population gap is < 1 GW and the 31.9 ↔ 35.4 GW spread is basis + the deliberate reconcile cap, **not** missing plants. *(Reasoning stated in advance: 31.9/35.4 = 0.90, and 11.40 % is exactly miso-141's measured clean CC_REGULAR nameplate→net-summer gap — the spread has the size of a basis difference, not of a population hole.)* | 0.70 |
| **P2** | The admission rule admits **≥ 85 %** of CC+CT flat-derate MW (the corrupt/absent residual is small) | 0.75 |
| **P3** | Restored summer h12–17 capability lands **4.8–6.0 GW** (below miso-141's 5.69–5.93 because corrupt rows are excluded by design) | 0.65 |
| **P4** | **G-L1c PASSES**: S1-2025 `AV_CC − A_CC` rises from −2,614 MW to between **−900 and +500 MW**; P(sign actually flips to ≥ 0) = **0.45** | 0.70 |
| **P5** | **C3a-2025 gets WORSE** (more negative than −14.1 %). *Stated against interest and led with: this repair ADDS capability, so its price effect is DOWNWARD — the wrong direction for a model already 14 % low. miso-141 §7 disclosed this sign in advance and this session does not walk it back.* | 0.75 |
| **P6** | **|ΔC3a-2025| < 1.5 pp** — the restored MW sits 2.4–3.2× inside miso-139's cushion (13.7–18.8 GW), so it should rarely reach the marginal unit | 0.60 |
| **P7** | **May-2025 over-pricing IMPROVES** (moves toward 0 from +12.4 %) — restored CC displaces the expensive CT the model runs in May (miso-147 §6's "one object, both signs") | 0.60 |
| **P8** | Fail set stays **⊆ {C3a}**; no new criterion fails | 0.70 |
| **P9** | net: P(mechanism armed AND solved this session) | 0.65 |

**The two sides, stated explicitly.** *Other side #1:* P5 and P7 are in
tension — one mechanism cannot be credited for helping May unless it is also
debited for hurting summer, and if May does **not** improve, the "one object,
both signs" reading of miso-147 §6 is weakened and I will say so. *Other side
#2:* P1 may well be wrong — `cc_capacity_reconcile` caps 23 plants and could be
concealing a population hole underneath, in which case B-2 fires and this
session delivers a data correction and **no arm**. *Other side #3:* the whole
lane may be structurally right and completely inert on price (P6), in which case
the keeper decision rests on structural fidelity alone and goes to the owner.

---

## 7. Traps — each with its pre-committed counter-measurement

* **T1 — FIXING THE NUMBER (the charter's named trap).** The temptation to size
  the derate removal so C3a-2025 closes. **Counter-measurement:** the mechanism
  is a boolean with **zero continuous DOF** (§4); the admission rule is a data
  predicate. **No parameterized variant will be built or solved**, and the C3a
  effect is measured **after** the mechanism is fixed, never used to choose it.
  The charter's against-interest bound is restated as binding: **2023 carries
  nearly the same CC gap and C3a-2023 PASSES at −0.4 %** — the composition
  defect does **not** predict closing 2025's −14.1 %, and no claim that it does
  will be made whatever the arm returns.
* **T2 — assuming the basis instead of measuring it.** miso-141 measured
  CC_REGULAR at only 83.6 % net-summer. **Counter-measurement:** G-L1a measures
  the admission rule on the actual solve fleet and reports admitted vs kept MW
  per class — the arm is not solved before that table exists.
* **T3 — silent double-removal or no-op.** The flag touches two read sites
  (main loop + temp-derate anchor); it could remove the derate twice, or not
  reach the LP at all. **Counter-measurement:** an availability-matrix A/B assert
  — the ONLY hours that change are summer, only for admitted units, and the
  per-unit ratio is exactly `1/(1−d)` (1.1111 CC / 1.1429 CT); plus **K4**.
* **T4 — cross-ISO leakage (rule 25).** **Counter-measurement:** default False;
  no other ISO's config, bundle, keeper shard or matrix cell is written; the
  matrix cell minted is MISO's only.
* **T5 — gross↔net confusion in L2.** CAMPD p99 is **gross**; model `pmax` is
  **net**. Reading them directly against each other manufactures a fake gap.
  **Counter-measurement:** G-L2b applies and reports the conversion explicitly,
  and both bases are quoted side by side.
* **T6 — quoting the reconcile cap as a defect.** `cc_capacity_reconcile`
  lowers CC capacity **on purpose**, from measured CAMPD demonstrated peaks.
  **Counter-measurement:** G-L2d reports its MW as a deliberate measured input;
  it is never counted into a "missing capacity" total.
* **T7 — the C3c tail motivating something.** **Counter-measurement:** the 88
  hours are footing only (G-F2); no tail statistic appears in any adjudication.

---

## 8. Kill gates — pre-registered, breach REPORTED AND ESCALATED, never silent

Under the owner guidance of 2026-08-09 (*structural integrity may outrank gate
regression; rules 1 + 14*), a breach is **not auto-fatal** — but it is reported
at **full magnitude** and the keeper call **escalates to the owner**. Never
silently promoted, never silently reverted.

* **C3b-2025 NRMSE ≤ 0.200** — currently **0.191**, headroom **0.009**.
* **C3a 2023 / 2024 stay PASS** — currently −0.4 % / −6.0 %.
* **MAY 2025** (+12.4 % over): the arm's May effect is **reported explicitly**,
  in $ and %, whatever its sign. *A mechanism that does not report its May
  effect has not been measured.*
* **C1 / C2 PASS on gated years**; 2025 stays **descriptive** vs EIA-930
  (preliminary EIA-923 blocker).
* **C8** — no material class's forced share rises; no D-4 window breaks.
* **C3c** — 1/1 SPENT; the tail may not motivate anything.
* **fail-set ⊆ {C3a}.**

---

## 9. Solve plan and the keeper decision rule — fixed in advance

* **CONTROL:** `scripts/replay_keeper.py results/calibration/miso132_ccmin_B
  --out-dir results/calibration/miso148_basis_A` — **zero deltas**, same HEAD.
* **ARM:** identical + `--set summer_derate_basis_aware=true --out-dir
  results/calibration/miso148_basis_B`.
* Both: `--year 2023 2024 2025`, **one invocation each**, years sequential
  (rule 12). Rule 22: no year outside 2023–2025 is solved, scored or registered.
* **BOTH RUNS ARE REGISTERED** on the backcast dashboard in this session —
  control and arm, keeper or rejected (rule 15).

**Keeper decision rule, pre-declared:**

1. If **G-L1c PASSES** (the availability deficit is repaired) and the fail set
   stays ⊆ {C3a}, the arm is the **more structurally faithful configuration by
   construction** — model availability no longer sits below observed generation.
   It is then a **keeper CANDIDATE on structural fidelity**, and it is proposed
   to the owner **with every gate regression reported at full magnitude**,
   including a C3a-2025 that may be worse (P5).
2. If **G-L1c FAILS**, the arm is **REJECTED** and registered as such.
3. **Leave-one-year-out** within 2023–2025 is run before any promotion
   (rule 22). With zero fitted parameters the LOYO question is whether the
   effect is same-signed across years, not whether a parameter transfers.
4. **No promotion is executed on my own authority under a gate regression** —
   the owner's 2026-08-09 guidance makes it an escalation, not a licence.

---

## 10. Disclosure

* **DO-NOT-REDO honoured** (rule 28(a)): the full carried list plus the miso-147
  additions. Specifically not re-opened — the quantity and merit-order families,
  congestion, floors, the offer-LEVEL hypothesis and offer-side class bridge,
  price-threshold splits, the 88-hour arithmetic (footing only), the LEVEL
  adder, `*_lw` re-derivation, trough pricing, the CT/CC/coal bridge, seam
  classes, the fitted trough adder, the CC committed band 1.005, the coal
  deep-discount, the SOM PDF corpus, FERC EQR, Michigan PSCR,
  **`cc_nameplate_summer_derate` without a new mechanism**,
  `miso_cc_coal_rebalance`, the exhausted scarcity-tail list, the miso-147
  composition/monthly tables (cited, never re-derived), the January cold-snap
  candidates (all adjudicated unsupported at miso-147), and **CEMS/dispatch
  bridging**.
* **miso-141's ~5.8 GW double-count measurement is CITED, never re-derived**
  (rule 23 `[R-FROZEN-DERIVE]`: `SUMMER_CLASS_DERATE` is not re-derived against
  any residual — it is not re-derived at all; the mechanism changes *where it
  applies*, on a basis argument, not *its value*).
* **Probe hygiene:** `_miso143_stack.hygiene()` in every entry point; strata and
  the CAMPD unit loader reused from `scripts/probes/_miso147_strata.py`
  (**never** `campd.load_campd_hourly`; IL/TX facility-level shadow; str→int
  `facilityId` cast).
* **Rule 28 duties:** the matrix cell for `summer_derate_basis_aware` and the
  §5.4 queue stamp are written **in this session**, rejection included; the new
  `ScenarioConfig` field carries its matrix row **in the same PR** (28(c),
  CI-enforced). Items 8 and 9 of §5.4 **stand** and are not displaced; this lane
  enters as **item 11**.
* **Instrument limits** will be disclosed in the finding as measured, not
  papered over — including any class where the admission rule's evidence is
  weaker than CC's.
* **Nothing is written under `data/raw/`.**
