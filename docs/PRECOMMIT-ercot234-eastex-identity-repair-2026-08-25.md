# PRECOMMIT — ercot-234: the card-Z-A `NE_LOB`→`EASTEX` identity repair — instrument, boundary rule, gates and promotion protocol, fixed BEFORE any derivation or solve

**Date:** 2026-08-25 · **ISO:** ERCOT · **Authorization:** card Z SIGNED
**(Z-A)** with the owner's advance promotion standard
(`docs/DECISION-CARD-ercot234-nelob-identity-repair-2026-08-24.md`
RESOLUTIONS). **This document is pushed and blob-verified BEFORE the EASTEX
static is computed, before any phase-0 boundary evidence is adjudicated, and
before any solve.** The only EASTEX numbers known at push time are the
survey's descriptive reads (FINDING-ercot234 §II.3: active/binding counts and
limit p50s) — the DERIVED static statistic has not been computed.

Evidence basis inherited:
`docs/FINDING-ercot234-subzonal-survey-nelob-identity-2026-08-24.md`.
Keeper at start: `2026-08-24-231-tie-zone-measured`
(`results/calibration/ercot231_tiegtc_full`), 2023 −38.0 % / 0.696 / 93 ·
2024 +0.4 % / 0.130 / 22 · 2025 −7.7 % / 0.099 / 1, NOT-YET on
{C3a-2023, C3b-2023}.

## P-1 Instrument reproduction (STOP-class)

The static statistic is `derive_ttc_limits.py`'s: **mean `Limit` over
binding rows (`ShadowPrice > 0`)** among GTC rows (empty `FromStation`),
pooled over the **2023+2024** archives — the window `iso_configs` cites for
the seeded statics. The archives are now the yearly
`SCEDBTCNP686_*.parquet` files (same product; the script's `*.zip` glob
predates the parquet conversion — a source-FORMAT accommodation only, no
statistic change). Reproduction gate: the statistic re-run on the parquet
form must reproduce the seeded statics within **±1.5 %** — WESTEX ≈ 10,000
(pre-split), PNHNDL ≈ 2,680, NE_LOB ≈ 1,300. A miss **STOPS** the
derivation and escalates (it would mean the parquet record ≠ the zip-derived
record that seeded the topology).

## P-2 Static rule (rule 23, source-data-cited)

`Northeast→North` export `ttc_mw` := EASTEX mean-limit-at-bind pooled
2023+2024 per P-1's statistic, rounded to the nearest 10 MW; per-year values
(2023/2024/2025) reported for context. Never revisited on a residual. The
import link (`North→Northeast`, 1,788 MW — the ERCOT-76 pooled dark-hour
envelope, genuinely NE-Texas data) is **unchanged**.

## P-3 Boundary reconciliation rule (phase 0, Z-B fallback live)

