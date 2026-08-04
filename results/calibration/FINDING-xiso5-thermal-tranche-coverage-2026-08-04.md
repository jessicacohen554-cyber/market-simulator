# XISO-5 — the cross-ISO thermal-tranche "coverage gap" is THREE objects, and only ONE of them is a gap

**Date:** 2026-08-04 · **Determination:** PHASE 0 COMPLETE — **DIAGNOSIS ONLY,
NO REGENERATION** · **No LP, no solve, no scoring, no registration, no keeper
changed in any ISO, no cell verdict minted.**

**Probe:** `scripts/probes/_xiso5_thermal_tranche_coverage.py` (committed bytes
only; no CAMPD read, no deriver execution — seconds).
**Record:** `results/calibration/_xiso5_thermal_tranche_coverage.json`.
**Transcript:** `results/calibration/PROBE-xiso5-thermal-tranche-coverage-2026-08-04.txt`.

> **Session label.** The charter prompt is titled "XISO-1". That label is
> already SPENT — `FINDING-xiso1-diurnal-price-amplitude-is-systemic-2026-08-01.md`
> — as are xiso-2, xiso-3 and xiso-4. This session is recorded as **xiso-5** so
> the citation is unambiguous; the branch name keeps the prompt's slug.

---

## §0 — Headline

The charter's three named populations are adjudicated **separately**, and they
do not share a cause:

| population | verdict | disposition |
|---|---|---|
| **(a)** CHP `online_frac` zero in every ISO | **BY DESIGN, not a defect** | **CLOSED AS DOCUMENTED** (kill rule K1 fires) |
| **(b)** PJM `ST_GAS` 0/10 vs MISO 16/16 | **ARTIFACT VINTAGE, not data/roster/CEMS** | **CHARTERED, NOT LANDED** — a subset of miso-95's owner-blocked re-baseline |
| **(c)** CAISO entirely blank + NEISO/NYISO no column | **SAME cause as (b)**, three more ISOs | **HANDED OFF PER-ISO** (rule 25; kill rule K3) |

Two governance results decide what this session was allowed to do, and both
came out against acting:

* **Rule 23 gate: NO source-data change is cited ⇒ NO regeneration is
  licensed.** Kill rule **K2 fires**. §3.
* **Blast radius, measured:** the gap is **INERT at all six current keepers** —
  zero armed gates read a blank or absent column anywhere. But a regen is
  **not** column-scoped: it rewrites `committed_pct` / `mustrun_pct`, which
  **every** artifact-bearing ISO's keeper reads **unconditionally**. §4.

**Kill rule K4 is satisfied without special handling:** no PJM gate reads the
column PJM is missing (`st_gas_mustrun_per_plant` is OFF at PJM), so nothing
proposed here can move a PJM gate.

The charter's measured-state prose was **re-verified, not trusted**, and it is
correct in every cell (CAISO 0/156, PJM 168/256, MISO 178/282, NEISO/NYISO no
column). §1 restates it at group grain.

---

## §1 — The census, re-verified from committed bytes

`status="ok"` rows are rows that reached the deriver's full emit path.
`eia923_cf` rows are CHP-floor-only carry-forwards that never had a CAMPD
sample. Emitting groups are `{COAL, CC_REGULAR, CT_PEAKER, ST_GAS}` (§2).

| ISO | rows | max `online_hours` | `mustrun_online_pct` | `online_frac` | `chp_btm_pct` | `steam_level_cf` | **ok rows blank in an EMITTING group** |
|---|---|---|---|---|---|---|---|
| ERCOT | — | — | — | — | — | — | **no artifact** (by design) |
| CAISO | 156 | 22,760 | ✓ | ✓ (all null) | ✓ | ✓ | **70** |
| PJM | 256 | 26,280 | ✓ | ✓ | — | — | **10** |
| MISO | 282 | 26,280 | ✓ | ✓ | — | — | **0** |
| NYISO | 78 | 26,253 | — | — | — | — | **47** |
| NEISO | 76 | 24,504 | — | — | — | — | **39** |

Per-ISO detail of the blank emitting-group `ok` rows:

