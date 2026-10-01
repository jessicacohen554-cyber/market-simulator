# PRECOMMIT — pjm-h3: arm `pjm_reserve_pergen_sync`, the SYNCHRONIZED reserve
# sub-product split, on the re-opened price-formation frontier

**Session** `pjm-h3` (continuation of `pjm-h2`) · **ISO** PJM · **Date** 2026-09-13
**Committed BEFORE any solve.** Every gate below is fixed here and is not re-read afterwards.
**Keeper** `2026-09-11-pjm-d4-4-gasoutage` — CALIBRATED, 8/8, zero caveats. Unchanged by this card.

---

## 0. OWNER RULING — THE FRONTIER IS RE-OPENED

**Owner, 2026-09-13, verbatim: *"I don't care if it touched frontier do 2"*** — where option 2 was
"re-open the pjm-142 price-formation frontier", put to the owner with the alternative (a coal
`phys_*` build) and declined in its favour. The pjm-138 §6 DO-NOT-REDO ("do not propose a
reserve/scarcity mechanism for PJM") and the pjm-141 §5.3 terminal state are **superseded for this
lane by that ruling**. Nothing else in either document is disturbed, and the two things the ruling
does **not** license are stated up front:

* **No MIP.** The Stack mandate is untouched; this arm is pure LP.
* **No adder.** `ordc_scarcity_overlay` stays `G`. This is not a post-solve overlay.

## 1. THE ARM — one field

`pjm_reserve_pergen_sync = True` (dataclass default `False`; requires `energy_reserve_coopt` +
`pjm_reserve_pergen`, **both already in the keeper's recipe**). Registered on the matrix row
`reserve_pergen` (rule 28(c), pjm-151 census: a sub-product leg lives on its family row).

**What it is** (`scenarios.py:9828`, Manual 11 §4.2/§4.3.3): (i) the SYNCHRONIZED reserve
sub-product as its own measured balance families — RTO `sr_req_mw` + nested MAD `mad_sr_req_mw`
from PJM Data Miner `reserve_market_results` service=SR — priced by the **published** Synchronized
two-step ORDC rows (`pjm_ordc_curve.csv`, as filed); (ii) a per-pool split of the R columns into a
**SYNC column servable only by ONLINE capacity's 10-min ramp** and a NON-SYNC column servable by
offline fast-start ramp; (iii) online scoping of the SYNC caps at the P0→P1 seam from the model's
own P0 run pattern. **Zero parameters fitted to the price residual** — measured requirement,
published curve, physics ramp/commitment gates.

## 2. WHY IT IS THE MECHANISM AND NOT THE RESIDUAL

**The model's reserve market is dead and PJM's is not.** Measured on the keeper's committed
`reserve_family_<year>.parquet` against PJM's own published AS price series
(`data/raw/PJM-AS/ancillary_services_<year>.parquet`, `unit == "Price"`, `row_is_current`):

| | model dual, mean | model hours > 0 | **PJM MAD Sync, mean** | **PJM hours > 0** |
|---|---:|---:|---:|---:|
| 2020 | $0.194 | **0.02 %** | **$1.71** | **45.7 %** |
| 2021 | $0.005 | **0.07 %** | **$3.89** | **60.3 %** |
| 2022 | $0.003 | **0.02 %** | **$9.19** | **61.3 %** |

The defect is structural and named in the source: with the SYNC requirement servable by **offline**
capacity, "the LP can almost always source PJM's small measured requirement from SOME idle pool"
(pjm-87), so the dual is zero — the same "letting an offline peaker's pmax satisfy a spinning
requirement" misrepresentation `reserves/spec.py:618` records for NYISO. **PJM's synchronized
reserve is, by market definition, supplied only by synchronized units.** Rule 14 `[R-ACCURATE]`.

**Its SHAPE is what the diagnosis demands.** pjm-138 §7 lead 1: *"any successor lever must be
shape-only and must raise tight hours without raising slack ones."* PJM's published reserve price is
peaked **3.0×–22.0×** (h16-18 ÷ h01-04) in every one of the six years, and is near-zero overnight:

| yr | h01-04 | h16-18 | ratio |
|---|---:|---:|---:|
| 2020 | $0.42 | $3.44 | 8.3× |
| 2021 | $1.11 | $8.60 | 7.7× |
| 2022 | $5.88 | $17.53 | 3.0× |
| 2023 | $0.70 | $3.89 | 5.6× |
| 2024 | $0.39 | $8.19 | 20.9× |
| 2025 | $0.62 | $9.49 | 15.3× |

**Why the owner closure's merit arithmetic no longer holds — the new evidence rule 28(a) requires.**
The standing verdict on this field is an **owner closure on merit**, not a structural refutation:
*"SYNC product split owner-closed on merit for PJM (**$0-10 vs $75-200 need**)"*. That compared the
mechanism against pjm-84/85's **afternoon scarcity band**. The target measured since is an order of
magnitude smaller: pjm-141 §5.1 puts the **peak under-pricing at −$7.62 / −$11.37 / −$22.19**, and
the missing MAD reserve credit at h16-18 is **$3.89 / $8.19 / $9.49** — i.e. **43 % / 72 % / 43 %**
of it. A mechanism worth $0-10 is a rounding term against $75-200 and a **major fraction** against
$7.62-$22.19. The closure's own reasoning inverts on the corrected target.

**What it is expected to close, and what it is not.** pjm-141 §5.1 point 3 and pjm-138 §7 lead 2
both state that the reserve credit **does not touch the overnight half** (PJM's overnight reserve
price is small and the model's is zero). So this arm addresses the **PEAK half** of the amplitude
deficit and the on-hours consequence that follows from a steeper stack. **The overnight
+$6.82/+$5.78/+$3.40 is NOT claimed and is NOT a gate here** — pjm-142's measured slope
(2.88/3.37/2.57 GW per $1/MWh) says closing it needs 9-20 GW of stack movement, which no lever in
the queue supplies, and that remains an open structural limitation.

## 3. G-CTRL — FORM 4, NO CONTROL SOLVE

The incumbent keeper's committed bundle **is** the control (rule 29(b)). G-DRIFT is discharged by
the strongest available form, established by pjm-d4-4 and not re-derived here: the keeper's own
833-field `cache_key()` is identical at its `git_sha` and at HEAD, and since capx D79 that key
carries the solve-surface fingerprint, so no registry table, solve-surface row or config default the
keeper touches has moved. **Form 4 holds; no control LP is spent or authorized.**

## 4. SCREEN YEAR — **2022**, NAMED ON FOOTPRINT

Rule 29(1): the screen year is the one where **the mechanism's own measured footprint is largest**,
never the largest residual. The mechanism's footprint is the missing reserve credit it would price:
annual mean **$1.71 / $3.89 / $9.19** and h16-18 **$3.44 / $8.60 / $17.53** for 2020 / 2021 / 2022.
**2022 is largest on both, by ~2.4×.** This is demonstrably a footprint choice and not a residual
one: 2022 is **not** the largest C1 residual (2021's CC_REGULAR is bigger on the HEAD basis,
+16.98 vs +12.81 TWh), and it is not the year the owner named.

## 5. THE GATES — STRUCTURAL, STOP-ONLY, FIXED HERE

A screen **may kill this arm; it may never promote it**, and none of these reads the target residual.

| # | gate | pass condition |
|---|---|---|
| **S1** | **arm identity** | the armed config differs from the keeper in `pjm_reserve_pergen_sync` and its declared prerequisites ONLY; any other config delta ⇒ **STOP, do not push** |
| **S2** | **the mechanism is LIVE** | the SYNC family's dual is non-zero in **≥ 20 %** of 8,760 hours (control: 0.02 %). PJM's own 2022 figure is 61.3 %; the bar is a third of it and tests liveness, not accuracy. Still ~0 ⇒ **KILL** |
| **S3** | **shape, not level** | mean SYNC dual at h16-18 **≥ 2×** mean SYNC dual at h01-04 (PJM measured 3.0× in 2022). A flat credit is a level shift, which pjm-138 §7 lead 1 forbids ⇒ **KILL** |
| **S4** | **confinement** | Δ(energy dual) vs control must live in the hours the reserve prices: Pearson r(Δ energy dual, SYNC dual) **≥ +0.30** over 8,760 h, AND mean \|Δ\| in SYNC-dual-zero hours **< 25 %** of mean \|Δ\| in SYNC-dual-positive hours. Otherwise the arm is moving price through another channel ⇒ **STOP** |
| **S5** | **no collateral damage** | no criterion PASSing on the committed 2022 control may FAIL on the arm, over the PROTECTED set **C2, C4, C6, C8**. (C1/C3a/C3b are the targets on 2022 and are excluded from the kill — rule 1: an arm is never promoted by its target improving, and never killed by it either.) |

**NOT gates, reported at full magnitude, gating nothing in either direction:** C1 CC_REGULAR and
COAL_BIT, C3a, C3b, C3c, the annual price level, and the D-A amplitude.

## 6. MEMORY — the documented caution

`scenarios.py:9828` warns the R-column count **doubles** vs `pjm_reserve_pergen` and cites the
2026-07-02 P1 OOM precedent. The shard runs the runner **unmodified**, never passes
`--no-container-preflight`, and **REPORTS the `container preflight:` and `memory peak:` lines**. A
shard approaching its stated budget with no artifact **STOPS and reports** (rule 32(b)); it never
pushes a half-written bundle.

## 7. WHAT HAPPENS NEXT

Screen clears ⇒ the full span **2020 2021 2022** in ONE `--year` invocation and ONE bundle
(rules 16/32(b)), registered per rule 15. Screen kills ⇒ that is the session's result, the remaining
years are never spent, and the matrix cell is stamped with the refutation.

**Rule 31 `[R-RETAIN]`:** the shard pushes its bundle to its own branch (rule 34
`[R-SHARD-PROMOTABLE]` (a)) so a promotion costs zero re-solves. Nothing is deleted.
