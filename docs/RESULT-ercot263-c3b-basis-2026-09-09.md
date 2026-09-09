# RESULT — ercot-263: ERCOT's 2021 C3b failure was measured against a deprecated benchmark basis

**Session:** ercot-263, 2026-09-09. Branch `claude/ercot-c3b-closure-uon654`.
**Base:** `74671cca` (origin/main at session start). **PRECOMMIT:** `3964ff00`,
`docs/handoffs/PRECOMMIT-ercot263-c3b-basis-2026-09-09.md` — predictions sealed before the repair.
**Scope:** DATA + BENCHMARK + DOCS. **Zero LP solved. No `ScenarioConfig` field changed. The
keeper's payload is byte-identical. No `src/` or `scripts/` file edited.**

---

## Headline

ERCOT 2021 and 2022 were being scored with a **load-weighted model against an equal-hour actual** —
the basis the owner deprecated in July 2026 (rubric v2.4). `derive_actual_lmp.py --lw-retrofit`
had simply never been run for those two years. Repaired.

**The number moved the wrong way, and it stays.** On the like-for-like basis the training years
already use, **C3b 2021 is 0.559, not 0.238.** The gate is 0.20, so ERCOT's five-year determination
is **further** from closing than the handoff's brief assumed — not 0.038 away, but 0.359 away.

**ERCOT's headline determination does not change.** The train tier {2023, 2024, 2025} is
byte-identical, still carries no failure, and the ISO still reads **CALIBRATED** under rule 30(c).
The run-level determination stays **NOT-YET on `price_shape` alone.** No criterion status changed.

**The 2021 object is now singular and it is not October.** February (Winter Storm Uri) carries
**95.7%** of the 2021 C3b SSE.

## 1. Phase 0 killed the handoff's construction before an LP was spent

The handoff directed October first: *"OCTOBER (+140.3%) is the outlier and the obvious first
object."* That ranks months by **percentage** bias; C3b is an **absolute-dollar** NRMSE over 12
monthly points. On the keeper's committed payload, **February carried 58.5% of the SSE against
October's 25.4%** — and **zeroing October outright still left 0.2055 > 0.20, still FAIL.** The
recommended object could not close the gate under any outcome.

Asking why February's error was large is what found the defect: `score_price_shape` labelled the
2021 actual **"LEGACY equal-hour basis"**, while 2023–2025 read **"load-weighted actual"**.

## 2. The defect

`score_price_shape` / `score_price_mean` pick the actual through a ladder:
`rt_lw_mon` → `da_lw_mon` → `rt_mon` (the labelled legacy fallback). The **model** side is always
load-weighted. Committed `actual_lmp.json`, ERCOT:

| 2018 | 2019 | 2020 | **2021** | **2022** | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| legacy | LW | LW | **legacy** | **legacy** | LW | LW | LW |

**ERCOT was the only ISO with an interior hole in that field.** Every other ISO's legacy years are a
contiguous prefix, where the source genuinely stops; ERCOT had LW on *both sides* of the gap.

**It was never a data gap.** Both years' inputs are committed and complete, and identical in shape
to 2023–2025: `actual_lmp_hourly_ERCOT.parquet` 8,760 h / 0 NaN; `actual_lmp_zonal_ERCOT.parquet`
131,385 rows / 15 settlement points / 0 NaN. The retrofit was run on ERCOT for {2019, 2020} in one
pass and {2023, 2024, 2025} in another; **2021 and 2022 fell between the two passes.**

The rubric's own v2.4 amendment names the defect and predicts exactly where it bites hardest
(`calibration_verdict.py` header):

> *"C3a/C3b score on the LIKE-FOR-LIKE load-weighted actual … instead of the legacy equal-hour hub
> mean. **The legacy basis mixed a demand-weighted model mean with an equal-hour actual, a wedge
> that grows with tail realism** — a byte-perfect ERCOT 2023 model scores +33.5% against its own
> actual on the old basis."*

2021 is ERCOT's most tail-heavy year on record. It is the worst case of a wedge the owner
deprecated 14 months ago, left in place by an unexecuted retrofit pass.

## 3. The repair

`python3 scripts/data/derive_actual_lmp.py --lw-retrofit --isos ERCOT --years 2021 2022`, then the
committed `write_bench_part` writer over the two affected bench parts.

- **Zero free parameters** (rule 21 `[R-DOF]`). No multiplier, adder, offset or haircut; nothing swept.
- **Rule 14 `[R-ACCURATE]` + rule 22** — data applies to every year or it is not an input.
- **Blind to the model** (rule 13 `[R-MEASURED]`): `lw_retrofit` reads only measured prices and
  measured demand. It cannot see the residual it moves.
