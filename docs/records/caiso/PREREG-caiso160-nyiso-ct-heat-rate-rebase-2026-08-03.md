# PREREG — caiso-160 / NYISO: CT heat-rate meter screen re-based onto the nyiso-113 keeper

**Session:** caiso-160 · **Date:** 2026-08-03 · **ISO:** NYISO
**Lane:** cross-ISO CT heat-rate meter screen (caiso-156 → 158 → 159)
**Charter:** caiso-159 §8 follow-up item 1 — the one lane caiso-159 could not close.

Written and committed BEFORE any arm solves (caiso-139..159 precedent).

---

## 1. Why this run exists

The caiso-156 fix (`f6238a5`) applies the CT heat-rate derive's own declared
physical band `[6.0, 25.0]` MMBtu/MWh **at the hour**, not only at the plant
aggregate. It is a rule 14 `[R-ACCURATE]` **input correction with zero
`ScenarioConfig` surface** — not a mechanism, so no matrix cell changes verdict
on it (caiso-158 §7).

caiso-158 ran the A/B in three ISOs. caiso-159 promoted CAISO and NEISO.
**NYISO could not be promoted**, for a reason that is itself the lane's newest
pipeline rule:

> An A/B is only promotable against the keeper it was **controlled on**.

The caiso-158 NYISO arms were baselined on `nyiso112_rampplus_peaker`. While they
solved, nyiso-113 promoted `2026-08-02-nyiso-113-li-locational` underneath them.
Measured drift, arm B vs the current keeper (`config_drift`, absence-aware):

```
value_diffs : nyiso_li_locational_reserve   arm=False   keeper=True
arm_only    : []
keeper_only : []
```

Exactly one disqualifying field. Promoting that arm would **drop a published
NYISO Long Island (Zone K) locational reserve requirement** in order to gain an
input correction — a rule 14 regression committed in the name of rule 14. The
"gates may regress if structure improves" allowance does not rescue it: that
candidate *removes* structure while the gates stay flat.

This run re-solves the treatment on the **nyiso-113 recipe** so the two changes
compose instead of competing.

---

## 2. The input delta, measured (not restated)

`data/raw/_processed-legacy/campd_ct_heat_rates_NYISO.csv`, pre-fix
(`f6238a5^`, md5 `749f4ffff41f`) vs post-fix (HEAD, md5 `6fb854399825`):

| | pre-fix | post-fix |
|---|---|---|
| plant rows / applied (`flag=='ok'`) | 19 / 19 | 19 / 19 |
| applied class capacity | 2,395.2 MW | 2,395.2 MW |
| **cap-weighted applied net HR** | **12.0769** | **12.4355** (+0.3586) |
| unit rows | 80 | 79 (drops 2494 CT03-6) |

**The movement is ONE-SIDED DEARER: 17 plants dearer, 0 cheaper, 2 unchanged**,
and **no plant changes flag**. Two plants move > 0.5 MMBtu/MWh — Gowanus
15.2804 → 16.9538 and Narrows 15.7537 → 16.7814, both NYC in-city oil/gas CTs
whose sub-6.0 loaded hours were diluting the meter low.

NYISO carries the **largest cap-weighted movement of all six ISOs** (+0.359,
against CAISO +0.176, NEISO +0.171, PJM +0.069, ERCOT +0.063, MISO +0.030).

---

## 3. Arms — and why a control arm IS re-solved here

The caiso-159 handoff states "NO CONTROL RE-SOLVE NEEDED — `nyiso113_lilocational_B`
IS the control." **That premise does not hold at this HEAD and is not relied on.**
The keeper solved at `3746eda` / `2026-08-02T22:59:52`; **seven `src/market_sim`
commits have landed since**, two of which touch paths this ISO uses
(`a0fc302` deletes the CT_CHP override triple and re-scopes `caiso_ra_min_load_frac`;
`9a54412` moves the reserve balance-row activity inside the co-opt branch).

Each is *documented* solve-inert. But "documented inert" is exactly what failed
in CAISO: caiso-146 recorded that the outgoing keeper's committed sidecars **no
longer reproduced at HEAD**, diverging up to 2.1/1.7/3.2 GW on a class-hour after
a comparable run of "inert" commits, cause still unidentified. Comparing a fresh
arm against a bundle solved at a different HEAD would confound the CT correction
with that drift and there would be no way to tell them apart afterwards.

So both arms solve at **this** HEAD (`195ff18`), differing **only** in the bytes
of the CT artifact:

| arm | recipe | CT artifact | bundle |
|---|---|---|---|
| **A** control | nyiso-113 keeper config, zero delta | **pre-fix** (`f6238a5^`) | `nyiso160_ctmeter_control_A` |
| **B** treatment | nyiso-113 keeper config, zero delta | **post-fix** (HEAD) | `nyiso160_ctmeter_screen_B` |

Both via `scripts/replay_keeper.py results/calibration/nyiso113_lilocational_B
--out-dir <arm>`, which replays the keeper's `meta.json` kwargs with **no
`--set`**, so the config delta is structurally zero rather than asserted. The
`--out-dir` redirect mints each arm its own dated id (the miso-117 clause).

