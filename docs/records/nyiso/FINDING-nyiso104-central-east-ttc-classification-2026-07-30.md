# FINDING — nyiso-104: the Central-East measured TTC envelope is an OVERLAY, and it was invisible to D-5

**Session:** nyiso-104 · **Date:** 2026-07-30 · **ISO:** NYISO
**Keeper:** `2026-07-30-nyiso-100-silretire` — **UNCHANGED** by this session.
**Scope:** `scripts/legitimacy_diagnostics.py` (D-5 registry) + provenance
comments in `config/constants.py` / `pipeline/ttc.py` + declared-overlay list +
tests + matrix. **No LP ran. No solve-affecting code changed.**

---

## 0. Headline

`pipeline/ttc.py::apply_iso_monthly_ttc` (and its sibling
`apply_iso_year_ttc`) apply NYISO's measured Central-East day-ahead TTC to the
`Upstate_West -> Capital_Hudson` link in the backcast only. They carried **no
`D5_REGISTRY` row at all**, so D-5 forecast/backcast parity has been blind to
the entire family for as long as the tables have existed.

The charter posed the classification fork and forbade settling it by analogy to
nyiso-102. It resolves to **(a), a genuine backcast overlay** — the opposite of
nyiso-102's `nyiso_local_selfsupply` result — on a falsifiable test of the
source data. The consequence is a declared registry row, **not** a forecast
wiring; wiring these numbers forward would be an active defect (§3).

D-5 still **PASSES** on the keeper's config, now with the overlay visible and
`declared`. The committed keeper artifact is re-emitted with the row and every
other gate block byte-identical (§5).

---

## 1. The gap, exactly

Both helpers live in `src/market_sim/pipeline/ttc.py` and are called only from
`scripts/run_calibration.py` (`:1871` and `:2021`, via the `_`-prefixed
aliases). `src/market_sim/runner.py` references neither. That is the classic
D-5 shape — a mode difference — but D-5 never reported it, because
`D5_REGISTRY` had no row to match. On the pre-session tree:

```
$ git show origin/main:scripts/legitimacy_diagnostics.py \
    | grep -c "central_east\|iso_monthly_ttc\|iso_year_ttc"
0
```

Before this session, D-5 on the keeper emitted **11 rows**, none of them this
overlay. The gate was green on an incomplete inventory, which is worse than a
red gate on a complete one.

Note the scope: the charter names only `_apply_iso_monthly_ttc`, but
`apply_iso_year_ttc` has the identical gap and reads the identical source
series. They are two aggregations (calendar-month mean, annual mean) of one
posting series over one link, so they take **one** row, not two — rule 19
`[R-ONE-MECH]`.

---

## 2. What the source data actually is

`constants.NYISO_INTERFACE_TTC_BY_MONTH` / `_BY_YEAR` are produced by
`scripts/data/derive_nyiso_central_east_ttc.py` from the **`TTC (DAM)` column
of NYISO's MIS `ATC_TTC` postings** for the `CENT EAST` interface, hour by
hour, aggregated to a calendar-month arithmetic mean and rounded to 25 MW.

That is a **realized operational series**: the limit NYISO actually posted for
each hour of each day, reflecting the as-planned network configuration for that
day — including that day's approved transmission outages. It is not a rating
table. NYISO posts no DAM TTC for a forward year.

(`data/raw/NYISO/ATC_TTC.zip` is **not present in this environment** — see the
`DATA NEEDED` note in `data/raw/NYISO/README.md`. The committed tables are the
derived artifact, and the tests below are written against them.)

---

## 3. The classification test, and why it discriminates

Rule 13 `[R-MEASURED]`: *could this same quantity be produced for a forward
year from forward drivers, and would it respond to changed conditions?*

The two hypotheses make **opposite, checkable predictions** about the committed
tables:

* **(b) published seasonal rating** — a deterministic engineering quantity
  recomputed the same way every year. On an unchanged network it *must* repeat:
  the same months derate, by the same relative amount.
* **(a) realized posting** — embeds that year's own approved outage schedule,
  which is idiosyncratic per year.

