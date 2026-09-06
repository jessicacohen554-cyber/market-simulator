# FINDING — Y-18: the FR-22 backcast→forecast parity red, adjudicated

**Session:** Y-18, Model Audit & Release-Finalization Program
**Date:** 2026-09-06
**Branch:** `claude/y18-fr22-parity-two-mechanisms-ggvada`
**Scope:** zero LP. No solve, no score, no registration; no keeper shard, marker,
freeze file, bundle or matrix-cell verdict changed.

---

## 0. Headline

The two FR-22 FAILs are **not the same kind of thing**, and the evidence that
separates them is in each mechanism's own module, under a rule-13 heading, in
its own words. They are adjudicated independently (rule 25 `[R-ISO-SCOPE]`):

| Mechanism | ISO | Rule 13 forward analogue? | Disposition |
|---|---|---|---|
| `ercot_storage_as_soc_reserve` | ERCOT | **NO** — the measured award corpus is per-historical-year and the forward channel is a *different*, validator-exclusive mechanism | `BACKCAST_ONLY` |
| `nyiso_seam_deliverability_envelope` | NYISO | **YES** — its own module asserts forward regeneration and condition-response, verbatim | `GAP` + wiring plan, routed to the NYISO/forecast desk |

`BACKCAST_ONLY` was **available on one of the two and refused on the other.**
Filing the NYISO field `BACKCAST_ONLY` would have turned the check green in one
line; it would also have asserted a non-regenerability the code explicitly
denies, which is the exact failure mode this gate exists to catch.

**Before:** `EXIT=1`, 2 unaccounted, 13 filed gaps.
**After:** `EXIT=0`, 0 unaccounted, 14 filed gaps. (§4, `$?` read directly.)

---

## 1. ERCOT — `ercot_storage_as_soc_reserve` → `BACKCAST_ONLY`

### 1.1 The call site, read

`scripts/run_calibration.py:4814-4832` — the **backcast** orchestrator, its sole
consumer:

```python
# Measured AS SOC reservation (ercot_storage_as_soc_reserve, ercot-167 —
# matrix §5.1 item 10, the ercot-162 §2 named successor). The power
# reservation above withholds the measured award's MW from the discharge
# cap but "reserves *power*, not state of charge" (its own docstring);
# ERCOT Nodal Protocols §3.17.3 also requires the SOC BEHIND each award
# (award × published product duration) to stay in the tank. ...
storage_soc_min = None
if (
    getattr(config, "ercot_storage_as_soc_reserve", False)
    and getattr(config, "storage_as_commitment", False)
    and not getattr(config, "ercot_storage_as_endogenous", False)
    and iso == "ERCOT"
    and storage.n_storage
):
```

The gate's **third clause is the whole adjudication**: the mechanism is
constructed to be unreachable whenever the endogenous split is armed.

### 1.2 The admissibility answer: NO

> *Could this same quantity be produced for a forward year from forward drivers,
> and would it respond to changed conditions?*

The quantity is `Σ_p award_p(t) × duration_p`. The durations are published and
forward-safe (`reserves.spec.ERCOT_AS_PRODUCT_DURATION_H`, Nodal Protocols
§3.17.3). **The awards are not.** `model/storage.py:633-634` reads them from

```
data/raw/ercot-AS/ercot_{year}_as_by_restype_hourly.parquet
data/raw/ercot-AS/ercot_{year}_storage_as_products_hourly.parquet
```

— a **per-historical-year** 60-Day DAM PWRSTR corpus, keyed on `year`, with
`if not (total_path.exists() and prod_path.exists()): return soc_min` (all-zero,
inert) as its forward behaviour. A forecast year has no such file, so limb 1
fails on the artifact. Limb 2 fails on the object: a frozen historical hourly
award series does not move when the forward fleet, load or AS requirement
changes.

Four independent confirmations, all in-repo and all pre-existing:

