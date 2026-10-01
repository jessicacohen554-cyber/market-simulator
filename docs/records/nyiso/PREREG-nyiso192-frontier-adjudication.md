# PRE-REGISTRATION — nyiso-192: the frontier re-assessment — the two handed-forward objects decomposed WITHOUT an LP, an instrument defect found and repaired, and ZERO arms

**Session:** nyiso-192, NYISO backcast-calibration track, 2026-09-05.
**Branch:** `claude/nyiso-192-frontier-adjudication-mo2nrq`, fresh off `origin/main`
at `a0014864` (carries PR #4769, the nyiso-191 `CC_CHP` rejection, and PR #4772).
**Keeper at entry:** `2026-09-05-nyiso-189-steam-identity` — CALIBRATED, grade 7,
fails 0, C3c the lone ledgered caveat; C1-2024 `CC_REGULAR` +3.33 TWh / +2.8 pp
against 3.0 pp (headroom 0.49 TWh / 0.2 pp).
**Markers, verified at HEAD and NOT re-executed:** `complete.NYISO` exists, keyed to
the current keeper with its determination re-verified by the D56-R records lane;
`final` empty; the locked-test freeze is active. The rule-22 D-5(b) duty is
already discharged — **this session re-keys nothing, requests no marker, and
spends nothing**: training years 2023–2025 only. **Frontier is WITHDRAWN**
(`keepers/NYISO.json` `frontier.withdrawn` = 2026-08-30) and this session does NOT
declare it; it produces the evidence for card C-10 / Q39.

**THIS DOCUMENT IS COMMITTED AND PUSHED BEFORE THE ONLY SOLVE OF THIS SITTING (a
same-HEAD control replay of the keeper, §3) AND BEFORE ANY DASHBOARD PAYLOAD IS
RE-RENDERED.** No LP artifact of this sitting exists at the time of writing.
Everything in §0–§2 was measured on committed bytes and the no-LP fleet
reconstruction (`scripts.lib.bundle_fleet.reconstruct_bundle_fleet`).

---

## §0 — DISCLOSURE 1: the instrument the two handed-forward objects were measured with is DEFECTIVE, and the defect inflates the top-of-queue object THREE-FOLD

`scripts/render_calibration_html.py` adds a cogen's behind-the-meter host supply
back onto its **model** series so the plant heatmap compares the full plant to
the full CAMPD plant. The bench side passes the nyiso-147 **measured** per-plant
shares (`measured=_btm_measured`, the nyiso-149 pin); **the model-payload site
(the `mplants[key]["m"]` / `m_ann` writer) did not** — it fell through to
`chp_btm_pct(sector)`, the 35 % "merchant" default. The keeper's LP, under
`nyiso_chp_btm_measured`, held out the **measured** share (0 % at Sithe
Independence 54547, 22 % at Linden 50006). So every NYISO cogen's dashboard
series carries `e_ann × 35 %` of **flat phantom energy** the LP never dispatched.
Measured on the committed keeper payload
(`scripts/probes/nyiso192_payload_addback_audit.py`,
`_nyiso192_payload_addback_audit.json`):

| year | payload Σ `CC_CHP` plants | LP `class_hourly` `CC_CHP` | flat offset | Sithe payload / LP / CAMPD (TWh) | Sithe over-run published → corrected |
|---|---|---|---|---|---|
| 2023 | 21.29 TWh | 15.50 | 643–674 MW | 5.65 / 4.24 / 4.06 | +1.59 → **+0.18** |
| 2024 | 25.42 | 18.84 | 735–763 MW | 9.47 / 7.32 / 6.29 | +3.19 → **+1.04** |
| 2025 | 25.89 | 20.05 | 655–682 MW | 9.81 / 7.64 / 6.32 | +3.48 → **+1.31** |

The payload's hourly minimum at Sithe is exactly the flat add-back (243 MW ≈
6.158 TWh × 0.35 / 8760), and subtracting the sector add-back from every CHP
plant closes the class identity to the committed `class_hourly` totals within
byte-quantisation (−0.03 to −0.08 TWh). **Consequences for the record, stated
before the repair:** (a) the nyiso-190 §3 "±8 TWh plant-grain misallocation" is
**7.4 / 8.2 / 9.3 → 8.4 / 7.0 / 6.9 TWh** (gross over 11.9 / 11.3 / 11.2 →
8.4 / 7.0 / 6.9; the object shrinks but does not vanish); (b) Sithe is **not**
the fleet's largest over-runner in 2023 or 2024 (Ravenswood `ST_GAS` is, at
+3.13 / +1.74 TWh, unaffected by the defect); (c) Linden 50006 flips from a
−0.18 / −0.43 / −0.55 TWh under-run to **−0.90 / −1.15 / −1.28**; (d) the
"model peak 1,366 MW vs CAMPD 1,193" cited at nyiso-190 §3 is the add-back on
top of an LP capacity of 1,157.8 MW × availability ≤ 0.972 = 1,125 MW — **there
is no phantom winter capacity at Sithe**. Class totals, every gate, and every
determination are **unaffected** (C1 scores bundle class totals, never the
payload).

