# DESIGN — SPP-106: offer-side unavailability (zero LP, 2026-10-01)

Lane: SPP-106, chartered by the owner's SPP-105 card "Offer-side design" (2026-09-30).
Keeper: `2026-09-28-spp-100-chp-scope`, bundle `results/calibration/spp100_arm_span` (2019–2025).
Probe: `scripts/probes/_spp106_offer_unavailability_phase0.py` (reuses SPP-105's rebuild harness and SPP-84's merit re-clear).
Numbers: `results/phase0/spp/_spp106_offer_unavailability_phase0.json`.
Source: SPP MMU, *Unavailable Generation Capacity in SPP Markets: Causes and Impacts* (2025-12-19),
<https://spp.org/documents/75563/unavailable%20generation%20capacity%20in%20spp%20markets%20causes%20and%20impacts.pdf>;
SPP MMU *State of the Market* 2024 (doc 73953) and 2025 (doc 76798).
**No LP. No shard. No bundle. No `src/` edit. No `ScenarioConfig` field. No multiplier touched.**

## 0. Headline

1. **No admissible SPP-own series exists at the grain a carrier needs.**
   - The MMU classes are **annual, system-wide MW for 2020–24**.
   - Only reliability status is split by fuel (Fig 3).
   - Nothing is published at unit, class (CC / CT / ST) or hour grain.
   - SPP's portal products carry no commitment status, economic max or emergency max (SPP-82's survey,
     re-checked here: the resource-forecast products carry wind / solar forecasts only).
2. **Even taken at face value, the classes cannot close the gap.**
   - Upper-tercile gap (RT − keeper P1): **$11.2 / 14.6 / 13.2** in 2023 / 24 / 25.
   - Best zero-LP carrier: **+$1.3 / 2.9 / 3.0** (gas reliability status removed cheapest-first).
     That is ≤ ~20 %, and it uses the one allocation the MMU does not identify.
   - The identified-allocation-free carriers move **+$0.4 to +0.7**.
3. **The classes do not have the residual's shape.**
   - The residual steps from 2019–21 ($3–6) to 2023–25 ($11–15).
   - The MMU classes are roughly flat 2021–24, and the carriers move 2019–21 about as much as 2023–25.
   - So they are level movers. They would push the over-priced validation years (C3a 2019 +11.5 %, 2020
     +27.5 %) further up. This is SPP-83's verdict on the offline-capacity excess, reached again from the
     offer side.
4. **Not concentrated in scarce hours.** The MMU publishes no hourly or seasonal shape, apart from ambient
   derates (summer days). The 2024 ASOM states that the emergency / reliability category "remained
   constant at around 3 %" month to month. A carrier built from it is flat by construction.
5. **The reliability-status carrier walks into SPP-105 B's scarcity trap.**
   - It removes whole gas units. In 2024 the re-clear goes short for **3–6 h**, and the minimum margin
     falls from +0.61 GW to about **−1.0 GW**.
   - Physically this is also wrong-way: reliability-status capacity is exactly what SPP commits in tight
     hours. A flat removal takes it away in the hours it actually serves.
6. **A rule-14 side finding (no lever, direction down).**
   - The keeper's flat GADS performance derate plus flat summer class derate (CC 10 %, CT 12.5 %, on a
     net-summer pmax: `summer_derate_basis_aware` is off) removes **0.6–0.9 GW more** (2023–25; up to 1.15 in 2021–22) fossil capacity in
     the upper tercile than the MMU's measured "above emergency max" plus ambient derate.
   - Replacing one with the other **lowers** upper-tercile price $0.2–0.9.
   - Recorded for the matrix; not proposed here.
7. **Recommendation: record offer-side unavailability as an SPP model-class limit.** Build nothing.

## 1. MMU classes, as published (MW, annual average, rated conventional capacity basis)

Exact where the report prints numbers (Fig 12 table, prose). Otherwise **digitized from the figures
(±~100 MW)**.

| class | 2020 | 2021 | 2022 | 2023 | 2024 | source |
|---|---:|---:|---:|---:|---:|---|
| rated conventional capacity | 67,300 | 65,900 | 66,000 | 63,400 | 64,800 | Fig 16 |
| reliability status, all fuels | 1,650 | 2,550 | 2,700 | 2,650 | 2,900 | Fig 17 (prose: 1,600 → 3,000) |
| reliability status, gas | 1,050 | 1,220 | 1,240 | 1,300 | 1,920 | Fig 3 (prose: avg ~1,300, ~2,000 in 2024) |
| economic → emergency max | 1,750 | 1,650 | 1,800 | 1,800 | 1,750 | Fig 17 (prose: 1,600–1,800) |
| above emergency max (<10 + >10 MW) | 2,500 | 1,500 | 1,700 | 1,950 | 1,700 | Fig 17; Fig 4 agrees |
| ambient derate, MW on derate days × days | 338 × 115 | 185 × 122 | 367 × 134 | 422 × 116 | 340 × 112 | Fig 12 (exact) |

