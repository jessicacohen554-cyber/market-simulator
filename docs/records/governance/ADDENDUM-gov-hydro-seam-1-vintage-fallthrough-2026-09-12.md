# ADDENDUM (gov-hydro-seam-1): the PRECOMMIT's early-release fall-through was
# INSUFFICIENT — measured, and repaired on structure before any effect number

**Session** `gov-hydro-seam-1` · **Date** 2026-09-12 · **ZERO LP.**
Amends §0 decision 1 of `docs/PRECOMMIT-gov-hydro-seam-1-2026-09-12.md`.

---

## 1. WHAT THE PRECOMMIT SAID, AND WHAT THE MEASUREMENT SAID BACK

The PRECOMMIT named the cost exactly and proposed a fall-through: a folded ISO-year
whose EIA-923 vintage is an early release routes to the **existing** `ann930 <= 0.0`
carry-forward (the nyiso-106 repair), on the argument that an inadmissible authority
should be handled as an absent one.

**Measured, that fall-through DOES NOT FIRE, and the reason is structural.** The carry's
trigger is `_vintage_completeness` — an **ISO-TOTAL** ratio, EIA-923 net generation over
EIA-930 `net_gen`. In 2025 it reads:

| ISO | ISO-total vintage completeness | **hydro class's OWN coverage** | carry fires? |
|---|---:|---:|:--:|
| **PJM** | **0.9233** | 2.2898 / 8.8612 = **0.258** | **NO** |
| **MISO** | **0.9230** | 0.9697 / 9.0414 = **0.107** | **NO** |
| NEISO | 0.8278 | 0.0907 / 6.7136 = 0.014 | yes (but NEISO 2025 is post-split, not folded) |
| CAISO | 0.7331 | — | n/a (not folded) |
| NYISO | 0.8850 | — | n/a (not folded) |
| SPP | 0.8040 | — | n/a (not folded) |
| ERCOT | 0.9372 | — | n/a (no PS fleet) |

The early 2025 monthly release covers the large fossil and nuclear plants that carry
almost all of the MWh, and omits the long tail of small hydro (PJM files **10 of 72**
hydro plants, MISO **14 of 160**). So the ISO total reads 92 % "complete" while the hydro
class is 11–26 % filed. **A class-blind completeness measure cannot detect a
class-specific truncation** — and because it reads *above* the 0.90 threshold, the carry
is never even attempted.

**Left as written, the repair would have scored PJM 2025 hydro against 2.2898 TWh**
against a conventional population of ~8.9 — a **−74 %** error replacing the +74 % error it
was fixing. That is precisely the "worse defect than the one you are fixing" the
commissioning handoff named, and it is a **STOP**, not a detail.

## 2. THE THREE SCALARS, AND WHY TWO OF THEM ARE UNUSABLE

A carry-forward needs a scalar for "what fraction of this class's energy is filed". Every
candidate available without the missing data is **measurably wrong for this class**:

* **ISO vintage completeness (0.923)** — wrong by construction, as above; it is a measure of
  the *fleet's* filing, dominated by plants that are not hydro.
* **Plant-census fraction (PJM 10/72 = 0.139)** — wrong in the other direction: the filed
  plants are not a size-random sample, so `2.2898 / 0.139 = 16.5 TWh` against a modal ~8.9.
* **Prior-year energy, unscaled (8.8612)** — not a scalar at all but a *substitution*; it
  asserts 2025 hydro ≈ 2024 hydro, i.e. it puts a **climatological estimate where a scored
  actual belongs**. An actual that is a climatology tells a reader nothing about the year
  being scored, which is the one thing a backcast benchmark exists to say.

**There is no defensible scalar.** That kills the carry construction for hydro outright —
not because the numbers came out badly, but because the instrument does not exist.

## 3. THE REPAIR — refuse the swap only where refusing it is unambiguously a repair

