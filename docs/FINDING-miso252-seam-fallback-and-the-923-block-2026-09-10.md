# FINDING — miso-252: the pre-2023 seam fallback is a bang-bang switch, and every other queue item is externally blocked

```
SESSION       : miso-252
ISO           : MISO
HEAD          : 5fa3a07f196d263293bec74384df41a04ca68c29
KEEPER        : 2026-09-09-miso-250-ep-gas   (bundle results/calibration/miso_fuelvintage_A)
DETERMINATION : UNCHANGED — MISO stays CALIBRATED on the train tier
LP SPENT      : ZERO. No shard was launched, no solve was run, no bundle was written.
```

**Headline.** Phase 0 answered every question in the miso-252 queue without an LP, and the
answers eliminated every arm. The seam anomaly miso-251 flagged has a complete, measured root
cause — **pre-2023 all four MISO seam ladder tables are empty, so every seam band collapses onto
a single flat price and the seam stops being a supply curve at all** — but repairing it properly
is blocked on data the repo does not have. The one in-sample rubric blemish (MISO 2025 C1/C2) is
blocked on EIA, which I proved by measurement rather than inference. **No LP was warranted and
none was spent.**

---

## 1. What phase 0 settled, item by item

| # | queue item | status after phase 0 | blocker |
|---|---|---|---|
| 1 | the seam | **root cause found and quantified** (§2) | repair needs EIA-930 per-seam interchange for 2020–2022; repo has 2023–2025 only (§3) |
| 2 | 2025 C1/C2 blackout | **blocked on EIA — proven, not assumed** (§4) | EIA has not published a fuller 2025 survey |
| 3 | regime limit / coal supply | blocked, unchanged | no coal-stocks input in repo; data-intake lane |
| 4 | `MISO_PRICING_API_KEY` | blocked, unchanged | no key in this session |
| 5 | declared-degradation channel | **owner decision, unchanged** | §7 |

Rule 29 `[R-SCREEN]` step 0 is explicit that a zero-LP gate that kills an arm is the session's
result and the remaining spend is never made. That is what happened here, four times over.

---

## 2. THE SEAM — root cause, measured

### 2.1 The mechanism is absent before 2023, not merely degraded

The miso-252 charter described `miso_seam_neighbour_hourly_spp`'s table as *"a no-op for any year
absent here"*. That understates it. **All four MISO seam ladder tables cover exactly 2023, 2024
and 2025:**

| table | years |
|---|---|
| `MISO_SEAM_LADDER_BY_YEAR` | 2023, 2024, 2025 |
| `MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR` | 2023, 2024, 2025 |
| `MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR` | 2023, 2024, 2025 |
| `MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR` | 2023, 2024, 2025 |

`inject_miso_seam_ladder_prices` returns at its first guard (`if ladder is None: return False`)
for **every** pre-2023 year, so it is not the SPP sub-gate that degrades — the entire measured
ladder family never fires. Every seam band then takes the generic reference price.

### 2.2 What the fallback puts in its place

`neighbor_heat_rate` resolves in three tiers: measured `hr_by_year` → gas-elastic
`hr_phys + hr_adder/gas` → flat `marginal_heat_rate`. Pre-2023 MISO gets tiers 2 and 3:

| seam | 2020 | 2021 | 2022 | track |
|---|---:|---:|---:|---|
| PJM | $25.70 | $46.45 | $74.21 | gas-elastic |
| SPP | $22.45 | $28.16 | $35.78 | gas-elastic |
| South | $24.41 | $46.92 | $77.03 | **flat HR — no elastic fit exists** |

**One number per seam per year.** The measured ladder it replaces is an eight-band rising curve.
Forcing the fallback onto the three years whose measured answer we *do* have shows the size of the
substitution:

| seam | yr | fallback $ | measured ladder import mean $ | error |
|---|---:|---:|---:|---:|
| PJM | 2023 | 31.30 | 27.34 | **+3.96** |
| PJM | 2024 | 27.43 | 33.38 | **−5.95** |
| PJM | 2025 | 42.14 | 53.32 | **−11.18** |
| SPP | 2023 | 23.99 | 130.57 | **−106.57** |
| SPP | 2024 | 22.93 | 196.76 | **−173.84** |
| SPP | 2025 | 26.97 | 209.65 | **−182.68** |
| South | 2023 | 30.48 | 141.44 | **−110.96** |
| South | 2024 | 26.28 | 207.43 | **−181.15** |
| South | 2025 | 42.24 | 235.56 | **−193.31** |

