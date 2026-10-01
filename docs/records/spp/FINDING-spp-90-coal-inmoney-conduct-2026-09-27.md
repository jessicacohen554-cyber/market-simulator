# FINDING — SPP-90: SPP coal's in-the-money shortfall is on-line dispatch conduct, not missing availability. No admissible coal-availability repair exists.

**Lane** SPP-90 · **ZERO LP** · keeper `2026-09-26-spp-86-coal-extract` (bundle `spp86_arm_span`, basis_sha `d72e5f10`)
· probe `scripts/probes/_spp90_coal_inmoney_conduct.py` (reads the SPP-89 `_spp89_stack_dump.py` stacks, fleet_only rebuild)
· record `results/phase0/spp/_spp90_coal_inmoney_conduct.json`. Nothing solved or registered. Keeper unchanged. No promotion
question (rule 31).

## 1. Method

For every keeper coal plant (COAL_PRB + COAL_LIGNITE) and hour, all on the **gross** basis. SPP-87 showed the keeper's coal is gross:

- **K**: keeper available MW, `Σ pmax × availability`.
- **M**: keeper P1 coal output.
- **A**: CAMPD CEMS gross MW of the plant's coal units.
- **D_u**: each unit's demonstrated capability, the per-year p99 of its fully-on hourly gross.
- **Cw**: the unit's **same-week** demonstrated capability. This is its max gross in that ISO-week's on-line hours with actual LMP ≥ $30.

`K − A` splits exactly into `(K − Cw)`, which is keeper availability against what the fleet showed it had on line, plus
`(Cw − A)`, which is on line and below its own same-week capability. `ON − A` is split further. **Start** covers the ≤ 12 h
after a unit start. **Ramp context** covers the ≤ 6 h after an actual-LMP < $25 hour. **Sustained** is everything else,
split summer (Jun–Sep) and non-summer. Buckets use the actual system RT LMP.

## 2. Where the keeper actually over-loads in the money (actual LMP ≥ $30)

| year | hours | K GW | keeper M/K | actual A/K | M − A TWh |
|---|---|---|---|---|---|
| 2019 | 946 | 15.25 | 0.83 | 0.91 | **−1.20** |
| 2020 | 726 | 13.74 | 0.77 | 0.86 | **−0.89** |
| 2021 | 2,602 | 15.29 | 0.96 | 0.95 | +0.69 |
| **2022** | 4,836 | 15.08 | 0.96 | **0.89** | **+5.33** |
| 2023 | 2,085 | 13.37 | 0.87 | 0.89 | **−0.51** |
| 2024 | 1,875 | 12.87 | 0.83 | 0.85 | **−0.49** |
| 2025 | 2,744 | 13.64 | 0.94 | 0.91 | +1.04 |

- **In-the-money coal is already short in 4 of 7 years**: 2019, 2020, 2023 and 2024. At unit grain 2021 is near balance.
  SPP-89's 0.92 was a plant-grouped aggregate. The material excess is **2022 (+5.3 TWh)** plus 2025 (+1.0).
- Actual A/K stays in 0.85–0.95 in every year. The keeper's M/K is what moves with gas (0.77 → 0.96).

## 3. Why the real fleet stops at ~0.85–0.95 of K (actual LMP ≥ $30, mean GW)

| component | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| **K − Cw** (net) | −1.20 | −0.64 | −1.28 | −1.08 | −0.89 | −0.88 | −1.02 |
| ↳ keeper keeps MW the fleet did not have on line (+) | +0.69 | +1.14 | +0.74 | +0.79 | +0.89 | +0.97 | +0.75 |
| ↳ keeper removes MW the fleet had on line (−) | −1.89 | −1.78 | −2.02 | −1.87 | −1.77 | −1.85 | −1.77 |
| **Cw − A**, on line below same-week capability | 2.51 | 2.58 | 2.11 | 2.80 | 2.39 | 2.77 | 2.29 |
| ↳ rising > 5 % D/h (ramping up) | 0.65 | 0.71 | 0.48 | 0.57 | 0.63 | 0.65 | 0.56 |
| ↳ flat (\|ΔG\| ≤ 2 % D/h) | 1.14 | 1.11 | 0.98 | 1.35 | 1.04 | 1.26 | 1.02 |
| weekly-capability derate (D − Cw, on line) | 0.48 | 0.32 | 0.49 | 0.51 | 0.46 | 0.56 | 0.36 |
| start-up (≤ 12 h after start) | 0.30 | 0.42 | 0.32 | 0.34 | 0.32 | 0.39 | 0.34 |

