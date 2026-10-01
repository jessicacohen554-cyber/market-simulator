# FINDING — neiso-78: NEISO's rule-28(c) matrix column is CLOSED (10 absent / 8 armed-with-no-cell → 0/0), and the census surfaced one live defect: `neiso_oil_burn_budget` is armed on every NEISO bundle ever registered and is UNREACHABLE on all of them

**Date:** 2026-08-03 · **Scope:** NEISO + the shared-field column, rule 28(c)
`[R-MECH-MATRIX]` duty (c) · **NO LP was solved, no keeper changed, no bundle
was produced, no dashboard registration was made** (rule 15 governs completed
runs and there is none). **Keeper:** `2026-08-03-neiso-caiso156-meter-screen`,
untouched.

**Probes (committed):**
`scripts/probes/_neiso78_oil_budget_reachability.py` (the `ast` precedence
proof + the all-ISO bundle census; idempotent, read-only).
**Records:** `PROBE-neiso78-matrix-gap-census-2026-08-03.txt`,
`PROBE-neiso78-oil-budget-reachability-2026-08-03.txt`.

---

## §0 — the fork, and why this box

The neiso-78 prompt offers two forks. **Fork A** (§5.6 item 5b, the
stack-traversal charter neiso-76 requested) **requires an owner green-light
and none was in hand**, so under §5.6 frontier discipline it stays unopened.
Fork B directs this session to the highest-value **non-owner-gated** box on the
cross-ISO queue.

**ERCOT was checked first and does not offer one.** It is the only NOT-YET ISO
and therefore the highest-value calibration lane, but all three of its live
queue items are gated:

| ERCOT item | status | gate |
|---|---|---|
| 9 — `energy_online_capability_cap` (the ERCOT-155 named successor) | UNCHARTERED | owner authorization required; it is a structural LP change |
| 8 — CT-band re-identification intake | data-intake first | three parts, **each explicitly owner-authorized** |
| 7 — WP-B nodal curtailment layer | data-intake first | the station→area crosswalk does not exist in-repo, **and neither does the source**: `data/raw` holds curtailment corpora for CAISO, MISO and NYISO but nothing nodal for ERCOT (only the single `reference/ercot_wtx_curtailment_share.csv`) |

So the highest-value ungated box is in this session's own lane. §5.7's
`matrix_gap_census` row records that NYISO (nyiso-114) and ERCOT (ercot-156)
have closed their rule-28(c) columns and that **"the other five columns hold
146 enumerated gaps and are their own lanes' work (rule 25/28(d))"**. NEISO's
share was **10**. Closing it is zero-LP, puts no keeper at risk, is
CI-ratchet-verifiable, and rule 28(c) is explicit that a mechanism missing from
the matrix **"is an unregistered tuning channel in spirit (rule 24)"** — this is
governance debt, not bookkeeping.