PJM's fallback is defensible (±15–20 %): it has a real gas-elastic fit and a shallow ladder
(band 0 → band 7 spans $13→$47 in 2023). **SPP and South are under-priced by a factor of five to
eight**, because their ladders are steep (SPP 2023: $33→$205) and the fallback keeps only a level.

### 2.3 The consequence: the seam becomes a bang-bang switch

A flat price against a seam with no band curve makes the seam all-or-nothing each hour. Measured
directly from the committed sidecars — **hourly net seam flow, MW, `+` = import**:

| year | pricing | net TWh | mean MW | p25 | p50 | p75 | **hours at the rail** |
|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | measured ladder | +43.19 | 4,931 | 4,162 | 5,143 | 5,911 | **3** (0.0 %) |
| 2024 | measured ladder | +27.50 | 3,140 | 2,150 | 3,394 | 4,289 | **1** (0.0 %) |
| 2025 | measured ladder | +20.35 | 2,323 | 1,120 | 2,500 | 3,457 | **2** (0.0 %) |
| **2021** | **flat fallback** | **+75.93** | **8,667** | **8,700** | **8,700** | **8,700** | **8,654** (**98.8 %**) |
| **2022** | **flat fallback** | **−22.58** | −2,578 | −8,700 | −3,365 | +2,600 | 398 (4.5 %) |

