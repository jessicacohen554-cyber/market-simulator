# FINDING miso-217 — THE `phys_*` COVERAGE-GAP ARM: **PROMOTED**, keeper → `2026-09-05-miso-217-intermphys`. One MISO-gated, zero-DOF field returns **38,501.0 MW = 58.4 % of MISO's assembled gas capacity** to the armed offer-margin mechanism; every kill silent and §6's footprint disposition not firing — and the pre-registered, explicitly **un-instrumented** cross-class backfill **materialised**, consuming 91 % of `CC_REGULAR`-2024's headroom without exiting the band (2026-09-05)

**KEEPER → `2026-09-05-miso-217-intermphys`** (bundle
`results/calibration/miso217_intermphys_B`), superseding `2026-09-05-miso-213-layering`.
Determination **UNCHANGED IN CLASS**: NOT-YET on **C3a-2025 alone**, C3c the single ledgered
caveat, C6 attested **41/2**. PREREG `PREREG-miso217-intermediate-phys-arm-2026-09-05.md`
pushed **BLIND** at `76c2574c`, before the field existed. Scorer
`scripts/probes/_miso217_ab_gates.py` **committed BEFORE the solve** at `f3284261` with every
band frozen from the PREREG and the control's own committed verdict. Records
`_miso217_ab_gates.json`, `_miso217_liveness.json`. Rule 22 `[R-HOLDOUT]`: 2023–2025 only.

---

## 0. Verdict in one paragraph

