# FINDING — SPP-84: the keeper's outage LEVEL matches SPP's published outage in total but not by fuel; rebasing to it is not a lever for 2019–21 C3a (zero LP, 2026-09-26)

Lane: SPP-84 (SPP rubric-failure tuning). Parent: SPP-83
(`FINDING-spp-83-keeper-clears-on-offline-capacity-2026-09-26.md`). Keeper: `2026-09-24-r-spp-corrected-inputs`,
bundle `results/calibration/rspp_span`, `basis_sha` `ec13e5c2ad35c4f817cc496ff2363affb3fed2f9`.
Session base: `origin/main` `722b40f9`.
Probe: `scripts/probes/_spp84_published_outage_rebasis.py`. Numbers: `results/calibration/_spp84_published_outage_phase0.json`.
**No LP. No shard. No bundle. No PRECOMMIT. No `src/` edit. No `ScenarioConfig` field. No multiplier touched. Nothing landed under `data/`.**

## 0. Headline

1. **Target failure.** Excluding C3c, every failing criterion is already adjudicated in §5.7 (§1). The
   largest-weight one is **C3a 2019 / 2020 / 2021: +13.3 / +21.2 / +10.0 %** (model $2.8 / $3.5 / $3.8
   too dear). The charter's candidate direction was a measured gas availability input for SPP-83's
   ~6 GW gas over-availability. This lane measured the only admissible candidates that exist.
2. **EIA-860M monthly status: no seasonal lay-up.** Across all 84 monthly inventories 2019–2025, the
   keeper's own gas plants carry only **0.05–0.45 GW** of SB / OS / OA MW in any month. The keeper
   already drops non-OP units at the annual vintage (`eia860.py`, `status == "OP"`). **Closed.**
3. **SPP's own published hourly outage by fuel (`capacity-of-generation-on-outage`) is new here, and
   it is the right comparator.** Against the keeper's own unavailable MW (COD / retirement edges
   excluded):
   - **gas: the keeper carries LESS outage than SPP publishes** in 2019 / 20 / 23 / 24, by −2.35 /
     −1.39 / −1.26 / −2.19 GW (2021 −0.38; 2022 +1.04). The keeper's CT_PEAKER fleet is 94 %
     available all year: CTs have no CAMPD outage windows, and SPP's gas outage includes them.
   - **coal: the keeper carries MORE outage than SPP publishes in every year**, by **+1.18 / +2.56 /
     +2.59 / +2.40 / +2.31 / +3.40 GW** (2019 → 2024). The excess is largest in **winter**
     (2020: +4.2 / +4.0 GW Jan / Feb; 2024: +9.4 GW Feb), when coal outages should be lowest. This
     is the signature of CAMPD ≥ 5-day zero-operation windows that are **economic reserve shutdowns**
     counted as outages. It is also consistent with SPP-83's physically impossible reading that the
     keeper's coal available sits **below SPP's coal online** (−0.5 to −1.7 GW) in every year.
4. **So SPP-83's ~6 GW gas excess is ~1.3–2.4 GW missing CT/gas outage plus ~4 GW of genuinely
   uncommitted offline capacity.** The published outage cannot own the remainder: that is still a
   commitment state (SPP-82 / SPP-83).
5. **Re-clear instrument (Leg C): rebasing BOTH families pro rata to SPP's published hourly totals
   is not a lever for the target.** All-hours Δ price is **+0.76 / −0.26 / +0.27** in 2019 / 20 / 21,
   against a needed **−2.8 / −3.5 / −3.8**. It also costs the train-adjacent years (2022 −3.79,
   2023 −0.74). It does not carry SPP-79's pairing either: the 2023/24 − 2019/20 upper-tercile
   differential is **≈ 0**. **STOP under the charter's step 4. This is a SUCCESS outcome.**
