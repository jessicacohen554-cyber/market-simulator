# FINDING — caiso-186: the published seasonal CC capability basis is **BUILT, EXACT, and REFUSED BEFORE SOLVE** by its own pre-registered `G-NOCONTRA` bar. The basis arithmetic passes every leg to machine precision; what kills it is a **SECOND mechanism the incumbent nameplate basis was silently absorbing** — the full statistical CC forced-outage rate stacked on the CAMPD outage overlay. **KILL-BEFORE-SOLVE: zero LP spent, nothing registered, keeper unchanged, C3a never read.**

**Outcome: the chartered lever is REJECTED. The DEFECT it targets is REAL and is confirmed
at full magnitude; the INSTRUMENT is refused because arming it would make the model assert
an incapability the CEMS record refutes at 4 of 27 commensurable CAISO CC plants** — the
caiso-185 failure mode reached from the opposite direction, caught by the bar this charter
put in place precisely to catch it.

Keeper **UNCHANGED** at `2026-08-09-caiso-184-c1-lpbasis`. DOF ledger **11 / 8**, untouched.
No data byte written, no derive re-run. `calibration-complete.json` and `holdout-freeze.json`
**untouched (owner acts)**. **C3a WAS NEVER READ** — no arm was solved, so no fit outcome
could have influenced this verdict (rule 1 `[R-STRUCT]` in its strongest available form).

**Pre-registration:** `PRECHECK-caiso186-seasonal-capability-2026-08-09.md`, 433 lines,
sha256 `d97aec251595c8ed73ecc5ec9b6d3b6b9be0fc0202c10851b181e91e0f6644de`, commit
`7fb3bee1`, pushed and blob-verified (commit-SHA round trip, local == remote) **before any
measurement of this session's object was taken and before any line of the instrument was
written**.

Instruments: `scripts/probes/_caiso186_seasonal_capability.py`, `_caiso186_be_proof.py`.
Records: `_caiso186_seasonal_capability.json`, `_caiso186_be_proof.json`.
Test: `tests/unit/data/test_fleet.py::TestCcWinterCapabilityBasis` (6 tests / 9 subtests).

---

## 1. P0-1 — DO-NOT-REDO, discharged

Discharged in full in PRECHECK §0 and not repeated. In summary: **not**
`cc_capacity_reconcile` (caiso-185, `R`, REFUSED — not armed, table not re-derived, not
hand-edited, and no CEMS value written into any capacity slot); **not** the denominator
basis (caiso-184, `K` — `outages.py` is not modified, see G-DENOM); **not** the envelope
depth (caiso-181) or grain (caiso-183); **not** any struck lever. `caiso_dam_outages` stays
`U` and was not armed. The positive licence is FINDING-caiso185 §5 and §10 item 2, which
file this exact object as the root cause that refusal opened and which that charter was
barred from taking.

---

## 2. P0-2 — THE AVAILABILITY-BASIS RULE, honoured

PRECHECK §2 fixed, per quantity, which side of `pmax × availability` it lives on. The
instrument writes **only EIA-860 PUBLISHED RATINGS** (`Nameplate`, `Summer`, `Winter`
Capacity) and ratios of them into the capacity slot and the multipliers. **The CEMS record
enters only as a check.** `git diff` over `src/` contains no CAMPD/CEMS read on any path
reachable from `capacity_mw` or `availability`; every CEMS figure in the probe records sits
under a `cems_*` key. **G-CHECKONLY PASSES.**

---

## 3. THE INSTRUMENT AS BUILT

`ScenarioConfig.cc_winter_capability_basis`, default `False`, acting only alongside
`cc_nameplate_summer_derate`. Capacity basis becomes the published seasonal envelope
`B = max(net_summer, winter)`; each season's availability takes its own published rating.

| | incumbent | armed |
|---|---|---|
| LP `capacity_mw` | `nameplate` | **`B`** |
| summer leg | `× net_summer / nameplate` | `× net_summer / B` |
| off-summer leg | *(none)* | **`× winter / B`** |
| temperature-curve anchor | summer mean only | **summer mean AND off-summer mean** |

Zero fitted scalars, zero new numeric parameters, **DOF ledger 11 / 8 unchanged**.

