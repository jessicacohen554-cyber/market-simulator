# FINDING — closeout-PJM-decommit phase 0: no decommitment mechanism charters (ZERO LP)

**Verdict: NOT CHARTERED.** Nothing built, solved or registered; keeper `2026-10-03-closeout-pjm-nuc-keeper`
unchanged. Owner ruling R-55 (*"Find a mechanism to get it to decommit."*). Readings fixed ex ante in
`PRECOMMIT-closeout-pjm-decommit-phase0-2026-10-03.md` (commit `66f2959a`), probe
`scripts/probes/_closeoutpjm_decommit_reach.py` (`0c9c673e`), output `results/phase0/pjm/_closeoutpjm_decommit_reach.json`.

## 1. Reach table (static price-taker DP per plant at the keeper zone price; an UPPER bound)

B1 bar = half the COAL_BIT excess over the ±8 TWh band: **5.86 / 2.37 / 4.36 TWh** (2019/20/21).
`dec` = COAL_BIT energy removed (TWh); `dark` = share of it in real-dark coal hours (bar 0.6).

| candidate | 2019 dec / dark | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | B1 | B4 | B2/B3 flips |
|---|---|---|---|---|---|---|---|---|---|---|
| (a0) friction posture (start-up 100 $/MW, min-down 16 h, measured min-load, floors replaced) | net **−0.40** (adds coal) | +0.01 | +0.02 | +0.15 | +1.77 | +1.79 | +0.64 | ✗ | ✗ | none |
| (a1) three-part: (a0) + measured CAMPD no-load | 2.09 / 0.49 | 3.34 / 0.61 | 1.21 / 0.68 | 0.82 / 0.54 | **6.09** / 0.59 | **4.52** / 0.38 | 1.60 / 0.51 | ✗ (2019, 2021) | ✗ (0.59 pooled; 2019 0.49) | C3a 2020 → +10.5 % |
| (a1-real) (a1) at real zonal DA (diagnostic) | 5.65 / 0.37 | 13.94 / 0.51 | 5.83 / 0.40 | 1.48 / 0.49 | 11.54 / 0.42 | 13.55 / 0.32 | 6.13 / 0.35 | ✗ (2019) | ✗ (0.45) | n/a |
| (b1) `coal_committed_nested_on_mustrun` | 7.86 / 0.29 | 11.51 / 0.39 | 2.92 / 0.29 | 11.79 / 0.39 | 15.10 / 0.31 | 9.82 / 0.35 | 2.14 / 0.33 | ✗ (2021) | ✗ (0.34) | 7 (below) |
| (b2) `commitment_floor_window_netload` ceiling | 0.99 | 0.89 | 1.05 | 0.93 | 0.92 | 0.78 | 0.86 | ✗ | — | — |
| post-hoc, NOT pre-registered: (a1) with offers floored at measured incremental fuel cost | 11.95 / 0.52 | 27.29 / 0.59 | 3.00 / 0.70 | 7.01 / 0.57 | **36.55** / 0.36 | **46.43** / 0.31 | 9.62 / 0.49 | — | — | C3a 2020 +17.9 %, 2023 +12.4 %, 2024 +10.1 % |

(b1) flips after the static re-clear: COAL_BIT 2023 +3.05→−12.05 and 2024 +0.59→−9.22; CC_REGULAR 2019
+3.62→+9.34, 2020 +6.00→+13.10, 2023 +3.40→+8.98; CC_REGULAR 2022 worsens +8.96→+16.49; C3a 2020 → +12.1 %.

**B0 (measured no-load basis): PASS.** The CAMPD regression `heatInput = a + b·grossLoad` is identified on every
year: positive intercept on 0.96–0.99 of unit capacity, capacity-weighted median R² 0.96–0.98, full-load average
HR 9.2–9.6 against incremental 8.5–9.0 MMBtu/MWh, no-load 0.68–0.77 MMBtu/h per MW (≈ $1.5–2/MW-h at delivered
coal). Coverage caveat: 11 of 57 (2019) to 11 of 34 (2025) keeper COAL_BIT plants have no CAMPD coal-fuel unit
match and carry zero no-load, which understates (a1)'s reach, but not enough to change any reading: (a1) misses
B1 in 2019 by 3.8 TWh and its excess falls in the controls either way.

## 2. Readings

