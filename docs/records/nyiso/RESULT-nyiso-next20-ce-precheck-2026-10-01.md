# RESULT — NYISO-NEXT-20: CENTRAL EAST flowgate pre-check — FAIL, CE ledgered — 2026-10-01

- **Session:** NYISO-NEXT-20 (orchestrator). **Zero LP**, no shards, keeper unchanged (`2026-09-30-nyisonext18-retiree-carry-span` + stamped `-2021`).
- **Card:** `docs/records/nyiso/DESIGN-nyiso-next19-ce-flowgate-2026-10-01.md` (NEXT-19; landed on `main` in this lane's PR).
- **Probe:** `scripts/probes/nyisonext20_ce_precheck.py` → `results/phase0/nyiso/_nyisonext20_ce_precheck.json`. Method choices are fixed in the probe docstring and were set before the first run.

## Owner rulings (decision card, this session)

| # | question | ruling |
|---|---|---|
| 1 | pre-check or ledger now | **Run the §4 pre-check** |
| 2 | is a shift factor identified from RT congestion-component ratios admissible under rule 13? | **Admissible, ledgered** (a DOF-ledger entry identified from the components) |
| 3 | intake of the P-24B RT archive for 2021 and full 2023–2025 | **Intake now** |

**Intake:** `scripts/data/fetch_nyiso_zonal_lmp.py --start 202101 --end 202512 --kind rt` staged 39 new months (60 of 60 present). The months are gitignored and regenerable under the existing `.gitignore` rule. The fetch command is the recovery route (`data/raw/lmp-data/README.md`).

## Result: the flowgate FAILS. CE is ledgered as a model-class limitation.

Row tested: `CE(t) = k_F·(r·TE + (1−r)·W_F) ≤ posted limit`, with `W_F` = F load − F generation (CAMPD hourly + EIA-923 flat for non-CAMPD F plants) − NE-NY AC schedule.

| | V1 (pre-Dec-2023) | V2 (from Dec-2023) |
|---|---|---|
| `r` (median over active 5-min intervals) | 0.687 (108,063) | 0.767 (9,909) |
| `k_F` (through-origin fit on active hours) | 0.650, R² 0.969, resid sd 282 MW | 0.675, R² 0.989, resid sd 279 MW |

| year | P-1 exceedance (≤ 10 %) | P-2 binding lift (≥ 2.0) | P-3 months within ±0.10 (≥ 10) | CE-active hours |
|---|---|---|---|---|
| 2021 | 9.1 % ✔ | **1.64 ✘** | 10 ✔ | 3,600 |
| 2022 | **11.6 % ✘** | **1.28 ✘** | 10 ✔ | 4,319 |
| 2023 | **16.7 % ✘** | 2.81 ✔ | **9 ✘** | 1,945 |
| 2024 | 0.4 % ✔ | 5.55 ✔ | **4 ✘** | 384 |
| 2025 | 1.1 % ✔ | 4.65 ✔ | **4 ✘** | 624 |

The card's pre-registered rule: *if P-1 or P-2 fails, the 5-zone model cannot carry CE.* Both fail, and they fail **in the years CE actually binds** (2021–2023). The years that pass are the post-upgrade years, when CE rarely binds and the row would do little.

## Why (diagnostics; they do not change the verdict)

| year | lift, measured CE / limit | lift, TE / limit | lift, flowgate LHS | corr(TE, CE) | corr(LHS, CE) |
|---|---|---|---|---|---|
| 2021 | 2.51 | 1.24 | 1.64 | 0.875 | 0.911 |
| 2022 | 2.62 | 1.29 | 1.28 | 0.907 | 0.897 |
| 2023 | 3.83 | 2.20 | 2.87 | 0.798 | 0.818 |

- **The gate is reachable with real flow.** Measured CE/limit gives a lift of 2.5–3.8. The failure is in the zonal injection proxy, not in the threshold.
- **`W_F` adds almost nothing.** In 2022 the LHS tracks CE *worse* than TE alone. The ~280 MW fit residual (card risk 4: loop flow and PAR schedules) scrambles which hours are the top decile. A zonal-injection row cannot capture that.
- **DF-route analog** (`CE = α·TE`), scored the same way: P-1 17.0 / 18.2 / 15.6 % in 2021–2023. The `W_F` term improves P-1, but not enough.
- **Unmeasured Blenheim-Gilboa pumped storage** (1,160 MW in F, annual net only). With Gilboa at full output in every hour (an extreme bound), P-1 drops to 0.5–6.7 %. **So P-1 is sensitive to this gap; P-2 is the decisive failure.** A constant shift in W_F barely changes the decile ranking.
- **P-3:** V1 is stable (10 of 12 in 2021 and 2022; the misses are Jul–Aug 2021 and Aug / Nov 2022, matching card risk 1). V2 is unidentified: monthly r ranges from 0.06 to 2.65.

## What this closes, and what it does not

- **Ledgered:** the CE-hour spread (2021 $2 model vs $19 measured) is a model-class limitation of the 5-zone network. It is now in the keeper's matrix stamp and in `nyiso_fg_split`'s evidence (cell stays **R**).
- **Not built:** no ScenarioConfig field, no PRECOMMIT, no shard. The DOF entry for `r` (ruling 2) is moot until a design passes.
- **Re-open only on new evidence:** hourly sub-zonal (bus- or PAR-level) injections, or published NYISO shift factors. Do not lower upstate offers to close the residual (rules 1 and 19).
- **Bug found and fixed before the verdict:** the first run read CAMPD's `facilityId` (a string) against integer plant codes. That silently replaced F's hourly fossil output with a flat annual mean. The numbers above come from the corrected run, with method and gates unchanged.

## Retrievability (rule 34 (e))

No bundles were produced. The probe JSON is committed. The RT archive is regenerable with the fetch command above.
