# FINDING — SPP-83: the keeper clears on ~8 GW SPP kept offline — in EVERY year, not a doubling; no admissible commitment-cost source (zero LP, 2026-09-26)

Lane: SPP-83 (SPP commitment-state owner). Parent: SPP-82
(`FINDING-spp-82-offered-not-setting-2026-09-25.md` §7.1–7.2). Keeper: `2026-09-24-r-spp-corrected-inputs`,
bundle `results/calibration/rspp_span`, `basis_sha` `ec13e5c2ad35c4f817cc496ff2363affb3fed2f9`.
Session base: `origin/main` `f30e3704`.
Probe: `scripts/probes/_spp83_keeper_online_vs_market.py`. Numbers: `results/calibration/_spp83_keeper_online_vs_market_phase0.json`.
**No LP. No shard. No bundle. No `src/` edit. No `ScenarioConfig` field. No multiplier touched. Nothing landed under `data/`.**

## 0. Headline

1. **Keeper side: yes, the LP clears on capacity SPP's market kept offline. But the amount is flat at ~8 GW
   in every year. It does not rise from 8 GW to 15 GW.** On SPP-82's exact sample hours, keeper available
   MW minus SPP's published online thermal capacity `C_th` is **+8.17 / +8.04 / +8.17 / +8.85 / +8.09 /
   +6.90 GW** (2019 → 2024). About 6 GW of that is **gas**: keeper gas available minus SPP online gas is
   +5.97 / +6.05 / +6.21 / +6.32 / +6.10 / +5.42 GW. The keeper's coal is *below* SPP's online coal in
   every year (−0.5 to −1.7 GW). The keeper's spare capacity above its own dispatch is **12.2–14.2 GW**,
   against SPP's online headroom of **4.1–5.4 GW**.
2. **So the keeper's offline-capacity excess is a LEVEL defect, not the 2023+ step.** SPP-82's rising
   floor (7.5 → 15.7 GW of offline ≥ $10 MW below MEC) is the market's *fixed* offline offers falling
   below a *rising* MEC. The keeper has the same ~8 GW of excess in 2019/20, where it has no premium to
   close, as in 2023/24.
