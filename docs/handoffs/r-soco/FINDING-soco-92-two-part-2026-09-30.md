# FINDING soco-92 Track B — two-part cost for SOCO's pure-LP P1: real structure, wrong answer for C3a

**Owner ruling in force (soco-91 card, 2026-09-29): "Reopen two-part cost".** A zero-LP design lane: no solve, nothing
built. Keeper unchanged: `2026-09-29-soco87-gas-hh-monthly` (`results/calibration/soco87_span`), NOT-YET 7/4/0/1/2.
Probe: `scripts/probes/_soco92_two_part_census.py` (`census`, `greedy --arm {posture,posture_mload,incr_only}`).
Scratch outputs are not committed.

## Conclusion (one)

**Do not build it for C3a.** Two-part cost is the right *structure* for a cost-based pool, because FERC-714 system λ is
by definition the incremental cost among committed units. But SOCO's own CEMS record, read without using λ for any value,
says it cannot close the night gap. At the fleet's **measured night operating point**, CC incremental heat rate is
**0.92–0.97 × average**. λ sits at **0.75–0.83 × the CC offer**. Incremental pricing therefore explains at most a
quarter to a third of the night ratio. The coherent pure-LP form of the construction **raises** the night price in 6 of
7 years, because its sunk minimum-load block backs off cheaper supply and coal becomes marginal. The CT half cannot
reach the afternoon gap from any measured start cost. What is left of the night gap is the fuel-price basis in
Southern's λ, which free public data cannot identify (soco-85 §7, soco-90).

## 1. The construction (what "coherent" means in a pure LP)

A no-load cost can reach an LP price only through a commitment state. Without one, the tightest LP relaxation of
{no-load + convex incremental curve} is its convex hull. That hull prices the first block at the plant's **minimum
average** heat rate, which is the flat average offer SOCO already uses, and prices above it at incremental (≥ average,
soco-85). So without a commitment state, two-part cost can only raise prices (soco-85 §3 measured exactly that:
+$0.17 to +$2.37/MWh).

The one pure-LP vehicle that lets incremental cost set the price is the repo's **commitment-posture family**
(`miso_/caiso_/pjm_/spp_commitment_posture`, the last added by SPP-102 on main since the soco-87 solve). It provides a
continuous online capacity U[p,t], the measured min-load coupling ΣP ≥ mlf·U, and a start charge on ΔU⁺. When U is held
above output (for example, CCs kept online overnight because restarting costs more), the marginal MW costs only its
incremental heat rate. A SOCO build would be that posture on the CC pool, with SOCO's own values:

| parameter | SOCO measured value | source |
|---|---|---|
| min-load coupling mlf | LSL/HSL **0.60** | soco-85 §2, CAMPD cap-weighted p50 |
| no-load | **0.32** of full-load heat | soco-85 §2 |
| incremental curve above LSL | x = 0 / 0.5 / 0.9 → **0.81 / 1.00 / 1.21** × own average | soco-85 §2 (frozen `derive_campd_marginal_hr`) |
| CC start | NREL class table ($/MW), the family's existing source | `COMMITMENT_PARAMS_BY_FUEL` |
| CT start | measured fuel-only **$3.6/MW**; NREL **$20/MW** | SOCO-64, soco-77 §1 |

This is one config for all seven years, with zero values read off λ. CTs are fast-start (min-down ≤ 2 h, start < $30/MW),
so rule 18 exempts them from the posture. Their two-part half would be the start amortization alone (§4).

## 2. Engaging soco-91's night fact: where are SOCO's CCs at night?

