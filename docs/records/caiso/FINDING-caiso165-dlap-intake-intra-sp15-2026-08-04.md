# FINDING — caiso-165: CAISO DLAP intake + intra-SP15 congestion, MEASURED

**Session** caiso-165 · **Date** 2026-08-04 · **Branch**
`claude/caiso-dlap-intake-sp15-9yvs1v`

**Prereg** `PRECHECK-caiso165-dlap-intake-intra-sp15-2026-08-04.md`, pushed
(and auto-merged to main) **before the probe ran on intaken data**.

**No LP. No solve. Keeper UNCHANGED** at
`2026-08-04-caiso164-zonal-loss-surface`. No run registered, because no run was
produced.

**Outcome: caiso-164 §6's attribution is CONFIRMED.** Three of the four
full-coverage corridor-years meet the pre-registered CONFIRMED bar, the fourth
is PARTIAL, and **not one is FALSIFIED**. The intra-SP15 corridor congests
heavily, in the belly, in the direction an import-constrained load pocket must
take — while the model separates it in **0.00 % of 8,760 belly hours**.

---

## 0. Headline

**caiso-164 inferred the intra-SP15 corridor from prices and energy balances.
It is now measured, and it is real — and larger than the inference implied.**

In the 2025 solar belly the real SCE load pocket prices above the SP15
generation hub in **98.05 %** of hours at a mean **|dMCC| = $2.00/MWh**, and the
SDGE pocket in **99.69 %** of hours at **$6.45/MWh**. The caiso-164 keeper, in
those same hours, separates `LA_BASIN` from `SP15_rest` in **zero hours — 0 of
8,760 across all three years** — and separates `SDGE` from `SP15_rest` in the
**wrong direction** in 2024–25.

The corridor is also **growing fast**: belly mean `dMCC` goes
**+0.701 → +1.912** (SCE) and **+3.924 → +6.420** (SDGE) $/MWh from 2024 to
2025.

**Method note that carries forward:** the corridor was not merely unmeasured
before this session, it was **structurally invisible**. A `TH_*_GEN` hub prices
where power is *injected*; a DLAP prices where load is *withdrawn*. With only
one southern hub in the record, no hub-to-hub basis can contain an intra-SP15
corridor at all. §1.

---

## 1. What the intake changed

CAISO's four `DLAP_*-APND` load aggregation points now flow through the whole
CAISO intake path and into the committed aggregates:

| stage | change |
|---|---|
| `scripts/data/fetch_caiso_oasis.py` | `DLAPS` constant + `--nodes` selector (`hubs`/`dlaps`/`all`/literals); default unchanged, so no existing caller moves |
| `scripts/data/fold_caiso_oasis_grp_zips.py` | `NODES` = `HUBS + DLAPS + interties`; `--refold` rewrites windows extracted against the older, narrower set |
| `scripts/data/postprocess_oasis_downloads.py` | **no change needed** — already node-agnostic (pivots on `NODE`) |

**Coverage landed:**

| year | complete hours | nodes | source |
|---|---:|---:|---|
| 2023 | 528 | 7 | 22 committed Jan `DAM_LMP_GRP` bulk zips, refolded at 10 nodes |
| 2024 | **8,784** | 7 | 120 OASIS `PRC_LMP` windows, **zero failures** |
| 2025 | **8,760** | 7 | ″ |

2024 and 2025 are **exact** — 61,488 = 7 × 8,784 and 61,320 = 7 × 8,760 rows,
no gaps.

### 1.1 Additivity is proven, not asserted

Both consumers of `CAISO_dam_hourly_<year>.csv` select hubs explicitly
(`caiso_zonal_sufficiency._hub_wide` takes `list(HUBS.values())`;
`derive_actual_lmp` weights `CAISO_HUB_WEIGHTS`), and
`derive_caiso_loss_surface.py --acceptance` re-runs **6/6 pair-years in the
`[0.5×, 1.5×]` band with `CAISO_loss_surface.csv` byte-unchanged**, before and
after the full intake. **The intake perturbs no derived artifact and no
keeper.**

### 1.2 The identity guards pass *with the DLAPs included*

This is the precondition for using CAISO's published decomposition on a DLAP at
all, so it was checked rather than assumed:

| year | max MCE spread across all 7 nodes | max \|LMP − (MCE+MCC+MCL+MGHG)\| |
|---|---:|---:|
| 2023 | `0.00e+00` $/MWh | `3e-05` |
| 2024 | `0.00e+00` | `5e-05` |
| 2025 | `0.00e+00` | `1e-05` |

