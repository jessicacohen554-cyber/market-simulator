# PRE-REGISTRATION — nyiso-190 (`backcast-calibration` lane): WHOSE ENERGY the nyiso-189 promotion moved into the 2024 `CC_REGULAR` cell — a ZERO-SOLVE provenance decomposition on committed artifacts, bars fixed before the first number is read

**Session:** nyiso-190, NYISO backcast-calibration track, 2026-09-05.
**Branch:** `claude/nyiso-190-backcast-calibration-n7t2e1`, fresh off
`origin/main` at `c9f1d26e` (carries PR #4754; PR #4743 = the nyiso-189
keeper promotion, `e608966e`, is an ancestor).
**Keeper at entry:** `2026-09-05-nyiso-189-steam-identity`
(`results/calibration/nyiso189_steam_identity`) — **CALIBRATED**, grade 7,
fails 0, C3c ledgered; C3a +4.9 / +1.7 / −8.3 %; C3b 0.119 / 0.166 / 0.177;
**C1-2024 `CC_REGULAR` +3.33 TWh / +2.8 pp against a ±3.82 TWh / 3.0 pp band**
— the closest cell to an edge on this keeper; C8 `ST_GAS` 19.7 / 23.6 / 18.3 %.
**Markers:** NYISO holds neither `complete` nor `final` at `c9f1d26e`
(D56 is issued and has NOT landed — `calibration-complete.json` still carries
NYISO in `withdrawn`, and no re-key under rule 22 D-5(b) applies). Holdout
freeze ACTIVE. **No marker is requested by this session.**

**THIS DOCUMENT IS COMMITTED AND PUSHED TO `origin` BEFORE THE FIRST NUMBER OF
THE OBJECT IS READ.** At the time of writing, nothing of §3's instrument has
been evaluated: no per-plant model level, no measured level, no share, no
partition. **THIS SESSION RUNS NO LP SOLVE** (see §5, stop S1).

---

## §0 — DISCLOSURE: everything read before this document

**Documents (in full or in the cited section):**
`docs/FINDING-nyiso189-steam-collapse-identity-2026-09-05.md` (§§1–6);
`results/calibration/PREREG-nyiso189-steam-collapse-identity-ab.md` §0;
`docs/FINDING-nyiso187-ct-steam-merit-position-2026-09-04.md` §§1–2.2;
`docs/FINDING-nyiso97-load-pocket-identification-2026-07-29.md` §§4–5 (the
cell-G re-open conditions, verbatim below);
`docs/mechanism-testing-matrix.md` §5.5 (the nyiso-189 header + the four
preserved queues); the NYISO shard cells `egrid_steam_collapse_heat_rates`
(K), `scuc_load_pocket_commitment` (G), `cc_capacity_reconcile` (K);
`docs/DECISION-CARD-nyiso148-2025-level-remainder-2026-08-21.md` (heading
scan only — **Q1 is confirmed still PENDING**, so §5 stop S5 applies);
CLAUDE.md rules 1, 5, 12–16, 19, 21–25, 27, 28.

**Code / artifact SCHEMA inspected (structure only — no value of the object
read):** `scripts/lib/backcast_artifacts.py` (`decode_run_js`, the gzb64 wire
format); `scripts/render_calibration_html.py` lines 154–163, 373–378 (the
`_b64` per-plant codec: `round(100 · mw / npl)` clipped to `[0, 250]`,
uint8, 8760) and 1553–1590 (the bench `plants` payload construction —
`campd`, `c_ann`, `c_mon`, `e_ann`, `npl`, `zone`, `group`, `nodata`, the
CT-only reporter flag); `scripts/calibration_verdict.py::score_fuelmix` and
`_fuelmix_vol_band` (C1 scores `gmModel` against `classFull`, i.e. the
EIA-923 grid-delivered actual, band `min(max(2 % load, 3 % actual gen),
8 TWh)`). **Field names and array shapes only were listed** — for
`2026-09-05-nyiso-189-steam-identity.js` the key list of
`years['2024'].plants` and the field names of ONE entry (`2490`); its
`m_ann`/`m`/`r`/`nrmse` values for that entry were displayed incidentally by
the schema dump and are NOT part of any bar below. No control payload has been
opened. No bench plant value beyond the schema of one entry (`2480`,
Danskammer) has been read.

