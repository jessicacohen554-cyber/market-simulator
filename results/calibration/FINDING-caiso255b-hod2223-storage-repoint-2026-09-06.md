# FINDING — caiso-255b: **`NG: OTH` IS CAISO's battery fleet (G-ID passes on all three legs) — and on the model's own clock the model OVER-discharges storage at hod 22–23 in EVERY year. caiso-253 queue item 1 is REFUTED, on a one-hour clock mismatch in its own diagnostic.** ZERO LP, nothing armed, keeper UNCHANGED. Scoring is untouched: the scorer already reads through the correct loader.

**Session caiso-255 (second object), 2026-09-06.** Branch
`claude/caiso-backcast-calibration-x5v8uq`. Keeper
**`2026-09-05-caiso-252-b1-notrim`** UNCHANGED, DETERMINATION **CALIBRATED**.
Pre-registration: `PRECOMMIT-caiso255b-hod2223-storage-repoint-2026-09-06.md`
(`78d76cf2`), pushed **before any cell of the object was computed**. Rule 22
`[R-HOLDOUT]`: 2023–2025 only; no `complete`/`final` marker; freeze ACTIVE.
Probe: `scripts/probes/_caiso255b_hod2223_storage.py`; artifact
`results/calibration/_caiso255b_hod2223_storage.json`.

---

## §1 — THE GATES, SCORED

| # | registered | measured | verdict |
|---|---|---|---|
| **G-ID-1** (decisive) | `NG: OTH` goes NEGATIVE in the solar belly (hod 10–15) | belly mean **−999 / −2,778 / −4,312 MW**; negative in **84.7 / 97.0 / 97.4 %** of belly hours | **PASS** |
| **G-ID-2** | gross throughput grows monotonically 2023→2025 | **8,093 → 16,314 → 24,276 GWh** | **PASS** |
| **G-ID-3** | \|annual net\| / gross ≤ 0.35 (a battery moves energy, it does not make it) | **0.005 / 0.070 / 0.073** | **PASS** |
| **P-2** | reproduce caiso-253's published pair to ±5 % | **model side +0.0 % in all three years**; **actual side −70.6 / −47.5 / −39.8 %** | **HALF-FALSIFIED — §3** |
| **P-4** | the sign flip is real (model over-discharges 2023, under 2024/25) | **FALSIFIED**: the model **OVER**-discharges in **all three** years | **FALSIFIED** |
| **P-5** | G-FLEET — the model's storage fleet is not materially short | model max discharge / actual max = **1.35 / 1.21 / 1.14** | **HOLDS** |
| **P-6** | G-ENERGY — CC over-run and storage gap opposite in sign, within a factor of 2 | **FALSIFIED, and worse than falsified — §4** | **FALSIFIED** |

**G-ID is the reusable result.** `NG: OTH` is not a residual bucket that happens
to move; it is a battery fleet by three independent signatures. The neutrality
ratio is the sharpest: 24,276 GWh of gross throughput against a **−1,760 GWh**
net in 2025 implies a round-trip efficiency of **≈ 86.5 %**, which is simply
what a lithium fleet is. **No future session needs to re-establish this.**

---

## §2 — THE OBJECT REVERSES

On the model's own clock, hod 22–23, annual mean:

| year | actual `NG: OTH` | model net storage | gap | direction |
|---|--:|--:|--:|---|
| 2023 | 80.6 | 612.8 | **+532.3** | model **OVER**-discharges |
| 2024 | 1,108.1 | 1,657.5 | **+549.4** | model **OVER**-discharges |
| 2025 | 2,011.5 | 2,718.8 | **+707.3** | model **OVER**-discharges |

caiso-253's re-pointing rests on the model being **short** of battery discharge
at 22–23, with CC covering the difference. **The model is not short there. It is
long, in every year, by 0.5–0.7 GW** — and it *still* over-runs CC by
≈ 1,550 MW at those hours. Storage therefore does not explain the 22–23 CC
over-run; it makes it **harder** to explain, because the model already has more
storage output in those hours than the market did.

The diurnal profiles (2025, `NG: OTH` vs model net storage) show the model long
across the whole evening and overnight and charging harder in the belly
(hod 10 diff **−1,090 MW**), with **discharge peaking at hod 19 in both series**.
**There is no phase error. The model over-cycles** — 35.4 GWh/d discharged
against 28.5 actual, 42.1 charged against 33.3.