EASTEX qualifies as the model's Northeast→North boundary iff:
(a) ERCOT's definition identifies it as the East-Texas-area export
constraint — already in hand ("a voltage stability limit associated with
flows out of the East Texas area", GTC Workshop definitions 2020-02-24); AND
(b) at least one further public source corroborates its area or elements
(Constraints & Needs report, SOM, market notice, ROS/workshop material)
without placing its boundary materially inside a DIFFERENT model zone.
- (a)+(b) met → **Z-A**: hourly overlay armed (`EASTEX` →
  `(("Northeast","North"), 1.0)`).
- (b) unmet or elements ambiguous → **Z-B**: NO hourly overlay for the link;
  the static still re-derives per P-2 (the definition alone identifies the
  area; only element-grain confidence gates the overlay).
- (a) contradicted (not expected — it would contradict ERCOT's own
  definition) → STOP, escalate.

## P-4 Repair spec (zero fitted scalars, no `ScenarioConfig` field — 28(c) not engaged)

`NE_LOB` is REMOVED from `ERCOT_GTC_LINK_MAP` (an intra-South pocket, the
VALEXP class — the model's own map places the Rio Grande Valley inside
South); `EASTEX` is added per P-3's verdict; no other map entry moves. The
"NE_LOB = NE-Texas export" glosses are swept from live comments
(`iso_configs`, `constants`, `gtc.py`, `derive_ttc_limits.py`,
`transmission_expansion.py`, `zone_assignment.py`, `zonal_shares.py`,
`scenarios.py`) with citations to the FINDING; historical
FINDINGs/log entries are NOT rewritten.

## P-5 Solve plan

- **Arm:** `replay_keeper.py` on the ercot231 bundle's `meta.json` at
  repaired HEAD → `results/calibration/ercot234_eastex_identity`, years
  2023 2024 2025 **sequential** (rules 12/16).
- **Control = the committed keeper bundle BY IDENTITY.** Drift audit
  `c9a07b9..HEAD` over `src/market_sim`, `scripts/run_calibration_full.py`,
  `scripts/replay_keeper.py`, `scripts/lib`: exactly two files —
  `config/paths.py` (+1 MISO directory constant, no ERCOT path) and
  `runner.py` (a diagnostics-gate expression, byte-identical at default
  flags per its own comment, forecast-entry-screen code besides). Both
  provably inert for a backcast replay at the keeper's flags, so no control
  re-solve is run.
- The official scorer (`scripts/probes/ercot226_official_score.py`) is
  validated with `--validate-keeper` against the keeper bundle BEFORE
  scoring the arm.

## P-6 Gates

STOP-class (fire ⇒ no promotion, escalate to the owner; the run is still
registered per rule 15):
- **G-SHED-NEW:** any shed hour not in the keeper's own per-year shed sets.
- **G-COAL148-GROSS:** ERCOT coal generation rise vs keeper > **2.0 TWh** in
  any year (gross physical implausibility; 4× the standing 0.5 TWh bar).
- P-1's instrument-reproduction miss.

Report-class (recorded at full magnitude; promotion proceeds under the
owner's advance standard even where they regress — rule 14 explicitly
instructs keeping the accurate input when the fit worsens):
- **G-COAL148:** coal rise vs the standing 0.5 TWh bar (named in the
  promotion record if exceeded — a real residual the phantom 1,300 MW cap
  was compensating).
- **G-SPUR:** per-year banded count vs the keeper's (2023: 21 known), PLUS
  the lidless band/top decomposition (the unsigned ercot-225 card's form) so
  either later gate ruling reads cleanly.
- **G-C3c:** per-year model tail counts vs actual 181/53/31 (keeper 93/22/1).
- **G-SPAN:** max class annual-energy move, named if any class moves > 2 %
  of ISO load.
- **G-OWNER guard years:** C3a/C3b 2024 and 2025 PASS/FAIL status; if BOTH
  guard years exit their C3a bands, escalate before promotion.
- **G-DOF:** ledger `n_residual` not increased (this repair adds zero
  parameters; the re-derived static is a rule-23 measured constant).
- **G-D2:** no new D-4 FAIL row.
- **Q-B/R-A side-effects:** C3a/C3b/C3c-2023 at full magnitude — reported,
  never the basis.

## P-7 Promotion protocol

No STOP leg fired ⇒ the arm is promoted per the owner's in-advance signature
("If structural integrity improves but gates regress that may still be a
keeper"), with the mechanical gate verdict recorded unrewritten beside the
promotion basis (the ercot-215/221/231 pattern). Run id
`2026-08-25-ercot234-eastex-identity`; registration, keeper re-key, matrix
§5.1 + ERCOT-shard stamps, and `audit_keepers` follow in the same session.

## Fences

Years ⊂ {2023, 2024, 2025} (rule 22); ERCOT-only (rule 25); Q-B/R-A stand;
the ercot-233 zonal-grain closure, `internal_congestion_split` `G`, and the
ercot-231 tie placement are not re-tested; the ercot-225 gate card stays a
separate signature; no CI jobs. The ercot-188/E2 P0 bit-identity forfeiture
is inherited unexpired (this repair is not an offer-surface change; the P0
seam is untouched, but no P0 bit-identity claim is made).
