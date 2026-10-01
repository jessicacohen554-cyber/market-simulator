# RESULT miso-172 (arm 2) — the p25 LEVEL basis: ALL GATES PASS, **PROMOTED TO KEEPER**, and C8-2023 is CLEARED

**Session miso-172, 2026-08-20.** Executes
`PREREG-miso172-p25-level-basis-2026-08-20.md`, committed before either arm
result was read. Control `miso172_control`, arm `miso172_p25mw`, both
`--year 2023 2024 2025` sequential in one invocation (rules 12/16).

**Outcome: EVERY PRE-REGISTERED GATE PASSES. Promoted to keeper
`2026-08-20-miso-172-p25mw` on the arm's own gates — the structure-over-gates
clause was NOT needed and is not invoked.** MISO's determination goes from
**NOT-YET on C3a-2025 + C8-2023** to **NOT-YET on C3a-2025 ALONE**.

## 1. The defect, and why the census is a proof rather than an assertion

The frozen deriver measures

```
acf     = net_MW / (nameplate × avail_mult)      # avail_mult is HOURLY
p25_cf  = percentile(acf[online], 25)            # a fraction of AVAILABLE capacity
```

and `campd_bins.thermal_tranche_p25_level` reconstructed the runtime floor LEVEL
as **`p25_cf × nameplate`** — dropping the very `avail_mult` the statistic was
divided by. Every plant with a deep availability derate was therefore over-floored
by `1 / avail_mult`.

Measuring the **same percentile of the same online sample directly in MW** over
all 134 MISO rows:

> **88 of 134 agree to within 0.1 %** — exactly the plants with **no** derate,
> where `avail_mult = 1` makes the two bases algebraically identical — while
> **25 of 134 are ≥ 1.10×, every one of them derated** (1402 Little Gypsy
> **2.594×**, 1122 Ames **2.220×**, 2070 2.03×, 3459 Sabine **1.726×**).

Nothing but a dropped `avail_mult` produces that split. A fitted adjustment moves
everything it touches; this moves only the plants whose basis was actually
dropped, by exactly the dropped factor.

## 2. Governance

* **Rule 23 `[R-FROZEN-DERIVE]` satisfied with the frozen deriver UNTOUCHED** —
  zero bytes; its pooled artifact is **not** regenerated. The new script
  (`scripts/data/derive_thermal_tranche_p25_level_mw.py`) **imports** the frozen
  online mask, parasitic-factor net, derate source, fleet nameplate/primary-group
  attribution and pooled window, so it is provably the same statistic on the same
  sample. An additive side artifact on the **same pooled window** — the only
  thing a consumer sees change is the BASIS.
* **Rule 21 `[R-DOF]`: ZERO new free parameters.** `n_scalars` 0; the attestation
  carries 33 ledger entries / 2 residual, unchanged from the predecessor.
* **Rule 14 `[R-ACCURATE]` governs**, and is why the instrument is a LEVEL repair
  and **never** an exclusion: Ames's floor is right in kind (a real municipal
  self-commitment) and wrong in LEVEL. Fix the measurement, never delete the plant.
* **Rule 19 `[R-ONE-MECH]`:** the level SOURCE is replaced. Membership, window,
  mechanism id and the cheapest-first `pmax × availability` clip are untouched;
  no second floor is stacked.
* **Rule 13:** a pooled multi-year percentile of measured operation — the same
  admissible family as `p25_cf` itself, same forward story (it re-derives from
  each new CAMPD vintage). Registered backcast-only.
* **Rule 22:** no year outside 2023–2025 was solved, scored or registered; MISO
  holds neither `complete` nor `final`, the spend freeze is untouched, and no
  marker re-key is owed (D-5(b) applies to `complete` ISOs only).
* **Leave-one-year-out is vacuous here, and that is argued rather than assumed.**
  Rule 22's LOO requirement targets *overfitting* — in-sample gain with held-out
  degradation. This mechanism has **zero free parameters**: the level is a
  measured percentile of a plant's own CEMS sample, identified per plant and
  never against any year's residual, so re-deriving on two of three years would
  simply re-measure the same statistic. The evidence LOO exists to produce is
  present directly — the improvement is **uniform across all three years**
  (share −5.9 / −6.1 / −7.4 pts; Ames error improving every year; every mover
  moving every year by the same basis ratio). A gain concentrated in one year
  would be the red flag; there is none.

## 3. The gates, as scored

