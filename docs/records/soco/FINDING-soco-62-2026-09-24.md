# FINDING — SOCO-62 (2026-09-24): the 2023 CT_PEAKER / ST_GAS split is boiler commitment, and no admissible input reaches it — no solve spent

**Lane** SOCO-62 · **DATA PROFILE** soco · **Model** Opus (rule 27).
**Keeper / control of record** `2026-09-24-soco61-dark-unit` (bundle `results/calibration/soco61_dark_unit_span`),
unchanged. Precondition verified at `origin/main` `b024e34c`: `keepers/SOCO.json` names it, and no
`claude/soco62*` ref existed.
**Per-plant legs** recovered at zero LP from the SOCO-61 shard SHAs (`git fetch origin <sha>` worked for all
three): 2023 `4cc73989…`, 2024 `b13d473e…`, 2025 `418c7be6…` → `results/calibration/soco61_arm_<Y>` (gitignored,
0 files tracked).
**Probe** `scripts/probes/_soco62_phase0.py` (zero LP; subcommands `plants decomp floorcap monthly ctbasis parasitic`).
**LP cost: zero.** No shard launched, no run registered, nothing promoted or pruned.

---

## 1. HEADLINE

**Object chosen: (1), the 2023 ST_GAS / CT_PEAKER rows.** Phase 0 measured all three leads, and
**none reaches the object through an input this lane may arm.** Per the lane's own rule, that is stated
ex ante and no lever is taken.

| lead | measured | verdict |
|---|---|---|
| (1) ST commitment — what `soco_gas_st_campaign_commitment` (K) does not reach | The deficit is **66 % / 79 % commitment HOURS** (2023 / 2024) at the four campaign plants. A floor at the registered campaign level recovers **at most 0.61 / 0.82 TWh** of the 4.68 / 4.32 TWh, even if every measured synchronized hour were committed. | Closed: a floor can't reach it. Loading a committed boiler above min needs a cost separation. |
| (2) CT start cost | The only registered path to put a start cost on the CT econ/peak tranches (10.9 of 12.8 TWh) is `tranche_startup_amortization` (**G**). No other SOCO-applicable start-cost input exists. | Closed by governance. Not reopened. |
| (3) 2023-specific inputs | No 2023-specific input found. The CT excess is spread over ~15 plants, and no over-dispatched CT unit is dark in any year. The three zone prices never separate. The 2023/2024 gap follows the price band. | Same defect as 2024, on a larger marginal block. |

**Why the split is out of reach.** The split sits on a near-tie between two classes:

- **CT side:** the over-dispatched CTs carry `mc` 34.4–35.3 $/MWh: Tenaska Georgia 34.58, Walton County 34.38,
  Calhoun 35.07, 7709 35.31.
- **Boiler side:** the boilers carry 34.9–37.5 $/MWh: Greene 34.92, Watson 35.38, Yates 36.71, Gaston 37.55.
- **Why the real fleet splits them anyway:** SOCO operates boilers in weeks-long campaigns and CTs in ~9 h
  blocks. Two real features produce that:
  - CT start costs;
  - boiler incremental heat rate below the average.

  At the identity bands SOCO must carry (G5), the LP has neither.

Both instruments that would carry them are closed:

- **start costs:** `tranche_startup_amortization` is G;
- **incremental heat rate:** a SOCO band away from 1.0 is refused by G5, and this lane must keep every band at 1.0.

## 2. THE ROWS (keeper, committed bench, `_soco58_checkd.py`)

| year | class | model | actual | Δ | share | margin to ±3.00 pp |
|---|---|---|---|---|---|---|
| 2023 | ST_GAS | 3.797 | 9.293 | −5.50 | −2.26 pp | 0.74 pp |
| 2023 | CT_PEAKER | 9.562 | 4.330 | +5.23 | +2.19 pp | 0.81 pp |
| 2024 | ST_GAS | 2.924 | 7.615 | −4.69 | −1.81 pp | 1.19 pp |
| 2024 | CT_PEAKER | 6.765 | 4.407 | +2.36 | +0.98 pp | 2.02 pp |
| 2024 | CC_REGULAR | 113.448 | 110.305 | +3.14 | +2.19 pp | 0.81 pp |

The 2023 CT + ST total is almost right: **13.36 model vs 13.62 actual TWh**. The error is the **split**, not
the level.

## 3. LEAD (1) — THE DEFICIT IS COMMITMENT HOURS, AND A FLOOR CANNOT DELIVER IT

The deficit at the four campaign-duty plants (`campd_gas_st_campaign_params_SOCO.csv`, flag `ok`) splits
exactly into:

- **hours part** = (H_act − H_mod) × L_act
- **loading part** = H_mod × (L_act − L_mod)

Here H is synchronized hours and L is mean MW while synchronized. H_act is the artifact's own per-year count;
L uses benchmark TWh.

