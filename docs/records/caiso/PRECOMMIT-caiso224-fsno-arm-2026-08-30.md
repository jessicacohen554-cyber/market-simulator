# PRECOMMIT — caiso-224: the FSNO sub-zonal partition ARM ROUND (caiso-222 Q2 route (iii), solve round) — method, adjudication, invocations, gates and falsifiers fixed ex ante (2026-08-30)

**Charter.** The owner opened this session with *"Assess CAISO backcast status
and launch a new run for the next step(s)"* (2026-08-30, session
`claude/caiso-backcast-next-run-5u7ob7`). The standing record is unambiguous
about what the next step is: the caiso-222 §9 owner rulings chartered route
(iii), its zero-solve opening round landed as caiso-223, and
`FINDING-caiso223-subzonal-scope-2026-08-30.md` §D(d) names the next round —
the limit-side rule-13/14 adjudication with its own precommit, the
topology/config implementation, and the full-span rule-16 solves — as "a NEW
owner-visible charter, not requested here". This session reads the owner's
launch instruction as that charter and states the interpretation openly: if
the owner intended something narrower, every deliverable here is still a
registered probe pair plus reversible default-off code, and promotion remains
a separate owner act in any case. **Nothing here touches the keeper, the
markers, the freeze, the rubric, or any out-of-training year.**

## §1 — The delta under test (ONE mechanism, rule 19 [R-ONE-MECH])

A single gated `ScenarioConfig` field, **`caiso_fsno_subzonal_topology`**
(bool, default **False**, CAISO-only per rule 25 [R-ISO-SCOPE]), arming the
caiso-223 §A partition P-A′ verbatim:

* **Zones**: new **FSNO** (San Joaquin Valley pocket) carved from NP15 —
  7 zones, 6 load-carrying. Load shares re-cut by the caiso-223 §C measured
  3-way LDF split of the PG&E TAC share (0.4615 × {NP15 0.752614, FSNO
  0.132592, ZP26 0.114794} → **NP15 0.347332 / FSNO 0.061191 / ZP26
  0.052977**); SP15-side and WECC shares untouched; sum stays 1.0.
* **Links**: the NP15↔ZP26 5,400 MW Path-15 link is REMOVED (Los Banos–Gates
  + Panoche–Gates become FSNO-internal spine, per the DMM record in which they
  are not top binders); new **NP15↔FSNO ttc = 1,940 MW** (Tesla–Los Banos #1
  1,600 + Moss Landing–Las Aguilas 340) and **FSNO↔ZP26 ttc = 2,500 MW**
  (Gates–Midway #1). ZP26↔SP15_rest stays 4,000 (existing boundary, out of
  scope — isolates the FSNO delta). WECC links and the simultaneous-import
  interface limit unchanged.
* **Fleet**: the caiso-223 membership recut applied verbatim as data — the
  committed `_caiso223_membership_recut.csv` subzone column promoted to
  `data/raw/reference/caiso-fsno-subzone-membership.csv` (rows with subzone ∈
  {FSNO, NP15, ZP26}; SP15_side rows are hub-unchanged by construction) and
  consumed by the `zone_assignment` CAISO first-check when armed; unjoined
  plants whose eGRID county ∈ {Fresno, Kings, Madera, Merced} and whose
  geographic zone is NP15/ZP26 re-cut to FSNO (the caiso-223 county tier —
  Helms PS lands in FSNO). Zero silent defaults; zero free parameters.
* **Hourly load shapes**: the measured PG&E TAC hourly share is re-split by
  exact scalar rescale (share_z(h) = PGE(h) × w′_z; the three rows replace the
  two and the column sums are preserved bit-exactly) — no new hourly series
  exists or is invented, matching the 2-way construction's own documentation.

## §2 — Rule-13 admissibility of the DMM 2023 element scalars as link limits

The caiso-222/223 records deliberately left this UNADJUDICATED; this precommit
performs it. The test ([R-MEASURED]): *could the quantity be produced for a
forward year from forward drivers, and would it respond to changed
conditions?*