The CEMS record (AL/GA/MS/FL, soco-85's 53 CC units in 16 `ok` plants, 18.6 GW HSL) was put on the CST 8760 (GA shifted
−1 h). Each online unit's load position was taken from its own pooled I/O fit, along with its incremental heat rate at
that position. λ selects the **hours** (soco-91's sets) and nothing else.

| year | night: fleet loading / mean x / share of online HSL at x < 0.25 | **night incremental ÷ average** | night *average* HR ÷ own average | λ ÷ CC offer (soco-91) | afternoon incremental ÷ average |
|---|---|---:|---:|---:|---:|
| 2019 | 0.73 / 0.38 / 0.30 | **0.93** | 1.01 | 0.75 | 1.08 |
| 2020 | 0.74 / 0.41 / 0.27 | **0.93** | 1.01 | 0.75 | 1.08 |
| 2021 | 0.72 / 0.36 / 0.36 | **0.92** | 1.01 | 0.83 | 1.08 |
| 2022 | 0.74 / 0.39 / 0.33 | **0.94** | 1.01 | 0.78 | 1.09 |
| 2023 | 0.77 / 0.47 / 0.18 | **0.95** | 0.99 | 0.81 | 1.08 |
| 2024 | 0.77 / 0.45 / 0.23 | **0.97** | 1.00 | 0.78 | 1.09 |
| 2025 | 0.76 / 0.43 / 0.24 | **0.93** | 1.00 | 0.81 | 1.09 |

- SOCO's CCs do sit lower at night: x ≈ 0.4 against ≈ 0.8 in the afternoon, with 18–36 % of online capacity in the
  bottom quarter of the ramp. So the commitment effect is real.
- It is not deep enough. The incremental rate at that point is 3–8 % below average. λ needs 17–25 % below.
- Soco-85's 0.81 applies only at x = 0. The fleet is not there at night; its mean position is 0.36–0.47.

## 3. Greedy bound (soco-91 restack instrument, baseline-differenced, re-scored through `calibration_verdict`)

| arm | what it does | Δ price, night / afternoon ($/MWh) | C3a 2019 / 2020 / 2022 (keeper +14.0 / +14.4 / −12.7) | flips |
|---|---|---|---|---|
| `incr_only` | incremental segments, no commitment state | +0.2…+1.0 / ~0 (2022 −0.7 night) | +15.0 / +15.9 / −11.9 | none |
| `posture_mload` | online capacity sized to the **measured** hourly CC loading; sunk LSL block; segments at the measured curve | +0.4…+1.0 (2022 −0.1) / ~0 | +15.0 / +15.9 / −11.6 | none |
| `posture` (online state = measured f_on on nameplate) | perfect-hindsight commitment | — | invalid: the model's CC fleet cannot carry its own energy inside the measured online fraction, so the restack moves 11–20 TWh CC → CT | — |

In the admissible arms C1/C2 do not move (class moves ≤ 0.9 TWh), and neither C3a nor C3b flips. 2019 and 2020 get
**worse**. The `posture` arm is recorded as invalid rather than as a result: it tests CC capacity accounting (the model's
CC nameplate against CEMS HSL), not price formation.

Why the night price rises even at the measured operating point: the sunk min-load block (0.6 × U) enters below every
offer. The CC capacity left to set price is the upper segments, at 0.95–1.19 × average. The cheaper-than-CC stack at
night is COAL_PRB, which soco-91 §2 measured at $0.3–3.7 *above* the CC setter, so it becomes marginal.

## 4. CT start / no-load (the afternoon half)

The afternoon gap is λ **+$1.0 to +$24.6** above the CT setter's average offer, and it grows with gas price. A start
amortized over SOCO's measured CT run (plant medians 6–15 h, soco-77 §2) adds:

- $3.6/MW (measured fuel-only) → **≈ $0.2–0.6/MWh**
- $20/MW (NREL table) → **≈ $1.3–3.3/MWh**

Neither ex-ante value reaches the 2021–2025 gaps ($6.3–24.6), and in 2019–2020 either would fill the $1.0–1.3 gap. So
the start is at most the 2019/2020 residual, not the mechanism. A CT's incremental below full load is below average, so
the no-load half moves the CT offer **down**, which is the wrong sign. soco-77's finding still holds: the CT problem is
plant ranking, not level.

## 5. Rules

- **Rules 1/13/21/23:** every value above is from SOCO's own CEMS or a published table. λ picked hours only. One config
  for 2019–2025.
- **Rule 19:** no CC floor exists on SOCO today (keeper D-2: 0.0 % forced on CC_REGULAR), so a posture would stack on
  nothing. The `soco_gas_st_campaign_commitment` floor is ST_GAS only.
- **Rule 25:** no ISO's posture verdict is transferred. `spp_commitment_posture` is SPP-exclusive (SOCO cell `.`).

## 6. Build card (for the owner)

1. **Close the reopen (recommended).** Record CC two-part cost for SOCO as **I** on C3a (measured operating point, wrong
   sign in the coherent form), keep CT start **G**, and name the fuel-price basis as the residual owner.
2. **Build a SOCO CC commitment posture for structure anyway.** This means a new SOCO-gated `ScenarioConfig` field
   (the posture family pattern), a matrix row plus a cell in every shard (rule 28(c)), and 7 year-isolated shards
   (~2–9 min LP each). Expected from §3: C3a worse in 2019/2020 by ~1–1.5 pp, no flips, determination unchanged.
3. **Stop SOCO C3a work.** The two failing years are driven by the fuel basis in Southern's λ. That basis is
   unidentifiable from free data, and the owner has ruled against buying the daily series.

## 7. Records

- Probe: `scripts/probes/_soco92_two_part_census.py`. Scratch outputs (`cc92_<y>.npz`, `soco92_cc_night_census.csv`,
  `soco92_greedy_<arm>.json`, `fleet91_<y>.npz`) are not committed.
- Matrix: note only, no verdict minted without the owner card.
- Retrievability: no bundle.