| 2023 | H_act | H_mod | L_act MW | L_mod MW | hours part | loading part |
|---|---|---|---|---|---|---|
| Gaston (26) | 4,888 | 2,453 | 338 | 292 | 0.824 | 0.113 |
| Jack Watson (2049) | 8,451 | 5,111 | 387 | 234 | 1.292 | 0.781 |
| Yates (728) | 7,739 | 4,607 | 289 | 162 | 0.906 | 0.587 |
| Greene County (10) | 6,592 | 6,355 | 199 | 179 | 0.047 | 0.132 |
| **total** | | | | | **3.070** | **1.613** (deficit 4.683) |

In 2024 the same split gives **3.405 / 0.916** (deficit 4.321). Barry (3) accounts for the rest of the class
row (−0.60 / −0.19). It is standby iron at a 6.3 % synchronized share, and the derive's duty gate correctly
refuses it.

**The ceiling on a floor** (`floorcap`): suppose every measured synchronized hour the model leaves idle were
committed at the registered campaign level, `min_load_frac × class_capacity`. That is 67 / 72 / 59 / 70 MW
at the four plants. The added energy is **0.606 TWh (2023) and 0.824 TWh (2024)**, or 13 % and 19 % of the
deficit.

- The floor's level is measured correctly (p5 of synchronized output), so raising it would be a fitted value.
- What the model lacks is a boiler that is economic *above* its floor once committed. That is a cost
  separation, which is leads (2) and (3) of SOCO-53 §2.2–§2.3, not a commitment state.

The monthly profile says the same thing (`monthly`, model − benchmark plant block, GWh):

- **ST_GAS** is short in every month of 2023, by −285 to −633 GWh.
- **CT_PEAKER** excess is concentrated in Jun–Sep 2023 (+3.77 TWh of +5.69).

Boilers carry campaign energy year-round. In the model, CTs pick it up only when the price reaches their band.

## 4. LEAD (2) — NO REGISTERED START-COST INPUT OTHER THAN THE G'D OBJECT

`compute_monthly_markup` (`model/commitment.py`) is P1's only start-cost channel, and it prices tranches as
follows:

- **CT `_committed` tranche:** carries the NREL $/MW start amortized over P0 run lengths.
- **Econ / peak tranches:** carry a start only under `tranche_startup_amortization` (`data/fleet/assembly.py`,
  the `_fsp_econ` / `_fsp_peak` limbs). That field is **G** for SOCO with no reopen condition (SOCO-53).
- **ERCOT offline-increment offer objects** (`ercot_faststart_pool_offer`, `ercot_offline_commit_offer`):
  market-offer constructs, `.` in SOCO's shard.

Nothing else reaches the CT econ/peak tranches, so **no admissible SOCO start-cost input exists.** SOCO-53d
refused the other CT-side route, a CT min-run floor, because it pushes CT the wrong way.

## 5. LEAD (3) — NOTHING 2023-SPECIFIC

- **Per plant** (`plants`): the 2023 CT excess is spread over ~15 plants. The largest are Tenaska Georgia +2.07,
  Calhoun +1.19, Walton County +0.93, 7709 +0.92 and Washington County +0.50 TWh. The 2024 excesses are the
  same plants, smaller.
- **CAMPD** shows every one of those CTs running tens to hundreds of hours a year, with none dark.
  - Calhoun's 2023 low (357 CAMPD unit-hours against the model's 2,401 plant-hours) is economic, not an outage.
  - The outage overlay excludes CT peakers by convention, and that convention holds.
- **Zones:** the three SOCO zones never separate in price in either year (0 hours > $0.50/MWh). No congestion
  input exists to find.
- **Nuclear:** it matches in both years (51.92 vs 52.14 TWh; 62.92 vs 63.06 TWh). Vogtle 4's 2024 energy
  shrinks the block that lands in the CT/ST price band:

  | year | hours at 34–38 $/MWh | hours ≥ 38 $/MWh |
  |---|---|---|
  | 2023 | 1,407 | 753 |
  | 2024 | 471 | 205 |

  The 2023 row is thin because more of the year prices inside the near-tie, not because a 2023 input is wrong.

## 6. TWO SIDE LEADS MEASURED AND CLOSED