> **The `NG: WAT` swap is refused when the ISO-year is BOTH pumped-storage-folded AND its
> own EIA-923 `HY` plant census is COMPLETE. Otherwise the swap stands.**

The second predicate is the repo's **already-adjudicated** hydro-census gate,
`data.hydro.complete_923_hydro_years` (miso-109's "2025 trap", miso-110) — a per-ISO check
that a year's `HY` filing reaches `EIA923_COMPLETE_FILING_CENSUS_FRACTION` of the ISO's
modal census and is no newer than `EIA923_LATEST_FINAL_VINTAGE`. It is a data-quality
filter that *can only ever remove* a year; it is the same instrument the model side already
uses to keep an early release out of its own hydro level. **Rule 19 `[R-ONE-MECH]`: the
second end of the comparison reuses the second predicate too, rather than inventing one.**
Measured, it returns exactly the right verdict with no tuning: **2020–2024 complete in all
seven ISOs, 2025 incomplete in all seven.**

**Why this is the right shape and not a retreat:**

* **It never replaces a measurement with a worse one.** Where the 923 census is complete the
  repair swaps a wrong-population *measurement* for a right-population *measurement*. Where
  it is not, there is no right-population measurement to swap to, and the repair declines.
* **Zero estimation enters a scored actual.** The benchmark stays a measurement in every
  ISO-year. No carry, no scalar, no free parameter (rules 21 / 24).
* **It is SELF-HEALING, which is the property that makes the residue acceptable.** When the
  final 2025 EIA-923 vintage lands, `EIA923_LATEST_FINAL_VINTAGE` advances and the census
  fills; the predicate flips to complete and the repair applies to 2025 **with no code
  change and no re-adjudication**. The residue is a data-vintage state, not a design
  compromise.
* **A per-year source basis is the adjudicated pattern, not a new one.** neiso-72 refused a
  *mid-year* splice and explicitly accepted a *year-to-year* basis change ("a year is
  admissible on ONE source basis only"). PJM reading 923 `HY` for 2023/2024 and `NG: WAT`
  for 2025 is that same construction.

## 4. THE COST, STATED AT THE GATE AND NOT ABSORBED

**PJM 2025 and MISO 2025 keep the pumped-storage-contaminated hydro actual.** They are the
only two cells in the whole matrix where the seam is diagnosed and left unrepaired (NEISO
2025 is past its `EIA930_PS_SPLIT_COMPLETE_FROM` year and is not folded at all; no other ISO
is folded). Those two cells are **reported, never quoted as repaired**, and their named
successor is the final 2025 EIA-923 vintage — which discharges them automatically.

Any run scored on 2025 in PJM or MISO therefore still compares a conventional-hydro model
against a conventional-plus-PS meter in that one year. That is the status quo for that cell,
made **no worse**, and now documented on the row rather than invisible.

## 5. THE PRE-REGISTERED STOP GATES ARE UNCHANGED

G1–G4 of the PRECOMMIT stand exactly as written; this addendum changes the construction
inside decision 1, not what the change must prove. **G1 and G2 were already measured PASS
before this addendum was written** (G1: 366 rows move, all `WAT`/`PS`, zero reaching a gas
class, zero `mixed_fossil_plants` delta; G2: injected `OTHER` must-run moves 0.000000 MWh in
all 42 ISO-years, and there are zero over-filter rows). **G3 was measured PASS**
(`check_cache_key_registration --base origin/main` clean; `moved_rows` byte-identical at
`origin/main` and at the arm for all seven ISOs — the two rows that do show,
`NUCLEAR_MONTHLY_CF_BY_YEAR` and `STATE_CARBON_PRICE_BY_ISO`, are pre-existing and another
lane's). G4 is measured after this repair lands.

Also recorded before the effect was read: **the control regeneration reproduces every
committed bench `classFull.hydro` to 4 dp in every ISO-year**, so the hydro row carries
**zero** pre-existing drift and every delta reported later is attributable to this change
alone.
