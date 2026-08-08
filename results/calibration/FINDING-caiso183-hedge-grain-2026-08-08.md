# FINDING — caiso-183: the H-EDGE grain repair is **BUILT, PROVEN BYTE-INERT FOR FIVE ISOs, AND MEASURED**. After it the model asserts **ZERO** in-window hours its own CEMS contradicts — down from 3.36 / 3.25 / 3.55 %. One pre-registered gate, **G-DEPTH′, FAILS in 2023** and is reported at full magnitude

<!-- RESULTS SECTION APPENDED AFTER THE ARMS SOLVED; PHASE 0 IS AS WRITTEN BEFORE. -->

**Pre-registration:** `PRECHECK-caiso183-hedge-grain-2026-08-08.md`, pushed and
blob-verified (358 lines, blob `e7db168d…`, remote SHA identical to local)
**before the repair was written and before any scored metric existed**.

Keeper at session start **`2026-08-06-caiso-175-tac-intake`** (**NOT-YET**, rubric
v3.1, 8 criteria, **C3a the sole FAIL**). DOF ledger **11 / 8**. `complete` **NOT
held**. 2023 + 2024 + 2025 only, one bundle per arm.
`calibration-complete.json` and `holdout-freeze.json` **UNTOUCHED** (owner acts).

Instruments: `scripts/probes/_caiso183_hedge_grain.py`,
`_caiso183_loader_snapshot.py`, `_caiso183_arm_identity.py` (a thin driver over the
**reused** `_caiso180_arm_identity`), and the **grain-aware**
`_caiso181_cems_confrontation.py`. Records: `_caiso183_hedge_grain.json`,
`_caiso183_gcontract.json`, `_caiso183_loader_p03.json`, `_caiso183_sha_ledger.json`,
`_caiso183_arm_identity.json`.

---

## 1. THE OBJECT, AND WHY IT IS NOT THE SETTLED DEPTH QUESTION