**Third comparison, free:** arm A vs the committed `nyiso113_lilocational_B`
sidecars isolates HEAD drift alone, answering the standing caiso-146 open item
for NYISO. This is reported whatever it shows.

**Cold-solve protocol (caiso-158 §4a):** `rm -rf results/NYISO` before **each**
arm, and confirm the log says `(cold)`. `cache_key` hashes config fields only —
the two arms are config-identical, so they share a key and arm B would silently
load arm A's results.

**Per-arm order (caiso-158 §4b):** solve → register → `legitimacy_diagnostics.json`
→ `calibration_verdict.py --write-metrics`.

**Rule 16:** `--year 2023 2024 2025`, one bundle per arm. Rule 22: NYISO holds a
`complete` marker only; the spend freeze is ACTIVE; **no out-of-training year is
touched**.

---

## 4. Predictions (recorded before the solve)

**P1 — direction.** CT_PEAKER energy **falls** and NYISO load-weighted λ **rises**
in all three years. The artifact is one-sided dearer, so the class can only move
up the stack.

**P2 — magnitude.** caiso-158 K3 measured this artifact against the nyiso-112
base at CT_PEAKER **−0.012 / −0.005 / −0.036 TWh** and λ **+0.028 / +0.020 /
+0.080 %** (2023/24/25) — the **smallest** dispatch response of the three solved
ISOs despite the **largest** artifact movement, because NYISO's CT fleet is
already largely out of merit. Arm B − arm A is predicted to reproduce these to
within the same order of magnitude. A materially larger response would mean the
Zone-K reserve family and the CT re-pricing **interact**, which is a reportable
finding, not a licence to revert.

**P3 — scorecard.** **No criterion flips.** The keeper baseline is C1 14/14
all-class · 10/10 free-class, C2/C3a/C3b/C4/C6/C7/C8 PASS, C3c the sole ledgered
caveat, determination CALIBRATED-WITH-CAVEATS, grade 9 scored / 8 target, 0 fails.
Arm B is predicted identical on all nine.

**P4 — C3c.** Unchanged at 3/0/7 model vs 10/12/42 actual h > \$300. Two CTs
getting dearer cannot manufacture a summer scarcity tail. **No caveat slot is
spent and no C3c evidence moves.**

**P5 — Zone-K liveness preserved.** The nyiso-113 K3 result must survive: the LI
30-minute family binds in the 5 hours of 2025 (h4193-4195, h4217-4218) and 2 hours
of 2023 where Zone-K thermal headroom falls below its published requirement, and
the 10-minute limb never binds. Arm B now also persists
`hourly/reserve_family_<year>.parquet` (`9df32c2`), so for the first time this is
**directly observable from the committed bundle** rather than reconstructed — the
standing gap nyiso-113 filed.

---

## 5. Gates

| gate | test | fail condition |
|---|---|---|
| **K1** | `config_drift(arm_B, nyiso113_lilocational_B)` | any `value_diffs` entry. Schema drift (`keeper_only` = the three deleted `ct_*_hr_override` fields) is expected and permitted |
| **K2** | control integrity: arm A reproduces the keeper's class hourlies | reported, not fatal — a divergence is the caiso-146 drift finding, and it is attributed before arm B is read |
| **K3** | liveness: arm B ≠ arm A on CT_PEAKER dispatch | zero movement in all three years ⇒ the correction is inert in NYISO; report as such, do **not** re-tune |
| **K4** | no criterion regresses vs the keeper | any PASS → CAVEAT/FAIL, or a new caveat slot spent |
| **K5** | span `[2023, 2024, 2025]`, freeze untouched | any out-of-training year |

---

## 6. Binding no-tuning clause

This is an **input correction**. If arm B scores worse, the corrected artifact
**still ships** (caiso-156 prereg §7: the artifacts ship regardless of arm
outcomes; the A/B measures the consequence, it does not license a revert). Under
rule 14 a worse fit on an accurate input is a **discovered bug elsewhere**, to be
opened as a root-cause item — never buried by reverting to the diluted meter.

Neither the band `[6.0, 25.0]`, the `_MIN_LOADED_HOURS` trust gate, the cap
percentile, nor any `nyiso_*` field may be re-levelled, re-scoped or re-derived
in response to this result. **Zero free parameters are introduced.** If the
promotion proceeds, the DOF ledger is carried verbatim from nyiso-113.

---

## 7. Deliverables

1. Both arms registered on the backcast dashboard (rule 15), `--no-prune`.
2. `measured_ct_heat_rates` NYISO cell note/evidence stamped (rule 28b); the
   **verdict stays K** — this lane tests no mechanism.
3. On promotion: keeper shard + `status/NYISO.js`, and — because NYISO holds a
   `complete` marker — `calibration-complete.json` re-keyed with a
   **determination re-verification** from committed artifacts only, no solve
   (rule 22 D-5(b); `audit_keepers` M1 enforces).
4. `FINDING-caiso160-*` + calibration-log entry.