**The repair (already made in this branch, before this document was pushed and
before any solve):** the model-payload site now passes the run's own hold-out
map — the measured shares iff the run's `nyiso_chp_btm_measured` flag is on,
the sector default otherwise — so the add-back mirrors what that run's LP held
out; the `volErr` actual-side `_grid_frac` passes the measured map whenever the
artifact exists (the bench convention). Pinned by
`tests/scoring/test_render_chp_addback_measured.py`, which reads the source and
fails on any bare `_btm_share(` call. **The keeper's committed payload is
re-rendered from a same-HEAD control replay (§3), so the record's plant-grain
numbers come from the repaired instrument; historical NYISO payloads (14 other
registered runs) are NOT re-rendered here — their slim bundles carry no
dispatch parquet — and are flagged as carrying the defect in the FINDING.**

## §0b — DISCLOSURE 2: object 1 (Sithe) — the census rule is RIGHT, and the corrected residual is not an offer object on in-repo data

Phase 0 (`scripts/probes/nyiso192_sithe_duty_phase0.py`,
`_nyiso192_sithe_duty_phase0.json`), on the corrected LP series:

* **The cohort-admission rule declines Sithe correctly.** Its census row reads
  `cells_zero 0 of 18`, pooled median 752 MW, HSL 1,187 MW, online share 0.844,
  verdict `operating`. The rule is a lay-up test (median gross = 0 in every
  4-hour block of every year) and Sithe is a plant that ran 6.3 TWh; a rule that
  admitted it would be a low-CF test, which nyiso-148 rejected by name. A
  price-conditional "duty curve" for a live merchant CC would pin observed
  conduct (rule 13) — it is not proposed.
* **The corrected over-run is level-when-on, not hours-on**: 2024 +1.04 TWh =
  +0.81 both-on level + 0.32 measured-off/LP-on − 0.10 LP-off/measured-on; 2025
  +1.32 = +1.20 level. CAMPD shows all four trains on for 72 % of on-hours at a
  mean 949 MW (80 % of HSL); the LP holds the plant near its available cap.
* **On the model's own SRMC (Tenn Z4 200L + $2 VOM + RGGI), Sithe's last econ
  tranche ($25.2 in 2024) is in merit 95.8 % of hours at the model's
  Upstate_West price but 75.7 % at the ACTUAL Zone-C RT LBMP**; the model has
  Upstate_West below $20 in 0.7 % of 2024 hours against 15.3 % actual (p05 23.4
  vs 16.7). **0.47 of the 1.04 TWh 2024 residual sits in those trough-flip
  hours** — the price-compression object already adjudicated (nyiso-109 corrected
  the trough half; nyiso-167/168: a year-invariant 0.70 price-response gain, its
  one new mechanism provably LP-inert; the remainder owner-court under
  DECISION-CARD-nyiso148 Q1). In 2023 the trough matches (28.9 % vs 29.6 %) and
  Sithe's residual is +0.18 TWh; in 2025 it is 2.4 % vs 4.1 % and the +1.31 TWh
  residual is NOT price-explained: in 74 % (2024) / 66 % (2025) of the hours the
  plant part-loaded, the actual Zone-C price was ABOVE its full-load SRMC.
* **What that leaves is unidentifiable in-repo**: Sithe files no EIA-923
  Schedule-5 delivered-gas cost (0 rows; only 5 NY plants do — 2493 / 2511 /
  2516 / 2517 / 56196), so whether its true delivered basis sits above the SOM
  Zone A–B hub the model assigns (its supply is not Tenn Z4 200L) cannot be
  measured; and four trains at 80 % while in merit is the signature of a
  regulation / reserve reservation, a product the representation does not carry
  (the NYCA reserve families are hydro-saturated at zero dual in every hour —
  nyiso-152). **Pre-committed disposition: INADMISSIBLE / IDENTIFICATION-BLOCKED
  at the current representation**, with the intake that would unblock it named.
  No arm.