* **CAISO** — `CC_REGULAR` 23/23, `CT_PEAKER` 44/44, `ST_GAS` 3/3 (no COAL fleet).
* **PJM** — `ST_GAS` 10/10. `CC_REGULAR` 69/69 and `COAL` 29/29 are populated.
* **MISO** — none. Every emitting-group `ok` row publishes a value.
* **NYISO** — `CC_REGULAR` 19/19, `CT_PEAKER` 17/17, `ST_GAS` 11/11.
* **NEISO** — `CC_REGULAR` 29/29, `CT_PEAKER` 8/8, `ST_GAS` 1/1, `COAL` 1/1.

**166 `ok` rows across four ISOs** that a HEAD re-derivation would populate and
the committed artifact does not.

**The schema columns are a vintage ladder, and it does not order consistently.**
NYISO/NEISO have neither `mustrun_online_pct` nor `online_frac` (oldest).
PJM/MISO have both but neither WP-3 column. CAISO has *both WP-3 columns*
(`chp_btm_pct`, `steam_level_cf` — landed 2026-07-19) **and** an all-null
`online_frac`. CAISO is therefore **newer than PJM/MISO on the CHP axis and
older on the `online_frac` axis simultaneously** — which no single deriver
commit can produce. **The family has no common vintage:** each ISO's file is a
snapshot of whatever deriver branch that ISO's own lane last ran, and the
branches did not merge in a consistent order.

---

## §2 — Q1: the CHP zero is DESIGN. Cited code path, not inference

`scripts/data/derive_thermal_tranches.py:409`:

```python
_ONLINE_FRAC_GROUPS: frozenset[str] = frozenset(
    {"COAL", "CC_REGULAR", "CT_PEAKER", "ST_GAS"}
)
```

The emit expression (`:685`) is gated on exactly that set, and its own comment
states the reason in one line: *"CHP groups stay blank — their floor is the
steam host (rule 19)."* The constant's docstring (`:396–408`) says the same at
length: `online_frac` exists for COAL's step-3a min-load forcing and for the
merchant gas commitment floors; CHP's floor is `chp_pmin_cf` / `steam_level_cf`.

**Three independent confirmations, all measured:**

1. **The zero survives the full `ok` emit path.** CHP rows that reached
   `status="ok"` — CAISO 13, PJM 10, MISO 20, NYISO 16, NEISO 4 — computed
   `committed_pct`, `p25_cf` and `median_cf` and still published **no**
   `online_frac`, in every ISO. A coverage gap would not be that clean; a
   `group in _ONLINE_FRAC_GROUPS` test is.
2. **The measurement is computed for CHP anyway and deliberately withheld.**
   `sync_hours` accumulates for *every* group (`:585–592`); `_ONLINE_FRAC_GROUPS`
   only gates which rows *publish* it. So the blank is a suppression decision,
   not a missing statistic.
3. **CHP is already floored, by a different column, in all six keepers.** D-2
   `chp_steam` is armed and binding everywhere: ERCOT 0.03–12.81, CAISO
   1.47–4.69, MISO 0.07–4.44, PJM 0.00–1.34, NYISO 0.04–0.54, NEISO 0.02–0.04
   TWh/yr.

**Rule 19 `[R-ONE-MECH]` closes it affirmatively, not just permissively.** The
enumeration the rule demands returns exactly one incumbent floor per CHP class —
`chp_steam` (`MECH_CHP_STEAM`), sourced from `chp_pmin_cf` and, where armed,
superseded in LEVEL by `steam_level_cf` (a level swap, not a second floor).
Populating `online_frac` for CHP and wiring it to a commitment floor would
**stack a second forcing mechanism on a class that already has one** — forbidden
outright. Population (a) is **CLOSED AS DOCUMENTED. K1 fires.** It is not a
defect, it must not be "fixed", and no future lane should re-open it as one.

---

## §3 — Q2: PJM `ST_GAS` 0/10 vs MISO 16/16 is a VINTAGE divergence. Code-proven

This is the charter's whole load, and the answer is not a roster, a CEMS
coverage, a status filter or a threshold.

**The emit condition cannot produce PJM's blank at HEAD.** From
`derive_thermal_tranches.py:685–693`, a row publishes `online_frac` iff:

```python
group in _ONLINE_FRAC_GROUPS and sync_hours.get((code, group), [0, 0])[1] > 0
```

