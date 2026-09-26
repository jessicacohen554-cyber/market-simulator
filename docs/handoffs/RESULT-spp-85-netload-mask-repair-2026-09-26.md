# RESULT: SPP-85, net-load-mask repair of SPP's CAMPD outage extracts (7-year control + arm)

**Recommendation under the pre-registered rule (PRECOMMIT §6): DO NOT PROMOTE as-is.** Conditions
(a)–(d) hold, but (e) fails narrowly: one new D-4 per-unit conduct row (§3). The owner may still promote
on rule 14 (§5). Nothing was promoted, pruned or deleted (rule 31).

Records:
- PRECOMMIT: `PRECOMMIT-spp-85-netload-mask-repair-2026-09-26.md`, pinned `0ff620d11d91797313f5f565b5e94ff3b123330b`
  before any shard launched.
- Phase 0: `FINDING-spp-85-coal-outage-basis-2026-09-26.md`.
- Registered run: `2026-09-26-spp-85-netload-mask`, bundle `results/calibration/spp85_arm_span`.

## 1. What ran

- **Seven shards, one per year 2019–2025** (rule 36). Each solved the keeper `rspp_span` recipe as a
  control, then the same recipe with `--set unit_outage_netload_mask_repair=true` as the arm. Both ran
  at the pinned SHA in the same container.
- **The parent composed** both spans with `_rspp_compose.py --require unit_outage_netload_mask_repair=<true|false>`.
- **Shard-check incident (instrument defect, fixed).**
  - The first check diffed each leg against the committed keeper. At HEAD, `replay_keeper` translates the
    keeper's bare `COAL` offer-curve key to its subclasses, which already carry the identical 0.93 bands.
    So control and arm both showed that one key.
  - All seven shards correctly stopped. On the parent's ruling they pushed unchanged bundles.
  - The corrected check diffs arm against same-shard control. **It passes on all seven legs:** the recipe
    diff is exactly the one field, the gas price matches, six extract sha256 values match, and the resolved
    CAMPD path is the `-netloadmask-` extract.
- **HEAD drift (G-DRIFT LIVE).** Control − committed keeper demand-weighted P1 price is 0.000 in 2019–22
  and 2025, −0.202 in 2023 and −0.017 $/MWh in 2024. The arm is judged against its control.
- **Retrievability (rule 34(e)).**
  - The per-year legs are on shard branches `claude/spp85-<Y>`:
    - 2019 `0d0bf61784ff592ad07609608399495ef9e8118b`
    - 2020 `fc02415689e963779fcff537ddf602ebfc38c8c1`
    - 2021 `4fc57c60188161905fb98dc31d6d506f51adf8ff`
    - 2022 `fdce71950c94d3b69e53e2681281a35079a9a51e`
    - 2023 `f3ecf33b9afd2e9a4505cf566344773686c851d2`
    - 2024 `a4cf4b13e932d0696d6ff5eed18c55f5d738d48e`
    - 2025 `3fdcb71ac8f57d306faea95f3f291a452fb07973`
    - These SHAs are provenance, not durable storage (rule 33(d)).
  - The arm composite is committed on this lane's branch in its registered shape. If the branch is lost,
    re-solving costs about 7 × 12 min of shard wall time.
  - Controls and per-year dirs are gitignored and stay out of `main` (rule 29(c)).

## 2. Arm − control, per year (P1)

