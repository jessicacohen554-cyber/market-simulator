# PRE-REGISTRATION — caiso-152: the `dam-public-bids` RLE parse defect

**Written and committed BEFORE any comparison value was computed.** The parser
fix is written and unit-tested at the time of freezing; **no re-derived
multiplier existed**, no OLD-vs-NEW arm had been run, and no solve had been
spent. Gates and triggers below are final — a trigger this document does not
contain cannot be quoted afterwards. Format mirrors
`PREREG-caiso151-firm-selfsched-clip-2026-07-31.md`, not copied.

Lever: **not** a mechanism-matrix §5.2 queue item. This is the defect
`FINDING-caiso150` §E1 filed and explicitly refused to absorb ("the RLE parse
defect is the offer-surface lane's, and is cross-ISO by construction"), which
has been unowned since. It biases a **LIVE keeper input**, so it is taken as
this session's primary lever. Matrix row touched: `measured_offer_surface`,
CAISO cell **`K`** at the time of writing (caiso-92) — this document does not
pre-grant any change to it.

Base keeper: `2026-07-31-caiso-151-firm-selfsched`, determination
CALIBRATED-WITH-CAVEATS, 0 FAILs, C1 12/12 · free 8/8, 2 ledgered non-protective
caveats from the owner's caiso-145 disposition (C3a-2025 on the caiso-141 A2
water wall, C3c-2023/24 on caiso-131 A4), 1 of 3 slots free, protective 0/1.
CAISO holds **no** rule-22 calibration-complete marker (re-verified this
session) — so if this session solves, it solves **2023 2024 2025 only** and
writes no marker.

**Promotion is NOT pre-granted and is not requested in advance.** Neither is a
solve: §4 registers the condition under which this session stops without one.

---

## §1 — the defect, exactly

`scripts/lib/dam_public_bids/caiso.py` keys every clean row by its range START
stamp (`SCH_BID_TIMEINTERVALSTART_GMT` for curve rows, `TIMEINTERVALSTART_GMT`
for self-schedule rows) and **never reads the STOP columns**. The OASIS
disclosure is **run-length-encoded**: the stamp pair is `[start, stop)` over
whole hours and a bid held unchanged across several operating hours is published
as ONE row — a whole-day hold is a single 24-hour row.

The datatype's own schema declares the grain as *one row per masked resource ×
**operating hour** × product × breakpoint*, so the parser has been violating its
own contract. Every hour of every multi-hour range is dropped, and the dropped
hours are **exactly the stable-bid ones**.

Measured on the raw CSV before any fix, CAISO GENERATOR EN curve rows:

| trade date | raw rows | true curve-hours | carried |
|---|---|---|---|
| 2023-01-02 (this session, direct on the raw CSV) | 18,520 | **50,972** | 36.3 % |
| 2023-01-15 (caiso-150 §E1, resource-hour grain) | 5,514 | 12,878 | 42.8 % |
| 2023-02-10 (caiso-150 §E1) | 6,628 | 14,036 | 47.2 % |
| 2024-07-10 (caiso-150 §E1) | 9,195 | 18,414 | 49.9 % |

On 2023-01-02, 909 of the 18,520 rows carry a **24-hour** span.

**Why it reaches a keeper input.** `scripts/data/derive_caiso_offer_surface.py`
groups on `(resource_seq, interval_start_utc)` with **no hour weighting**, so
every statistic it forms — the per-resource-day body price feeding the
gas-coupling classification, the per-resource-hour band price, the
per-resource-year median multiplier, the top-of-curve ladder's net-load bin
assignment — is computed on a population biased toward frequently-rebidding
resource-hours. It writes two artifacts that are **both armed in the live
keeper** (`caiso151_clip_B/run_config.json`):

* `caiso_offer_curve_measured.json` → `ScenarioConfig.caiso_offer_surface_measured = true`
* `caiso_offer_surface_condbinned.json` → `ScenarioConfig.caiso_offer_surface_conditional = true`