- **No 2019, no 2025.** The ASOMs give one combined number ("reliability status or above economic max"):
  **~4,000 MW (2024) → ~4,600 MW (2025)**.
- **Rule-14 reconciliation fails at the first check.** The white paper's two classes sum to **4,650 MW**
  for 2024, while the 2024 ASOM gives **~4,000**. Both are MMU products, but they use different bases
  (rated vs installed capacity, and scope). A carrier would have to pick one, and nothing published
  settles which.

## 2. Phase 0: keeper upper-tercile headroom (GW; RT p67 ≤ RT < p99, Feb excluded)

Each cell is available MW minus P1 generation, on the keeper's own `fleet_only` rebuild.

| year | gas CC | gas CT | gas ST | coal | RT / P1 upper mean, $/MWh |
|---|---:|---:|---:|---:|---|
| 2019 | 0.78 | 6.21 | 1.78 | 2.69 | 32.0 / 26.5 |
| 2020 | 0.84 | 5.91 | 1.82 | 3.07 | 27.9 / 24.6 |
| 2021 | 2.02 | 6.51 | 2.46 | 0.61 | 46.4 / 40.5 |
| 2022 | 1.83 | 6.78 | 2.99 | 0.22 | 88.9 / 63.6 |
| 2023 | 1.17 | 5.57 | 2.21 | 1.78 | 41.6 / 30.4 |
| 2024 | 0.81 | 5.37 | 2.19 | 2.21 | 46.1 / 31.5 |
| 2025 | 1.14 | 6.57 | 2.47 | 0.96 | 47.6 / 34.4 |

- **CT headroom stays 5.4–6.6 GW** in every train year. All the MMU's offer classes together, gas and
  coal included, are ~5.9–6.4 GW across *all* conventional capacity (nuclear and hydro included). Removing them cannot exhaust the CT
  tranche, so a CT keeps setting price at roughly the same offer. SPP-81b measured the residual as a
  **gas-independent level shift lifting every setter class by ~$10**. A volume removal from a flat CT
  stack cannot produce that.
- **Upper-tercile hours are spread through the year**, not concentrated: 2024 runs Jan 13 %, Jun–Dec
  ~10 % each, and Mar–May 4–6 %. They peak at hours 10–18.
- **The MMU reliability-gas MW (1.0–1.9 GW) is 17–35 % of SPP-83's ~6 GW** keeper-gas-over-SPP-online
  excess. It is a part of that level, and flat like it.

## 3. Admissibility, class by class (rules 13 / 14 / 21)

| class | series | forward story (rule 13) | rule 21 | verdict |
|---|---|---|---|---|
| reliability status | annual gas MW, 2020–24, digitized; ASOM gives only a combined figure | a participant choice, held-last from an annual MMU statistic; it would regenerate only if the MMU keeps publishing it | **which units go offline is unidentified**, and the price effect varies ×3 across the allocation bounds, so the allocation is a free parameter | **inadmissible** |
| economic → emergency max | annual all-fuel MW, flat 2020–24 | a flat per-unit top slice, held-last; regenerable only as a constant | none if flat pro rata | admissible in form, **inert in effect** (+$0.4–1.3 upper) |
| above emergency max + ambient | annual all-fuel MW; ambient table exact | a replacement for the flat GADS performance + summer derates (rule 19) | none | admissible in form; **moves price down** |
| physical parameters (min-run, start, ramp) | ASOM gives fleet averages by fuel; no unit series, no costs (SPP-83) | none | — | **no series** (and `spp_commitment_posture` is R) |

## 4. Zero-LP predictions (SPP-84 re-clear, keeper stack at keeper non-VER P1 generation)

Each cell is Δ upper-tercile price in $/MWh (Δ fossil availability removed in the upper tercile, GW),
followed by short hours. The carriers are instruments, never configs (probe docstring). 2019 takes 2020's
MMU values and 2025 takes 2024's; that hold rule was fixed before any number was computed.