---

## §3 — WHY caiso-253's NUMBERS DIFFER: A ONE-HOUR CLOCK MISMATCH, AND THE REPO ALREADY OWNED THE FIX

The model side of caiso-253's pair reproduces **to the digit** (680.3 / 1,683.0 /
2,769.2 against its published 680 / 1,683 / 2,769). The actual side does not,
and the reason is not arithmetic:

* `data/raw/eia-930-hourly/CISO hourly.parquet` carries EIA's own stamps, whose
  `Local time` is the **hour-ENDING** label on a DST-aware wall clock. Its
  `Hour` column runs **1 → 24**, and rows with `Hour == 24` carry local
  **00:00 of the next day** — unambiguous.
* The model's hourly index is neither. Mixing the two is an off-by-one-hour
  error, and caiso-253's actuals (274 / 2,112 / 3,342) reproduce **exactly** on
  the raw stamps, at hours `{23, 0}`.
* **The repo already fixes this.** `eia930.frames._eia_hourly_frame_filled`
  returns a frame whose **row k is local hour k on the model's clock**, applying
  the HE→HB shift at anchoring. Its docstring names the bug it was written for:
  *"the CISO-2025 solar-profile +1h shift (FINDING-caiso102, 2026-07-19; also
  hit PJM-2023/MISO-2025)."* **This is the third ISO-year that clock has bitten,
  and the second time in CAISO.**

**The alignment is anchored three ways, not asserted:**

| anchor | result |
|---|---|
| **astronomy** — June 2025, sunrise 05:45 / sunset 20:15 PDT | loader **and** model both first exceed 200 MW of solar at **hod 6** and last at **hod 19** |
| **solar correlation**, model vs loader | **0.9999** at zero shift, against 0.9407 / 0.9415 at ∓1 h |
| **an independent series** — demand | loader clock ranks above both raw-stamp readings in 2023 (**0.906** vs 0.779 vs 0.525) and 2025 (**0.715** vs 0.700 vs 0.620) |

### §3.1 — BLAST RADIUS: NONE. Scoring never used the raw stamps

`src/market_sim/data/eia930/actuals.py` — the path C1 and C4 score through —
reads `_eia_hourly_frame_filled`, i.e. the **correct** loader. The defect was
confined to an **ad-hoc diagnostic read** in caiso-253. **No keeper, no
determination, no rubric score and no registered run moves**, and none is
re-scored by this finding. What is retracted is one queue item's premise.

---

## §4 — G-ENERGY: STORAGE IS NOT PART OF THE 22–23 OBJECT — IT IS ON THE WRONG SIDE OF IT

The registered gate asked whether the CC over-run and the storage gap are the
same energy — opposite in sign, within a factor of 2. They are **the same
sign**: the model is long CC at 22–23 (**+1,547 / +1,558 MW**, caiso-253) **and**
long storage (**+707 MW**). Both are generating more than the market did in
those hours.

So the 22–23 object is **not** "the market used batteries where the model used
CC". Something else absorbs that energy in the real market — and the honest
statement is that this session has **narrowed the object by removing a
candidate**, not closed it. caiso-253 had already refused the import
candidate on admissibility while measuring that it would have cleared in
54–59 % of those hours. Import and storage are now both excluded as the
explanation; **the 22–23 CC over-run remains open with no named carrier.**

---

## §5 — DISCLOSURES AGAINST INTEREST

1. **I GOT THE ALIGNMENT WRONG TWICE BEFORE FINDING THE LOADER, and the
   intermediate conclusions were both publishable-looking and both false.**
   First I read the raw parquet's `Local time` as hour-beginning and concluded
   *"caiso-253 has a one-hour bug in its own comparison"* — the opposite of the
   truth about who was misaligned, since its actuals were at least on a
   self-consistent raw-stamp clock. Then, correcting to hour-ending by a naive
   per-row `(hour−1) % 24`, the June solar edge still sat one hour off
   astronomy and I was about to conclude *"EIA-930's stamps are +2 h"* — an
   assertion about a published federal dataset that would have been wrong.
   **What stopped both was checking the pipeline instead of the shape**, and the
   loader's own docstring naming FINDING-caiso102. The lesson is the boring one
   and it is the reason this probe reads through the loader and anchors three
   ways: *a diurnal alignment argued from shape can be made to support almost
   anything; anchor it on something external, or don't publish it.*
