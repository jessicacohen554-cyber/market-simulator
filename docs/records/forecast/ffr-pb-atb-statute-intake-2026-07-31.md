# FFR-PB — ATB vintage intake + §45Y/48E primary-statute verification

**Session:** FFR-PB (forecast-readiness prompt pack §FFR-PB), 2026-07-31.
**Scope:** FR-20 items **M1** (ATB vintage) and **M2** (IRA phase-down statute).
**DATA + CITATIONS ONLY — no LP solved, no parameter value changed, nothing registered.**

## Headline

Both "manual downloads" closed, and **neither actually needed a manual download** —
each was blocked on a premise that turned out to be wrong:

| Item | Audit premise | What is actually true |
|---|---|---|
| **M1** | "ATB vintage 2024, **two editions behind**; `atb.nrel.gov` blocked, OEDI has ≤2024" | **No ATB 2025 or 2026 edition exists.** 2024 is the current edition. The real gap was a *point-version*: OEDI published ATB 2024 **v4.0.0** on **2026-07-28**; the repo held **v3.0.0**. Fetched over the existing OEDI channel and landed. |
| **M2** | "2033–36 steps triangulated from secondary OBBBA alerts; Federal Register bot-walled" | The **codified statute** controls, and `uscode.house.gov` (Office of the Law Revision Counsel) **is reachable**. All four step years **confirmed unchanged** from primary text. |

**No value changed anywhere in the model.** M1 landed data beside the pinned vintage;
M2 was a pure provenance upgrade. Rule 23 satisfied on both.

## M1 — ATB 2024 v4.0.0 landed

### There is no ATB 2025/2026

Three independent checks, all agreeing:

- **OEDI listing** (`ATB/electricity/{csv,parquet}/`) ends at `2024/` — re-probed this session.
- **The publisher's own site.** `atb.nrel.gov` is still proxy-blocked (CONNECT 502), but the lab
  renamed and the site moved to **`atb.nlr.gov`**, which **is reachable here**. It states
  *"The 2024 Electricity ATB is live!"* and its most recent electricity page is `2024b`.
- **PUDL's raw-ATB archive** (Zenodo 15772175, v8.0.0, published 2025-07-01) covers 2019–2024 only.

> **Standing note for later sessions:** try **`atb.nlr.gov`** before recording an ATB page as
> unreachable. The `atb.nrel.gov` block that shaped the FF-0D/FF-1E write-ups is a *domain*
> block, not an ATB block.

The `data/raw/nrel-atb/README.md` claim that 2024 is the "final" edition was overstated
(nothing declares it last) and has been softened; its *no-2025/2026* half re-verified and stands.
**The FR-20 "two editions behind" framing was simply wrong** and is corrected in the audit.

### What v4.0.0 changes

Source object `ATB/electricity/csv/2024/v4.0.0/ATBe.csv` — 102,696,929 B / 585,631 rows
(v3.0.0: 98,516,887 B / ~572k). Run through the **unmodified** `fetch_nrel_atb.filter_atb`
and diffed against the committed v3.0.0 extract:

- **Key coverage identical** — 3,858 rows, zero added, zero removed; `display_name`,
  `default` and `atb_year` unchanged on every row.
- **56 values changed** beyond float noise — **all** of them
  `Geothermal` / `DeepEGSFlash` / `Moderate`: CAPEX for 28 years (max **+6.14 %**;
  2030: `7897.52` → `8315.49` 2022 $/kW) and Fixed O&M for 28 years (max **+2.00 %**).
- 16 further rows differ only in last-digit serialization (≤1e-12 relative) — the ulp drift
  the raw README already documents.
- **Every entry technology is unchanged**: wind, solar, gas CC/CT/CCS, nuclear, all five battery
  durations, offshore wind, and the other three EGS classes.

**Consequence for FR-20:** the "2024–26 cost escalation vs a frozen ATB vintage" concern is
**not** an ATB-vintage artifact — NREL's own refresh moved nothing in this model's entry-cost
set. The one live consumer exposure is EGS: `derive_egs_fom` reads `NFEGSFlash` (unchanged), but
`GEOTHERMAL_PARAMS`' EGS capex band and any DeepEGS-derived figure would move on a re-derive.

### How it landed (intake contract)

- **Raw (additive; v3.0.0 bytes untouched):**
  `data/raw/nrel-atb/atb_2024v4_electricity_filtered.part{00..09}.csv`, 3,858 rows.
  **Verified byte-for-byte reproducible** from a fresh
  `fetch_nrel_atb.py --atb-version v4.0.0` run.
- **Schema:** new **`atb_version`** column, added to `key_columns`. An ATB *edition* is
  re-released under successive *versions*, so edition-year alone never identified a vintage;
  with the version in the key, v3.0.0 and v4.0.0 coexist in the one partition instead of
  colliding.