## §0c — DISCLOSURE 3: object 2 (`ST_GAS` zonal placement) decomposes to TWO named owners, neither a lane lever — and the one lever it points at is refused EX ANTE, with the computation

Phase 0 (`scripts/probes/nyiso192_stgas_zonal_decomp.py`,
`_nyiso192_stgas_zonal_decomp.json`):

* **Offer anatomy.** Ravenswood's heat-rate basis is **CLOSED** on the keeper
  (`egrid_family_heat_rates`, armed at nyiso-185: committed-tranche HR 12.906 =
  12.29 × 1.05; its capacity-weighted HR 19.15 is now the HIGHEST of the NYC
  steam plants). What makes NYC steam cheaper than LI / CH steam in the model is
  the **zonal delivered-gas basis**: NYC `ST_GAS` at the Transco Z6 NY hub
  (1.94 / 2.07 / 3.71 $/MMBtu) against LI / CH at Iroquois Z2 (3.28 / 2.77 /
  5.06) — a $0.70–1.38 gap that the repo's own monthly Transco / Iroquois series
  reproduces to ±$0.1. On the Iroquois reference basis (S2) the NYC committed
  tranches' in-merit share falls from 0.31–0.53 to **0.04–0.12**, level with LI /
  CH. The basis is a measured input (SOM Figure A-6), so the NYC over-run is a
  **delivered-gas identification** question, not a price-formation one: the
  model's NYC price is at or BELOW actual (−0.7 / −7.0 $/MWh in 2024 / 2025).
* **LI / CH under-run.** S1 (model offer vs ACTUAL zonal price) lifts LI / CH
  in-merit shares by only 0.05–0.09; the model's LI price is −$2.9 / −$9.7
  below actual (the compressed downstate premium, C3a-2025 owner-court). Northport
  is ON 99.9 % of measured hours at CF 0.28 and Bowline ON 27 % against a 13 %
  in-merit share on its own SRMC — **out-of-market commitment**, the nyiso-187
  disposition (`b ≥ 0.50` in every downstate cell), cell G, owner-closed.
* **The one lever the decomposition points at**, and why it is refused without a
  solve: NYC steam plants file no F923 receipts, so the only in-repo delivered
  basis above the hub is the LDC-delivered daily index the `CT_PEAKER` leg
  already uses (`nyiso_downstate_ct_gas_daily`: Transco Z6 NY daily + KEDNY
  SC-22 non-firm transport; 4.54 / 4.91 / 7.82 $/MMBtu in NYC). Extending it to
  NYC `ST_GAS` shifts the committed tranches by **+$33.6 / +$36.7 / +$53
  per MWh** and their in-merit share to **0.4–1.1 %** in every year, on the
  keeper's own hourly prices. The class would then dispatch only what the NYC
  persistent-base reliability floor holds (2.85 / 2.31 / 1.67 TWh; 325 / 263 /
  191 MW mean) — **~100 % floor-forced, so rule 20 / C8 fails BY CONSTRUCTION**
  (the pre-registered rejection rule). nyiso-145 already refused the same
  extension for the LI CC/ST fleet on F923 grounds (cell
  `nyiso_downstate_ct_gas_basis`, K). **Pre-committed disposition: the correct
  delivered basis for NYC steam is an identification intake (plant → LDC
  transport service; Con Edison's electric-generation transportation rate,
  absent from the repo — Ravenswood and Astoria are Con Ed, Arthur Kill is
  KEDNY); and whatever basis is adopted, the market's NYC steam dispatch is
  out-of-market commitment that the representation cannot carry without cell G
  → BLOCKED (G) + identification intake.** No arm.

---

## §1 — WHAT IS BUILT (exactly)

1. **The payload repair** (§0): two call sites in `scripts/render_calibration_html.py`
   + `tests/scoring/test_render_chp_addback_measured.py`. Zero `ScenarioConfig`
   changes, zero constants, zero derive edits.
2. **Nothing else.** No mechanism, no field, no artifact, no arm.

## §2 — WHAT IS SOLVED (exactly one control, no arm)

`scripts/replay_keeper.py results/calibration/nyiso189_steam_identity` — the
byte-faithful in-place replay (years 2023 2024 2025 sequential, rule 12), which
regenerates the gitignored `dispatch/`, `system.parquet` and `btm.parquet` the
payload writer needs and leaves every committed slim file byte-identical. Then
`scripts/dashboard_add_run.py --label "nyiso 189 steam identity" --bundle
results/calibration/nyiso189_steam_identity --no-prune` re-renders the keeper's
own `runs/2026-09-05-nyiso-189-steam-identity.js` under the same id.

