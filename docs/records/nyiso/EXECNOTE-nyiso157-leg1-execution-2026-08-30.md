# EXECNOTE nyiso-157 — Leg-1 execution of the winter identification intake: K6 re-specification, and a RECORD CORRECTION the executor found first

**Filed BEFORE any solve of this session.** This note is pushed and
blob-verified before either A/B invocation starts, so the re-specified gate,
the companion-condition measurement and the record correction are on the
record ahead of any result (the nyiso-115/117/119 discipline the intake spec
§1 condition 2 orders).

**Authority executed:** `docs/INTAKE-SPEC-nyiso156-winter-locational-2026-08-30.md`
§1 (Leg 1), under the owner's Q1 ruling of 2026-08-30 (OPTION A). The standing
pre-registration is `PREREG-nyiso126-eastern-seam-attribution-2026-08-04.md`
**plus its two nyiso-127 addenda** (`PREREG-nyiso127-addendum-eastern-seam-
availability-source-2026-08-05.md`, `PREREG-nyiso127-addendum2-full-seam-
attribution-2026-08-05.md`) — the addenda are part of the standing record and
are not re-negotiated here, exactly as the parent is not.

---

## §1 — RECORD CORRECTION: this lane was EXECUTED AND REJECTED at nyiso-127, and the 2026-08-30 record correction was itself incomplete

