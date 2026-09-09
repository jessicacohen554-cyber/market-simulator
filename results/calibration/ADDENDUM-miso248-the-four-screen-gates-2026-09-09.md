# ADDENDUM miso-248 (third) — **ALL FOUR SCREEN GATES PASS.** `G-1` 1.211×, `G-2` 16/16 confined, `G-3` exact on **both** arm and control, `G-4` zero flips. The full span is spent on **rules 23 / 14 and the ungated-anchor argument — not on the screen's authority**

**Governs:** what happens after the 2023 screen. **No bar in
`PREREG-miso248-the-spp-hourly-ladder-rederive-on-the-repaired-clock-2026-09-09.md` §7 is moved**;
the one bar that WAS repaired is `G-2`'s, and that repair was published in ADDENDUM 2 **before** the
repaired number existed, with the first-run failure preserved verbatim. Machine records
`results/calibration/_miso248_screen_gates.json` and `_miso248_g4_collateral.json`.

---

## 1. THE GATES

Screen year **2023**, selected by `argmax F` in phase 0 before any solve. Arm = the re-derived
offsets; **control = the EARNED control solve** (`G-DRIFT` found one LIVE hunk, so rule 29(b) form 4
is falsified — ADDENDUM 1 §5).

| gate | bar (PREREG §7) | measured | |
|---|---|---|---|
| **`G-1`** direction & order of magnitude | same sign as `ΔE_pred = +0.2085` TWh **and** ratio ∈ `[1/3, 3]` | **realised +0.252459 TWh · ratio 1.2108 · same sign** | **PASS** |
| **`G-2`** confinement (zero LP) | only SPP rows move, by exactly `δ_new − δ_old`, hour-constant | **16 of 48 rows moved, all SPP; 0 non-SPP; every delta and hour-spread ≤ 1e-9** | **PASS** |
| **`G-3`** applied identity in the SOLVED year | `mc = hub(t) + δ_k` at `atol 0.01`, **both** bundles | arm: 16 rows, **0** violating hours, max err **1.4e-05**; control: 16 rows, **0**, **1.3e-05** | **PASS** |
| **`G-4`** collateral | zero load-bearing PASS → FAIL flips | **0 flips** | **PASS** |

**`G-1` is the one that could have killed the arm and did not.** The pre-solve prediction was a
first-order calculation on the keeper's frozen internal price (declared as such, in advance); the LP
re-priced and landed **1.21×** it. **That is a closer agreement than this lane has any right to
expect** — miso-247's four in-scope classes ran 0.52–3.28× — and I state it as luck as much as
design: a single seam's 16 rows is a far simpler object than a fleet-wide fuel-cost repair.

**The SPP seam's own energy, at full magnitude** (from each bundle's own `unit_hourly`, so the
fallback that pools all four seams never fired):

| | import | export | **net import** |
|---|---:|---:|---:|
| control | 1.890700 | −0.713433 | 1.177267 |
| **arm** | 2.432965 | −1.003238 | **1.429726** |

**Both directions grew**, exactly as phase 0 §3 said the offsets' structure implies (every import
offset fell, every export offset rose). The seam is more active in both directions, and the net moves
+0.2525 TWh toward import.

## 2. `G-4`'s MOVES — reported at full magnitude, gated in neither direction (rule 1 `[R-STRUCT]`)

**Zero flips. Eleven scored bands move, and they do not all favour the arm:**

| toward | away |
|---|---|
| `CT_PEAKER` −0.687 → **−0.563** | `CC_REGULAR` −6.306 → −6.562 |
| `COAL_BIT` −3.356 → **−3.305** | `CC_CHP` −1.986 → −2.026 |
| `COAL_PRB` −2.619 → **−2.594** | `ST_GAS` +0.171 → +0.208 |
| system **coal** volume −6.54 → **−6.46** | `ST_CHP` −2.741 → −2.745 |
| | `COAL_LIGNITE` −0.714 → −0.715 |
| | system **gas** volume −11.55 → −11.69 |
| | **mean price 1.69 → 1.71** |

**Mean price moves AWAY**, and it is named here rather than left in the machine record. **Not
scorable at a screen:** `governance` (no attestation on a replayed bundle), the `da_diagnostic` price
mean and two `forced_share` rows (SKIPPED on both sides).

**A note against the temptation to read this as vindication.** MISO's coal deficit — the successor
object miso-247 handed forward — moves **toward** here on three of its bands. **That is a
by-product, it was not targeted, it is 0.03–0.08 of a band, and it is one year.** It closes nothing
and it is not a reason for anything. The 2024/2025 direction is the opposite sign on `ΔE_pred` and is
measured in the full span, not asserted here.

## 3. **WHY THE FULL SPAN IS SPENT — the authority is named, and it is NOT the screen's**

Rule 29 `[R-SCREEN]`'s screen is **STOP-only**: it may kill an arm and may never promote one. It did
not kill this one, which authorises nothing by itself. What carries the full span, stated so a reader
can reject either:

1. **Rule 23 `[R-FROZEN-DERIVE]` — the licence, with the trigger cited.** `86e45462` repaired the
   source series the ladder is Q-Q coupled against. Re-deriving on a source-data change is what rule
   23 *is*; the commit is cited, the residual is not consulted, and there are **zero free
   parameters**.
2. **Rule 14 `[R-ACCURATE]` plus the UNGATED ANCHOR.** `measured_miso_spp_hub_prices` reads the same
   repaired file and carries **no `ScenarioConfig` field and no cache-key entry**, so **every future
   MISO solve carries the repaired anchor whether or not it carries repaired offsets**. Between the
   repair and this re-derive the applied offer is a MIXTURE — repaired-clock anchor, pre-repair-clock
   offsets — and the pre-repair posture is **not available to keep**. This is the same structural
   shape that made miso-247's `_apply_simple_cycle_hr_floor` non-declinable.
3. **Rule 16 `[R-ALLYEARS]`.** A determination cannot be produced from a one-year screen at all, so
   answering the promotion question requires 2023–2025 in one invocation and one bundle. The screen
   bundle is a throwaway probe and its year is re-solved inside the full bundle.

**WHAT IS NOT CLAIMED.** The gates passing is **not** evidence that the arm scores better, and no
gate above reads a residual. Whether the resulting bundle is promoted is the **owner's** decision.

## 4. Non-claims

1. **`G-2`'s first-run failure is not withdrawn**; it is ADDENDUM 2, published before its repair, and
   the repair was declared before the repaired number.
2. **No bar was moved for `G-1`, `G-3` or `G-4`.**
3. **`G-1`'s agreement at 1.21× is reported, not claimed as skill** — the prediction is first-order
   and a factor-of-three band is all it was ever asked to detect.
4. **Every band move is reported both ways**, including mean price moving away.
5. **Nothing here is registered, promoted or scored as a determination.** 2023–2025 only; no marker
   sought or implied; C3c untouched and a target in neither direction.
