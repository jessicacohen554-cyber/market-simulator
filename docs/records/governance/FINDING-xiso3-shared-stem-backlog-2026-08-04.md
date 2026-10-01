# FINDING — xiso-3: the CROSS-ISO SHARED-STEM backlog is CLOSED

**Date:** 2026-08-04 · **Session:** xiso-3 (cross-ISO lane) · **Branch:**
`claude/xiso-3-shared-stem-e4y67p`
**Pre-registration:** `PREREG-xiso3-shared-stem-backlog-2026-08-04.md` — committed and pushed
**before** any row was written, any anchor repaired, or the probe run.

**Zero solves. Zero years touched. No `ScenarioConfig` value, constant or derive script
changed. No keeper, gate or determination changed in any ISO. NO CELL MINTED ANYWHERE.**

---

## §1 — headline

**The last rule-28(c) debt is discharged.** All **45 distinct SHARED (non-ISO-prefixed)
fields** — **54 (ISO, field) pairs**, nine armed in two ISOs at once — that a designated
keeper **ARMS with no matrix cell anywhere** are registered as **literal sub-scalar entries
on 19 EXISTING rows' defs**.

| metric | before | after |
|---|---|---|
| shared-gap, CAISO / ERCOT / MISO / PJM | 5 / 14 / 17 / 18 | **0 / 0 / 0 / 0** |
| shared-gap, NEISO / NYISO | 0 / 0 | 0 / 0 |
| every ISO's family absent / prose-only / armed-no-cell | 0 / 0 / 0 | 0 / 0 / 0 |
| matrix rows | 169 | **169** (zero new) |
| ratchet `shared_armed_on_keeper` | 54 entries | **empty, all six** |
| matrix line anchors that resolve | **4 of 167** | **167 of 167** |

With every ISO's own-family column already closed (ercot-156, caiso-161, pjm-151,
neiso-78, nyiso-113, nyiso-121), **both halves of the rule-28(c) census are now at zero.**

## §2 — the registrations: 45 fields, 19 rows, zero new rows

Every home is chosen on a **cited code read site**, never on theme, and the citation is in
the registration text. Full pre-declared mapping: PREREG §2 (unchanged — no home moved).

| home row | fields | the dependency |
|---|---|---|
| `coal_passthrough_sigmoids` | 8 | `trajectories.py::coal_passthrough_series` → `coal_sigmoid_params` |
| `offer_curve_by_group` | 5 | `offer_curves.py::_offer_curve_for_group`; `assembly.py` ramp shape |
| `netload_drag_floors` | 7 | `floors.py::apply_ct_/apply_gas_st_netload_drag_floor` |
| `temp_dependent_derate` | 5 | `arrays.py::_availability_matrix` |
| `wefor_statistical_stack` | 3 | `arrays.py` WEFOR stack |
| `coal_mustrun_per_plant` | 2 | `campd_bins.py` / `assembly.py` min-load band |
| `p1_bidcost_pass` | 2 | `commitment.py::compute_monthly_markup` class gates |
| `chp_steam_following` | 2 | `assembly.py` steam `pmin_cf` |
| `campd_outage_windows` | 1 | `arrays.py::_apply_outage_overlays` |
| `unit_outage_short_windows` | 1 | `arrays.py` — "the third window shape" |
| `st_gas_mustrun_p25` · `gas_plant_monthly_pricing` · `coal_takeorpay_committed` | 3 | level swap / donor pool / take-or-pay share |
| `cc_nameplate_summer_derate` · `use_campd_bins` · `plant_level_fleet` | 3 | `_availability_matrix` / `bins_to_fleet` / `eia860.py` |
| `gas_daily_shape` · `storage_measured_anchors` · `tranche_startup_amortization` | 3 | `gas_seasonal_shape` / `reserves/spec.py` / `run_ratio_t` |

## §3 — mechanical cause: the caiso-161 §2 abbreviation defect, three more times

**Seven registrations already existed but only as ABBREVIATIONS no literal-matching
checker could resolve.** A human reads them as coverage; the census cannot:

* a bare **`etc.`** on `wefor_statistical_stack`, standing in for **three armed fields at once**;
* **`(+seasonal)`**, **`p25 level`**, **`class_aware`**, **`_from_data`**;
* **`conditional runs`** — the field name written with a space instead of an underscore;
* **`outage_source=historic :7709`**, whose anchored token `historic` is not a field at all.

This is the same defect that hid four armed `caiso_ra_bridge_*` fields until caiso-161, the
`pjm_seam_*` glob until pjm-151, and `miso_pjm_lmp` until nyiso-121. **It is now the single
most common cause of matrix invisibility on the record, and it is mechanically detectable —
which is what §5's checker turns into a standing gate.**

## §4 — O-1: SEVEN armed-looking pairs are PROVABLY UNREADABLE on their own keeper

Pre-registered in PREREG §7 with PASS / FAIL / UNINFORMATIVE and a **mandatory positive
control**, all specified before the probe ran. **Written on CONSTRUCTION, not on a solved
dual** (the nyiso-115 G2 / nyiso-118 lesson; the nyiso-121 G-1 pattern). **No LP, no solve,
no dual.** Built twice at one HEAD, `np.array_equal` on float32 — **exact equality, not a
tolerance**.

| ISO | field(s) | keeper value | gate (at keeper) | Δ | control Δ |
|---|---|---|---|---|---|
| ERCOT | `coal_prb_passthrough_floor` | 0.76 | `coal_prb_passthrough_sigmoid=False` | **0.0** | 0.662 |
| ERCOT | `coal_lignite_passthrough_floor` | 0.675 | `coal_lignite_passthrough_sigmoid=False` | **0.0** | 0.583 |
| ERCOT | `coal_lignite_passthrough_ceil` | 1.0 | `coal_lignite_passthrough_sigmoid=False` | **0.0** | 0.744 |
| ERCOT | `coal_prb_follower_floor` | 0.76 | `sigmoid AND tiered` (first conjunct False) | **0.0** | 0.662 |
| CAISO | `ct_drag_slope_per_gw` / `_intercept` / `_cap` | 0.00901 / −0.1124 / 0.36 | `ct_netload_drag=False` | **0.0** | 80.1 MW |

**O-1 PASS.** Every arm is exactly equal; **every one of the five positive controls
separates**, so the silence is the mechanism's and not the instrument's. Those two
`run_config.json` files **overstate what the solve read** — the caiso-161 §5 / pjm-151 /
nyiso-121 G-1 shape, now measured in a third and fourth ISO.

**The CAISO result is CONSISTENT with this file's existing CAISO `R` for that family**, not
in tension with it: the mechanism was rejected and the derived coefficients are residue.

**Both are filed, neither adjudicated.** Whether an inert fitted scalar is cosmetic, a
rule-19 `[R-ONE-MECH]` question or a rule-26 `[R-DELETE]` candidate belongs to a lane that
may adjudicate that ISO. **A census may not** (rule 28(d)). **No cell moved.**

### §4.1 — the mandatory positive control caught TWO defects in this session's OWN instrument

Recorded because it is the argument for the control being mandatory rather than advisory.

1. The **first** version used one pooled control over all four ERCOT fields. It separated —
   but only because the prb and lignite floors moved. It **never exercised
   `coal_prb_follower_floor`'s read path at all**, so that field's "silence" would have
   been an artifact.
2. The **per-field** rewrite then reported the `coal_prb_passthrough_floor` control as
   **VOID**. Cause: the probe's emulation of `assembly.py`'s tiered branch **overwrote** the
   baseload prb entry, while the real code keeps **both** maps and routes only low-must-run
   plants to the follower. The instrument was blind to the very field it was testing.

Both were caught by the control, not by inspection. The committed probe keeps the two
cohorts as separate keys and every field now has its own separating control.

## §5 — the line-anchor decay, measured, repaired and now GATED (TASK 1b)

nyiso-121 found **all 20 MISO anchors stale** and filed a standing checker as a suggestion.
**Measured file-wide here, the decay is near-total:**