6. **What it does leave is a rule-14 finding, not a lever.** The keeper's coal outage basis
   over-counts against SPP's own measured outage by 1.2–3.4 GW in every year. That is recorded here as
   a named, owner-gated successor (§5). It must not be armed on this lane's evidence, for two reasons:
   the boundary and definition reconciliation that rule 14's misalignment test requires has not been
   done (§3.3), and its coal-only leg would move 2024 C3a to about −10.5 % (§3.2).

## 1. Failing criteria, keeper `2026-09-24-r-spp-corrected-inputs` (committed status part)

| year | tier | failing (non-C3c) | magnitude | adjudicated in §5.7 |
|---|---|---|---|---|
| 2019 | validation | C3a | +13.3 % (23.61 vs RT 20.85) | SPP-74 / SPP-79 (body over-level, cancellation) |
| 2020 | validation | C3a; C3b | +21.2 % (20.02 vs 16.52); NRMSE 0.286 | SPP-74 / SPP-79 |
| 2021 | validation | C3a | +10.0 % (41.11 vs 37.36) | SPP-74 / SPP-79 |
| 2022 | validation | C1 COAL_PRB; C4 gas | +9.58 TWh / +2.9 pp; NRMSE 0.32 (r 0.957) | SPP-41 / SPP-44 (crossover; deliverability R) |
| 2023–2025 | train | none (C3c ledgered) | — | — |

C3c fails 2022 / 2023 / 2024 / 2025. It is ledgered and excluded by the charter.

**Pick:** C3a 2019–21 (load-bearing, three years, the largest-weight failure). Every failure is
adjudicated in §5.7, so the lane went **off-queue per rule 28(a)** to the charter's named direction: a
measured availability input. The §5.7 queue has no live SPP item for this object: SPP-79 / 82 / 83
closed the body and commitment legs, and SPP-41 / 44 closed the coal legs. The published-outage
comparator has never been adjudicated for SPP (cell `dam_availability_rebasis` was U).

## 2. Method

- **Keeper fleet:** rebuilt `fleet_only` per year through `_spp81b_upper_tercile_marginal_unit.rebuild`,
  identical to SPP-83.
- **Unavailable MW:** per row, `pmax − pmax × availability`, where `pmax` is the row's maximum
  available MW over the year. This is a **lower bound** on unavailability for a row that is never
  fully available. Leading and trailing all-zero runs of ≥ 30 days are excluded as COD / retirement
  masks.
- **SPP published outage:** hourly `Coal MW` / `Natural Gas MW` from the portal year zips. The last
  snapshot of each market hour is kept, re-indexed onto the model's CST clock. **2025 is unmeasured:**
  its zip downloads empty (0 bytes), the same as SPP-83's gencap zip.
- **860M:** twelve monthly inventories per year, SWPP rows, joined to the keeper's gas `plant_code`s.
- **Leg C:** per hour, merit-clear the keeper's own stack at its own non-VER P1 generation (`p_full`).
  Then rebase each family's unavailable MW to SPP's hourly total **pro rata**, the one zero-DOF
  allocation:
  - where SPP's total is lower, restore availability in proportion to each row's unavailable MW;
  - where it is higher, remove availability in proportion to each row's available MW.

  Re-clear coal-only, gas-only and both. System-wide, one zone, no ramps: an instrument, not a solve.
  Only the deltas are used. `p_full` sits $0.0–3.1 below the keeper's P1.

## 3. Results

### 3.1 Outage level (GW, annual mean)

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| keeper gas unavailable | 7.85 | 6.74 | 7.65 | 8.26 | 6.67 | 7.47 |
| SPP published gas outage | 10.19 | 8.13 | 8.03 | 7.23 | 7.93 | 9.66 |
| **gas, keeper − SPP** | **−2.35** | **−1.39** | **−0.38** | **+1.04** | **−1.26** | **−2.19** |
| keeper coal unavailable | 6.46 | 7.54 | 7.18 | 6.96 | 7.22 | 8.33 |
| SPP published coal outage | 5.28 | 4.98 | 4.59 | 4.56 | 4.91 | 4.93 |
| **coal, keeper − SPP** | **+1.18** | **+2.56** | **+2.59** | **+2.40** | **+2.31** | **+3.40** |
| 860M: keeper gas plants' non-OP MW in month, mean / max | 0.40 / 0.44 | 0.45 / 0.46 | 0.21 / 0.21 | 0.25 / 0.26 | 0.20 / 0.20 | 0.15 / 0.16 |