## §3 — THE BARS (fixed before the replay)

* **V1 — control identity.** The replay must be bit-identical to the keeper:
  0 of 52,560 P1 zonal prices differ in each year (`hourly/system_<year>.parquet`
  regenerated vs committed), and `git status` shows no committed file of the
  bundle changed. If not, the instrument is not the keeper and the re-render is
  NOT performed (the committed payload stays as it is, defect disclosed).
* **V2 — repair identity.** In the re-rendered payload, (a) every NON-CHP plant's
  `m` bytes and `m_ann` are unchanged; (b) for each CHP class, Σ_plants `m_ann`
  − Σ_plants (measured BTM add-back) equals the committed `class_hourly` class
  total within 0.02 TWh (`btm.parquet` basis); (c) Sithe's `m_ann` reads
  4.24 / 7.32 / 7.64 ± 0.02 TWh.
* **P1 — my falsifiable prediction.** The corrected Sithe over-run on the
  re-rendered payload is **+0.18 / +1.04 / +1.31 TWh** (± 0.03); the corrected
  plant-grain offsetting misallocation is **8.4 / 7.0 / 6.9 TWh** (± 0.1). If
  either misses, my §0 arithmetic was wrong and the FINDING says so.
* **B3 — no verdict rule is engaged**: no arm is solved, so nothing can flip.
  The keeper's determination is re-verified artifact-only after the re-render
  (`scripts/calibration_verdict.py --run-id`) and must read CALIBRATED,
  unchanged — a change is a stop-the-line event (the payload is not a scoring
  input, so a change would mean the replay is not the keeper).

## §4 — PRE-COMMITTED DISPOSITIONS FOR THE ASSESSMENT

| object | disposition, fixed now |
|---|---|
| Sithe 54547 duty | INADMISSIBLE / IDENTIFICATION-BLOCKED (census rule correct; residual = trough-flip hours (owner-court compression object) + unmeasured delivered basis / unrepresented regulation product); magnitude CORRECTED 3× |
| `ST_GAS` zonal placement | NYC over → delivered-gas identification intake (owner-court) + BLOCKED (G); LI / CH under → cell G (nyiso-187) + C3a-2025 owner-court. The LDC extension to NYC steam is REFUSED EX ANTE (C8 by construction); no solve |
| nyiso-190 plant-grain ±8 TWh | INSTRUMENT DEFECT: corrected to 8.4 / 7.0 / 6.9; the CHP rows re-stated; the non-CHP rows stand |
| every other item | as enumerated in the assessment, from its own record |

**Frontier verdict rule, fixed now:** the assessment answers YES only if every
enumerated object reads CLOSED / REJECTED / INADMISSIBLE-BLOCKED / OWNER-HELD /
LEDGERED with a citation; any object left STILL OPEN **with a live admissible
lever** forces NO. An un-owned OBSERVATION with no admissible lever named is
reported as such and does not by itself force NO (the nyiso-154 standard: no
`O`/`U` cell with an admissible in-repo identification), but is named as the
assessment's weakest point.

## §5 — STOPS

* **S1** — no arm, no `ScenarioConfig` field, no derive, no constant (rules 5 / 19 / 21 / 24).
* **S2** — the LI / CH `ST_GAS` delivered basis is NOT touched (nyiso-145, DO-NOT-REDO).
* **S3** — cell G stays G; C3a-2025 (Q1) untouched; `chp_layup_duty_curve` not re-adjudicated; `cc_capacity_reconcile` `CC_CHP` widening not redone; the Bethlehem, Zeltmann and Astoria-routing items not re-opened.
* **S4** — no marker requested, no out-of-training year solved / scored / registered.
* **S5** — the historical payloads are not rewritten arithmetically; they are flagged.
* **S6** — no frontier field is edited; the declaration is the owner's (card C-10 / Q39).

## §6 — GOVERNANCE

Rule 1: bars and dispositions fixed and pushed before the only solve; the
instrument defect is disclosed before its repair is exercised. Rule 11 / 14:
the found defect is repaired at its root (the call site), not worked around.
Rule 13: every measured series diagnoses; nothing is fed back. Rule 15: the
control replay mints no new run (in place, same id); the re-rendered keeper
payload is committed and pushed in-session. Rule 22: 2023–2025 only; markers
untouched. Rule 25 / 28: NYISO shard only; the matrix cells touched are named in
the FINDING. Rule 27: on-disk bytes pushed; every ≥300-line blob verified after
each push.