`gas_offer_net_revenue_margin` merges its `phys_*` keys onto exactly five gas classes, so the
three duty-split `*_INTERMEDIATE` curves carried **none**,
`gas_offer_margin_markup_mult` returned its documented rule-24 neutral **0.0** for every
band, and the armed mechanism **skipped 58.4 % of MISO's gas fleet** — leaving it in the
fully fuel-scaled multiplier form the mechanism exists to replace. One MISO-gated
`ScenarioConfig` boolean, `miso_intermediate_gas_offer_margin`, resolving at
`data/offer_curves._offer_curve_for_group` and returning a **copy** carrying the PARENT
class's already-registered, already-frozen `phys_econ_low` / `phys_econ_high`, closes it at
**zero free parameters** — the ledger is unchanged at 41/2, and the borrowing was
**validated 9 of 9 cohort-years at miso-215 §3 before the field existed**. S-2 liveness,
measured **before** the solve, hit the PREREG's P-1 bar **to the unit: exactly 534 tranches**
(264 + 234 + 36), every one positive, zero existing markups moved, zero changes outside the
econ band, `mc` changed on exactly those rows and nowhere else. **Every pre-registered kill
is silent** and §6's footprint disposition does not fire, so the PREREG's own promotion rule
is met. **What the arm costs is reported at full magnitude and is never the justification
(rule 1 `[R-STRUCT]`):** the risk the PREREG named as explicitly un-instrumented — the
cross-class backfill a price-taking screen cannot see — **materialised**, taking
`CC_REGULAR`-2024 from **+7.419 to +7.947 TWh** and consuming **91 %** of its 0.581 TWh
headroom without exiting the ±8.00 band; `CT_PEAKER`-2024 falls **−0.884 → −3.634**; the C8
`CT_PEAKER` forced share goes **0.2044 / 0.1218 / 0.1421 → 0.2280 / 0.1573 / 0.1319**, with
**2024 crossing the 0.15 peaker budget** (K-2 silent exactly as pre-registered, because rule
20's conditional provenance+shape route still clears); and C3a moves **+0.183 / +0.960 /
−0.550 pp**, its 2025 leg **0.05 pp outside my own predicted bound**. One instrument
condition is disclosed rather than renegotiated: the **first** scoring pass fired K-4, and
the C3c values are **byte-identical between the legs** — a replay writes no attestation, so
C6 read UNATTESTED and guard (b) of the C3c standing rule blocked the reclassification. §7
scores my priors: **P-1 exactly right, P-5's 2025 leg wrong.**

## 1. What was built, and why it is coverage rather than a lever

**The defect.** `pipeline/backcast_config._GENERIC_NEUTRAL_GAS_CLASSES` names five gas
classes (`CC_REGULAR`, `CC_CHP`, `CT_CHP`, `CT_PEAKER`, `ST_GAS`) and `_MISO_OFFER_CURVE`
deep-merges `phys_*` onto those same five. The keeper arms all three duty splits, so
`CT_INTERMEDIATE`, `CC_INTERMEDIATE` and `ST_GAS_INTERMEDIATE` carried **no `phys_*` keys at
all** — and `gas_offer_margin_markup_mult`'s documented rule-24 neutral fallback returns
**0.0** for a band whose key is absent, so `apply_gas_offer_margin` skipped the whole cohort.
Measured at miso-215 §2 off the assembled fleet: **38,501.0 MW = 0.5842 of the 65,907 MW**
assembled MISO gas capacity, identically in all three years.

**The repair.** One MISO-gated boolean, default False.
`data/offer_curves._offer_curve_for_group` returns each intermediate curve as a **COPY**
carrying its parent's `phys_econ_low` / `phys_econ_high`
(`CT_PEAKER → CT_INTERMEDIATE`, `CC_REGULAR → CC_INTERMEDIATE`, `ST_GAS →
ST_GAS_INTERMEDIATE`). Three properties make it coverage and not a lever:

* **Zero free parameters.** Nothing is computed and nothing minted — the merged values are
  the parent class's own already-registered p50s. Ledger **41 → 41**, `n_residual` **2 → 2**.
* **Rule 19 `[R-ONE-MECH]`.** It supplies keys an *existing* mechanism already reads; the two
  cannot stack, because without the keys the mechanism is simply inert on those rows.
* **The borrowing was validated before the field existed** (miso-215 §3): each cohort's own
  CEMS-measured marginal-HR multiplier lands within **0.0344 / 0.0388 / 0.0149** of the
  parent midpoint it borrows, against a ±0.06 bar, on **94–100 %** of the cohort's capacity.

**The seam, and why it matters.** `_offer_curve_for_group` is read at **fleet-assembly
time** — `data/fleet/assembly.py` computes
`_margin_markup_hr = base_hr × gas_offer_margin_markup_mult(suffix, tr_hr/base_hr, offer)`
from exactly the dict it returns — so a `replay_keeper --set` fires. A config-**build**-time
merge would **not**, because `--set` rides the generic `prb_overrides` channel applied
*after* `backcast_config` merges the per-ISO curves. It returns a copy so
`config.offer_curve_by_group` — the recorded config — is never mutated through a read path.

**ECON-ONLY, frozen in the PREREG before the solve.** `phys_peak` is deliberately not
borrowed: `CT_INTERMEDIATE`'s registered peak 3.00 against `CT_PEAKER`'s `phys_peak` 1.00
would replace a fuel-scaled scarcity wall with a ~$73/MWh fixed margin and **lower** the
cohort's peak offer by $29.03 / 8.69 / 23.81 (`ST_GAS_INTERMEDIATE` by $38.96 / −4.25 /
10.23) in years where C3c is already the single ledgered caveat. `phys_committed` is excluded
too: both CT and ST intermediate committed bands sit **below** their parents' `phys_committed`
and clip to 0, so including it would silently move only `CC_INTERMEDIATE`.

**A defect the repo's own freeze tests caught, disclosed.** Adding any `ScenarioConfig`
field moves the default cache key. Three pinned tests
(`test_ramp_envelope_basis`, `test_cc_committed_offer_margin`,
`test_caiso_nqc_class_factors`) failed until the field was registered in
`_CACHE_KEY_OPTIONAL_FIELDS` at its default. Without that registration the pinned key would
have moved off `4c6b03ae098b6e3e` and **orphaned every cached run repo-wide**. Default key
restored; an armed run keys distinctly. **21 unit tests** pin flag-off object identity, the
neutral-zero markup when off, the econ-only band scope, the no-mutation copy contract, the
rule-25 non-MISO gate, the live markup values, a no-op when the parent carries no `phys_*`, no
overwrite of a curve's own key, and the cache-key contract.