### 3a. One implementation defect found and fixed in P0, declared

The first cut inherited the incumbent's `if ratio < 1.0` anchor skip. That left the arm
**inconsistent**: a plant whose summer rating equals its nameplate got no summer anchor at
all, so its summer mean landed at `_sm × rating` instead of at the rating. Fixed to anchor
**unconditionally** — the flag's identity is "each season's mean IS its published rating,
for every plant or none", and a per-plant exemption would have been exactly the subsetting
PRECHECK §6.4 forbids. Reported as a defect found and repaired in P0, not smoothed over;
every number below is post-fix.

---

## 4. P0-3 — THE SIZING. **Not inert, and the summer identity holds to measurement.**

Read-only, through the shipped path (`load_or_synthesize_bins` → `bins_to_fleet` →
`generators_to_fleet_arrays`), built twice from the keeper bundle's own `run_config.json`,
identical but for the one field, all three years.

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| CC bins moved (of 258) | 45 | 45 | 45 |
| **non-CC bins moved** | **0** | **0** | **0** |
| net bin capacity Δ | −1191.9 MW | −1191.9 MW | −1191.9 MW |
| **off-summer capability moved** | **−2264.3 GWh (−3.18 %)** | **−2069.4 GWh (−3.30 %)** | **−1724.5 GWh (−2.93 %)** |
| **summer capability moved** | +12.3 GWh (**+0.036 %**) | +1.9 GWh (**+0.005 %**) | +35.2 GWh (**+0.106 %**) |

**Not inert** (BRANCH C threshold 0.1 %: off-summer exceeds it 29-33×). And the summer leg
is invariant to five thousandths of a percent in 2024 — the identity
`B × (ns/B) ≡ nameplate × (ns/nameplate)` holding as a **measurement**, not an assertion.

**Direction, as pre-registered in P0-4:** the dominant leg **REMOVES** ~3 % of off-summer CC
capability, which raises price — the **wrong** direction for a model already +10.5 % / +13.1 %
over. That was pre-declared admissible and is reported here because it is what happened, not
because it was hoped for.

---

## 5. THE GATES THAT PASS — and they pass *exactly*, not approximately

### G-MONO — the sign rule is **proved**, per plant, in three legs

* **G-MONO-A (capacity, exact).** The bin rescale must equal `B / nameplate` whatever the
  fleet-vs-EIA membership. Measured: **0 violations of 45 bins**, to machine precision (plant
  358 Mountainview `1.0706` got, `1.0706` predicted). The sign rule follows arithmetically:
  **falls** wherever `B < nameplate` (55 of the 67 California CC plants publish
  `winter < nameplate`), **rises** wherever `B > nameplate` (8 plants: 7307 +8.87 %, 358
  +7.06 %, 56041 +6.92 %, 55985 +5.55 %, 54912 +5.00 %, 55970 +4.45 %, 55656 +2.57 %,
  55933 +1.81 %).
* **G-MONO-B (summer mean).** 33 plant-years move, **0 against their own published pair**:
  24 fall (0.9875–0.9979) and 9 rise (1.0963–1.1186), and every one moves in the direction
  its own `B / nameplate` dictates. The falls are the declared **H-SUMMER** consequence
  (PRECHECK §3a — availability is clipped at 1, so the peak is bounded by `pmax`, and moving
  `pmax` onto the published envelope bounds it there); the rises are the same effect on the
  raise plants.
* **G-MONO-C (off-summer constancy).** The per-hour ratio is constant within the season for
  every plant except where the two declared clips bind (81 plant-years show a spread,
  bounded above at exactly 1.0 — the trailing availability clip — and below by the
  temperature curve). Confirms a **single rating swap**, not an hour-shaped adjustment.

**G-MONO PASSES.**

### G-DENOM — caiso-184's identity preserved bit-for-bit

`outages.py` is **not modified** and the flag cannot reach `_iso_plant_capacity` at all.
Under `unit_outage_lp_capacity_basis` the raised denominator is still exactly the EIA-860
**nameplate** the extract's `unit_capacity_mw` numerator is written on — median
`raised / nameplate` = **1.000** across 49 CC bins (against **0.910** unraised). The outage
derate stays the dimensionless share `unit_nameplate / plant_nameplate`, applied to whatever
capacity the LP carries. **G-DENOM PASSES.**