1. **The function's own docstring** (`src/market_sim/model/storage.py:620-623`)
   states the conclusion and names the substitute:
   > "Zero fitted parameters (rule 23); **forward runs price the split
   > endogenously (`ercot_storage_as_endogenous`), so this measured record is
   > backcast-only**, a capability input, never a pinned outcome (rule 13)."
2. **A construction-time validator enforces the exclusivity**
   (`src/market_sim/config/scenarios.py:16697-16701`):
   > `"ercot_storage_as_soc_reserve is mutually exclusive with
   > ercot_storage_as_endogenous: the endogenous split prices the AS/energy
   > split itself (a measured SOC floor would pre-commit it)."`
   The forward channel is not merely available — arming both is a hard error.
3. **The forward channel is live in the forecast orchestrator.**
   `src/market_sim/runner.py:4630` branches on `ercot_storage_as_endogenous`,
   deriving storage AS revenue from the co-opt's own reserve duals.
4. **The whole measured-award family is guarded the same way inside the SHARED
   module.** `src/market_sim/model/reserves/spec.py:1365-1371` and `2124-2131`
   each gate on `and not getattr(config, "ercot_storage_as_endogenous", False)`
   under the comment *"Measured 60-Day-DAM storage AS awards — backcast-only
   record (the forward story is `ercot_storage_as_endogenous`)."*

### 1.3 The counter-argument, considered and rejected

The registry's neighbouring FFR-1E row files `ercot_storage_capability_measured`
and `ercot_storage_as_deployment` as **GAP**, reasoning: *"the admissible twin
`storage_as_commitment` IS shared, so these two forking to the backcast
orchestrator alone is an asymmetry, not a design."* Since this SOC dock reserves
the energy behind the very same award total the power dock subtracts (rule 19,
one award basis, both sides), symmetry seems to argue for GAP here too.

It does not, and point 4 above is why. `storage_as_commitment`'s "sharedness" is
a **checker-tier fact** — the flag happens to be read inside
`model/reserves/spec.py`, which the checker classes as a shared builder — not an
admissibility fact. Every one of those shared reads is itself gated on
`not ercot_storage_as_endogenous` and annotated *backcast-only record*. So the
measured award series is not a forward input on the power side either; the
forward path is the endogenous split on both sides, symmetrically.

This lane does **not** re-adjudicate those two sibling rows — out of scope, and
GAP is the disposition that decides nothing, so nothing there is wrong today.
The observation is recorded only because it is the reason the sibling row's
premise does not carry over to this field. This field's own docstring answers
rule 13 negatively and a validator enforces the answer; that is stronger
evidence than a neighbour's tier classification.

Membership in `scenarios._BACKCAST_ONLY_OVERLAY_FIELDS` was checked and is
**not** a signal in either direction: neither field is in it, and the set
already mixes dispositions (`carry_operating_mothballs` is in it and is
`BACKCAST_ONLY`; `caiso_offer_surface_measured` is in it and is `GAP`).

### 1.4 Repair

A `BACKCAST_ONLY` row in `scripts/lib/forecast_parity_registry.py` whose reason
names all three required things — measured source, forecast substitute, and the
gating call-site line. Evidence: `scripts/run_calibration.py` (names the field
at :4814/:4827) and `src/market_sim/model/storage.py` (names it at :590). The
checker's stale-declaration guard verifies the field is still not
forecast-wired, so this row cannot rot into a permanent excuse.

---

## 2. NYISO — `nyiso_seam_deliverability_envelope` → `GAP`

### 2.1 The call site, read

`scripts/run_calibration.py:2739-2756` — an **`elif`**, the second limb of a
rule-19 exclusive pair:

```python
if getattr(config, "nyiso_seam_par_attribution", False) and iso == "NYISO":
    ...  # supersedes nyiso_seam_deliverability_envelope
elif (
    getattr(config, "nyiso_seam_deliverability_envelope", False) and iso == "NYISO"
):
    ttc, ttc_import = nyiso_seam_ttc_hourly(
        np.asarray(ttc, dtype=float), iso_config, year, demand.shape[1]
    )
```