- **Heat-rate basis asymmetry.** CT heat rates are measured on the loaded window (≥ 0.8 × p95); ST on
  operating hours (opTime ≥ 0.99, fixed ex ante in the ST deriver's docstring and never swept). Put on the ST
  basis, SOCO's CTs move by only **+1.13 %** (generation-weighted, `ctbasis`), about $0.4/MWh. Too small to
  move the split. Flipping the ST basis instead would re-derive a frozen choice on a residual (rule 23), so it
  is refused.
- **Parasitic factors.** `parasitic_load_factors.parquet` carries **no SOCO row**, so every SOCO CAMPD heat
  rate uses class defaults (SOCO-54 §9.6). The in-memory census (`parasitic`) shows the measured plant-annual
  net/gross is **misaligned** to a heat-rate conversion:
  - 16 of 24 CT/ST plant rows are `out_of_band`;
  - the in-band CT values (Tenaska 0.891, Calhoun 0.894) fold a low-CF peaker's all-year auxiliary draw into a
    per-running-MWh factor;
  - multi-class sites (Gaston, Greene, Watson) blend coal or CT with gas boilers.

  Rule 14's misalignment exception applies, so rule 14 does not make this lever right as-is. **Routed** as a
  cross-ISO intake with a unit-grain construction, not taken.

"If the only argument for an arm were that 2023 ST_GAS passes, it would not be taken." No candidate here has
any other argument.

## 7. GOVERNANCE / GATES

- No `ScenarioConfig` field added. No bundle, sidecar, payload or bench part written. No offer band touched,
  and no `authorized_price_tuning` key.
- The keeper's reads are unchanged (C1 14/14 · free 10/10 · C2/C4/C6/C8 PASS · C3a/b/c UNSCORABLE · grade
  5/5/0 · DOF 13/1). The scorer's literal "PHYSICALLY-CALIBRATED (PRICE UNSCORED)" is not SOCO's
  determination.
- **E13 standing:** `2026-09-20-soco53g-prb-own-iso` is still unruled. Rule 31 forbids deleting it. **Owner
  question, re-raised:** decline it so the next promoting SOCO lane can prune it? (Standing recommendation:
  decline.)
- **Matrix (rule 28(b)):** no verdict changed. Reach notes were added to `soco_gas_st_campaign_commitment` (K),
  `tranche_startup_amortization` (G) and `measured_ct_heat_rates` (K) in the SOCO shard, plus a §5.8 note.

## 8. ROUTED

1. **The object is a cost separation between committed boilers and CT blocks.** SOCO's governance forecloses
   both real carriers, CT start costs (G) and boiler incremental HR (G5 identity bands). Only an owner ruling
   on G5's scope can open this.

   **The question for the owner:** may SOCO carry *measured* incremental-HR `phys_*` bands (CEMS input-output
   slopes; physics, not price tuning) while every price-tuning band stays 1.0?
2. **Parasitic factors for SOCO**, needing a unit-grain / running-hours construction (§6). This is a
   cross-ISO intake.
3. **2024 CC_REGULAR** (+3.14 TWh, margin 0.8 pp) and the **CC per-plant 9.28 TWh**: unchanged, and no
   admissible input reaches them (SOCO-61 §4).
4. **Leftover shard branches** (the owner must remove them; a session cannot delete refs):
   `claude/soco61-arm-{2023,2024,2025}`, `claude/soco60-arm-*`, `claude/soco60-armB-*`. SOCO-62 created none.

## 9. WHERE EVERY BYTE LIVES

Nothing was solved, so nothing is promotable and there is no promotion question for this lane. The keeper
bundle on `main` is untouched. The recovered per-plant legs `results/calibration/soco61_arm_<Y>` are
gitignored inputs, not results, and exist on this container only.

## Log entry

```
## soco-62 — 2026-09-24

THE 2023 CT_PEAKER / ST_GAS SPLIT IS BOILER COMMITMENT, AND NO ADMISSIBLE INPUT
REACHES IT -- ZERO LP SPENT. Keeper 2026-09-24-soco61-dark-unit unchanged.

Phase 0 on the keeper's own per-plant legs (recovered at zero LP from the
SOCO-61 shard SHAs). 2023 CT+ST total is right (13.36 vs 13.62 TWh); the split
is wrong. At the four campaign-duty plants the ST deficit (4.68 / 4.32 TWh in
2023 / 2024) is 66 % / 79 % COMMITMENT HOURS (Watson 5,111 vs 8,451 synced h;
Yates 4,607 vs 7,739; Gaston 2,453 vs 4,888) -- but a floor at the registered
campaign level can add at most 0.61 / 0.82 TWh even at full measured sync. The
LP never finds a committed boiler economic above its floor: CTs at 34.4-35.3
$/MWh sit at or below boilers at 34.9-37.5, and the real separators (CT start
costs, boiler incremental HR) are closed by tranche_startup_amortization G and
the G5 identity bands. Lead 2: no SOCO start-cost input other than the G'd
object. Lead 3: nothing 2023-specific -- excess spread over ~15 CT plants, none
dark, zones never separate, nuclear matches; 2023 has 2,160 hours in the CT/ST
price band vs 676 in 2024 (Vogtle 4). Side leads closed: CT loaded vs
operating HR basis +1.13 % only; SOCO parasitic factors misaligned to a HR
conversion (16/24 rows out of band). No lever taken, no shard, no registration.

OWNER QUESTIONS: (1) may SOCO carry MEASURED incremental-HR phys_* bands while
price bands stay 1.0 (the only admissible route to the split)? (2) decline
2026-09-20-soco53g-prb-own-iso (E13)? Leftover refs for the owner:
claude/soco61-arm-*, claude/soco60-arm-*, claude/soco60-armB-*.
Records: docs/handoffs/FINDING-soco-62-2026-09-24.md,
scripts/probes/_soco62_phase0.py.
```
