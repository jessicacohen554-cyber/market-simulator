# FINDING — miso-159: the `_commission_year` hardcoded-2010 fall-through is REPAIRED with the fleet's own measured EIA-860 COD — the age-escalation limb of `THERMAL_AVAILABILITY` prices real vintages at MISO for the first time

**Session** miso-159 · **ISO** MISO · **Date** 2026-08-15 ·
**Keeper at session start** `2026-08-09-miso-148-basis-aware` (`miso148_basis_B`) ·
**Model** `claude-fable-5`.

**PREREG** `results/calibration/PREREG-miso159-commission-year-cod-fallback-2026-08-15.md`,
pushed at **`fdb099f`**, blob **`77b76622`**, **verified byte-identical against the
FETCHED remote ref** before the construction was built and before any
adjudicating statistic was computed (rule 27 `[R-PUSH]`).

**Rule 22 `[R-HOLDOUT]`:** 2023 / 2024 / 2025 only. MISO holds **neither**
`complete` nor `final`; the holdout spend freeze is ACTIVE and untouched. No
out-of-training year was read, solved, scored or registered.

**Rule 28(a) provenance:** the MISO lever queue was EMPTY of named,
un-adjudicated candidates (miso-156 §8, miso-157 §10); this session executes
the construction miso-157 §11 item 1 prepared for the owner, whose rule-25
scoping prerequisite was discharged by the miso-158 census (PR #3966). The
owner's standing instruction to this session was to pick the workstream up
and drive toward a calibrated backcast.

---

## 1. The construction (Phase 0)

`ScenarioConfig.commission_year_cod_fallback: bool = False` (scenarios.py:9630),
registered in `_CACHE_KEY_OPTIONAL_FIELDS` + the pinned-defaults ledger in the
same commit. When armed, `assembly.bins_to_fleet::_commission_year` consults
`cod_ramp.load_cod_map()` — the repo's single COD source, already driving every
backcast's monthly online mask — before the 2010 literal. Precedence unchanged:
curated coal dict, then the (ERCOT-only) master registry, then the COD map,
then a disclosed 2010. **Zero continuous degrees of freedom.** Unit tests:
`tests/unit/data/test_campd_bins.py::TestCommissionYearCodFallback` (4/4:
off-path 2010, armed COD year, armed double-miss 2010, registry precedence).

## 2. Phase-0 instrument gates (probe `_miso159_cod_vintage_instrument.py`, record `_miso159_cod_vintage_instrument.json`)

| gate | result |
|---|---|
| **V2** off-path byte-inertness | **PASS 3/3** — every `THERMAL_AVAILABILITY`-classed row still `online_year == 2010` with the flag off; `test_cache_key_default_flip_guard` 9/9 (default key unmoved) |
| **S-CACHE** pre-check | **PASS** — armed config hashes distinctly (`cache_key` off ≠ on) |
| **V3** keeper fleet | **PASS 3/3** — n_gen 2929 / 2923 / 2923, 6 carry zones, both arms |
| **V1** armed vintages vs census truth | **PASS ON ATTRIBUTION after S-V1 fired** (§3) |

### 3. S-V1 fired — the excursion is the WEIGHTING BASIS, not the data, and both numbers are kept

Three V1 rows breached ±1.0 yr, all CT_CHP, all **+1.015 yr** on the LP-pmax
basis. Debug per the miso-157 §3 protocol: re-weighting the SAME armed
per-plant online years by the census's own bin-sheet NAMEPLATE reproduces the
census to **+0.011 yr** (CT_CHP), **+0.058** (CC_CHP), **−0.36/−0.45**
(ST_CHP) — the excursion is exactly the CHP grid-facing capacity holdout
(`chp_steam_following` removes host BTM self-supply from LP pmax, shifting the
class's internal weights), the same scope difference the census's own V-C1
gate disclosed for the CHP classes. Every non-CHP class passes on BOTH bases
in all years (worst |Δ| ≤ 0.12 yr). The mis-scoped bar was the instrument's,
not the record's; both bases are committed in `V1_rows`.

**A second clean-zero got its second derivation (T-3):** the armed fleet's
"rows still at 2010" (18 COAL rows, 1.951 GW in 2025) are NOT fall-throughs —
a bin-sheet × registry × COD-map scan shows **zero MISO plants absent from
both sources** — they are genuine ≈2010 measured CODs floor-rounded by the
capacity-weighted reduction.

## 4. P-1 priors — MISSED LOW, attributed, and the miss is the finding's first result

Pre-registered reach (census arithmetic): non-CHP summer 1.8–2.8 GW, annual
3.0–5.0 GW. **Measured on the production availability arrays (off − on):**

| year | annual GW | Jun–Sep GW | Jun–Sep h12-17 GW | in P-1 band? |
|---|---|---|---|---|
| 2023 | **2.132** | **1.308** | 1.308 | NO (low) / NO (low) |
| 2024 | **2.464** | **1.480** | 1.480 | NO / NO |
| 2025 | **2.869** | **1.638** | 1.638 | NO / NO |

2025 per class (annual / summer GW): COAL 1.294 / 0.689 · CT_PEAKER
0.800 / 0.462 · ST_GAS 0.676 / 0.427 · CC_REGULAR 0.098 / 0.060 · CHP classes
≤ 0.06 each. **Attribution, measured not argued:** (a) the census's uniform
`derate + share×wefor` formula does not model the availability builder's
branches — under the keeper's `coal_drop_pof=True` coal's SUMMER availability
is `1 − derate` (no WEFOR term), so coal's summer leg moves on DERATE alone
(census said 1.339 GW, truth 0.689); (b) the census weighted bin-sheet
NAMEPLATE where the LP prices net-summer `pmax`; (c) floor/sync rows carry
their own availability branches. CT_PEAKER — the summer price-setter — lands
at 94 % of its census estimate (0.800 vs 0.851 annual), so the class the lane
cares about is essentially as censused.

The DIRECTION and materiality stand: ~1.6 GW of summer capability and
~2.9 GW of annual capability (2025) was phantom — concentrated in COAL,
CT_PEAKER and ST_GAS, the classes that set MISO's summer and shoulder prices.

## 5. Phase 1 — the A/B (control `miso159_cod_A`, arm `miso159_cod_B`)

Same-HEAD, single-delta (`replay_keeper --set commission_year_cod_fallback=true`),
years 2023 2024 2025 in one invocation per arm, arms sequential (rule 12;
MISO peaks ≈10.8 GB on a 15 GB box). Runs registered (rule 15):
`2026-08-15-miso-159-control` / `2026-08-15-miso-159-cod-vintage`.

The box needed infrastructure work to solve at all: two OOM kills (13.34 GiB
cgroup cap, then 15 GiB) before the cap was raised to 23 GiB with an 8 GB
swapfile; the chain then completed with **peak 14.99 GiB**. 2023 solved P0
382 s (cold) / P1 172 s (warm).

**The control reproduces the committed keeper EXACTLY at the gated grain** —
C3a −2.0 / −8.0 / −15.6 %, C3b NRMSE 0.082 / 0.125 / 0.212, every criterion
verdict identical — so unlike miso-148's K0, no drift qualifier attaches to
any delta below. S-CACHE holds (config cache keys a7c5bdc709877ec9 vs
336f1b2b6b85d867; the arm's run_config records the flag true; prices move).

| grain (arm − control) | 2023 | 2024 | 2025 |
|---|---|---|---|
| demand-weighted P1 price, $/MWh | **+0.635 (+1.97 %)** | **+0.837 (+2.82 %)** | **+1.123 (+2.93 %)** |
| C3a (model vs RT lw actual) | −2.0 % → **−0.1 %** | −8.0 % → **−5.4 %** | −15.6 % → **−13.1 % (still FAIL)** |
| C3b monthly NRMSE | 0.082 → 0.080 | 0.125 → 0.113 | **0.212 (FAIL) → 0.200 (PASS, AT the gate)** |
| C3c >$200 RT hours (actual 30/37/88) | 0 → 0 | 4 → 5 | 0 → 1 |

C1 16/16 (free 12/12), C2, C4, C8 PASS in both arms with no new forcing id;
C6 attested on the arm (`calibration_attestation.json`, free-parameter ledger
UNCHANGED at 30 entries / 2 residual — the mechanism is zero-DOF). C3c stays
the ledgered model-class caveat. **Arm determination: NOT-YET on C3a-2025
ALONE** — the smallest fail set any MISO keeper has carried.

## 6. Priors and triggers, scored

* **P-1 (reach): MISSED LOW, attributed** (§4) — census arithmetic could not
  see the availability builder's branches; the production truth is
  2.13/2.46/2.87 GW annual, 1.31/1.48/1.64 GW summer (non-CHP).
* **P-2 (direction): CONFIRMED 3/3** — prices up in every year, as disclosed
  in advance and against the no-skill-claim discipline.
* **P-3 (magnitude): CONFIRMED** — 2025 lands +1.123 $/MWh, inside the
  +0.3…+3.0 band, and the registered "smaller in 2023/2024" holds on the
  band's own $/MWh basis (+0.635 < +0.837 < +1.123).
* **P-4 (2023 bound): HELD** — +1.97 % < +3 %; S-2023 never fired. 2023 C3a
  lands at −0.1 %, essentially zero error.
* **P-5 (composition): HELD** — C1 stays 16/16 in the arm; no class's |C1
  error| grows past the 2 TWh band (C1 PASSES both arms).
* **P-6 (fail set): HELD, STRICTLY** — {C3a-2025, C3b-2025} → {C3a-2025}; no
  criterion-year PASS→FAIL flip anywhere. C3b-2025 flips the OTHER way.
* **Triggers:** S-2023 silent; S-FLIP silent; S-ZERO silent (every
  adjudicating delta nonzero); S-CACHE silent; S-V1 fired in Phase 0 and was
  debugged/attributed (§3).

## 7. Decision per the PREREG §7 rule — PROMOTED

§7(a)'s condition is met exactly (V1/V2/V3 pass; fail set strict subset; no
new criterion-year FAIL), so the arm is **PROMOTED to keeper** on rules 1
`[R-STRUCT]` / 14 `[R-ACCURATE]`: a measured EIA-860 input replaces a rule-5
magic literal on the price-setting fleet, the age-escalation limb of
`THERMAL_AVAILABILITY` prices real vintages at MISO for the first time, and
the residual's (favorable) direction of travel was disclosed before the solve
and is not the ground of adoption. Keeper: **`2026-08-15-miso-159-cod-vintage`**
(`miso159_cod_B`). The control ships slim (BLOAT-B-3 convention); the keeper
bundle carries its `hourly/` sidecars. This is the first MISO promotion since
miso-127 to clear its own PREREG condition without owner escalation.

## 8. Where this leaves the lane

1. **The blocker is now ONE criterion-year: C3a-2025 at −13.1 %** (gate
   ±10 %). C3b passes everywhere (2025 at the gate exactly — knife-edge, not
   margin). The miso-156 diagnosis stands: the remaining miss is summer-peak
   marginal-unit identity — the model still stops less than half-way up its
   CT stack in the top-tail hours.
2. **The remaining named availability object is `SUMMER_WEFOR_SHARE = 0.30`**
   (miso-157 B-DISAGREE, unresolved): the owner's data-provenance decision
   (which measured record adjudicates a forced-outage seasonal shape) is the
   gate on the next availability lever. Its reach (~1.2–1.7 GW of summer CT
   capability) is now the largest single un-adjudicated quantity bearing on
   the 2025 cushion.
3. **The vintage repair is exportable**: CAISO/PJM/NYISO/NEISO carry the same
   defect at censused magnitude (PJM's summer overstatement +2.749 GW is the
   largest); their cells enter `U` and each lane arms after its own
   measurement (rule 25).
4. **Path to testing years** (the owner's question this session was opened
   with): close C3a-2025 → determination flips to CALIBRATED-WITH-CAVEATS
   (C3c ledgered) → owner declares MISO `complete` → owner lifts the holdout
   freeze narrowly (PJM/NEISO 2022 precedent) → 2022 validation solves.

---

**Artifacts.** Probe `scripts/probes/_miso159_cod_vintage_instrument.py`
(`ruff` clean, zero 3-arg `getattr`); record
`results/calibration/_miso159_cod_vintage_instrument.json`; unit tests
`TestCommissionYearCodFallback`; PREREG `fdb099f` blob `77b76622`; bundles
`results/calibration/miso159_cod_A` / `miso159_cod_B`.
