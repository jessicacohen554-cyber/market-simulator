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

**Every pre-declared cache key was realized exactly.** Eight keys declared before any
solve; **all eight solved, all eight matching** — plus the four FC-6 arm keys, of which
the `base` arm's is byte-equal to the campaign's, which is the reproduction gate.

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
where 14 conversions / 2741.8 MW clear on the corrected constants.
And **D41 §7's routed RGGI question is answered on the full horizon by GOLDEN-3, more
sharply than it was asked**: the corrected constants **end NEISO's retrofit wave nine
years early** — conversions fall 83 rows / 14,774.5 MW → 60 / 11,208.9 MW (−24.1 %) and
the 2040 conversion that sat *at* the 3 GW cap disappears entirely — even though the cap
still binds in 2028–2030. The 2026–2030 t1f window cannot see any of that, because the
wave outlives the window. Determinations: **HOLD** on all four T1-H legs, ERCOT t1f,
CAISO t1f and GOLDEN-3 (all unchanged), **PROMOTE** on NEISO t1f (unchanged).

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
| CAISO T1-F | **2.8 h** | **22.6 min** | 4.9 GB peak; likewise |
| GOLDEN-3 campaign | ~35 min | **33.0 min** | 3.7 GB peak, 25/25 years — this anchor was right |
| GOLDEN-3 FC-6 battery | 2.2–2.7 h | **2.37 h** | 4 paired arms at 32.5–32.9 min + the T1.6 ladder at 11.0 min |

**All three t1f estimates the board carries are wildly conservative — by factors of
7–10× — while the GOLDEN-2-derived anchors (35 min campaign, 2.2–2.7 h battery) were
accurate.** That asymmetry matters for scheduling Stage 3: if PJM's 7.3 h and MISO's
10.1 h carry the same t1f factor, the owner-scheduled tail may be far cheaper than it
was priced. That is an
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
| `caiso-t1f` | `caiso-t1f-pre-d46` | `caiso-2026-2030-d46-remeasure` | `772b1e5abc7fc80c` | `2026-09-03-caiso-240-b1-stgas` | HOLD → HOLD |
| `neiso-t3` | `neiso-t3-pre-d46` | `neiso-2026-2050-t3-golden3-bau` | `67678e58b2d0526c` | `2026-08-17-neiso-99-joint-p1` | HOLD → HOLD |

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
| **CAISO t1f** (state carbon) | corrected | 2028 37 / 2997.1 · 2029 12 / 2997.9 · 2030 11 / 2857.3 | **yes, every year** |
| **GOLDEN-2** 2026–2050 (RGGI) | preserved (900 / 25.0) | 2028–2032 **and 2040** — **83 rows, 14,774.5 MW** | 2028, 2029, 2030 **and 2040** (3000.0 MW) |
| **GOLDEN-3** 2026–2050 (RGGI) | corrected (1521.4 / 65.0) | 2028–2031 only — **60 rows, 11,208.9 MW** | 2028, 2029, 2030; **2040 gone** |

Two results, both against expectation:

1. **D41 §4.3's zero-clearing result does not extend past PJM and MISO.** ERCOT is
   also carbon = 0, and 14 conversions / 2741.8 MW clear there on the **corrected**
   constants. D41 scoped its claim to the two ISOs it reconstructed and this does
   not contradict it — it bounds it. **Why ERCOT's host economics clear a bar PJM's
   and MISO's do not is not answered here and is ROUTED, not inferred.**
2. **D41 §7's routed RGGI question is answered — and the window you ask it in
   decides the answer.** In NEISO's **2026–2030 t1f** window the corrected constants
   thin the conversion count (58 → 50 rows) and trim total MW by 0.6 %, but the
   3 GW/yr cap **still binds in every year**, so read there the answer is "no
   change". On the **full 2026–2050 horizon** the same comparison reads very
   differently: conversions fall **83 → 60 rows** and **14,774.5 → 11,208.9 MW
   (−24.1 %)**, and the wave **ENDS IN 2031 INSTEAD OF 2040** — GOLDEN-2 converted
   in 2028–2032 and again in 2040 at exactly the 3000.0 MW cap; GOLDEN-3 converts
   in 2028–2031 and nothing thereafter, so **2040 no longer binds because no
   retrofit clears there at all**. The t1f window is structurally blind to this
   because the retrofit wave outlives it. **A five-year instrument cannot answer a
   twenty-five-year question**, and that is the transferable lesson, not the number.