Keeper gas by class (2020): CT_PEAKER 9.24 GW pmax, 8.71 available; CC_REGULAR 9.42 / 7.16;
ST_GAS 8.46 / 2.91. The gas **total** is close to SPP's, but it is distributed onto ST and CC, while
SPP's outage includes CTs the keeper never outages.

Coal, keeper − SPP by month (GW):
- 2020: 4.2, 4.0, 2.8, 4.1, 3.7, 3.0, 0.4, 0.6, 2.3, 2.0, 2.5, 1.3.
- 2024: 2.4, 9.4, 6.5, 3.9, 1.6, 2.0, 0.5, 1.4, 2.8, 2.5, 4.4, 3.7.

### 3.2 Re-clear instrument, Δ $/MWh (coal-only / gas-only / both)

| segment | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| RT − keeper P1, all hours (the gap to close) | −2.41 | −2.75 | −1.34 | +2.29 | −0.17 | −0.01 |
| all hours | −0.37 / +0.97 / **+0.76** | −0.70 / +1.11 / **−0.26** | −4.58 / +7.06 / **+0.27** | −3.78 / +0.03 / **−3.79** | −1.01 / +0.47 / **−0.74** | −1.68 / +3.34 / **+0.16** |
| body, RT < p67 | −0.37 / +0.46 / +0.03 | −0.62 / +0.40 / −0.37 | −3.59 / +1.02 / −3.10 | −3.62 / +0.09 / −3.55 | −0.99 / +0.27 / −0.82 | −1.41 / +1.26 / −1.06 |
| upper tercile, p67–p99 ex-Feb | −0.36 / +1.74 / +1.94 | −0.85 / +2.24 / −0.04 | −3.41 / +0.63 / −3.16 | −3.95 / −0.04 / −4.13 | −0.99 / +0.92 / −0.37 | −2.06 / +6.56 / +2.25 |

(The first row is on the probe's equal-hour basis. The scored C3a is load-weighted, so it differs from
the ±% in §1 in size, not sign.)

**Reading, at full magnitude.**
- **Both legs together barely move the target years** (+0.76 / −0.26 / +0.27), and in 2019 and 2021
  they move the wrong way. Coal and gas cancel.
- **Coal-only** helps 2021 (−4.58, the Uri-heavy year) but only −0.37 / −0.70 in 2019 / 20. It costs
  **2024 −1.68**, which is about −6.6 pp on a year already at −3.9 %, so 2024 C3a would go to about
  −10.5 % (22.77 vs 25.45), a FAIL in the gating train tier. It would also add coal energy to 2022, whose COAL_PRB is
  already +9.58 TWh (FAIL).
- **Gas-only** raises every year, which is the wrong direction for 2019–21.
- **SPP-79's pairing is not carried.** The "both" upper-tercile differential, 2023/24 − 2019/20, is
  (−0.37 + 2.25)/2 − (1.94 − 0.04)/2 ≈ **−0.01**, against the needed +8.3.

### 3.3 Why this is not armed even as a structural (rule 1 / rule 14) change

A rule-14 case exists for the **coal** leg: SPP's own measured outage is the better source for
"outage", and the keeper's CAMPD-inferred windows over-count it in every year, most in winter.

But rule 14's misalignment exception has **not been tested**, and it has to be before anything is armed:
1. **Boundary:** SPP's report covers the SPP market / RC footprint. The keeper's fleet is the SWPP BA
   thermal set after EIA-860 OP filtering. Coal pmax agrees roughly (keeper 21.3 → 19.2 GW), but no
   unit-level reconciliation exists.