caiso-181 established that CAISO's outage envelope is **depth-correct** — interior
CEMS contradiction is **exactly zero** across 599,736 interior in-window hours — and
that **100 %** of the contradictions it did find are **edge**, every one within
**22 h (< 24)** of a window boundary. It named the cause, sized it, and deliberately
did **not** repair it (§5 open item 1: *"needs its own charter, precommit and
gates"*). This is that charter, and it touches a different object:

* the **detector** is untouched — no window is added, removed, re-dated or moved;
* what changes is the **CSV round-trip**. The deriver detects in **hours**
  (`start = clock[s]`, `last = clock[e-1]`) and wrote `strftime("%Y-%m-%d")`; the
  loader re-expanded `outage_start` 00:00 → `outage_end` 23:00. Up to **23 h at each
  edge** were asserted unavailable that the detector never detected — exactly where
  the event-based contract guarantees the neighbouring hour was **running**.

**Measured, this session: the mean edge over-derate is 22.54 h per window** — under
the 24 h structural ceiling and squarely inside caiso-181's independently-measured
≤ 23 h / max-22 h bound.

## 2. THE REPAIR — zero DOF, and byte-inert for every ISO that does not opt in

Optional `outage_start_hour` / `outage_end_hour` carried through
deriver → schema → curate → loader:

* **Writer** — `derive_campd_unit_outages.py --hour-grain`, **default off**. The
  hours are taken from the *same* `start` / `last` objects the day strings are
  formatted from, so the two grains cannot disagree; without the flag the keys are
  simply not selected into `cols`.
* **Loader** — `outages.unit_outage_event_window` consumes them when present and
  falls back when absent. **The fallback is the incumbent behaviour by identity, not
  approximation:** an absent grain is exactly `start_hour = 0` / `end_hour = 23`, and
  `+(23+1) h ≡ +1 day`. A null hour falls back per row.
* **Schema** — both columns `nullable: true`, so a day-grain ISO's clean partition
  still validates against a closed schema.

**Zero DOF. Zero new fitted scalars. No threshold re-valued.** The change is a grain
carriage, not a mechanism, so no `ScenarioConfig` field is added (rule 28 duty (c) is
not engaged).

## 3. PHASE 0 — every byte-equivalence obligation, measured

| leg | bar | result |
|---|---|---|
| **BE-1** | unmodified deriver reproduces every committed extract | **4 / 6 byte-identical**; MISO and NEISO differ, both pre-existing and fully attributed (§3a) |
| **BE-2 / G-SIXISO** | code present + flag absent ⇒ each extract sha256-identical to its own BE-1 output | **PASS, all six** |
| **BE-3** | CAISO detection unchanged | **PASS** — 4,328 rows, same `(plant, unit, start-day, end-day)` tuples, same order; 547 / 458 / 635 windows per year, matching caiso-180's A0 census exactly |
| **P0-3** | day-grain loader mask bit-identical to pre-change | **PASS** — 24 (ISO, year) digests identical on **both** consumer legs, against a snapshot taken **before** the change |
| **G-NOFIT** | frozen detector constants unmoved | **PASS** — `_MIN_DAYS` 5, `_SMOOTH_DAYS` 7, `_CEILING_FRAC` 0.65, `_RUN_FLOOR_CF` 0.06, `_BASELOAD_CF` 0.55, `ST_GAS_CF_PEAK` 0.02 |

**Exactly one data file changed: `data/raw/campd-unit-outages-CAISO.csv`**
(`c4ded33d…` → `25360e90…`). The other five extracts and every layup companion are
untouched on disk.

### 3a. TWO pre-existing BE-1 mismatches — one disclosed in advance, one NOT

**MISO reproduces xiso-2 §4 exactly**: **+17 windows, 0 lost**, all **2022 COAL**,
layup companion byte-identical. Disclosed in PRECHECK §4a before measurement.

**NEISO was NOT disclosed and is a new finding.** xiso-2 recorded NEISO as
byte-identical on 2026-08-02; at this head it is not:

| | committed | re-derived |
|---|---:|---:|
| kept windows | 3,189 | 3,168 |
| layup windows | 1,294 | 1,315 |
| **detected union** | **4,483** | **4,483** |

**21 windows moved kept → layup; the DETECTED set is IDENTICAL — zero gained, zero
lost.** All 21 land in the re-derived layup companion, so this is the **merit-order
guard's classification** moving under a changed delivered-fuel input (the guard
prices measured SRMC = CAMPD heat rate × delivered fuel price), **not** detector
drift and **not** a CEMS change. The affected years are 2019 (2), 2020 (4) and
2026 (15) — **none in 2023–2025**.

**Both ISOs are training-clean**: the 2023–2025 slice is byte-identical row-for-row
(NEISO 981 rows each side, MISO 3,659). **No keeper is affected, no extract is
rewritten here, and neither is this session's object** (rule 25 `[R-ISO-SCOPE]`).
Filed for the NEISO lane.

**This is why G-SIXISO binds on the self-comparison** (`be2 == be1`) rather than on
the committed file: that is the only comparison that isolates *this* change, and
PRECHECK §4a fixed that form before any of it was measured.

## 4. G-CONTRACT — the repair removes exactly the hours it was supposed to

caiso-181's confrontation instrument, re-run on the repaired envelope (made
grain-aware so it keeps mirroring the loader it was built to mirror). The
before-run at this head reproduces caiso-181 exactly, which is a clean positive
control on the instrument.

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| windows scored (before / after) | 545 / **545** | 456 / **456** | 603 / **603** |
| in-window hours contradicted by CEMS, **before** | 3.358 % | 3.248 % | 3.550 % |
| in-window hours contradicted by CEMS, **after** | **0.000000** | **0.000000** | **0.000000** |
| **interior** contradiction, after | **0** | **0** | **0** |
| contradicted CEMS energy (MW-h) | 762,479 → **185** | 927,356 → **182** | 1,263,185 → **299** |
| L2 impossible share of depth | 3.68 % → **2.00 %** | 4.00 % → **2.22 %** | 3.32 % → **1.38 %** |

**After the repair the model asserts ZERO in-window hours that the unit's own CEMS
contradicts.** The detector's contract now holds exactly as written, at hour grain,
and it holds while the window count is unchanged — so nothing was removed from
*detection*; only un-detected edge hours stopped being asserted.

