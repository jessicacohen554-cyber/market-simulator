# FINDING — ercot-191: the signed A1 DAM-deriver lane executed (#9 → #8 → #10), the family re-derived and re-gated, and the card-Q checkpoint read FAIL → (Q-B) final

**Session ercot-191, 2026-08-12.** Authority: owner signature **A1**
(`docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md` card A,
RESOLUTIONS) — one precommit, one re-derive, one re-gate sweep, #9 first.
Precommit pushed before any derive or solve:
`docs/PRECOMMIT-ercot191-a1-dam-deriver-2026-08-12.md`. Checkpoint authority:
the signed card-Q rule (ercot-190, RESOLUTIONS of
`docs/DECISION-CARD-ercot189-c3a2023-after-the-offer-family-2026-08-11.md`).
ISO: ERCOT only (rule 25). Years: {2023, 2024, 2025} (rule 22). The rule-23
re-derivation citation for every artifact regenerated here is the A1
signature itself.

## 1. The three repairs, as landed

* **#9a — `_site()` collapses to the physical train.** The CC resource-name
  grammar is `<MNEMONIC>_<CCTAG><train#>_<config#>` (verified: all 310
  unique CC names across both disclosure lanes match the train regex). The
  site key is now the TRAIN (`GUADG_CC1`), so the existing site-summing
  aggregations become the SUM of per-train maxes the ercot-149 §3.1/§6.1
  diagnosis names; config-collapse within a train is unchanged. Non-CC keys
  byte-identical.
* **#9b — crosswalk completion.** (i) Sibling completion: a rejected site
  with STRONG unique corroboration to a plant that already has an accepted
  site in the same class, failing ONLY the capacity band from below, flips
  to `accepted=1` under a plant-sum guard (Σ accepted p98 ≤ 1.30 ×
  nameplate). Recovered exactly the ercot-149 §6.2 set: `BRAUNIG_VHB1/2`
  (0.187/0.198), `GIDEON_GIDEONG1/2` (0.177/0.199), `OLINGR_OLING_2`
  (0.25). (ii) A hand seed `JCKCNTY2_CC1 → 55230 Jack County` in the new
  reviewable `data/raw/reference/ercot-dam-gas-site-seeds.csv` (same QSE
  pair as JACKCNTY; 654.0 + 627.0 = 1,281 MW vs nameplate 1,280.0). No bars
  moved (`_STRONG`, `_CAP_LO/_CAP_HI` untouched).
* **#8 — multi-year rating basis.** `derive_years()` derives all years in
  one pass; a (class, site) with no in-year rating takes the nearest other
  year's (tie → earlier). An all-year-OUT site now enters BOTH sides of
  every grain at live 0. **`BIN_FORCED_DERATE_BY_YEAR["N_COAL4"]` is NOT
  retired**: its TO-RETIRE condition names the OUTAGE derive (or a
  registry), and the entry still guards configurations without the plant
  pin; the ERCOT-137 `min()` ceiling composition makes the two expressions
  of the same measured fact non-stacking.
* **#10 — pin remove-direction coverage dilution.** On remove hours only,
  `pf_eff = pf·cov + cur·(1−cov)` with `cov = clip(covered rating MW /
  Σ pmax, 0, 1)` (new companion loader
  `ercot_thermal_dam_availability_plant_rating_series`); restore direction
  untouched (the armed event caps own it, rule 19); the unmapped-residual
  accounting stays on raw `pf` (the ERCOT-137 precedent).
* The ercot-170 probe gained the pre-registered GRAIN ADAPTER only
  (`committed_pairs()` normalizes crosswalk keys through the probe's own
  `_site_of_train`; identity on every pre-repair key).

## 2. One re-derive — every seam prediction landed

Single invocation `--years 2023 2024 2025`, all three grains, then the
crosswalk rebuild (`--years 2023`, committed scope):

* **CT_PEAKER and ST_GAS class-day: byte-identical** (0/1,066 days changed).
* **COAL: changed in 2025 only** (365 days) — Martin Lake U1 (`MLSES_UNIT1`)
  now live 0.0 at its 830 MW cross-year rating (COP `OUT` all 8,760 h).
* **CC_REGULAR: rating denominator +5,031 MW median** (~30.8 → ~35.8 GW,
  the train-sum unwind); avail delta mean −0.0112 (p5 −0.0398, p95 +0.0087,
  max |Δ| 0.0549). The GUADG family reads **0.463–0.482** through its
  Oct-2024 single-train block (was ≈0.97) — the ruling-#9 phantom, gone.
* **Crosswalk: 48 → 56 accepted; zero surviving sites changed plant.** CC
  12 → 15 (train re-keys + GUADG/KMCHI two-train splits + seeded
  JCKCNTY2_CC1), ST_GAS 4 → 9, COAL 26 = 100 % of class rating.
* One committed-artifact test pin re-set (CC 2023-06-14 day 0.834 → 0.828);
  new unit coverage for the train key, the #8 fallback, and the #10
  dilution (`tests/unit/data/test_dam_deriver.py`).