2. **The `--anchor` mode exists because of (1)** and is part of the committed
   probe, so the alignment claim is re-runnable rather than a paragraph.
3. **P-4 was my own prediction and it is FALSIFIED in the direction that
   simplifies the object.** I registered a sign flip as "hostile to the simple
   story" and warned that any arm would have to explain it. There is no sign
   flip — the model is long in all three years — so the warning was aimed at an
   artifact of caiso-253's clock, which I had not yet identified when I wrote it.
4. **G-ID's PASS is the one result here that helps a future session, and it
   arrived attached to a refutation.** The identification is clean and reusable;
   what it identified turned out to kill the object it was built to support.
5. **P-6's failure mode was registered in advance as possibly "partly", and the
   truth is worse than "partly"** — same sign, not opposite. The gate was built
   to be able to say so, and it did.
6. **No solve was spent, no arm was coded, no `ScenarioConfig` field was added,
   the keeper did not move, and no `complete` marker was declared.** Rule 15
   `[R-DASHBOARD]` is not engaged: no run was produced.
7. **An earlier intermediate read of mine (901 / 3,243 / 4,860 MW at 22–23) is
   WRONG and must never be quoted.** It is the raw stamp treated as
   hour-beginning. The correct actuals are **80.6 / 1,108.1 / 2,011.5 MW**.

---

## §6 — DO-NOT-REDO ADDS

1. **Never compare a model hourly series to `data/raw/eia-930-hourly/*.parquet`
   stamps directly.** That file's `Local time` is **hour-ENDING** on a DST-aware
   clock and its `Hour` column runs 1→24. Go through
   `eia930.frames._eia_hourly_frame_filled`, whose contract is *row k = local
   hour k on the model's clock*. This has now bitten CISO twice
   (FINDING-caiso102, and caiso-253's queue item 1) and PJM-2023 / MISO-2025.
2. **Never re-open the hod 22–23 gap as a STORAGE object.** The model is LONG
   storage there in all three years (+532 / +549 / +707 MW) and its discharge is
   in phase (both peak hod 19). The re-pointing is refuted.
3. **Never re-establish that `NG: OTH` is CAISO's battery fleet.** G-ID settles
   it on three independent signatures, including a round-trip efficiency of
   ≈ 86.5 % implied by the 2025 net/gross.
4. **Never read the model's storage shortfall from caiso-253's published
   274 / 2,112 / 3,342.** Those are raw-stamp numbers; the model-clock values are
   80.6 / 1,108.1 / 2,011.5.
5. caiso-254 §6, caiso-253 §7, caiso-252 §7 and §12, caiso-251 §8, caiso-250 §7,
   caiso-249 §7, caiso-248 §8, caiso-247 §8, caiso-246 §8, caiso-245 §7,
   caiso-244 §7, caiso-243 §10, caiso-242 §9, caiso-241 §10, caiso-240 §7,
   caiso-239 §8, caiso-230 §9, caiso-229 §10, caiso-169, caiso-168 §8 stand in
   full.

---

## §7 — QUEUE

1. **The hod 22–23 CC over-run is OPEN with no named carrier.** Import was
   refused on admissibility (caiso-253); storage is refuted here, on the wrong
   side of the sign. The next candidate should be identified from what the
   market actually ran in those hours, not from what the model has spare.
2. **The model OVER-CYCLES storage** — 35.4 vs 28.5 GWh/d discharged, 42.1 vs
   33.3 charged in 2025, with correct phase. That is a **new, separately
   testable object** (arbitrage spread, the ε tiebreaker, cycling degradation,
   or an SOC/duration bound), and it is the first thing this session found that
   is worth its own charter.
3. **The parked partition object** — the owner's grant of FINDING-caiso254 §4
   OPTION 1 stands; the OASIS corpus needs a full re-fetch
   (`PRECOMMIT-caiso255b §7` records exactly what a resuming session inherits).
4. Carried unchanged: the `complete` marker (owner act, raised not granted); the
   stale `program-status.json` CAISO keeper stamp (ask before touching); the C3a
   weight basis; the per-zone storage/class sidecar; the DMM 2025 RA-import
   basis; Panoche.

**No run registered (none produced), no keeper change, no artifact written, no
`ScenarioConfig` field, no `complete` declaration.**
