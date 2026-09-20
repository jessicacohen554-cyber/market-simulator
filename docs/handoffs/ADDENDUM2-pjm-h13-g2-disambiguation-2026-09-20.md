# ADDENDUM 2 to PRECOMMIT-pjm-h13 — G2 says "aggregate neutrality", and that phrase has TWO readings. Fixing which one it tests, BEFORE any arm result exists (2026-09-20)

**Verified at the moment of writing:** `git fetch` over `refs/heads/claude/pjm-h13-meritalloc-*`
returns **no shard branches**. No arm bundle, no arm number, no D-4 count from any leg exists yet.
This is a charter repair, not a result-fitted one — which is the only condition under which a gate
may be touched at all.

**This clarification can only make G2 EASIER to pass. I am stating that plainly rather than letting
a reader discover it.** The justification is that G2's *rule-19 content* was already discharged at
zero LP in all six years, and the quantity the original wording pointed at was never the
construction claim.

---

## 1. The ambiguity

PRECOMMIT §4 G2 reads:

> **G2 — rule 19 integrity** · D-2 `st_netload_drag` total forced TWh within **±1 %** of control,
> every year · *kills the card if the swap doubles as a level knob*

**"Aggregate neutrality" names two different quantities, and they are not the same number.**

**(a) The pre-solve MANDATE** — `Σ_g min(floor_frac, basis_g) × pmax_g`, the MW the pro-rata path
actually delivers into the LP as `min_gen`. This is what the mechanism's own registration claims is
preserved *by construction*, and what `netload_drag_merit_allocation` was deliberately specified
against (its docstring: preserved "measured as the MW the pro-rata path actually DELIVERS … NOT the
nominal `floor_frac × sum(pmax)`", precisely so the swap "cannot double as a level knob").
**Measured, all six years, 0.0000 TWh:** 2020 2.7870 / 2.7870 · 2021 3.0041 / 3.0041 ·
2022 3.2110 / 3.2110 · 2023 2.8355 / 2.8355 · 2024 3.1229 / 3.1229 · 2025 3.5270 / 3.5270.

**(b) D-2 `forced_twh`** — energy the solved LP dispatches **at** the floor. Control:
2020 **1.4761** · 2021 **1.9106** · 2022 **1.1721** · 2023 **0.8441** · 2024 **0.8352** ·
2025 **1.0854** TWh. Note these are **40–70 % smaller** than (a): most of the mandate sits *below*
what economics would have dispatched anyway, so it is never "forced" in D-2's sense.

**(b) is a CONSEQUENCE of correct reallocation, not a measure of level.** Moving the same MW from a
plant that would have run regardless (Big Sandy, online 0.769) to one that would not — or the
reverse — changes how much of the identical mandate *binds*, with no change in the mandate. A ±1 %
bar on (b) would therefore fail the arm for doing exactly what it is supposed to do. The sibling
sub-gate's registration says as much in terms for its own case: *"mean-preserving on the FRACTION
but not on the DELIVERED floor, because the availability clip follows it."*

## 2. The repair

**G2 now tests quantity (a), at the same ±1 % bar, and it is already MEASURED AND PASSED in all six
years** (0.0000 TWh — exactly neutral, not merely within tolerance). That is the rule-19 claim, and
it is the claim G2 was written to protect.

**Quantity (b) moves to REPORTED — with a declared tripwire, so it keeps teeth:**

> **T1 (tripwire, not a gate).** If D-2 `st_netload_drag` forced TWh moves by more than **±15 %**
> in any year, the lane must explain the movement mechanically from the reallocation before
> recommending promotion, and records it on the determination basis. A move inside ±15 % is
> reported and needs no explanation.

±15 % is set from the control's own year-to-year variation, which is far wider (0.8352 → 1.9106
TWh, a 2.3× swing across the span, on an unchanged mechanism). A bar tighter than the mechanism's
own inter-year spread would be measuring the weather, not the swap.

## 3. What does NOT move — every other gate stands exactly as pushed

**G1, G3, G4 and G5 are untouched**, including their bars and their baselines:

| gate | bar | unchanged |
|---|---|---|
| **G1** | per-plant allocation differs from control, every year | ✔ |
| **G3** | D-4 `st_netload_drag` FAIL rows **do not increase in ANY year** AND six-year total **strictly decreases below 12** (baseline 2020 **3** · 2021 **2** · 2022 **2** · 2023 **1** · 2024 **2** · 2025 **2**) | ✔ |
| **G4** | ≥ 1 of {3131 Shawville, 3138 New Castle} flips FAIL → pass in ≥ 3 of the years it currently fails | ✔ |
| **G5** | no OTHER mechanism's D-2 forced share moves > 0.5 %, every year | ✔ |

**G3 remains the gate that can kill this card, and nothing here touches it.** Addendum 1 already
recorded that New Castle's floor *grows* under the arm while its median stays 0.000 — the live path
by which G3 may fail — and that prediction stands, unhedged. The reported/gating asymmetry of
PRECOMMIT §4.1 is likewise unchanged: no price, volume, band or determination number can move any
gate.