3. **The re-clear bound confirms it.** Remove the keeper's gas excess over SPP online gas from its own
   ≥ $10 gas stack, cheapest first (SPP-82's reading of which MW are offline), and re-clear at the keeper's
   own thermal generation. The price rises **+$7.9 / +7.9 / +14.3 / +23.8 / +7.0 / +13.1**. Removing
   dearest first gives +$0.0 to +2.1. The 2023/24-minus-2019/20 differential at the upper bound is
   **+$2.1, against a needed step of +$8.3** (RT MEC − keeper P1: +2.5 / −0.8 → +7.7 / +10.6). It also
   **overshoots 2019/20 by ~$7** and 2021 by ~$16. This is an instrument, not a solve.
4. **Commitment-cost source survey: FAILED. This is the charter's STOP, and a SUCCESS outcome.** No
   public source gives SPP per-class or per-unit start-up or no-load **dollars** (§2).
   - The SPP MMU ASOM gives measured **times**, not costs: min-run, min-down and start time, as fleet
     averages by fuel, with gas not split.
   - Marketplace Protocols Appendix G gives **formulas only**; each unit's mitigated values are
     confidential.
   - The make-whole and uplift reports are realized **outcomes** (monthly $ by named location) and fail
     rule 13.
   - EQR has no operating parameters.
   - ITP/PROMOD inputs are proprietary (Hitachi Velocity Suite).
   - The NREL/APTECH cycling-cost tables are national engineering estimates, not SPP data.
5. **Design (step 3) is moot twice over.** First, no admissible source exists. Second, even a perfect
   commitment state that removed the keeper's excess would move every year's level. It could not carry
   SPP-79's coupling pairing (§3). **No mechanism, no PRECOMMIT, no G-DRIFT, no shard.**

## 1. Keeper side (FINDING-spp-82 §7.1)

**Method.** Sample: `_spp82_offered_not_setting.sample_days` verbatim, i.e. SPP-80's non-scarcity RT upper
tercile, ex-Feb, two days per month. Hours: **352 / 335 / 304 / 332 / 342 / 341**. That is SPP-82's count
exactly, except 2023 (+1 hour, where SPP-82 had no offer snapshot).

- **Keeper fleet:** rebuilt `fleet_only` through `_spp81b_upper_tercile_marginal_unit.rebuild`
  (`scripts.lib.bundle_fleet.reconstruct_bundle_fleet`, the fidelity-guarded reconstruction).
  `K_av` = Σ pmax × availability over every fleet row. Wind and solar are LP variables, not fleet rows,
  and `C_th` excludes them too.
- **Keeper generation:** `K_gen` = P1 `class_hourly` over non-VER classes.
- **SPP side:** `C_th`, `C_gas`, `C_coal` from `hourly-generation-capacity-by-fuel-type`, with SPP-82's
  own parser (`gencap_hourly`), and `G_th` from GenMix.

| GW, sample-hour means | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| RT MEC / keeper P1, $/MWh | 29.24 / 26.77 | 25.32 / 26.09 | 42.02 / 43.42 | 81.21 / 62.64 | 38.38 / 30.68 | 43.35 / 32.80 |
| `K_av`, keeper available (all fleet rows) | 40.06 | 39.48 | 39.30 | 41.19 | 38.82 | 38.11 |
| `C_th`, SPP **online** thermal | 31.89 | 31.44 | 31.13 | 32.35 | 30.73 | 31.21 |
| **`K_av − C_th`, keeper-online beyond market-online** | **+8.17** | **+8.04** | **+8.17** | **+8.85** | **+8.09** | **+6.90** |
| of which gas (`K_gas − C_gas`) | +5.97 | +6.05 | +6.21 | +6.32 | +6.10 | +5.42 |
| of which coal (`K_coal − C_coal`) | −0.49 | −0.95 | −1.36 | −0.99 | −1.23 | −1.66 |
| of which other (oil / hydro / nuclear / other) | +2.21 | +1.99 | +1.97 | +2.53 | +1.99 | +1.48 |
| `K_gen` / SPP `G_th`, thermal generation | 26.87 / 27.75 | 27.13 / 27.29 | 26.88 / 27.07 | 26.95 / 26.91 | 25.57 / 25.78 | 25.90 / 26.34 |
| **headroom: keeper `K_av − K_gen` / SPP `C_th − G_th`** | **13.20 / 4.14** | **12.35 / 4.15** | **12.42 / 4.05** | **14.24 / 5.44** | **13.24 / 4.87** | **12.21 / 4.87** |
| `K_below`, keeper MW at/below its own zone P1 | 28.81 | 29.30 | 27.92 | 28.20 | 27.91 | 28.03 |
| `K10_below`, keeper ≥ $10 MW at/below its own P1 | 20.41 | 21.30 | 19.73 | 20.02 | 20.26 | 20.47 |
| keeper ≥ $10 MW at/below **RT MEC** | 20.06 | 18.46 | 19.06 | 24.32 | 22.85 | 21.96 |
| SPP-82 `B10`, real ≥ $10 offered at/below RT MEC | 38.88 | 39.03 | 41.20 | 42.87 | 46.50 | 46.46 |

Keeper available by class, 2019 → 2024 (GW):
- CT_PEAKER 8.69 → 9.03;
- CC_REGULAR 6.89 → 6.92;
- ST_GAS 2.86 → 4.00;
- coal 14.65 → 11.24;
- oil 1.53 → 1.59, hydro 3.1, nuclear 1.8.

**Reading, at full magnitude.**
- **The LP treats ~8 GW as available that SPP's market had offline, in every year.** It has no
  commitment state, so every non-outaged MW is "online" to it. Its generation tracks SPP's to within
  0.9 GW, so the excess sits entirely as idle headroom: **~3× SPP's online headroom**. That is SPP-82
  §2.3's hypothesis confirmed on the keeper side.
- **It is not the 2023+ step.** The excess is flat (8.2 / 8.0 → 8.1 / 6.9 GW) and *slightly smaller*
  in 2024. The market's offline-below-MEC floor doubled because its fixed offline offers fell under a
  rising MEC (SPP-82 §2.3, last bullet: the offline fleet did not grow; it got cheaper relative to
  MEC). The keeper's ≥ $10 MW below RT MEC rises only +3.1 GW (19.3 → 22.4) against the market's
  +7.5 GW. The difference is the offline fleet the keeper cannot see as offline.
- **The excess is gas, mostly CT and ST.** That is the fleet SPP-44 / SPP-46 / SPP-75 found the model
  commits *too little* in low-price hours. The same fleet is too available in high-price hours. The
  keeper's gas commitment is too elastic in both directions: too cheap to leave off at the top, too
  dear to keep on at the bottom. A commitment state is the one structure that couples the two, and it
  is exactly what the engine lacks.

### 1.1 Re-clear bound (instrument, not a solve)

Per sampled hour, system-wide (one zone, no ramps, no start-up markup):
- merit-clear the keeper's own fleet stack at its own thermal generation `K_gen` (`p_full`);
- then remove `max(0, K_gas − C_gas)` from its ≥ $10 gas rows, **cheapest first** (`p_rm_cheap`, the
  upper bound and SPP-82's reading) or **dearest first** (`p_rm_dear`).

**Fidelity:** `p_full` sits $1.5–2.6 below the keeper's P1 in every year (zonal prices and P1 markup).
Only the deltas are used.

| $/MWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| RT MEC − keeper P1 (the premium to explain) | +2.47 | −0.76 | −1.40 | +18.57 | +7.70 | +10.55 |
| Δ, excess removed cheapest first | **+7.92** | **+7.93** | **+14.26** | **+23.82** | **+7.00** | **+13.13** |
| Δ, excess removed dearest first | +0.00 | +0.02 | +0.00 | +1.89 | +0.00 | +2.06 |

- **Differential, 2023/24 − 2019/20, upper bound: +$2.1 against a needed +$8.3.** The bound carries
  about a quarter of the step.
- **It overshoots the pairs that have no premium.** 2019/20 gains +$7.9 against +$0.9. 2021 gains +$14.3
  against −$1.4.
- A commitment state sized to SPP's online capacity would therefore be a **body/level** lever. It would
  land on the years that are already in band. That is SPP-79's constraint from the other side: a lever
  that moves every year cannot pair.
- 2022 is the one year where the bound and the premium match in size (+23.8 / +18.6). That is gas-price
  scaling of the same flat MW, not a step.

**2025 not measured.** SPP's `hourly-generation-capacity-by-fuel-type` 2025 year zip downloads empty
(0 bytes), and SPP-82 had no 2025 offer sample either (its §7.3).

## 2. Commitment-cost source survey (the hard stop)

Each source was opened this session, anonymously:

| source | grain | content | rule 13 |
|---|---|---|---|
| SPP MMU ASOM 2022 / 2023 / 2024 ([2024](https://www.spp.org/documents/73953/2024_annual_state_of_the_market_report.pdf), [2023](https://www.spp.org/documents/71645/2023%20annual%20state%20of%20the%20market%20report%20v2.pdf), [2022](https://www.spp.org/documents/69330/2022%20annual%20state%20of%20the%20market%20report.pdf)) | fleet average **by fuel**; gas not split into CT/CC/ST | "Average physical parameter values" (Fig 3-6 2023, Fig 3-10 2024): econ min/max, hot/cold start **time**, min-run (2024: coal 100 h, gas 21 h, oil 2 h), min-down (coal 38 h, gas 8 h). Start **cost** only as a binned share chart (2022 Fig 3-36) and as a mitigation mark-up chart (Figs 6-18/6-19, mark-up over the mitigated offer, not levels) | times are physical and admissible, but they are **not costs**, and gas is one lump |
| Marketplace Protocols App. G, mitigated offer methodology ([v106a excerpt](https://www.spp.org/documents/71629/excerpt%20of%20appendix%20g%20mitigated%20offer%20methodogoloy%20integrated%20marketplace%20protocols%20106a%20reference%20doc%20for%20mdwg.pdf)) | per-unit **formula** | start = start fuel × fuel cost × performance factor + station service + labor + start VOM; the only per-technology numbers are regulation VOM adders; the worked-example dollars are illustrative | formula admissible; **no values published**; per-unit mitigated offers are confidential |
| portal `make-whole-payment-report` = `resource-uplift-report` (same folder) | monthly $ per **named** settlement location, ~2020 → | DA MWP, RUC MWP, RT out-of-merit, regulation adjustments, total uplift; no EIA id; `MWP_*.xlsx` is daily footprint totals | **realized OUTCOME** of commitment, prices and offers; fails rule 13 |
| portal `operator-initiated-commitments` | event, zone/BA | location, size, start, reason | outcome; not a cost |
| FERC EQR | contract/transaction | seller, product, price, quantity | no operating parameters |
| SPP ITP / PROMOD (ITP Manual 3.0 p.36; 2025 ITP scope) | per unit | UC uses min/max runtime and start-up cost from Hitachi Velocity Suite | **proprietary**, secure site; not anonymous |
| NREL/Intertek-APTECH *Power Plant Cycling Costs* (NREL/SR-5500-55433, 2012) | per technology, **national** | lower-bound hot/warm/cold $/MW-start (2011 $) | forward-reproducible engineering estimate, **not SPP-measured**; the served PDF held only the key findings, so the table values were not verified this session |

**Verdict: no public, SPP-specific, per-class start-up / no-load cost exists. STOP.**

The only per-class candidate is the generic national NREL estimate. It is refused as this lane's owner for
two reasons that do not depend on its values:
1. **Rule 14:** it would replace nothing measured. The keeper already carries per-class start-up $/MW on
   its committed tranches (coal 100 / CC 50 / ST 35 / CT 20, SPP-73 M4). The existing LP channel for start
   cost, `tranche_startup_amortization`, was refused on size for SPP at a maximum +$2.14/MWh (SPP
   merit-order lane, 2026-09-07). A per-start cost only raises offers in a pure LP. It never takes MW out
   of the stack, so it is the wrong structure for §1's object, whatever its value.
2. **§1.1:** a structure that correctly removed the excess would still be a level lever.

The ASOM **times** (gas min-run 21 h, min-down 8 h) are admissible measured physics. They are recorded here
as the one source a future commitment-state design could use for its time constraints.

## 3. Design question (step 3): moot, stated so a successor does not re-ask it

- **Rule 19:** the only representation that removes cheap MW from the price-setting stack is a
  commitment **state** (binary or relaxed-binary online status with min-run/min-down coupling). It would
  *replace* the P1-native bridges (all `R` in SPP) and the start-up amortization channel (`R`), never
  stack on them.
- **Rule 18:** it would gate by unit physics (the ASOM times by fuel, the committed-tranche start costs).
- **Rule 13 forward story:** start costs and min-run/min-down times are physical parameters that
  regenerate for a forward year. That part is admissible.
- **What blocks it:**
  - the engine is pure LP (no MIP; P2 archived), so a state representation is an engine design lane, not
    a lever;
  - the gas cost inputs are unpublished for SPP (§2);
  - §1.1: even done perfectly, it lifts 2019/20 and 2021 by +$8–14 with no premium to close, and carries
    only ~+$2 of the +$8 2023/24 step.
- **SPP-79's coupling pairing:** it **cannot be carried**. SPP-79 needs an upper-tercile lever that moves
  2023–25 more than 2019–22. §1 shows the keeper's offline excess is year-flat. **SPP-79's constraint
  stands: a body lever alone breaks 2023–25 C3a, and this owner is itself a body lever.**

## 4. Rules and state

- **Rule 1:** no multiplier touched (0.93 everywhere, year-invariant).
- **Rule 13:** measured online capacity is still an outcome and was used **only as a diagnostic
  comparator**, never as an input. Uplift and make-whole reports are outcomes and are refused.
- **Rule 14:** the generic national start-cost estimate is not preferred over the keeper's existing
  values, and it cannot own the object anyway.
- **Rules 19 / 18:** no floor, bridge or state proposed for build.
- **Rule 21:** the SPP 2023+ upper-tercile level stays an **open root-cause issue**. The keeper-side part
  (a flat ~8 GW gas-led over-availability, i.e. no commitment state) is now quantified, and it is a
  model-class limitation of a pure-LP engine.
- **Rule 25:** every number is SPP's own.
- **Rules 29(b) / 30(c) / 31–36:** no arm, no solve, no shard, no bundle, no registration. Nothing to
  promote, nothing stranded, no shards launched and so none to archive.
- **Rule 28(b):**
  - `docs/codebase-site/data/mechanism-matrix/SPP.js`: `online_capacity_envelope` (stays U; keeper-side
    evidence appended) and `tranche_startup_amortization` (stays R; source survey appended).
  - `docs/mechanism-testing-matrix.md` §5.7: DO-NOT-REDO note added above SPP-82's.
- **Data:** nothing landed under `data/`. The SPP gencap year zips are re-fetchable
  (`https://portal.spp.org/file-browser-api/download/hourly-generation-capacity-by-fuel-type?path=%2F<y>%2F<y>.zip`,
  0.36–0.40 MB) and pass to the probe as `--zdir`.

## 5. Successors

1. **An engine design lane for commitment state in the LP.** This is the only structure that couples
   the too-available top and the too-uncommitted bottom (§1). It is owner-gated, and it is not an SPP
   lever. It would need the ASOM times plus a start-cost source. §1.1 says it would land as a level
   lever in SPP.
2. **The 2023+ step itself stays unowned on the model side.** The market-side object is SPP-82's fixed
   offline offers under a rising MEC. Neither this lane nor SPP-82 found a forward driver of *why the
   MEC rose* through a flat online stack at flat gas. The DA-SCUC horizon is the remaining candidate,
   and it is model-class.

## 6. Housekeeping owed to the owner (reported, not attempted)

Leftover shard branches from the R-SPP lane need the owner to remove them (sessions cannot delete refs,
rule 33(f)): `claude/rspp-2019`, `claude/rspp-2020`, `claude/rspp-2021`, `claude/rspp-2022`,
`claude/rspp-2023`, `claude/rspp-2024`, `claude/rspp-2025`.