*(nyiso-192, 2026-09-05. Pushed before the control replay and before any payload re-render.)*

---

## §7 — AMENDMENT 1 (pushed BEFORE the arm is solved): the Astoria merit-panel stack-duplicate defect is MEASURED, it is NOT Astoria-only, and it is A/B-solved as the session's ONE arm

**Why the plan changes.** Enumerating the objects opened since nyiso-154 for the
assessment, the Astoria merit-panel stack-duplicate defect (nyiso-184 §4.1 —
"sized, not repaired; needs its own A/B on that lane"; carried unbuilt through
nyiso-185…191) is a **live, admissible, untested measured-input repair** inside
the NYISO keeper's own availability envelope. Under §4's frontier verdict rule
that alone forces **NO**, so it is adjudicated here rather than left open.

**The repair (one call site, code already in this branch):**
`scripts/lib/outage_detect.build_merit_order_panel` read the CAMPD parquets with
a bare `pd.read_parquet` and never applied the stack-duplicate helpers
`campd._normalize_campd` applies. Astoria 8906's `31RH`/`32SH` and `51RH`/`52SH`
pairs therefore entered the panel as two units each carrying the SAME generator
MW with half the heat — SRMC at half its physical value inside the guard that
decides mechanical outage vs economic lay-up. The loader now drops the
duplicate's `grossLoad` copy and re-labels it onto its primary
(`stack_duplicate_mask` / `merge_stack_duplicate_units`), exactly as
`_normalize_campd` does; `tests/curation/test_merit_panel_stack_duplicate.py`
pins it (merged HR 10.33 on the fixture, 5.33 before). The registered stack-pair
set is `{8906}` (NY only), so every other ISO's panel is **byte-identical by
construction** — no other ISO's extract is re-derived or touched (rule 25).

**Phase 0 — the extract re-derived under the keeper's committed invocation**
(`--iso NYISO --years 2019…2026 --per-unit-crosswalk --merit-order-guard`, the
`.meta.json` flags verbatim; output to a scratch path so the running control
kept reading the committed file), diffed against the committed extract
(sha256 `45bc4f7c…`; repaired `sha256` in the arm bundle):
3,668 → 3,717 rows; **106 windows leave** (all Astoria: the primaries `31RH` /
`51RH` drop from 226 / 241 → 89 / 0 window-days in 2023, 189 / 219 → 0 / 0 in
2024) and **155 windows enter at fifteen OTHER plants** — because the panel's
revealed clearing cost (the capacity-weighted p90 SRMC of the RUNNING units) is
itself built from Astoria's rows: with its steam priced at its physical SRMC the
RCC rises in the hours it runs, every other unit reads IN merit more often, and
fewer of their dead spans clear the `MERIT_OOM_FRAC` bar. **My §0-era assumption
that this was an "Astoria-only" object was WRONG and is recorded as such.**
Mean availability, the engine's own builder on each extract
(`_availability_{keeper,repaired}_extract.json`, 2023 / 2024 / 2025):

| plant | keeper extract | repaired extract |
|---|---|---|
| **8906 Astoria `ST_GAS`** | 0.177 / 0.240 / 0.330 | **0.367 / 0.509 / 0.462** |
| **2500 Ravenswood `ST_GAS`** | 0.786 / 0.478 / 0.309 | 0.786 / **0.260 / 0.121** |
| 2490 Arthur Kill | 0.855 / 0.907 / 0.527 | 0.829 / **0.453** / 0.527 |
| 2516 Northport | 0.527 / 0.526 / 0.552 | **0.368** / 0.521 / 0.526 |
| 2625 Bowline Point | 0.148 / 0.224 / 0.397 | 0.104 / 0.224 / 0.288 |
| 8006 Roseton | 0.057 / 0.067 / 0.755 | 0.057 / 0.067 / **0.357** |
| 2480 Danskammer | 0.222 / 0.223 / 0.215 | 0.222 / 0.223 / 0.079 |
| 2517 Port Jefferson | 0.925 / 1.000 / 1.000 | 0.916 / 0.989 / 0.830 |
| 2511 Barrett · 2493 East River · 52168 · 50744 | unchanged | unchanged |