### G-SIXISO / BE — the other five ISOs are byte-unchanged

| leg | bar | result |
|---|---|---|
| **BE-1** | default `False`, six ISOs' DEFAULT-CONFIG cache keys unmoved vs `origin/main` (`e9f99e66`) | **PASS** — 6 / 6 identical (ERCOT `603c2498bf71d21d`, CAISO `51b2892ed6f0d742`, PJM `5cfabdff9bfd6de6`, MISO `ea1c7983d5c54ec4`, NYISO `1462c74e6775a24b`, NEISO `62923af03d1c9bac`) |
| **cache-key registration** | in `_CACHE_KEY_OPTIONAL_FIELDS` **and** `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`, **same commit as the field** | **PASS** — `check_cache_key_registration.py`: ok, 706 fields, 153 registered, all resolve, all declared defaults match. (caiso-184 omitted this step and needed an FFR-8A backfill; PRECHECK §3c named that as the reason to do it here.) |
| **armed hashes distinctly** | an armed run cannot reuse a bundle | **PASS** — CAISO parent-only `1be3248ad5894885` → armed `cb845e6b7c907745` |
| **BE-3** | parent flag off ⇒ no-op | **PASS** — ERCOT (304 bins) and MISO (423 bins): bin capacities and the full availability matrix **bit-identical**, max abs Δ **0.0** |
| **BE-4** | a **test**, not merely a measurement | **PASS** — `TestCcWinterCapabilityBasis`, 6 tests / 9 subtests: default-off on all six ISOs, distinct cache key, registration + declared default, the published-pair arithmetic (including the deliberately **unclamped** winter — deleting it would delete the upward direction), the absent-plant fallback, and the parent-off no-op |
| **BE-5 / rule 23** | no data byte written | **PASS** — sha256 ledger over the EIA-860 parquet and all six `cc_capacity_reconcile_*.csv`, unchanged; no derive run |

**G-SIXISO PASSES.** PJM / NYISO / NEISO also arm `cc_nameplate_summer_derate`, so
default-off is what keeps them still.

---

## 6. THE REFUSAL — **G-NOCONTRA fails, and the arithmetic is one number**

The arm creates **14 NEW measured contradictions** and **deepens 3**, across **4 of the 27
commensurable CAISO CC plants**, in both seasons.

| plant | season | published `B` | CEMS p999 | CEMS ÷ `B` | keeper max | **arm max** | **arm ÷ CEMS** |
|---:|---|---:|---:|---:|---:|---:|---:|
| 260 Moss Landing | summer | 1020.0 | 1011.1 | 0.991 | 1049.6 | **984.3** | **0.974** |
| 55345 Otay Mesa | off-summer | 602.5 | 603.5 | **1.002** | 685.8 | **581.4** | **0.963** |
| 55345 Otay Mesa | summer | 602.5 | 591.8 | 0.982 | 685.8 | **581.4** | **0.982** |
| 56026 | summer | 147.8 | 145.3 | 0.983 | 148.6 | **142.6** | **0.981** |
| 62116 | off-summer | 690.0 | 673.7 | 0.976 | 674.7 | **665.9** | **0.988** |
| 62116 | summer | 690.0 | 674.7 | 0.978 | 674.7 | **665.9** | **0.987** |
| 55748 *(deepened)* | summer | 300.0 | 301.3 | **1.004** | 295.4 | **289.5** | **0.961** |

**Every one is the same number.** The arm's implied peak availability —
`arm_max ÷ B` — is **0.9648–0.9651 on every violated plant-season**. It is not a coincidence
and it is not the basis: it is the **statistical CC forced-outage rate**.

### 6a. The root cause, named

In a historic backcast a CC unit's availability is set to `1 − WEFOR`
(`arrays.py`, the `is_cc_np and cc_np_derate_backcast` branch). The block's own comment says
the CAMPD overlay "already carr[ies] every ≥ 5-day outage … so their full statistical WEFOR
would double-count those events. Cap it at the short-outage residual". **On the CAISO keeper
`wefor_residual` is `None`, so that cap is never applied** and the FULL statistical CC WEFOR
(~3.5 %) sits on top of the CAMPD outage overlay that already supplies every real outage.
The code comment adjacent to the relief switch concedes the point explicitly — the relief is
"harmful where the class is already over (CC)".

