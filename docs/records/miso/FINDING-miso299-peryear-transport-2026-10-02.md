# FINDING — miso-299: per-year (vintaged) MISO gas variable transport from each year's own EIA-923 receipts — phase 0, zero LP

```
LANE    : miso-299 (owner ruling 2026-10-01, miso-298 decision card "What should miso-299 do?": "Per-year transport phase 0 (Recommended)")
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), legs at 8f765fef — unchanged
LP      : none in this document. Fleet-only rebuilds (miso-297 census machinery) cleared at the keeper's own P1 thermal quantity
STATUS  : §0 written and committed BEFORE any per-year table or census number existed (this commit). §§1–4 filled afterwards.
```

## 0. Pre-stated reading (fixed before any number)

**The object.** `data/raw/reference/miso_gas_variable_transport.csv` is a frozen derive (rule 23) of each plant's
volume-invariant wedge over its zone's traded hub, `print − hub = v + F/burn`, burn-weighted WLS, pooled over the
**2023–2025** receipts (`derive_miso_gas_variable_transport.py::YEARS`). miso-298 solved the owner-ruled gas form with
that table over 2019–2025 and was killed by K-1; the RESULT (§3 item 2) attributes the early-year cost to the table's
level sitting ABOVE the 2019–2022 print-over-hub wedge, so the form RAISED CC_REGULAR fuel +$0.07–0.14/MMBtu there.

**What this lane measures, at zero LP.** The SAME estimator, bars (`MIN_MONTHS` 12, `MIN_BURN_SPREAD` 2.0) and ladder
(own → zone|group → group → MISO-wide), run on each receipt year 2019–2025 ALONE, written as a NEW companion
(`data/raw/reference/miso_gas_variable_transport_vintaged/<year>.csv` + `.pool.csv`); the frozen table is not touched.
Rule 23: a re-derive on NEW source years (2019–2022 receipts were never in the fit) is admissible and the commit cites
the data. Then the miso-297 census ("joint" leg, m = 1.00) is re-run for every year pointed at the per-year table.

**The reading, stated now:**

- **PROCEED to a PRECOMMIT + 7 shards only if BOTH hold:**
  (a) the per-year table moves static cap-weighted **CC_REGULAR fuel DOWN in each of 2019, 2020, 2021 and 2022** relative to
  the keeper print (the miso-298 kill mechanism reversed: the ruled form must lower, not raise, the CC margin in the
  years it was killed on); and
  (b) in **2023, 2024 and 2025** the per-year table's static cap-weighted CC_REGULAR fuel stays within **±$0.05/MMBtu** of the
  frozen table's value for that year (the training-tier form the owner ruled on is not moved by the re-derive).
- **Otherwise: FINDING only.** Both `R` cells stay `R`, no shard, no PRECOMMIT; the owner gets a decision card with the
  measured numbers.

Reported at full magnitude either way, per year: own-plant coverage (plants, capacity share, by class), `v` cap-weighted
on CC_REGULAR / CT_PEAKER / ST_GAS / all gas, the burn-weighted print-over-hub wedge the panel measures, the static
CC_REGULAR fuel move, static dispatch (coal / CC_REGULAR / all gas / seam, mean GW), static q1–q2 and all-hours
load-weighted price error, and the bid-stack coal marginal share. Nothing is selected on any of these.

**Structural note stated up front (rule 1 / 13).** The frozen derive's docstring calls one value per plant across every
scored year a rule-1(b) property. A per-year table is a per-year MEASURED input (like the per-year EIA-923 print it
replaces), not a tuned value: every row is whatever that year's receipts say, with zero chosen scalars; its forward
analogue is the latest year's table carried forward, exactly as the frozen table already is. The tension is recorded
here so the owner sees it before anything is solved. A PRECOMMIT, if one follows, carries it in §1.

## 1. Derive provenance and receipt availability

(filled after §0 was committed)

## 2. The per-year tables

(filled after §0 was committed)

## 3. Census per year (zero LP)

(filled after §0 was committed)

## 4. Reading against §0, and what happens next

(filled after §0 was committed)