**PASS, as follows.** The object class is a transmission element operating
limit — the same input class as the WECC Path Rating Catalog statics already
seeding every CAISO link (Path 15 5,400 / Path 26 4,000 / COI 4,800 / WOR
10,623) and the published MIC seam limits the keeper arms. A rating
regenerates for a forward year (published rating records persist; an upgrade
changes the rating, not a residual) and responds to changed conditions. The
DMM 2023-annual *average binding limit* is a measurement OF the limit in
effect (the constraint RHS), not of any dispatch outcome: no value is chosen
from exceedance curves, split counts, binding-hour records, or any residual —
the caiso-218 §F fence-2 object is untouched, and fence-3's own text admits
exactly this class ("year-varying and element-grounded … **or sub-zonal**").

**Rule-14 misalignment, documented (the three unwaivable qualifications
carried, not waived):**

* *(a) single vintage* — 2023-annual only; 2024/2025 carry the 2023 scalars.
  This is the same static treatment as the WECC catalog values already in the
  topology; the caiso-218 §C insufficiency risk it creates is falsifier **F2**.
* *(b) parallel unrated elements* — each boundary cap counts only its
  DMM-rated elements (NP15↔FSNO omits unrated parallel feeds; FSNO↔ZP26 omits
  Diablo–Gates, Cal Flat–Gates and the Gates TBs). The caps are therefore a
  **lower-bound reconciliation** of each boundary's capability, per rule 14's
  parallel-path clause; the over-trapping this can cause is falsifier **F1**.
* *(c)* the caiso-218/219 fences wall these scalars as single-cut intake; this
  round uses them ONLY on the sub-zonal partition, the branch the fence
  explicitly leaves open. The caiso-222 §8.2 watch tests remain the only
  sanctioned wall re-checks; W-2/W-3 remain the upgrade feeds.

No directional split is published for these elements, so the caps enter
symmetric; the old Path-15 directional pair (3265/5400), keyed on the removed
("NP15","ZP26") link, is intentionally superseded by the chain's tighter
symmetric caps — both directions tighten, and this is part of the declared
delta, not a silent drop.

## §3 — Implementation contract (default path byte-identical; control proves it)

* Gate: a process-wide topology-variant context
  (`market_sim/config/topology_variant.py`) set ONCE per solve from the
  ScenarioConfig field at both lanes' existing config seams (the
  `set_eia860_vintage` pattern), consumed by `get_iso_config` (partition
  transform + `validate_topology`) and the `zone_assignment` carve (cache key
  extended). This makes every `get_iso_config` caller see the same topology —
  the transform-time alternative would give the LP 7 zones while
  renewables/hydro/storage build 6 (the recon-mapped silent-inconsistency
  hazard).
* Registration: `_CACHE_KEY_OPTIONAL_FIELDS` + defaults ledger + `TIER_TAGS`
  in the same commit; mechanism-matrix base row + a cell line in every ISO
  shard in the same PR (rule 28c).
* **Pre-registered inheritance rules (zero new tunables):** wherever an armed
  CAISO mechanism is zone-keyed and has no FSNO entry, FSNO inherits its
  parent NP15's value: the zonal gas basis (FSNO is PG&E citygate territory)
  and the zonal loss surface (no TH_FSNO exists to derive one). The AS_NP26
  region gains FSNO (it is north of Path 26 by construction). The LCT
  "Greater Fresno" LCR row stays pointed at ZP26 — inert in backcast (only
  the MIC seam half of `capacity_deliverability_limits` fires) and recorded
  as a sharpener. Renewable/solar shapes, hydro budgets, storage fleets and
  PS physics all follow plant membership automatically and need no new data.
* Everything is inert when the flag is off; the control solve (§4) is the
  proof, held to the caiso-200 tolerance discipline.

## §4 — Invocations, pre-registered (sequential — 15 GB box, CAISO 2025 is single-solve-only)