**Correction to the prompt's status line, against interest.** The prompt states
the NEISO keeper is `2026-07-31-neiso-72-hy-window`. It is not: the shard
`frontend/data/backcast/keepers/NEISO.json` designates
**`2026-08-03-neiso-caiso156-meter-screen`** (neiso-72 SUPERSEDED-NOT-RETRACTED
at caiso-159, 2026-08-03, which changed only the shared measured CT heat-rate
artifact's content). Every number below is read against the *current* keeper.

---

## §1 — the census result

`scripts/mechanism_matrix_gap_sweep.py --iso NEISO`, before → after:

| measure | before | after |
|---|--:|--:|
| family fields (`neiso_*`) | 20 | 20 |
| **ABSENT from the matrix** | **10** | **0** |
| prose-only | 0 | 0 |
| **ARMED ON THE KEEPER WITH NO CELL ANYWHERE** | **8** | **0** |
| shared-gap (`shared_armed_on_keeper`) | 0 | 0 |
| **live-but-invisible** (non-default in a bundle, no matrix mention) | **1** | **0** |

**NEISO is now the third ISO with a fully closed column**, after NYISO
(nyiso-114) and ERCOT (ercot-156). The full six-ISO sweep confirms **no other
column grew**: CAISO 0/5, ERCOT 0/14, MISO 11/17, NYISO 0/0, PJM 15/18
(absent / shared) — identical to the committed baseline. The ratchet
`docs/codebase-site/data/mechanism-matrix-gaps.json` was regenerated and the
diff is **shrink-only**, exactly the ten NEISO entries.

### What the ten actually were — all registrations, no invented verdicts

Every one was a **literal-name registration on an existing family row**, the
nyiso-114 / ercot-156 escape-hatch template. **No matrix row was added, no cell
verdict was flipped, and no `U` was minted** — rule 25 bars a census from
adjudicating, and none of these needed it, because each field's owning row
already carried the correct per-ISO verdict:

1. **`gas_coldsnap_derate` row** (NEISO cell `K`) — the three shape sub-scalars
   `neiso_gas_derate_t0_c` / `_slope_per_c` / `_cap` registered literally, at
   their shipped NERC-anchored defaults (−7.0 °C ≈ 20 °F cold-limb
   zero-crossing; slope = cap/(t0 − T_extreme) = 0.018 per °C; 0.20 cap from
   the Winter Storm Elliott gas fuel-supply share). The row's stale `:2138`
   line reference is corrected to `:2878`.
2. **`winter_fuelsec_posture` row** (NEISO cell `K`) — six fields registered:
   Component A `neiso_winter_fuel_inventory` + its sizing scalar
   `neiso_winter_fuel_start_fill_bbl`; Component B's three sub-scalars
   `neiso_winter_fuelsec_min_stable_pct` / `_commit_frac` / `_tmin_c`; and the
   superseded `neiso_oil_burn_budget` (§2). The row's stale `:2286` is
   corrected to `:3026`.
3. **`dam_availability_rebasis` row** (NEISO cell `R`) —
   `neiso_operable_capacity_availability`. The `def` previously carried the
   **truncated stem** `neiso_operable`, which no literal-match census can
   resolve. The `R` verdict is neiso-62's ("operable-capacity source NOT
   ADOPTED — fleet-wide denominator on thermal-only application") and is
   unchanged.

### The eleventh: a SHARED field with no matrix mention at all

The live-but-invisible slot held `unit_partial_outage_windows` — a shared
(non-ISO-prefixed), solve-affecting, `GATED CHANGE` availability flag,
non-default on the committed `neiso69_shortpartial` bundle. Its owning row
`unit_outage_short_windows` referenced it only as a **bare parenthetical line
number** (`scenarios.py:7771 (+partial windows :7796)`) — *both numbers stale*
(the fields are at `:9419` and `:9444`) and neither resolvable by name, so the
shared-field sweep read the flag as having **no matrix mention anywhere**.
Registered literally; the row's NEISO cell `R` (neiso-69, rejected on
provenance) is unchanged. This one was not in NEISO's ten — it is a
**cross-ISO** gap this session found while closing them, and it is the same
failure mode nyiso-115's shared-field census was built to catch.

---

## §2 — the live defect: an armed mechanism that has never once built a row

Two of the eight armed-with-no-cell fields are `bool` gates the keeper arms
**away from their shipped `False` default** — the nyiso-112 "live-but-invisible"
shape, the exact class that hid a promotable mechanism from every session:

* `neiso_winter_fuel_inventory` = `True`
* `neiso_oil_burn_budget` = `True`

Both feed the **same** LP builder — `model/lp/rows.py::_build_oil_budget_rows` —
through the same `oil_*` dispatch kwargs. Rule 19 `[R-ONE-MECH]` therefore asks
whether arming both **double-counts** the winter oil-burn constraint.

**It does not, and the reconciliation is already in the wiring.**
`scripts/run_calibration.py:4250` is a single `if`/`elif`: the `if` gate is
`neiso_winter_fuel_inventory`, the `elif` gate is `neiso_oil_burn_budget`. The
successor wins and the superseded F923 limb is **unreachable whenever it is
armed**. Proven mechanically rather than read off the comment — the probe
parses the file with `ast` and asserts the two gates are the test and the
`orelse` test of *one* `If` node (two independent `if`s would double-count):

```
[1] SOURCE-LEVEL PRECEDENCE (ast over scripts/run_calibration.py)
  if-statement line          : 4250
  if   gate                  : neiso_winter_fuel_inventory
  elif gate                  : neiso_oil_burn_budget
  single if/elif chain       : True
  VERDICT                    : NO DOUBLE-COUNT — the superseded limb is
                               unreachable whenever the successor is armed
```

**The bundle census makes it stronger than "usually inert".** Across every
committed `run_config.json` in the repo:

| | count |
|---|--:|
| bundles recording the field (all six ISOs) | **120** |
| NEISO bundles | **15** |
| NEISO bundles arming **both** gates | **15 / 15** |
| bundles in which the F923 limb is **REACHABLE** | **0 / 120** |