| year | COAL_PRB TWh | COAL_LIG TWh | CC_REG TWh | CT_PEAK TWh | ST_GAS TWh | wind TWh | price $/MWh | slack MWh ctl → arm |
|---|---|---|---|---|---|---|---|---|
| 2019 | +1.389 | +0.077 | −0.718 | −0.563 | −0.151 | −0.001 | **−0.228** | 0 → 0 |
| 2020 | +1.246 | +0.394 | −0.654 | −0.620 | −0.212 | −0.100 | **−0.417** | 0 → 0 |
| 2021 | +3.516 | +0.287 | −2.133 | −1.091 | −0.146 | −0.341 | **−2.099** | 0 → 0 |
| 2022 | +2.816 | +0.550 | −1.792 | −0.995 | −0.253 | −0.281 | **−2.279** | 389.6 → 46.8 |
| 2023 | +2.059 | +0.089 | −0.781 | −0.832 | −0.351 | −0.132 | **−0.509** | 0 → 0 |
| 2024 | +2.626 | +0.292 | −1.045 | −1.278 | −0.359 | −0.155 | **−0.717** | 1,115.2 → 787.1 |
| 2025 | +3.198 | +0.125 | −1.451 | −1.188 | −0.478 | −0.123 | **−0.885** | 76.9 → 76.9 |

- E2 (coal up every year) holds.
- E3 (price down every year) holds.
- E7 (slack not up) holds. Dump is 0 throughout, and hours above $200 fall or hold.
- Restored coal also displaces some wind (up to −0.34 TWh), reported.

## 3. Scored (rubric at HEAD; keeper = `2026-09-24-r-spp-corrected-inputs`)

**Determinations:**

| span | keeper | arm |
|---|---|---|
| 2023–25 (designated train span) | CALIBRATED (C3c ledgered) | **CALIBRATED** (C3c ledgered) |
| 2019–22 (validation, reported, not gating; rule 30(c)) | NOT-YET | NOT-YET |

**Every criterion that moved, keeper → arm:**

| criterion | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| C3a mean price | +13.3 → +12.2 % F | +21.2 → +18.6 % F | **+10.0 F → +4.4 % P** | +1.6 → −3.6 % | −2.3 → −5.2 % | −3.9 → −6.8 % | −1.1 → −4.2 % |
| C3b monthly NRMSE | 0.161 → 0.152 | 0.286 → 0.264 F | 0.132 → 0.170 | 0.182 → 0.177 | 0.167 → 0.170 | 0.165 → 0.167 | 0.154 → 0.146 |
| C1 COAL_PRB TWh vs 923 | +0.96 → +2.38 | −4.24 → −2.96 | **+6.76 → +10.31 F** | +9.58 → +12.40 F | +0.59 → +2.42 | −0.18 → +2.44 | (prelim) |
| C1 CC_REGULAR TWh | +3.78 → +3.06 | +0.39 → −0.26 | **−6.88 → −8.98 F** | **−7.94 → −9.72 F** | −3.27 → −4.30 | −4.32 → −5.34 | (prelim) |
| C4 gas NRMSE | 0.123 | 0.194 → 0.193 | **0.289 → 0.316 F** | 0.320 → 0.354 F | 0.188 → 0.200 | 0.218 → 0.227 | 0.249 → 0.268 |
| C8 ST_GAS forced share | 13.1 → 13.6 % | 15.2 → 15.6 % | 25.6 → 26.9 % | **29.4 → 31.5 %, GROUNDED pass** | 20.9 → 22.2 % | 19.3 → 20.4 % | 17.1 → 17.8 % |

- The C8 move is a denominator effect. ST_GAS total falls from 7.98 to 7.61 TWh, while forced energy
  barely moves (2.350 → 2.393 TWh).
- D-2 flags it above the 30 % cap. The rubric's rule-20 escalation grounds it: D-4 clears for
  `st_gas_mustrun_per_plant`, profile r 0.96 and off-peak CV ratio 1.39.
- **D-4: one new row.** 2021 `coal_mustrun`, plant 108 (Holcomb). The incumbent coal floor re-applies in
  restored hours where Holcomb's own meter reads zero (52 % of 1,071 binding hours).
  - Holcomb already fails this rider in 2019 / 20 / 22 / 24 in the keeper, the control and the arm.
  - The keeper's other D-4 rows (Mooreland 3008 ST_GAS) are unchanged.
- **DOF.** `build_dof_ledger --check` reads current. There are 5 entries / 3 residual, as in the keeper. The
  only change is `offer_curve_by_group` scalars 72 → 67: the translated bare `COAL` key drops out, and the
  subclass values are identical. **Zero new free parameters.** C6 governance PASS.
