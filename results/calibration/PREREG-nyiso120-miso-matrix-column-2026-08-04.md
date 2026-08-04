# PRE-REGISTRATION — nyiso-120 (TASK 2): close MISO's rule-28(c) matrix column

**Date:** 2026-08-04 · **Session:** nyiso-120 · **Lane:** NYISO session taking the
**cross-ISO column work** (TASK 2) · **Target column:** **MISO**
**Branch:** `claude/nyiso-120-calibration-hekvta` · **Committed and pushed BEFORE any
row is written and before the construction probe is run.**

---

## §1 — why this session is here, and why it is MISO

**NYISO's own queue is exhausted and its column is closed.** Re-confirmed this session,
nothing else touched:

```
mechanism_matrix_gap_sweep.py --iso NYISO
NYISO   41 family | 0 absent | 0 prose-only | 0 armed-no-cell | 0 shared-gap | 0 invisible
```

sole exclusion the declared `weather_year`, exactly as nyiso-119 left it (the 40 → 41 was
nyiso-119's own new field + row, not drift).

TASK 1 is **not available to this session** and is not taken:

* **(a) the compressed peak-half price distribution** is DECOMPOSED and route-EXHAUSTED at
  nyiso-110 (its flag-only arm solved INERT) and is **pending an owner amplitude-criterion
  call**. nyiso-119's incidence/depth residual is *adjacent* to it but this session does
  **not** treat it as new evidence and does **not** solve it. It is flagged to the owner in
  the finding, not acted on.
* **(b) C3c** is closed as a lever lane; its re-open condition is a `Capital_Hudson` →
  Zone-F/Zone-G **topology split** needing its own owner charter, not a mechanism flag.
* **The SENY curve lane is CLOSED** (three independent measurements; $40 / 1,300 MW /
  $500 base frozen under rule 23). Not re-opened, not re-levelled, not re-scoped.

**Therefore TASK 2, and the target is MISO — measured, not assumed.** The counts in the
handoff are from 2026-08-03 and have moved; the sweep was re-run this session:

| ISO | family | absent | prose | armed-no-cell | shared-gap | invisible |
|---|---|---|---|---|---|---|
| ERCOT | 84 | 0 | 0 | 0 | 14 | 12 |
| CAISO | 61 | 0 | 0 | 0 | 5 | 1 |
| **MISO** | **25** | **8** | **4** | **7** | **17** | **18** |
| NEISO | 20 | 0 | 0 | 0 | 0 | 0 |
| NYISO | 41 | 0 | 0 | 0 | 0 | 0 |
| PJM | 36 | 0 | 0 | 0 | 18 | 0 |

**PJM's own-family column is now CLOSED** (`pjm-151` Phase 0, 15 absent → 0), so the
handoff's "MISO and PJM are the worst columns" resolves to **MISO alone**. With ERCOT
(`ercot-156`), CAISO (`caiso-161`), NEISO and NYISO (`nyiso-113`) already closed, **MISO is
the last open column** — which `matrix_gap_census`'s own note already says in terms
("WITH PJM CLOSED, MISO IS THE LAST OPEN COLUMN").

MISO keeper at session start: **`2026-08-04-miso-122b-scope-gate`**, 34 bundles scanned.

## §2 — scope: what this session WILL do

Register all **8 absent + 4 prose-only** `miso_*` fields — **7 of them ARMED on the
published MISO keeper with no cell anywhere** (the 227-3 shape) — as **LITERAL sub-scalar
registrations on EXISTING family rows**, per the `pjm-151` / `caiso-161` / `ercot-156`
precedent. The pre-declared mapping, fixed before any text is written:

| # | field | keeper value | home row | status now |
|---|---|---|---|---|
| 1 | `miso_zonal_reserves` :4660 | **True** | `energy_reserve_coopt` | absent, ARMED |
| 2 | `miso_zonal_reserve_zones` :4677 | None | `energy_reserve_coopt` | absent |
| 3 | `miso_midwest_subregional_reserves` :4681 | **True** | `energy_reserve_coopt` | absent, ARMED |
| 4 | `miso_rpe_pricing` :4814 | **True** | `rdt_tcdc` | absent, ARMED |
| 5 | `miso_south_seam_split` :4785 | **True** | `seam_flow_envelopes` | absent, ARMED |
| 6 | `miso_seam_envelope_merit_cap` :3820 | **True** | `seam_flow_envelopes` | absent, ARMED |
| 7 | `miso_manitoba_seam` :3911 | **True** | `seam_flow_envelopes` | prose-only, ARMED, **mis-homed** |
| 8 | `miso_pjm_border_anchor` :3789 | **True** | `import_hub_pricing` | absent, ARMED |
| 9 | `miso_pjm_lmp_import_pricing` :3872 | False | `import_hub_pricing` | prose-only |
| 10 | `miso_firm_import_floor` :3841 | False | `reference_price_interface` | prose-only |
| 11 | `miso_cc_coal_rebalance` :3859 | False | `diurnal_price_amplitude` | prose-only |
| 12 | `miso_native_outage_source` :9576 | False | `campd_outage_windows` | absent |

Home rows are chosen on a **code-level dependency**, not on theme: 1–3 all state
"Requires `energy_reserve_coopt`"; 4 states "Requires `miso_rdt_tcdc` (fails loud
otherwise)"; 5–7 all compose through `inject_miso_seam_flow_limit` /
`get_interchange_spec`; 12 is the same shape as `ercot_noncampd_plant_availability`,
already registered on `campd_outage_windows`.

