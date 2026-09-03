# FINDING — capx D46: the batched re-measure (Stage 1) — the fossil-dates flip does not add exits so much as RE-ROUTE them, and where it re-routes them differs by ISO; ERCOT's hindcast null is a window artifact that still made a gate leg worse; D41's zero-CCS result does not extend past PJM/MISO

**Lane:** capx D46 — the BATCHED RE-MEASURE the director queued at r#30/r#31 and
the owner scoped at r#32 (ruling **Q32: STAGED** — the cheap set now, the t1f tail
later). Branch `claude/capx-d46-remeasure-batch-oe1h77`, FRESH off `origin/main`
`32e07427`. The pre-declaration
`docs/handoffs/PREDECL-capx-d46-remeasure-2026-09-03.md` was committed and pushed
(`71d3f1a6`) **before the first solve started** and is graded at full magnitude in
§7, misses included.

**What this lane is.** A **BASELINE REFRESH, not an A/B.** Every registered
forecast bundle was stale on up to three independent axes already measured on
their own lanes — (i) **Q30/D44**, `fossil_announced_exits_enabled` flipped
default-ON at `57088c33`; (ii) **D41**, the CCS fixed-cost constants re-identified
(`ccs_retrofit_capex_kw` 900.0 → 1521.4, `fixed_om_gas_cc_ccs` 25.0 → 65.0);
(iii) **keeper vintage** — CAISO 231→240, MISO 198→202, NYISO 159→177. **No
per-ISO control was solved and nothing is attributed to an axis; nothing arms.**
No `ScenarioConfig` field is added or moved, no parameter value changes, no
keeper / shard / marker moves, the backcast namespace is untouched (rules 12, 13,
22, 25, 27, 28).

**Every pre-declared cache key was realized exactly.** Eight keys declared before
any solve; seven solved so far, all matching.

---

## 0. Verdict (one paragraph)

The refresh's substantive result is not that the dates flip adds retirements — it
is that **the flip re-routes the exit decision out of the economic screen, and
what happens to the displaced exits is per-ISO and does not transfer.** At **MISO**
the identical coal capacity still exits, moving from `retire:economic` 3684.0 MW to
`retire:announced` 2410.3 + 1495.9 derate — rule 19 working, no exit lost, and
`retire.unit_recall_gt300` flips **5/19 → 16/19, FAIL → PASS**, the batch's one
gate-leg improvement. At **NEISO** — the batch's one clean single-axis leg — the
same flip **loses 791.5 MW of coal economic exits and gains 849.4 MW of gas_cc
economic exits**, a genuine re-ranking at an ISO whose dated set holds essentially
no in-window coal, so recall goes **4/6 → 3/6** and `false_retire` **0.263 → 0.315**,
both worse. At **CAISO** exits rise into an ISO that barely retired anything, so
G3 reads worse by construction (+6.642 → +9.469) — the expected rule-14 signature.
At **ERCOT** the channel retires **exactly nothing** in the hindcast, because all
three of its filed rows are dated 2027–2029 and the window ends in 2025 — a
**data-coverage null, not a screen null** — and it *still* made a board row worse,
pushing `retire.unit_recall_gt300` from `SKIP` to a scored **0/1 FAIL** by making a
target reachable it then did not retire. The same three ERCOT rows **do** fire in
the 2026–2030 forecast window, so the hindcast null is a *window* artifact. On the
CCS axis, D41 §4.3's "at carbon = 0, no host class clears the retrofit bar in any
year" was scoped to PJM and MISO and **does not extend to ERCOT**, also carbon = 0,
where 14 conversions / 2741.8 MW clear on the corrected constants; and D41 §7's
routed RGGI question gets a **negative** answer in NEISO's t1f window — the
3 GW/yr/ISO cap **still binds in every year**. Determinations: **HOLD** on all four
T1-H legs and ERCOT t1f (all unchanged), **PROMOTE** on NEISO t1f (unchanged).

---

## 1. Scope corrections made before the first solve (pre-declaration §1)

