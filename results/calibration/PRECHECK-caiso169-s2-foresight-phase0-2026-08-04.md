# PRECHECK — caiso-169: is the CAISO evening/overnight storage over-position a PERFECT-FORESIGHT artifact, and is lever-queue item 3 (S2, the DA/RT two-settlement separation) REACHABLE?

**Session** caiso-169 · **Date** 2026-08-04 · **Branch**
`claude/caiso168-calibration-continuation-adaqwy` · **Base** `6d24a84d`

**Committed and pushed BEFORE any value in §4 exists.** No LP, no solve, no
derive, no `ScenarioConfig` field is contemplated by this document. This is a
measurement-only Phase 0 on committed artifacts — the caiso-167 / caiso-168
pattern — and its only possible outputs are a verdict on an existing queue item
and a matrix cell.

---

## §0 — session numbering, and a PRECONDITION CORRECTION

The dispatching prompt opened this lane as "caiso-168". That id is **SPENT**:
`results/calibration/FINDING-caiso168-storage-bid-belly-dual-2026-08-04.md` is
on `origin/main`, as is caiso-167. This lane is therefore **caiso-169**.

**The prompt's stated PRECONDITION does not reproduce from the repository, and
this is recorded before any work is done on it** (detail and evidence:
`FINDING-caiso169` §1).

| prompt asserts | repository state |
|---|---|
| CAISO keeper is `2026-08-04-caiso-166-measured-dlap` | keeper is **`2026-08-04-caiso164-zonal-loss-surface`** (`frontend/data/backcast/keepers/CAISO.json`) |
| that keeper is CALIBRATED-WITH-CAVEATS, 0 FAILs | `calibration_verdict.py --run-id 2026-08-04-caiso-166-measured-dlap` returns **NOT-YET** — "undocumented out-of-tolerance (FAIL) criteria: price_mean" |
| `AMENDMENT-caiso166-S3-recharter-2026-08-04.md` exists | **absent**; never committed |
| branch `claude/caiso166-measured-loss-zones-uwsq1n` may still be open with 3 commits (S3 amendment, promotion, log) | branch **deleted**; PR #3506 merged the finding, the registration and the matrix cell — the amendment, the promotion and the log entry were **never pushed** |

**Consequence, pre-committed here:** this session does **NOT** promote Arm A.
Promoting it would move CAISO from CALIBRATED-WITH-CAVEATS to **NOT-YET** — a
strictly worse determination — which rule 22 D-5(b) says *stops* a promotion and
escalates to the owner rather than being silently written. `FINDING-caiso166`
§4 independently pre-stated the same blocker: promotion "would also need the
2024 `price_mean` FAIL ledgered or fixed", and a ledger disposition is an
explicit **owner act** on its own evidence (the caiso-145 pattern), never a
session's own judgment.

**What this session DOES land from that lane, because the owner directed it in
writing in the dispatching prompt:** the **prospective S3′ re-charter**, as an
amendment document only. `FINDING-caiso166` §3 pre-stated that a future session
may re-charter the ceiling *prospectively* and that the re-charter is an owner
call; the prompt makes it ("S3′ IS NOW THE STANDING CEILING … per pair-year
`|delta|/|measured dMCL|` within the frozen miso-76 B1 band, imported from
`derive_caiso_loss_surface.ACCEPT_BAND`"). Recording it changes no verdict, arms
nothing, and **does not unblock the promotion**, which stays blocked on C3a-2024.

## §1 — the lever, and why it is this one

`docs/mechanism-testing-matrix.md` §5.2 lever queue, **item 3 — S2, the DA/RT
two-settlement separation charter**, on its **evening/overnight** object. It is
the only live item in the CAISO queue:

* items 1, 4, 5, 6, 7, 8 are struck (discharged / `G` / `I` / promoted);
* **item 2** is CLOSED AND SPENT on both halves (caiso-167);
* **item 9** is *recorded* in the matrix as "NEW at caiso-152, BLOCKING,
  unowned" but is in fact **CLOSED — SPENT AND PROMOTED at caiso-153**
  (`FINDING-caiso153-offer-classifier-reid-2026-08-02.md`: the classifier was
  re-identified, all four frozen gates PASS, reproducibility restored, and the
  re-derived surface became the keeper). The matrix text is **stale** and would
  send a session to redo closed work; this session repairs it (rule 28 duty b).
  *This was established by reading, before any measurement, and is stated here
  so the repair cannot be mistaken for a result.*

caiso-168 shut the **belly** route into item 3 and left S2 "STANDING and
UNTOUCHED on its own object". This session takes that object.

## §2 — the object, stated from the record and not re-derived

`FINDING-caiso127` §2: the model's storage is pinned on **192 / 197 / 276 of
365 days**, and that pin "is still the whole compression" of the evening /
overnight price shape. `FINDING-caiso129` §5 closed every *shaped-floor*
instrument against it from one side or the other and named the survivor
explicitly: **"candidate S2 (the DA/RT two-settlement separation — the LP's
single-market perfect-foresight arbitrage itself) is the remaining diagnosis"**,
to be **chartered separately, not approximated by a shaped floor.**

So the question this Phase 0 answers is the *prior* one, which has never been
measured: **is the over-position actually a foresight artifact at all, and
could a two-settlement separation reach it?**

