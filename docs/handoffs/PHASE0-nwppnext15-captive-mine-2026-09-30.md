# PHASE 0 — NWPP-NEXT-15: captive-mine marginal coal fuel cost (zero LP)

Follows `DESIGN-nwppnext14-captive-mine-marginal-fuel-2026-09-30.md` §4. Design only: no field, no solve.

## §1 Captive-identification rule — FIXED BEFORE THE CENSUS WAS READ

Committed in its own commit, before `scripts/probes/_nwppnext15_captive_census.py` was run. Nothing below §1 existed
at that commit.

**Source:** EIA-923 Page 5 receipts, `data/raw/coal-receipts/coal_receipts_<Y>.csv` (verbatim columns). Zero DOF: every
input is a filed field; no per-plant list, no ownership map, no threshold tuned to anything.

**A receipt row is CAPTIVE iff all three hold:**

1. `Primary Transportation Mode` is a mine-mouth mode: `CV` (conveyor) or `TR` (truck) — the mine delivers without a
   common carrier;
2. `Coalmine State` == `Plant State`;
3. `Purchase Type` is not `S` (spot) — a spot purchase is by definition not a dedicated supply.

Every other coal row is **NON-CAPTIVE** (rail, barge, pipeline/slurry, multi-modal, out-of-state, or spot).

**Why this and not ownership.** The economic property that makes a mine's booked cost an *average* rather than a
*marginal* cost is that it is **dedicated** to the plant: its fixed cost is recovered over that plant's tons, whether the
mine is an affiliate (Bridger Coal Co.) or a third-party cost-plus mine-mouth contract. Dedication is observable from
the delivery mode and geography; ownership is not in the filing and would need a hand-kept affiliate map (rule 24).

**Known limits, stated before the numbers:** (a) a truck-delivered in-state *non-dedicated* mine is misclassified as
captive; (b) a dedicated mine that ships by rail (none expected in NWPP) is misclassified as non-captive; (c) rows with
`FUEL_COST` withheld count toward shares but not prices.

**Derived quantities (per plant, per year Y):**
- `mmbtu = QUANTITY × Average Heat Content`;
- `captive_share = Σ mmbtu[captive] / Σ mmbtu[all coal]`;
- `p_captive`, `p_noncaptive`, `p_blend` = MMBtu-weighted `FUEL_COST` ($/MMBtu, EIA reports cents/MMBtu — converted)
  over rows with a reported cost;
- **mixed-source** iff `0 < captive_share < 1` — only these plants are in scope for the design's object;
- `gap = p_blend − p_noncaptive` ($/MMBtu), the move the object would make on the econ tranches.

**Scope:** the NWPP model coal fleet (plants in keeper #18's `dispatch/<Y>_P1.parquet` with a `COAL_*` class),
2019–2024. **2025 receipts are not on disk** (`coal-receipts/` stops at 2024) — 2025 is reported as a gap, never
extrapolated.