## §2 — the fix, and why it is ISO-generic

A shared `expand_rle(frame, stop_utc)` in `scripts/lib/dam_public_bids/__init__.py`
expands `[start, stop)` to one row per hour **before** `step_idx` is assigned;
`caiso.py` calls it once per row shape with that shape's own STOP column. The
expander lives in the shared package, not the CAISO module, because every ISO's
DAM bid disclosure is run-length-encoded the same way and CAISO is only the
first registered spec.

It **reuses the caiso-151 expander's semantics** rather than re-deriving them
(`scripts/data/derive_caiso_intertie_selfsched.py::_expand`, committed): expand
to hour slots before any hourly statistic; a null or non-positive span means
"this hour only" and is never dropped; the clock is **exact UTC**, converted to
US/Pacific only downstream, and `envelopes._caiso_interchange_model_clock` is
**not** applied (that lag undoes an EIA-930 publication artifact this source
does not carry).

The fix is a **correctness repair to a measured input**, not a mechanism. Rule
14 `[R-ACCURATE]` therefore governs: the corrected parse is kept whatever it
does to the backcast, and a worse fit is a **discovered bug whose root cause is
named**, never a reason to revert to the biased population.

## §3 — the measurement, and what may be compared with what

**Corpus.** A single balanced **358-day** re-fetch: days 2, 5, 8, 11, 14, 17, 20,
23, 26, 29 of every month of 2023/2024/2025 (Feb 29 absent in the two non-leap
years). `data/raw/caiso-public-bids/zips` is gitignored and died with the
container, so the corpus is regenerated by
`scripts/data/fetch_caiso_public_bids.py`. Seasonal and year balance is
**load-bearing** (caiso-150 §B: a winter-only corpus overstates its headline by
~50 % and mislocates the diurnal peak); the sampler is balanced by construction
and spacing 3 walks the weekday through all seven within each month.

**The comparison is OLD-parse vs NEW-parse on the SAME corpus.** Both arms
curate the same 358 zips and run the same deriver at the same HEAD; the only
difference is the parser. This is the only construction that isolates the parse
defect.

**The committed artifact is NOT the control.** `caiso_offer_curve_measured.json`
was derived 2026-07-19 on a corpus that no longer exists, so any NEW-vs-committed
difference confounds parse with corpus. NEW-vs-committed is reported **as
context only** — it is the delta a re-derive would actually ship to the keeper —
and no causal claim is attached to it. This is the same discipline as solving a
same-HEAD zero-delta control instead of comparing against committed keeper
bytes.

**Nothing is written to a keeper input during the measurement.** Both arms run
with the consumed JSONs restored from git afterwards; the live artifacts move
only if §4 says the effect is material and the corrected derive clears its own
gates.

## §4 — the materiality trigger, frozen before any value was computed

The threshold is **not invented here**. It is the deriver's own frozen
estimation-stage tolerance, `max(0.08 mult units, 10 %)` — the band inside which
G2 (cut robustness) and G3 (estimation LOYO) already declare two values to be
the same statistic. If the parse defect moves a consumed stat by more than the
tolerance the derive itself uses to certify that stat as identified, the biased
population is producing a different answer from the correct one.

**MATERIAL if either fires**, on OLD-vs-NEW over the same corpus:

* **T1 — static bands.** Any of the **6 consumed** static band multipliers
  (CC_REGULAR and CT_PEAKER × econ_low / econ_high / peak) moves by more than
  `max(0.08, 10 %)`.
* **T2 — conditional ladder.** For any (class × net-load bin), the mean of that
  bin's 5 equal-capacity rungs — the average markup the P1 mechanism applies in
  that bin, which is what the LP consumes — moves by more than
  `max(0.08, 10 %)`.

The unarmed `committed` band and the G1 bucket capacities are **reported, never
triggers**: the committed band is not consumed (rule 19 — its owner is unit
commitment), and G1 is a gate, not a consumed stat.