3. **CAISO's state-carbon case, which D41 never dispositioned**, clears retrofits
   with the cap binding in every t1f year (2997.1 / 2997.9 / 2857.3 MW). Read, not
   graded — this lane made no prediction for it.

### 4.6 The forecast legs, gate-row by gate-row

**Scope caveat that governs the whole subsection.** `ercot-t1f-pre-d46` and
`caiso-t1f-pre-d46` are **FFR-3A-2 vintage** records (cache epoch 2026-08-03), so
their deltas span a month of HEAD movement *plus* this batch's three axes and are
attributable to none of them individually. They are reported as *"the board row
this replaces"*. `neiso-t1f-pre-d46` and `neiso-t3-pre-d46` are recent and their
deltas are much closer to the axes themselves — GOLDEN-3's, in particular, is
**exactly** the three axes.

| leg | determination | what moved |
|---|---|---|
| **ERCOT t1f** | HOLD → HOLD | I12 reserve margin 2027 9.1 → 8.9 %, 2028 3.8 → 3.0 %, 2029 3.0 → **−2.5 %**, 2030 −1.5 → **−7.1 %** (FAIL throughout, now negative two years earlier); sustained-VOLL `hours_ge_500` peak **1137 → 4039 h/yr** vs the 800 h bar. **All worse.** |
| **NEISO t1f** | PROMOTE → PROMOTE | All 14 invariants PASS both; every FC-2 row PASS both. One row moves: backstop share 0.0 → 1.2 % (bar 10 %). **Essentially unchanged.** |
| **CAISO t1f** | HOLD → HOLD | I12 2026 1.8 → **10.4 %**, 2027 **−3.1 → 7.7 %**, 2028 **−0.3 → 10.2 %** (still below the 15 % floor, but **no longer negative in any year**), 2029 leaves the out-of-band list; backstop share 65.5 → **52.6 %**; FC-1 FAIL set **shrinks** `[I12, I3, I7] → [I12, I7]`. **The one Stage-1 leg better on every moved row.** |
| **GOLDEN-3** | HOLD → HOLD | Category map identical to GOLDEN-2 on **seven of eight**. Final reserve margin 6.6 → 5.4 % (in band both); backstop share 0.0 → 0.3 % (PASS both); cobweb widens `gas_cc(7)` → `gas_ct(7); gas_cc(11)` (FAIL both); FC-1's I3 renewable-dump failure **identical year-by-year**. All three paired invariants PASS both, with **P2 now clean** where GOLDEN-2's carried a *"not scored at this grain"* qualifier. |

**Two instrument differences, reported rather than absorbed, because each moves a
category for a reason that is not the model:**