```
A (control, HEAD reproduction + inertness proof):
python3 scripts/run_calibration_full.py \
  --replay-bundle results/calibration/caiso220_c1_crosswalk \
  --out-dir results/calibration/caiso224_a0_control \
  --note "caiso-224 A0: caiso-220 keeper recipe replayed at HEAD with the gated FSNO partition IN TREE and OFF - bit-zero control"

B (arm, the single delta):
python3 scripts/replay_keeper.py results/calibration/caiso220_c1_crosswalk \
  --out-dir results/calibration/caiso224_b1_fsno \
  --set caiso_fsno_subzonal_topology=true \
  --note "caiso-224 B1: P-A' FSNO partition armed - caiso-223 measured membership/load split, DMM 2023 element caps 1940/2500"
```

Years 2023–2025 in one bundle each (rule 16); `legitimacy_diagnostics.json`
generated for both; per-year `hourly/` sidecars committed as each year lands
(container-death insurance). **G-CTRL**: the comparator probe
(`scripts/probes/_caiso224_ctrl_tolerance.py`, the `_caiso200_ctrl_tolerance`
construction verbatim) compares A0 vs the committed
`caiso220_c1_crosswalk/hourly/*` sidecars; bit-zero expected; if non-zero,
per-column maxima are quoted at full precision and projected onto |ΔC3a| ≤
0.1 pp / |ΔC3b| ≤ 0.005 per year BEFORE any arm result is read; outside
tolerance ⇒ **STOP-THE-LINE, no arm is read** (an arm already solved is
quarantined unread), and the finding is about the head, not the mechanism.

## §5 — Pre-registered outcomes, gates and falsifiers

* **Primary (structural, not a residual target):** the caiso-220 split
  witness re-measured on the arm — north↔south separation hours (>$15) and
  the NEW pocket-boundary separation (FSNO vs NP15, FSNO vs ZP26) vs
  reality's 1310/1691/1347; pocket-floor engagement concentrated in the
  caiso-221 §E.1 Local-curtailment-active windows (655/508 h, 2024/25). The
  program's C3a case rests on CHANGED SYSTEM DISPATCH (caiso-223 §D(b)); the
  direct pocket-floor channel alone was pre-bounded SMALL (≈ −$0.23/−$0.32/
  −$0.25 lw) and a full 2025 close is NOT expected ex ante (convertible mass
  +0.94 vs required −1.90).
* **C3a movement reported at full magnitude** (required for a band pass:
  −0.85 2024 / −1.90 2025); no promotion claim is derived from it here.
* **Guards:** C1 rows re-scored (the zonal recut must not flip fuel-mix
  rows); C3b tripwire — any year worsening by > 0.005 EMD must be named to a
  mechanism in the finding; C2/C4/C8 re-scored as always.
* **F1 (over-trapping falsifier):** the lower-bound caps are too tight if the
  arm's pocket boundaries bind far beyond the DMM record's own binding-share
  ceiling (Moss Landing–Las Aguilas 24–27 % of ALL hours is the highest
  observed; Gates–Midway 9 % of hours in 2024) or FSNO floors/negative hours
  appear at magnitudes reality's record contradicts. F1 firing ⇒ the static
  DMM-cap arm is **R** for keeper purposes; the partition representation
  itself remains, with W-2/W-3 the upgrade feeds.
* **F2 (static-vintage falsifier, the caiso-218 §C signature):** if the arm's
  split-hour vector is strictly year-ordered while reality's is non-monotone,
  single-vintage statics are insufficient at this grain too; the
  backcast-admissible transmission-outage derate channel (today unpublished
  for these elements) is recorded as the watch, not armed.
* **Verdict space:** K (structural improvement — owner may promote on the
  registered evidence) / O (engages, partial) / R (falsified per F1/F2).
  **Never auto-promoted**; the matrix cell is stamped with the tested verdict
  either way (rule 28b), and both runs are registered whatever they show
  (rule 15).

## §6 — Records this round will produce

Both bundles registered on the backcast dashboard; `_caiso224_ctrl_tolerance.json`;
the split-witness probe artifact; `FINDING-caiso224-fsno-arm-2026-08-30.md`;
`docs/calibration-log/caiso.md` caiso-224 entry; matrix base row + all-shard
cell lines + the CAISO cell verdict stamp. Keeper, markers,
`holdout-freeze.json`, DOF ledger of the keeper, and every other ISO's shard:
untouched. Reads stay in 2023–2025 [R-HOLDOUT]. THE OWNER MERGES.