Both flags are armed in keeper `2026-09-06-nyiso-196-extract-basis`, so this
limb is **armed but shadowed** at runtime. Shadowing is a fact about the current
keeper, not an admissibility answer — and it is precisely why the field must not
be silenced: a keeper that later drops `nyiso_seam_par_attribution` re-exposes
the fork with no gate left watching.

### 2.2 The admissibility answer: YES

`src/market_sim/data/nyiso_seam_envelope.py:50-58` carries a section headed
**"Admissibility (rule 13 `[R-MEASURED]`)"** that answers both limbs of the test
affirmatively, verbatim:

> "The envelope is a per-neighbour deliverability CAPABILITY, not an outcome
> pinned back into the model: it bounds what the seam may deliver and leaves the
> LP to choose what it does deliver. **It regenerates for a forward year from the
> forward tie set by the same frozen formula and responds to changed conditions**
> (it moves 974 → 828 → 975 MW on `NYC` and 1,012 → 986 → 990 MW on
> `Long_Island` across 2023-25 purely from measured behaviour, and **a new tie
> such as CHPE is picked up automatically**)."

Unlike ERCOT's per-year award corpus, the construction is a **frozen formula over
the tie set** — p90 of the directionally-clipped net schedule within each
(month × hour-of-day) bin, at the definitional repo-wide
`NYISO_SEAM_FLOW_PERCENTILE = 90`, over ties enumerated by physical landing zone
(`NYISO_SEAM_TIE_LANDING`). Add a tie and the envelope picks it up; that is
condition-response in the sense rule 13 asks for.

