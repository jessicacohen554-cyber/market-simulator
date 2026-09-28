# RESULT — SPP-100: the CHP steam-level swap, scoped to hosts whose meter supports an all-hours floor

**Lane** SPP-100 · control = keeper `2026-09-28-spp-99-remap-rederive` (`spp99_remap_span`, rule 29(b) form 4) ·
PRECOMMIT `docs/handoffs/PRECOMMIT-spp-100-chp-conduct-scope-2026-09-28.md` (merged `2e1f387d`; Addendum A
shard-check repair merged `11b72265`, the round-2 pin) · registered run **`2026-09-28-spp-100-chp-scope`**, bundle
`results/calibration/spp100_arm_span` (2019–2025).

## 1. What changed (two fields, zero free parameters)

- `chp_steam_floor_p25 = true`: the existing swap. A CHP host's floor uses its measured multi-year steam level
  instead of the never-below p2 minimum.
- `chp_steam_floor_conduct_scope = true` (new, default off): a **metered** host takes the swap only if its pooled
  on-frequency is above 0.5 — D-4's own conduct bar, applied ahead of the solve.

On SPP this lifts **Eastman 55176** (on 0.989) and **Black Hawk 55064** (on 0.995) to their measured flat level. It
leaves **Lake Road 2098** (on 0.246) on its p2 floor — the plant whose 24/7 trickle sank SPP-75. Small unmetered
cogens keep the swap (no meter, no verdict).

## 2. Legs (rule 36, one per year; the parent solved nothing)

Round 1 (pin `2e1f387d`) solved but did not push: the shard check had a bug (Addendum A). Round 2 re-solved on
`11b72265`. All seven round-2 legs pass the check in the shard and again in the parent.

| year | leg SHA (provenance only) | ΔCHP TWh | ΔCC_REGULAR | ΔCOAL_PRB | Δwind | Δprice $/MWh | slack MWh leg / keeper |
|---|---|---:|---:|---:|---:|---:|---|
| 2019 | `7d463322f2ccd72531f503539b2d495ea9c5f160` | +0.89 | −0.25 | −0.33 | −0.00 | −0.09 | 0 / 0 |
| 2020 | `d4d5530ac4be4a520a7844075f51a8e29283e31b` | +0.91 | −0.28 | −0.38 | −0.01 | −0.08 | 0 / 0 |
| 2021 | `65720bac88bf61d0b36efb9718c8e07c70db1344` | +1.07 | −0.39 | −0.37 | −0.09 | −0.36 | 0 / 0 |
| 2022 | `e5cb7754cc1f7453ed3bd8a9661450ea7eeec43c` | +1.17 | −0.39 | −0.36 | −0.13 | −0.44 | 0 / 0 |
| 2023 | `68667e6428c170d610b8c7ada74647317abe1fc8` | +0.94 | −0.27 | −0.31 | −0.09 | −0.23 | 0 / 0 |
| 2024 | `24ed08bef190ed25aad0e312814d952eff5d8e21` | +0.81 | −0.28 | −0.22 | −0.09 | −0.16 | 862 / 862 |
| 2025 | `7021af9b6056839e517715602097b70c9ab14a6a` | +0.93 | −0.28 | −0.29 | −0.09 | −0.22 | 136 / 136 |

ΔCHP = CC_CHP + CT_CHP + ST_CHP. The added steam base displaces CC_REGULAR and coal about equally; wind barely moves.

## 3. Expectations (PRECOMMIT §5) and the rule (§6)

| # | result | holds? |
|---|---|---|
| E1 | shard check PASS, 7 / 7 legs | yes |
| E2 | ΔCHP +0.81 to +1.17 TWh (band +0.15 to +1.6); max \|ΔCC_REGULAR\| 0.39 (≤ 0.8); max \|ΔCOAL_PRB\| 0.38 (≤ 0.6) | yes |
| E3 | price falls in every year; max \|Δ\| $0.44 (≤ $0.60) | yes |
| E4 | **D-4: no new FAIL row; no CHP row fails in any year** (Eastman / Black Hawk pass all 7). Keeper 8 FAIL rows → 7 (2021 `coal_mustrun` at 6095 clears) | yes |
| E5 | Train 2023–25 CALIBRATED, no status flip | yes |

Unserved energy does not rise in any year. **Rule §6 → RECOMMEND PROMOTE.**

## 4. Scored effect at full magnitude (not a criterion, rule 1)

**Train 2023–25: CALIBRATED**, lone ledgered C3c, unchanged (RT > $200 hours 0 / 7 / 2 vs 42 / 59 / 68).

**Validation 2019–22: NOT-YET**, the same failing rows:

| row | keeper | arm | direction |
|---|---|---|---|
| C3a 2019 | +11.9 % | +11.5 % | better |
| C3a 2020 | +28.0 % | +27.5 % | better |
| C3b 2020 | 0.349 | 0.343 | better |
| C4 gas 2021 | 0.316 | 0.307 | better |
| C4 gas 2022 | 0.367 | 0.356 | better |
| C1 COAL_PRB 2021 | +13.57 TWh | +13.20 | better |
| C1 COAL_PRB 2022 | +13.53 | +13.17 | better |
| C1 CC_REGULAR 2021 | −9.26 TWh | −9.65 | worse |
| C1 CC_REGULAR 2022 | −10.46 | −10.84 | worse |

The CC_REGULAR rows worsen for the reason SPP-75 found: the steam floor displaces CC that is already short. It is
small next to the 9–13 TWh coal/CC swap, which remains the DA-commitment / 2022 coal-markup object (SPP-89) and is
not touched here.

## 5. Findings

1. **The duty window alone does not fix a cycler whose on-hours don't follow load.** Lake Road runs 5–28 % of hours,
   but not in SPP's peak-load hours. Scoping the swap by the plant's own meter is the zero-DOF fix.
2. **Shard-check lesson** (Addendum A): a recipe test must treat an existing keeper field moved off its default as
   part of the arm. Round 1's seven solves were lost to it, about 35 min of parallel shard time.

## 6. Retrievability (rule 34(e)) and year set (rule 35(b))

- **On `main`** with this lane's PR: the composite `results/calibration/spp100_arm_span` (committable set), its
  sidecar and its run payload. **Promotion costs zero re-solves.**
- **Not on `main`:** the per-year legs (gitignored). The SHAs above are provenance, not a recovery route.
- **Year set:** SPP's registered years are 2019–2025, all on `spp-99`. `spp-100` covers all seven.