*("At the rail" = within 1 % of that year's own maximum absolute flow.)*

**2021 is pinned at its import rail from p5 all the way to p100** — every quantile from the 5th up
reads exactly 8,700 MW. The seam sat at 99.6 % of its own maximum *as an annual average* and
imported in 8,757 of 8,760 hours. **2022 is pinned at the opposite rail**: p1–p25 all exactly
−8,700 MW (max export), p99–p100 at +8,700 (max import), median −3,365 — it slams between the two
rails with almost no interior clearing.

Under the measured ladder the same seam is at its rail in **3, 1 and 2 hours** of the year. That
is the whole finding in one comparison: **0.0 % vs 98.8 %.** The eight rising bands are what make
the seam modulate; the flat fallback deletes them and leaves a switch.

### 2.4 Why the ~98 TWh swing between adjacent holdout years

The flat fallback turns the seam's direction into a single threshold crossing against MISO's own
internal price:

| year | MISO model LW price | SPP | PJM | South |
|---|---:|---|---|---|
| 2021 | $37.69 | $28.16 → **import** | $46.45 → export | $46.92 → export |
| 2022 | $60.66 | $35.78 → **import** | $74.21 → export | $77.03 → export |

In 2021 MISO's price distribution sits low enough that the SPP import rail wins nearly every hour
and the export seams rarely bind; in 2022 the higher, more volatile price flips the balance to the
export rail. With no band curve on either side, the crossing is absolute rather than graduated,
which is exactly how a ~98 TWh swing appears between two adjacent years.

*Stated as a limit on this attribution:* the committed sidecars carry the `import` class as one
unbanded aggregate, so the **per-seam** split is inferred from the price crossing above, not
measured. Confirming it per seam would need a re-solve, which this session did not spend.

### 2.5 This CANNOT move MISO's headline — and that is a measurement, not a hope

The charter suggested the seam "touches an IN-SAMPLE gate." **Phase 0 falsifies that.** The
fallback is reachable in exactly one place — an armed-interface MISO backcast year before 2023:

- **2023–2025 (the train tier):** all four tables are populated and displace it entirely (§2.1).
  Independently confirmed by the in-sample row of §2.3 — the keeper's seam behaves as a curve.
- **MISO forecast:** `reference_price_interface` is `False` in the dataclass and MISO's `ISOConfig`
  carries **no override**, so a forecast run arms it only by explicit opt-in, which per capx S-123
  (2026-08-30) MISO forecast configs do not make.
- **Any solve year ≥ 2026:** no extract resolves a seam load shape, so the fallback cannot fire.

So the defect's entire blast radius is the three holdout rungs, and rule 30(c) `[R-TOUCHPOINT-FOLD]`
says a held-out year can neither certify nor decertify the ISO. **MISO stays CALIBRATED, and no
repair here would change that.** It is worth fixing on its own terms under rule 1 `[R-STRUCT]` —
not because a residual would move.

### 2.6 A correction owed to the codebase

`spec.py`'s capx S-123 note (2026-08-30) enumerates three domains where this fallback is
unreachable and concludes it *"never fires there either."* The enumeration is right about all
three and **misses the fourth** — the armed-interface pre-2023 backcast year, which is precisely
where miso-251 hit it. The comment is corrected in this session's commit; the conclusion it draws
about the `SOCO` `ba_code` re-point is untouched and still stands.

---

## 3. Why the seam repair is blocked, and what would unblock it

Two candidate repairs were evaluated at zero LP. **Both are refused on the evidence.**

**(a) Derive the ladder for 2020–2022 with the frozen script.** This would be the clean fix — same
`scripts/data/derive_miso_seam_ladders.py`, same construction, no new field, rule 23
`[R-FROZEN-DERIVE]`-clean. It is blocked on inputs:

| input | coverage | verdict |
|---|---|---|
| `eia-930-interchange/MISO interchange hourly.parquet` | **2023–2025** | **binding blocker** |
| `_validation-source/actual_lmp_hourly_MISO.parquet` (`da`) | 2022–2026 (2022 at 94 %) | available for 2022 |
| `_validation-source/pjm_border_lmp_hourly_MISO.parquet` | 2023–2025 | blocker for the PJM overlay |
| `_validation-source/actual_lmp_hourly_zonal_SPP.parquet` | 2023–2025 | blocker for the SPP overlay |

The flow-duration half of the Q-Q construction does not exist before 2023 for any seam — not even
for 2022, where MISO's own hub price *is* present. **The ladder is 2023–2025 by data availability,
not by choice.** Unblocking it is an EIA-930 DIBA interchange + hub-LMP intake for 2020–2022: a
data-intake lane with its own charter, the same class of blocker as queue items 3 and 4.

**(b) Freeze the band SHAPE and ride the gas-elastic LEVEL.** Tempting — it would regenerate
forward from gas and so pass rule 13's forward test. **It fails on measurement.** Normalising each
ladder to its own band 0 and taking the coefficient of variation across 2023–2025:

| seam · direction | max CV across bands |
|---|---:|
| PJM import | 0.19 |
| PJM export | 0.10 |
| **SPP import** | **0.33** |
| SPP export | 0.10 |
| **South import** | **0.32** |
| South export | 0.09 |
| **Manitoba import** | **0.49** |
| Manitoba export | 0.12 |

The export curves are stable, but exports are not the problem. **Every import curve — the side
that is broken — moves 32–49 % across just three years.** A shape frozen off three years that
disagree by half would be a fitted object dressed as a measured one, which rule 1 `[R-STRUCT]`
forbids reaching for however much it would improve a rung. **Refused, and recorded so the next
lane does not re-derive it.**

---

## 4. THE 2025 EIA-923 BLACKOUT IS BLOCKED ON EIA — measured, not assumed

The charter said *"CHECK FIRST — it may have landed."* It has not, and this is now settled by
direct comparison rather than by reading a release calendar.

`https://www.eia.gov/electricity/data/eia923/archive/xls/f923_2025.zip` exists (19,708,197 bytes,
`Last-Modified: Fri, 20 Feb 2026`) and contains exactly one workbook,
`EIA923_Schedules_2_3_4_5_M_12_2025_20FEB2026.xlsx`. Downloaded and compared against the repo's
committed vintage:

| | EIA's current file | repo on disk |
|---|---:|---:|
| Page-1 rows | 7,653 | 7,653 |
| unique plants | 3,427 | 3,427 |
| plant set identical | — | **True** (0 only-in-EIA, 0 only-in-disk) |

**The repo is already current with EIA's latest 2025 publication.** There is nothing to re-fetch
and nothing to re-score. The vintage is complete on *months* (all twelve, 5,419–5,719 plant-months
each) and incomplete on *plants* — 7,653 rows against 2024's 17,964, because this is the monthly
respondent frame and the small-plant tail only arrives with the final annual survey.

`scripts/audit_eia923_completeness.py --year 2025` was re-run at HEAD and still returns **2**
gate-eligible (ISO, class) pairs across all seven ISOs; MISO's eight C1 classes stay SKIPPED.
Its verdicts are correct — e.g. MISO `COAL_BIT` has all 18 plants reporting but only 92 % of
plant-months, and `CT_PEAKER` is missing 73 of 98 plants.

*One incidental note:* re-running the audit rewrites the shared cross-ISO artifact
`frontend/data/backcast/completeness/eia923_2025.json` with two marginal SPP-row shifts (COAL_BIT
prior 0.079 → 0.033 TWh on one fewer prior plant; COAL_PRB prior 56.793 → 56.838 TWh). **No
`status`, no `gate` and no determination moves in any ISO**, and the gate-eligible count stays 2.
The change was **reverted, not committed** — it is unrelated to this finding, and a MISO lane that
solved nothing should not push a cross-ISO generated file. Whichever lane next re-derives it on
purpose owns it.

**Do not relax this gate to make C1 score.** The gate exists to stop scoring a model class against
a half-reported actual, and the data really is half-reported. The fix is EIA's to publish. This
row affects CAISO, NEISO, NYISO, PJM and SPP identically, so it stays a cross-ISO win — for
whichever session runs after EIA's final 2025 annual lands.

---

## 5. What was NOT done, and why

- **No offer-curve tuning.** miso-251 declined it on evidence (C3a reads +4.9 / +1.8 / −6.2 %
  across the span — both directions, all PASS, no common mode to remove) and nothing in this
  session's measurements changes that. Reaching for it to move 2022 would be per-year fitting
  against a gate, which rule 1 carve-out (c) refuses.
- **No G-DRIFT audit.** Rule 29(b) owes one before *the first LP of an arm*. No arm survived phase
  0, so there is nothing to control-difference. It is owed by whichever session next solves.
- **No shards, no LP, no bundle.** Rule 32 `[R-SHARD]` (a) makes this session an orchestrator; it
  had nothing to orchestrate.
- **No dashboard registration.** Rule 15 `[R-DASHBOARD]` governs completed *runs*. This session
  produced none.
- **Nothing deleted.** Rule 31 `[R-RETAIN]`: the three miso-251 rung bundles
  (`miso251_tp2020`, `miso251_tp2021`, `miso251_screen2022`) are still on local disk and were read,
  not removed. §2.3's in-sample/out-of-sample contrast exists *because* they survived — a concrete
  dividend of that rule.

---

## 6. Mechanism matrix

No cell verdict moves. `seam_neighbour_hourly_ladder` and `seam_neighbour_anchored_ladder` stay
**K** — this session tested no mechanism with an LP. The MISO shard is annotated with (i) the
reachability boundary of §2.5 and (ii) the rejected shape-freeze candidate of §3(b), so neither is
re-derived.

---

## 6b. Two PRE-EXISTING failures at HEAD, found in passing — neither is this lane's to fix

Both reproduce on the parent commit `5fa3a07f` with none of this session's changes applied, and
both are reported rather than touched.

1. **`scripts/check_mechanism_matrix.py` FAILS on the SPP shard** — *"missing cell(s) for 2
   mechanism(s): `nyiso_hub_gap_month_level`, `spp_curtailment_ceiling`"*. This is the rule 33
   `[R-MECH-MATRIX]` duty (c) obligation (a new base row needs a cell line in **every** shard)
   left unmet by whichever lane added those rows. Rule 33 also says a lane edits **only its own
   ISO's shard**, so a MISO session must not repair SPP's. It is a **CI-red at HEAD** and belongs
   to the SPP lane.
2. **`tests/unit/config/test_miso175_seam_hour_ending_key.py` carries a stale cache-key pin** —
   it asserts `547053bdfccd4264` and gets `0a1e2b02da5d709b`. Verified not to be this session's
   doing by direct comparison: the default `ScenarioConfig().cache_key()` is **`3a296bf0fe938f68`
   on the parent commit and `3a296bf0fe938f68` on this one — identical**. That is expected, since
   the capx D79 solve-surface fingerprint is a *value* hash over seven registry modules and
   `model/interchange/spec.py` is not one of them, so a comment edit there cannot move a key. The
   pin needs re-baselining by whichever change actually moved it.

---

## 7. Open for the owner

1. **The seam repair (§3).** It needs an EIA-930 DIBA interchange + hub-LMP intake for 2020–2022.
   Worth chartering as a data lane, or leave the pre-2023 rungs documented as running an unpriced
   seam? My recommendation: **charter it**, because the same intake also unblocks queue item 4 and
   would let all three rungs be re-scored on a real seam.
2. **The `--declared-degradation` channel** — `docs/GOVERNANCE-NOTE-miso251-declared-degradation-channel-2026-09-10.md` §5,
   unchanged and still awaiting a ruling. Refusing it leaves MISO's pre-2023 rungs permanently C6
   UNATTESTED on governance alone.
3. **`MISO_PRICING_API_KEY`** — still the single thing that unblocks C3a/C3b/C3c on 2020 and 2021.

**Nothing on local disk needs a promotion decision** (rule 31): this session solved nothing.
