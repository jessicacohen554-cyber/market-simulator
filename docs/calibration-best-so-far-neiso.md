# NEISO calibration — best config so far

> **DETERMINATION: CALIBRATED-WITH-CAVEATS.** Current keeper
> `2026-07-09-neiso-56-reserve-coopt` (bundle
> `results/calibration/neiso56_reserve_coopt`, years 2023/24/25; ablation twin
> `2026-07-09-neiso-56-coopt-ablation`). **NEISO calibration-complete** was
> declared 2026-07-07 (`frontend/data/backcast/calibration-complete.json`).
> **FRONTIER-ACHIEVED** was declared 2026-07-11 for the C3c/C5b winter
> scarcity-price-formation family (§3). This supersedes the stale
> `neiso-49-stgas-netload` / "NOT-YET" text this file carried until 2026-07-11.

## 1. Reconciling the three keeper pointers

Three files name a NEISO "keeper" and they legitimately point at three
different run ids — this is not drift, it is three different questions:

| Source | Field | Value | What it answers |
|---|---|---|---|
| `frontend/data/backcast/keepers.json` | `.NEISO` | `2026-07-09-neiso-56-reserve-coopt` | **The live dashboard/train-tier keeper today** — the newest, most structurally faithful 2023–2025 run. |
| `frontend/data/backcast/keepers.json` | `.frontier.NEISO.note` | names `2026-07-09-neiso-56-reserve-coopt` | Same run — the frontier note is written against the current keeper. |
| `frontend/data/backcast/calibration-complete.json` | `.complete.NEISO.keeper` | `2026-07-08-neiso-54-steamgas-ct` | **The train-tier keeper frozen at the moment calibration-complete was declared** (2026-07-07/08) — irrelevant to which run is live today. |
| `frontend/data/backcast/calibration-complete.json` | `.complete.NEISO.locked_test_scored_on` | `2026-07-07-neiso53-winter-fuelsec-coldsnap` | **The exact config the rule-22 locked-test one-shot (2019 + H1-2026) was scored against, once, ever.** |

Why they diverge: `calibration-complete.json`'s `keeper` field is a
point-in-time freeze, not a live pointer — rule 22 forbids ever re-scoring the
locked test, so that field records the config the one-shot result is
attributable to, and does not update when the train-tier keeper is later
superseded. The lineage since declaration:

- **neiso-53** (`2026-07-07-neiso53-winter-fuelsec-coldsnap`) — the config
  actually adjudicated in
  `docs/handoffs/neiso-calibration-complete-memo-2026-07.md` and the config
  the locked-test one-shot is (and forever will be) scored against
  (`locked_test_scored_on`).
