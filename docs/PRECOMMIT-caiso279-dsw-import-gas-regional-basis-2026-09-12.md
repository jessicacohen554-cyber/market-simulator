# PRECOMMIT — caiso-279: **THE CAISO LMP OVERSHOOT IS IDENTIFIED.** The desert-SW gas-import coupling prices Palo Verde imports off the **SoCal citygate**, so in December 2022 it charged 4 GW of imports a **California pipeline-congestion premium the exporting region never paid**. Re-base it on the desert-SW's own published gas.

**Session caiso-279, 2026-09-12. CAISO only (rule 25 `[R-ISO-SCOPE]`). Written and pushed BEFORE
any solve; the shard pins this document's own commit SHA (rule 32 `[R-SHARD]` (c) 1).**
Keeper / control: `2026-09-12-caiso-275-gascoupling`; folded 2022 rung bundle
`results/calibration/caiso275_B_gascoupling_2022` (G-CTRL **form 4** — the committed keeper IS the
control, rule 29(b); **no control solve is spent**).

---

## §1 — WHAT THE OVERSHOOT ACTUALLY IS (measured, zero LP, this session)

The owner's framing — *"a level issue where it's running over every year"* — resolves, on
measurement, into something much narrower.

**(a) The 2022 gate is 1.130 $/MWh away, not 9.579.** Model load-weighted 94.069 (reproduced to
the milli-dollar from the committed `system_2022.parquet`), gated actual `rt_lw` 84.490, band
±10 % ⇒ ceiling **92.939**. C3a-2022 is the rung's **only** failing criterion.

**(b) 40 % of the annual miss is DECEMBER.** Monthly decomposition against the committed bench:

| | Dec | Jan | Feb | all other months |
|---|--:|--:|--:|--:|
| model − actual $/MWh | **+49.51** | +11.71 | +11.69 | +1.76 … +9.42 |
| contribution to the annual gap | **4.000** | 0.910 | 0.819 | ≤ 0.750 each |

**(c) Inside December it is the LAST NINE DAYS.** Daily, load-weighted:

| Dec day | 1–22 (net) | 23 | 25 | 27 | 29 | 30 | 31 |
|---|--:|--:|--:|--:|--:|--:|--:|
| model | — | 401.5 | 361.1 | 430.2 | 432.1 | 407.1 | 414.2 |
| actual RT | — | 291.0 | 195.4 | 191.6 | 169.9 | **103.2** | **98.6** |
| actual DA | — | 317.4 | 282.2 | 296.2 | 181.9 | **130.0** | **118.7** |
| gap | **−0.7 total** | +110.5 | +165.7 | +238.6 | +262.2 | +303.9 | +315.7 |

**Dec 23–31 contributes +4.58 $/MWh of the annual gap; Dec 1–22 contributes −0.7.** The top four
days alone are **2.905** — 2.6× the 1.130 the gate needs; **Dec 30–31 alone is 1.59**.
**Both** benchmarks collapsed and the model did not, so this is **not** a DA/RT basis artifact.

**(d) It is not scarcity.** In all **744** December hours: `slack` **0.0**, `dump` **0.0**,
`reserve_price` **0.000**. Dec 29–30 prices are a flat 351.8–443.5 plateau. Marginal class from
`class_band_hourly`: `CC_REGULAR` econ (`econc00`…`econc05` all partially loaded).

**(e) And it reverses a standing kill.** caiso-276's kill #2 held that "2022 is one object —
December's dHR ranking **3 of 12**, z = **+0.51**". Recomputed on the **rule-14-preferable
EIA-923 series caiso-277 itself introduced** as the correct denominator, December 2022 is
**rank 1 of 12** at dHR **+2.143** against an ex-December mean of 0.806 (sd 0.441) — **z = +3.03**.
December **is** special. That is the **new evidence** rule 28(a) requires to reopen this area, and
it is why December is the object.

## §2 — THE DEFECT, IN THE CODE'S OWN WORDS

`model/interchange/caiso.py::inject_caiso_import_gas_coupling` (armed on the keeper,
`caiso_import_gas_coupling=True`) shifts the desert-SW gas import tranches by

    mc[row] += (iso_hub_monthly_gas_prices - iso_monthly_gas_prices)[m] x HR_tranche

where the hub series is the **SoCal citygate** print. `model/interchange/spec.py` already flags the
mismatch against itself:

> *"gas = the measured SoCal citygate weekly print (`pge_socal_citygate_weekly.csv` — **an LDC
> citygate proxy for the desert-SW border hubs, documented misalignment per rule 14: reconciled
> real data over a guess**)"*

That was the right call **when no desert-SW series was available**. It is the wrong call now, and
December 2022 is where the proxy breaks completely.

**The physical driver.** December 2022's SoCal citygate blowout was the **El Paso Natural Gas
Line 2000 outage** plus regional cold — a constraint **between** the Permian / San Juan supply
basins **and California**. `DSW_CCGT` and `DSW_CT` are Palo Verde / Path-46 (West-of-River)
resources sitting **upstream** of that constraint. They burned basin gas and never paid the
California premium. The model charges it to them in full.

**Measured, from the committed EIA state series** (`eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv`),
December 2022 delivered gas to electric power, $/MMBtu:

| CA | **AZ** | NV | NM | TX | CO |
|--:|--:|--:|--:|--:|--:|
| **28.68** | **18.65** | 15.83 | 6.18 | 5.40 | 8.48 |

## §3 — THE PRE-SOLVE DELTA (rule 29 `[R-SCREEN]` step 0 — computed before any solve)

Tranche constants are the committed ones: `HR_DSW_CCGT = 0.37/0.0531 = 6.97`,
`HR_DSW_CT = 0.55/0.0531 = 10.36` (`_CAISO_IMPORT_COUPLE_HR`); depths 1,800 MW and 2,200 MW;
base offers $68 and $110. Dec-2022 SoCal citygate mean **33.77** (weekly prints to 48.74 / 57.07);
CAISO F923 delivered **23.10**.

| tranche | depth | **current** Dec-2022 shift | **repaired** shift | **swing** |
|---|--:|--:|--:|--:|
| DSW_CCGT | 1,800 MW | **+74.3 $/MWh** | −31.0 | **−105.4** |
| DSW_CT | 2,200 MW | **+110.5 $/MWh** | −46.1 | **−156.6** |

