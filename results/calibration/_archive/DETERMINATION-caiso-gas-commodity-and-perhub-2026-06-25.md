# CAISO gas-commodity-spot body + per-hub import netting — determination (2026-06-25)

Branch: `claude/caiso-gas-cost-import-netting-p91egg`. Task: (PRIMARY) price the
marginal gas median on commodity-spot gas, not F923 all-in delivered; (SECONDARY)
per-hub signed legs for import netting. Solve all 3 years; lead with the
determination + mean-LMP Δ.

## TL;DR — both requested levers are ALREADY implemented and ACTIVE in the keeper

The task premise (body bounded at ~$46–50 = HR×**F923-delivered** gas + CARB) is
the **2026-06-19** pre-overlay state. Since then **both** levers landed and are ON
in the current keeper `2026-06-23-caiso-25-corridor-deliverability`:

1. **PRIMARY — commodity-spot gas (lever B): DONE.** `--gas-hub-basis-overlay`
   reprices every CAISO gas unit at **Henry-Hub-month + the measured SoCal/PG&E
   citygate basis** (the commodity spot) and **drops the F923 pipeline reservation
   as sunk**. The data is **in repo** (`data/raw/gas_basis_by_iso_month.csv`, CAISO
   2015–2025, EIA `N3050CA3 − Henry Hub`, refreshed by the `fetch-eia-gas-prices`
   workflow) — **not env-blocked**. Verified in this HEAD reproduction:
   `hub-basis overlay (CAISO 2024, monthly): 1139 gas generators repriced … 12/12
   months`. Gas $/MMBtu drops **F923 $4.31 → citygate $3.38 (2024)**, $9.02→$6.96
   (2023, real Feb-23 SoCal blowout), $4.68→$3.96 (2025). Paired with
   `--caiso-import-gas-coupling` so desert-SW gas imports track the same commodity
   spot (volume discipline). Grounded: sunk-cost principle, forward-reproducible,
   no residual fit (rules #10/#11).

2. **SECONDARY — per-hub signed legs: DONE.** `--caiso-per-hub-intertie` splits the
   pooled `WECC_import` node into the two real signed corridors (Malin/COI → NP15,
   Palo Verde/Path-46 → SP15), each priced at its own measured hub, one net
   direction per hour per corridor; `--caiso-corridor-flow-limit` adds the measured
   diurnal deliverability cap. Exactly the topology of
   `DIAGNOSIS-caiso-perhub-overimport-diurnal-2026-06-23`.

**Reproduced at HEAD** (bundle `caiso_gascommodity_repro_3yr`, all 3 years, same
config, current `origin/main`): body marginally **lower** than the stale-sha keeper
(2024 NP15 47.4→46.0), no regression.

## Mean-LMP Δ (this reproduction, report [3] system price)

| year | model avg | model p50 | actual DA mean | actual RT mean | Δ vs DA | Δ vs RT |
|---|---|---|---|---|---|---|
| 2023* | 62.96 | 53.96 | 49.84 | 43.83 | +13.1 (+26%) | +19.1 (+44%) |
| 2024 | 44.87 | 45.77 | 35.85 | 32.98 | +9.0 (+25%) | +11.9 (+36%) |
| 2025 | 48.13 | 49.96 | 34.62 | 33.63 | +13.5 (+39%) | +14.5 (+43%) |

*2023 is the data-blocked year (static-ladder hub fallback; intertie LMP missing for
~1704 Jan–Feb hours, and the actual LMP series itself is only 7175/8760 finite —
OASIS retention, see HANDOFF Fix C). Its over-price is expected and not closable
until that gap is filled.

## Why commodity-spot gas does NOT pull the median to ~$34 (the core finding)

Even with gas at the **commodity spot** ($3.38, 2024), the marginal gas-CC SRMC is
a floor **above** the actual median:

```
HR ~7.3 × $3.38  +  CARB (0.37 t/MWh × $35.23) ~$13  +  VOM ~$3-4  ≈  $41-43
```

The reproduction's 2024 system **p50 = $45.77** sits right at this floor plus a thin
markup. The actual RT median is **$33.99** — **below** CA gas-CC cost. This
empirically confirms **2026-06-19 diagnosis point #4 with lever B implemented**:
reality clears its median *under* an efficient CA CC's commodity-spot cost (abundant
cheap hydro + imports + sub-SRMC bilateral gas bids set the margin there), so
**no re-pricing of gas can reach $34** — the F923→citygate move was the available
$/MMBtu and it is already taken. Pushing lower would require cutting measured gas/
carbon below their true level or a fitted import shape — both forbidden (#10/#11).

The residual above the floor ($45.77 vs the ~$42 SRMC) is the standing **in-state
midday over-pricing** item (`DIAGNOSIS-caiso-body-overprice-2026-06-21`,
`…-perhub-overimport-diurnal`): with imports correctly volume-limited, gas sets more
midday hours than reality, where neighbors' idle solar would clear cheaper but is
not deliverable into a simultaneously-long CAISO.

## Gas VOLUME guardrail (task: stay near EIA-923 76.0/67.7 for 2023/24)

| year | model gas TWh | EIA-923 | Δ |
|---|---|---|---|
| 2023 | 77.95 | 76.04 | +1.9 (+2.5%) ✓ |
| 2024 | 77.62 | 67.68 | +9.9 (+14.7%) ✗ over |
| 2025 | 77.82 | 55.18 (partial vintage) | n/a |

2023 is on target. 2024 over-burns ~10 TWh — but this is a **+7.1 TWh total
over-generation drift** (energy-balance warning: model gen 197.7 vs EIA-930 net gen
190.6), driven by 2024 **under-import** (−28.85 vs −32.38 TWh) + **solar over**
(47.6 vs EIA-930 44.6) — **not a lever-B artifact** (gas commodity-spot + import
coupling is exactly the mechanism that keeps gas from over-running further). Solar-
over and the import diurnal phase are separately tracked; load is correct (handoff).

## Net interchange (per-hub signed legs)

| year | model | actual EIA-930 | corr |
|---|---|---|---|
| 2023 | −29.73 | −28.87 ✓ | +0.97 (ladder) |
| 2024 | −28.85 | −32.38 (under 3.5) | +0.12 |
| 2025 | −39.71 | −36.16 (over 3.5) | +0.16 |

Per-hub netting holds annual volume within ~3.5 TWh; the diurnal phase residual
(corr +0.12/+0.16) is the deliverability item already flagged as priority-2.

## Determination

Both requested levers are in the keeper and active at HEAD; the disciplined outcome
(matching `DIAGNOSIS-caiso-body-overprice`'s "keep the keeper") is that **no
grounded single lever closes the body to ~$34**: commodity-spot gas is already
applied and its SRMC floor (~$42) structurally exceeds the actual median; per-hub
topology is already correct. The keeper stands, reproduced at HEAD.

### Open items (handed forward, all out of the "re-price gas / fix netting" scope)
- **2023 intertie-LMP + actual-LMP data gap** (HANDOFF Fix C): ~1704 missing
  Jan–Feb hub hours + the partial actual series. 2023 price work is blocked until a
  grounded gap-fill lands.
- **In-state midday over-pricing** (`DIAGNOSIS-caiso-body-overprice`): the ~$4
  above the SRMC floor; needs a measured midday-deliverability lever, not a gas or
  import re-price.
- **2024 over-generation drift** (+7 TWh: under-import + solar-over) — the gas
  over-burn lives here, not in the gas price.

### Note on defaults (optional follow-up, not done here)
`gas_hub_basis_overlay` and the three CAISO topology levers are still passed as
explicit CLI flags; `_calibration_config` defaults `gas_hub_basis_overlay` to
NEISO-only (the help text invites "validate before flipping the default"). They are
co-dependent (cheap gas on the un-validated pooled node would over-import), so a
default-flip must move all four together or none — left as a deliberate follow-up.