## 2. S-0 / S-1 / S-2 — all three pass

* **S-0 inherited.** The control **is** the keeper bundle `miso213_layering_B`, already
  attested and never re-solved, so bit-identity is definitional. All 12 keeper sidecars
  present.
* **S-1 single delta.** **789 fields in common, ZERO diffs.** Five fields are arm-only: four
  added to `main` since the keeper solved (`capacity_market_supply_clearing_by_iso`,
  `egrid_steam_collapse_heat_rates`, `locality_capacity_curves`, `retirement_sector_gate`) —
  all verified at their dataclass defaults — plus the new field itself at True.
* **S-2 liveness, measured BEFORE the solve** (`_miso217_liveness.py`, a zero-solve
  double fleet build per year):

| | tranches | capacity MW | cap-w markup HR | fixed margin @ anchor |
|---|---:|---:|---:|---:|
| `CT_INTERMEDIATE` | **264** | 6,927.3 | 4.6574 | **$14.20/MWh** |
| `CC_INTERMEDIATE` | **234** | 11,869.6 | 0.4938 | **$1.51/MWh** |
| `ST_GAS_INTERMEDIATE` | **36** | 2,984.7 | 2.4517 | **$7.48/MWh** |
| **total** | **534** | | | |

  Every one strictly positive; **0** existing markups moved; **0** changes outside the econ
  band; `mc` changed on exactly those 534 rows with **max |Δmc| = 0.0** on every other row.

## 3. The kills, every one silent

| kill | bar | measured | verdict |
|---|---|---|---|
| **K-1** C1 band exit | any cell inside ±8.00 exiting it | **none.** `CC_REGULAR`-2024 +7.419 → **+7.947** (headroom 0.581 → **0.053**); `CT_PEAKER`-2023 −5.121 → −5.934 (2.879 → 2.066) | **SILENT** |
| **K-2** C8 conditional route | the route ceasing to clear (a rise alone is not a kill) | `CT_PEAKER` share 0.2044/0.1218/0.1421 → **0.2280/0.1573/0.1319**; **zero** new D-4 failures, **zero** new D-1 failures | **SILENT** |
| **K-3** caveat budget | >1 ledgered or >0 protective | arm: 1 ledgered (C3c), 0 protective — identical to the control | **SILENT** |
| **K-4** determination class | NOT-YET on anything beyond {C3a-2025} | control fails {`price_mean|2025`}; arm fails {`price_mean|2025`}; **no new fails** | **SILENT** (see §5) |
| **K-5** instrument | S-1 or S-2 failing | both pass | **SILENT** |
| **K-6** any other PASS→FAIL | any flip | **none** | **SILENT** |

**§6's F-4 footprint disposition does not fire.** Like-for-like on the econ band, the arm's
own mean absolute deviation from the registered multiplier form is **14.97 %** of
`CT_INTERMEDIATE`'s own cap-weighted offer against `CT_PEAKER`'s already-accepted **19.19 %**
— **4.22 pp BELOW**, inside the pre-committed 5 pp disposition. **But `ST_GAS_INTERMEDIATE`
is 15.36 % against `ST_GAS`'s 6.24 %, +9.12 pp ABOVE its parent**, and the disposition as I
pre-registered it keys on the CT cohort only and does not reach it. **That is a scope limit
of my own PREREG, disclosed and not renegotiated** — §8(3).

## 4. What the arm costs, at full magnitude, never as justification

**Rule 1 `[R-STRUCT]` was pre-committed both ways** and is applied that way here: an adverse
residual inside band was declared EXPECTED before the solve and is **not** treated as a
reason to reject; it is also **not** dressed up as a gain.

**C1 — the eight largest movers** (control → arm, TWh; control headroom → arm headroom):