**~94 % of the coupling's entire December shift is the operand error**: `(CA 28.68 − AZ 18.65) ×
HR` = **+69.9 / +103.9 $/MWh** of the +74.3 / +110.5 applied.

**The repriced MW can actually flow**: caiso-276 §5b measured December import utilisation
**0.4263** with **0 hours ≥ 99 %** — ~9.1 GW of headroom. So cheaper DSW offers displace the
`CC_REGULAR` econ tranches §1(d) shows are marginal.

**What the gate needs**: 1.130 $/MWh annual ÷ December's 0.0808 load share = **−14.0 $/MWh on
December**, against a measured +49.51 overshoot.

## §4 — THE ARM: ONE FIELD, ONE OPERAND, NOTHING ELSE

`caiso_import_gas_coupling_regional_basis: bool = False` (new, CAISO-gated, requires
`caiso_import_gas_coupling`). When set, the **DSW** tranches' commodity term is the **desert-SW**
published delivered-gas series (EIA `N3045AZ3m`, Arizona — Palo Verde's host state) instead of the
SoCal citygate print. **The PNW tranches are untouched** (their own basis question is separate and
is not opened here). Border CARBON stays on its own per-tranche EF, exactly as now.

* **Rule 14 `[R-ACCURATE]`** — the misalignment exception the code invoked no longer applies,
  *because an admissible measured replacement now exists*, from the same publisher and vintage as
  the CA series the mechanism already reads.
* **Rules 21/24 — ZERO free parameters.** One published series swapped for another inside an
  existing formula. No adder, no cap, no factor.
* **Rule 19 `[R-ONE-MECH]`** — re-bases an existing mechanism's operand; stacks nothing.
* **Rule 13 `[R-MEASURED]`** — forward monthly regional gas × heat rate is exactly the forecast
  construction; it regenerates for a forward year and responds to changed conditions.
* **Rule 25** — CAISO-only; no shared default, no other ISO.
* **Rule 1 `[R-STRUCT]`** — this is a structural operand correction. It is **not** the authorized
  offer-curve channel, **not** a multiplier, and **not** sized against any gate.

**Stated against the arm:** AZ *delivered* is itself a proxy for desert-SW *commodity* gas — the
mechanism's design intent is spot-to-spot. Both the incumbent and the repair are proxies; the
repair's claim is only that the **region** is right where the incumbent's is wrong. Named here so
no later session reads it as an exact series.

## §5 — SCREEN YEAR = 2022, on the mechanism's OWN operand error

Max monthly |CA − AZ| spread, computed before the solve:

| year | max monthly spread | month | mean |
|---|--:|--:|--:|
| **2022** | **10.03** | **12** | 1.35 |
| 2023 | 9.50 | 1 | 2.48 |
| 2025 | 2.41 | 10 | 1.48 |
| 2024 | 1.84 | 4 | 1.39 |

2022-12 is the largest single-month operand error in the record, by 5.4× over 2024/2025.
**Disclosed against the choice:** 2023's *mean* spread (2.48) exceeds 2022's, because Jan-2023 is
the tail of the same El Paso event; and 2022 is also the failing year. The selection is on **max
monthly footprint**, fixed here before the solve, and §6's gates **do not read C3a**.

## §6 — PRE-REGISTERED STOP GATES. They can KILL the arm; none can promote it.

| gate | requirement |
|---|---|
| **G-IDENT** | The arm's `run_config.json` differs from the control's in **exactly one** field. Demand, renewables, hydro, outages and fleet capacity byte-identical. |
| **G-FOOT** | Only `DSW_CCGT` / `DSW_CT` `mc` rows move. `PNW_*`, `DSW_solar_PV`, `WECC_scarcity` and every in-state class byte-identical off-December. |
| **G-OPERAND** | The applied December shift reproduces §3 to ±$1/MWh: DSW_CCGT −31.0, DSW_CT −46.1. An arithmetic miss voids the run. |
| **G-LIVE** | DSW import energy **rises** in December and `CC_REGULAR` econ falls; ≥ 200 December hours carry \|Δprice\| > $5. INERT ⇒ cell `I`, not `R`. |
| **G-DIR** | December Δλ is **negative** and its magnitude does not exceed the offer swing × the DSW marginal share. An overshoot beyond that means the response is not the mechanism's arithmetic. |
| **G-COLLAT** | No non-target load-bearing criterion (C1/C2/C3b/C4/C6/C8) flips PASS → FAIL for a reason other than DSW import volume. **C4-2025 is named in advance** as the most likely failure (0.298 against ≤ 0.300). |

**There is deliberately NO gate on C3a, and no gate whose satisfaction promotes the arm.**

## §7 — EXPOSURES DECLARED BEFORE THE SOLVE

1. **It may overshoot DOWNWARD, hard.** The swing is −105 / −157 $/MWh on 4 GW. December needs
   −14.0 to pass; the arm could deliver far more and put C3a-2022 **negative**. That is a live
   outcome, reported at full magnitude either way, and the factor will **not** be resized to land
   it (rule 1 (c)).
2. **2023 MOVES TOO** — Jan-2023's spread is 9.50, the same event's tail. 2023 currently **passes**
   C3a at +3.18 %; a January correction can take it negative. This is a multi-year mechanism, so
   rule 16 `[R-ALLYEARS]` / rule 34 `[R-SHARD-PROMOTABLE]` (c) apply: **the span shard solves every
   year the keeper carries — 2022, 2023, 2024, 2025 — in one invocation and one bundle.**
3. **C4** — more imports means less in-state gas. 2025's operand error is small (max 2.41), so the
   2025 effect should be minor; it is gated anyway.
4. **The determination may get worse.** If it does, that is the result. The keeper is not replaced
   by a worse run.

## §8 — GOVERNANCE

* **Rule 32 `[R-SHARD]`** — the parent spends **zero LP**: it does phase 0 (§§1–3, done), this
  PRECOMMIT, the implementation, the launch, then composition and scoring. One shard, one
  `--years 2022 2023 2024 2025` invocation, one bundle.
* **Rule 34 `[R-SHARD-PROMOTABLE]`** — the shard **pushes its bundle** to its own branch
  (`git add -f <out-dir>`); it is never gitignored on the shard side, so a promotion needs no
  re-solve. The parent keeps per-year dirs out of `main`.
* **Rule 31 `[R-RETAIN]`** — nothing solved is deleted; the promotion question goes to the owner
  explicitly before the session ends.
* **Rule 28 `[R-MECH-MATRIX]`** — a NEW `ScenarioConfig` field ⇒ duty (c): its matrix row plus a
  cell line in **every** ISO shard land in the same PR.
* **Rule 27 `[R-PUSH]`** — parent-side edits only, pushed as on-disk bytes, blob-verified.