## §3 — instrument and inputs (all committed; nothing derived, nothing fitted)

`scripts/probes/caiso169_s2_foresight_phase0.py`, one command, no LP anywhere.

* keeper bundle `results/calibration/caiso164_zonal_loss_surface/hourly/` —
  `storage_<y>.parquet` (P1 charge/discharge MW by tech), `system_<y>.parquet`
  (zonal duals + demand);
* `data/raw/lmp-data/CAISO/CAISO_dam_hourly_<y>.csv` **and**
  `CAISO_rtm_hourly_<y>.csv` — the measured **two settlements**, the object
  under test;
* `data/raw/eia-930-hourly/CISO hourly.parquet`, `NG: OTH` — the measured
  **battery** fleet net (excludes pumped storage by construction, caiso-168 §H).

**Clock.** The model frame is the fixed **non-leap 8760** with Feb-29 dropped;
the caiso-168 `_model_hour` mapping is reused verbatim. Any measured series is
Feb-29-filtered before alignment (caiso-168's flagged inherited clock defect).

**Limb separation.** `li_ion` and pumped storage are kept **strictly separate**
throughout. The PS limb is the owner-ledgered walled C3a-2025 object; landing on
it is a **stop-and-report**, never an approximation.

## §4 — THE FALSIFIERS, fixed here, before any value exists

S2 is a *structural* change (a second settlement in an LP that has one). This
Phase 0 does not decide whether to build it; it decides whether the object it
would target is really there. Two independent gates, either of which alone
demotes the lever:

* **F1 — FORESIGHT ADVANTAGE.** Score the model's battery dispatch and the
  measured battery fleet's dispatch on the **same measured price series**, as a
  discharge-MWh-weighted **within-day price percentile**. S2's premise requires
  the model to be timing its position better than the real fleet does.
  **Material iff the model's mean daily discharge percentile exceeds the
  measured fleet's by ≥ 0.10 (10 percentile points) on the measured RT series,
  in at least 2 of 3 years.** Below that, there is no foresight advantage to
  remove and S2 is not the instrument for this object.

* **F2 — SETTLEMENT SEPARATION.** A two-settlement representation can only
  change a position to the extent the two settlements **order the day
  differently**. Measure the mean within-day **Spearman rank correlation
  between the measured DA and RT hourly prices**. **Material iff that mean is
  ≤ 0.90.** Above 0.90 the two settlements rank the day near-identically, a
  DA-scheduled fleet and an RT-perfect-foresight fleet place energy in
  substantially the same hours, and the separation cannot reach the position
  whatever else is true.

**0.10** is the smallest advantage that is not within the noise of the
percentile statistic across the three years; **0.90** is the conventional line
above which two orderings are treated as the same ordering. Both are declared
here, before computation, and **neither will be re-cut after it fires** —
`FINDING-caiso166` §3's lesson, which cost that lane its promotion, is
inherited: re-cutting a gate after seeing the number is precisely the move
pre-registration exists to prevent.

**Pre-registered dispositions:**

1. **Both F1 and F2 material** → S2's object is confirmed and its instrument
   can reach it. Outcome is a **charter to the owner** — a structural
   second-settlement change is explicitly out of a lever session's scope
   (caiso-129 §5). **No mechanism is armed in this session either way.**
2. **F1 immaterial** → the model has no foresight advantage over the real fleet
   on this object; S2 is demoted for it, and the over-position is a *quantity*
   or *bound* object, not a foresight one.
3. **F2 immaterial** → the separation cannot reach the position; S2 is refused
   for this object on reach, the caiso-167 `caiso_seam_loss_surface` pattern.
4. **Either falsifier fires** → the matrix cell records the verdict with its
   citation **in this session** (rule 28 duty b), and item 3 is struck or
   re-scoped accordingly. A refutation is a result and is registered as one.

## §5 — what this session will NOT do

* **No solve.** Nothing is registered on the backcast dashboard, because
  nothing is run (the caiso-136/143/144/149/150/167/168 pattern).
* **No promotion.** Per §0 — blocked on C3a-2024, an owner act.
* **No mechanism, no `ScenarioConfig` field, no derive, no re-derive.** In
  particular `CAISO_loss_surface.csv` is not touched and the caiso-153 offer
  surface is not re-derived.
* **No out-of-training year.** CAISO holds **no** rule-22 `complete` marker; the
  holdout spend freeze is ACTIVE. Only 2023 / 2024 / 2025 are read, and **no
  marker is written**.
* **No re-test of any DO-NOT-REDO cell** — `energy_reserve_coopt` (`I`),
  `cc_mustrun_per_plant`, `wecc_endogenous_node`, `caiso_corridor_export_path`,
  `caiso_p1_export_sink_seam`, `netload_drag_floors`,
  `caiso_zonal_loss_surface` (`K`), `caiso_asymmetric_path_ratings`,
  `caiso_per_year_import_caps`; no `td_loss_factor` on top of the loss surface
  (rule 19); no N-S topology lever; the S1 shaped-floor family stays closed
  (caiso-129 §6).
* **Arm B (intra-SP15 transfer limit) stays FILED, not approximated.** No
  published physical limit is in `data/raw`; knowing the measured separation
  precisely binds the prohibition harder, not softer (rule 13; rules 5/21/24).
