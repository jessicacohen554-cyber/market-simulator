# MAP — the C-1 ERCOT wind-entry closure map: 12.313 GW, six measured postures, one number

_2026-08-31 · C-1 ERCOT wind-entry lane, discharging the **MAP** half of owner
ruling **R-D** (2026-08-31 director sitting), which placed this lane at
**TERMINAL REST + MAP**. The rest half was executed by
`docs/FINDING-c1-joint-wind-ab-2026-08-31.md` (ruling R-B's joint A/B); this
document is the map that ruling owed and that had never been produced._

**ZERO SOLVE.** No LP, no year solved, no bundle registered on either
dashboard. Every number below is read from a committed artifact, a committed
finding, or the committed ERCOT mechanism-matrix shard. **No default is
flipped, no lever is proposed, no keeper shard / marker / freeze file /
`program-status.json` is touched.** Rule 26 `[R-MECH-MATRIX]`: **this lane
tests no mechanism and moves no matrix cell** — it READS
`docs/codebase-site/data/mechanism-matrix/ERCOT.js` and reports what is
already adjudicated there.

**R-D itself is not yet in the committed record.** At this base
(`origin/main` @ `54d5772c`) the director board
`docs/handoffs/audit-program-director-board-2026-08.md` §111–130 records only
R-A / R-B / R-C from the same sitting. This document is therefore the first
artifact to carry R-D, and it carries it as what it is: a ruling recorded, not
a ruling adjudicated here.

---

## 0. The one-paragraph answer

**Six postures have now been solved against the 12.313 GW ERCOT wind entry
miss, and they return exactly three numbers: 0.000, 0.604 and 1.092 GW. The
best is 1.092 GW — 8.87 % — and it is the SAME 1,092.2 MW decision in every
posture that reaches it.** Three structurally different signal constructions
(raw prior-year LP duals; duals re-levelled forward; duals + the D11-R
margin-exhaustion walk) each build that identical 1,092.2 MW at the 2022
bridge step and nothing more, across a ~$200/MWh swing in the mean entry
signal. The volume rule adds **exactly zero** on top of it (R-B's joint A/B,
`NON_COMPLEMENTARY` against a naive 13.77 % sum). The storage-entry pair adds
**exactly zero** (every addition band identical to the digit). And the posture
that is *currently the ERCOT forecast default* — `entry_margin_exhaustion` +
`entry_forward_reserve_leg`, armed by ruling Q15 — builds **wind 0.350 GW,
closing 0.00 %**. So: at HEAD's armed default the miss is **100 % open**; at
the best measured posture, which is not armed and cannot be composed with the
armed default, it is **91.13 % open**. The residual is not a volume residual
and not a signal-construction residual: on the model's own zonal duals wind's
per-MWh margin at the build zone is **negative in both admissible steps**, and
its capture ratio is **below 1.0 in every ERCOT zone**. Nothing in the
committed record is an admissible closure. **The frontier is closed.**

---

## 1. The closure table

**The miss.** Decision-basis 2023–2025 additions vs RD-5 actuals, from each
bundle's committed `score.json`: actual wind **12.663 GW**, registered/control
model wind **0.350 GW**, miss **12.313 GW**. Every share below is
`(model_arm − 0.350) / 12.313`. Verdicts are taken verbatim from
`docs/codebase-site/data/mechanism-matrix/ERCOT.js` at this base; `cell` is
the backcast-lane verdict, `fc` the forecast-lane verdict.

| # | mechanism (posture) | bundle / cache key | wind GW | **Δ GW** | **% of 12.313** | verdict (ERCOT shard) | evidence citation |
|---|---|---|--:|--:|--:|---|---|
| 0 | *baseline* — registered T1-H posture | `…-t1h-refresh` / `28cef3500ec1fd9e` | 0.350 | — | — | — | `FINDING-entry-screen-t1h-2026-08.md` §1.1 |
| 1 | `vre_procurement_additions` (armed) | same | *supplies all 0.350* | — | *defines the baseline* | `O` / **`fc K`** | FFR-9C §3.6 via the ERCOT shard cell: wind **350.2 MW** injected at the 2022 step; committed cohort 6,761 MW (wind 1,847 / solar 4,914); ~4,921 MW effective-2021 remainder **held-and-discarded** at base year 2021 |
| 2 | `entry_lookahead_reprice` **DISARMED** (dual-based signal object) | `…-t1h-disarm` / `2eab21467a4214c7` | **1.442** | **+1.092** | **8.87 %** | **`K`** / **`fc O`** | `FINDING-entry-signal-disarm-2026-08.md` §0; share computed at `FINDING-t1h-capacity-entry-phase0-2026-08-30.md` §4.1 |
| 3 | `entry_forward_expectation_signal` (duals re-levelled forward) | `…-t1h-fwdexp` / `a2dc52ffebf14761` | **1.442** | **+1.092** | **8.87 %** | `O` / `fc O` | `FINDING-entry-signal-forward-expectation-2026-08-25.md` §2 P2, §5 |
| 4 | `entry_margin_exhaustion` alone (D11-R volume rule, on the shipped signal) | `…-t1h-d11r-exhaustion` / `cc7bbe1170db65c2` | 0.954 | +0.604 | **4.91 %** | `O` / **`fc K`** | `docs/handoffs/FINDING-capx-d11r-entry-volume-rule-2026-08-30.md` §3 (wind 603.4 MW enters 2023) |
| 5 | **JOINT** — disarm **+** `entry_margin_exhaustion` | `…-t1h-c1joint-arm` / `0490af522537a67c` | **1.442** | **+1.092** | **8.87 %** | both cells stamped with this A/B | `FINDING-c1-joint-wind-ab-2026-08-31.md` §3.3 — **`NON_COMPLEMENTARY`** |
| 6 | `entry_margin_exhaustion` **+** `entry_forward_reserve_leg` — **the ERCOT forecast default at HEAD** (ruling Q15) | `…-t1h-d12c-armed` / `f061b2646bfaac8b` | **0.350** | **0.000** | **0.00 %** | `O` / `fc K` (both fields) | `docs/handoffs/FINDING-capx-d12c-confirm-pair-2026-08-30.md` §3–§4.1 row R-3/R-4/R-5: "wind 0.350"; arming `FINDING-capx-d12a-arming-2026-08-30.md` |
| 7 | `storage_entry_availability_gate` **+** `storage_entry_cost_normalized_rank` (Leg A pair, armed by R-A) | `…-t1h-capentry-repair` / `dcbd3b9567b2fe26` | **0.350** | **0.000** | **0.00 %** | `O` / `fc K` (both fields) | `FINDING-t1h-capentry-phase1-ab-2026-08-30.md` §3.1 wind row: `Δ\|err\| 0.0000`; arming §7 |
| 8 | `entry_dampers` | — | — | **0.000** | **0.00 %** | **`I`** / **`I`** | FFR-3L §2/§3 + FFR-9B §3 via the ERCOT shard cell — inert |
| 9 | `entry_vre_capacity_revenue` | — | — | **0.000** | **0.00 %** | **`I`** / **`I`** | `FINDING-entry-screen-t1h-2026-08.md` §7 cell table — inert: ERCOT is energy-only, capacity pays \$0 |

**Rows deliberately absent.** Every mechanism I could not cite to a committed
artifact is not in this table. In particular: no row is entered for the
Q15-armed pair *combined* with the R-A storage pair (§7 watch item — composed
but never solved), and no row is entered for `entry_lookahead_reprice`
disarmed *combined* with `entry_forward_reserve_leg`, because that posture
**does not construct** — `__post_init__` raises, `entry_forward_reserve_leg`
requires `entry_lookahead_reprice` (`PRECOMMIT-c1-joint-wind-2026-08-31.md`
Amendment 1, verified at the CLI).

### 1.1 The three numbers, and what they are

- **1,092.2 MW** — the wind that enters at the **2022 bridge step** whenever
  the entry screen consumes a locational price object. Identical to the
  megawatt in rows 2, 3 and 5. It is *not* re-derived per construction; it is
  one decision that three different price surfaces all admit.
- **603.4 MW** — the wind that enters at the **2023 step** under the volume
  rule on the shipped zone-flat signal (row 4). A different decision in a
  different year by a different route, and the two never coexist (§2).
- **0 MW** — every posture that leaves the shipped zone-flat signal in place
  without the volume rule acting alone on it: rows 6, 7, 8, 9.

---

## 2. Additivity — what composes, what does not, and why the naive sum overstates

**The naive sum is 13.77 %** (8.87 % signal + 4.91 % volume). **The measured
joint is 8.87 %.** The volume rule contributes **exactly 0.000 GW** of wind on
top of the dual-based level — a difference of **0.00 pp** against the best
single, not a partial composition
(`FINDING-c1-joint-wind-ab-2026-08-31.md` §3.3).

### 2.1 What is NOT additive, by construction

**The shared queue budget.** Both mechanisms allocate out of the same
`QUEUE_CAP_GW["ERCOT"] = 12` ISO budget and the same
`QUEUE_CAP_PER_TECH_GW` per-tech caps
(`FINDING-entry-screen-t1h-2026-08.md` §1.1). The Phase-0 record said so
before the joint arm was solved: *"they are not additive by construction,
since both act on the same shared queue budget"*
(`FINDING-t1h-capacity-entry-phase0-2026-08-30.md` §4.1). Two closures drawn
from one budget cannot be summed.

**And the mechanism is now measured, not merely asserted**
(joint A/B §3.4). The two legs act on **the same 5,550 MW of entering-2023
solar, from opposite sides**:

- Under the **shipped** zone-flat signal, the exhaustion walk stopped solar
  **below its cap** (4,946.6 → 1,250 in 2022; 5,550 → 4,946.6 in 2023),
  freeing budget headroom that bang-bang solar had consumed at a manufactured
  margin, and wind cleared into it. The volume rule's 4.91 % is **an indirect
  effect of a shipped-signal artifact**, not a wind result.
- Under the **dual-based** level that route is closed at both ends: (a) in the
  2022 step wind already clears on its own merit — the pure disarm builds
  1,092.2 MW there with no volume rule at all — so there is no headroom left
  to hand it; and (b) in the 2023 step the walk exhausts solar **all the way
  to zero** rather than partially, and no wind clears in its place.

**Exhausting a competitor to zero does not produce an entrant when the
entrant's own repriced margin never clears.** That single sentence is the
whole non-additivity result.

### 2.2 What the walk actually did in the joint arm

Exactly one decision changes across the entire 2021–2025 window: **entering-2023
solar, 5,550 MW → 0, fully exhausted.** Every other entry decision, storage
decision, technology and step is byte-identical to the pure disarm arm — the
2022-step wind included, left at exactly 1,092.2 MW (joint A/B §3.4). The arm
is **not** wiring-inert (pre-registered stop rule 3 checked mechanically and
read false; the walk emits 4 `screen_signal_diag_*.npz` dumps where the pure
disarm emits 0). It is live and it does not act on wind.

### 2.3 What DOES compose — trivially, and it is worth naming

Rows 7, 8 and 9 compose additively with anything, because each contributes
0.000 GW of wind. The storage-entry pair changes *which* storage technologies
2023 builds (`iron_air` 3,000 + `flow_battery` 2,000 → `li_ion_4hr` 3,000 +
`li_ion_8hr` 2,000) with **every addition band identical to the digit**, wind
included (`FINDING-t1h-capentry-phase1-ab-2026-08-30.md` §0, §3.1). It is a
technology-mix repair, not a wind closure, and this map credits it as neither
more nor less.

### 2.4 The signal family saturates

Three signal constructions — zone-flat MC-step + pro-forma tail (shipped),
raw prior-year zonal duals (disarm), duals re-levelled forward (fwdexp) —
produce entering-2024 signal means of **\$28.22 / ~\$156 / −\$48.22 per MWh**
and terminal reserve margins of **25.19 / 40.24 / 40.38 %**
(`FINDING-entry-signal-forward-expectation-2026-08-25.md` §3). Across that
~\$200/MWh swing the **wind number does not move**: 0.350 / 1.442 / 1.442 GW.
Signal construction owns the *sign structure* of the entry error (L-1's
result); it does not own the wind volume beyond the first 1.092 GW.

---

## 3. The residual — how much is unexplained, and what its shape says

### 3.1 The arithmetic

| basis | wind GW | **open GW** | **open %** |
|---|--:|--:|--:|
| **at HEAD's armed ERCOT forecast default** (row 6 posture; rows 7–9 add nothing) | 0.350 | **12.313** | **100.00 %** |
| **at the best measured posture** (rows 2 / 3 / 5 — none armed) | 1.442 | **11.221** | **91.13 %** |

**Credited against K-verdict mechanisms specifically.** The forecast-lane
`K` cells in the entry path — `vre_procurement_additions`,
`entry_margin_exhaustion`, `entry_forward_reserve_leg`,
`storage_entry_availability_gate`, `storage_entry_cost_normalized_rank`,
`capacity_screen_unified_lookahead`, `capacity_screen_scarcity_restoration`,
`entry_pipeline_aware_signal` — are **all already inside the 0.350 GW
baseline or measured at 0.000 GW of wind on top of it.** The one `K` cell
that carries wind is `entry_lookahead_reprice`, and its closure is obtained by
**disarming** it (its backcast cell is `K`; its forecast cell is `fc O`, moved
`K → O` by the disarm probe on 2026-08-24). **So there is no posture in which
crediting every K-verdict mechanism closes any of the 12.313 GW.** The honest
residual after full K credit is **12.313 GW, 100 %**.

### 3.2 What the residual's shape says about where it lives

Five measurements, each committed, and together they place the residual
outside the entry screen entirely.

1. **It is not a volume residual.** The trajectory is invariant across all
   three signal constructions, and the volume rule contributes 0.000 GW of
   wind on the dual level. D-1's bang-bang was the last candidate owner of the
   *amplitude* and it is productionized
   (`FINDING-entry-signal-forward-expectation-2026-08-25.md` §3;
   joint A/B §5 item 1: *"the wind entry miss is a SIGNAL-OBJECT question,
   not a volume question"*).

2. **It is not closed by making the signal locational, because wind does not
   clear on merit even there.** At the build-zone row, on the model's own
   committed zonal duals, wind's per-MWh margin is **negative in both
   admissible steps** — **−0.74 \$/MWh (2024)** and **−3.76 \$/MWh (2025)**
   against a **31.82 \$/MWh** LCOE
   (`FINDING-t1h-capacity-entry-phase0-2026-08-30.md` §4.3, "the honest
   limit"). Zonal resolution does not make ERCOT wind bankable in this model.

3. **Wind is shape-disfavoured in every ERCOT zone, on the model's own
   prices.** Capture ratio against its **own** zone's mean, 2024 duals:
   Houston/North/South/South_Central **0.9590**, West (the build zone)
   **0.9592**, Northeast **0.9767**, **Panhandle 0.4774**
   (Phase-0 §4.3 item 2). The headline 1.055 build-zone ratio is a **level**
   artifact — West's \$29.254 mean sits above an unweighted ISO mean of
   \$26.596 that Panhandle's \$11.752 drags down. Resolving zonally makes the
   build zone's *level* look good relative to a depressed average; it makes
   wind *shape*-favoured nowhere.

4. **The representation that would be more accurate makes the miss bigger.**
   `data/renewables.py:219` routes **both** ERCOT wind and solar to `"West"`.
   Panhandle — the wind-rich, congestion-depressed zone with the 0.477 capture
   ratio — is never a build zone, so its economics never reach the screen. A
   variant siting wind where ERCOT wind actually interconnects *"would move
   the answer by roughly a factor of two in the opposite direction"*
   (Phase-0 §4.3 item 3). The residual's true size, under a faithful siting
   representation, is plausibly **larger** than 11.221 GW.

5. **The one entry that does happen is the one the record cannot explain.**
   All 1,092.2 MW enters at the **2022 bridge step**, whose duals are not
   committed — *"no committed hourly LP duals for prior solve 2021 — keeper
   sidecars span 2023–2025 only"* (Phase-0 §4.4). The closure this map credits
   at 8.87 % is therefore measured end-to-end but **not attributed** at the
   step that produces it.

**The shape, stated in one sentence.** The residual does not live in the entry
screen's volume rule, its ranking object, its technology gate, or its price
construction; it lives in the fact that **the model's own price object, on
every construction measured including its own LP duals, prices ERCOT wind
below its levelized cost in every zone** — while the real ERCOT added
12.663 GW of it over 2023–2025. Whatever made those 12.663 GW bankable is not
a merchant energy margin, and the committed record does not name it.

---

## 4. DO-NOT-REDO — cells already adjudicated `R` / `I` / `G` (rule 26 duty a)

**Scope.** The ERCOT shard carries **40** cells at `R`, `I` or `G` at this
base. Listed here are the ones a future wind-entry or capacity-entry session
could plausibly reach for; the full population is enumerable from
`docs/codebase-site/data/mechanism-matrix/ERCOT.js` and every one of them
carries the same duty. **A future session may not re-test any of these without
new evidence.** Cells whose shard entry carries no `ev` string are marked as
such — that absence is reported, not filled.

### 4.1 Entry-lane cells

| cell | verdict | citation |
|---|---|---|
| `entry_dampers` | **`I` / `I`** | FFR-3L (`docs/handoffs/ffr-3l-ercot-t1x-attribution-2026-08-04.md` §2/§3 — four-arm 2×2, A≡C and D≡B exactly; the dampers carry the scored-window delta in the **wrong** direction, ruled out as the cause) + FFR-9B (`docs/handoffs/ffr-9b-vre-entry-diagnosis-2026-08-09.md` §3, diagnosis only: at the three hot screens every candidate clears cost 9–24×, so **the caps are the ENTIRE allocator**) |
| `entry_vre_capacity_revenue` | **`I` / `I`** | **No `ev` string in the shard.** The adjudication is in `docs/FINDING-entry-screen-t1h-2026-08.md` §7 cell table: *"DO NOT re-propose for ERCOT (inert: energy-only pays \$0)"* — ERCOT `MARKET_DESIGN.capacity_market = False` |
| `forecast_xyear_warmstart` | `.` / **`fc R`** | D-9 arming A/B (`docs/handoffs/wallclock-baseline-2026-07.md` Exp 5) + the retirement tie-flip that made Option 3 unacceptable (`docs/cross-year-warmstart.md`) |

### 4.2 Price-object cells the entry signal is built on

| cell | verdict | citation |
|---|---|---|
| `ordc_scarcity_overlay` | **`R`** (backcast) | ERCOT-97. The forecast-lane scarcity adder is the **separate** `capacity_screen_scarcity_restoration` object (`fc K`) — do not conflate them (`FINDING-entry-screen-t1h-2026-08.md` §7 cell table) |
| `internal_congestion_split` | **`G`** | Trough diagnosis §10 / ERCOT-117; re-affirmed and **measured-complete** by ercot-233's `NE_LOB` timing Phase-0 (all four precommitted drivers CLOSE clear of tolerance). **DO-NOT-REDO as a topology change** without genuinely sub-zonal admissible data — and `FINDING-ercot234-subzonal-survey-nelob-identity-2026-08-24.md` established that **no public rule-13 sub-zonal driver source exists** |
| `energy_online_capability_cap` | **`R`** | ERCOT shard `ev` (5,508 chars) |
| `online_capacity_envelope` | **`R`** | ERCOT shard `ev` |
| `temp_dependent_derate` | **`R`** | ERCOT shard `ev` |

### 4.3 Wind-specific cells

| cell | verdict | citation |
|---|---|---|
| `wind_ptc_vintage_offers` | **`I`** | **No `ev` string in the shard.** Adjudicated in `CLAUDE.md` (Dispatch & Commitment) as *"probe-adjudicated provably inert"*, with the reasoning in `docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md` §§7–10. This is a **dispatch-side offer** mechanism; the **screen-side** wind PTC is a different object and is already live (§5.1) |
| `negative_renewable_offers` | **`G`** | **No `ev` string in the shard.** `CLAUDE.md` records it default-off as rule-25 `[R-ISO-SCOPE]`-refused; reasoning in `docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md` §§7–10 |
| `ercot_wind_zone_shape` | `K` (keeper, **not** a DO-NOT-REDO) | listed only so a reader does not mistake it for an open wind lever — it is the armed backcast wind shape object |

### 4.4 Standing refusals a wind lane will meet

- **`entry_forward_reserve_leg` requires `entry_lookahead_reprice`.**
  `__post_init__` raises otherwise; verified through the real CLI path
  (`PRECOMMIT-c1-joint-wind-2026-08-31.md` Amendment 1, last row of its
  posture table). **The only posture that closes any of the miss (the disarm)
  is structurally incompatible with the currently-armed ERCOT forecast
  default.** That refusal was not revisited by R-B's charter and is not
  revisited here.
- **The ERCOT 2023 backcast admissible queue is EMPTY** under the open lane —
  new evidence or Door D (2026 SOM RTC+B-era anchors, ~mid-2027, card W)
  (`FINDING-ercot233-nelob-timing-phase0-2026-08-24.md`). The wind-entry
  residual is a forecast-lane object and does not reopen that queue.

---

## 5. What remains ADMISSIBLE — **nothing that closes the miss**

Assessed against rule 1 `[R-STRUCT]`, rule 13 `[R-MEASURED]` and rule 14
`[R-ACCURATE]`. **This section proposes no lever and charters nothing.** The
honest answer is that the frontier is closed, and this map states it rather
than manufacturing a candidate to fill the space.

### 5.1 The obvious candidate is already in the model

A reader arriving fresh will reach first for *"the screen must be missing the
wind PTC."* It is not. `wind_ptc_levelized_per_mwh`
(`src/market_sim/model/capacity_evolution/new_entry.py:479`) levelizes the §45
credit over book life and it is subtracted from wind's LCOE inside the entry
screen itself (`:576-577`), gated by `ira_wind_solar_last_year`. **The screen
already values wind with the PTC and wind still clears negative on the model's
own duals** (§3.2 item 2). The gap is not a missing credit.

### 5.2 The one structurally-admissible object in the record is measured
**anti-closing**

The build-zone routing (`data/renewables.py:219`, both ERCOT wind and solar to
`"West"`) is a modelling choice that a faithful representation would change —
that is a rule 14 `[R-ACCURATE]` object, not a fitting one. But Phase-0 §4.3
item 3 measured its direction: siting wind where ERCOT wind actually
interconnects moves the answer **~2× in the opposite direction**, because
Panhandle's capture ratio is 0.477 against West's 0.959. Under rule 14 a worse
fit from more accurate data is a reason to **keep the accurate input and hunt
the real root cause elsewhere** — it is emphatically not a reason to revert.
But it is also **not a closure**, and this lane does not charter it. Recording
it is the point: a future session must not read Phase-0's 1.055 build-zone
ratio as an argument that zonal resolution closes wind.

### 5.3 The named-but-unrun successor construction has a measured low prior

`FINDING-entry-signal-forward-expectation-2026-08-25.md` §4 named the
scarcity-consistent delta basis as a zero-DOF successor and did not run it,
and its §7 offered the owner (a) that successor or (b) rest. §2.4 above is why
(b) was the lane's own recommendation and why this map does not revive (a):
the wind number is **invariant across every signal construction measured**, so
a fourth construction carries a measured prior of returning the same 1.092 GW.
That is not a refusal — the object stays zero-DOF and admissible in kind — but
it is not a closure candidate on this evidence, and R-D placed the lane at
rest rather than at the successor rung.

### 5.4 What is forbidden, named so it is not re-derived

- **Any wind-specific entry adder, capture-ratio uplift, elasticity, or
  damping coefficient chosen to move the residual.** Rule 13
  `[R-MEASURED]` — no forward analogue; rule 21 `[R-DOF]` — *"a residual that
  can only be closed by a tuned value is an open root-cause issue, not a
  parameter"*, which `FINDING-entry-screen-t1h-2026-08.md` §7 L-1b/L-4 already
  states in those words for this exact screen.
- **Any entry credit calibrated to the 12.663 GW actual**, or pinning wind
  entry to observed CODs. Rule 13, explicitly refused for the sister CAISO
  storage object at L-4 and applying identically here.

### 5.5 The bounded exogenous object, named without chartering

`vre_procurement_additions` (`fc K`, armed) carries a committed vintage-2020
cohort of 6,761 MW (wind **1,847 MW**), of which 1,840.2 MW is injected in
evolving years and **~4,921 MW effective-2021 is held-and-discarded at the
base year**; FFR-9C §3.6 records that *"widening vintage/statuses/base-year
injection is an owner decision, refused here."* Two facts bound it as a
closure: it is an **exogenous pipeline read**, not entry economics — crediting
the miss to it would mean the model is reading wind off EIA-860 rather than
forecasting it — and its **entire wind cohort is 1.847 GW against a 12.313 GW
miss (15 %)**, so even fully injected it cannot close the object. It stays an
owner decision, untouched by this lane, and it is not offered here as a
candidate.

### 5.6 The verdict of this section

**Nothing admissible remains that closes the ERCOT wind entry miss.** The
volume side is measured non-complementary and contributes zero. The signal
side saturates at 1.092 GW across every construction solved. The one
accurate-data repair the record identifies is measured anti-closing. Every
remaining route is either already armed and worth 0.000 GW, already
adjudicated `R`/`I`/`G`, or forbidden by rules 13/21. **"The frontier is
closed" is the result, and it is a full-value one.**

---

## 6. Why the lane rests

The rest was earned by measurement, not by fatigue, and the arithmetic is what
makes that checkable six months out. **Six postures were solved against this
one object across nine days** — the shipped baseline, the dual-based signal
object, the forward-expectation signal, the volume rule alone, the volume rule
jointly with the signal object, and the Q15 pair that is now the armed default
— plus a seventh (the storage-entry repair pair) that touched the same screen
in the same window. Every one of them was posture-gated (a driver that
hard-fails on a third differing field), every one reproduced the registered
control's cache key `28cef3500ec1fd9e` byte-for-byte before any verdict was
read, and every one had its predictions committed before its solve. They
returned **three numbers**, the best of which is one 1,092.2 MW decision that
three structurally different price surfaces all admit and none exceeds. The
last untested combination — the joint arm R-B chartered precisely because the
two partial closures *looked* complementary — was solved and returned
**exactly the signal leg's number, adding 0.000 GW**, with both chartered
kill-gates passing and four of five pre-registered directions confirmed. That
is the difference between a lane that stopped and a lane that finished: the
hypothesis that would have justified continuing was named in advance, tested,
and measured false. What remains is not a lever waiting for effort; it is a
model whose own price object prices ERCOT wind below its cost in every zone,
which is a different question in a different part of the model, and the
discipline of rules 13 and 21 is exactly that you do not close it by paying
the residual. **The lane rests because the measurements ran out of things to
disagree about, and the map is what a future session reads instead of
re-running them.**

---

## 7. WATCH ITEM (open, unresolved)

**R-A armed the T1-H storage-entry pair** —
`storage_entry_availability_gate` and `storage_entry_cost_normalized_rank`,
**both default `True` since #4442** (`scenarios.py:4351`, `:4392`). **The
COMBINED posture with the capx desk's `entry_margin_exhaustion` is composed
but UNMEASURED.**

That framing is the finding's own. The ERCOT shard's `ev` string on both cells
records it verbatim: *"entry_margin_exhaustion armed as the ERCOT forecast
default at D12-A (ruling Q15) the day before, so a bare ERCOT T1-H run now
carries the exhaustion walk AND these gates together — the A/B ran at the
shipped unarmed walk by design (finding §4 item 2), so that combination is
composed-by-construction (rule 19: one gate helper, one rank helper, both
consumed by the walk) but UNMEASURED."*

**This lane does not measure it and does not propose measuring it.** It
belongs to the capx desk, which is not this program's to direct. It is
recorded here so that a reader of this map knows the armed default posture at
HEAD has never been solved as a whole, and therefore that row 6's
`wind 0.350 / 0.00 %` is measured at the Q15 pair **without** the R-A gates —
the closest solved posture to the current default, not the current default
itself.

---

## 8. Rule compliance

- **Rule 1 `[R-STRUCT]`** — the headline is reported at full magnitude and not
  softened: the joint arm closes 8.87 %, the volume rule adds 0.000 GW, the
  armed default closes 0.00 %, and the residual is stated as 100 % open at
  HEAD. §5.2 keeps an accurate-data object that is measured to make the miss
  *worse*, and says so.
- **Rule 12 `[R-PARALLEL]`** — no solve run; nothing to parallelize.
- **Rule 13 `[R-MEASURED]` / 14 `[R-ACCURATE]` / 21 `[R-DOF]`** — §5.4 names
  the forbidden closures explicitly; no parameter, adder or coefficient is
  introduced or proposed anywhere in this document.
- **Rule 15 `[R-DASHBOARD]`** — **no run is registered on either dashboard.**
  Nothing was solved; every bundle cited is already registered on the forecast
  namespace by the lane that produced it.
- **Rule 22 `[R-HOLDOUT]`** — no year is solved, scored or registered; every
  artifact read is from the registered 2021–2025 T1-H window; the freeze,
  markers and `calibration-complete.json` are untouched.
- **Rule 24 `[R-REGISTRY]`** — nothing tunable changed; no `ScenarioConfig`
  edit; no default flipped.
- **Rule 25 `[R-ISO-SCOPE]`** — every number is ERCOT's; no verdict transfers
  to or from any other ISO.
- **Rule 26 `[R-MECH-MATRIX]`** — **no mechanism is tested, so duty (b) does
  not fire and NO matrix shard is edited.** Duty (a) is discharged by §4,
  which reads and reports the adjudicated cells rather than re-testing any.
  Duty (c) does not fire — no `ScenarioConfig` field is added.
- **Rule 27 `[R-PUSH]`** — this file is written locally and pushed as exact
  on-disk bytes; being ≥300 lines it is blob-verified after push before
  anything else. No existing file is rewritten from response content; no CI
  workflow is added.
- **Out of scope and untouched:** every keeper shard, the mechanism matrix,
  `calibration-complete.json`, `holdout-freeze.json`, both registries,
  `program-status.json`, and the plan/board.

---

## 9. How to re-read this map

Zero solves; every figure is re-readable from committed artifacts.

```
# the six postures' scored additions (decision basis 2023-2025 vs RD-5)
#   each bundle's committed score.json, via its registry sidecar:
#     frontend/data/forecast/registry/ercot-2021-2025-realized-t1h-*.json
# the A/B artifacts that carry the per-step rows and the complementarity read
results/calibration/joint_wind_entry_ab_ercot.json         # rows 2/4/5 + K1/K2
results/calibration/entry_volume_rule_ab_ercot.json        # row 4
results/calibration/entry_confirm_pair_d12c_ercot.json     # row 6
results/calibration/storage_entry_repair_ab_ercot.json     # row 7
results/calibration/entry_signal_fwd_expectation_ercot.json# row 3
results/calibration/entry_signal_disarm_ledger_ercot.json  # row 2 per-step ledger
results/calibration/entry_signal_l1_dual_replay_ercot.json # section 3.2 capture ratios
results/calibration/entry_screen_t1h_phase0_ercot.json     # the baseline screen replay

# the zero-solve Phase-0 probe that produced section 3.2 items 2-4
python3 scripts/probes/_t1h_capentry_phase0.py --section legb
```

The verdict column of §1 and the whole of §4 are read from
`docs/codebase-site/data/mechanism-matrix/ERCOT.js` (rendered:
`docs/codebase-site/mechanism-matrix.html`) at base `54d5772c`.
