# PRE-REGISTRATION — nyiso-189 (`backcast-calibration` lane): the eGRID GEN-sheet steam-generator collapse census over EVERY NYISO combined cycle (Step 0 of the Bethlehem 2539 object), and the owner decision it feeds — NO SOLVE THIS SESSION unless the owner picks a form

**Session:** nyiso-189, NYISO backcast-calibration track, 2026-09-04.
**Branch:** `claude/nyiso-189-bethlehem-vintage-census`, fresh off `origin/main`
at `a35c9f9b` (carries PR #4717, the nyiso-188 keeper promotion, and #4720).
**Keeper at entry:** `2026-09-04-nyiso-188-combined`
(`results/calibration/nyiso188_combined`) — **CALIBRATED**, grade 7, fails 0,
C3c ledgered; C3a +7.9 / +3.8 / −6.9 %; C1-2024 `CC_REGULAR` +2.05 TWh PASS.
NYISO holds neither `complete` nor `final`; freeze ACTIVE; no marker requested.

**THIS DOCUMENT IS COMMITTED AND PUSHED TO `origin` BEFORE THE CENSUS IS
RUN.** No per-plant number beyond Bethlehem's (already published in
FINDING-nyiso188 §4) exists at the time of writing; no solve of this session's
making exists, and none will unless the owner selects a form (§4).

---

## §0 — DISCLOSURE

This session runs in the SAME container and model context as nyiso-188 and
holds everything nyiso-188 measured, including Bethlehem 2539's seven-vintage
decomposition (FINDING-nyiso188 §4.1: steam generator GEN 8 net generation
0.49–0.52 of CT output in 2018–2022 → 0.065 in 2023 → 0.000 in 2024; heat per
CT-MWh 10.26–10.44 every vintage but 2022; block HR at the plant's own steam
share 6.88–7.01) and its adjudication (§4.2: no threshold-free source-internal
identity reaches the applied 2023 vintage). Read: FINDING-nyiso188 §4 / §5.2,
PREREG-nyiso188 §3 (the Object-3 admissibility rule, carried verbatim into §4
below), matrix §5.5 (nyiso-188 queue), the NYISO shard cells
`egrid_identity_heat_rates`, `cc_capacity_reconcile`, `scuc_load_pocket_commitment`.
**Not read:** any other NYISO CC's GEN-sheet rows.

## §1 — THE OBJECT

Whether Bethlehem's filing artifact is a population property or a single
plant's — the census the nyiso-188 hand-forward required BEFORE any form is
built (rule 24: a population rule, never a carve). Output: one row per (NYISO
CC plant with a filed CA generator, eGRID vintage 2018–2024) and one summary
row per plant, committed under `results/calibration/_nyiso189_gen_collapse_census/`.

## §2 — RULE 19: what already prices these plants

The fleet's base heat rate is eGRID 2023 `PLHTRT` for every plant
(`process_eia860.py::_join_egrid_heat_rate`); `egrid_identity_heat_rates` (K)
reaches only CAMPD-less plants, `egrid_family_heat_rates` (K) only
multi-family plants, `_egrid_boundary_hr_repairs` only PLHTRT > 11.5 with a
co-located sibling. No armed mechanism reads the GEN sheet's per-generator
split. Either form in §4 would be ONE new field replacing the base rate for
the plants its test admits — nothing stacks.

## §3 — MEASUREMENT (no LP; eGRID GEN / PLNT sheets, seven vintages), fixed now

Population: every EIA plant the NYISO fleet carries a `CC_REGULAR` or `CC_CHP`
generator for AND eGRID files at least one `PRMVR == CA` generator for
(single-shaft `CS` units and plants with no filed steam generator are outside
the object and listed as excluded).

* **T1 — the zero test (threshold-free):** an operating CA generator reports
  `GENNTAN == 0` in a vintage whose CT generators report `GENNTAN > 0`.
  Reported per plant-vintage; the plant's `T1_fires_in` list is the finding.
* **T2 — the steam-share record:** `ST/CT = Σ GENNTAN(CA) / Σ GENNTAN(CT)` per
  vintage; per plant the min / max across vintages and the median over the
  T1-clean vintages. REPORTED, never thresholded.
* **T3 — the CT-heat identity:** `PLHTIAN / Σ GENNTAN(CT)` per vintage (the
  heat per CT-generator MWh); its per-plant min / max is the invariance
  record.
* **T4 — the applied-vintage rate:** the fleet's applied heat rate vs (a) the
  2023 block HR at the plant's own T1-clean median share, (b) the 2023 block
  HR at the EIA-860 nameplate share `NAMEPCAP(CA) / NAMEPCAP(CT)`.

**What the census DECIDES (fixed now):** nothing about a repair. It reports
(i) how many plants T1 fires at and in which vintages; (ii) for every plant,
the T2 / T3 records; (iii) the T4 gap at every plant. **No bar, no verdict,
no lever** — it is the population fact the owner's decision needs.

## §4 — THE OWNER DECISION (verbatim from FINDING-nyiso188 §4.2 / §5.2; nothing is built until one is chosen)

Admissibility rule (PREREG-nyiso188 §3, unchanged): a repair is built only if
it is (a) zero-parameter and threshold-free, (b) source-internal, (c)
regenerating per vintage, and (d) reaches the applied 2023 vintage.

* **Form A — pooled-vintage eGRID basis:** the identity derive's own rule
  (ΣPLHTIAN / ΣPLNGENAN over ALL vintages, LOYO recorded) applied to every
  CAMPD-covered plant as a registered mechanism. Satisfies (a)–(d) in FORM;
  at 2539 it yields 7.85 (LOYO [7.51, 8.05]), knowingly contaminated by the
  two artifact vintages; it is a fleet-wide basis change, A/B'd as one.
* **Form B — the CT-heat identity with a cited steam share:**
  `PLHTIAN / Σ GENNTAN(CT) / (1 + ST/CT)` for the plants T1 admits, with the
  share either the EIA-860 nameplate ratio (a published field; 2539: 0.532 →
  6.72) or the plant's own T1-clean median (a measured record; 2539: 0.49 →
  6.91). Reaches the physical block; needs the owner to authorize the bound
  and to say which share, and needs T1 (or a rule the census motivates) to
  say which plants it reaches — the 2023 vintage at Bethlehem is NOT reached
  by T1 (CA = 267,718 MWh, not zero), which is the open point.

Either form: one `ScenarioConfig` field with a matrix row (rule 28c), its own
PREREG with bars before any solve, control = same-HEAD replay on the
committed artifacts (the nyiso-188 chain), verdict rule REJECTED iff
C2 / C3a / C3b / C8 flips PASS → FAIL.

## §5 — FORBIDDEN / STOP

F1 no solve this session without the owner's written choice of form; F2 no
per-plant dict, no threshold introduced by the census (T1 is a zero test; T2 /
T3 / T4 are records); F3 no re-opening of the 2024 `CC_REGULAR` disposition,
C3a-2025 (Q1), or Zeltmann's pooled cap; F4 no CAISO edits; F5 2023–2025
only, no marker requested. S1 the census is committed whatever it shows.