MCE is one system reference across generation hubs **and** load aggregation
points, so a DLAP-to-hub basis is exactly `dMCC + dMCL` — the same algebra
caiso-164 used, now on the corridor that matters.

### 1.3 Partial 2023 — the declared outcome, not a shortfall

Prereg §2.2 declared, before the fetch, a per-`(zone, year, month)` coverage
rule keyed to the **existing frozen** `MIN_HOURS_PER_YEAR / 8760` ratio (zero
new parameters). Under it 2023 takes **no** measured DLAP month: its 528 hours
are 22 days of January (71 % of the month). That is recorded, not worked around
— 2023 was never backfilled from an out-of-window year, and
`MIN_HOURS_PER_YEAR = 8000` stays.

---

## 2. THE MEASUREMENT — congestion vs loss on the corridor caiso-164 inferred

All hours, CAISO's own components. `dMCE ≡ 0`, so basis = `dMCC + dMCL` exactly.

| year | corridor | mean total | **dMCC** | **dMCL** | cong % | loss % |
|---|---|---:|---:|---:|---:|---:|
| 2024 | SCE pocket − SP15 gen | 1.344 | **0.419** | **0.924** | 31.2 % | 68.8 % |
| 2025 | SCE pocket − SP15 gen | 2.193 | **1.225** | **0.969** | 55.8 % | 44.2 % |
| 2024 | SDGE pocket − SP15 gen | 3.536 | **2.325** | **1.211** | 65.8 % | 34.2 % |
| 2025 | SDGE pocket − SP15 gen | 5.261 | **3.951** | **1.310** | 75.1 % | 24.9 % |

Context corridors, which make a null result *locate* rather than merely exclude
(they are not null): `SDGE − SCE` is **86.9 / 88.9 %** congestion — the two
southern pockets are themselves separated from each other — and `SCE − NP15`
runs **−6.649 / −3.816** $/MWh, i.e. the southern pocket is *cheaper* than the
north on an all-hours mean even while it is dearer than its own generation hub.

---

## 3. THE BELLY WINDOW AND THE PRE-REGISTERED VERDICT

