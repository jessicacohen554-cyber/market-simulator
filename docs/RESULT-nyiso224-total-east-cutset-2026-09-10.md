# RESULT — nyiso-224: the 2022 object is CONFIRMED; the arm is REJECTED on its own gate

**Session:** nyiso-224 · **ISO:** NYISO · **Date:** 2026-09-10
**Arm:** `nyiso_total_east_cutset_ttc=true`, **2022 screen only** (rule 29 `[R-SCREEN]`)
**Pre-registration:** `docs/PRECOMMIT-nyiso224-total-east-cutset-2026-09-10.md`, pushed at
`3215d7c1114f9d401dcc65bb6b48c157ce01b8c7` **before the first LP**.
**Control:** the committed keeper-recipe 2022 touchpoint `nyiso_fuelvintage_H2`
(G-CTRL form 4, G-DRIFT all hunks INERT). **No control solve was spent.**
**Execution:** rule 32 `[R-SHARD]` — one shard, one year; the parent ran no LP.
**Keeper UNCHANGED** (`2026-09-09-nyiso-221-fuelvintage-span`). **Nothing registered on the
dashboard** (rule 29 clause 2: a screen bundle is never a keeper and never a registration).

---

## 0. The headline, in two lines

**The diagnosis is CONFIRMED BY SOLVE: this one link carries essentially the whole 2022 C3a
miss.** Relieving it moves the ISO load-weighted price **+$8.81/MWh** and takes C3a from
**−13.00 % to −2.04 %**.

**And the arm is REJECTED anyway, on the structural gate it registered against itself.** It
does not land the model inside the measured congestion band — it **overshoots past it to the
other side**. Rule 1 `[R-STRUCT]`: the residual is not the gate, and an eleven-point C3a gain
does not buy a structure that is wrong in a new direction.

---

## 1. The gates, as registered

| gate | registered bar | control | **arm** | verdict |
|---|---|---|---|---|
| **G-1** separation share (`NYC − Upstate > $20`, Feb–Jun+Sep) | land in **[8 %, 60 %]** | 97.08 % | **2.06 %** | **FAIL (went inert)** |
| **G-2** the $1.40 pin (`Upstate < $5`, same months) | fall **below 15 %** | 42.89 % | **0.00 %** | **PASS** |
| **G-3** confinement to the one TTC column | no other link limit moves | — | only `Upstate_West→Capital_Hudson` moved | **PASS** |
| **G-4** direction not selectable | upstate **up** and downstate **down** | — | Upstate **+39.67**, NYC **−7.37** | **PASS** |
| **G-5** no non-target load-bearing flip | none | — | **COAL_PRB 0.655 → 1.268 TWh** vs a 0.00 benchmark | **FAIL** |
| **F-1** energy conservation | total move **< 0.05 TWh** | — | **+0.324 TWh** | **FAIL** |

**Three of six fail. The screen STOPS the arm and the remaining years were never spent.**

### 1.1 G-1 is a real failure, not an instrument artifact

The pre-registered instrument is a price-spread proxy, so the level is the check that matters:

| | mean `NYC − Upstate` spread |
|---|---|
| control | **$54.14** |
| **arm** | **$6.59** |
| **measured (2022 zonal RT)** | **$32.58** |

The control over-separates by 1.7×; the arm **under-separates by 4.9×**. The target was
between them and the arm flew past it.

**The direct instrument agrees that the arm moved the right lever and disagrees about how
far.** The arm's `network_2022.parquet` — an artifact the control bundle does not carry, which
is why G-1 was written as a price proxy — measures the link binding (`dual ≠ 0`) in
**12.47 %** of hours, against phase 0's pre-solve prediction of **9.85 %** and the market's own
binding sub-cutset at **10.0 %**. Mean armed flow **2,667.4 MW** against a measured TOTAL EAST
mean of 3,170.7 MW.

**This is reported, not claimed as a pass.** Had the flow gate been the registered one it would
have passed, and swapping instruments after the fact to convert a FAIL into a PASS is exactly
the selection rule 1 forbids. It is recorded because it says something the price gate cannot:
the **frequency** of binding is now roughly right while the **price consequence** is far too
small — so the defect that remains is not the limit's level.