(K − Cw is the plant-level sum of the ± parts.)

**The keeper does not over-state coal availability.** Net, it offers **0.6–1.3 GW less** than the units SPP had on line
demonstrably delivered that week. The gap to actual is entirely **Cw − A**, about 2.1–2.8 GW in every year. That is units on
line, below a level they reached in the money the same week.

## 4. The four candidates

| # | candidate | measured | verdict |
|---|---|---|---|
| 1 | Partial derates below pmax that the outage family misses | Weekly-capability derate is 0.32–0.56 GW, flat across years. The keeper already removes **more** than this, net −0.6 to −1.3 GW against Cw | **Not the object.** No missing derate |
| 2 | Summer / ambient max below nameplate | Sustained on-line shortfall is summer ≈ non-summer in 6 of 7 years. The exception is 2022 $30–60: 2.59 vs 1.37 GW. On-line capability is **higher** in summer (16.1–19.5 vs 12.1–15.9 GW) | **Not the object.** No ambient signature; `coal_nameplate_summer_derate` / `temp_dependent_derate` stay U |
| 3 | Units offline in the money that the keeper counts | +0.69–1.14 GW kept that CEMS had offline, but −1.8 to −2.0 GW removed that CEMS had on line. **Net the keeper is conservative.** This is placement (which plants), not level | **Not the object** for the level. Placement is the SPP-84/85/86 family's domain, and a re-derivation needs a data change (rule 23) |
| 4 | Ramp after low-price hours | CEMS up-ramp p99 = **0.21–0.23 D/h** (cap-weighted, stable 2019–25). In-money rising steps run at a median 0.11 D/h. Rising-hour shortfall is 0.48–0.71 GW plus 0.30–0.42 GW of start-up. The keeper runs `ramp_limits = False` | **Real, measured, forward-reproducible**, but year-invariant. See §5 |

The largest single component is the **flat** 1.0–1.35 GW: on line, not ramping, and below the same week's demonstrated
level while the hub LMP ≥ $30. Two explanations fit and neither is an availability input. The first is regulation /
spinning headroom carried on coal; SPP's `energy_reserve_coopt` is already `I` (SPP-55). The second is nodal congestion: the
comparison uses the hub LMP, and SPP's plant-node LMPs are not in the repo. Both are unmeasured here.

## 5. Verdict

- **No admissible, material coal-availability change. No PRECOMMIT, no G-DRIFT, no shard.**
- Every measured conduct component is **year-invariant**. A cap on the coal-outage family built from it would cut coal
  in all seven years. In 4 of 7, the keeper is already short in the money (−0.5 to −1.2 TWh). That fails the brief's
  "must not break the passing years" test, and it would select a driver because it closes 2022 (rule 1).
- The 2022-specific excess (+5.3 TWh) is the keeper's **price-driven** loading, not a real-fleet capability change. The
  real 2022 gap to K per plant is only +0.42 GW above the 2023–24 mean, spread across plants with no single outlier. It
  remains SPP-44's object: the 2022 coal markup / delivery reliability, procurement-blocked.
- **Ramp (candidate 4) is the one real mechanism found.** It has a measured driver (CEMS unit up-ramp p99 ≈ 0.22 D/h) and an
  existing seam (`measured_ramp_capability`, U). It is not a coal-availability repair: it binds on the model's own
  trajectory and applies to every class, so its sign on 2022 C1 cannot be predicted at zero LP. Any successor opens it as
  its own structural lane (rule 1), not as a 2022 fix. It must also first beat SPP-73's C3a/C3b bound on this same cell.
- Net/gross: A and the keeper are both gross (SPP-87). On a net basis (EIA-923 ≈ 0.89–0.91 × gross), actual A/K would be
  ~0.05–0.09 lower in every year. The ranking and the conclusion do not change.
- Do not re-tune the 0.93 multipliers (rule 1(c)).
