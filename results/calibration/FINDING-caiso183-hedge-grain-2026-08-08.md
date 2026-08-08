# FINDING — caiso-183: the H-EDGE grain repair is **BUILT, PROVEN BYTE-INERT FOR FIVE ISOs, AND MEASURED**. After it the model asserts **ZERO** in-window hours its own CEMS contradicts — down from 3.36 / 3.25 / 3.55 % — and C3a narrows in **all three years**. **TWO pre-registered gates FAIL — and the arm is PROMOTED on the owner's ruling**

> **PROMOTION ADDENDUM (2026-08-08, after the body below was written).** The owner
> ruled: *"if structural integrity improves but gates regress that may still be a
> keeper."* That adjudicates exactly the question §5 and §7d routed to them.
> **`2026-08-08-caiso-183-b1-hour` is now the designated CAISO keeper**, the repaired
> hour-grain extract is **ADOPTED** into `data/raw/`, and a governance attestation was
> generated for the arm (`scripts/gen_caiso183_attestation.py`, four fail-closed legs)
> so **C6 now reads PASS** and C3c returns to its inherited **ledgered CAVEAT**.
> Determination is **NOT-YET**, C3a still the sole FAIL. **Nothing in §§1–9 below was
> rewritten to suit the promotion** — the two gate failures stand at full magnitude and
> neither bar was moved; what changed is who adjudicated them. §8's "not adopted"
> disposition is **superseded by this addendum**, not retracted: it records what this
> session was willing to do on its own authority.

**Outcome: the repair is CORRECT, MEASURED, and — on the owner's ruling — PROMOTED.** C3a moves
+4.2 → **+3.9 %**, +11.5 → **+10.9 %**, +14.7 → **+13.9 %** — the pre-registered
direction prediction **confirmed**, well clear of the measured noise floor — but
**2024 and 2025 remain FAIL, the determination stays NOT-YET, and the residual does
NOT close.** Two gates I pre-registered myself, **G-DEPTH′** and **G-CAISO180**, fired;
both are reported at full magnitude, **neither bar was moved**, and I am **not
adjudicating my own gates**. Adoption is an owner decision.

Keeper **`2026-08-08-caiso-183-b1-hour`** (was `2026-08-06-caiso-175-tac-intake`).
DOF ledger **UNCHANGED at 11 / 8** on both arms. No `ScenarioConfig` field added,
removed or re-valued. No frozen identification constant touched.
**`data/raw/campd-unit-outages-CAISO.csv` is ADOPTED at the hour grain**
(`25360e90…`, §8 addendum).

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

**Exactly one data file was re-derived: `data/raw/campd-unit-outages-CAISO.csv`**
(`c4ded33d…` → `25360e90…`). The other five extracts and every layup companion were
untouched. **It is restored to the committed day-grain at session end and is NOT
adopted** — see §8.

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


---

## 7. THE ARMS — control exact, treated narrows C3a in all three years, residual does NOT close

**Two arms, one delta, solved sequentially at one head** (rule 12), each 2023 + 2024 +
2025 in **one** bundle (rule 16), both registered (rule 15):
`2026-08-08-caiso-183-b0-control` and `2026-08-08-caiso-183-b1-hour`.

### 7a. CONTROL — reproduces the keeper to the cent, but is NOT bit-zero

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| keeper λ (load-weighted) | 56.4476819404 | 38.6313726293 | 39.4624179310 |
| control λ | 56.4450007364 | 38.6290053930 | 39.4624179310 |
| **drift** | **−0.0027** | **−0.0024** | **0.0000** |
| drift, % of level | −0.0048 % | −0.0061 % | 0.0000 % |
| zone-hours differing | 5,012 / 61,320 | 2,465 / 61,320 | **0** |
| max \|Δprice\|, any zone | $81.01 | $125.57 | 0 |
| max \|Δprice\|, **load-carrying** zones | $2.30 | $2.28 | 0 |

**CONTROL PASSES as pre-registered** — scored C3a is identical to the keeper's
(+4.2 % / +11.5 % / +14.7 %, level 56.45 / 38.63 / 39.46).