1. **NEISO t1f, in the improving direction.** Its first score read
   PROMOTE-WITH-CAVEATS purely because no DOF ledger was passed. The ledger was
   then **built from this run's own `run_config.json`** by the committed
   `build_forecast_dof_ledger.py` (7 entries, 0 UNIDENTIFIED — the same shape as
   the preserved record's) and the re-score reads PROMOTE, matching its baseline.
   That is an instrument gap **closed**, not a model gain.
2. **GOLDEN-3, in the worsening direction — and this one is left standing.** FC-7
   goes PASS → **FAIL** on a single row: `no forecast_attestation.json (a golden
   run cannot be certified unattested)`. Its other three FC-7 rows all PASS exactly
   as GOLDEN-2's did. **No attestation was authored, deliberately.** This lane's
   pre-declaration did not declare one — it treated the leg as a re-solve rather
   than a new campaign, which was an oversight — and authoring one *after* reading
   that the row fails without it is exactly the sequence golden-1 refused and that
   GOLDEN-2 §3 wrote its own pre-declaration to prevent: *"inventing an instrument
   after the pre-declaration to clear a row is forbidden."* **The governance value
   of that rule is in the sequence, not the content**, so the row is left failing
   and named here instead. The determination is HOLD either way — GOLDEN-3 already
   carries four FC FAILs — so **nothing the board reads is changed by it**. A
   properly pre-declared attestation is **ROUTED**; it would restore FC-7 with no
   re-solve.

**FC-4 correction, recorded against myself.** GOLDEN-3's first T3 score read FC-4
`SKIPPED` because I passed a crossover-score path that does not exist. That was my
error, not a property of the run; re-scored against the committed
`neiso-2023-2027-crossover-rcrepair` crossover score, FC-4 reads **FAIL**, matching
GOLDEN-2. Only the corrected score was registered.

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
| 21 | NEISO golden: fewer conversions **AND** the 3 GW cap stops binding in ≥1 year | — | **HIT on the full horizon** — 83 → 60 rows, and 2040 stops binding entirely. (Read in the 5-year t1f window alone it is a SPLIT: fewer rows, cap still binding — the window is blind to it.) |
| 22 | CAISO CCS: **no prediction** | — | retrofits clear; cap binds every t1f year. Read, not graded. |
| 23 | keeper-vintage axis: **no direction predicted** | — | held; none asserted |
| 24 | GOLDEN-3 FC-6 battery vacuous ⇒ CAVEAT (GOLDEN-2's standing expectation, carried) | — | **HIT** — both T1.6 rungs all-constant, FC-6 CAVEAT |

**Tally: 13 hits, 6 misses, 1 split, 3 deliberate non-predictions, and 8/8 cache
keys.** Two of the misses (20, and 21 read narrowly) are the same lesson from
opposite ends: **D41's per-ISO CCS result does not transfer, and a five-year
instrument cannot answer a twenty-five-year question.**

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
| **1b** GOLDEN-3 (`neiso-t3`) | **COMPLETE** — campaign + full FC-6 battery + T1.6 ladder, registered |
| **1c** T1-F ×3 | **COMPLETE** — ERCOT, NEISO, CAISO all registered |
| **1d** board refresh | **COMPLETE** for every landed key; gate (a) untouched |
| **1e** matrix | **COMPLETE** — four shards stamped, no verdict letter moved |
| **2** PJM/NYISO t1h + NYISO t1f | **PENDING — GATE VERIFIED CLOSED, NOT STARTED.** Checked against `origin/main` at the end of this session: `FINDING-capx-d45-pjm-nyiso-curves-2026-09-03.md` §§4, 5, 6, 7, 8 **and 9** are all still literal placeholders (`[filled]`, `[filled after L4]`, `[filled after L2/L3]`). D45 owns the PJM/NYISO forecast surfaces until it closes. Per the dispatch this lane **STOPS after Stage 1**; the director re-releases Stage 2. |
| **3** PJM t1f + MISO t1f | **NOT THIS DISPATCH** — owner-scheduled |

### Stage-1 stale-set closure (ledger §0ac.7)

| key class | §0ac.7 status | now |
|---|---|---|
| `neiso-t1h` `miso-t1h` `caiso-t1h` `ercot-t1h` | stale on (i)+(iii) | **CLOSED** |
| `ercot-t1f` `neiso-t1f` | stale on (i)+(ii) | **CLOSED** |
| `caiso-t1f` `neiso-t3` | stale on (i)+(ii)+(iii) | **CLOSED** |
| `pjm-t1h` `nyiso-t1h` `nyiso-t1f` | stale | **PENDING Stage 2** |
| `pjm-t1f` `miso-t1f` | stale | **PENDING Stage 3** |

**RE-OPENED 2026-09-04, after this table was written:** `caiso-t1h` and `caiso-t1f`
return to stale on the keeper-vintage axis — `caiso-241` was promoted after this lane's
CAISO legs solved. See §11. `neiso-*`, `miso-*` and `ercot-*` remain CLOSED: their live
keepers are still exactly the ones their D46 legs solved against.

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
6. **GOLDEN-3 needs a pre-declared attestation.** Its FC-7 reads FAIL on that row
   alone; this lane deliberately did not author one post-hoc (§4.6). A follow-up
   that pre-declares it restores FC-7 **with no re-solve** — the campaign bundle,
   its DOF ledger and its FC-6 battery are all committed.
7. **The `-pre-d46` baselines are not all like-for-like, and the finding says which
   are.** `ercot-t1f-pre-d46` / `caiso-t1f-pre-d46` are FFR-3A-2 vintage (epoch
   2026-08-03); `neiso-t1h-pre-d46` and `neiso-t3-pre-d46` are one- and three-axis
   respectively. Any future reading of a `-pre-d46` delta should carry §4.6's
   scope caveat.
8. **CAISO's row re-opened, and every path-filtered PR now inherits a failing
   gate-(a) job** — the `caiso-241` promotion, landed after this lane's CAISO legs.
   Both halves are recorded in §11 and neither is this lane's to close.

---

## 10. Session close-out

**Stage 1 is COMPLETE and every deliverable is committed and pushed.** Eight bare
keys re-registered or minted with every prior preserved; the board refreshed;
`check_gate_a_provenance.py`, `check_forecast_staleness.py` and
`check_mechanism_matrix.py` all clean; four matrix shards stamped with no verdict
letter moved; the pre-declaration graded at full magnitude with its misses named
and one of them attributed to my own process rather than to the model.

**Stage 2 was NOT started**, and the gate was verified closed at the end of the
session rather than assumed at the start (§8). **Stage 3 was not touched.**

**One under-commit, caught at close and repaired.** GOLDEN-3's FC-6 T1.6 ladder
writes per-rung metrics to `fc6/_battery_metrics/NEISO/*.json`, and GOLDEN-2
**tracks** its equivalents — they are part of the committed FC-6 evidence, not
scratch. This lane's first pass committed the ladder's `driver-battery-*.json/.md`
and `paired_invariants.json` but missed them; both files are now committed. In the
same repair, the two new lanes got the per-lane `.gitignore` blocks the house
pattern gives every other lane (`/results/ff-t1f-d46/` on the
`/results/ff-t1f-s6-pjm/` template, and `fc6/_battery_cache_*/` alongside the
existing `fc6/arms/*/NEISO/` rule), so the 105.8 MB of per-year dispatch parquets,
screen-diagnostic `.npz`, floor-retention dumps and the ladder's disposable solve
cache are excluded by rule rather than by omission. Verified both ways: every one
of those artifacts is now ignored, and **no previously-tracked file became
ignored** — GOLDEN-2's own `_battery_metrics` included.

Every push touching a file ≥300 lines was blob-verified against the local bytes
before the next commit (rule 27): `register_forecast_run.py` at each of its five
edits, `ff-verdicts.json` at each of six, all six `run_config.json` bundles, the
GOLDEN-3 `full_horizon_summary.json`, the four mechanism-matrix shards and this
finding. No mismatch occurred.

---

## 11. Re-dispatch of 2026-09-04 — Stage 1 verified landed, the Stage-2 gate re-verified closed, one row re-opened

The D46 dispatch was **re-issued verbatim on 2026-09-04** on branch
`claude/capx-d46-remeasure-batch-ofmvb8`, fresh off `origin/main` `8d5a3e16`.
Stage 1 had already landed and merged from the first dispatch's branch
(`…-oe1h77`). **Nothing was re-solved, nothing was re-registered, nothing was
armed.** This section is the whole product of the re-dispatch.

**Why re-execution was refused, on the dispatch's own terms.** Every `-pre-d46`
key already holds its preserved baseline. Re-running Stage 1 would re-preserve
the *D46* records over those baselines, destroying them — which the dispatch's
own collision guardrail forbids outright (*"if … a key collides with an existing
suffixed record, STOP and route — never overwrite a preserved baseline"*). At an
unchanged HEAD the refresh also has nothing to add for three of the four ISOs.

**Independent verification of the landed state** — read from the artifacts, not
from §§3–8:

| check | result |
|---|---|
| bare keys → D46 records | 8/8 resolve (`neiso/miso/caiso/ercot-t1h`, `ercot/neiso/caiso-t1f`, `neiso-t3`) |
| `-pre-d46` preservations | 6/6 present, each carrying the prior determination; `caiso-t1h` / `ercot-t1h` have none, as chartered (minted keys) |
| `VERDICT_MAP` (AST) | 45 rows, **0 duplicate keys**, all 9 D46 + re-pointed rows present |
| committed artifacts | 232 tracked `d46`/`golden3` files (bundles, sidecars, hindcast reports) |
| `check_forecast_staleness.py` | **exit 0** (WARN-level only) |
| `check_mechanism_matrix.py` | **exit 0** — integrity, anchors, keeper stamps, §5.x headers |
| matrix shards | ERCOT / CAISO / MISO / NEISO each carry their own measured `fossil_announced_exits` evidence; PJM / NYISO carry the D44 stamp alone, as Stage 2 requires |

**Stage-2 gate: RE-VERIFIED CLOSED on 2026-09-04.** `FINDING-capx-d45-pjm-nyiso-curves-2026-09-03.md`
§§4, 5, 6, 7, 8 **and 9** are still literal placeholders (`[filled]`,
`[filled after L4]`, `[filled after L2/L3]`) on `origin/main` `8d5a3e16`. D45 owns
the PJM/NYISO forecast surfaces until it closes. **Stage 2 was not started;
Stage 3 was not touched.**

### 11.1 NEW and routed — `caiso-241` re-opens CAISO's row, and leaves a gate-(a) failure every path-filtered PR inherits

`a6c8db2f` (PR #4663) promoted **`2026-09-03-caiso-241-b1-ctpeaker`** *after* this
lane's CAISO legs solved against `caiso-240`. Two consequences, **neither this
lane's to close**:

1. **`check_gate_a_provenance.py` exits 1 at HEAD.** CAISO's `a_keeper_marker` in
   `frontend/data/forecast/program-status.json` still cites the superseded
   `caiso-240`. This is the **eighth** real firing of the guard. **Stated
   precisely, because the first draft of this section overstated it:** the job is
   wired into `.github/workflows/ci.yml:213` (job `forecast-staleness-warn`), and
   `ci.yml` triggers on **`pull_request` only — there is no `push:` trigger**, so
   nothing runs against `main` directly and "CI is red on main" is the wrong
   phrase. The correct one: the failure lives in `main`'s content, so **every PR
   touching one of the workflow's filtered paths (`src/`, `scripts/`, `tests/`,
   `frontend/data/{backcast,hindcast,forecast}/`, the matrix files, `CLAUDE.md`,
   `ci.yml`) inherits a failing job it did not cause**, until the stamp is
   re-keyed. This branch is not one of them — it touches only
   `docs/handoffs/`, which no filter matches, so it triggers no CI run at all.
   Not repaired here, for two independent
   reasons: this lane's charter says *never move gate (a)*, and the stamp's own
   detail records that its last two re-keys were made *"by the capx director desk
   under an owner one-push grant (capx ledger §0ac card C-2)"* — a grant this lane
   does not hold. The stamp text additionally records the standing
   **"R-T ROUTING NON-COMPLIANCE"** dispute over which lane owes the re-key; a
   silent repair from here would insert this lane into that dispute.
2. **CAISO's keeper-vintage axis re-opens.** `caiso-t1h` and `caiso-t1f` now sit
   on a superseded keeper, returning both to the §0ac.7 stale set one day after
   this lane closed them. Per the ledger's own standing clause (§0ac amendment 2:
   *"a keeper promotion in any ISO after D46's leg re-opens that ISO's row … the
   promoting lane owes the re-solve decision, this desk only records the
   staleness"*), the decision belongs to the promoting lane. **Recorded, not
   taken** — and explicitly **not** re-solved here, which would have been this
   lane taking a decision the ledger assigns elsewhere.

**The other three Stage-1 ISOs are unaffected.** Their live keepers are exactly
the ones their D46 legs solved against — ERCOT `2026-08-25-234-eastex-identity`,
MISO `2026-09-03-miso-202-unitclip`, NEISO `2026-08-17-neiso-99-joint-p1` — so
`ercot-t1h`, `miso-t1h`, `ercot-t1f`, `neiso-t1h`, `neiso-t1f` and `neiso-t3` all
remain current at HEAD.

### 11.2 Re-dispatch close-out

No solve ran, no key moved, no baseline was touched, no matrix verdict moved, and
gate (a) was not moved. The re-dispatch's deliverable is this section: Stage 1
verified landed, the Stage-2 gate re-verified closed **at the time of reading
rather than assumed**, and one newly re-opened row routed to the director with its
CI consequence named precisely (§11.1: inherited by path-filtered PRs, not a
`main` run — the first draft of that line was corrected before this one). **Stage 2 still awaits the director's re-release**, which
D45's close-out gates.