| anchor form | total | resolved | **stale** |
|---|---|---|---|
| `<field> :<line>` | 152 | **4** | **120** |
| row-`id` `scenarios.py:<line>` | 43 | **0** | **43** |
| `<path>.py:<line>` in range | 99 | 99 | 0 |

**163 stale, 4 correct.** Most are off by 900–1,400 lines because `scenarios.py` grew under
them; several by exactly 10, the authoring-vs-merge drift nyiso-121 recorded. **161 were
repaired mechanically** (163 findings, two duplicate keys), verified **digits-only**: with
every `:\d+` normalised, before and after are byte-identical.

`scripts/check_mechanism_matrix.py` now carries a standing anchor leg — three checks
(field-style, row-id, file-in-range), a **shrink-only ratchet**
(`mechanism-matrix-anchors.json`, **currently empty**), and a **`--fix-anchors`** repair
path so compliance is one command rather than a tax on every `scenarios.py` PR. **Existence
is gated first**, which preserves the deliberate `miso_pjm_lmp :2914` defect **quotation**
in `import_hub_pricing`'s repair note (verified still present, 3 occurrences).

The check is what **verified this session's own 54 registrations**: field anchors checked
rose 124 → 178 and all resolve.

## §6 — a pre-registered criterion FIRED, and is recorded rather than redefined

PREREG §9 criterion 6 — the nyiso-121 §6.2 guard restated for the lane it was filed for:
*every field leaving a live-but-invisible list must be one of the 45, registered ON A ROW.*

**It fired.** ERCOT's list lost **`coal_lignite_passthrough_sigmoid`**, which is **not one
of the 45**.

**Measured, not argued.** An audit of **every** field newly mentioned by this session's
edits — 24 of them — finds **all 24 are `own_row` `def:` registrations** and **zero
prose-only mentions were introduced**. The departure is one of **seven companion fields**
(gates, thresholds and siblings of the registered scalars: the two rank sigmoid gates,
`coal_prb_passthrough_tiered`'s follower threshold, two intermediate-split CF thresholds,
`offer_curve_smoothing_exp`, `coal_committed_takeorpay_sunk_fixed`, `ct_drag_ramp_start`)
that the registrations name **in a def** because naming a scalar while hiding its own gate
would be the very abbreviation defect §3 documents.

**So the criterion's GUARD holds — no prose leak occurred — and its WORDING was too
narrow.** The corrected form, stated here rather than applied silently: *every departure
must be a `def:` registration on the row whose code owns it, pre-declared or not, and any
non-pre-declared departure must be itemized.* It now is, in this section and in the row.

**Every other ISO's counts are byte-unchanged**: CAISO invisible 1 → 1, NEISO / NYISO / PJM
0 → 0, and no ISO gained an entry in any list.

## §7 — verification against the seven pre-registered criteria

| # | criterion | result |
|---|---|---|
| 1 | shared-gap 0 for all six; ratchet empty | **PASS** — 5/14/17/18 → 0, all six empty |
| 2 | family counts stay 0/0/0; 169 → 169 rows | **PASS** — zero new rows, row ids identical |
| 3 | every `cells:` string byte-identical to main | **PASS** — all 169, no mint anywhere |
| 4 | checker passes incl. the anchor leg; ratchet empty | **PASS** — 0 unresolvable of 320 checked |
| 5 | anchor repair is digits-only | **PASS** — normalised texts byte-identical |
| 6 | invisible only shrinks, every departure registered on a row | **FIRED, §6** — guard holds, wording corrected, departures itemized |
| 7 | O-1 reported with its positive control | **PASS** — §4, 5 arms, 5 separating controls |

**Kills:** K-1 (zero cell changes anywhere) **holds** · K-2 (zero verdicts, zero transcribed
adjudications) **holds** — every sentence added is either a description sourced to the
field's own committed comment or a construction fact labelled as an observation · K-3 (no
solve, no re-derivation, no tuning) **holds** · K-4 (digits-only) **holds** · K-5 (no bare
literal enumeration in prose) **holds**, verified at 24/24.