**But it is not bit-zero, and that qualifies a claim two prior sessions made.** The
large deltas sit **entirely on `WECC_PNW` / `WECC_DSW`, the two WECC import nodes,
which carry ZERO CAISO demand** and so contribute nothing to the load-weighted mean;
the signature is adjacent-hour price swaps at an import node, i.e. **LP alternate
optima under degeneracy**, not a model change. caiso-180's and caiso-181's *"exactly
$0.000"* was measured at **scored** precision, which cannot see sub-cent churn;
measured hour-by-hour at full precision it is $0.000 only in 2025. **This is reported
as a correction to the record, and it is what makes the treated arm readable: the
same-head noise floor is ≤ 0.006 % of level, so any move above ~0.01 % is signal.**

### 7b. TREATED — the direction prediction is CONFIRMED, and the residual still does not close

| | actual | B0 control | B1 hour-grain | Δ$ | C3a B0 → B1 |
|---|---:|---:|---:|---:|---|
| 2023 | 54.17 | 56.45 | **56.30** | −0.15 | +4.2 % → **+3.9 %** PASS |
| 2024 | 34.65 | 38.63 | **38.44** | −0.19 | +11.5 % → **+10.9 %** **FAIL** |
| 2025 | 34.42 | 39.46 | **39.20** | −0.26 | +14.7 % → **+13.9 %** **FAIL** |

The move is **−0.3 / −0.6 / −0.8 pp**, i.e. **50–130×** the same-head noise floor —
signal, not churn. **PRECHECK §5's prediction was that the repair adds capability and
therefore lowers price. It is CONFIRMED in all three years**, including 2023 where I
allowed it might widen.

**AND IT DOES NOT CLOSE THE RESIDUAL. 2024 and 2025 remain FAIL against the ±10 %
band, C3a remains the sole load-bearing failure, and the determination stays
NOT-YET on both arms.** The repair takes roughly **one-seventh** of the 2024 excess and
**one-sixth** of the 2025 excess. Saying so is the point: the honest remaining named
contributor is the **WALLED hourly pumped-storage water state**
(`FINDING-caiso140` §B / caiso-141 A2), an **owner-funded intake decision, not a
session lever**. No close is manufactured here.

**The mechanism is coherent end to end.** Freeing wrongly-derated CC capability lets
cheap CC displace expensive peakers and imports:

| TWh, B1 − B0 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| CC_REGULAR | **+0.195** | +0.172 | +0.253 |
| CC_CHP | +0.055 | +0.069 | +0.054 |
| CT_PEAKER | **−0.118** | −0.052 | −0.071 |
| ST_GAS | −0.043 | −0.091 | −0.054 |
| import | −0.091 | −0.098 | −0.200 |
| nuclear / wind / solar / biomass | ~0 | ~0 | ~0 |

### 7c. Gate tally