**Numbers already in the committed record (published in the nyiso-189 FINDING
§3.1, not measured here):** the 2024 class totals control → arm
(`CC_REGULAR` 36.11 → 37.39 TWh, i.e. the **+1.28 TWh** this session is
about; `CC_CHP` −0.71, `ST_GAS` −0.30, `CT_CHP` −0.11, `ST_CHP` −0.11,
`CT_PEAKER` −0.01) and the 2024 top plant movers (Empire 56259 −0.284,
Brooklyn Navy Yard −0.225, East River 2493 −0.209, Cricket Valley 57185
−0.168, Athens −0.116 TWh). These are the object's INPUT, not its answer:
what is unmeasured, and what every bar below turns on, is **whether the hours
and plants that lost that energy were running in the real market**.

---

## §1 — THE OBJECT, AND THE CLAIM UNDER TEST

The nyiso-189 promotion put Bethlehem 2539 at its CT-heat identity and moved
+1.78 TWh into it in 2024. About 72 % of that arrived as a **class** gain:
`CC_REGULAR` rose 36.11 → 37.39 TWh and the C1-2024 cell went +2.05 → +3.33
TWh (+1.8 → +2.8 pp), leaving **0.2 pp of margin** against the 3.0 pp band.
The nyiso-189 FINDING §3.1 asserts, in one clause and without measuring it,
that this is acceptable because *"the NYC steam it displaces is what the
market committed anyway"* — i.e. the increment is the receiving end of the
nyiso-187 §2 out-of-market-commitment disposition (cell **G**), not a new
defect.

**That clause is an unmeasured claim on the current keeper, and it is the
single load-bearing sentence standing between this cell and a fail.** This
session measures it. Nothing else.

**H1 (the standing-disposition reading).** The MWh the arm removed from the
displaced plants were removed from hours in which those plants were
**measured running**, at plants the control model was **already under-running**
— so the displacement deepens an existing model deficit at units the market
itself committed, and the CC excess is that deficit seen from the receiving
end.

**H0 (the alternative).** The removed MWh came from hours the market had those
units **off**, or from plants the control was **over-running** — in which case
the displacement is a correction (or a mis-placement) on the displaced side,
the +1.28 TWh is a class-level over-generation of its own, and its owner is
NOT the nyiso-187 disposition.

The two readings imply different owners, different queues, and a different
answer to the owner's question, which is why the bars are fixed here.

---

## §2 — THE INSTRUMENT (committed artifacts only; NO LP)