**(a) The T1-F window is 2026–2030, not 2026–2050.** The dispatch priced the
Stage-1 t1f legs as "full-horizon 2026–2050". The t1f tier as registered is a
5-solve-year **2026–2030** gate run: `neiso-t1f`'s live record was
`neiso-2026-2030-s4b-ara`, every committed t1f sidecar spans 2026–2030, and
`VERDICT_MAP` keys the bare t1f keys off `<iso>-2026-2030-ff-t1-gate`. A 25-year
window is additionally REFUSED by `assert_schedulable` without
`--full-solve-authorized`, which **this lane does not hold for ERCOT or CAISO**.
Running 2026–2050 there would have been both an unregistrable tier mismatch and an
unauthorized full-horizon campaign. The three t1f legs therefore ran 2026–2030,
matching the keys they overwrite; GOLDEN-3 keeps its own 2026–2050 window under the
NEISO §2.1b authorization.

**(b) The NEISO T1-H leg reproduced the bare key's flag set**, so it kept
`--neiso-net-icr-requirement`. The dispatch's posture rule has two halves that
diverge at exactly one leg, and the second — *"read the last committed bare-key
bundle's `run_config.json` for the flag set … and change NOTHING except what HEAD's
defaults changed"* — governs, because dropping D37's Q28 lever would have added a
FOURTH axis to a lane whose discipline is that it attributes nothing. **Consequence
stated, not fixed:** the bare `neiso-t1h` key continues to advertise a posture that
is not NEISO's shipped default (`neiso_net_icr_requirement` ships `False`, and
D37's own P9 flip condition failed). That is D37's standing decision;
`neiso-t1h-d37-control` remains the unarmed-posture record. **ROUTED to the
director**, not re-litigated here.

**(c) D41's CCS axis is INERT in all four T1-H legs — asserted before the solves
and VERIFIED after.** `ccs_retrofit_available_year=2028` and the T1-H window solves
{2021, 2023, 2024, 2025}, so no retrofit decision can be taken. Verified from the
per-year `evolution_<year>.json` ledgers: `ccs_retrofits` is the **empty list in
every solve year of every T1-H leg**. Axis (ii) therefore touches the forecast legs
only, which is where §4 reads it.

**(d) A cost correction the pre-declaration also made.** The dispatch prices
GOLDEN-2's re-solve at "~35 min, ~3.5 GB". That is the campaign solve alone; full
rubric scoring as GOLDEN-2 did it includes the FC-6 paired battery, measured at
**2.30 h** in GOLDEN-2 §7.1.

---

## 2. Environment and cost, reported because they were not free

This container began with **no Python dependencies and an empty `data/clean`**.
`uv sync` installed the pinned runtime; `regenerate_clean.py` built **54 datatypes
in ~55 min**, one of which (`ercot-wtx-congestion`) failed on a missing `tzdata`
and was repaired and re-run rather than left as a silent gap. That prerequisite is
a real part of this session's wall clock and is stated rather than absorbed.

Measured wall times, against the board's `c_cost` estimates:

| leg | board estimate | measured | note |
|---|---|---|---|
| NEISO T1-H | ~6 min | ~7 min | paired with CAISO |
| CAISO T1-H | ~20 min | ~10 min | paired with NEISO |
| ERCOT T1-H | ~10–15 min | ~12 min | paired with GOLDEN-3 launch |
| MISO T1-H | ~25 min | ~24 min | solo (rule 12) |
| ERCOT T1-F | **2.0 h** | **11.8 min** | 4.1 GB peak; the estimate is an order out |
| NEISO T1-F | **1.0 h** | **8.0 min** | 3.3 GB peak; likewise |

The two t1f estimates the board carries are **wildly conservative**, which matters
for scheduling Stage 3: if PJM's 7.3 h and MISO's 10.1 h carry the same factor,
the owner-scheduled tail may be far cheaper than it was priced. That is an
observation about the estimates, not a measurement of PJM or MISO, and it is
**routed, not asserted**.

---

## 3. The register — every key, before and after