* `ST_GAS ∈ _ONLINE_FRAC_GROUPS` at HEAD — it joined **2026-07-12**, and the
  constant's own comment names the lane that added it: *"ST_GAS joined
  2026-07-12 (MISO 2025 Southern-gas lane)"*.
* The denominator `sync_hours[...][1]` accumulates `len(series)` for every year
  the plant has a CAMPD series (`:592`). Every PJM `ST_GAS` row is
  `status="ok"` with `online_hours > 0` — Big Sandy 20,164 h, Brunner Island
  19,681 h, Montour 11,610 h — so each necessarily had a series, and the
  denominator is necessarily positive.

Both conjuncts hold for all ten PJM `ST_GAS` rows, so **HEAD cannot emit a
blank there**. The committed file does. Therefore the committed PJM artifact
was produced by a deriver vintage **predating 2026-07-12**, when `ST_GAS` was
not in the set. MISO's 16/16 is the *same code on the same inputs* run **after**
that date — it is the artifact the adding lane itself regenerated.

**MISO is the clean control arm the charter asked for, and it does its job:**
it proves the deriver CAN populate `ST_GAS` (16/16, values 0.026 → 0.982,
spanning true cyclers and always-on VLR steamers), so PJM's zero is not a
property of the class, the estimator or the data. It is a property of *when the
file was last written*.

**The same proof generalizes to population (c)** — CAISO's 70, NYISO's 47 and
NEISO's 39 blank emitting-group `ok` rows are the identical condition failing
for the identical reason, at three earlier points on the vintage ladder.
Populations (b) and (c) are **one object at different depths**, not two.

**This is a NEW fact, and it is bounded against the incumbent finding.**
miso-95 (2026-07-26, determination `PROVENANCE-BLOCKED`) established that all
five artifacts are provenance-orphaned on a code axis (`apply_cc_summer_guard`)
and a data axis (CAMPD/parasitic vintage drift), and its §5 schema table
already recorded *"only CAISO's has `steam_level_cf`; NYISO and NEISO also lack
`mustrun_online_pct` and `online_frac`."* What miso-95 did **not** name — and
what this session adds — is (i) **PJM `ST_GAS` 0/10 and CAISO's all-null
`online_frac`**, both of which sit *inside* files whose schema looks current, and
(ii) the **non-monotone vintage ladder** (§1) that shows the family has no
common ancestor at all. This session does **not** re-derive miso-95's numbers
and does not re-open its verdict.

---

## §4 — Q4: blast radius, measured per ISO from each keeper's own `run_config.json`

### 4.1 Which gate reads which column

| artifact column | runtime consumer | arming gate |
|---|---|---|
| `committed_pct` | `campd_bins.thermal_tranche_overrides` → `bins_to_fleet`; `model/reserves/spec.py::_min_stable_headroom` | **none — unconditional under `use_campd_bins`** |
| `mustrun_pct` | `campd_bins.thermal_tranche_overrides` → `bins_to_fleet` | **none — unconditional** |
| `mustrun_online_pct` | same, online-Pmin select (`campd_bins.py:1645`) | `coal_mustrun_online_pmin` |
| `online_frac` (COAL) | `assembly.py:1149` → `coal_sync_online_frac` | `coal_sync_srmc_tranche` |
| `online_frac` (CC_REGULAR) | `assembly.py:1002–1005, 1154` → `cc_mustrun_online_frac` | `cc_mustrun_per_plant` |
| `online_frac` (ST_GAS) | same code path, own gate | `st_gas_mustrun_per_plant` |
| `p25_cf` | `arrays.py:1894` → `thermal_tranche_p25_level` | `st_gas_mustrun_p25_level` |
| `peaking_pct` | `campd_bins.thermal_tranche_peaking` | `cc_peaking_per_plant` |
| `chp_pmin_cf` | `chp.py::chp_pmin_cf` → `chp_grid_pmin_mw` | `chp_steam_following` |
| `steam_level_cf` | `assembly.py:611` → `thermal_tranche_chp_steam_level` | `chp_steam_floor_p25` |

### 4.2 Armed state of every one of those gates, in the CURRENT keeper

Keepers as designated at HEAD: ercot158-pool-arm / caiso-166-measured-dlap /
pjm-152-collapse / miso-127-onlinepmin / nyiso-125-seam-envelope /
neiso81-chpheatrate.