**Expected result: 7 rows edited, ZERO new rows, ratchet baseline MISO 8 → 0, sweep
`MISO 25 family | 0 | 0 | 0`.**

## §3 — the KILL that governs this session: NO VERDICT MAY BE MINTED

**A census can mint a `U` and nothing more (rules 25 / 28(d)).** Binding, and this is the
gate this session is scored on:

* **K-1 — ZERO mechanism-cell changes.** No `cells:` string of any *mechanism* row may
  change, in any ISO position. Discharged by diffing every `cells:` literal before/after.
* **K-2 — ONE cell mint, and it is an AUDIT status, not a mechanism verdict:**
  `matrix_gap_census` MISO **`O` → `K`**. This is precisely the mint `ercot-156`,
  `caiso-161` and `pjm-151` each made for their own column.
* **K-3 — every verdict-bearing sentence added must TRANSCRIBE an adjudication already on
  the record, with its citation.** No new adjudication. The transcriptions available and
  pre-identified (so that anything beyond them is visible as a breach):
  - `miso_firm_import_floor` — **rejected as an outcome pin (rule 13)**; recorded in the
    `reference_price_interface` note (miso-114) and in `miso_seam_measured_ladder`'s own
    code comment ("contrast the rejected `miso_firm_import_floor` pin").
  - `miso_pjm_lmp_import_pricing` — **REFUTED EX ANTE on MISO's own data** for the seam
    hour-of-day defect and must not be armed for it (miso-114, recorded verbatim in
    `reference_price_interface`).
  - `miso_cc_coal_rebalance` — **LICENSED BY NOTHING**; its target is defined relative to
    another *model* quantity with no measured identification (rules 5/21/24), and
    miso-115 §2 removes its stated premise. Recorded twice in `diurnal_price_amplitude`.
  - `miso_zonal_reserves`' per-Reserve-Zone §5.2.1.2 **Zonal ORDC ladder is
    measured-refuted** and deliberately NOT used by the Midwest family (never separated in
    26,280 h; miso-71 design §1b/§2a, recorded in the field's own comment).
* **K-4 — no MISO field is re-derived, re-levelled or re-scoped.** No solve is run against
  any MISO mechanism. **NO-TUNING CLAUSE: this session changes no `ScenarioConfig` value,
  no constant, and no derive script.** It is documentation + one audit-status cell.

## §4 — the one MEASUREMENT this session makes, pre-specified

A census may not adjudicate, but `caiso-161` §5 and `pjm-151` both **reported** which
armed-looking keeper fields are **provably unobservable**, because a `run_config.json` that
records a flag `True` overstates what the solve actually did. Two candidates are visible in
MISO's code and are pre-registered here **as observations, never as cell verdicts**:

* **O-1 — `miso_pjm_border_anchor` is displaced by `miso_seam_measured_ladder`.** The
  keeper arms **both**. `inject_miso_seam_measured_ladder`'s docstring
  (`interchange/miso.py:308`) states it "Runs LAST among the seam price overwrites,
  displacing the `miso_pjm_border_anchor` / `miso_pjm_lmp_import_pricing` prices on any row
  it covers (the flags are alternatives, never stacked)", and
  `MISO_SEAM_LADDER_BY_YEAR` carries a full 8-band import + 8-band export PJM entry in
  **all three keeper years** (2023/2024/2025).
* **O-2 — `miso_firm_imports` is dropped by `miso_manitoba_seam`.** The keeper arms
  **both**. `interchange/spec.py:1757-1763` drops the MHEB firm block when
  `miso_manitoba_seam` is set, so `inject_miso_firm_imports` no-ops.

**GATE G-1, written on CONSTRUCTION and not on a solved dual** (the binding lesson of
nyiso-115 G2 / nyiso-118): build the MISO reference-price seam **twice at one HEAD** on the
keeper's own flags — `miso_pjm_border_anchor` ON vs OFF, `miso_seam_measured_ladder` **ON in
both** — and diff the resulting seam band marginal costs.

* **G-1 PASS (inert):** the two constructions are **exactly equal** (`np.array_equal`, not a
  tolerance — float32 exact, per nyiso-116 G3/P4) in all three years ⇒ the flag is
  **provably unobservable on the keeper**, reported as an observation.
* **G-1 FAIL (live):** any band differs ⇒ the flag is live, the O-1 hypothesis is **WRONG**,
  and **that is recorded as a failed pre-registration**, not quietly redefined
  (nyiso-115 G2 / nyiso-117 G2a / nyiso-119 G4 discipline).
* **G-1 UNINFORMATIVE:** if the probe cannot build a MISO seam at all, it is reported
  UNINFORMATIVE — **never** as a pass. The instrument must be shown to SEPARATE on
  something before its silence is trusted: the probe therefore also builds
  `miso_seam_measured_ladder` OFF, where the border anchor **must** move the PJM bands. If
  that positive control does not separate, the whole probe is void.

**Neither observation moves a cell.** Whether O-1/O-2 are cosmetic or a rule-19 stacking
question belongs to a lane that may adjudicate MISO; this one may not.

## §5 — what this session does NOT close, stated so it is not over-read

* **The 17 shared-stem fields MISO's keeper arms invisibly** (`coal_warm_committed`,
  `ct_intermediate_split`, `temp_derate_*`, `tranche_startup_conditional_runs`,
  `carry_operating_mothballs`, …) are **CROSS-ISO** — the same fields sit in PJM's 18 and
  ERCOT's 14 — and stay filed for a cross-ISO hygiene lane. One column's session does not
  close them, exactly as `pjm-151`/`caiso-161`/`ercot-156` each declined to.