| cell | control | arm | Δ | headroom |
|---|---:|---:|---:|---|
| `CT_PEAKER`\|2024 | −0.884 | **−3.634** | **−2.750** | 7.116 → 4.366 |
| `COAL_PRB`\|2024 | −3.166 | −2.159 | +1.007 | 4.834 → 5.841 |
| `CT_PEAKER`\|2023 | −5.121 | **−5.934** | −0.813 | 2.879 → **2.066** |
| **`CC_REGULAR`\|2024** | **+7.419** | **+7.947** | **+0.528** | **0.581 → 0.053** |
| `CC_REGULAR`\|2023 | −2.774 | −2.288 | +0.486 | 5.226 → 5.712 |
| `CC_REGULAR`\|2025 | −2.423 | −2.061 | +0.362 | 5.577 → 5.939 |
| `ST_GAS`\|2024 | −6.803 | −7.155 | −0.352 | 1.197 → 0.845 |
| `CC_CHP`\|2024 | +0.161 | +0.417 | +0.256 | 7.839 → 7.583 |

**THE PRE-REGISTERED UN-INSTRUMENTED RISK MATERIALISED.** The PREREG declared, before the
solve, that the phase-0 static screen holds price fixed and is therefore **blind to
cross-class backfill** — CT displaced into CC — and that K-1 was the only instrument that
could see it. It happened: `CT_PEAKER` loses 2.750 TWh in 2024 and `CC_REGULAR` gains 0.528,
leaving **0.053 TWh** of a 0.581 TWh band. **No exit, so K-1 is silent as written — but this
is the single most important number in the record**, and any future MISO arm that moves CC
upward in 2024 now has essentially no headroom to work with.

**C8** — `CT_PEAKER` forced share **0.2044 / 0.1218 / 0.1421 → 0.2280 / 0.1573 / 0.1319**.
2023 rises further above the 0.15 peaker budget; **2024 crosses it**; 2025 falls below its
starting point. K-2 is silent **exactly as pre-registered** — rule 20's conditional
provenance+shape route still clears, with zero new D-4 off-window failures and zero new D-1
shape failures on the class — but a class-year crossing a protective budget is a real cost of
the arm and is named here, not buried in a table.

**C3a — reported, never argued.** `+0.9132 → +1.0959` (**+0.183 pp**, away from zero),
`−3.8390 → −2.8793` (**+0.960**, toward), `−11.7466 → −12.2965` (**−0.550**, away). C3a-2025
is the criterion the determination hangs on and the arm makes it **worse**. That is stated
plainly and is not offset against anything.

## 5. The first scoring pass fired K-4 — an instrument condition, disclosed not renegotiated

The **first** run of the scorer fired **K-4**: `price_tail` (C3c) scored **FAIL in all three
years** in the arm against **CAVEAT** in the control. The measured tail values are
**byte-identical between the legs**:

| year | model hours RT LMP > $200 | actual | control status | arm status (pass 1) |
|---|---:|---:|---|---|
| 2023 | 3 | 30 | CAVEAT | FAIL |
| 2024 | 7 | 37 | CAVEAT | FAIL |
| 2025 | 0 | 88 | CAVEAT | FAIL |

**The arm did not move the price tail at all.** A `replay_keeper` solve writes **no
attestation**, so the arm's C6 governance gate read **UNATTESTED**, and **guard (b) of the
C3c standing rule requires governance to PASS** — so the reclassification the control enjoys
was blocked and the raw FAIL stood. This is the miso-200 vacuous-pass trap in its mirror
image, and the charter already required the attestation as a deliverable. It was written
(`scripts/gen_miso217_attestation.py`, the gen_miso213 pattern, ledger 41/2 unchanged) and
the arm **re-scored**. **Both passes are in the record**: `_miso217_ab_gates.json` holds the
final scoring, and this section is the first one. No bar was moved and no kill was
renegotiated — the bundle was completed.

## 6. What this does and does not close