So: normalize each year's 12 monthly means by that year's own annual mean
(removing the level, which is not in dispute) and correlate the residual shapes
across **2024 and 2025** — the two years that share the post-AC-Transmission
topology (NY Transco Segment A energized Dec 2023).

| test | result |
|---|---|
| Pearson r, level-normalized monthly shape, 2024 vs 2025 | **+0.209** |
| Spearman ρ, same | **+0.155** |
| One-sided p vs the dihedral calendar null (12 rotations × reflection) | **0.250** |
| Deepest-derate month | **Sep (2024) → Apr (2025)** |
| Peak month | Feb (2024) → Jan (2025) |

A rating would sit at r ≈ 0.9+ and p ≈ 0. Instead the **true calendar alignment
fits no better than a rotated or reversed calendar**. The derate is not
anchored to a season; it moves with the year's maintenance schedule.

### 3.1 The provenance comment was wrong

`constants.py` claimed the postings show "a recurring late-summer/shoulder
derate". Tested directly against the tables it describes:

| year | Aug–Nov index | rest-of-year index | derate |
|---|---|---|---|
| 2024 | 0.946 | 1.027 | **+7.9 %** |
| 2025 | 1.000 | 1.000 | **+0.0 %** |

**Falsified.** It is not recurring. The comment is corrected in `constants.py`
and in `pipeline/ttc.py`'s docstring, both of which had propagated the claim.

### 3.2 How much is actually in dispute

Decomposing all 36 monthly means:

| component | SS | share |
|---|---|---|
| between-year (level / the Dec-2023 step) | 9,588,576 | **82.0 %** |
| within-year (monthly shape) | 2,104,271 | 18.0 % |
| …of which post-upgrade only — *the disputed part* | 792,448 | **6.8 %** |

Within-year sd is 162 MW (2024) and 199 MW (2025) on a 2,850 MW link — 5.7 %
and 7.0 %. The non-reproducible component is both non-reproducible **and**
small; the large component is the level, and the level is not in dispute.

### 3.3 Why it is nonetheless admissible in a backcast

A year's approved transmission-outage schedule is a **physical availability
event on the network** — the same admissibility family as `historic_outage_overlay`
on a unit, which rule 13 names as the canonical allowed case. It is an input
constraint, not an outcome: the LP still chooses the flow within the limit;
nothing is pinned to a measured flow. So it is admissible, backcast-only, and
therefore belongs on the declared-overlay list — which is exactly the set of
admissible-but-backcast-only inputs.

### 3.4 Steelmanning (b), and why it still fails

The strongest form of (b): *NYISO does publish seasonal interface ratings;
take those and apply them forward.*

That is true, and it describes a **different input than the one in the code**.
The code applies month-means of realized DAM postings. Building a forward
mechanism out of published seasonal ratings would be a new derivation with its
own source and its own row — not a wiring of this table into `runner.py`. And
§3 shows *these* numbers do not behave like a rating, so wiring *them* forward
would import one historical year's outage schedule into every forecast year —
precisely what rule 13 forbids. Hence the forecast lane is **G (refused)**, not
**U (untested)**.

---

## 4. The forecast loses nothing

This is what makes the refusal cheap rather than a trade-off. The
forward-reproducible component — the level — **already has its forward
channel**:

* `data/raw/transmission-expansion/nyiso.csv`, a registry of transmission
  projects with a published instrument, an `in_service_year` and a ΔTTC, applied
  by `data/transmission_expansion.py::apply_transmission_expansion` and wired
  into `runner.py`.