- **Rule-1 channel untouched.** The offer multipliers are 0.93 everywhere, SHA-identical to the keeper net
  of the bare-COAL translation.

## 4. Against the pre-registered recommendation rule (PRECOMMIT §6)

| condition | verdict |
|---|---|
| (a) E1 on every leg | **PASS** (corrected check; §1) |
| (b) E2 sign every year | **PASS** |
| (c) E7 | **PASS** |
| (d) zero new DOF | **PASS** |
| (e) D-4 shows no new off-window binding | **FAIL**: Holcomb 2021 `coal_mustrun` per-unit conduct row |

**Rule outcome: do not recommend promotion.** It was fixed before the solve, and I am not re-reading it now.

## 5. What the result says (rules 1 / 14)

- **The repair is structurally correct and stays built.** The recorded in-merit filter was inert for SPP.
  With it live, the keeper's coal outage basis moves toward SPP's own published outage in every year.
- **It exposes compensation, which is rule 14's signature.**
  - With 0.5–1.0 GW more coal available, the model **over-dispatches coal against EIA-923** (COAL_PRB 2021
    +10.3, 2022 +12.4 TWh) and under-dispatches CC (2021 / 22 about −9 TWh).
  - So part of the over-counted coal outage was silently holding coal generation down. The coal-vs-gas
    merit order was wrong somewhere else, and that is the root cause:
    - the coal offer and commitment side (SPP-41 / 44 / 69 / 75 / 77's 2022 crossover object);
    - Holcomb's `coal_mustrun` floor, which already asserts must-run on a metered-offline plant in 4 years.
  - Rule 14 says keep the accurate input and fix that root cause, not bury it back in the outage basis.
    That is the case for promotion anyway. The case against it is the pre-registered D-4 condition and
    the new validation-tier C1 / C4 failures.
- **Price effect.**
  - It helps 2021 C3a (a FAIL becomes a PASS) and moves 2019 / 20 by 1.1–2.6 pp toward band.
  - It lowers 2023–25 by about 3 pp. All three stay inside ±10 %, and the train span stays CALIBRATED.
  - It is **not** a lever for 2019–20 C3a, which still FAILs at +12.2 / +18.6 %.

## 6. Promotion question (rule 31): the owner's to decide

- **Option A, hold (the recommendation).** The field stays built and default-off. The matrix cell stays O.
  Successors:
  1. Holcomb `coal_mustrun` floor-window conduct (pre-existing in 4 years).
  2. The coal-vs-CC merit order the restored availability exposes (2021 / 22).
- **Option B, promote on rule 14.** Promote `2026-09-24-r-spp-corrected-inputs` → `2026-09-26-spp-85-netload-mask`.
  Headline 2023–25 stays CALIBRATED. The validation tier gains C1 / C4 rows and loses C3a 2021.
  - The run is registered and its composite is committed in registered shape.
  - The year set {2019..2025} is covered by the one bundle (rule 35(b)/(c)).
  - Promotion then prunes `rspp_span` in the rule-35 order.

## 7. Rules

- **Rule 1:** no multiplier touched; nothing swept; one config across all years.
- **Rule 13:** the removal test is net-load × own-CEMS, forward-regenerable. A realized-LMP test was refused.
- **Rule 19:** layers replaced, not stacked; no new floor.
- **Rule 23:** no frozen setting changed; measured-source basis.
- **Rule 25:** SPP's own data only. SOCO / NWPP's identical missing key is left to their lanes.
- **Rule 28:** matrix row + 9 shard cells were added with the field. SPP cells were updated in this session.
- **Rules 31–36:** one shard per year; full bundles pushed; bytes fetched and verified before all seven
  shards were archived; nothing deleted.
- **Housekeeping for the owner** (sessions cannot delete refs):
  - `claude/rspp-2019` … `claude/rspp-2025`;
  - `claude/spp85-2019` … `claude/spp85-2025`.