- **Rule 22 spend:** ERCOT holds the `complete` marker (2026-08-31); the holdout freeze scopes to
  `locked_test` alone. 2019 and H1-2026 are untouched.

**Verification the repair is faithful, not hand-made.** `_actual_avg_lmp` reproduces the committed
`avgLMP` block **exactly** for 2023, 2024 and 2025, and a full write round-trip leaves those three
parts **byte-identical** (sha unchanged). For 2021/2022 the diff is **four keys ADDED**
(`rt_lw`, `rt_lw_mon`, `da_lw`, `da_lw_mon`) — nothing changed, nothing removed; the legacy fields
are still there. `check_bench_freshness --iso ERCOT`: **0 STALE.**

## 4. Scored result — before → after, reported at full magnitude

| criterion | year | before (legacy basis) | after (like-for-like) | status |
|---|---|---|---|---|
| **C3b** price_shape | **2021** | 0.238 FAIL | **0.559 FAIL** | **worse** |
| C3b | 2022 | 0.099 PASS | **0.172 PASS** | worse, still passes |
| C3b | 2023 / 2024 / 2025 | 0.097 / 0.122 / 0.106 | **unchanged** | byte-identical |
| **C3a** price_mean | **2021** | +4.2% PASS | **−6.7% PASS** | **sign flip** |
| C3a | 2022 | +9.8% PASS | **−8.1% PASS** | **sign flip** (was 0.2 pts from FAIL) |
| C3a | 2023 / 2024 / 2025 | −6.5% / −0.3% / −6.8% | **unchanged** | byte-identical |

C1, C2, C4, C6, C8 all PASS, unchanged. C3c remains the single ledgered caveat.
**Determination: NOT-YET on `price_shape` alone — unchanged in kind.** No non-target load-bearing
criterion flipped PASS → FAIL (PRECOMMIT P6 satisfied). `audit_keepers --iso ERCOT`: all checks
passed. `build_status --iso ERCOT`: **CALIBRATED**.

Note the C3a sign flips. The model was believed to be running **4.2% rich** in 2021 and **9.8% rich**
in 2022; it is in fact **6.7% and 8.1% cheap**. That inverts the qualitative story of both years,
and 2022 was sitting 0.2 points inside the ±10% FAIL boundary on a basis that was overstating it.

## 5. Sealed predictions — scored

| | prediction | outcome |
|---|---|---|
| **P1** | retrofit yields non-null `rt_lw_mon` for both years, `src_lw` identical to 2023–25 | ✅ **CONFIRMED** (string-identical) |
| **P2** | Feb 2021 LW actual **higher** than $1,521.84, so the model's miss gets **worse** | ✅ **CONFIRMED** — $1,767.07 (+16.1%); error −$99.71 → **−$344.94** |
| **P3** | every other month's actual rises, shrinking the model's positive bias | ✅ **CONFIRMED** (+5.0% to +17.4% across all eleven) |
| **P4** | net direction on C3b 2021 unknown ex ante | ✅ **resolved against the session** — P2 dominates; 0.238 → 0.559 |
| **P5** | the repair stays whichever way it moves | ✅ **HONOURED** — kept, reported at full magnitude, no offsetting mechanism sought |
| **P6** | 2023–25 byte-identical; 2022 moves; a non-target PASS→FAIL flip is a STOP | ✅ **CONFIRMED**, no flip occurred |
| **P7** | a basis repair is not a market mechanism and won't be presented as one | ✅ **HONOURED** |

P2 was written knowing it cut against the session's own goal. It was right, and it decided the outcome.

## 6. The object for the next lane — February 2021, and nothing else

2021 C3b decomposed on the **corrected** basis:

| month | model | actual | err $ | err % | **SSE share** | NRMSE if exact |
|---|---:|---:|---:|---:|---:|---:|
| **Feb** | **1422.13** | **1767.07** | **−344.94** | **−19.5%** | **95.7%** | **0.1156** |
| Oct | 112.62 | 52.31 | +60.31 | +115.3% | 2.9% | 0.5511 |
| Jun | 67.73 | 44.22 | +23.51 | +53.2% | 0.4% | 0.5581 |
| Jul | 63.00 | 40.73 | +22.27 | +54.7% | 0.4% | 0.5582 |
| Aug | 55.79 | 38.10 | +17.69 | +46.4% | 0.3% | 0.5586 |
| the other seven | | | | +11.6% … +23.0% | **0.2% combined** | — |

**Making February exact scores 0.1156 — a clean PASS with room to spare. Every other month in 2021
combined is 4.3% of the SSE.** October, the handoff's recommended object, is **2.9%**; zeroing it
moves 0.5593 → 0.5511.