### 1.2 What G-5 and F-1 caught

- **COAL_PRB 0.6554 → 1.2675 TWh** — nearly doubles, on a class whose EIA-923 benchmark is
  **0.00**. Upstate coal runs because upstate price rose; the arm makes an already-wrong class
  twice as wrong.
- **CC_CHP 13.4171 → 15.5065 TWh (+2.09)** — moves the *wrong way*. Downstate price **fell**
  $7.37, so a downstate class should back down. It does not, and this is unexplained.
- **F-1 +0.324 TWh.** Physically coherent (more transfer across an armed loss surface means
  more generation for the same load), but it is 6× the threshold registered against the arm,
  and the threshold stands as written.

### 1.3 What improved, stated at full magnitude so it is not buried

| | control | arm | actual |
|---|---|---|---|
| ISO LW model price | 69.917 | **78.730** | RT 80.368 · DA 77.432 |
| **C3a vs RT** | **−13.00 %** | **−2.04 %** | ±10 % band |
| Upstate_West | 33.712 | **73.378** | 60.61 |
| NYC | 89.170 | 81.796 | 93.19 |
| gas family TWh | 64.637 | **63.097** | 60.22 |
| CC_REGULAR TWh | 36.870 | **35.674** | 31.56 |
| model max price | 2,000.00 | **450.40** | — |
| VOLL slack | 360.5 MWh | **0.0** | — |

C3a would clear its band; the gas family and CC_REGULAR both move toward their benchmarks; the
$2,000 VOLL slack event disappears. **None of that is a reason to promote**, and the arm's own
pre-registered gate is the reason it is not.

---

## 2. What this session ESTABLISHED, and it is the durable result

**The 2022 C3a failure is an UPSTATE ZONAL failure caused by a cutset misalignment, and it is
now confirmed by solve rather than only by attribution.**

Phase 0 (zero LP) said `Upstate_West` carries **63.5 %** of the 2022 gap, at model **33.71**
against a measured **60.61**, because the model's single `Upstate_West → Capital_Hudson` link
— the A–E → F+ cutset, i.e. **TOTAL EAST** — is capped at the posted **CENT EAST** DAM TTC, a
nested sub-cutset carrying about half the flow. That cap sits **below the measured cutset flow
in 86.3 % of 2022 hours**.

The solve confirms it: relieving that one limit, **changing nothing else**, moves the ISO
load-weighted price **+$8.81** of the **+$10.45** the year was missing — **84 %** of the whole
2022 residual, from one link. No offer curve, no fuel, no fleet, no reserve parameter was
touched.

**Why 2022 alone fails on a chronic defect** (phase 0, unchanged): upstate pins at its cheapest
offer whenever the link separates, so the error is (downstate marginal cost − $1.40) × the
separated share, which scales with gas. The two high-gas years under-shoot (2022 −9.7 %, 2025
−5.7 % vs DA) and the two cheap-gas years over-shoot (2023 +2.6 %, 2024 +3.3 %).

---

## 3. Why the fix is NOT "pick a different quantile", and what the successor is

The correct limit is somewhere between **1,825 MW** (CENT EAST — 97 % separation, $54 spread)
and the **p90 TOTAL EAST envelope** (2 % separation, $6.59 spread), with the measured target at
**$32.58**. **Selecting that level by where the gates land is a swept free parameter and rule 1
`[R-STRUCT]` condition (c) refuses it.** It is not attempted here and should not be attempted by
the next lane.

The reason no single aggregate limit reaches the object is the one nyiso-169 named and this
screen has now demonstrated from both sides: **a five-zone radial chain cannot hold a nested
constraint.** Central-East is a sub-cutset *inside* Total East. Cap the link at the sub-cutset
and it binds always; cap it at the cutset and it binds almost never. Both are wrong because one
link cannot represent two nested boundaries.