**Therefore `BACKCAST_ONLY` is unavailable.** A `BACKCAST_ONLY` row would assert
a non-regenerability the code denies — the same reasoning the registry already
records for `caiso_ct_peaker_committed_measured` ("A BACKCAST_ONLY row would
assert a non-regenerability the code denies"). It is also **not** in the
measured-TTC `BACKCAST_ONLY` family by default: `ercot_gtc_limits_measured` is
declared backcast-only because a measured hourly limit imports one historical
year's *outage/derate schedule* forward, which is a different object from a
deliverability envelope built off the tie set.

### 2.3 Why the repair is a wiring plan, not a consumer built here

The charter's YES limb allows "a documented wiring plan if the consumer is a
larger job than this lane." It is, for a reason specific to this field:

- It is the **superseded** member of a rule-19 `[R-ONE-MECH]` exclusive pair.
  Wiring the shadowed limb forward while the limb that actually fires
  (`nyiso_seam_par_attribution`) stays unwired would arm two-of-four links in
  forecast mode and all-four in backcast — a **worse** fork than the one being
  closed.
- `nyiso_seam_par_attribution` is itself an open `GAP` under **owner ruling R-X**,
  which expressly reserved "whether it joins the measured-TTC `BACKCAST_ONLY`
  family or gets a forward channel" to the forecast desk. That row already names
  this field as "pinned open … **on the same question**."

The two are one question and must be answered together, by the desk that owns
it. Filing this field `GAP` beside its twin is the disposition that decides
nothing and hides nothing: GAPs print on every run, are counted in the report
header, and fail under `--strict-gaps`.

### 2.4 Repair

A `GAP` row citing this finding, with evidence `scripts/run_calibration.py`
(names the field at :2740) and `src/market_sim/data/nyiso_seam_envelope.py`.

### 2.5 The wiring question, stated for the NYISO / forecast desk

**Unanswered here, deliberately.** For the desk that takes it:

1. Decide `nyiso_seam_par_attribution` **first** — it supersedes this mechanism
   on its own two links plus two more. This field's answer follows from it and
   should never be set independently.
2. If the pair is wired forward, the seam of record is the TTC overlay block at
   `scripts/run_calibration.py:2699-2756`; the forecast twin would sit on
   `runner.py`'s TTC path, and the forward tie set — not a stored historical
   envelope — must drive it, or the forward claim in §2.2 is not actually
   exercised.
3. The identification refusal is load-bearing and survives any wiring decision:
   `Upstate_West` and `Capital_Hudson` are refused on identification (rule 20
   `[R-DOF]`) because `SCH - PJ - NY` spans the Central-East cutset and no public
   source splits it. A forward channel must not quietly resolve that split.

---

## 3. What was NOT done

- No forecast consumer was built for either mechanism (ERCOT does not want one;
  NYISO's is not this lane's to decide — §2.3).
- No sibling registry row re-adjudicated (`ercot_storage_capability_measured`,
  `ercot_storage_as_deployment`, `nyiso_seam_par_attribution` untouched).
- No keeper, marker, freeze file, bundle or matrix-cell **verdict** changed.
- No solve, score or registration. Zero LP.

---

## 4. Before / after — `$?` read directly

**Before** (clean tree at `origin/main` = `5fdd4374`):

```
$ uv run --frozen python scripts/check_forecast_parity.py; echo "EXIT=$?"
...
SUMMARY: 6 keeper posture(s); 2 unaccounted, 13 filed gap(s), 0 registry failure(s), 0 error(s)
  FAIL  ERCOT: ercot_storage_as_soc_reserve is armed in the keeper with no
        forecast-orchestrator consumer and no registry declaration
  FAIL  NYISO: nyiso_seam_deliverability_envelope is armed in the keeper with
        no forecast-orchestrator consumer and no registry declaration
EXIT=1
```

### 4.1 After — captured run

```
$ uv run --frozen python scripts/check_forecast_parity.py; echo "EXIT=$?"
...
=== ERCOT  2026-09-05-ercot248-two-config-keeper  (107 armed)
  wired 101  alias 0  backcast-only 2  input 0  inert 0  GAP 4  UNACCOUNTED 0
  BACKCAST_ONLY  ercot_storage_as_soc_reserve = True
...
=== NYISO  2026-09-06-nyiso-196-extract-basis  (98 armed)
  wired 93  alias 0  backcast-only 2  input 0  inert 0  GAP 3  UNACCOUNTED 0
  GAP            nyiso_seam_deliverability_envelope = True
...
SUMMARY: 6 keeper posture(s); 0 unaccounted, 14 filed gap(s), 0 registry failure(s), 0 error(s)
EXIT=0
```

No `FAIL` line is printed: **0 unaccounted, 0 registry failures, 0 errors** in
all six ISOs. Filed gaps go 13 -> 14 — the NYISO field moving from *unaccounted*
to *filed*, which is the honest direction. The ERCOT field leaves the gap count
entirely because its forward channel is settled, not open.

### 4.2 Test-suite consequence, handled

`tests/scoring/test_forecast_parity.py::test_check_exits_zero_on_the_current_keepers`
carried `@pytest.mark.xfail(strict=True)` whose own reason read: *"strict=True:
when that lane lands, this marker must be removed rather than left to rot."*
This is that lane, so the marker is removed. The companion
`_FR22_OPEN_UNACCOUNTED` exemption set is deleted rather than emptied, and
`test_all_six_keepers_resolve` now asserts the STRONG form — zero unaccounted in
every ISO, with no exemption list left to rot. `22 passed`; `ruff check` and
`ruff format --check` clean on both edited files.

### 4.3 Rule 28 duty (b)

No mechanism was tested and **no matrix cell verdict changed** (ERCOT
`storage_measured_anchors` and NYISO `seam_flow_envelopes` both stay `K`). An
evidence citation recording the FR-22 disposition was appended to each
mechanism's own ISO shard only — `mechanism-matrix/ERCOT.js` and
`mechanism-matrix/NYISO.js`, never the other's (rule 25 `[R-ISO-SCOPE]`) — so a
later forecast lane reads that ERCOT's channel is SETTLED and NYISO's is an OPEN
question owned by its desk. `scripts/check_mechanism_matrix.py` exits 0.
