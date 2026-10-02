# DESIGN — SPP-107: repair the MMU offer-side carrier (zero LP, 2026-10-02)

- **Lane:** SPP-107, on the owner's SPP-106 cards "Hold, investigate shortfall" and "Repair EX" (2026-10-01).
- **Keeper / control:** `2026-09-28-spp-100-chp-scope`, bundle `results/calibration/spp100_arm_span`.
- **Incumbent arm:** EX = `spp_mmu_offer_unavailability = true` (SPP-106, HELD on E3).
- **Probe:** `scripts/probes/_spp107_repair_phase0.py` → `results/phase0/spp/_spp107_repair_phase0.json`.
  It rebuilds EX through the code path (not a re-derivation; max |re-derived − built| = 0.0 every year), then
  applies the repairs to the captured pre-band availability.
- **No LP. No shard. No `src/` edit yet.**

## 0. Headline

| | EX (built) | repaired (M + S) |
|---|---|---|
| South capacity vs keeper, EX short-event hours | −471 to −599 MW | **+93 to +148 MW** |
| predicted unserved (E3) | +1.4 / +2.9 GWh (solved) | **≤ keeper** (0 / 862 / 136 MWh in 2022 / 24 / 25) |
| train C3a 2023 / 24 / 25 | −4.4 / −6.0 / −1.6 % (solved) | **≈ −5.4 / −7.7 / −3.3 %** (predicted) |
| share of EX's train C3a gain kept | 100 % | **≈ 49 %** (59 / 34 / 54 % by year, §3.2) |
| validation 2021 C3a | +11.3 % FAIL (solved) | ≈ +9.5 % (borderline) |
| upper tercile Δ vs keeper (re-clear) | +0.43 to +0.72 $/MWh (2023–25) | +0.06 to +0.28 $/MWh |

1. **The repair fixes the scarcity failure.** In every hour EX went short, the repaired carrier leaves SPP-South
   with *more* dispatchable capacity than the keeper.
2. **It gives back about half of EX's price gain.** Most of EX's price effect came from construction error (1):
   removing a share of *rated* MW from units already on outage.
3. **It is still not the owner of the $11–15 upper-tercile gap.** Repaired, the carrier is a structural
   correction worth ~+$0.1–0.3 in the upper tercile, roughly level-neutral against the keeper.

## 1. The two repairs (one sub-gate, rule 19)

Proposed field: `spp_mmu_offer_repair: bool = False`. It is valid only with `spp_mmu_offer_unavailability = true`
(validation error otherwise) and changes only how EX's bands are constructed. It adds no second mechanism.

### (1) Multiplicative bands — `M`

- **Now (EX):** `a ← max(0, a − share)`. The band is a share of RATED pmax, even on a unit already derated by a
  measured CROW/CAMPD outage.
- **MMU definition (report §3.1.2):** "above emergency max" is measured against the *derated* amount; units on
  outage are excluded from the economic → emergency comparison.
- **Repaired:** `a ← a × (1 − share)` for the above-emergency, ambient and eco → emergency bands alike.
- A fully outaged unit is unchanged (0 either way). A partly outaged unit loses the share of the MW it still has.

### (2) Economic → emergency slice in scarcity only — `S`