| bare key | prior preserved at | new record | cache key (pre-declared = realized) | keeper at HEAD | determination |
|---|---|---|---|---|---|
| `neiso-t1h` | `neiso-t1h-pre-d46` | `neiso-2021-2025-realized-t1h-d46` | `da19b85495178949` | `2026-08-17-neiso-99-joint-p1` | HOLD → HOLD |
| `miso-t1h` | `miso-t1h-pre-d46` | `miso-2021-2025-realized-t1h-d46` | `eff2c890746ec966` | `2026-09-03-miso-202-unitclip` | HOLD → HOLD |
| `caiso-t1h` | — (**MINTED**) | `caiso-2021-2025-realized-t1h-d46` | `2c8cc7d19ccaed4c` | `2026-09-03-caiso-240-b1-stgas` | (new) HOLD |
| `ercot-t1h` | — (**MINTED**) | `ercot-2021-2025-realized-t1h-d46` | `67d5dcc1ada2e2df` | `2026-08-25-234-eastex-identity` | (new) HOLD |
| `ercot-t1f` | `ercot-t1f-pre-d46` | `ercot-2026-2030-d46-remeasure` | `873d8c0e6cab52ae` | `2026-08-25-234-eastex-identity` | HOLD → HOLD |
| `neiso-t1f` | `neiso-t1f-pre-d46` | `neiso-2026-2030-d46-remeasure` | `6690e4d6d66bc819` | `2026-08-17-neiso-99-joint-p1` | PROMOTE → PROMOTE |
| `caiso-t1f` | `caiso-t1f-pre-d46` | *(§8)* | `772b1e5abc7fc80c` | `2026-09-03-caiso-240-b1-stgas` | *(§8)* |
| `neiso-t3` | `neiso-t3-pre-d46` | *(§8)* | `67678e58b2d0526c` | `2026-08-17-neiso-99-joint-p1` | *(§8)* |

**Every realized cache key matched its pre-declared value**, and none collided
with any of the 88 keys committed under `results/`.

**Run-id deviation, recorded.** The pre-declaration guessed t1f run ids of the form
`<iso>-2026-2030-t1f-d46`. `register_forecast_run.py --summary` derives the id as
`<iso>-<start>-<end>-<label>`, so with the dispatch's own `--label d46-remeasure`
the actual ids are `<iso>-2026-2030-d46-remeasure`. `VERDICT_MAP` and every verdict
provenance carry the **actual** ids.

**`VERDICT_MAP` discipline.** New rows were added for each new run. Two superseded
rows were **RE-POINTED in place** to their `-pre-d46` preservations
(`neiso-2021-2025-realized-t1h-d37-armed`, `miso-2021-2025-realized-t1h-d33`)
rather than shadowed by a second literal with the same key — the dispatch's
"add rows, never edit existing ones" would have produced a **duplicate dict key**,
which is silently order-dependent and would trip any dup-key check. Re-pointing is
the `miso-t1h-pre-d31` / `-pre-d33` precedent and keeps the invariant the map
exists for: *a run must never render a verdict its own score contradicts.* Verified
by AST: 44 rows, **zero duplicate keys**.

---

## 4. What actually moved — per ISO, at full magnitude

### 4.1 The mechanism the batch surfaced: the flip RE-ROUTES exits, and the sign is per-ISO

Window totals by channel, read from the per-year `evolution_<year>.json` ledgers
(not inferred from the score):

| | dates OFF (preserved) | dates ON (D46) |
|---|---|---|
| **MISO** | coal `retire:economic` **3684.0 MW** — the only thermal exit | **ZERO economic exits of any fuel**; coal 2410.3 retire + 1495.9 derate, gas_st 504.1 + 313.8, gas_ct 132.3 derate, oil 153.0 retire — all `announced` |
| **NEISO** | coal `retire:economic` **791.5 MW**; gas_st `retire:economic` 1438.2; gas_cc `retire:confirmed` 706.8 | coal `retire:economic` **0.0**; gas_cc `retire:economic` **849.4** (new); gas_st `retire:economic` 1438.2 (unchanged to the decimal); gas_cc `derate:announced` 539.5; oil `retire:announced` 26.0 |

**MISO is rule 19 working, not a lost exit.** The same coal capacity still exits
(3684.0 → 3906.2 MW); it moves out of the economic screen's jurisdiction into the
channel holding its filed date, which is exactly what CLAUDE.md's step-1 amendment
describes and what D42's "displaces nothing" claims. **Verified directly against
D42's own committed legs at zero solve cost**: its control shows coal
`retire:economic` 3684.0 MW and its armed leg the identical `announced` breakdown.

**NEISO genuinely re-ranks.** It loses 791.5 MW of coal economic exits and gains
849.4 MW of gas_cc economic exits. Its dated set holds essentially no in-window
coal (Merrimack, 113.6 MW, dated 2027), so the coal that stops exiting **was not
exempted by its own filed date** — the re-ranking runs through the derate path's
effect on the margin surface. **The sign of the coal effect is per-ISO and
transfers to nobody.** The full causal decomposition needs a paired control, which
a baseline refresh does not carry by charter; it is **ROUTED, never inferred**.

### 4.2 T1-H retirement rows, before → after