| role | artifact | fields |
|---|---|---|
| arm, per plant | `frontend/data/backcast/runs/2026-09-05-nyiso-189-steam-identity.js` | `years[Y].plants[key]`: `m_ann` (TWh, exact float), `m` (b64 uint8 hourly, `round(100·mw/npl)`) |
| control, per plant | `frontend/data/backcast/runs/2026-09-04-nyiso-188-combined.js` | same |
| measured, per plant | `frontend/data/backcast/bench/NYISO/<Y>.json.gz` | `bench.plants[key]`: `campd` (b64 uint8 hourly, same codec), `c_ann` (CAMPD TWh), `e_ann` (EIA-923 TWh), `npl`, `zone`, `group`, `nodata` |
| class totals | the same two payloads + bench | `gmModel[class]` (model), `classFull[class]` (C1's own actual) |

**Why `2026-09-04-nyiso-188-combined` is the control.** The nyiso-189 sitting
established G-CONTROL on its own same-HEAD replay: `nyiso189_control` is
**BIT-IDENTICAL** to the superseded keeper — 0 of 52,560 hourly zonal prices
differ in each of 2023 / 2024 / 2025, max |Δ| 0.0 (FINDING §3). The registered
nyiso-188 payload is therefore the control's per-plant dispatch, and no replay
is needed. **Pre-registered verification (V1):** before any bar is evaluated,
the control payload's 2024 `gmModel` class totals must reproduce the FINDING's
control column (`CC_REGULAR` 36.11, `CC_CHP` 19.56, `ST_GAS`, `CT_CHP`,
`ST_CHP`, `CT_PEAKER`) to ≤ 0.01 TWh, and the arm payload's must reproduce the
arm column. **If V1 fails, every bar below is reported UNEVALUABLE and the
card reports only V1** — the instrument would not be the runs it claims to be.

**Decoding.** `MW(h) = byte(h)/100 · npl` for both the model (`m`) and the
measured (`campd`) series — one shared codec, so their difference is a true
MW-space delta, quantized at 1 % of nameplate. **Annual levels are read from
the exact floats (`m_ann`, `c_ann`, `e_ann`) and NEVER from the blobs**; the
blobs are used only to classify hours and to apportion the removed MWh.

**Excluded rows, declared now:** any key with `nodata: true` (no usable CEMS
series) is excluded from the hour-grain bars B1 and reported separately; the
CT-only CEMS reporters (bench flag) are carried in B2's EIA-923 column, since
their CAMPD annual is understated by construction.

---

## §3 — THE BARS (fixed before measurement; **2024 is the gated year**, 2023 and 2025 are reported as context)

Let `Δm_ann(key) = m_ann(arm) − m_ann(control)`. **The displaced set `D`** =
every plant-class key with `Δm_ann < −0.001` TWh (1 GWh; above the 4-dp
rounding of the payload's own annual). `T_D = Σ_D |Δm_ann|` TWh.

**B1 — WERE THE DISPLACED HOURS MARKET-COMMITTED?** For each key in `D`,
hourly removal `ρ(h) = max(0, control_MW(h) − arm_MW(h))`. A plant-hour is
**measured online** when its decoded CAMPD MW ≥ 2 % of `npl` (two codec bytes
— twice the quantum; the nyiso-175 online-bar convention). Then
`s_online = Σ_D Σ_h 1[online(h)] · ρ(h) / Σ_D Σ_h ρ(h)`.
> **H1 is SUPPORTED on B1 iff `s_online ≥ 0.50`. Below 0.50 → REFUTED.**
Sensitivity reported at bars of 1 % and 5 % of `npl`; the 2 % bar is the one
that decides.

**B2 — DID THE DISPLACEMENT MOVE THOSE PLANTS AWAY FROM THEIR ACTUALS?**
With `err_c = m_ann(control) − c_ann` and `err_a = m_ann(arm) − c_ann`,
`w_away = Σ_{D : |err_a| > |err_c|} |Δm_ann| / T_D`.
> **H1 is SUPPORTED on B2 iff `w_away ≥ 0.50`. Below 0.50 → REFUTED**
> (the displacement is predominantly a correction on the displaced side).
Reported on BOTH bases — CAMPD (`c_ann`) as the primary and EIA-923 (`e_ann`)
as the scorer-consistent column; **the CAMPD column decides**, and a
disagreement between the two bases is reported as a finding in its own right.

**B3 — IS THE GAS FAMILY STILL PINNED?** Over `{CC_REGULAR, CC_CHP,
CT_PEAKER, CT_CHP, ST_GAS, ST_CHP}`, compare Σ`gmModel` against Σ`classFull`
for control and arm in 2024 (nyiso-186 measured this EXACT at 67.80 vs 67.80
TWh on its own keeper).
> **The "within-family reallocation" reading holds iff (a) the arm's family
> total is within the C1 volume band (±3.82 TWh) of the family actual AND
> (b) |Σ family model (arm) − Σ family model (control)| ≤ 0.25 TWh.**
> If (b) fails, the increment is NOT a pure reallocation and the standing
> disposition does not carry to this keeper unmodified.

**B4 — WHAT IS THE DISPLACED SET, ACTUALLY?** Report `Σ_D |Δm_ann|` split by
`zone` and by `group`. Descriptive, no pass/fail — it fixes the card's
WORDING.
> **Pre-committed naming rule:** the card calls the increment *"NYC steam /
> cogen displacement"* ONLY IF ≥ 0.50 of `T_D` falls in
> `{NYC, Long_Island, Lower_Hudson} × {ST_GAS, ST_CHP, CC_CHP, CT_CHP}`.
> Otherwise the card names the composition it actually finds, in those words.

---

## §4 — WHAT THE CARD SAYS UNDER EACH OUTCOME (pre-committed, so the result cannot choose the recommendation)

* **B1 ≥ 0.50 AND B2 ≥ 0.50 AND B3 holds → H1.** The +1.28 TWh is the mirror
  of the out-of-market-commitment deficit on units the market ran. The card is
  a **two-option owner decision**: (A) re-open cell **G**
  (`scuc_load_pocket_commitment`) as a *represented* out-of-market commitment —
  admissible under rule 13 only on an input that regenerates for a forward year
  and responds to changed conditions — versus (B) **accept the cell at
  +2.8 pp**, with the consequence stated at full magnitude: any further
  in-merit CC repair breaches the band, so several already-queued accurate-data
  repairs become un-promotable while the out-of-market half is unrepresented.
* **B1 < 0.50 → H0 on placement.** The model displaced units in hours the
  market had them OFF. The card reports a **NEW open object** (the hour
  placement of the displaced plants) and does **not** put the G question to the
  owner at all; the standing disposition is reported as not covering this
  increment.
* **B2 < 0.50 → H0 on direction.** The control was over-running the displaced
  plants and the arm corrected them; the CC excess is a class-level
  over-generation whose owner is not the nyiso-187 disposition. The card
  reports that, re-queues the cell, and again puts no G question.
* **B3 (b) fails → the reallocation reading breaks.** The card reports that
  the family is no longer pinned on this keeper and that the nyiso-186 / -187
  "within-family fill" attribution must be re-derived before any disposition
  is quoted.

**In every branch the card reports every bar at full magnitude, including the
ones that cut against H1**, and states on its face that this measurement can
NEVER identify a mechanism (§5, S2).

---

## §5 — STOPS (binding)

* **S1 — ZERO SOLVE.** No LP runs in this session for this object. A bar that
  cannot be evaluated on committed artifacts is reported **UNEVALUABLE**;
  it is never approximated by a replay, and no bundle is registered (rule 15
  has nothing to register because no run is produced).
* **S2 — THIS MEASUREMENT CAN NEVER IDENTIFY THE MECHANISM.** nyiso-97 §5
  forbids re-opening cell G *"by inferring the requirement from observed unit
  conduct, BPCG uplift, LBMP, or the C3c/`CT_PEAKER` residual."* This
  decomposition **is observed unit conduct**. It may characterize the cell and
  size the owner's choice; it may not supply a parameter, a unit set, an MW
  requirement, or a window. The card carries this sentence.
* **S3 — NO CC LEVER, NO BAND MOVE** (nyiso-187 queue, standing; carried
  verbatim into the nyiso-189 queue).
* **S4 — NO RE-OPEN RECOMMENDATION ON THIS EVIDENCE.** The card may present
  option (A) and state what a qualifying source would have to be — the three
  nyiso-97 re-open conditions, verbatim — but it does **not** recommend
  re-opening, because nothing this session can measure satisfies any of them.
  The nyiso-160 access closure (the owner cannot produce the MyNYISO files)
  is reported as standing.
* **S5 — C3a-2025 IS NOT TOUCHED.** `DECISION-CARD-nyiso148` Q1 is confirmed
  still pending; the −8.3 % remainder stays owner-court and no lever is
  proposed for it.
* **S6 — NO KEEPER CHANGE.** `2026-09-05-nyiso-189-steam-identity` remains the
  keeper whatever this measurement finds; no promotion, no demotion, no
  determination is re-verified (nothing solved).

## §6 — GOVERNANCE

Rule 1: the bars are fixed and pushed before the first number; no outcome is
adopted or rejected on a residual. Rule 13/21: no measured outcome is fed back
as an input — this is a diagnostic decomposition producing a document, not a
config field. Rule 15: no run is produced, so nothing is registered; the
dashboard is untouched. Rule 22: 2023–2025 only, no marker requested, freeze
respected. Rule 24: no tunable is added. Rules 25 / 28: no mechanism is tested,
so no matrix cell changes status; the NYISO shard's §5.5 queue is updated with
this session's outcome and NO other ISO's shard is touched. Rule 27: on-disk
bytes pushed; any ≥300-line blob verified after each push.

*(nyiso-190, 2026-09-05. Pushed before the first measurement.)*