The intake spec §0 corrected nyiso-150 §4's "seam half UNIDENTIFIABLE" to
"authorization-blocked, not identification-blocked". **That correction did not
go far enough.** The GitHub record establishes that on 2026-08-05, under an
owner authorization given that day (quoted verbatim in addendum 2 §1: *"Expand
scope: rebuild all four seam caps"*), the lane was executed end-to-end:

| PR | merged (UTC) | what it did |
|---|---|---|
| #3570 | 2026-08-05 01:13 | "nyiso-127 Phase 0: intake the NY-NJ PAR postings, and the split is NOT 47/21/32" — `data/raw/NYISO/par-data/` (P-33 `outSched` windows + P-34 `ParFlows` hourly, 8 PARs, 2023–2025) |
| #3582 | 2026-08-05 05:21 | "wire the two NYISO seam flags through run_year" |
| #3584 | 2026-08-05 05:32 | "commit both solved A/B arms (slim bundles, all three years)" |
| #3586 | 2026-08-05 06:23 | "the PAR seam attribution is REJECTED — kill gate K3 fires" |

The mechanism (`ScenarioConfig.nyiso_seam_par_attribution`,
`data/nyiso_par_attribution.py`), the intake, the matrix base row and the
NYISO cell verdict **R** are all at HEAD today. The R note records: K3 fired
(C1 fuel-mix free-class 10/10 → 9/10, ST_GAS 2023 out of band at +3.63 TWh /
+3.1 pp vs ±3 pp), K6 passed (control reproduced the nyiso-125 keeper's C3a
+7.7/−0.8/−10.2 exactly), C3a-2023 improved +7.7 → +0.5 %, C3a-2025 worsened
−10.2 → −11.5 %, C3c bit-identical (18/2/21 h both arms), P3 confirmed.

Why the later record lost this: **a session-number collision** (the caiso-186
precedent class). A second sitting also numbered nyiso-127 — the
holdout-readiness review (`FINDING-nyiso127-holdout-readiness-and-frontier-
review-2026-08-05.md`) — wrote the `docs/calibration-log/nyiso.md` nyiso-127
entry, which states "ITEM 1 … was NOT executed — owner-gated, no authorisation
given". That was true when that sitting's text was drafted and false by the
end of the day; no log entry for the execution sitting was ever written; the
dashboard registrations were later pruned by the automatic top-15 retention
(the same pruning nyiso-155 §6 records for the nyiso-146b pair). Every
subsequent session (nyiso-150, -156, -156b, and the nyiso-157 handoff) then
read the log and inherited the gap. **Nothing here changes the nyiso-127
verdict as recorded in the matrix; this section restores it to the log-visible
record.** The companion log entry for this session carries the same
correction; originals stay unedited.

**Consequences for this session's ordered steps:**

* Handoff step 1 (intake) is **already done** — verified present and
  regenerating the recorded split exactly at this HEAD (46 / 7 / 47
  availability-conditioned, `zone_shares` reproduces `_nyiso127_par_phase0.json`
  to 4 decimals). Nothing is re-fetched; `data/raw` stays immutable.
* Handoff step 2 (build) is **already done** — flag, module, wiring and
  matrix row all at HEAD; the smoke test above confirms the input path.
* Handoff step 3 (the A/B) is therefore a **RE-TEST of a cell adjudicated R.**

## §2 — why the re-test is licensed (DO-NOT-REDO satisfied, not waived)

Rule 28's discipline forbids re-testing an R cell **without new evidence**.
The new evidence, named:

1. **The owner ruling of 2026-08-30 itself** — it postdates the R
   adjudication and orders exactly this execution (spec §1: "the owner gate
   is now LIFTED"; handoff: "do not re-litigate").
2. **The baseline moved in precisely the quantity K3 fired on.** The K3
   rejection was ST_GAS 2023 volume (+3.63 TWh past the band) at the
   nyiso-125-era HEAD. One day later that HEAD stopped reproducing
   (nyiso-128 §2: K6 fired with all 680 config fields identical), and the
   nyiso-128/129 **solar market-generator basis repair** then removed
   ~1.6–2.9 GW of phantom solar and showed in-state thermal — ST_GAS
   included (+365 MW JJA peak-block 2025) — picking up the slack. The C1
   fuel-mix baseline the K3 tolerance is measured against belongs to a
   model that no longer exists.
3. **The object changed.** The winter face (Jan+Feb 2025 downstate −$3.92/MWh,
   `_nyiso156_offer_level_phase0.json`) and the companion chain (seam →
   cutset binds → iroquois re-test, nyiso-150 §2.2) were both formulated
   AFTER the rejection; the 2026-08-05 A/B was never scored against them.

The standing kill gates are **unchanged and scored as written** (K1–K7 parent,
K8–K9 addendum 2). If K3 fires again at this HEAD, the R verdict is
re-confirmed on fresh evidence and the cell so re-stamped; nothing in this
note pre-commits the outcome.

## §3 — K6, re-specified onto what it meant (original wording alongside)

* **Original (parent §7):** "K6 — control reproduces. The same-HEAD control
  must reproduce the **nyiso-125 keeper's** C3a to ±0.2 pp, else the
  comparison is invalid and nothing is read."
* **Re-specified (intake spec §1 condition 2):** the same-HEAD zero-delta
  replay of the **CURRENT keeper** `2026-08-25-nyiso-155-hydro-repair`
  (bundle `results/calibration/nyiso155_hydro_repair`, its `meta.json` the
  recipe snapshot) must reproduce that keeper's committed scorecard C3a —
  **+6.8 / −1.7 / −10.8 %** (finding §4.4 / verdict at this HEAD:
  2025 −10.8 % sole C3a FAIL) — to **±0.2 pp per year**. The G1 drift class
  (nyiso-155 §(4): degenerate alternative-optima reshuffle, 2023/2024 annual
  mean +0.016/+0.018 $/MWh) is inside that tolerance and is reported, not
  gated. **The arm is scored against the control, never against the committed
  keeper's bytes.**

## §4 — the two invocations (single-delta channel, rule 12)

```
# control (zero-delta replay of the current keeper recipe)
python3 scripts/replay_keeper.py results/calibration/nyiso155_hydro_repair \
  --out-dir results/calibration/nyiso157_parctl_A \
  --note "nyiso-157 Leg-1 control: zero-delta replay of 2026-08-25-nyiso-155-hydro-repair at HEAD (K6 re-specified)"

# arm (single delta: the PAR seam attribution; supersession of the two-link
# envelope is automatic in run_year — exactly one of the two mechanisms applies)
python3 scripts/replay_keeper.py results/calibration/nyiso155_hydro_repair \
  --out-dir results/calibration/nyiso157_pararm_B \
  --set nyiso_seam_par_attribution=true \
  --note "nyiso-157 Leg-1 arm: + nyiso_seam_par_attribution (standing PREREG nyiso-126 + nyiso-127 addenda; re-test of the nyiso-127 R at the nyiso-155 HEAD under the 2026-08-30 owner ruling)"
```

Both invocations run **concurrently** (two processes), years **2023 2024 2025
sequential within each** (rule 12). Freeze ACTIVE: no other year, no
`--holdout-authorized`. Both runs register whatever the outcome (rule 15).

## §5 — the companion condition, pre-committed measurement

nyiso-150 §2.2's re-open condition for `nyiso_iroquois_winter_spread` (R):
*"re-test as the companion of a locational mechanism that lets the west→east
cutset bind — never alone."* Measured, before results exist, as:

* **Cutset:** the internal `Upstate_West → Capital_Hudson` link — the model's
  Central-East representation (2,850 MW static; the four-zone mainland block
  nyiso-150 proved prices as one).
* **Binding signal (primary, committed-format):** hourly zonal LMP separation
  across that link — `price(Capital_Hudson) − price(Upstate_West)` from
  `hourly/system_<year>.parquet`. Prices are LP duals (rule 4) and internal
  links carry no losses, so any spread is the link's congestion signal.
  Threshold: an hour with spread > $0.50/MWh counts as binding.
* **Corroboration:** the fresh (pre-slim) bundle's persisted `flows` array —
  UW→CH flow at ≥ 99.9 % of its effective hourly bound in the same hours.
* **"Measurably lets the cutset bind in the winter event months"** = in
  Jan+Feb (the winter face's months, all three years reported, 2025 the
  object): the ARM shows a non-trivial binding-hour count (≥ 24 h in
  Jan+Feb-2025, i.e. ≥ 1.7 % of the window) where the CONTROL shows
  effectively none (< 6 h), AND the arm's Jan+Feb downstate gradient moves
  toward the measured $14.83 (nyiso-156 M6) rather than away.
* Only if the arm ALSO passes its own gates does the iroquois companion
  become re-testable, as a second arm with its own prereg section filed and
  blob-verified before it solves (spec §1 condition 3). Neither condition
  alone suffices.

## §6 — what is scored, and the decision rule

Parent §8 unchanged (promotion on rule 1/14 grounds, never on a score; the
named adverse case — C3a-2023 pushed through +10 % — now reads from a 2023
baseline of +6.8 %, leaving 3.2 pp of headroom where the 2026-08-05 test had
2.3). Addendum-2 §6 P1/P2/P3/P4 stand. §9 LOYO consistency is scored from the
A/B results (scorer-side; the shares are constants, so a verdict that flips
on the held-out year indicts the availability read and is a stop). The
nyiso-137 clock caveat governs C3c: arm-vs-control deltas may be relied on,
absolute band verdicts may not. Any determination change is D-5(b)-escalated,
never self-adjudicated; THE OWNER MERGES.

Freeze ACTIVE. Hydro input pair untouched (rule 14; volume tautological under
the 930 pin — declared, never banked). No scarcity parameter anywhere in the
construction (rule 19). Zero fitted scalars; `n_residual` stays 6.