| gate | ERCOT | CAISO | PJM | MISO | NYISO | NEISO |
|---|---|---|---|---|---|---|
| `use_campd_bins` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `coal_mustrun_online_pmin` | — | — | **✓** | **✓** | — | — |
| `coal_sync_srmc_tranche` | — | — | **✓** | — | — | — |
| `cc_mustrun_per_plant` | — | — | **✓** | — | — | — |
| `st_gas_mustrun_per_plant` | — | — | — | **✓** | — | — |
| `st_gas_mustrun_p25_level` | — | — | — | **✓** | — | — |
| `cc_peaking_per_plant` | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| `chp_steam_following` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `chp_steam_floor_p25` | — | **✓** | — | — | — | — |

### 4.3 The two results that matter

**(i) ZERO silent no-ops at any current keeper.** No ISO arms a gate over a
column its own artifact lacks. The one gate that reads the newest column,
`chp_steam_floor_p25` → `steam_level_cf`, is armed at **CAISO alone** — the one
ISO whose artifact carries it. Likewise `st_gas_mustrun_per_plant` is armed only
at MISO, whose `ST_GAS` coverage is 16/16. **The coverage gap is measured-INERT
across all six keepers today.** Nothing is currently broken by it.

That inertness is **latent, not permanent**, and it is the real hazard: if any
future PJM/CAISO/NYISO/NEISO lane armed `st_gas_mustrun_per_plant`,
`cc_mustrun_per_plant`, `coal_sync_srmc_tranche` or `chp_steam_floor_p25`, the
loader (`campd_bins.py:1287`) would skip every blank row **silently and without
error** — the mechanism would engage on nothing and read as inert on the
merits when it was never given its parameters. That is the failure this census
exists to pre-empt.

**(ii) A regen is NOT column-scoped, and that is the binding constraint.**
`thermal_tranche_overrides` is called **ungated** at `campd_bins.py:1644` under
`use_campd_bins` (armed in all six keepers) and again from
`model/reserves/spec.py:1073`. So `committed_pct` / `mustrun_pct` — the tranche
sizing itself — are read **unconditionally** by every artifact-bearing ISO. A
re-derivation rewrites the whole file, so **any regen of ISO X's artifact is a
keeper-moving change in ISO X**, whatever column motivated it. It can only be
done as that ISO's own pre-registered, keeper-grade A/B.

**Against interest, and reassuring on rule 25:** the artifact is **per-ISO by
construction** — every consumer (`chp.py:270`, `coal.py:331`,
`campd_bins.py:1162`, `arrays.py:1894`) resolves
`thermal_tranches_{iso}.csv` from its own `iso` argument, and no solve-path
reader pools across ISOs. **A regen of one ISO's file cannot reach another
ISO's keeper.** Kill rule **K3's cross-ISO leak does not exist structurally**;
the per-ISO hand-off in §6 is required by the *within*-ISO blast radius, not by
a cross-ISO one.

### 4.4 Forced energy the artifact currently carries (committed D-2 rows, TWh/yr)

| ISO | artifact-fed mechanisms | range across 2023–2025 |
|---|---|---|
| ERCOT | `chp_steam` (off the hardcoded maps, not the artifact) | 0.03 – 12.81 |
| CAISO | `chp_steam` | 1.47 – 4.69 |
| PJM | `cc_mustrun_per_plant` / `coal_mustrun` / `chp_steam` | 9.81 – 22.81 / 1.59 – 4.86 / 0.00 – 1.34 |
| MISO | `st_gas_mustrun_per_plant` / `chp_steam` | 8.00 – 10.48 / 0.07 – 4.44 |
| NYISO | `chp_steam` | 0.04 – 0.54 |
| NEISO | `chp_steam` | 0.02 – 0.04 |

**ERCOT is a special case and is reported apart, not as a no-op.** It has no
`thermal_tranches_ERCOT.csv` at all: its per-plant committed / must-run / CHP
values come from `custom-bin-assignments.csv` and the hardcoded fleet maps
(`CC_REGULAR_COMMITTED_PCT_BY_PLANT`, `COAL_MUSTRUN_BY_PLANT`,
`CHP_PMIN_CF_BY_PLANT`). ERCOT is `·` on this object, structurally.