- **(a0) cannot decommit by construction, and it does not.** With no cost on being online, any hour whose price
  clears the offer has non-negative margin, so staying on is never worse. Start-up cost and min-down only add
  min-load energy through the troughs. This is why the existing posture family, ported to coal, is the wrong tool.
- **(a1) is the structurally right form, but its reach falls in the wrong years.** A measured no-load plus a
  start-up makes multi-day off spells optimal. At the keeper's prices it decommits 1.2–3.3 TWh in the fail years
  and 4.5–6.1 TWh in the 2023/24 controls. COAL_BIT 2023/24 PASS today at +3.05/+0.59, and the static re-clear
  takes them to −2.6/−3.5: still PASS, but moving away from the actuals. Against the excess over the band (11.7 / 4.7 / 8.7 TWh), the net cut is 14 % / 65 % / 12 %.
  It also breaks C3a 2020 (+9.0 → +10.5 %).
- **The finding the owner's question turns on: the decommitment the real fleet shows is not year-discriminating.**
  Every form that decommits (a1, a1-real, the post-hoc cost floor, b1) removes as much or more coal in 2023/24 as
  in 2019–21. The post-hoc cost-floored form removes 36–46 TWh in 2023/24 against 3–27 TWh in the fail years.
  The real 2023/24 coal fleet runs while it sits below measured going cost about as often as the 2019–21 fleet
  does (NEXT-34 Q5). A decommitment mechanism large enough to close 2019–21 breaks the controls.
- **(b1) is a loading cut, not a decommitment.** It removes the double-counted cheap committed MW (rule-14
  units repair, NWPP-NEXT-4) and reaches the 72 % of the overage that NEXT-24/32 place on units the real fleet
  had online. But only 0.29–0.39 lands in dark hours, it is largest in the controls (15.1 TWh 2023), and it
  flips seven class-years. Not chartered here. Its keeper-level effect is the shared committed/must-run artifact
  convention, which belongs to a separate rule-14 lane if the desk wants it measured at the CC side effect.
- **(b2)** can only relocate the sync floor; ≤ 1.05 TWh of it sits in real-dark hours.

## 3. (c) The price side

- At **zonal** grain the keeper's price in the real dark spells is within +0.3 / +1.9 / +1.2 $/MWh of real DA in
  2019–21 (NEXT-33 Q1). NEXT-32's "price above real" was a system-price artefact. The setters are CC_REGULAR econc
  and COAL_BIT econc (NEXT-33 Q2, 0.86 of the gap).
- The *shape* matters more than the level. At the same mean, (a1) at the real hourly zonal DA decommits 2.7× to
  4.8× more than at the keeper price (5.6 vs 2.1 TWh in 2019): real troughs are deeper than the keeper's (the
  NEXT-29/33 low-hour level gap, +4.4 to +7.4 $/MWh in 2019–21).
- Even real prices fail B1 (2019: 5.65 < 5.86), fail B4 (dark share 0.45), and decommit 11.5–13.6 TWh in the
  controls. So a price repair would not make a decommitment mechanism year-discriminating either.
- The trough-level channels are adjudicated: `pjm_replacement_cost_fuel` R; `zonal_gas_basis` K with its hub
  series DATA-BLOCKED; the rule-1 band channel, which NEXT-34 shows has no year-uniform operand.
- **Named:** the carrier is neither a missing commitment state nor the price level. It is real-fleet conduct that
  differs by year at the same economics: coal sat dark in 2019–21 and ran in 2023/24 at comparable margins below
  going cost. That is the availability/conduct frontier NEXT-13/30/31/34 already describe.

## 4. Cost of the candidates (as stated in the PRECOMMIT, none incurred)

- **(a1):** src change: a coal leg of the posture family with a no-load cost on `U`; PJM-scoped
  `pjm_coal_three_part_commitment` replacing the `_mustrun`/`_sync` floors; P1 start-up amortization zeroed on
  postured coal; a matrix row plus a cell in every shard; tests; 7 shards.
- **(b1)/(b2):** recipe `--set` only, plus 7 shards.

None is warranted on this reach.

## 5. Matrix (PJM shard only)

| Cell | Change |
|---|---|
| `coal_committed_nested_on_mustrun` | U → **R** (zero-LP reach, §1) |
| `commitment_floor_window_netload` | U → **R** (reach ceiling below B1) |
| `online_capacity_envelope` | stays R; new coal-leg evidence appended ((a0)/(a1) as above) |

COAL_BIT 2019–21 goes back to the R-47 frontier card with the commitment channel now measured in its strongest
structural form.