`neiso_oil_burn_budget` is NEISO's **backcast default** — `backcast_config.py:1549`
sets it `(iso.upper() == "NEISO")` unconditionally — which is why it reads as
armed on all 15. It has **never once built a row**, on any bundle, in any ISO.
Its matrix status is therefore inert-by-precedence, recorded in the
`winter_fuelsec_posture` note; the row's `K` cell continues to describe the
**adopted** limbs (must-run + Component A inventory), which is what it always
meant.

### Reported against interest

The `scenarios.py` docstring for `neiso_oil_burn_budget` says it is "**not a
keeper path**". **That claim is false as written against the current keeper** —
the field is `True` there. It is *unreachable*, not *unarmed*, and the
distinction matters: an unarmed flag cannot be re-armed by a config change,
whereas this one is already on and would begin building rows the moment a
bundle turned its successor off. The comment describes the intent correctly
and the state incorrectly.

---

## §3 — FILED NOT FIXED, and routed to the owner

**The F923 limb is a rule 26 `[R-DELETE]` candidate.** Rule 26 says deprecated
knobs are *removed, not zeroed* — "a deprecated parameter that still parses is
a re-armable answer key". This one is worse than parsing: it is **armed by
default**. And its own docstring records why it is inadmissible on the merits —
the budget derives from EIA-923 petroleum **receipts**, "a measured
deliveries-to-tank OUTCOME … no forward analogue; the dispatch validated is not
the dispatch forecast", i.e. a rule 13 `[R-MEASURED]` failure. It is exactly the
shape rule 26 exists to delete.

**This session does not delete it**, for two reasons, and neither is
squeamishness: (a) deleting it touches a **NEISO backcast default** in
`backcast_config.py`, which is a solve-affecting recipe change and not a
census's call; (b) it is the same cross-lane shape nyiso-115 raised and
deferred for `campd_facility_outages` ("a flag documented dead that still
parses … belongs to a cross-lane decision rather than to a NYISO calibration
session"), and nyiso-114 made deletion affordable via
`_CACHE_KEY_RETIRED_FIELDS`. **Two rule-26 candidates now sit in the same
queue**; they should be decided together, and the owner should decide them.

**A second, smaller filing.** The census's ability to see a field depends
entirely on the `def` string carrying its **literal name**. Three of the four
registrations in this session were fixing `def`s that named a field by a
truncated stem or a bare line number — and **every line number encountered was
stale** (`:2138`→`:2878`, `:2286`→`:3026`, `:7771`/`:7796`→`:9419`/`:9444`).
Bare line numbers rot silently and are invisible to the ratchet. Recommendation,
not enacted: `check_mechanism_matrix.py` could assert that any `scenarios.py:N`
reference in a `def` resolves to a line actually defining a `ScenarioConfig`
field. That is a CI change and belongs to whoever owns the gate.

---

## §4 — governance

Years 2023–2025 only; **no year outside the training window was read**. The
holdout spend freeze is untouched; NEISO's locked test remains SPENT and
untouched (rule 22). **No LP was solved**, no `ScenarioConfig` field was added,
removed or changed, no default was altered, no derive was re-run, no keeper
moved, no bundle was written, and no dashboard registration was made. The only
committed artifacts are the matrix `def`/`note` strings, the shrink-only
ratchet baseline, one new read-only probe and its two records.

**Matrix duty (b)** is discharged in-session: four rows touched
(`gas_coldsnap_derate`, `winter_fuelsec_posture`, `dam_availability_rebasis`,
`unit_outage_short_windows`), all `def`/`note` only. **No cell verdict was
changed anywhere in the file** — verified: `winter_fuelsec_posture` `U..U.K`,
`gas_coldsnap_derate` `U..U.K`, `dam_availability_rebasis` `KUGR.R`,
`unit_outage_short_windows` `IIKKIR`, all as committed. CI gates pass
(`check_mechanism_matrix.py`: integrity OK, keeper stamps match every shard).

**DO-NOT-REDO.** Do not re-run the NEISO column census by hand — the sweep
does it in ~1 min (`--iso NEISO`) and re-scores automatically on a keeper swap.
Do not re-litigate the oil-budget precedence: the `ast` proof is mechanical and
the probe re-runs it. **Do not "fix" `neiso_oil_burn_budget` by flipping the
`backcast_config` default to `False`** — that is a solve-affecting recipe change
to a keeper's recorded config, it would alter no dispatch (the limb is already
unreachable) while invalidating the recorded recipe of 15 bundles, and the
rule-26 answer is deletion, which is the owner's call.

**This licenses nothing.** No mechanism was adopted, demoted or re-scoped; no
parameter was introduced or re-derived; the NEISO frontier declaration and the
C3c owner routing (CHARTER-neiso75 §5) are exactly where neiso-76 left them.