**The identified successor is a TOPOLOGY change: split `Upstate_West` at the Central-East
boundary**, so the nested CENT EAST constraint and the parallel non-CE cutset paths become
separate links, each carrying its own posted limit with zero free parameters. That is an
owner-gated change and it is **named here, not attempted**.

---

## 4. Governance

- **Rule 1 `[R-STRUCT]`** — the gate was structural and was a STOP gate; it stopped the arm
  **against** an 11-point C3a gain. `authorized_price_tuning` = **NONE**.
- **Rule 13/14** — the basis; the misalignment exception is quoted verbatim in the PRECOMMIT.
- **Rule 21 `[R-DOF]`** — zero free parameters; the p90/month/25 MW construction was inherited
  from the armed `nyiso_seam_deliverability_envelope`, not chosen here. It is precisely because
  it was inherited rather than tuned that the arm was allowed to overshoot and be rejected.
- **Rule 29 `[R-SCREEN]`** — one year, screen year chosen on footprint (+2,054.6 MW, the largest
  of four); the span was **never spent**; the bundle is **never registered**.
- **Rule 30 `[R-MECH-MATRIX]`** — cell stamped **O → R** in `NYISO.js` this session, with the
  confirmed object and the successor recorded.
- **Rule 31 `[R-RETAIN]`** — **nothing deleted.** See §5.
- **Rule 32 `[R-SHARD]`** — parent ran no LP; one shard, pinned SHA, 7/7 config signature
  verified, ~18 min.

## 5. The artifacts, and the promotion question (rule 31 `[R-RETAIN]`)

> ### ⚠️ CORRECTION 2026-09-16 (session nyiso-238) — **THE BUNDLE DOES NOT SURVIVE.**
> Verified at `39174d6d`: branch `claude/nyiso224-cutset-2022` is **gone** (`git ls-remote --heads
> origin` returns four branches in total, none of them this one), so the paragraph below is false as
> written — "it is therefore in git and does not depend on either ephemeral container" no longer
> holds. This is rule 33 `[R-SHARD-ARCHIVE]` (f)(4)'s dead-recovery-line case. **The recovery route
> is a re-solve: ~4 min for 2022 alone, ~17 min for the full span**, as §5's last line already
> costed. The owner promotion question below was ruled on 2026-09-10 — **reject as constructed**
> (`nyiso_total_east_cutset_ttc` stays `False`, armed by nobody) — and nyiso-225 then closed the
> named successor, so nothing is pending on this bundle; it is recorded here so no later lane plans
> around bytes that are not there.

**The bundle SURVIVES.** The shard pushed it to branch **`claude/nyiso224-cutset-2022`**
(`results/calibration/nyiso224_cutset_2022/`: `run_config.json`, `meta.json`,
`legitimacy_diagnostics.json` and all seven `hourly/` sidecars including `network_2022.parquet`
and `unit_hourly_2022.parquet`). It is therefore in git and does **not** depend on either
ephemeral container. **That branch must not be merged to `main`** — rule 29(c) keeps a screen
bundle out of `main`, and the path is gitignored on the working branch for exactly that reason.

**THE OWNER HAS NOT RULED ON PROMOTION, AND THIS SESSION DOES NOT SELF-PROMOTE OR WITHHOLD.**
My recommendation is **do not promote as constructed** — the arm overshoots the measured
separation and doubles an already-wrong coal class. But rule 31 exists because that judgement is
not mine to act on, so the question is put explicitly:

1. **Reject as constructed** (my recommendation) — the object stands confirmed, the successor is
   the topology split, and `nyiso_total_east_cutset_ttc` stays default-off and armed by nobody.
2. **Charter the topology split** (`Upstate_West` divided at the Central-East boundary) as the
   next NYISO lane. It is the only route identified that reaches the object with zero free
   parameters, and it needs owner sign-off because it changes the ISO's zone count.
3. **Promote anyway on the C3a gain** — available, and I am naming it rather than hiding it,
   but it would be promoting a mechanism that failed its own pre-registered structural gate, and
   I advise against it.

Re-solving 2022 costs ~4 min of LP; the full 2022–2025 span ~17 min.