| | `retire.total_gw` model (actual) | err_frac | `unit_recall_gt300` | `false_retire` |
|---|---|---|---|---|
| **NEISO** | 3.645 → **4.447** GW (4.997) | −0.271 → **−0.110** | 4/6 = 0.667 → **3/6 = 0.500** (FAIL both) | 0.263 → **0.315** (FAIL both) |
| **MISO** | 4.469 → **9.799** GW (17.369) | −0.743 → **−0.436** | 5/19 = 0.263 → **16/19 = 0.842**, **FAIL → PASS** | 0.000 → 0.000 (PASS both) |
| **CAISO** | 2.240 → **3.068** GW (0.293) | +6.642 → **+9.469** | n/a (SKIP both) | 2.240 → 2.969 GW; frac **1.000 → 0.968** |
| **ERCOT** | 0.000 → **0.000** GW (2.294) | −1.000 → −1.000 | n/a SKIP → **0/1 FAIL** | 0.000 → 0.000 (PASS both) |

Per-fuel classes opening off exactly zero: **MISO** gas_cc 0.002, gas_ct 0.132,
gas_st 0.849, oil 0.154 GW; **NEISO** oil 0.547, gas_ct 0.006 GW; **CAISO** gas_st
0.821 (all `derate:announced`, Redondo Beach p356), gas_ct 0.007 GW.

**CAISO's 2.240 GW nuclear false-retire is not this channel's** and persists to the
decimal: the ledgers show it as `nuclear retire:announced` (1122.0 MW 2024 + 1118.0
MW 2025) through the **non-fossil** announced route, present at both postures and
unmoved by the keeper going 231 → 240.

### 4.3 The FC-3 band-FAIL lists — mostly blind

| ISO | before | after | membership change |
|---|---|---|---|
| NEISO | 11 rows | 11 rows | **NONE — byte-identical** |
| CAISO | 11 rows | 11 rows | **NONE** |
| MISO | 8 rows | 8 rows | −`retire.unit_recall_gt300`, −`add.shares.gas_cc`; +`add.by_tech.gas_ct`, +`add.shares.gas_ct` |
| ERCOT | 10 rows | 11 rows | +`retire.unit_recall_gt300`, +`add.shares.gas_ct`; −`add.by_tech.gas_ct` |

At NEISO the gate leg is **blind to every one of §4.1's moves** — the same
blindness D37 recorded of its own lever. Only MISO's flip and ERCOT's
reachable-set change are visible at gate grain.

### 4.4 ERCOT: a data-coverage null that still made a board row worse

The channel is **correctly armed** at ERCOT and loads 3 live rows / 1309 MW —
O W Sommers 1 (2027, 446 MW gas_st), J K Spruce (2028, 566 MW coal), O W Sommers 2
(2029, 446 MW gas_st) — and **every one is dated past 2025**, the T1-H window's last
solve year. `announced_derates` is the empty list in all four solve years.

It nonetheless moved a gate leg **the wrong way**: because the dates channel counts
as an admissible exit route, the **D-24 reachable-set member rule** stops excluding
one of the two ≥300 MW targets, so `retire.unit_recall_gt300` goes n/a (`SKIP`) → a
scored **0/1 FAIL** and joins the band-FAIL list. **A board row got worse on an
input that retired nothing.**

**And the null is a WINDOW artifact, not an ERCOT-wide coverage gap**: in the
2026–2030 t1f window all three rows fire — gas_st 446.0 MW derate 2027, coal 566.0
MW derate 2028, gas_st 446.0 MW retire 2029.

### 4.5 The CCS axis, where it is live

| leg | posture | conversions | cap binding? |
|---|---|---|---|
| all four T1-H | either | **0 rows in every solve year** | n/a — retrofits open 2028, window ends 2025 |
| **ERCOT t1f** (carbon = 0) | corrected constants | 2028: 11 rows / **2130.9 MW**; 2029: 3 / **610.9 MW** | — |
| **NEISO t1f** (RGGI) | preserved (900 / 25.0) | 2028 20 rows / 2999.9 MW · 2029 23 / 2999.4 · 2030 15 / 2997.5 — **58 rows, 8996.8 MW** | **yes, every year** |
| **NEISO t1f** (corrected 1521.4 / 65.0) | D46 | 2028 17 / 2999.6 · 2029 23 / 2994.4 · 2030 10 / 2948.6 — **50 rows, 8942.6 MW** | **yes, every year** |

Two results, both against expectation:

1. **D41 §4.3's zero-clearing result does not extend past PJM and MISO.** ERCOT is
   also carbon = 0, and 14 conversions / 2741.8 MW clear there on the **corrected**
   constants. D41 scoped its claim to the two ISOs it reconstructed and this does
   not contradict it — it bounds it. **Why ERCOT's host economics clear a bar PJM's
   and MISO's do not is not answered here and is ROUTED, not inferred.**
2. **D41 §7's routed RGGI question gets a NEGATIVE answer in this window.** The
   corrected constants thin the conversion count (58 → 50 rows) and trim total MW
   by 0.6 %, but **the 3 GW/yr/ISO cap still binds in every year**. This lane
   pre-declared that it would stop binding in at least one year; it does not.

---

## 5. Board refresh and gate integrity

`scripts/check_gate_a_provenance.py` reads **OK (6 rows)** — before, during and
after. **This corrects the pre-declaration's §5 expectation**, which anticipated
inheriting the r#32 §0ac gate-(a) failures on CAISO/MISO/NYISO: those were repaired
by audit v23 and the C-2 grant before this lane started. **Gate (a) was never
moved by this lane**, as chartered.

`scripts/check_forecast_staleness.py` runs clean (WARN-level only, never blocking).
`scripts/check_mechanism_matrix.py`: integrity OK, anchors 0 unresolvable beyond
the ratchet, keeper stamps and §5.x prose headers match every shard.

FC legs and gate rows were re-derived **only where a record moved**; no untouched
row was rewritten.

---

## 6. Matrix (rule 28) — no verdict letter moves

No mechanism was tested, so **no cell verdict moves**. Each of the four Stage-1
shards gains its own ISO's measured evidence on `fossil_announced_exits` (rule 25),
which is what the cells' standing *"OPEN HERE: this ISO's own T1-H measurement of
its own exit cohort"* clause asked for.

**NEISO qualifies for the dispatch's bounded exception** — single-axis delta,
keeper unmoved, CCS verified inert in both legs — and its cohort measurement is now
**supplied**. It stays `fc: O` rather than becoming `K` **because the reading is
genuinely MIXED**: `retire.total_gw` improves while recall and `false_retire` both
worsen. Stamping `K` ("tested & accepted") on that would claim an acceptance the
numbers do not support. **MISO**'s `K` stands on D42 and is *confirmed* at HEAD,
not re-tested. **CAISO** stays `O` (two axes, so not the clean cohort measurement
the cell is open for). **ERCOT** stays `O` for the strongest reason: its cohort
**cannot be measured in a T1-H window at all**.

---

## 7. The pre-declaration, graded at full magnitude

**Cache keys: 7 predicted, 7 realized exactly. Postures: as declared on every leg.**

| # | prediction | conf | outcome |
|---|---|---|---|
| 1 | ERCOT `retire.total_gw` UP off exactly zero | **HIGH** | **MISS** — stays 0.000 GW |
| 2 | ERCOT coal + gas_st model UP off zero | **HIGH** | **MISS** — both stay 0.000 |
| 3 | ERCOT err_frac toward 0 | HIGH | **MISS** — stays −1.000 |
| 4 | ERCOT `false_retire` UP off zero, band may flip PASS→FAIL | MED | **MISS** — stays 0.0, PASS |
| 5 | ERCOT recall becomes scorable | MED | **HIT** — n/a → 0/1, `n_excluded_unreachable` 2 → 1 |
| 6 | MISO recall UP to ≈16/19, FAIL→PASS | **HIGH** | **HIT, exactly** — 16/19 = 0.842, PASS |
| 7 | MISO `retire.total_gw` UP, err toward 0 | HIGH | **HIT** — 4.469 → 9.799, −0.743 → −0.436 |
| 8 | MISO gas_cc/gas_ct/gas_st/oil all UP off zero | HIGH | **HIT** — all four |
| 9 | MISO `false_retire` stays ≈0, PASS | MED | **HIT** — 0.000, PASS |
| 10 | NEISO `retire.total_gw` UP, err toward 0 | MED | **HIT** — 3.645 → 4.447, −0.271 → −0.110 |
| 11 | NEISO oil + gas_ct UP off zero | MED | **HIT** — 0.547 / 0.006 GW |
| 12 | NEISO recall UP; FAIL→PASS a live possibility | MED | **MISS, wrong direction** — 4/6 → 3/6 |
| 13 | NEISO `false_retire` frac FALLS; band stays FAIL | MED | **SPLIT** — band FAIL held; frac ROSE 0.263 → 0.315 |
| 14 | CAISO `retire.total_gw` UP ⇒ err_frac WORSE | MED | **HIT** — +6.642 → +9.469 |
| 15 | CAISO gas_st + gas_ct UP off zero | MED | **HIT** — 0.821 / 0.007 GW |
| 16 | CAISO `false_gw` UP absolute, `frac_of_model` falls below 1.0 | MED | **HIT** — 2.969 GW, 0.968 |
| 17 | CAISO nuclear false-retire: **no prediction**, read only | — | persists to the decimal; it is the **non-fossil** announced route |
| 18 | `retire.total_gw` stays FAIL on ≥3 of 4 legs | — | **HIT** — FAIL on all four |
| 19 | D41 axis INERT in all four T1-H legs | — | **HIT, verified** from the ledgers |
| 20 | ERCOT t1f: **zero** CCS conversions (carbon = 0) | — | **MISS** — 14 conversions / 2741.8 MW |
| 21 | NEISO golden: fewer conversions **AND** the 3 GW cap stops binding in ≥1 year | — | **SPLIT** (t1f window) — fewer (58 → 50 rows), but the cap **still binds every year** |
| 22 | CAISO CCS: **no prediction** | — | §8 |
| 23 | keeper-vintage axis: **no direction predicted** | — | held; none asserted |