---

## §5 — Q3: the rule 23 `[R-FROZEN-DERIVE]` gate, decided EXPLICITLY and up front

**Is there a CITED SOURCE-DATA CHANGE licensing a re-derivation? NO.**

* **Precedent is directly on point.** miso-95 ruled the tranche staleness a
  **code** axis: *"A **code** change, so rule 23's data-change trigger never
  fired — which is exactly why nothing re-derived."* The finding this session
  adds (§3) is likewise a **code-vintage** axis: `_ONLINE_FRAC_GROUPS` gained
  `ST_GAS` by a source edit, not by a data arrival.
* **The only input move since is out of scope.** xiso-2 (2026-08-02) measured
  the sole post-guard change to a deriver input — MISO's outage extract, root-
  caused to source commit `5cd937407` filling the MISO EIA-930 2022 hole — as
  **2022-only, with 2023–2025 identical row-for-row**. The tranche artifacts
  are derived on a 2023–2025 window (max `online_hours` 22,760–26,280 ≈ 2.6–3.0
  × 8,760), so it cannot license moving their statistics. *Cited from xiso-2, not
  re-measured here.*
* **No other change is cited.** No commit has touched `data/raw/campd-unit-level`
  or the parasitic factors since the guard (xiso-2 dependency census), and the
  CAMPD extension to 2026 is both outside the derive window and quarantined by
  rule 22 in a backcast input.

**⇒ Kill rule K2 FIRES. No regeneration happens in this session under any
framing.** This charter may only diagnose and document coverage, and that is
all it did: no file under `data/` was read for anything but its committed bytes,
none was modified, and the deriver was never executed (the probe *parses*
`_ONLINE_FRAC_GROUPS` out of the source precisely so it cannot accidentally run
it).

**What WOULD license a regen** — recorded so a future session does not have to
re-derive this reasoning: a new CAMPD hourly or `parasitic_load_factors.parquet`
vintage covering 2023–2025, a new EIA-860 fleet vintage, or a new EIA-923
vintage for the CHP fallback legs. **The `apply_cc_summer_guard` defect miso-95
identified is NOT such a licence** — it is a code fix, and miso-95 already
ranked its adoption as an owner call (its §4 option 2), not a rule-23-admissible
re-derivation.

---

## §6 — Disposition of each population, separately

**(a) CHP `online_frac` zero — CLOSED AS DOCUMENTED.** By design
(`_ONLINE_FRAC_GROUPS`), confirmed three ways, and required to stay that way by
rule 19: CHP already carries `chp_steam` in every keeper. **Not a defect; must
not be "fixed."** This section is the documentation the kill rule asked for.

**(b) PJM `ST_GAS` 0/10 — CHARTERED, NOT LANDED.** Cause identified (vintage,
§3); currently inert at the PJM keeper (§4.3(i)); **not actionable in this
session** (§5). It is a strict subset of miso-95's `PROVENANCE-BLOCKED`
re-baseline, whose unblock is an **open owner call** — miso-95 §4 ranked the
options: (1) re-baseline all five artifacts deliberately, one registered arm per
ISO; (2) adopt the CC-guard sub-axis alone; (3) stamp a `campd_vintage`
provenance header into every derived artifact. **This session adds a fourth
option and recommends it as the cheapest**: (4) stamp the deriver's
`_ONLINE_FRAC_GROUPS` (and the schema generation) into a header comment or a
sidecar, so a one-line read answers "which groups was this file's vintage
emitting?" — the question that cost this session its whole §3.

**(c) CAISO / NEISO / NYISO — HANDED OFF PER-ISO (rule 25).** Same cause, same
blocker. Each ISO's re-baseline belongs to that ISO's own lane because
`committed_pct` / `mustrun_pct` are read unconditionally by that ISO's keeper
(§4.3(ii)) — it is a keeper-grade single-delta A/B, never a maintenance chore.
**No verdict crosses a boundary**: MISO's populated `ST_GAS` is evidence about
the *deriver*, not about any other ISO's fleet, and a target lane must derive
its own parameters from its own market's data.