**The ercot-150 zone-anchor re-trigger resolved as an exact re-assertion:**
`derive_gas_offer_margin_anchor.py --iso ERCOT --by-zone` on the repaired
family (weights off the keeper reconstruction) reproduced **all six
registered zone values byte-for-byte** (South 3.2778 / South_Central 2.7578
/ North 2.7178 / Northeast 2.7178 / Houston 2.3111 / West 1.9586) —
expected, since the weights are capacity-based and the fuel path does not
read availability. `constants.py` unchanged;
`_ercot150_zonal_anchor_derivation.py` re-pointed to the re-gate bundle (the
original ercot-149 weights bundle is retention-pruned from disk) and re-run
to refresh the committed derivation record.

## 3. One re-gate sweep — `2026-08-12-run191-dam-deriver-regate`, PROMOTED under the pre-registered direction-blind rule

The run188 keeper recipe replayed UNCHANGED (`--replay-bundle`), full span,
years sequential; both armed DAM keeper mechanisms
(`ercot_dam_availability_coal_event_cap`, `ercot_dam_availability_gas_event_cap`)
re-gated on the repaired derivation. **Determination NOT-YET, fail set
{C3a-2023, C3b-2023} — unchanged from the keeper.** C6 ATTESTED + PASS (DOF
ledger carried verbatim — zero new scalars in the whole lane), C8 PASS, C1
16/16, C2 PASS, C4 PASS. C3c stays the single ledgered CAVEAT ×3 with
magnitudes re-measured (58/181, 22/53, 1/31) and the carry text extended.

Measured moves, at full magnitude (none of them the promotion basis):

| metric | run188 keeper | run191 re-gate |
|---|---|---|
| C3a-2023 | −32.8 % ($43.23) | **−33.7 % ($42.63)** vs actual $64.32 |
| C3a-2024 | +1.2 % PASS | **−0.8 % PASS** |
| C3a-2025 | −8.0 % PASS | **−7.5 % PASS** |
| C3b-2023 | 0.608 | **0.610** |
| C3b-2024 | 0.158 | **0.135** |
| C3c tails | 58/181 · 23/53 · 3/31 | **58/181 · 22/53 · 1/31** |
| G-SHED shed hours | 4/2/0 | **4/1/0** (no new shed year) |

Guards: G-SHED PASS, G-OWNER PASS (2024/2025 both hold PASS), G-C1 PASS,
G-C8 PASS, G-C6 PASS. The 2023 level deepening (−$0.60/MWh) is the rule-14
signature stated in the precommit ex ante: phantom availability had been
silently propping the level; the root cause (2023 scarcity-tail formation)
stands as the accepted model-class limitation. The `[7c]` operating-shape
report gate shows **15 cf_emd/r regressions** vs the run188 baseline,
concentrated in CC_CHP / CC_REGULAR / COAL — reported UN-TARGETED; the
dispatch-shape root cause (ERCOT-126/142/143 loading-conduct family) stays
open and is not this lane's object.

**Promotion.** Pre-registered direction-blind (precommit §2): the prior
keeper rests on an aggregation the record calls wrong, so the accurate
derivation is the keeper whatever the residual does (rules 1/14). Keeper
shard re-keyed, status rebuilt, matrix shard header + three cells
re-stamped (`dam_availability_rebasis`, both event caps), §5.1 prose header
re-stamped, run registered with `market_story`. Zero fitted parameters ⇒
structurally LOYO-exempt (ERCOT-145b/148/149 precedent), per-year guard
table above standing in. The ercot-188/E2 P0 bit-identity forfeiture is
inherited unexpired.

## 4. The card-Q checkpoint — licence FAIL → (Q-B) automatic and final

On the repaired deriver and rebuilt crosswalk, the ercot-170
coverage-licence re-test ran as a phase-0 read, NO LP, bars unchanged:

* **L1 (SCED-side closure) = 0.3857 vs ≥ 0.90 — FAIL** (defensible-tiers-only
  0.3560; committed baseline 0.5111/0.3375). X1 rose to 13 sites (train-grain
  keys + the seeded JCKCNTY2), X2 7, X3/E3 2 — 22 of 58 SCED sites.
* **L2 (ambiguity budget) = 0.0000 vs ≤ 0.10 — PASS.**
* Verdict **FILED-UNLICENSED**; attribution identity error **0.0000 GW**;
  A_capability 2.5869 GW = 102.6 % of the 2.5224 GW gap (the object itself
  remains intact and characterised — it is the *licence* that fails).

Read: `results/calibration/ercot191_cc_headroom_licence_retest.json`
(baseline `ercot170_cc_headroom_phase0.json` preserved). Per the signed
rule: **(Q-B) — no further ERCOT C3a-2023 spend; ERCOT stands at NOT-YET on
C3a-2023 as a model-class limit. Recorded and stopped.** Item 11 CLOSED in
the mechanism-testing matrix. The remaining ERCOT-C3a items are both
doc-grade and outside this lane: the §5 `readiness_limits` price-tail
disclaimer (authorized at ercot-190, implemented on the forecast lane) and
the owner's `complete`-declaration question.

## 5. Fences honoured

No other C3a-2023 work of any kind (the Q-C freeze — the licence re-test is
the checkpoint itself, and (Q-B) closed the lane). Card B's coal-limb
re-adjudication untouched. No rubric text, no ledger scope change (carry
text only), no holdout marker, no out-of-training year, no new
`ScenarioConfig` field, no new matrix row.