**Closed:** the `phys_*` coverage gap named at miso-214 §6, sized at miso-215 §2 and
unblocked at miso-216. 58.4 % of MISO's assembled gas capacity now enters the armed
offer-margin mechanism at zero free parameters.

**NOT closed, and this finding does not claim otherwise.** miso-214's standing result holds:
**62–70 % of the CT energy the model misses was produced by the real market below the plant's
own delivered cost, at the market's own price** (41–49 % on the strictest single
substitution; 44–60 % paying the better of DA and RT) — energy **not reachable by any offer
or price mechanism**. This arm reached at most **bucket C** (0.167 / 0.257 / 0.167 of the
missed MWh) and part of **bucket A** (0.131 / 0.130 / 0.215) — and in the event it moved
`CT_PEAKER` **further from** actual in 2023 and 2024, not toward it. **No CT C1 movement from
this family is presented as closing the class's gap.** C3a-2025 remains an evening
net-load-ramp scarcity-tail object (miso-202/203) that this lane never claimed to reach.

## 7. My prior, scored against interest

* **P-1 (S-2 liveness) — RIGHT, exactly.** Predicted **534** tranches (264 + 234 + 36);
  measured **534**, every one positive, with the `ov` bypass I named as the only downside
  risk not materialising.
* **P-2 (LP vs the screen bound) — RIGHT on both legs.** |LP Δ| ≤ 0.75 × |screen Δ| for
  `CT_PEAKER` in **3 of 3** years (ratios 0.551 / 0.520 / 0.056) against a ≥ 2-of-3 bar; sign
  match in **2 of 3** (2025 the screen said +1.457 and the LP delivered −0.082) against a
  ≥ 2-of-3 bar.
* **P-3 (C1, the named risk) — RIGHT, barely.** Predicted `CC_REGULAR`-2024 in **[+7.2,
  +8.0]** with no exit; measured **+7.947**. Right by **0.053 TWh**. I record that as a near
  miss, not a clean call.
* **P-4 (C8) — RIGHT on both legs.** Predicted `CT_PEAKER`-2023 into **[0.21, 0.26]** with
  the conditional route still clearing; measured **0.2280**, route clears. I did **not**
  predict 2024 crossing the budget, and it did.
* **P-5 (C3a) — the 2025 leg WRONG.** Predicted |ΔC3a-2025| **< 0.5 pp**; measured
  **0.550 pp**. Wrong by 0.05 pp, and in the adverse direction. The 2023/2024 legs are RIGHT
  (0.183 and 0.960 against a < 1.5 pp bar).
* **P-6 (F-4 footprint) — RIGHT on the like-for-like basis, and my literal wording was
  mis-specified.** Predicted the arm's `CT_INTERMEDIATE` footprint **within ±5 pp of
  `CT_PEAKER`'s 24–30 %**. Against the only apples-to-apples comparator — `CT_PEAKER`'s
  **econ-band** 19.19 % — it is 14.97 %, **4.22 pp below**: right. Against the 24–30 % figure
  **as literally written** it is 9–15 pp below: wrong. miso-216's 24–30 % was measured over
  **all** marked-up bands and mine over the **econ** band; comparing them directly is a
  scope error and the disposition should have named the basis.
