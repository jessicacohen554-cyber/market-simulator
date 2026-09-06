# ADDENDUM nyiso-204b — three additions to the merged Capital_Hudson refusal: the narrowed **2480-only** fallback is foreclosed, the lay-up census **flags the limb's own backbone**, and 2625 is **Bowline**, not Bethlehem

**Parent (merged, PR #5199):** `docs/FINDING-nyiso204-ch-layup-exclusion-2026-09-06.md`.
**Session:** nyiso-204b, `claude/capital-hudson-exclusion-7uaogz`, 2026-09-06 — a **parallel lane
on the same object**, run independently and landing second.
**Keeper UNCHANGED: `2026-09-06-nyiso-202-startup-aware`.** ZERO LP. Nothing registered, no
`ScenarioConfig` field, no coefficient edit; `reliability_floor_coeffs_NYISO.csv` byte-unchanged.
**Rule 22 `[R-HOLDOUT]`:** 2023–2025 only. **Markers untouched** — owner acts.
**Instruments:** `scripts/probes/_nyiso204b_ch_exclusion_variants.py` →
`results/calibration/_nyiso204b_ch_exclusion_2480only.json` (`--exclude 2480`) and
`_nyiso204b_layup_census_cells.json` (`--census`).

**THE PARENT'S VERDICT IS UNCHANGED AND IS NOT RE-LITIGATED.** This lane reached the same
refusal independently and its numbers agree with the parent's exactly where they overlap —
zonal-target shrink **64.8 / 46.5 / 65.0 %**, collateral **88.0 / 99.5 / 97.7 %** onto 2625,
cure-to-disease **8.3× / 186× / 43×**. Nothing here reopens either ground. What follows is only
what the parent does not carry.

---

## 1. NAME CORRECTION — plant 2625 is **Bowline**, not Bethlehem

The parent names 2625 "Bethlehem 2625" twice (§0 and its matrix stamp). **2625 is Bowline**
(`bin_assignments_NYISO.csv` → `Plant_Name = Bowline Point`; the bridge lay-up artifact reads
`Bowline Generating Station`). **Bethlehem is 2539**, a `CC_REGULAR` — the plant the parent's own
sibling finding cites for the `+0.294 / +0.291` CF gap.

**This is a naming slip only. Every number attached to it is 2625's and is correct**, so no
conclusion moves. It is recorded because a reader chasing "Bethlehem" would land in the wrong
class and the wrong zone.

## 2. THE CENSUS FLAGS THE LIMB'S OWN BACKBONE — an independent route to the parent's ground (1)

The parent refutes the a-fortiori reading by **conditioning on the driver**: once you ask about
hot-day conduct rather than annual online share, the ordering *inverts* (2517's hot-day P(on) was
0.932; Roseton's is 0.56–0.79). That is correct and sufficient. There is a second, purely
census-side way to see it that needs no conduct measurement at all.

Re-deriving the **stricter** criterion the adjudicated bridge channel actually uses
(`derive_campd_bridge_layup_exclusions`: `median(grossLoad) == 0` in **every** (year, 4 h block)
cell — 6 blocks × 3 years = 18):

| plant | zero cells | annual online | qualifies "laid up"? |
|---|---:|---:|---|
| **2625 Bowline** | **18/18** | 0.2992 | **YES** |
| 8006 Roseton | 18/18 | 0.1463 | YES |
| 2480 Danskammer | 18/18 | 0.0294 | YES |
| *2517 Port Jefferson* | ***15/18*** | *0.3859* | ***no*** |

Two facts, both from the criterion alone:

1. **It would exclude 2625** — the plant carrying **92.2 / 99.8 / 98.5 %** of everything this limb
   forces, online **77.6 / 85.9 / 96.8 %** of the limb's own binding hours. A membership test that
   flags the backbone cannot prune this limb's membership.
2. **It does not select 2517** — the one plant the `reliability_floor_plant_exclusions` channel
   actually carries, and the reference the whole a-fortiori ordering was measured against.

So the census **does not identify lay-up in a seasonal class at all**. That is the general form of
the parent's inversion: the parent shows the ordering fails for these two candidates, and this
shows *why* — a whole-year zero-median statistic cannot separate "laid up" from "runs only in
summer", and Capital_Hudson steam is the latter, every plant of it.

## 3. THE NARROWED FALLBACK — **2480 alone** — is foreclosed here, so the next lane need not spend it

Once ground (1) refutes Roseton, the obvious next proposal is a one-plant arm. Measured on the
same instrument (`--exclude 2480`):

| year | zonal target ctrl → arm | shrink | total removed | **Δ off NON-candidates** |
|---|---|---:|---:|---:|
| 2023 | 76.7 → 65.1 MW | 15.0 % | 0.00581 TWh | **69.0 %** |
| 2024 | 175.5 → 163.5 MW | 6.8 % | 0.00519 TWh | **96.4 %** |
| 2025 | 150.7 → 144.0 MW | 4.5 % | 0.00404 TWh | **100.0 %** |

**Stated against interest: the parent's ground (2) is genuinely much weaker here.** A 4.5–15.0 %
target shrink is a different order from 64.8–65.0 %, and the narrowed arm is far closer to a real
membership correction. It still is not one: over three years it removes **0.01505 TWh** of which
only **0.00199 TWh** is 2480's own — a **6.6 : 1** collateral ratio — and in **2025 100 %** of the
effect falls on plants that are not candidates, in a year 2480 is not floored at all.

**Ground (1) is what decides it, and it is undiminished.** On the **engine's own** binding window
(`tmax > 31.1 °C` bridged at `min_event_hours = 48`, reproducing the binding-hour counts
**504 / 432 / 600** exactly), 2480's hot-day commitment probability is **0.125 → 0.255 → 0.370**
at a **5.7× → 17× → 41×** lift over its off-window rate — **and rising every year**. Rule 17
`[R-FLOOR-WINDOW]` asks whether a floor binds *"in hours its own driver evidence says the class is
offline"*; for a unit whose hot-day commitment probability is climbing toward 40 %, it does not.

**What 2480's D-4 rows actually say**, and it is worth recording precisely because it looks like
support for the arm: on the hours the cheapest-first fill *reaches* 2480 — 153 h in 2023, 23 h in
2024 — its meter reads zero **100 %** of the time. That is a statement about **which hours a
cheapest-first fill selects at the bottom of the stack**, not about whether 2480 belongs in the
class. The instrument it points at is the **fill order or the target level**, not the membership
column.

---

## 4. Disposition

**No verdict moves. The parent's refusal stands on both its grounds, and the DO-NOT-REDO now
covers BOTH forms of the arm** — 2480+8006 and 2480 alone. Rule 20 `[R-FORCED-BUDGET]` leg (a)
stays open and the nyiso-203b "cheapest route" to it stays closed. The NYISO matrix shard cell is
re-stamped with this increment in the same session (rule 26 duty (b)).

*(nyiso-204b, 2026-09-06. Zero LP. A parallel lane's increment, folded onto the merged refusal
rather than published beside it.)*