* over the static 2,850 MW in `iso_configs._nyiso_config` — which **is** this
  series' measured post-upgrade annual mean (`_BY_YEAR[2024] = _BY_YEAR[2025] =
  2850.0`).

The registry's own Smart Path Connect row already records that reasoning
verbatim: *"the model's Central-East 2,850 MW static is the measured 2024-25
DAM mean and already reflects the phased 2025 energizations."*

So the correct forward treatment of a Central-East re-rate is a registry row
with a published instrument and an in-service date. That mechanism exists, is
wired, and is unaffected by this session.

---

## 5. What changed, and the proof nothing else did

**Registry.** New `D5_REGISTRY` row `nyiso_central_east_measured_ttc`:
`toggle=None`, `mode="backcast_only"`, `declared=True`, `iso="NYISO"`,
`backcast_symbols=("apply_iso_year_ttc", "apply_iso_monthly_ttc")`.

**Infrastructure.** `MechanismSpec` gains an optional `iso` field, and `run_d5`
skips rows whose `iso` does not match the bundle's. This is *required* by the
new row: it has no config toggle to scope it (the overlay is unconditional for
any NYISO backcast year with a table), so without scoping it would report
itself active in all six ISOs. Every pre-existing row keeps `iso=None` and is
therefore untouched — proved, not asserted:

| bundle | committed rows | re-scored rows | removed | added | order |
|---|---|---|---|---|---|
| `caiso139_dumpguard_B` (CAISO keeper) | 11 | 11 | none | none | preserved |
| `nyiso100_silretire` (NYISO keeper) | 11 | 12 | none | `nyiso_central_east_measured_ttc` | preserved |

**Keeper artifact.** `results/calibration/nyiso100_silretire/legitimacy_diagnostics.json`
is re-emitted with the fresh D-5 block spliced in. `--only D5 --json-out` would
have *dropped* D1/D2/D4/D9/D10 (they need per-plant floor reconstruction from
raw inputs this container does not carry), so the D-5 block alone was
recomputed through the real `run_d5` and every other key asserted equal before
writing. The resulting diff is a **7-line pure insertion**; D-5 stays
`passed: true` with zero failures.

**No solve ran, and none was needed.** No solve-affecting code path changed:
the edits are the diagnostics registry, provenance comments, docs, tests and
the matrix. Rule 15 is satisfied **vacuously** — there is no run to register,
and registering the keeper again would be a duplicate.

---

## 6. Guards against silent drift

`tests/scoring/test_legitimacy_diagnostics.py::TestD5NyisoCentralEastTtc`:

1. the row is `declared`, `backcast_only`, `iso="NYISO"`, `toggle=None`;
2. it is emitted as a `declared` backcast-only difference against the **real**
   entry-point sources;
3. it does **not** appear for ERCOT / CAISO / PJM / MISO / NEISO;
4. neither helper appears in `runner.py` — if a future session wires these
   tables forward, this fails loudly with the reason;
5. **the classification's own evidence is pinned**: the same-topology monthly
   shape correlation must stay below 0.5. If refreshed postings ever *did* show
   a reproducible seasonal shape, the overlay would have to be re-adjudicated
   as a forward mechanism, and this test fails first.

---

## 7. Recorded, not fixed here

**`ordc_floor_active_mask` bleeds across ISOs.** It is an ERCOT mechanism with
`toggle=None` and no `iso` scope, so it reports itself active in every
non-ERCOT bundle's D-5 output — visible in the NYISO keeper's own committed
artifact ("ERCOT scarcity-floor measured active-hours mask"). The `iso` field
added here is exactly the fix, but applying it would change other ISOs'
committed D-5 row sets, which is a separate delta and not this session's.
Filed, not done.

**Binding frequency is unmeasured.** How often the monthly envelope binds
differently from the annual mean is not established: the keeper's `hourly/`
sidecars carry class dispatch, storage and system price, but no link flows, so
it would need an LP replay. The classification does not turn on it — an
admissible input is admissible whether or not it binds — but a successor
studying Central-East congestion should know the number is not on record.

---

## 8. Evidence

* probe: `scripts/probes/nyiso104_central_east_ttc_classification.py` (T1 shape
  reproducibility, T2 variance decomposition, T3 the falsified derate claim)
* declared-overlay list: `docs/backcast-measured-data-audit-2026-06.md`
  (2026-07-30 section)
* matrix: row `nyiso_central_east_measured_ttc`, cells `....K.` / fc `....G.`
* the fork this one deliberately did **not** follow:
  `docs/FINDING-nyiso102-d5-parity-wiring-2026-07-30.md`