Pacific local hours 09–16 (caiso-164's own window, unchanged), congestion
component only.

| year | corridor | belly h | sep % | mean \|dMCC\| | pocket-dearer % | **verdict** |
|---|---|---:|---:|---:|---:|---|
| 2024 | SCE − SP15 gen | 2,928 | 89.31 % | 1.038 | 52.4 % | **PARTIAL** |
| 2025 | SCE − SP15 gen | 2,920 | **98.05 %** | **1.999** | **84.0 %** | **CONFIRMED** |
| 2024 | SDGE − SP15 gen | 2,928 | **94.23 %** | **4.038** | **96.8 %** | **CONFIRMED** |
| 2025 | SDGE − SP15 gen | 2,920 | **99.69 %** | **6.451** | **99.1 %** | **CONFIRMED** |
| 2023 | both | 176 | 36.9 / 43.2 % | 0.403 / 1.244 | 29.2 / 93.4 % | *(PARTIAL — see below)* |

**3 CONFIRMED, 1 PARTIAL, 0 FALSIFIED** on the full-coverage years.

**The 2023 rows are reported but carry no weight, and that is not a
post-hoc exemption**: prereg §2.2 declared 2023 partial *before* the fetch. Its
176 belly hours are all January, the least belly-relevant month of the year.
They are printed because suppressing a measured row is worse than showing one
with its limits stated.

**The one PARTIAL is a direction split, and it is not rounded up.** SCE-2024
clears frequency (89.31 % ≫ 50 %) and magnitude (1.038 ≥ 1.00) but its
pocket-dearer share is **52.4 %**, under the 60 % bar — the corridor binds in
both directions in 2024 and only settles into the pocket-dearer direction in
2025 (84.0 %). Under the pre-registered rule that is PARTIAL, and it is recorded
as PARTIAL.

### 3.1 It is belly-timed, which the attribution requires

Measured `dMCC` by Pacific local hour, 2025 — overnight → belly:

* **SCE − SP15 gen**: ~0.80–0.99 overnight → **1.79–2.11 in h08–16**
* **SDGE − SP15 gen**: ~1.17–1.79 overnight → **5.58–7.38 in h08–17**

Both roughly double or triple into the solar belly and fall away after h17. The
congestion is not a flat annual offset; it has the shape caiso-164's story
needs.

---

## 4. WHAT THE MODEL DOES IN THOSE SAME HOURS

caiso-164 keeper, P1, committed hourly sidecars — no replay, no solve.

| year | corridor | belly h | sep % | mean | pocket-dearer % |
|---|---|---:|---:|---:|---:|
| 2023 | `LA_BASIN − SP15_rest` | 2,920 | **0.00 %** | 0.0000 | 0.0 % |
| 2024 | `LA_BASIN − SP15_rest` | 2,920 | **0.00 %** | 0.0000 | 0.0 % |
| 2025 | `LA_BASIN − SP15_rest` | 2,920 | **0.00 %** | −0.0000 | 0.0 % |
| 2023 | `SDGE − SP15_rest` | 2,920 | 1.03 % | +0.0489 | 76.7 % |
| 2024 | `SDGE − SP15_rest` | 2,920 | 20.41 % | **−2.6345** | **0.0 %** |
| 2025 | `SDGE − SP15_rest` | 2,920 | 24.93 % | **−5.3152** | **1.0 %** |

Two distinct defects, and they are **not** the same defect:

1. **`LA_BASIN` is a perfect copper-plate with `SP15_rest`** — 0 separated hours
   out of 8,760, against a measured 89–98 %. This is the corridor caiso-164
   named, and the model has no representation of it whatsoever.
2. **`SDGE` is INVERTED, not merely under-separated.** The model does separate
   it (20–25 % of belly hours) but runs the pocket **cheaper** than the
   generation hub (pocket-dearer 0.0 % / 1.0 %) at a mean of **−2.63 / −5.32**
   $/MWh, while the measured pocket is **dearer** in 96.8 % / 99.1 % of hours at
   **+3.92 / +6.42**. The sign is wrong, and the magnitude of the error is the
   sum of the two — roughly **$6.6 / $11.7 per MWh**.

Defect 2 was **not visible to caiso-164 at all** and is not stated in its
finding: with no DLAP the model's SDGE limb had nothing to be compared against.

---

## 5. What this does and does not license

**Licensed by this measurement:**

* caiso-164 §6's attribution stands. The blocker's "needs CAISO nodal/DLAP LMP
  components" half is **discharged** — the data is in `data/raw`.
* Its item 2 (the loss surface's two `interpolated=True` zones) is **fully
  unblocked**. The measured loss deltas the two zones are currently *missing* by
  inheriting the SP15 generation hub are **`dMCL` = +0.924 / +0.969 (SCE)** and
  **+1.211 / +1.310 (SDGE)** $/MWh — comparable to, and in SDGE's case larger
  than, the entire NP15−ZP26 loss component (+1.102 / +1.049) that the caiso-164
  keeper was promoted for representing.

**NOT licensed, and explicitly withheld:**

* **Arm B is not armed.** No published intra-SP15 transfer limit (CAISO LCT/LCR
  local-area import capability, a published path rating, or an ATC construction
  off measured directed flows) was located in `data/raw` or in CAISO's published
  record within this session. Per prereg §5.2 that means it is **filed as the
  remaining blocker, not approximated**. A limit chosen to reproduce the
  frequencies or magnitudes measured above would be an **OUTCOME PIN** — rule 13
  `[R-MEASURED]`, rules 5/21/24 — and the fact that this session now knows those
  numbers precisely makes the prohibition *more* binding, not less.
* **Arm A was not solved.** The session's OASIS intake consumed the time budget
  (§7). Arm A is chartered and fully specified — the crosswalk disposition, the
  strengthened acceptance gate and the rule-14 ruling are all pre-registered in
  prereg §5.1 — but a two-arm sequential CAISO 2023–2025 replay was not started
  rather than started and abandoned. **Nothing about Arm A was tuned, previewed
  or partially run.**
* **No N–S topology lever.** caiso-164 §0 measured that topology is not where
  the recoverable component was; the corridor here is INTRA-SP15, a different
  object. Unchanged.

---

## 6. Two OASIS operational facts, paid for once so the next lane does not

Both are now in `fetch_caiso_oasis.py`'s docstring and code.

1. **The `PRC_LMP` retention boundary moved *during this session*.** Recorded as
   2023-04-19 on 2026-07-31; binary-searched to ~2023-04-22 on 2026-08-04, and a
   day-level recheck found 04-22 and 04-23 themselves already gone (~2023-04-24
   in practice). It is a property of the **report, not the node** —
   `TH_SP15_GEN` and `DLAP_SCE` fail and succeed together at the same dates, so
   this is not a DLAP limitation. Near-boundary windows are additionally ~5×
   slower (20.7 s vs 4.5 s for the same 25-day size) and genuinely gappy.
   **Re-measure it; do not trust a recorded date.**
2. **A throttled OASIS hangs rather than 429s, and `urlopen(timeout=)` cannot
   catch it.** That timeout is per-socket-operation, not total, so a trickling
   read never trips it: measured, a stalled `resp.read()` sat **>10 minutes**
   inside a `timeout=180` call, printing nothing. Worse, **stalled readers hold
   the per-IP connection slots**, so the symptom looks exactly like an IP ban and
   is not one — killing the stalled process restored full-speed service
   immediately. `REQUEST_WALL_CLOCK_S` (SIGALRM, 240 s) now makes such a request
   *fail* so the existing retry/backoff can run.
   *Interaction worth knowing:* the adaptive window sizer treats any failure as
   "window too large" and halves. Under throttling that inference is wrong — the
   window was fine, the server was refusing — so a throttled crawl walks itself
   down to 1-day windows. Raising `--sleep` is the mitigation; the sizer was
   deliberately left alone, since a wrong-but-conservative halving still
   terminates.

Once bounded and unthrottled, the intake ran **120 windows with zero failures**
at a steady ~13 s/window.

---

## 7. Honest accounting of what was not delivered

* **Phase 3 did not run.** Neither arm was solved. The reason is time, not a
  result: roughly half the session went to diagnosing the OASIS stall described
  in §6, which presented as an IP ban and was in fact self-inflicted connection
  exhaustion. Phase 2 was the pre-declared deliverable "even if Phase 3 never
  runs", and it is complete.
* **`DLAP_PGAE` is intaken but not used for a model zone.** Prereg §5.1
  pre-committed that it would not be: it straddles NP15 and ZP26, so
  substituting it would replace two measured hub values with one blended one. It
  is carried for context and future lanes; §2's `PGAE − NP15` row is measured
  and reported.
* **No dashboard registration.** Rule 15 registers *runs*; this session produced
  none. Consistent with the caiso-161 / nyiso-121 no-LP precedent.

---

## 8. Artifacts

| | |
|---|---|
| prereg | `results/calibration/PRECHECK-caiso165-dlap-intake-intra-sp15-2026-08-04.md` |
| probe | `scripts/probes/caiso165_intra_sp15_decomp.py` |
| probe output | `results/calibration/_caiso165_intra_sp15.json` |
| intake — fetch | `scripts/data/fetch_caiso_oasis.py` (`DLAPS`, `--nodes`, `--start-date`, `REQUEST_WALL_CLOCK_S`) |
| intake — bulk-zip fold | `scripts/data/fold_caiso_oasis_grp_zips.py` (`NODES`, `--refold`) |
| data | `data/raw/lmp-data/CAISO/CAISO_dam_hourly_{2023,2024,2025}.csv` |
| unchanged keeper | `2026-08-04-caiso164-zonal-loss-surface` |

---

## 9. Standing lessons

1. **"Not in `data/raw`" is a claim about the repo, not about the market.**
   caiso-164 filed a blocker needing "CAISO nodal/DLAP LMP components"; those
   components were in CAISO's own published feed the whole time, and four of
   them were sitting inside bulk zips already committed to this repo. Before
   filing a data blocker, check what the market publishes *and* what the repo
   already holds.
2. **Ask whether the instrument can see the object at all.** The intra-SP15
   corridor was not under-measured by the hub record — it was *unobservable* in
   it, because a generation-hub basis with one southern hub has no degree of
   freedom for it. That is a stronger and more useful statement than "we lack
   data", and it is what made the DLAP the specific fix.
3. **A pre-registered rule earns its keep when the answer is mixed.** Three
   CONFIRMED and one PARTIAL is a more awkward result than a clean sweep, and
   the PARTIAL (SCE-2024, pocket-dearer 52.4 % against a 60 % bar) is exactly
   the row a session would be tempted to round up after the fact. It was written
   down first, so it did not get rounded.
4. **A hang is not a ban.** Half this session was spent treating self-inflicted
   connection exhaustion as an external rate limit. The diagnostic that settled
   it was cheap and should have come first: kill every local client, then issue
   one request by hand.