2. **Definition:** it is unverified whether SPP's "Outaged MW" includes partial derates (the keeper
   carries `unit_partial_outage_windows`), and whether it excludes reserve shutdowns (the working
   hypothesis for the coal gap).
3. **Representation:** an aggregate-by-fuel series has to be allocated to units. Pro rata is zero-DOF,
   but it restores MW to units whose own CAMPD record shows zero output. That is a choice a PRECOMMIT
   must defend against rule 13's "no outcome pin" line from the other side.

The honest structural reading is that the **coal-window basis** is the defect: economic reserve
shutdowns are admitted as outages because the in-merit filter (`min_inmerit_hours 24` over a ≥ 5-day
window) is lax. That is a **deriver-scope** question. Rule 23 forbids re-deriving it because a residual
moved, and this lane's evidence is a measured-source discrepancy, not a residual. It still needs its
own charter and G-DRIFT, and it would move the whole coal outage layer for SPP (rule 19: it replaces
the layer, never stacks on it).

## 4. Rules and state

- **Rule 1:** no multiplier touched (0.93, year-invariant). Nothing selected on a residual. The
  instrument was run once, at a pre-declared zero-DOF allocation.
- **Rule 13:** the published outage is a physical availability event, admissible as an input in
  principle. Nothing was pinned. 860M status is a contemporaneous, forward-regenerable input, and it is
  immaterial here.
- **Rule 14:** the coal over-count is recorded as a discovered inaccuracy (§3.3). It is routed, not
  buried.
- **Rule 19:** no floor or state proposed.
- **Rule 21:** the SPP 2019–21 C3a over-level stays an open root-cause issue with no admissible lever.
- **Rule 25:** every number is SPP's own.
- **Rules 29(b) / 31–36:** no arm, no solve, no shard, no bundle, no registration. Nothing stranded, and
  no shards launched, so none to archive.
- **Rule 28(b):** `SPP.js` `dam_availability_rebasis` **U → O** (admissible-in-principle measured source
  identified and quantified; not a lever for the target; the coal-basis successor needs an owner
  charter). `campd_outage_windows` stays **U**, with the coal over-count appended. §5.7 note added
  above SPP-83's.
- **Data:** nothing landed.
  - SPP outage zips: `https://portal.spp.org/file-browser-api/download/capacity-of-generation-on-outage?path=%2F<y>%2F<y>.zip`
    (0.5–0.6 MB).
  - 860M: `https://www.eia.gov/electricity/data/eia860m/archive/xls/<month>_generator<y>.xlsx`.
  - The probe docstring gives both routes.

## 5. Successors (owner-gated; none launched)

1. **SPP coal outage-basis reconciliation:** CAMPD windows vs SPP published coal outage, unit by unit.
   Does the +1.2–3.4 GW coal over-count sit in reserve-shutdown windows the in-merit filter admits?
   This is zero-LP first: per-window in-merit hours against SPP's published coal outage on those days.
   If yes, the structural fix is a deriver-scope change for SPP's coal windows (rule 23: cite the
   measured-source basis, not the residual). §3.2's coal leg says to expect it to **lower** prices in
   every year: it would help 2021 and cost 2024 C3a. Rule 1 lets the owner keep it on structure anyway.
2. **CT outage absence:** CT_PEAKER carries no outage at all (94 % available). SPP's published gas
   outage exceeds the keeper's by up to 2.4 GW. A CT outage basis (CAMPD CT windows, or a published
   per-fuel rebase) is the gas half. It raises prices (wrong way for 2019–21).
3. The ~4 GW of residual gas "available but uncommitted" is SPP-82 / 83's commitment state: an engine
   design lane, unchanged.

## 6. Housekeeping owed to the owner (reported, not attempted)

Leftover shard branches from the R-SPP lane need the owner to remove them (sessions cannot delete refs,
rule 33(f)): `claude/rspp-2019`, `claude/rspp-2020`, `claude/rspp-2021`, `claude/rspp-2022`,
`claude/rspp-2023`, `claude/rspp-2024`, `claude/rspp-2025`.