**The four ERCOT misses share one cause, and it was avoidable.** I predicted at
HIGH confidence that ERCOT's exits would move off zero without first checking
whether ERCOT has any filed date inside the window. One committed-artifact query —
the same `load_announced_fossil_exits` call §4.4 reports — would have shown all
three rows dated 2027–2029 before a single solve ran. That is a process miss, not
a model surprise, and the pre-declaration was weaker for it.

**Prediction 12 is the interesting miss.** I reasoned from "the channel can only
ADD exits", which §4.1 shows is false: it re-routes them, and at NEISO the
re-routing costs more recall than it buys.

---

## 8. Stage status

| stage | status |
|---|---|
| **1a** T1-H ×4 (NEISO, CAISO, ERCOT, MISO) | **COMPLETE** — registered, board refreshed, blob-verified |
| **1b** GOLDEN-3 (`neiso-t3`) | *(filled below)* |
| **1c** T1-F ×3 | ERCOT **COMPLETE** · NEISO **COMPLETE** · CAISO *(filled below)* |
| **1d** board refresh | **COMPLETE** for every landed key; gate (a) untouched |
| **1e** matrix | **COMPLETE** — four shards stamped, no verdict letter moved |
| **2** PJM/NYISO t1h + NYISO t1f | **PENDING** — gated on D45's §9 close-out reaching `origin/main` |
| **3** PJM t1f + MISO t1f | **NOT THIS DISPATCH** — owner-scheduled |

### Stage-1 stale-set closure (ledger §0ac.7)

| key class | §0ac.7 status | now |
|---|---|---|
| `neiso-t1h` `miso-t1h` `caiso-t1h` `ercot-t1h` | stale on (i)+(iii) | **CLOSED** |
| `ercot-t1f` `neiso-t1f` | stale on (i)+(ii) | **CLOSED** |
| `caiso-t1f` `neiso-t3` | stale on (i)+(ii)+(iii) | *(§8.1)* |
| `pjm-t1h` `nyiso-t1h` `nyiso-t1f` | stale | **PENDING Stage 2** |
| `pjm-t1f` `miso-t1f` | stale | **PENDING Stage 3** |

---

## 9. Routed to the director

1. **The re-routing decomposition.** NEISO loses coal economic exits its own filed
   dates do not explain. Needs a paired control this lane does not carry.
2. **ERCOT's CCS clearing at carbon = 0**, where PJM and MISO clear nothing on the
   same corrected constants.
3. **The board's t1f cost estimates are an order out** (2.0 h → 11.8 min; 1.0 h →
   8.0 min). If PJM's 7.3 h and MISO's 10.1 h carry the same factor, Stage 3 may be
   far cheaper than priced.
4. **`neiso-t1h` advertises a non-shipped posture** (D37's Q28 lever), preserved
   here deliberately so the refresh stayed single-axis.
5. **A gate leg can worsen on an input that changes nothing** — ERCOT's
   reachable-set flip. Worth knowing before reading any recall row as skill.
