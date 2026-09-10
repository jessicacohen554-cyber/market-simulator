# RESULT — nyiso-226 SPAN: the NYC persistent-base re-basing clears every criterion the parent could measure, and C3b could not be measured at all

**Session:** nyiso-226 (parent / orchestrator) · **ISO:** NYISO · **Date:** 2026-09-10
**Keeper / control:** `2026-09-09-nyiso-221-fuelvintage-span`
(`results/calibration/nyiso_fuelvintage_A`), **UNCHANGED.**
**Chain:** `PRECOMMIT-nyiso226-nyc-base-rebasis-2026-09-10.md` →
`ADDENDUM-nyiso226-my-own-gate-S3a-failed-…-2026-09-10.md` →
`RESULT-nyiso226-nyc-base-rebasis-2026-09-10.md` (the 2023 screen) →
`ADDENDUM-nyiso226-span-authorized-2026-09-10.md` (owner ruling) → **this document.**
**Shard record:** `docs/SHARDREPORT-nyiso226-span.md` on branch `claude/nyiso226-span`
(**never merged to `main`**).

**LP spent: ONE shard, 18 m 20 s, three years, exit 0.** The parent ran no LP. No control solve
(rule 29(b) form 4 + G-DRIFT). **Nothing registered, nothing promoted, `main` unchanged** —
`reliability_floor_coeffs_NYISO.csv` still reads `0.175`.

---

## 0. Headline

1. On **every criterion the parent could measure** — C1, C2, C3a, C8 — the arm passes exactly
   where the control passes, with **no flip in either direction**.
2. **C3b was NOT MEASURED**, and it is the criterion most at risk (2024 sits at 0.179 against a
   0.20 ceiling — the tightest margin in the keeper). Three independent blockers, §3.
3. **The change is TWO-SIDED, which is the session's most important finding**: it moves 2023's
   C1 ST_GAS **toward** its actual and 2024's **away**. A residual-fitted coefficient improves
   both. This one cannot, because it is one uniform construction repair.
4. **Promotion is the owner's** (rule 31 `[R-RETAIN]`). The bundle lives only on the shard's
   container and does not survive it.

---

## 1. What the span measured

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| **C1 ST_GAS** \|miss\| control → arm | 1.669 → **1.591 BETTER** | 1.369 → **1.410 WORSE** | *rubric-skipped* |
| C1 CT_PEAKER | 1.717 → 1.716 | 1.540 → 1.539 | *skipped* |
| C1 CC_REGULAR | 0.786 → 0.832 worse | 2.915 → 2.924 worse | *skipped* |
| C1 CC_CHP | 1.103 → 1.124 worse | 2.548 → 2.570 worse | *skipped* |
| C1 ST_CHP | 0.199 → 0.203 worse | 0.257 → 0.259 worse | *skipped* |
| C1 band | 3.820 TWh | 3.980 TWh | — |
| **C3a** control → arm (actual) | 33.6503 → 33.6760 (32.25) | 40.1499 → 40.1782 (38.12) | 61.5983 → 61.6235 (66.43) |
| **C8** ST_GAS forced share | 0.1611 → **0.159** | 0.209 → **0.205** | 0.1813 → **0.1785** |
| D-2 `reliability_floor × ST_GAS` TWh | 1.9019 → 1.8716 | 2.2021 → 2.1733 | 2.1240 → 2.0983 |

**Every C1 class PASSES on both sides in both gated years.** C3a passes all three years, moving
by **+0.026 / +0.028 / +0.025 $/MWh** — under a tenth of a percent. C8 **falls in every year**,
far under the 0.30 merchant cap. `slack` and `dump` are identically **0.000000** in all three
years and `demand` is identical to the control's.

**D-4 is `passed = False` in BOTH arm and control** — pre-existing, not introduced. Arm FAIL set:
2023 `{2480, 8906}`, 2024 `{2480, 54574}`, 2025 `{8006}`, on 0.0015 / 0.0002 / 0.0010 TWh
except 8906-2023 at 0.2283 TWh. Astoria 8906 **passes** 2024 and 2025.

### 1.1 A correction to my own arithmetic, before it propagates

My first hand-reconstruction scored **2025 C1** and produced an ST_GAS FAIL for the arm. It also
produced one for the **control**, which contradicts the keeper's registered CALIBRATED — the
signal that the reconstruction, not the model, was wrong. **The rubric SKIPS C1 and C2 for 2025
entirely**: *"preliminary EIA-923 vintage: incomplete plant data (11/20 prior plants missing
(45 % reporting)); not gated"*, and the same for CC_CHP at 12/17. **There is no 2025 C1 failure
in either run**, and any table showing one is scoring something the rubric deliberately does not
gate.

---

## 2. THE TWO-SIDEDNESS IS THE RESULT

The re-basing lowers ST_GAS everywhere — it can only lower it, since it only ever relaxes a
floor. Against the bench that is **help in one year and harm in the next**:

- **2023**: the model over-produces ST_GAS by **+1.669 TWh**. Lowering it moves **toward** actual.
- **2024**: the model under-produces ST_GAS by **−1.369 TWh**. Lowering it moves **away**.