**IMMATERIAL → FILE AND STOP.** If neither trigger fires, the corrected parser
and its test still land (the contract violation is real and the fix is right),
the finding records the measured non-effect, the matrix cell is marked
accordingly, and **no solve is spent and nothing is registered on the dashboard**
— the caiso-136/143/144/149/150 pattern.

**GATE FAILURE is a third, separate outcome.** If the corrected parse makes any
of the deriver's own frozen G1–G4 FAIL, the derive **refuses to write** and the
lane STOPS at the derive: the finding reports which gate failed and why, the
keeper keeps the artifact it has, and no gate threshold is retuned to rescue a
verdict (rule 23 `[R-FROZEN-DERIVE]`). A corrected input that cannot pass its
own identification gates is an open root cause, not a shippable artifact.

## §5 — expected direction, stated so it cannot be spun later

**The direction is NOT known and must not be assumed** — caiso-150 §E1 said so
explicitly ("the directional effect on the fitted band prices is NOT measured
here and must not be assumed"), and this document does not pretend otherwise.
What can be reasoned ex ante is *which statistic is exposed and how*:

1. **Static bands: expected SMALL, direction genuinely unsigned.** The
   estimation unit is a per-resource-year **median** across that resource's
   hours, then a cap-weighted median across resources. A resource whose bids are
   always stable, or always volatile, has an unchanged median — the bias only
   bites resources that MIX, and only by moving their median toward the stable
   hours. Whether stable hours price above or below volatile hours is not known
   a priori. **T1 firing at all would itself be the surprise.**
2. **Conditional ladder: expected LARGER, and the mis-assignment is directional
   even if its price consequence is not.** The net-load bin is assigned from the
   row's hour. A 24-hour hold currently lands **only in the bin of its start
   hour**, and the OASIS trade day starts at 08:00 UTC = **local midnight** —
   the bottom of the net-load distribution. So today every whole-day hold is
   charged entirely to **bin 0**, and the high-net-load bins retain only
   actively-rebidding resources. Correcting this must (a) remove whole-day holds
   from bin 0's exclusive ownership and (b) add stable resource-hours to the
   peak bins. That the peak bins' composition changes is near-certain; whether
   their rungs rise or fall is not registered as a prediction.
3. **Classification is exposed too, and it is reported.** The gas-coupling
   regression's per-resource-day body price becomes a median over up to 24 hours
   instead of over the start-hours only, so slopes, `r`, the CC/CT split at the
   8.5 MMBtu/MWh cut, and the G1 bucket capacities may all move. Any
   reclassification is reported in the finding as a first-class result.

**No sign is claimed for the eventual λ effect**, and none may be read back into
this document later.

## §6 — what makes this a REJECT

There is **no reject of the parse fix**. It repairs a violation of the
datatype's own declared grain; rule 14 keeps it whatever the fit does. What the
following reject is the **promotion of a re-derived keeper input**:

- **(a) A derive gate fails** (§4, third outcome). Lane stops at the derive.
- **(b) The effect is immaterial** (§4). Filed, not solved, not registered.
- **(c) A protective check regresses** — §7. Disqualifying regardless of what
  the corrected input does to the fit. CAISO's protective slot is **0/1** and
  this session does not spend it.
- **(d) The delta is not single.** Any second flag, or any parameter touched to
  make a number land — automatic reject, and the session says so.
- **(e) The corrected artifact is not what the corrected parse produced.** No
  hand-edit, no blend of OLD and NEW values, no per-band cherry-pick.

**Explicitly NOT reject grounds** (rules 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`): a
worse C3a, C3b, C3c or C5a; any criterion moving from a better number to a worse
one *while its verdict stays the same*; the keeper's headline MAE rising. Those
are outcomes to report and, where they FAIL, to root-cause — never grounds to
re-ship the biased population.

## §7 — protective checks (all must hold if a solve happens)

1. **Single delta.** Both arms are `replay_keeper.py` replays of
   `results/calibration/caiso151_clip_B` at the same HEAD; the control is a
   **zero-delta replay solved in this session**, never the keeper's committed
   bytes (caiso-146 measured the caiso-139 keeper drifting up to 3.2 GW on a
   class-hour at HEAD). The only difference between arms is the content of the
   two derived JSONs.
2. **No other ISO moves.** The expander is shared, but CAISO is the only
   registered `dam-public-bids` spec, and the two derived artifacts are
   CAISO-only (rule 25 `[R-ISO-SCOPE]`). No other ISO's keeper input changes —
   verified, not assumed.
3. **No criterion verdict may flip PASS → FAIL** for a promotion. CAISO is at
   0 FAILs. A new FAIL is disqualifying *for promotion*; the corrected input
   still stays, the arm is filed rather than promoted, and the FAIL's root cause
   is named (rule 14's "discovered bug" branch).
4. **Neither ledgered caveat is re-litigated.** C3a-2025 and C3c-2023/24 stay
   exactly as the owner dispositioned them at caiso-145. This session proposes
   no lever for either.
5. **Binding gates go on the classes that ABSORB the change** — for an
   offer-surface lever that is **CC_REGULAR** and **CT_PEAKER** (C7-gated; C8
   peaker cap 0.15), plus **ST_GAS / COAL** (C7-gated). Nuclear, CC_CHP, CT_CHP
   and ST_CHP are exempt from **both** C7 and C8 by **explicit class list**, not
   by the 2 % materiality floor — no exempt class's D-1/D-2 number may be quoted
   as a passed gate.
6. **ST_GAS 2024/2025 raw D-1 rows read FAIL on both arms** and have since
   before caiso-148: pre-existing, below the 2 % materiality floor, **not**
   attributable to this lever.
7. **`legitimacy_diagnostics.json` is generated for BOTH arms.**
   `replay_keeper.py` does not emit it, and without it C7/C8 score SKIPPED —
   a skipped protective gate is not a passed one.
8. **The corrected parse is verified on real data before it is trusted**: no
   duplicate schema key rows, hours confined to the trade date, and the
   GENERATOR EN clean-row count equal to the raw curve-hour count computed
   independently from the CSV. (Done at freeze time on 2023-01-02: 50,972 =
   50,972, 0 duplicate keys, hours 08:00 UTC .. 07:00 UTC next day.)

## §8 — C3a materiality trigger

**1.0 pp**, the caiso-151 standard. If a solved arm moves the C3a load-weighted
miss by **≥ 1.0 pp** in any year, that is material and is reported in the
finding as a first-class result — in either direction, including if it *helps*.
Below 1.0 pp the movement is reported and no claim is built on it.

C3a-2025 is a **ledgered caveat**, not an open lane. Movement here does not
reopen it: reopening requires new evidence against a named
caiso-140/141/142/143/144 DO-NOT-REDO cell, or the owner-funded non-public
hourly pumped-storage intake (caiso-145). A favourable movement is recorded as
incidental and explicitly **not** claimed as closing the caveat.

## §9 — solve mechanics registered in advance (only if §4 says MATERIAL)

Two arms, both `--year 2023 2024 2025` in a **single invocation each** (rule 16
`[R-ALLYEARS]`), run as concurrent separate invocations (rule 12
`[R-PARALLEL]`, cap 2 for plant-level CAISO):

```
control: replay_keeper.py results/calibration/caiso151_clip_B \
             --out-dir results/calibration/caiso152_control_A
arm:     replay_keeper.py results/calibration/caiso151_clip_B \
             --out-dir results/calibration/caiso152_rleparse_B
```

The arm carries **no `--set` flag**: the delta is the content of the two derived
JSONs on disk, so the arm is solved with the corrected artifacts in place and
the control with the committed ones. Both arms then get
`scripts/legitimacy_diagnostics.py --iso CAISO --years 2023 2024 2025`, and both
are registered on the dashboard (rule 15) whatever the verdict.

CAISO holds **no** rule-22 calibration-complete marker; no out-of-training year
is solved, scored or touched, and **no marker is written** (a separate owner
act).