- **neiso-54** (`2026-07-08-neiso-54-steamgas-ct`, "CT_PEAKER evening-ramp
  reliability drag + ST_GAS→Component-B consolidation") — promoted the very
  next day as the new train-tier keeper: "more structurally faithful (rule 1)
  with an identical 2023-2025 verdict and no winter degradation" than
  neiso-53 (`calibration-complete.json` `locked_test_note`). **The locked-test
  result was NOT re-scored for neiso-54** — per rule 22 it stands as scored
  against neiso-53 only. This is the run frozen in the `complete.NEISO.keeper`
  field.
- **neiso-55** — superseded neiso-54 as train-tier keeper in a later session
  (per `docs/calibration-log.md` 2026-07-09 entry, "keeper stays neiso-55"
  going into that day's probe).
- **neiso-56** (`2026-07-09-neiso-56-reserve-coopt`) — the neiso-55 recipe
  plus in-LP energy+reserve co-optimization (`energy_reserve_coopt=True`,
  ISO-NE's published 3-level nested RCPF demand curves, storage
  reserve-eligible), promoted to keeper 2026-07-09 per rule 1 (ISO-NE really
  clears energy and reserves jointly) even though the mechanism is DORMANT on
  2023–2025 — this is today's value in `keepers.json` and the subject of the
  `frontier.NEISO` note.

**Net:** `keepers.json` (train-tier, live) and the frontier note both correctly
say **neiso-56**. `calibration-complete.json` correctly says **neiso-54**
because that field freezes what was true when calibration-complete was
declared and is pinned to the **locked-test scoring config (neiso-53)**, which
per rule 22 can never be re-spent. All three are internally consistent once
read for what each actually records.

## 2. Calibration-complete status (declared 2026-07-07)

Per `frontend/data/backcast/calibration-complete.json` `.complete.NEISO`:

- **Declared:** 2026-07-07, by owner (session `neiso-calibration-complete-w1c`,
  `AskUserQuestion`: "Declare + run one-shot"; memo
  `docs/handoffs/neiso-calibration-complete-memo-2026-07.md`).
- **Locked-test scored on:** `2026-07-07-neiso53-winter-fuelsec-coldsnap`. The
  2019 + H1-2026 locked-test one-shot was scored ONCE with the frozen neiso-53
  config and STANDS (rule 22); it was **not** re-scored for neiso-54 (or for
  neiso-55/56 since).
- **Train-tier keeper promoted:** 2026-07-08 (session
  `neiso-steamgas-ct-drag`), i.e. neiso-54 superseding neiso-53 as the
  2023–2025 keeper the day after the marker was written.
- **One-shot 2022 holdout execution: HELD.** Per the memo §6, the owner
  authorized the full declare→intake→precheck→solve-once path on 2026-07-07,
  then the *same day, later*, held **execution** of every ISO's one-shot
  pending a cross-ISO holdout data-equivalency gap register (G-19). The NEISO
  2022 intake stands (`calibration-complete.json` `intake_log`), the
  declaration and marker stand, but the 2022 solve itself has not run.

## 3. FRONTIER-ACHIEVED (verbatim, `keepers.json` `.frontier.NEISO`)

> Declared 2026-07-11.
>
> "Frontier achieved: every named admissible mechanism for the ledgered
> C3c/C5b winter/summer scarcity-price-formation family has been tried on
> record — winter fuel-security stack (adopted, dormant), in-LP reserve
> co-optimization (keeper, dormant at static requirements), measured dynamic
> reserve requirements (Limb A, engages 1 of 12 2025 tail hours), and the
> measured fast-start DA offer surface (Limb B, dormant — the real tail forms
> while the model still carries cheaper non-fast-start headroom). Further C3c
> work needs a NEW measured identification (oil-parity/import/DA-bid offer
> formation), its own charter; C2 waits on the final 2025 EIA-923 vintage.
> 2026-07-11 calibration-log entry; docs/handoffs/neiso-limb-b-offer-surface-2026-07.md §5."

Practically: do not open a new C3c/C5b structural mechanism session against
these backcast years without a genuinely new measured identification per the
note above — the admissible-mechanism inventory for this family is exhausted.

## 4. What the keeper (neiso-56) is, and what it carries forward

The last full scoring on record in the specified sources is the neiso-53
adjudication in the memo (§2 of
`docs/handoffs/neiso-calibration-complete-memo-2026-07.md`), which reproduces
at HEAD as **CALIBRATED-WITH-CAVEATS, zero criterion FAILs**:

- **Caveat budget (rubric v2.2 at the time):** ledgered 2/3 (C3c price tail /
  C5b storage throughput — both classified, same winter scarcity-price-
  formation root), protective 0/1 (C7 SKIPPED-immaterial). Commercial-band
  auto caveats: C2 2025 gas +2.8% (preliminary EIA-923 vintage — not closable
  by dispatch); C3a 2023 −6.0% (2024 −4.0% and 2025 +0.8% PASSING); C3b 2024
  NRMSE 0.157 (2023/2025 passing). C1, C4, C5a, C6 PASS.
- **Known text-lag (disclosed in the memo, not gating):** the sidecar was
  stamped `rubric_version: 2.1`; HEAD's scorer emits 2.2, whose only addition
  (the C8 above-cap grounded-pass path) this keeper never engages (C8 passes
  below-cap anyway).

neiso-54/55/56 each superseded the prior train-tier keeper on rule-1 structural
grounds without moving this caveat picture: per `docs/calibration-log.md`'s
2026-07-09 entry, the neiso-56 reserve co-optimization probe scored
"CALIBRATED-WITH-CAVEATS with the identical caveat set as the keeper" it
replaced, and the mechanism itself is decisively dormant — the reserve
balance dual is $0.00 in all 26,280 hours of 2023–2025 on both the main run
and its zero-forcing ablation twin, C3c tail unchanged at 0h >$300 every year,
and C5b storage discharge byte-similar to the prior keeper (0.579/0.521/0.827
vs 0.578/0.521/0.828 TWh). It was kept anyway per rule 1 (the winter-fuel-stack
precedent: a real ISO-NE clearing structure, forward-live in a tighter fleet),
with LOYO trivially satisfied because the deltas are ≈0.

## 5. Locked-test status (rule 22 — touch-once)

- **2019 + H1-2026:** scored EXACTLY ONCE, against the frozen neiso-53 config,
  on 2026-07-07. Stands untouched since; will **never** be re-scored against
  neiso-54/55/56 or any future keeper (a locked-test year re-solved after its
  one-shot would be a governance breach, not a CI failure — CLAUDE.md rule 22).
- **2022 (validation, iterable):** intake done, one-shot execution HELD
  pending the cross-ISO data-equivalency gate (G-19) per memo §4/§6 — not yet
  run.

## 6. Reproduce

```
python scripts/calibration_verdict.py results/calibration/neiso56_reserve_coopt
```

Note (memo §4): reproducing the *locked-test-scored* neiso-53 recipe at HEAD
requires `--enable-legacy-p2` — its `--commitment` pass predates the P2
archival (`5b86685`, one day after neiso-53's solve commit); this is frozen-
recipe reproduction, not a new calibration choice.