- **Now (EX):** that slice is removed in every hour.
- **MMU definition:** those MW "are only accessible when SPP anticipates or identifies a reliability issue".
- **Repaired form:** one pseudo-generator per SPP zone (`SPP-North`, `SPP-South`).
  - Hourly capacity = Σ over the zone's fossil rows of `eco share × the row's post-outage available MW`. This is
    exactly the MW that (1) takes off those rows, so the units' economic max plus the pool equals their
    emergency max.
  - Offer = **the LP's own load-slack price minus the storage tiebreaker ε** (`voll − STORAGE_TIEBREAKER_EPSILON`).
  - It clears only where the zone would otherwise shed load, and it sits in its own zone, so the N→S limit still
    binds on it.
- **Precedent seam:** NYISO SCR/EDRP (`data.nyiso_demand_response`): per-zone pseudo-generators appended to the
  fleet list in `run_calibration.py`, with their hourly availability stamped on the arrays after build.
- **Price, zero fitted parameters (rules 21 / 24):** both numbers already exist in the registry (`voll`, rule 9's
  ε). No new numeric field.
  - *Rejected alternative:* SPP's $1,000 energy offer cap. It is a real tariff number, but in this LP it would let
    the pool clear in reserve-shortage hours below VOLL. That is a choice of trigger, not a definition.
    `voll − ε` is the literal "only when load would be shed".
- **Accounting:** pool energy is fossil energy from units already counted in their class. It is expected to be a
  few hundred MWh to ~1 GWh/yr. Its own fuel code (`emergency_band`) keeps it out of the class mix (C1) and
  out of reserves and AS. It carries no fuel cost or emissions. That understates fuel and CO₂ by at most
  ~1 GWh × a CT heat rate, which is declared, not hidden.

### What stays as EX

- Same MMU table, same hold rule (2019 ← 2020, 2025+ ← 2024).
- Same replacement of the flat GADS performance and summer class derates (rule 19).
- Same scope: SPP only, fossil rows (rule 25).

## 2. Admissibility

| rule | check |
|---|---|
| 1 | two construction errors fixed against the source's own definitions; chosen before any gate number |
| 13 | forward story unchanged: hold the last MMU year; the pool is endogenous (it clears on the LP's own scarcity) |
| 14 | moves the measured MMU bands onto the MMU's measurement basis |
| 17 | not a floor; the pool's window is the LP's own scarcity hours |
| 19 | a sub-gate of the one mechanism; replaces EX's construction, stacks nothing |
| 21 | zero fitted parameters; the price is the registered `voll` minus rule 9's ε |
| 24 | one boolean in `ScenarioConfig`; no env-var knob, no new numeric |
| 25 | SPP-only (validator, as EX) |

## 3. Zero-LP measurements

### 3.1 Price: SPP-84 merit re-clear at keeper non-VER P1 generation (Δ vs keeper, $/MWh)

| year | Δ all: EX | Δ all: M+S | kept | Δ upper: EX | Δ upper: M+S | fossil Δ upper, GW: EX / M |
|---|---:|---:|---:|---:|---:|---|
| 2019 | +0.53 | +0.33 | 61 % | +0.81 | +0.46 | −1.15 / −0.56 |
| 2020 | +0.41 | +0.26 | 63 % | +0.61 | +0.34 | −0.92 / −0.38 |
| 2021 | +1.47 | +0.93 | 63 % | +0.70 | +0.19 | +0.01 / +0.39 |
| 2022 | +1.28 | +0.83 | 65 % | +1.26 | +0.67 | −0.17 / +0.23 |
| 2023 | +0.45 | +0.26 | 59 % | +0.58 | +0.28 | −0.68 / −0.19 |
| 2024 | +0.32 | +0.11 | 34 % | +0.43 | +0.06 | −0.44 / +0.02 |
| 2025 | +0.63 | +0.35 | 54 % | +0.72 | +0.27 | −0.39 / +0.08 |

- `S` moves no economic-hour price: the pool sits at `voll − ε` and the re-clear is never short (all arms 0 h).
  So the M+S price columns equal M's.

### 3.2 C3a, keeper → EX (solved) → repaired (predicted = keeper + EX's solved gain × "kept")

| year | tier | keeper | EX (solved) | repaired (pred.) |
|---|---|---:|---:|---:|
| 2019 | validation | +11.5 % | +14.1 % | ≈ +13.1 % |
| 2020 | validation | +27.5 % | +30.4 % | ≈ +29.3 % |
| 2021 | validation | +6.5 % | +11.3 % FAIL | ≈ +9.5 % (inside ±10 %, barely) |
| 2022 | validation | −5.8 % | −1.6 % | ≈ −3.1 % |
| 2023 | train | −6.7 % | −4.4 % | ≈ −5.3 % |
| 2024 | train | −8.6 % | −6.0 % | ≈ −7.7 % |
| 2025 | train | −5.4 % | −1.6 % | ≈ −3.3 % |

- **Repair (1) gives back ≈ 51 % of EX's train C3a gain** (8.7 → 4.3 points summed over 2023–25).
- Train C3a stays inside ±10 % every year, so no train flip is predicted.

### 3.3 Coal (available-energy proxy, TWh/yr, Δ vs keeper)

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| COAL_PRB: EX | −6.8 | −6.4 | −4.3 | −5.1 | −5.7 | −5.0 | −5.0 |
| COAL_PRB: M | −5.0 | −4.5 | −3.0 | −3.7 | −3.9 | −3.2 | −3.4 |
| gas: EX | −1.5 | −1.4 | +2.5 | +1.0 | −0.5 | +1.2 | +1.3 |
| gas: M | +1.7 | +1.5 | +4.5 | +3.4 | +2.1 | +3.4 | +3.7 |

- About **65–70 % of EX's coal reduction survives** (coal is rarely on partial outage).
- Predicted C1 COAL_PRB 2023 / 24: +3.3 / +3.6 (keeper) → +0.6 / +0.8 (EX) → **≈ +1.4 / +1.8 TWh**.

### 3.4 Scarcity: SPP-South dispatchable capacity, arm − keeper (MW)

| year | hours | keeper South avail. | EX | M | M+S | pool | EX unserved (solved) | predicted |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 2022 | EX event, 19 May (day) | 14,971 | −599 | −261 | **+148** | 409 | 420 MWh | 0 (keeper 0) |
| 2024 | EX event, 21 Oct 13–17 h (keeper short 2 h) | 12,769 | −588 | −229 | **+115** | 344 | 3,737 MWh | ≤ 862 (keeper) |
| 2025 | EX event, 21 Dec 10–13 h (keeper short 1 h) | 13,537 | −471 | −271 | **+93** | 364 | 1,568 MWh | ≤ 136 (keeper) |

- Repair (1) alone restores 200–359 MW in these hours. That is not enough: M is still 229–271 MW short of the
  keeper. **Both repairs are needed for E3.**
- In the keeper's 200 highest-price South hours per year, M+S runs −157 to +222 MW vs the keeper (mean +161 to
  +418). The negative minima fall in 2019 / 20 / 23, years in which the keeper never goes short.
- Re-clear minimum system margin (GW), keeper → EX → M+S: 2024 0.61 → 1.17 → 2.70; 2025 1.40 → 1.99 → 3.64.

**Instrument limits.** The re-clear is single-zone with no ramps or reserves. The South comparison holds the rest
of the dispatch fixed. "Kept" scales EX's *solved* gains, so the C3a column is a prediction, not a score.

## 4. Recommendation

**Build `spp_mmu_offer_repair` and solve arm EXR (EX + repair) over 2019–2025.**

- **Rule 1:** it is the most structurally faithful form of a mechanism the owner has already chosen to carry, and it
  removes the one failure (E3) that held EX.
- **Expect:** a modest price effect, about half of EX's. It does not close the 2023+ upper-tercile gap and is not
  claimed to.
- **Cost:** one boolean, one pseudo-generator builder, a fuel code, tests, a matrix row with a cell in every shard,
  and 7 year-isolated shards at ~10 min wall each.

## 5. Matrix (rule 28)

- **If built:** a new row `spp_mmu_offer_repair` (SPP cell `U` → tested; every other shard `—`, SPP-only).
- **Until then:** the `spp_mmu_offer_unavailability` SPP cell stays **O**, with this DESIGN added as evidence.