**This is a rule-14 `[R-ACCURATE]` licence, stated before the solve**: the
repair uses no residual, adds no parameter, and applies the SAME measured
correction the canonical CAMPD normalizer already applies. It re-opens
Ravenswood's *availability* under the DO-NOT-REDO clause's own exception — NEW
EVIDENCE: nyiso-183 refuted a mis-BOOKING by the guard on a panel whose INPUT
was defective; the guard's classification was sound on the evidence it was
given. Nothing about the guard's rule or thresholds moves.

### §7.1 The arm

**Control** = the in-place same-HEAD replay of §2 (V1). **Arm** =
`scripts/replay_keeper.py results/calibration/nyiso189_steam_identity --out-dir
results/calibration/nyiso192_astoria_panel --note "nyiso-192 ARM …"` with the
repaired extract swapped in at the committed path for the duration of the solve
and the committed file **restored byte-for-byte afterwards** (git checkout;
hash verified), the nyiso-191 artifact-swap pattern. Years sequential, one
bundle (rule 16). **ZERO `ScenarioConfig` changes** — the recipe is the keeper's;
the delta is the committed artifact the armed `campd_outage_merit_order_guard`
reads. No new constants, fields or DOF entries.

### §7.2 Bars

* **G-DELTA** — the arm's `run_config.json` scenario config is IDENTICAL to the
  keeper's (computed: `delta_fields == []`); the ONLY difference is the extract,
  whose two hashes are recorded. Any config delta is a stop.
* **B1 — engagement.** The arm's `(2500, ST_GAS)` / `(8906, ST_GAS)` fleet
  availability equals the repaired-extract column above to ±0.005 (verified by
  reconstructing the arm's fleet through `bundle_fleet.reconstruct_bundle_fleet`
  with the repaired file in place). Not engaged ⇒ INERT, never a pass.
* **B2 — my falsifiable predictions.** (a) Astoria `ST_GAS` model energy RISES
  in all three years; (b) Ravenswood `ST_GAS` model energy FALLS in 2024 and 2025
  and is within ±0.15 TWh of the keeper in 2023 (its 2023 envelope is unchanged);
  (c) Roseton `ST_GAS` 2025 falls. If (a) or (b) fails, my reading of the
  mechanism was wrong and the FINDING says so before any verdict.
* **B3 — the rejection rule.** REJECTED iff any of **C2 / C3a / C3b / C8** flips
  PASS → FAIL. A **C1** flip (any class-year) is NOT an automatic rejection —
  reported at full magnitude with the structural evidence, the promote / reject
  call put to the owner under the standing formula.
* **B4 — structural integrity**, whatever the gates do: the CORRECTED
  plant-grain post-hoc (`nyiso192_payload_addback_audit`'s corrected table,
  re-run on the arm's re-rendered payload) control vs arm; the `ST_GAS` zonal
  placement (`nyiso191_stgas_placement` re-run on the arm); per-plant CF vs
  measured for the nine downstate steam plants.

### §7.3 Pre-committed outcomes

* B1 engaged, B3 no flip, C1 holds → keeper candidate on rule 14; recommendation
  under the owner's standing formula; the promotion executed only if the
  recommendation is *promote*.
* B3 flip → **REJECTED-AS-ARMED**, at full magnitude, with the structural
  evidence; the FINDING then says whether the rejection is on a structural
  collision or on the residual (rule 1 forbids the latter as a reason to drop a
  correct input — a residual-only regression is reported as a discovered
  root-cause issue, the repair stays as the accurate input, and the call goes to
  the owner).
* C1 flip only → owner call, full magnitude, structural integrity stated.
* B2 falsified → root-cause before any claim.

Every outcome is registered (rule 15): the arm as `2026-09-05-nyiso-192-astoria-panel`
(label / verdict in its sidecar), `calibration_verdict --run-id`, the matrix
cells `campd_outage_merit_order_guard` (the repaired input) and
`offer_curve_by_group` updated in the NYISO shard (rule 28), the computed
attestation (`scripts/gen_nyiso192_attestation.py`).

### §7.4 What this amendment does NOT change

§0–§6 stand verbatim: the payload repair, the control replay and its bars, the
Sithe and `ST_GAS`-basis dispositions, every stop (S1 is narrowed exactly to
"no arm EXCEPT §7's"; S2–S6 unchanged). No marker, no holdout year, no frontier
field.

*(Amendment 1, nyiso-192, 2026-09-05 — pushed before the arm is solved; the
control replay was already running on the committed extract.)*