**Rule 27 `[R-PUSH]`:** `mechanism-matrix.js` is **2,017 lines**; every push was edited
locally with the Edit tool, pushed as exact on-disk bytes, and the pushed blob verified
byte-identical (line count + sha256) before the next commit.

**Rule 22:** the holdout spend freeze is **ACTIVE and untouched** — no year outside
2023–2025 was solved, scored or read, and no year was solved at all.

## §8 — what this session did NOT do

* **No mechanism was tested, chartered or queued in any ISO**; no lever queue was touched;
  no cell verdict was minted. **NEISO's `matrix_gap_census` `O` is untouched** — minting it
  is NEISO's lane's call.
* **No ISO's own-family column was re-opened** (rule 28(a)). MISO's two
  filed-not-adjudicated observations stay the MISO lane's.
* **One declared cell mismatch was left unresolved on purpose:**
  `coal_nameplate_summer_derate` is **ARMED on the ERCOT keeper** while its only code-level
  home row (`cc_nameplate_summer_derate`) reads ERCOT **`U`** — correctly, since that row's
  own CC flag is `False` there. Resolving it would be minting a verdict. **Filed for the
  ERCOT lane**, which may decide whether the family warrants two rows or one re-scored cell.

## §9 — what the next lane inherits

**Both halves of the rule-28(c) census now read zero, and both are ratcheted.** What is
left is not a backlog but three **filed, un-adjudicated** items, each belonging to a lane
that may adjudicate its own ISO:

1. **ERCOT** — four coal passthrough scalars provably unreadable on the keeper (§4), plus
   the `coal_nameplate_summer_derate` cell mismatch (§8).
2. **CAISO** — three CT drag coefficients provably unreadable, consistent with the family's
   existing `R` (§4).
3. **NEISO** — its `matrix_gap_census` audit cell is still `O`; its own-family sweep reads
   20/0/0/0 and its column was closed at neiso-78, so the mint is available to that lane.

**The standing risk this session removed is anchor decay, and the guard is now
mechanical** — but note what the ratchet does NOT do: it cannot tell a *correct* literal
from a *wrong* one. The checker proves an anchor points at the field it names; **only a
human can tell whether that field is the right one to name.** The literal name remains the
durable identifier.

---

## §10 — AMENDMENT (same day, after the first merge): the anchor gate needed a blame split

**Recorded rather than quietly rewritten**, and it is a correction to §5's design, not to
its measurement.

**What happened.** §5 shipped the anchor check with a hard `--base` failure and an empty
ratchet. Within the same day, main merged further lanes that inserted fields into
`scenarios.py` — and **214 anchors re-staled**, all of them below the insertion points.
Nothing in the matrix was touched; the anchors decayed exactly as §5 says they do. Had the
next lane opened a PR, **the gate would have failed it for drift it did not cause.**

**Why the ratchet alone could not fix this.** The ratchet answers *"is this anchor already
known-bad?"*, which is the right question for a backlog and the wrong one for decay: a
freshly repaired file has an empty baseline by construction, so the very next
`scenarios.py` insertion produces hundreds of un-baselined findings at once.

**The fix, which is the file's own existing precedent.** Under `--base` the check now
computes findings at the BASE as well as at HEAD and splits by blame — the same rule
`keeper_drift` already uses two blocks below it:

* an anchor stale at HEAD but **not** at the base → **this PR staled it → FAIL**;
* an anchor stale at **both** → **pre-existing → WARN**, and it belongs to whoever last
  moved `scenarios.py`.

Verified in all three directions: clean tree exits 0; a PR that breaks one anchor exits 1
with an `::error`; a tree carrying the base's own 221 stale anchors exits **0** with 221
`pre-existing` warnings and zero errors.

**The general lesson, and it generalises past this checker.** A gate keyed on **absolute
line numbers in a file every lane edits** cannot be a hard gate on inherited state — it
would go red constantly, and *a gate that gets disabled protects nothing*. The durable
identifier is still the field NAME; the anchor is a convenience, now repaired by one
command (`--fix-anchors`) and enforced only against the PR that actually broke it.