**Over on what?** On capability — and the source of that surplus is precisely the thing this
session set out to remove. `nameplate ÷ B` on the violated plants is **1.0133 – 1.3706**:
between 1.4 % and 37.1 % of headroom over the published rating. That headroom is what
absorbs the 3.5 %. Meanwhile these plants demonstrably deliver **97.6 – 100.4 %** of their
published seasonal rating, so `0.965 × B` cannot reach them.

> **Rule 19 `[R-ONE-MECH]`: the nameplate rating headroom and the statistical CC WEFOR are
> two mechanisms doing one job.** Removing the first without reconciling the second breaks
> an offset the model has been relying on unnamed. That is why the basis — which is right —
> cannot be armed yet.

**This is caiso-185's disease in a third organ.** That session found a value and its slot on
different bases; caiso-184 found a numerator and a denominator on different bases; this is a
**capacity basis and a derate calibrated against a different capacity basis.**

### 6b. The repair half *works*, and is reported at full magnitude

The mechanism is not one-sided, and the direction it was built for lands. It **improves 14
pre-existing contradictions** the keeper carries:

| plant | keeper off-summer ÷ CEMS | **arm off-summer ÷ CEMS** |
|---:|---:|---:|
| **358 Mountainview** | 0.9005 | **0.9641** |
| 55933 | 0.9727 | **1.0258** |
| 55985 | 0.9758 | **1.0299** |
| 56041 | 0.9566 | **1.0228** |

Mountainview — the mirror-image plant FINDING-caiso185 §5 named, whose published winter
capacity (1110.0 MW) exceeds its nameplate (1036.8 MW) and whose demonstrated off-summer
peak is 1111.0 MW — moves from the model denying it **110 MW** it is recorded as having
produced to denying **40 MW**. The residual 40 MW is, again, the same 3.5 %.

**Rejected whole, not in part.** PRECHECK §6.4 pre-registered that arming a subset — for
instance only the 8 raise plants, which would have improved every number in this section —
is a residual-fitted mechanism and is forbidden. It was available and it was not taken.

### 6c. What was NOT done

**The pre-registered anchoring statistic was not re-selected.** PRECHECK §3 fixed
**mean**-anchoring on symmetry with the incumbent's own summer anchor and stated: "it will
not be re-selected after seeing a sizing or a price." A **rating-point** anchor (capability
at the coldest off-summer hours = the published winter rating) has an independent principled
justification, avoids the H-CLIP relaxation, and would have changed these numbers. It is
filed in §8 as a successor and was **not substituted mid-session**. That is what the
pre-registration is for.

**No compensating factor** (PRECHECK §6.5): no scalar, clamp or blend was added to lift the
arm over the bar.

---

## 7. THE COMMENSURABILITY CORRECTION — discovered in P0, declared as **NOT pre-registered**

Extending caiso-185's 7-plant check to the whole CC population initially produced 47
"contradictions", most of them nonsense: the CEMS figure is a CAMPD **plant** total (every
unit at the site) while the model capability sums only the CC bins, so at a
mixed-technology site the ratio measures fleet composition, not capability — plant 10294
showed the **keeper** at 80.6 MW against a 157.0 MW plant total.

The screen applied is the **deriver's own**, reused verbatim rather than invented here:
`derive_cc_capacity_reconcile._model_cc_capacity` keeps a plant only when its CC_REGULAR
capacity is ≥ `_PURE_PLAY_CC_SHARE` (0.90) of the plant's total model capacity. **27 of 49
plants are commensurable; the other 22 are reported in full** (`noncommensurable_rows`) and
simply not scored against a total covering machines the model number does not. This changed
no gate bar, no mechanism and no capacity — it corrected the **check instrument**, and it is
labelled as a P0 discovery throughout.

---

## 8. GATE TALLY AND DISPOSITION

