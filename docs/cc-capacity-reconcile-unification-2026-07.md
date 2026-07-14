# CC capacity reconcile — unification into one measured-capability stack (2026-07)

Executes Part A of `docs/handoffs/pjm-cc-capacity-reconcile-2026-07.md` (A.4
cross-ISO consistency first, then A.1–A.3 the measured-capability stack). This
lands the CC-capacity mechanism as **one ISO-agnostic model** (per-ISO switches
+ data, no `if iso ==` code), not a PJM patch.

## The problem (recap)

A CC plant's LP capacity was set by three overlapping mechanisms in
`fleet_to_bins`, applied in an order that let the weakest-justified bound clip a
stronger one:

1. **Guard** (`fleet._reconcile_cc_pmax_to_nameplate`, always-on, ISO-agnostic):
   clips a fleet-loaded CC pmax sum that exceeds the EIA-860 **nameplate** sum
   (double-file corruption) down to nameplate.
2. **`cc_nameplate_summer_derate`** (flag): rescales net-summer → nameplate.
3. **`cc_capacity_reconcile`** (flag): caps/raises to the **demonstrated CAMPD
   p999 peak** (the measured capability, which can sit above or below nameplate).

The guard ran *before* the reconcile and clipped to nameplate, so a plant whose
measured cold-weather peak sat **above** nameplate lost that measured headroom —
a rule-13 inversion (estimate beating measurement). The canonical case: **New
Covert (55297)** — nameplate 1176 MW, demonstrated peak 1192.4 MW — was clipped
to 1176, discarding 16 MW.

The switches and data had also drifted across ISOs (the A.4 footguns).

## What changed

### A.4.1 — the cross-ISO default-path footgun (rules 24/25)

`ScenarioConfig.cc_capacity_reconcile_path` defaulted to a hardcoded **ERCOT**
table literal, so any flag-off ISO carried `…_ERCOT.csv`; flipping the flag on
without overriding the path silently fed ERCOT's demonstrated peaks to another
ISO — a tuned curve crossing an ISO boundary.

- New resolver `paths.cc_capacity_reconcile_path(iso)` →
  `PROCESSED_DIR/cc_capacity_reconcile_<ISO>.csv`, the single canonical location
  both the config default and the guard use.
- The `ScenarioConfig` default is now `None`, resolved per-ISO in `__post_init__`
  by the run's `iso`. An explicit path still wins. The ERCOT literal is deleted
  (rule 25 — a deprecated default that still parses is re-armable). The default
  ERCOT config resolves to `…_ERCOT.csv` byte-identically, so cache keys are
  stable.

### A.4.3 — the guard's gating: ungated, documented as a validator

The guard is a **data-integrity validator** (an EIA-860 schema bound —
`net_summer ≤ nameplate` — that never discards measured capability), not a
tunable market feature. It is deliberately **always-on and ISO-agnostic, so it
is ungated** (handoff A.4.3 option b). Config is not threaded to
`_rows_to_generators`; inventing that plumbing for a validator would be
over-engineering. The choice is documented in the guard docstring. The
"no-guard control" the re-gate needs is produced at the pre-change git base, not
via a flag.

### A.1–A.3 — the unified measured-capability stack (measured > schema > net-summer)

Per-plant CC capacity now resolves from the most trustworthy available
measurement:

| plant CEMS state | LP capacity | mechanism |
|---|---|---|
| complete CAMPD record | demonstrated CAMPD p999 peak (raise OR cap) | reconcile table + peak-aware guard |
| CT-only / incomplete CEMS | EIA-860 nameplate | guard (peak excluded from table) |
| double-file corruption, no clean CAMPD | nameplate | guard |
| clean, CAMPD absent | net-summer (unchanged) | — |

**Precedence fix — the guard is peak-aware.**
`_reconcile_cc_pmax_to_nameplate` now clips a corrupt CC plant to
`max(nameplate_sum, demonstrated_peak)`, reading `demonstrated_peak` (the
`campd_p999_mw` column) from the plant's own ISO reconcile table
(`_cc_demonstrated_peaks`, cached). Where a plant has a **complete** CEMS record
whose peak sits above nameplate, the guard keeps that measured capability; where
the peak is absent (CT-only) or below nameplate, the bound is nameplate
(unchanged). This is "the guard consults the same demonstrated-peak table" — the
handoff's second suggested implementation — and it changes **only** plants whose
demonstrated peak exceeds nameplate.

**Non-circularity.** The demonstrated peak the guard reads is the pure
measurement (`campd_p999_mw`, from raw CAMPD), never the guard's own output.
The derive (`_model_cc_capacity`) measures the **un-guarded** fleet
(`load_fleet_from_csv(..., apply_cc_summer_guard=False)`), so `current_mw`
matches the original (un-guarded) basis and re-deriving reproduces the existing
cap rows byte-identically instead of oscillating (a guard-restored plant would
otherwise read as "at capacity" and drop from the next re-derive).

**Verified pin (unit test).** Under the keeper config, New Covert (55297) pins
to **1192.4 MW** (was 1176), and CT-only Allegheny 3-4-5 (55710) stays at its
nameplate 556.0 MW. Every other PJM CC plant's final capacity is unchanged by
the guard change. (`tests/test_fleet.py::TestNewCovertDemonstratedPeakPin`,
`::TestCcSummerCapacityGuard`.)

### A.3.2 / A.3.6 — the derive: bidirectional coverage + CT-only exclusion

`scripts/derive_cc_capacity_reconcile.py` gains `--mode both` (full bidirectional
coverage — every CC_REGULAR plant whose demonstrated peak differs from model
capacity in either direction) and three principled screens, all measured / no
residual fit:

- **CT-only exclusion** (`_ct_only_codes`): a plant whose EIA-923 net exceeds
  1.1× its CAMPD gross is an incomplete (CT-only 2×1) reporter whose peak
  understates it — excluded, falls back to the nameplate guard. Same detector as
  `render_calibration_html._flag_ct_only_reporters` (handoff A.3.3).
- **Cap feasibility guard** (retained, `_CAP_FEASIBLE_CF`): an implied annual CF
  > 0.90 at the capped level means the CEMS series is incomplete.
- **Symmetric raise margin**: a raise is credited only when the peak exceeds
  model capacity by ≤ `_CAP_MARGIN` (10%, the same threshold the cap uses). A
  raise *beyond* 10% is not a cold-weather over-rating — it is a data artifact
  (CAMPD contamination from co-located non-CC units, or a fleet-loading
  under-carry) and is skipped and flagged for separate root-cause (rule 11).

### A.3.7 — `cc_nameplate_summer_derate` is NOT deprecated

The unified stack does **not** make `cc_nameplate_summer_derate` collapse. Its
clamp-at-1.0 branch is a no-op for corrupt plants (correctly — the guard now
handles them), but the mechanism is fully alive for **clean** CC plants (e.g.
Bergen: net-summer 1255 → nameplate 1400.8). The clamp
(`cc_summer_capacity: ns_sum = min(ns_sum, np_sum)`) is computed from EIA-860
directly, independent of the guard, and remains necessary to keep the summer
derate ratio ≤ 1. Nothing became a dead re-armable knob, so rule 26 does not
apply — no removal.

## A.4.2 — even out coverage: all six ISOs on the same measured stack

`--mode both` derives were run for the three ISOs that had no table. Every
ISO's CC capacity is now on the same measured demonstrated-peak stack:

| ISO | table | mode | rows (cap / raise) | note |
|---|---|---|---|---|
| ERCOT | ✓ (existing) | raise (curated-bin) | — | CAMPD-bin basis; exempt from re-derive (its bins already bound it) |
| CAISO | **✓ new** | both | 6 / 1 | 4 CT-only excluded |
| PJM | ✓ (re-derived) | both | 17 / 3 | 4 CT-only excluded; keeper re-gate below |
| MISO | ✓ (existing) | cap-only | — | left as-is (static keeper; all peaks < nameplate ⇒ peak-aware guard is a no-op for MISO). Owner may re-derive `--mode both` on the next MISO forward solve |
| NYISO | **✓ new** | both | 12 / 2 | Astoria (55375) excluded (fleet under-carry artifact) |
| NEISO | **✓ new** | both | 10 / 4 | 8 CT-only excluded |

The always-on peak-aware guard reads each ISO's own table (rule 24). For the
existing static keeper bundles this changes nothing (they are not re-solved);
the tables affect only a future forward solve, which is the owner's call. For
MISO/ERCOT the guard is a strict no-op today: every ERCOT peak feeds only the
CAMPD-bin path (not `fleet_to_bins`), and every MISO cap-table peak sits below
nameplate.

## PJM re-derive findings

The `--mode both` PJM table = the existing 17 cap rows **byte-identical** + **3
new raise rows** (measured cold-weather over-ratings, all below their EIA-860
winter rating):

| plant | code | model MW | peak MW | Δ | note |
|---|---|---|---|---|---|
| Hamilton Patriot | 58426 | 870.0 | 882.4 | +1.4% | raise |
| Waterford | 55503 | 921.6 | 952.3 | +3.3% | raise |
| Bear Garden | 56807 | 628.2 | 656.2 | +4.5% | raise; 2nd rule-13 inversion (net-summer 628 > nameplate 559; guard had clipped it to 559, discarding real capability). Handoff A.3.5 anticipated 56807 changing |

**Excluded as artifacts (flagged for separate root-cause, rule 11):**

- **Chesterfield (3797)** — CAMPD peak 993 MW vs winter 465 MW: the plant series
  is contaminated by co-located coal units (Dominion Chesterfield is mixed).
- **CPV Fairview (60589)** — CAMPD peak 1079 MW vs model CC 725 MW / EIA-860
  net-summer 1057 MW: the model **under-carries** the plant by ~330 MW (a
  fleet-loading gap, not a cold over-rating). Raising to the peak would paper
  over that gap — a separate fleet investigation.
- **CT-only** (understated peaks): Ironwood 55337, Fremont 55701, Allegheny 3-4-5
  55710, Hunterstown 55976.

New Covert (55297) remains a **cap** row (un-guarded phantom 1586 > 1.1×1192);
the peak-aware guard restores it to the measured 1192.4 and the cap row confirms.

## Re-gate (PJM keeper) — plan

Re-solve `pjm-110`'s recipe verbatim (`scripts/probes/_pjm107_gas_daily_probe.py`,
years 2023–2025) with the unified stack, plus a pre-change control at base to
isolate the change from codebase drift. Expected PJM dispatch deltas vs pjm-110
(all measured rule-13 corrections):

- New Covert (55297): 1176 → 1192.4 MW (+16, via peak-aware guard + cap row)
- Bear Garden (56807): 559 → 656.2 MW (raise row; the 2nd inversion)
- Hamilton (58426): 870 → 882.4 MW (raise)
- Waterford (55503): 921.6 → 952.3 MW (raise)

Gate within-noise of pjm-110 on every scored criterion. Zero-DOF (measured CAMPD
input; no ablation twin per rule 20). `keepers.json` is owner-only — the
promotion is flagged, not flipped.