| year | gap | E (replace flat derates) | EX (+ eco→emer band) | R_dear | R_pro | R_cheap | EX + R_pro |
|---|---:|---|---|---|---|---|---|
| 2019 | 5.6 | +0.09 (−0.05) 0 | +0.81 (+1.15) 0 | +0.21 0 | +0.48 0 | +0.97 0 | +1.34 0 |
| 2020 | 3.3 | −0.02 (−0.27) 0 | +0.61 (+0.92) 0 | +0.00 0 | +0.29 0 | +0.81 0 | +0.95 0 |
| 2021 | 5.9 | −0.67 (−1.15) 0 | +0.70 (−0.01) 0 | +0.01 0 | +0.60 0 | +1.86 0 | +1.34 0 |
| 2022 | 25.3 | −0.90 (−1.14) 0 | +1.26 (+0.17) 0 | +0.37 0 | +0.95 0 | +2.98 0 | +2.47 1 |
| 2023 | 11.2 | −0.21 (−0.63) 0 | +0.58 (+0.68) 0 | +0.00 0 | +0.49 0 | +1.28 0 | +1.13 0 |
| 2024 | 14.6 | −0.52 (−0.80) 0 | +0.43 (+0.44) 0 | +0.92 **4** | +1.76 **3** | +2.86 **6** | +2.34 **2** |
| 2025 | 13.2 | −0.41 (−0.87) 0 | +0.74 (+0.40) 0 | +0.81 1 | +1.78 0 | +2.97 1 | +2.12 0 |

- **Unserved-energy risk (SPP-105 B's trap).** The re-clear's minimum fossil margin in 2024 is **+0.61 GW
  for the keeper**. Under the reliability carriers it is **−0.89 to −1.08 GW**, and in 2025 it is
  −0.17 to +0.01. This instrument has no ramps, no zones and no reserves, so the LP would be tighter
  still. SPP-105 B was milder here at zero LP and still produced 85 GWh of unserved energy in the solve.
- **Shape.** The carriers' 2019–21 moves (+0.3 to +1.9) are about the size of their 2023–25 moves. The
  residual is 2–4× larger in 2023–25. None of the carriers tracks the step.

## 5. The design that would be built (if one were), and why it is not recommended

- **Form (rule 19).** The only form that is clean under rules 19 and 21 is **EX**: replace the flat GADS
  performance derate and the flat summer class derate on fossil rows with the MMU's "above emergency
  max" share plus the ambient MW-days on Jun–Sep, then remove the "economic → emergency" share flat from
  every fossil row.
  - Zero fitted parameters.
  - The window is year-round, plus Jun–Sep for ambient (rule 17).
  - Forward: hold the last MMU year.
- **Why not.**
  1. It moves the upper tercile **+$0.4–0.7 against an $11–15 gap**.
  2. It moves 2019–21 as much as 2023–25, so it worsens the over-priced validation years.
  3. Its inputs are digitized annual figures from a one-off white paper. The recurring ASOM product
     disagrees with it by ~15 % for the same year (rule 14). Only a combined figure recurs, and that
     cannot be split into the two classes the carrier needs.
  4. Its E half moves price down, against C3a.
- **The reliability-status carrier is refused outright**: its allocation is an unidentified free
  parameter (rule 21), and it creates unserved energy in 2024 (rule 1 / SPP-105 B).
- **Cost profile if the owner overrides anyway.** One `ScenarioConfig` field (default off), a digitized
  MMU table under `data/raw/` with a SOURCES note, a matrix row with a cell in every shard, and tests.
  Seven year-isolated shards at ~12–15 min wall each, run in parallel. Compose / attest / register / score.
  About one session.

## 6. Recommendation

**Record offer-side unavailability as an SPP model-class limit, and build nothing.**
- The 2023–25 upper-tercile shortfall now has three adjudicated non-owners:
  - outage availability (SPP-104 / 105, R);
  - commitment cost (SPP-83, no source);
  - offer-side unavailability (this lane: no admissible series, and the wrong shape and size even taken at
    face value).
- What remains is SPP-81b's measured signature: a **gas-independent ~$10–14 level shift in RT price-setting
  that the offered stack does not explain**. That is outside what a marginal-cost LP with public inputs
  can carry.
- The train tier is CALIBRATED with C3c as its lone ledgered caveat. Under rule 1 that is the honest stop.

## 7. Matrix (rule 28)

- No mechanism was built, so there is no new row.
- `summer_derate_basis_aware` (SPP cell, stays **U**) gains the §0.6 measurement as evidence: on SPP's
  net-summer pmax, the flat summer class derate exceeds the MMU's measured ambient + unreported derate by
  0.6–0.9 GW in the 2023–25 upper tercile, and the direction of a basis-aware repair is price **down**.
