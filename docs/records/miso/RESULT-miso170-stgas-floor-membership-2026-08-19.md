# RESULT miso-170 — the laid-up-plant MEMBERSHIP repair: 15 of 18 D-4 conduct failures cleared, C8 2024 PASSES, and the pre-registered K-1 FAILS AS WRITTEN on an instrument artifact

**Session miso-170 (2026-08-19).** Executes the miso-169 §5 **ask 2** on its
second branch — the rider is right, the floors are wrong — per
`PREREG-miso170-stgas-floor-membership-2026-08-19.md`, committed before either
arm solved.

**Keeper `2026-08-19-miso-169-online-gated` UNCHANGED. Nothing is promoted by
this session.** Runs registered (rule 15): control
`2026-08-19-miso-170-control` (`miso170_membership_A`), arm
`2026-08-19-miso-170-membership` (`miso170_membership_B`).

**RHO_CLIP (the session's conditional scope item 2) WAS NOT TOUCHED.** No owner
ruling on the band exists — `docs/governance/` carries none and no commit since
miso-169 addresses it — so the standing nyiso-144 escalation holds and both arms
solved at the same uncited 0.5 floor the keeper did (`MEASURED
online_rho=0.5000 (pre-clip 0.1764)` in both solve logs).

---

## 1. What was built, and why the charter's single channel was not enough

The charter named the nyiso-140 `reliability_floor_plant_exclusions` machinery.
That machinery carries **2 of the keeper's 18** D-4 per-unit conduct failures;
the other **16** belong to `st_gas_mustrun_per_plant`, which had **no exclusion
channel at all**. This is the nyiso-140 → nyiso-144 story exactly one mechanism
later (rule 19 `[R-ONE-MECH]`, *enumerate what already floors the same class*),
so both halves shipped:

* **(a) reliability floor — existing machinery, data only.** The census is
  written into `reliability_floor_coeffs_MISO.csv`'s optional
  `exclude_plant_codes` column **mechanically**, by a new opt-in
  `--patch-reliability-coeffs` step on the census deriver, so the column cannot
  drift from the census and a later coefficient re-derive cannot wipe a
  hand-typed list. 19 of 78 limbs; **the original 17 columns are byte-identical**.
* **(b) per-plant must-run floors — one new GATED flag,
  `ScenarioConfig.mustrun_plant_exclusions`** (default off), reading the SAME
  census. It gates **both** seams in `_compose_min_gen_floors`: the
  committed-tranche block and the `st_gas_mustrun_p25_level` block, which reads
  the measured artifact directly and would otherwise have left the correction
  **silently inert on this keeper**.

Global default cache-key pin `603c2498bf71d21d` verified UNMOVED; the armed
variant hashes distinctly. **Rule 21 `[R-DOF]`: zero new free parameters** — a
plant-code SET produced by a conduct test, `n_scalars` 0.

## 2. The identification — one census, computed blind to D-4

Unchanged deriver, the nyiso-140 criterion verbatim: median CAMPD plant gross
load ZERO in every (year, 4-hour block) cell of 2023–2025. **15 of 62 covered
MISO plants qualify; the nearest non-qualifier sits at 16/18 cells.** The test
reads only the meter and **selects 7 of the 8 D-4-flagged plants without being
shown any of them** — agreement, not fitting.

**Plant 1402 Little Gypsy does not qualify and was left in, named before the
solve.** 6/18 cells, pooled median 45.0 MW, P(on) = 0.506 — an ordinary cycler,
the NYISO plant-7314 case verbatim. Its defect is measured and named as the
successor: its floor window is `online_frac` **pooled at 0.508** while its own
per-year metered online share is **0.2495 / 0.6134 / 0.6548**, so in 2023 the
floor commits it across the top 50.8 % of system-load hours against a plant
that ran 25 % of the year — a ~2.3× over-commitment produced by the pooled
vintage. **Named successor: per-year (not pooled) `online_frac` for the
per-plant must-run window.** Not bundled here (rule 19).

## 3. The pre-registered gates, as scored

Scorer `scripts/probes/_miso170_membership_ab.py`, **committed before either
result was read**; record `_miso170_membership_ab.json`.

| gate | verdict | measurement |
|---|---|---|
| **K-0** control inertness | **PASS** | 12/12 scored sidecars, all years, `max\|diff\| = 0.0`, non-numeric equal |
| **K-1** membership exactness | **FAIL AS WRITTEN** | 2 residual rows, both plant 1104 `reliability_floor` (2023, 2025); zero stray losses |
| **K-2** liveness | **PASS** | shed 0.5295 / 0.8653 / 0.9459 TWh vs pre-registered 0.5044 / 0.7531 / 0.7853, inside ±50 % every year |
| **K-3** conduct failures | **PASS** | 18 → 3, **zero new**, zero new off-window; the pre-named survivor (2023 `st_gas_mustrun_per_plant` × 1402) present |
| **K-4** C8 (objective) | **2024 FAIL → PASS** | 2023 and 2025 still FAIL |
| **K-5** no gated flip | **PASS** | zero record-grain PASS → FAIL flips over 67 records |
| **K-6** shape preserved | **PASS** | `profile_r` 0.951 / 0.958 / 0.975; `cv_ratio` 1.422 / 1.109 / 1.265 |

K-2's prediction was computed from the control's own committed D-4 rows before
the solve and landed within 5–20 % of measurement in every year.

## 4. The K-1 forensic — an instrument artifact, not a membership residual

Read at UNIT grain from the arm's own `floors/<year>_P1.npz`:

> **Plant 1104's ST_GAS rows carry ZERO reliability-floor unit-hours in the
> arm, in both years.** What survives is **777 (2023) and 763 (2025) unit-hours
> on the plant's CT_PEAKER tranches, entirely inside h15-21** — the MISO-Plains
> CT_PEAKER evening-ramp limb, which never leaves its own declared window.

D-4 reports that as `reliability_floor × ST_GAS` because
`aggregate_floors_by_plant` collapses a plant's unit rows into ONE plant row and
labels the plant with its **most common unit group** (1104: 4 ST_GAS rows vs 3
CT_PEAKER, so the plant reads ST_GAS). A **CT_PEAKER** floor is therefore
charged to **ST_GAS's** provenance leg — and the per-unit conduct rider, which
is deliberately gated to all-hours windows *because that is where the
off-window test is vacuous*, convicts on a floor whose own window test is live
and passing.

**This is the first half of the honest answer to miso-169's ask 2:** the
rider's per-unit conduct leg, as wired, can charge one class's provenance with
another class's floor. It is a real instrument defect, independent of this
lever.

**The mechanical verdict is NOT reinterpreted.** Under PREREG-miso170 §6, a
K-1 failure means the arm is **REJECTED-AS-ARMED**, and that stands as written.
The forensic above was produced *after* the result and does not get to convert
a pre-registered kill into a pass — that is precisely the discipline the
pre-registration exists to enforce. The arm is not promoted, and the session
does not self-absolve.

## 5. What the arm actually bought

* **D-4 per-unit conduct failures 18 → 3** (2023: 10 → 2, 2024: 4 → 0,
  2025: 4 → 1), with **zero new failures** anywhere.
* **C8 ST_GAS 2024 FAIL → PASS (grounded above budget)** — the first MISO year
  ever to clear C8's provenance leg. 2023 fails on 1402 (pre-registered) plus
  1104 (§4); 2025 on 1104 alone (§4).
* **~2.34 TWh over three years** of forcing removed from plants whose own meter
  says they were mothballed (0.5295 / 0.8653 / 0.9459), at zero DOF.
* Forced share 32.7 → 31.2 %, 34.4 → 31.9 %, 46.2 → 43.6 % — **still above the
  30 % cap in every year**, exactly as pre-registered. This lever buys
  legitimacy, not budget headroom.
* **C3a-2025 −12.4 % → −12.1 %.** Disclosed, not claimed: it is 0.3 pp on a
  load-bearing miss the miso-163 owner ruling closed as a model-class limit,
  and no gate in this prereg rewards it.
* Determination **NOT-YET on both arms** (C3a-2025; C6 UNATTESTED because fresh
  probe bundles carry no attestation) — exactly the honest ceiling §4 of the
  prereg stated in advance.

## 6. Open items for the owner

1. **The K-1 disposition.** The mechanical verdict is REJECTED-AS-ARMED on a
   gate that measured an instrument artifact. The repair itself is exact at
   unit grain and clears 15 of 18 conduct failures with zero new ones. Whether
   the arm is a keeper candidate on rule 1 `[R-STRUCT]` is an owner call, not
   this session's.
2. **The D-4 plant-grain class attribution** (§4). A plant that mixes classes
   has all its floors charged to its dominant class, so a windowed limb's
   forcing can fail an all-hours mechanism's conduct rider in another class.
   This affects any ISO with mixed-class sites, not just MISO.
3. **The 1402 window successor** (§2) — per-year rather than pooled
   `online_frac`. Its own identification, its own A/B, its own DOF answer.
4. **RHO_CLIP remains the standing nyiso-144 owner call**, untouched here.

## 7. Note for the record — a parallel session shares this number

`miso170_layup_A` and `FINDING-miso170-congestion-elmp-assessment-2026-08-19.md`
in `main` are a **different** miso-170 session (a no-LP congestion/ELMP
assessment plus its own K-0 control). That session's own text names this A/B as
a separate object. The two do not overlap; this result concerns only the
membership repair.