| gate | verdict |
|---|---|
| **G-DOF** | **PASS** — 11 / 8 on both arms |
| **G-NOFIT** | **PASS** |
| **G-SIXISO** | **PASS** |
| **G-CONTRACT** | **PASS**, decisively (§4) |
| **G-C1** | **PASS** — C1 all 12/12, free 8/8, both arms |
| **G-PROT** | C8 **PASS and SCORED** (`legitimacy_diagnostics.json` registered with both bundles). **C6 reads `UNATTESTED` on both arms** — a probe-arm artifact (neither carries a `calibration_attestation.json`; the keeper's ledger exceptions live in its own bundle), identical across arms and therefore discriminating nothing. Stated so it is not misread as an envelope effect, exactly as caiso-180 §5a stated it. |
| **G-LOYO** | **not reached** — no verdict flipped (both arms NOT-YET), so there is nothing to score leave-one-year-out |
| **CONTROL** | **PASS** to the cent (§7a) |
| **G-DEPTH′** | **FAIL in 2023** (§5) |
| **G-CAISO180** | **FAIL**, 5 of 9 banded cells (§7d) |

### 7d. G-CAISO180 **FAILS** — reported at full magnitude, bar NOT moved

The band is *"|ΔTWh| must not exceed the FULL regeneration leg it reverses"*:

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC_REGULAR | **+0.195 vs 0.11 — FAIL** | +0.172 vs 0.44 PASS | +0.253 vs 0.67 PASS |
| ST_GAS | **−0.043 vs 0.03 — FAIL** | −0.091 vs 0.13 PASS | −0.054 vs 0.07 PASS |
| CT_PEAKER | **−0.118 vs 0.02 — FAIL** | **−0.052 vs 0.04 — FAIL** | **−0.071 vs 0.06 — FAIL** |

**Five of nine cells breach. The gate fired and the bar is not moved.**

**G-CAISO180 and G-DEPTH′ fail for ONE shared reason, and it is a defect in how I
built them, not a defect the gates detected.** Both bound the repair's footprint by
**the caiso-180 regeneration leg's** footprint, which presumes the repair is the
regeneration's *inverse*. It is not, and **BE-3 proves it**: the window set is
identical to the regenerated one, so the repair strips edge hours from **every**
window — including all the windows that pre-date the regeneration — and its footprint
has no reason to sit inside the regeneration's. CT_PEAKER is the clearest case: its
band is 0.02–0.06 TWh only because the *regeneration* barely moved peakers, whereas
freeing CC capability across ~1,640 windows displaces them by more.

**I am not withdrawing either gate on my own authority.** I designed both, both fired,
and a session does not get to retire its own bar after seeing the number. The
falsifying arithmetic is recorded (§5 for G-DEPTH′, here for G-CAISO180) and **routed
to the owner**, exactly as caiso-180's §3a leg-2 withdrawal was recorded — and that
leg stays withdrawn and is **not** reinstated here. **This is the second and third
time a caiso-18x gate keyed to the caiso-180 regeneration leg has proved malformed;
the recurrence is itself the reportable pattern.**

## 8. DISPOSITION — as this session left it, then superseded by the owner's ruling

> **SUPERSEDED, NOT RETRACTED.** Everything in this section is what the session was
> willing to do **on its own authority**, and it is preserved verbatim because that is
> the honest record. The owner's ruling of 2026-08-08 — *structural integrity improving
> while gates regress may still be a keeper* — supplied the adjudication, so the arm
> **was** promoted and the extract **was** adopted. The final state is the addendum at
> the top of this document.

**NO PROMOTION ON THIS SESSION'S AUTHORITY. The keeper is UNCHANGED.** Two pre-registered gates failed; C3a was
never an admissible promotion basis (rule 1 — it is a live FAIL; rule 13 — nothing was
tuned to it), and the admissible basis (*the model no longer asserts unavailability its
own detector never detected*, now proven at 100 % by G-CONTRACT) does not override a
fired gate.

**`data/raw/campd-unit-outages-CAISO.csv` is left at the committed day-grain
`c4ded33d…`.** That path is what the **loader** reads, so committing the repaired
extract would silently change what the designated keeper reproduces **without a
promotion**. The extract is deterministically regenerable, byte-identically, from one
command:

```
python scripts/data/derive_campd_unit_outages.py --iso CAISO \
    --years 2018 2019 2020 2021 2022 2023 2024 2025 2026 \
    --merit-order-guard --hour-grain
```
→ sha256 `25360e90a9d11f32c293edf3224047da0d6fab447b551fac81b983e2da1166c6`.

**Flagged for the owner, against my own conservatism:** rule 14 `[R-ACCURATE]` and
rule 1 `[R-STRUCT]` both point toward adopting the repaired extract — it is strictly
the more faithful representation (CEMS contradiction 3.4 % → 0), it is zero-DOF, and
its fit effect is *favourable* rather than the "worse fit" those rules exist to
protect. **I am not making that call because two of my own gates fired on it.** The
decision is one command wide either way.

**The code is committed and is byte-inert by default**, so nothing changes for any ISO
until an extract is re-derived with `--hour-grain`. The other five ISOs enter as
**untested** for hour-grain adoption (rule 28 duty d); their magnitudes are unmeasured
and no verdict transfers (rule 25).

## 9. Known-open, carried forward

1. **NEISO's undisclosed BE-1 drift** (§3a) — 21 windows kept → layup under a changed
   delivered-fuel input, detected union identical, training-clean. NEISO lane, not
   repaired here.
2. **G-DEPTH′ and G-CAISO180 withdrawal** — routed to the owner with the falsifying
   arithmetic (§5, §7d).
3. **Adoption of the repaired CAISO extract** — owner decision (§8).
4. **C3a's residual after the repair** — 2024 +10.9 %, 2025 +13.9 %. First named
   contributor remains the **WALLED hourly pumped-storage water state**
   (`FINDING-caiso140` §B / caiso-141 A2), an owner-funded intake.
5. **Same-head control is not bit-zero in 2023/2024** (§7a) — WECC import-node
   alternate optima. Corrects the record for caiso-180/181.