- **Curation:** `curate_nrel_atb` gains a version registry (stem → edition/version/OEDI key).
  `curate()` writes **every** landed version (7,716 rows); `parse()` defaults to
  **`DERIVATION_PINNED_VERSION = "v3.0.0"`**.
- **Fetch:** `fetch_nrel_atb.py` writes a per-version filename stem (a new version can never
  overwrite the extract a constant was derived from); default now tracks the latest, `v4.0.0`.
- **Orchestrator:** `nrel-atb` *and* `ira-credit-parameters` added to `regenerate_clean.py`
  `DATATYPES` — both had a `curate_*.py` since intake but were never listed, so a bare
  `regenerate_clean.py` run silently skipped them. Both verified to run clean.
- **Tests:** 4 new cases (versions coexist; `parse` honours the pin; unknown version rejected;
  edition-year/stem mismatch rejected). **27 passed**, including the two rule-23 consistency
  tests that assert the committed constants still equal their derivation.

### Why NEW_ENTRY_COSTS was not re-derived

Out of scope by instruction — **FFR-SC** owns the re-derive. The pin is what makes that a clean
single change: flip `DERIVATION_PINNED_VERSION` to `v4.0.0`, re-run
`derive_entry_costs_from_atb.py` / `derive_cost_benchmark_envelope.py`, and let
`tests/unit/config/test_atb_entry_cost_consistency.py` + `tests/scoring/test_cost_benchmark_envelope.py`
gate it. Expect movement **only** in the DeepEGS-derived figures.

## M2 — §45Y/§48E phase-down verified against primary text

Read from the **Office of the Law Revision Counsel** US Code (`uscode.house.gov`, prelim
edition). The Federal Register bot-wall is real and unchanged — it was simply **never the
source needed**: these four years are set on the face of the statute, and post-OBBBA the
Secretary has no determination left to make.

**26 U.S.C. §45Y(d)(2)** — phase-out percentage by the calendar year construction *begins*,
relative to the "applicable year":

> (A) first calendar year following … **100 percent**, (B) second … **75 percent**,
> (C) third … **50 percent**, (D) any calendar year subsequent to (C) … **0 percent**.

**26 U.S.C. §45Y(d)(3)**, as amended by **OBBBA Pub. L. 119-21 §70512(a)(2)**, now reads in its
entirety:

> "For purposes of this subsection, the term 'applicable year' means calendar year 2032."

**⇒ applicable year 2032 gives exactly 100 % BOC-2033 / 75 % BOC-2034 / 50 % BOC-2035 /
0 % BOC-2036+ — the model's `ira_other_clean_{last_full,75pct,50pct,phaseout_end}` =
2033 / 2034 / 2035 / 2036, CONFIRMED UNCHANGED.**

Three findings the primary read added beyond confirmation:

1. **OBBBA removed a contingency.** It *struck* the prior (d)(3), which had read *"the later
   of— (A) the calendar year in which the Secretary determines that … greenhouse gas emissions
   from the production of electricity in the United States are equal to or less than 25 percent
   of [2022's], or (B) 2032."* Pre-OBBBA these steps could have slid **later** if the grid
   decarbonized fast enough. They no longer can — the schedule is a flat statutory certainty.
2. **The parameter name is now a misnomer.** `45Y,applicable_year_treasury_determination` in the
   citation store describes a Treasury determination that no longer exists. Kept for key
   stability, with the correction recorded in the row's `notes`.
3. **Exact amending sections.** OBBBA amended §45Y(d)(1) and replaced (d)(3)/added (d)(4); it did
   **not** touch the (d)(2) percentage table, which is original IRA text (Pub. L. 117-169
   §13701(a)). Likewise §48E(e)(2)-(3) are original (§13702(a)) — OBBBA §70513(a) amended only
   (e)(1) and added (e)(4). The OBBBA effect reaches §48E purely through the (e)(3)
   cross-reference to §45Y(d)(3). Citations now say so precisely rather than blanket-crediting
   OBBBA.

Also confirmed in passing, and upgraded from secondary to primary:

- **§45Y(d)(4)(A)**: wind/solar "applicable facilities" get no credit if **placed in service
  after 2027-12-31** → `ira_wind_solar_last_year = 2027` stands.
- **OBBBA §70512(l)(2)** effective-date note: the termination applies to facilities whose
  construction begins **after 12 months from 2025-07-04**, i.e. **after 2026-07-04** →
  the `wind_solar_boc_grandfather_deadline = 2026-07-04` row stands.
- **§48E(e)(2)** names **"energy storage technology"** expressly — the statutory basis for
  storage sitting in the model's "other clean" bucket.

**Modelling caveat left standing (unchanged, and correct as documented):** the statute keys the
percentage to *beginning of construction*; `ira_phaseout_fraction` applies it by model year,
using build/entry year as the BOC proxy. That approximation is stated in the `ira.py` docstring.

### Citation edits (values untouched)

- `src/market_sim/config/scenarios.py` — the `ira_other_clean_*` block: triangulation caveat
  replaced with the primary citation, including the struck-(d)(3) history.
- `src/market_sim/policy/ira.py` — `ira_phaseout_fraction` docstring, same.
- `data/raw/policy/ira-credit-parameters/ira-credit-parameters.csv` — all 8 phase-down rows plus
  the applicable-year and 2 wind/solar rows re-cited to codified sections with exact
  subparagraph `source_page`s. **Zero secondary (Sidley) citations remain** on any 45Y/48E row.
- `data/raw/policy/ira-credit-parameters/README.md` — RESOLVED section added; the old confidence
  note kept as historical record; its MANUAL DOWNLOAD checkbox closed.

## MANUAL DOWNLOADS NEEDED

**None from this session.** Both of its assigned items (M1, M2) resolved over reachable
channels. No value was guessed anywhere; where a source was blocked (`atb.nrel.gov`,
`federalregister.gov`) a *different primary channel* for the same fact was found and cited
(`atb.nlr.gov` + OEDI; `uscode.house.gov`).

Unrelated rows M3–M15 in `ff-inputs-currency-audit-2026-07.md` §7.3 are untouched and remain open.

## Files changed

| File | Change |
|---|---|
| `data/raw/nrel-atb/atb_2024v4_electricity_filtered.part{00..09}.csv` | **new** — ATB 2024 v4.0.0 extract (3,858 rows) |
| `data/dictionary/schema/nrel-atb.schema.yaml` | `atb_version` column + key; 2022$ caveat closed; description/`source_doc` updated |
| `scripts/data/curate_nrel_atb.py` | version registry, `available_versions`, versioned `parse`/provenance, `curate` writes all versions |
| `scripts/data/fetch_nrel_atb.py` | per-version output stem, default → v4.0.0 |
| `scripts/regenerate_clean.py` | registered `nrel-atb`, `ira-credit-parameters` |
| `tests/curation/test_curate_nrel_atb.py` | 4 new version-axis cases |
| `data/raw/nrel-atb/README.md` | editions-vs-versions section, v4.0.0 delta, `atb.nlr.gov` note, "final edition" softened |
| `src/market_sim/config/scenarios.py`, `src/market_sim/policy/ira.py` | primary-statute citations (comments/docstrings only) |
| `data/raw/policy/ira-credit-parameters/{README.md,ira-credit-parameters.csv}` | primary citations; MANUAL DOWNLOAD closed |
| `data/dictionary/data-dictionary.md`, `scripts/render_data_dictionary.py` | regenerated / blurb |
| `docs/forecast-readiness-audit-2026-07.md` | FR-20 row + Phase-5 line corrected |
| `docs/handoffs/ff-inputs-currency-audit-2026-07.md`, `docs/handoffs/ff-1e-policy-currency-2026-07.md` | M1/M2 closed with the corrected premises |

## Verification run in-session

- `fetch_nrel_atb.py --atb-version v4.0.0` against the downloaded source reproduces the
  committed parts **byte-for-byte**.
- `curate_nrel_atb.curate()` → 7,716 rows, both versions, `validate_clean` passes.
- `regenerate_clean.py nrel-atb ira-credit-parameters` → both `[ ok ]`.
- `pytest tests/curation/test_curate_nrel_atb.py tests/unit/config/test_atb_entry_cost_consistency.py tests/scoring/test_cost_benchmark_envelope.py` → **27 passed**.
- `ruff check scripts/ src/ tests/curation/test_curate_nrel_atb.py` → clean.
- Pre-existing, unrelated: `tests/curation/test_egrid_boundary_heat_rate.py` fails on a missing
  optional pandas Excel dependency in this environment — confirmed failing on an unmodified
  tree (10 failures there vs 3 here is dependency-install ordering, not this change).

## Rule notes

- **Rule 13 `[R-MEASURED]`** — ATB is a forward-regenerating published cost input; statute years
  are policy parameters. Neither is an outcome pinned to a residual.
- **Rule 21 `[R-FROZEN-DERIVE]`** — no derived parameter re-derived. The new ATB version is
  landed but **not consumed**; the pin holds the derivation to v3.0.0 until FFR-SC acts.
- **Rule 23 `[R-REGISTRY]`** — every value stays in `ScenarioConfig`/`constants.py` with a
  citation; nothing new is tunable.
- **Rule 28 `[R-MECH-MATRIX]`** — no mechanism proposed, tested, or armed; no
  `ScenarioConfig` field added. No matrix cell applies.
- **No solve** of any kind, in any year. No holdout year touched (rule 20).