* **P-7 (promotion) — RIGHT direction.** I put P(promote) at **0.40** and every kill came
  back silent. The two risks I named as live are exactly the two that moved most (K-1's
  headroom and K-2's budget) — both stopped just short of firing.

## 8. Reported against interest

1. **`CC_REGULAR`-2024 has 0.053 TWh of headroom left.** The arm consumed 91 % of it. K-1 is
   silent on its own terms, but this keeper is now one small CC-positive move away from a
   load-bearing C1 band exit, and the next MISO session must treat that cell as effectively
   spent.
2. **C8 `CT_PEAKER`-2024 crossed the 0.15 peaker budget** (0.1218 → 0.1573). K-2 was written
   to fire only if rule 20's conditional route stopped clearing, and it did not — but the
   arm converted a within-budget class-year into an over-budget one, which is a protective
   regression by any plain reading.
3. **§6's disposition does not reach the ST cohort.** `ST_GAS_INTERMEDIATE`'s footprint is
   **+9.12 pp above** its parent's while `CT_INTERMEDIATE`'s is 4.22 pp below its own. I
   wrote the disposition around the CT cohort because miso-216 had measured CT; had I written
   it per-cohort it would have fired on ST. The wording stands as written and the number is
   reported.
4. **The first scoring pass fired a kill.** §5 explains why and shows the C3c values are
   byte-identical, but the fact remains that a kill fired before the bundle was complete, and
   the fix was to complete the bundle — a step the charter required anyway. A reader who
   wants to discount this promotion should start there.
5. **C3a-2025, the only criterion the determination hangs on, got worse** (−11.747 →
   −12.297). Nothing in this arm was aimed at it and nothing here claims otherwise.
6. **`CT_PEAKER` moved further from actual in 2 of 3 years** (−5.121 → −5.934 in 2023,
   −0.884 → −3.634 in 2024), on the class miso-214 identified as the largest C1 mover. The
   arm's structural case does not depend on that going the other way, and it did not.
7. **The static screen predicted the 2025 CT sign wrong** (+1.457 screen vs −0.082 LP). The
   bound's magnitude discipline held in all three years; its sign did not.

## 9. Governance

Rule 15 `[R-DASHBOARD]`: the arm is registered as **`2026-09-05-miso-217-intermphys`**
(sidecar + run payload + bench parts + the KEEPER `hourly/` sidecars) in this session; the
control is the keeper bundle itself and was already registered. Rule 22: 2023–2025 only.
Rule 16 `[R-ALLYEARS]`: all three years in one invocation, sequential. Rule 12 `[R-PARALLEL]`:
solved in-session, never on CI. Rule 21 `[R-DOF]`: no new ledger entry — 41 entries, 2
residual, unchanged. Rule 19 `[R-ONE-MECH]`: coverage for an existing mechanism, which cannot
stack with it. Rule 24 `[R-REGISTRY]`: one registered field, recorded in `run_config.json`,
and registered in `_CACHE_KEY_OPTIONAL_FIELDS` at its default. Rule 25 `[R-ISO-SCOPE]`: the
field is MISO-gated with a unit test proving five non-MISO ISOs are untouched with the flag
on; **PJM and CAISO carry the same coverage gap in kind and their cells enter `U`** — their
lanes', never filled from here. Rule 28(c): the base row was added in the same commit as the
field, with **a cell line in every one of the six shards**;
`scripts/check_mechanism_matrix.py` passes and the keeper stamp is re-stamped. Rule 27
`[R-PUSH]`: every file edited locally and blob-verified after push.
`scripts/audit_keepers.py --iso MISO` PASS 0/0.

**DO-NOT-REDO honoured**: `gas_hub_basis_overlay` (R), `miso_offer_level_dispersion` (R),
`miso_offer_spread_anchored` (I), `miso_rdt_measured_limit` (R),
`miso_south_gas_delivered_cost_basis` (R), `gas_offer_margin_zonal_anchor` (I — the ZONAL
grain), `zonal_gas_basis` (K), `measured_offer_surface` (R) are neither re-tested nor
re-opened. **CLOSED BY MEASUREMENT and not re-opened**: the CT commitment-bridge / min-load AS
family (miso-214); the dual-fuel oil confound (miso-215); the anchor's BASIS/CLASS grain
(miso-216); heat- or peak-load-keyed capability removal (miso-203). **OWNER-COURT and not
armed**: the average-vs-marginal delivered-cost convention (miso-212 §8); the D-2 5(i)
seam-response object; and the FORM question miso-216 named — whether a fixed-margin
decomposition suits a class with that much delivered-fuel dispersion — which §3's ST-cohort
number now bears on and which this session did **not** decide.

Next shorthand: **miso-218**.