| gate | verdict | measurement |
|---|---|---|
| **K-0** control inertness | **PASS** | 12/12 scored sidecars, all years, `max\|diff\| = 0.0` vs the committed keeper — both new miso-172 mechanisms are provably byte-inert when off |
| **L-1** level exactness | **PASS** | unit grain: 1122 **73.26 → 33.00 MW**, 1402 137.48 → 53.00, 3459 493.96 → 286.15, 3457 141.80 → 113.49; the three underated plants unmoved (1403 724.00, 990 226.40, 6035 89.00) |
| **L-2** liveness | **PASS, all three years IN band** | Δ D-2 forced TWh **−1.6964 / −1.7245 / −2.1946** vs `[−2.232,−0.744]` / `[−2.222,−0.741]` / `[−2.867,−0.956]` |
| **L-3** Ames dispatch | **PASS** | model vs its own meter: **+64.8 / +74.5 / +92.9 % → −17.6 / −18.1 / +3.1 %** — toward the meter in every year, overshooting in none |
| **K-3** conduct failures | **PASS** | 2 → 2, **ZERO NEW**, zero new off-window |
| **K-5** record flips | **PASS** | 67 records, **ZERO** PASS → non-PASS flips |
| **K-6** ST_GAS shape | **PASS** | `profile_r` 0.947 / 0.961 / 0.981 — 2024–25 **improve** on the control; `cv_ratio` 1.607 / 1.222 / 1.452 |
| per-plant direction | **PASS 21/21** | 12/12 mover plant-years down by their measured basis ratio; 9/9 non-mover plant-years flat within 1.2 % |

## 4. What moved

**Total ST_GAS forced share 30.53 / 30.93 / 42.56 % → 24.59 / 24.88 / 35.16 %**,
taking **2023 and 2024 below the rubric's 30 % merchant cap**.

**C8 goes FAIL → PASS** (2023 ST_GAS FAIL → PASS). That single record is the
**only** change in the entire 67-record scorer output.

**Determination: NOT-YET on C3a-2025 ALONE**, C3c the single ledgered caveat,
governance PASS on a fresh attestation — against the predecessor's NOT-YET on
C3a-2025 **plus** C8-2023.

## 5. The blocker was cleared by the mechanism nobody expected — stated plainly, because the successor depends on it

Three prior sessions diagnosed C8-2023 as a **window** defect on plant 1402, and
this session's **own arm 1** (`mustrun_online_frac_per_year`, run
`2026-08-20-miso-172-peryear`, REJECTED-AS-ARMED on its K-2 band) attacked it
head-on and **did not clear it**: 1402's metered zero-share over its binding
hours fell **71.17 % → 52.19 %**, missing the rider's 50 % threshold by **2.2
percentage points**.

Arm 2 never touches 1402's window and clears C8 anyway — because taking the
**class** below its 30 % budget removes the escalation regime in which the
provenance leg, and hence 1402's conduct row, is consulted at all (rule 20:
the provenance+shape path is only reached *above* the cap).

**1402's window defect is REAL and UNREPAIRED.** It is not bought off; it is
simply no longer load-bearing for C8. Its own D-4 conduct row still FAILs in
2023 and is visible in this keeper's committed
`legitimacy_diagnostics.json`.

## 6. Reported against interest

* **C3a-2025 is unchanged and still FAILS.** Nothing here is claimed against the
  miso-163 owner ruling or the miso-171 end-to-end decomposition.
* **The latent CC/CT leg of the same defect is measured and NOT armed:**
  CC_REGULAR max 2.03×, CT_PEAKER max 1.50×, inert at MISO because the keeper
  runs `cc_mustrun_per_plant=False`. Arming that leg is a different mechanism
  under a different charter (rule 19); the cross-ISO half is a per-ISO hand-off
  (rule 25) — each ISO needs its own artifact and its own A/B.
* **The committed-vs-regenerated diagnostics exposure** is present in this
  session's control and is disclosed, not created here: with dispatch
  bit-identical, regenerated `reliability_floor` moves ST_GAS
  0.1663/0.2152/0.2295 → 0.0000/absent/0.0001 TWh, CT_PEAKER
  1.7909/1.7223/1.6453 → 2.0873/1.9592/1.9872, CC_REGULAR 0.1301/0.0217/0.1124 →
  absent, and it manufactures a D-4 conduct FAIL on plant 990 carrying
  **0.0000 TWh across ONE binding hour** ("100.0 % of the mechanism's forced
  energy"). It does not contaminate the A/B — `st_gas_mustrun_per_plant`
  reproduces exactly (7.2596/7.3357/9.3426 TWh) and every gate compares
  regen-control to regen-arm through the same path at the same HEAD.

## 7. Follow-up owed

`calibration-keeper-auditor` should be run against `--iso MISO` to confirm the
Calibration Status page and per-keeper report headers match this promotion. It
was **not** run in this session (agent invocation was outside the session's
standing instruction) and is carried forward explicitly rather than assumed done.