So the lane's question is now one question: **why is the model's Winter Storm Uri February 19.5%
too cheap?** That is a scarcity-formation question in the ERCOT week where load shed, gas
curtailment and the $9,000 cap all bind at once — adjacent to the C3c ledgered model-class
limitation, though C3b is `TIER_LOAD` and can never be caveated. **Do not open it with an offer-band
scale:** ercot-262 measured that channel at ~0.5% of price per 1% of band and ±0.004 on C3b, and a
level shift cannot move one month by −$345 without wrecking the other eleven.

**What this session does NOT claim.** The repair is a benchmark correction, not a market mechanism,
and it closes nothing. It makes the target harder and it makes it **correctly measured** — which is
the precondition for any mechanism work on 2021 being meaningful at all. Every arm ercot-262 and
earlier sessions screened against 2021 C3b was screened against a number that was wrong by 0.32.

## 6b. Characterizing February — the miss is an ONSET miss as much as a depth miss (zero LP)

From the keeper's committed `hourly/system_2021.parquet` (P1) against the committed hourly actual,
February's load-weighted error decomposes by event phase:

| band | hours | contribution to the Feb mean error | share |
|---|---:|---:|---:|
| Feb 1–10 (pre-event) | 240 | +$0.07 | 0.0% |
| **Feb 11–14 (ONSET)** | 96 | **−$179.00** | **52.6%** |
| **Feb 15–19 (deep event)** | 120 | **−$156.07** | **45.9%** |
| Feb 20–28 (post) | 216 | +$5.09 | 1.5% |

*(Total −$329.91 against the scorer's −$344.94; the residual is the zone-resolved LZ actual the
scorer uses versus the system-hub hourly series used here. It does not move the shares.)*

**The model's storm starts about two days late.** Daily counts of hours above $1,000/MWh:

| Feb | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| model | 0 | 0 | **1** | **6** | 22 | 24 | 24 | 24 | 9 |
| actual | 4 | 2 | **23** | **19** | 24 | 24 | 24 | 24 | 9 |
| day err $ | −312 | −173 | **−1,663** | **−1,314** | −1,209 | −1,074 | −855 | −461 | +66 |

Once the event is fully joined the model tracks it well — Feb 15–18 reach $5,556 / $7,896 / $8,147 /
$8,528 against $6,765 / $8,970 / $9,002 / $8,989, and Feb 19 is **+$66 over**. **The 52.6% that sits
in Feb 11–14 is a timing failure, not a ceiling failure**: on Feb 13 the market was scarce for 23 of
24 hours and the model was scarce for one.

Two secondary facts for whoever takes it: the model spends **38 hours at/above $9,000 against the
actual's 83**, and its dual peaks at **$10,771** — above ERCOT's $9,000 HCAP, which an energy-only
LP dual is free to exceed. So the tail is *mistimed and under-held*, not under-priced at its peak.

**This is a hypothesis about where to look, not a diagnosis.** It was measured from committed
artifacts with no solve, and it names no mechanism.

## 7. Governance

- **Rule 29 `[R-SCREEN]`:** phase 0 first; it killed the handoff's construction at zero LP cost, so
  no screen and no full span were spent. **G-DRIFT not engaged — no solve.**
- **Rule 31 `[R-RETAIN]`:** no bundle produced, nothing deleted.
- **Rule 28:** ERCOT matrix shard + §5.1 prose header re-stamped to the current keeper (a duty the
  ercot-261 promotion left owed). **No cell moved — no mechanism was tested.**
- **Historical text annotated, not rewritten:** the ercot-261 determination sentences in
  `keepers/ERCOT.json` and `calibration-complete.json` carry a `[BASIS-CORRECTED 2026-09-09]` clause.
  Those numbers were accurate on the basis they were measured on; what changed is the basis.

**PRE-EXISTING RED, NOT THIS LANE'S AND NOT FIXED HERE.**
`check_registry_payload_parity` fails on five committed bundle dirs — `results/calibration/ercot262_arm_{2021..2025}`
(79 tracked files, on `main` via ercot-262's shard commits `197f0b1f` and siblings). They are
rule-29(c) screen bundles that reached `main` instead of being kept out of it. **Rule 31
`[R-RETAIN]` forbids this session deleting them**: the owner has not ruled on ercot-262's promotion
question, and destroying a solved bundle ahead of that ruling is precisely the ercot-255 incident
rule 31 exists to prevent. **This branch touches no bundle directory** and does not make the RED
worse. It needs an owner decision on ercot-262 (promote → register; decline → then prune).