* **No MISO lever is tested, chartered or queued.** A census does not manufacture a
  successor.
* **NYISO's keeper, gates, determination and `calibration-complete.json` entry are
  UNTOUCHED.** No promotion is made in any ISO, so no re-key and no determination
  re-verification is owed (rule 22 D-5(b) does not fire).

## §6 — governance

* **Rule 15** — no run is produced, so nothing is registered on the dashboard. This session
  spends **zero solves**.
* **Rule 16 / rule 22** — no year is solved, scored or read. The **holdout spend freeze is
  ACTIVE and untouched**; no year outside 2023–2025 is approached.
* **Rule 25 `[R-ISO-SCOPE]` / 28(d)** — verdicts are strictly per-ISO. No NYISO verdict is
  copied into MISO's column and no MISO verdict is minted.
* **Rule 27 `[R-PUSH]`** — `mechanism-matrix.js` is ~2,014 lines; it is edited **locally with
  the Edit tool** and pushed as exact on-disk bytes, **never** as regenerated full content,
  and the pushed blob is verified (line count + hash) immediately after the push.
* **Rule 28(b)** — the matrix is updated in **this** session.
* **Ratchet** — `mechanism-matrix-gaps.json` is regenerated with `--write-baseline` (a full
  six-ISO write; the tool refuses a partial-ISO write), so the list can only shrink.

## §7 — falsifiable success criteria

1. `mechanism_matrix_gap_sweep.py --iso MISO` reports **25 family | 0 absent | 0 prose-only
   | 0 armed-no-cell**.
2. `scripts/check_mechanism_matrix.py` passes.
3. Every `cells:` string is byte-identical to main's **except** `matrix_gap_census`
   (`KKKOKO` → `KKKKKK`).
4. The five other ISOs' sweep counts are **unchanged** — no substring-shadow artifact
   silently drops another column's entries (the defect `pjm-151` had to correct for MISO).
5. G-1 is reported with its positive control, whichever way it lands.