**On the miso-127 §7 link, adjudicated rather than assumed.** miso-127 §7(a)
reported that only 0.605/0.611/0.629 of MISO's model `ST_GAS` class energy has a
committed bench counterpart (7.5–8.3 TWh/yr unmatched) and flagged that it
"touches the same artifact family." **It does not.** MISO's tranche artifact has
**zero** coverage gap (§1) — 16/16 on the very class in question — so the bench
shortfall cannot be a tranche-artifact coverage defect. It is a **bench class
assignment / bench membership** question on a different artifact
(`frontend/data/backcast/bench/MISO/<year>.json.gz`), and miso-127's own
instruction stands: it needs its own charter with a control arm. **This session
does not land it, and the two must not be merged.** Recording the negative here
is the point — it removes a false dependency that would otherwise have blocked
the MISO lane behind this one.

---

## §7 — What this session deliberately did NOT do

* **No regeneration of any artifact**, including to a scratch path — a
  scratch-out dry run would still be the regen K2 forbids, and §3's proof is a
  code proof that needs no execution.
* **No solve, no scoring, no registration.** Nothing to register (rule 15's
  duty fires on runs); the dashboard is untouched and correct.
* **No cell verdict minted.** No mechanism was tested. §8's matrix row is an
  **audit** row in the xiso-2 / xiso-3 shape, not a mechanism verdict.
* **No other ISO's keeper shard, status file or column touched** (rule 25).
* **The stale matrix `keepers.NEISO` header is FLAGGED, NOT EDITED.** It reads
  `2026-08-03-neiso-caiso156-meter-screen`; the designated NEISO keeper at HEAD
  is `2026-08-04-neiso81-chpheatrate`. That is neiso-81's rule 28(e) re-stamp
  debt, in NEISO's lane, and it is reported rather than silently fixed by a
  cross-ISO session.
* **miso-95 is not re-opened, re-measured or contradicted.** This extends it.

---

## §8 — Rule compliance

* **Rule 1 `[R-STRUCT]`** — nothing judged by fit; no fit was computed. The CHP
  closure rests on the code path and rule 19, not on a residual.
* **Rule 13 `[R-MEASURED]`** — no measured outcome fed back anywhere; the
  columns at issue are rule-13-admissible measured inputs, which is *why*
  populating them is the right direction whenever it is licensed.
* **Rule 14 `[R-ACCURATE]`** — the measured column is preferred over the
  implicit zero, and that preference is recorded as the direction of travel.
  Pre-registered for whoever executes a re-baseline: **a worse fit after
  populating a column is a DISCOVERED BUG to root-cause, never a reason to
  revert to the blank.**
* **Rule 19 `[R-ONE-MECH]`** — the incumbent floor on each affected class is
  enumerated before anything is proposed (§2 for CHP, §4.1/§4.4 for
  COAL/CC_REGULAR/ST_GAS). The CHP closure is *decided* by that enumeration.
* **Rule 22 `[R-HOLDOUT]`** — the spend freeze was read **FIRST** and is
  **ACTIVE**; `final` is empty for every ISO. No out-of-training year was
  solved, scored, read or registered. Only 2023–2025-derived committed bytes
  were inspected.
* **Rule 23 `[R-FROZEN-DERIVE]`** — decided explicitly and up front (§5): no
  cited source-data change, therefore no re-derivation. No parameter moved.
* **Rule 25 `[R-ISO-SCOPE]`** — no verdict transferred; the MISO control arm is
  evidence about the deriver, not about PJM's fleet; hand-offs are per-ISO.
* **Rule 27 `[R-PUSH]`** — no existing source file ≥300 lines rewritten; this
  session adds new files and appends to docs.
* **Rule 28 `[R-MECH-MATRIX]`** — matrix and §5.7 updated in this same session
  (duty b, in the audit-row form xiso-2/xiso-3 established); no new
  `ScenarioConfig` field, so duty (c) does not fire.

---

## §9 — Reproduce

```
python scripts/probes/_xiso5_thermal_tranche_coverage.py \
    --json results/calibration/_xiso5_thermal_tranche_coverage.json
```

Committed bytes only, seconds, no CAMPD read. **DO-NOT-REDO:** re-run the probe
rather than re-censusing by hand, and do not re-derive §3's vintage proof — it
is a code proof over a frozen constant and an emit expression, and it will hold
until `_ONLINE_FRAC_GROUPS` or the emit condition changes.