**It lands where caiso-181 predicted.** That session decomposed L2 into a **basis**
term (1.26 / 1.62 / 0.75 pp, un-representable by any envelope) and an
**envelope-excess** term (2.42 / 2.38 / 2.57 pp), of which it measured
**74.2 / 79.6 / 80.8 %** as edge-day. Post-repair the envelope-excess term falls to
≈ 0.74 / 0.60 / 0.63 pp — a **69 / 75 / 75 %** reduction against a predicted
**74 / 80 / 81 %**. Slightly under prediction, reported as measured.

## 5. G-DEPTH′ **FAILS in 2023** — reported at full magnitude, and the bar is NOT moved

| M MW-h | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| day-grain depth (A0) | 36.680 | 42.880 | 55.430 |
| hour-grain depth (repaired) | 34.836 | 41.042 | 52.955 |
| **removed by the repair** | **1.844** | 1.839 | 2.475 |
| removed, share of depth | 5.03 % | 4.29 % | 4.46 % |
| **G-DEPTH′ allowance** `|A0 − A1|` | **1.346** | 4.077 | 5.442 |
| **G-DEPTH′** | **FAIL** | PASS | PASS |
| G-DEPTH literal floor (A1) | 38.03 | 38.80 | 49.99 |
| G-DEPTH literal | FAIL | PASS | PASS |
| — same floor, *unrepaired* baseline | **FAIL (36.68 < 38.03)** | PASS | PASS |

**The gate fired and it is reported as a FAIL. No bar was moved, no allowance was
widened, and the arm is not promoted on this session's authority.**

Two things must be said about it, and both were written down **before** the
measurement:

1. **PRECHECK §6a recorded that the literal floor's 2023 leg is already breached by
   the UNREPAIRED keeper** (A0 36.68 < A1 38.03), because the 2026-07-24 regeneration
   *removed* 1.35 M MW-h of depth that year. A gate premised on the regeneration
   having *added* depth has no well-defined 2023 leg.
2. That defect propagates into the delta form I nonetheless pre-registered as
   binding: its allowance is `|A0 − A1|`, which in 2023 is the size of a depth
   *reduction*.

**The gate's stated purpose is to catch a revert in disguise, and the arithmetic
falsifies it as a revert-detector here:** a revert moves depth **toward** the
superseded A1 envelope (38.03); this repair moves it **away** (36.68 → 34.84,
*further below* A1). Independently, **BE-3 proves the window set is identical**, so
the stale envelope's shape — fewer, longer windows — is nowhere reintroduced. On its
own terms the gate cannot be detecting what it exists to detect.

**I am not adjudicating my own gate.** The withdrawal of G-DEPTH′'s 2023 leg is
**proposed with its falsification and routed to the owner**, exactly as caiso-180's
§3a leg-2 was recorded (and that leg stays withdrawn and is not reinstated here).
This is the **second** time a caiso-18x depth-ordering gate has been malformed for
the same underlying reason — 2023 is the year the regeneration *reduced* depth — and
that recurrence is itself the reportable pattern.

**Why the 5.03 % removal is larger than caiso-181's 2.42 % envelope-excess is not an
anomaly, and it is not over-removal.** Contradiction is only *observable* where the
unit happened to run in the edge hour; the over-derate exists at every edge
regardless. The measured contradiction is therefore a **lower bound** on the seam,
and the repair removes the seam, not the bound. The removal is bounded above by
construction: the monotone-subset invariant is asserted per row inside the deriver,
so the repaired window is always a subset of the day-granular one, and **no hour the
detector detected can ever be removed**.

## 6. Instrument note — a solve-cache confound that would have voided the ladder

`runner.py` short-circuits on `is_cached(iso, cache_key, year)`, and `cache_key`
hashes `ScenarioConfig` **only** — the outage extract's bytes are not in it. B0 and
B1 share a recipe, so a second arm run in the same tree would have **silently loaded
the first arm's parquet** and read as a perfect no-op. The cache is purged between
arms, and `_caiso183_arm_identity.check_arms_distinct` asserts the two arms produced
different hourly signatures rather than trusting that the purge happened.