| gate | verdict |
|---|---|
| **G-DOF** | **PASS** — 11 / 8, unchanged; no free parameter added |
| **G-NOFIT** | **PASS** — zero fitted scalars; every capacity EIA-860-published |
| **G-CHECKONLY** | **PASS** — no CEMS value reaches a capacity slot or a multiplier |
| **G-MONO** | **PASS** — A: 0/45 capacity violations, exact; B: 33 moves, 0 against the published pair; C: single rating swap |
| **G-DENOM** | **PASS** — `outages.py` untouched, median raised ÷ nameplate 1.000 |
| **G-SIXISO / BE-1..5** | **PASS** — six ISOs' default keys unmoved, ERCOT/MISO bit-identical, test added |
| **G-NOCONTRA** | **FAIL — 14 new + 3 deepened, 4 of 27 commensurable plants. STOP-THE-LINE.** |
| **G-C1 / G-PROT / G-LOYO / CONTROL** | **NOT REACHED** — no arm solved; nothing registered, so nothing is unscored on the dashboard |

**BRANCH D (PRECHECK §9).** No LP was spent. Nothing was registered on the dashboard —
there is no completed run to register, so rule 15 is not engaged. The keeper is unchanged.
**No bar was moved**, no statistic re-selected, no subset armed, no compensating factor
added.

**The field is RETAINED default-off rather than deleted.** Rule 26 `[R-DELETE]` targets a
deprecated **fitted** knob that "still parses" and can be re-swept — a re-armable answer key.
This carries **zero fitted content**: there is no answer to key, every value is a published
rating, and the named successor reuses this exact code once the WEFOR double count is
resolved. The refusal is written into the field's own docstring, the CLI help and the matrix
cell, so re-arming it is a governance act rather than an accident. **Flagged for owner
override** if the stricter reading is preferred.

---

## 9. THE ROOT CAUSE OPENED (rule 14's requirement) — filed, NOT built

1. **THE PRIMARY SUCCESSOR — reconcile the backcast CC forced-outage residual against the
   outage overlay.** `wefor_residual` is `None` on the CAISO keeper, so the full statistical
   CC WEFOR applies on top of a CAMPD overlay that already carries every real outage. That
   is a live rule-19 double count on the **current keeper**, independent of this session's
   flag, and it is what makes a published-rating capacity basis inadmissible today. It needs
   its own charter, its own pre-registration and its own DOF accounting
   (`wefor_residual` / `wefor_residual_groups` are existing registered fields, so the
   instrument may already exist). **Filed here, not built.**
2. **THE SECONDARY SUCCESSOR — rating-point rather than mean anchoring** of the off-summer
   block (§6c). Deliberately not substituted for the pre-registered statistic mid-session.
3. **PJM / NYISO / NEISO carry the same unmeasured exposure.** All three arm
   `cc_nameplate_summer_derate`, so the unpublished "full nameplate off-summer" premise is
   live on their keepers — **and so is the headroom-vs-WEFOR composition measured here**.
   **No verdict transfers** (rule 25 `[R-ISO-SCOPE]` / 28 duty d); each lane must measure its
   own fleet. Recorded in the matrix note, and no other ISO's cell, shard, sidecar or bench
   file was written.
4. **Observed, not edited (rule 25):** the `cc_capacity_reconcile_path` row's **NYISO `K` is
   still stale** (that keeper carries the flag `False`), as FINDING-caiso185 §8 recorded.
   That cell belongs to the NYISO lane and was left untouched.

---

## 10. THE OWNER QUESTION — the CAISO in-model queue is EMPTY with every cell adjudicated

Per the charter, an eleventh lever is **not** invented. The named routes are **owner acts**:

* **(a) Fund the hourly pumped-storage water-state intake.** Walled input, no public source
  (`FINDING-caiso140` §B / caiso-141 A2); still C3a's first named contributor. *(Independently
  corroborated this session while answering a direct question on hydro: against measured
  EIA-930 `NG:WAT`, the keeper's hydro reproduces annual energy to 0.3–1.7 %, monthly totals
  at r = 0.994–1.000 and the mean diurnal profile at r = 0.964–0.981, but only r =
  0.785–0.805 hourly — and adding the model's own PS discharge back, which the CISO `NG:WAT`
  series contains and the model routes through the storage block, lifts that to r =
  0.877–0.894. Roughly half the apparent hydro decorrelation at CAISO is the missing PS
  seam, which is exactly what this intake buys.)*