**A coefficient chosen to close a residual would improve both years. This one cannot**, because
it is a single uniform value applied to the same limb in every year, derived from source data and
fixed ex ante in the PRECOMMIT before any solve. The asymmetry is the same signature the program
already relies on elsewhere (capx D50's carbon-price asymmetry; the fuelvintage retiree window
being live in 2022 and exactly 0.000000 TWh in 2023–2025): **the direction of the evidence is not
under the lane's control, which is what makes it evidence.**

Reported at full magnitude, in both directions: **2024 C1 ST_GAS gets worse, by 0.041 TWh**, and
the four non-ST_GAS C1 classes get marginally worse in both years (≤0.046 TWh, against bands of
3.8–4.0 TWh). None of it is a flip; all of it is a cost.

---

## 3. C3b WAS NOT MEASURED — three blockers, and the general lesson

This is the second span in a row where a pre-registered price-shape check went unmeasured, and
the reasons are worth recording because **each fix exposed the next blocker**:

1. **Screen shard (RESULT §5):** the solve path writes no `metrics.json` — that is the
   registration path's job. *Fix attempted:* tell the shard to run the scorer itself.
2. **Span shard (SHARDREPORT §3):** `calibration_verdict.py` resolves **registered** runs only
   (*"could not resolve a registered run … no registry sidecar and no bundle match"*, all five
   invocations). Registration is precisely what rule 32(c) forbids a shard to perform, so **no
   shard can score an unregistered bundle by any flag combination.** The span addendum's claim
   that instructing the shard to run the scorer would close the S4 gap was **wrong**, and the
   shard was right to report it rather than work around it. *Fix attempted:* have the shard push
   its three `system_*.parquet` (2.48 MiB) so the parent computes C3b directly.
3. **Retrieval:** the shard's `git add -f` on gitignored parquets was **refused by its permission
   classifier**, and a shard has no human to approve it. **That decision was not routed around.**

**The general lesson, which is not about this arm:** an **unregistered, gitignored bundle on an
ephemeral container cannot be price-shape-scored by any route this architecture offers.** The
only clean fix is the one rule 15 `[R-DASHBOARD]` already prescribes — a completed full-span run
gets **registered**, which both creates the artifacts the scorer needs and puts the bundle
somewhere durable. Registration must happen where the bundle is, or the bundle must be
retrievable.

**What is NOT claimed.** The parent validated a C3b reconstruction from `system_*.parquet` that
reproduces the scorer to **±0.002** (0.1221 / 0.1769 / 0.1596 against the scorer's 0.122 / 0.179 /
0.160) — but with no arm sidecar there is nothing to apply it to. **C3b is UNMEASURED, not
inferred and not passed.** The live risk is concrete: **2024's 0.179 leaves 0.021 of headroom**,
nyiso-202 already named C3b-2024 *"the tightest remaining margin … the first thing a successor
lane watches"*, and a 0.002 reconstruction error would itself be 10 % of that headroom. **A
determination cannot be declared on this span while a load-bearing criterion is unmeasured**, and
none is declared here.

---

## 4. Rules

- **Rule 1 `[R-STRUCT]`** — the value was fixed ex ante, declared before the solve, never swept;
  §2 is the positive evidence that no fitting occurred. `authorized_price_tuning` = **NONE**.
- **Rule 13/14** — measured basis, forward-regenerable, no outcome pinned.
- **Rule 16 `[R-ALLYEARS]`** — one invocation, one bundle, all three years.
- **Rule 21 `[R-DOF]`** — the moved coefficient remains a ledgered free parameter.
- **Rule 23 `[R-FROZEN-DERIVE]`** — no source-data trigger, and none claimed.
- **Rule 29(b)/(c)** — form-4 control, no control solve; bundle gitignored, never registered,
  branch never merged.
- **Rule 31 `[R-RETAIN]`** — **nothing deleted.** §5.
- **Rule 32 `[R-SHARD]`** — parent ran no LP; one shard, 18 m 20 s, inside the 20-minute unit;
  the stop condition did not fire, so no continuation shard was owed.

---

## 5. RETENTION AND THE OPEN QUESTION

**The span bundle `results/calibration/nyiso226_span/` exists ONLY on the shard's container**
(gitignored per rule 29(c)/31, deliberately not deleted). **It will not survive reclamation.**
Every number this session will ever cite is in this document and in
`docs/SHARDREPORT-nyiso226-span.md`; the record is the doc, never the parquet. Reproducing the
span costs ~18 minutes of LP.

**PROMOTION IS THE OWNER'S CALL AND IT IS OPEN.** The nyiso-222 precedent is directly on point: a
full-span candidate was **registered without being promoted**, and the owner ruled on it
afterwards. That route needs the bundle, which is the retrieval §3 could not complete.

My recommendation, offered as one and nothing more: **the arm is sound but not yet decidable.**
It is a genuine rule-14 construction repair with zero new fields, exact confinement, a footprint
that landed within 7 % of its pre-registered prediction, C8 improving in all three years, and
two-sided evidence that it is not fitted. Against that: it **moves a frozen coefficient with no
source-data trigger** (the rule-21 admissibility question nyiso-203 refused to answer alone and
which is still unruled), it makes 2024's C1 ST_GAS worse, and **C3b — the tightest-margin
criterion — is unmeasured.**