* **(b) Rule on whether CAISO may be declared `CALIBRATED-WITH-CAVEATS` on a C3a ledger
  entry.** **Rubric v3.1 currently FORBIDS this** — since the owner amendment of 2026-08-06
  C3c is the *only* ledgerable criterion and C3a is load-bearing, so the fail-closed guard
  refuses it. Granting it would be a rubric amendment, not a session act.
* **(c) NEW, from this session:** authorise the **WEFOR-vs-overlay reconciliation** (§9 item
  1) as the next CAISO charter. It is a live double count on the sitting keeper, it is the
  gate on re-testing this basis, and unlike (a) it is **not data-blocked** — the fields exist
  and the evidence is on disk.

---

## 11. Known-open, carried forward

1. **C3a's residual: 2024 +10.5 %, 2025 +13.1 %** — unchanged; never read this session.
2. **The backcast CC WEFOR double count** (§9 item 1) — live on the sitting keeper.
3. **The rating-point anchoring variant** (§6c) — filed, not built.
4. **PJM / NYISO / NEISO's unmeasured exposure** (§9 item 3).
5. **The stale NYISO cell** on `cc_capacity_reconcile_path` (§9 item 4) — for the NYISO lane.
6. **Two pre-existing test failures at HEAD** carried over from caiso-184
   (`NuclearUnitAvailabilityTest::test_unknown_iso_degrades_to_empty` and its sibling) — not
   this charter's object, reported so they are not attributed here.

---

## 12. Governance

Rule 1 `[R-STRUCT]` — no mechanism judged by its effect on the fit; **C3a was never read**,
and the arm's pre-declared likely direction (price UP) was registered as admissible before
any measurement. Rule 11 — the defect found is root-caused in §6a and §9, not buried in a
capacity value. Rule 13 `[R-MEASURED]` — every input is an EIA-860 published rating,
forward-reproducible and responsive to a re-rating; the CEMS record entered **only** as a
check; no price residual or benchmark entered any input or any bar. Rule 14 `[R-ACCURATE]` —
the rule under test: accurate published data is preferred over an unpublished estimate, but
not when its application contradicts the measurement, and the root cause is opened (§9)
rather than the estimate re-blessed. Rule 15 / 16 — no run was completed, so none is
registered; no single-year bundle exists. Rule 19 `[R-ONE-MECH]` — the basis for the
refusal, and the instrument itself REPLACES a basis rather than stacking a second derate.
Rule 21 `[R-DOF]` — ledger 11 / 8, unchanged. Rule 22 `[R-HOLDOUT]` — **no year was solved
at all**; spend freeze respected; both markers untouched (owner acts); CAISO holds no
`complete`, so no determination re-key was owed. Rule 23 `[R-FROZEN-DERIVE]` — no derive
re-run, no data byte written; sha256 ledger recorded. Rule 24 `[R-REGISTRY]` — one
registered `ScenarioConfig` field, in `run_config.json`, cache-key-registered **in the same
commit**; no env knob, no hardcoded per-plant dict, no `getattr` fallback literal; partial
arming refused. Rule 25 `[R-ISO-SCOPE]` — CAISO only: no other ISO's extract, keeper shard,
registry sidecar, status part, bench file **or matrix cell** was written, and every ratio IS
that plant's own published rating, so no parameter crosses a boundary. Rule 26
`[R-DELETE]` — addressed explicitly in §8. Rule 27 `[R-PUSH]` — the pre-registration was
pushed and blob-verified before any measurement and before any code; every push verified by
commit-SHA round trip; no existing ≥300-line file rewritten from regenerated content (the
edits to large files are targeted inserts). Rule 28 `[R-MECH-MATRIX]` — duty (a) discharged
in §1, duty (b) in the matrix cell updated **this session** (a rejection, recorded as one),
duty (c) closed by the new `cc_winter_capability_basis` row added in the same PR as the
field; `check_mechanism_matrix.py` exits **0**.
