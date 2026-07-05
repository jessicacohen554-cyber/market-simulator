# Confirmed-vs-announced retirement channel — design plan (W0-P2)

**Date:** 2026-07-05 · **Produced by:** Fable session (W0-P2 of
`docs/fable-prompt-pack-2026-07.md`) · **Implements:** audit findings RC-1…RC-5
(`docs/fable-repo-audit-2026-07.md` §B) · **Consumed by:** W2-P2 (implementation
prompt in §8 below). **Design only — no mechanism code changed in this session.**

## 0. Owner intent and the design in one paragraph

Only **confirmed** retirements — units already offline, or future exits bound by an
enforceable instrument (RTO deactivation acceptance, consent decree, statute, PUC
order) — are exogenous. **Announced** retirements (EIA-860 planned dates, IRP/press
announcements) stay with the economic-retirement screen, because under current demand
growth plants scheduled for retirement keep staying online. Today's fuel-type proxy
(fossil ignores all dates, non-fossil honors all dates) is right in spirit but has no
channel to force a genuinely confirmed fossil closure (RC-1), drops the EIA-860
status/month signal at intake (RC-2), and force-retires non-fossil units on
speculative 2040–2072 end-of-life placeholders (RC-5). The design: a new
`confirmed-retirements` curated datatype (per-ISO registry of binding instruments,
schema-first), a forecast-mode **confirmed-exit injector** mirroring
`load_planned_additions`' construction-committed philosophy, a **data-horizon
confirmation gate** on non-fossil announced dates, and the RC-3 rename that makes the
"Known retirements" fossil no-op explicit. The channel is empirically load-bearing:
instrumented 2026–2029 forecast probes (§3) show the economic screen retires **zero**
units in both ERCOT (reliability floor in permanent deficit rescues everything) and
PJM (capacity revenue + low FOM bars keep 1,385 of 1,387 units loss-free) — without
an exogenous channel, consent-decree-bound units like Rockport run to 2050.

## 1. Current state (verified against code, 2026-07-05)

| Piece | Where | Behaviour |
|---|---|---|
| Date-based retirement step | `capacity.apply_known_retirements` (`capacity.py:201-235`), step 1 of `evolve_fleet` (`capacity.py:1674-1681`) | Drops any unit with `retirement_year <= year` — **except** fossil (`_FOSSIL_FUELS`, `capacity.py:196-198`) when `forecast_fossil_retirement_economic=True` (default, `scenarios.py:168`). For the entire fossil fleet, step 1 is a default no-op (RC-3). |
| First simulated year | `fleet.build_base_fleet` (`fleet.py:6623-6690`) | Applies **no** retirement dates at all — even a non-fossil unit whose announced date ≤ START_YEAR stays in the first year's fleet; dates only bite from year 2 via `evolve_fleet`. |
| EIA-860 intake | `scripts/process_eia860.py:53-66` (`_GENERATOR_COLUMN_MAP`) | Carries `Status` and `Planned Retirement Year` into `eia860_generators.parquet`, but **drops `Planned Retirement Month`** for operable units; the retired-sheet statuses (RE/CN/IP) surface only in the backcast within-window retiree build (`:246-347`). |
| Fleet loader | `fleet.py:3104-3106` | Hard-filters `status == "OP"` — SB (standby/mothball, 1,501 units), OS (out of service, not expected to return, 538) and OA (220) never reach the model; downstream `Generator` has no status field, so the distinction is unrepresentable (RC-2). |
| Exogenous-exit channels | `runner.py:372-374` (within-window retirees), `fleet.py:1987-1992` (COD ramp) | Both **backcast-gated**. Forecast mode has no exogenous exit channel of any kind beyond the non-fossil date honor above (RC-4). |
| Known additions (the philosophy to mirror) | `fleet.load_planned_additions` (`fleet.py:3750+`), `_PLANNED_FIRM_STATUSES = {U, V, TS}` (`fleet.py:3747`) | Only construction-committed statuses enter; announced-but-uncommitted (`P`) is excluded. Forecast-only. |

Population (EIA-860 2025 Early Release, committed parquets, verified by inspection):
the operable sheet carries **558** units with a planned retirement year (525 OP,
19 SB, 10 OS, 4 OA), of which **205** fall in 2026–2028 (70/72/63). Filtered to the
seven modeled markets (`eia860_generators.parquet`): 345 units with planned years —
192 fossil, 153 non-fossil. The non-fossil tail runs to **2065** (53 conventional
hydro and 54 solar rows, many of them FERC-license/EOL placeholders at 5–30 MW), and
includes 3 nuclear units (1,871 MW, 2030–2034). The 2026–2028 fossil subset in
modeled ISOs is ~26.5 GW, dominated by MISO (13.5 GW) and PJM (5.6 GW) coal/gas-steam.

## 2. The authoritative confirmed-retirement signal

### 2.1 What EIA-860 has — and what it does not

Raw files inspected: `eia860_generator_operable.parquet` (73 cols),
`eia860_generator_retired_and_canceled.parquet` (57 cols),
`eia860_generator_proposed.parquet` (47 cols).

Available signals:

* **Operable `Status`**: `OP` operating · `SB` standby/backup (mothballed —
  reversible, ~1,501 units) · `OA` out of service, expected back within the year ·
  `OS` out of service, **not** expected back within the year (538 units — de facto
  exits that have not filed retirement paperwork).
* **Operable `Planned Retirement Month`/`Year`**: the owner's self-reported
  *intention*. Month exists in raw but is dropped at intake today.
* **Retired-and-canceled sheet**: `RE` retired (actual, with actual
  `Retirement Month/Year` — fact) · `CN` canceled · `IP` planned but indefinitely
  postponed.

What EIA-860 does **not** have: any confirmation/bindingness flag on a planned
retirement. Form 860 asks *whether* and *when* the owner plans to retire the
generator — not whether that plan is enforceable. The 2026–2028 planned population
mixes consent-decree-bound exits with announcements that have already been
countermanded (see §2.3 examples). **Conclusion: the confirmed-vs-announced
distinction cannot be derived from EIA-860 alone; it requires an external
instrument registry.** EIA-860 contributes (a) the retired facts (already handled:
operable snapshot + within-window retirees), (b) the announced universe to
cross-check the registry against, (c) `OS` status as a *seeding aid* — a list of
units to investigate for instruments — never as auto-confirmation (it is
self-reported too), and (d) the identity/capacity spine (`plant_id`,
`generator_id`, MW) every registry row must join to.

### 2.2 External binding instruments, per ISO

The instrument classes below are public, re-queryable at every intake vintage, and
enforceable — the retirement analogue of the additions pipeline's U/V/TS statuses.

| ISO | Binding instrument (confirmation) | Public source to re-query |
|---|---|---|
| PJM | Deactivation request past reliability review, with confirmed deactivation date (no RMR); RMR **end** date where an RMR exists | PJM "Generator Deactivations" posting (XLSX of requests with status and dates) |
| MISO | Attachment Y retirement request **approved** (suspensions excluded — reversible) | MISO generator retirements / Attachment Y public status posting |
| NYISO | Generator Deactivation Notice completed per OATT deactivation process; state (DEC/PSC) orders | NYISO deactivation notices posting; Gold Book retirement table as cross-check (announced-grade only) |
| ISO-NE | Retirement / Permanent De-List Bid **cleared** in FCA (binding under the tariff); Non-Price Retirement Request approved | ISO-NE retirements & FCA results postings |
| CAISO | No RTO deactivation regime → state instruments: SWRCB once-through-cooling compliance dates, CPUC decisions (e.g. SB 846 Diablo Canyon schedule), CEC filings | SWRCB OTC compliance schedule table; CPUC/CEC dockets |
| ERCOT | Notification of Suspension of Operations (NSO) accepted with RMR review concluded **without** an agreement; permanent (not seasonal) suspensions | ERCOT market notices / suspension-retirement notices |
| all | Federal consent decrees & court-approved settlements (EPA/DOJ NSR cases — e.g. the Rush Island order that retired the plant in 2024); state statutes with dated closure mandates (IL CEJA, NY/WA/OR coal phase-outs); PUC-approved settlement/securitization orders with named exit dates | court dockets, state PUC dockets, statute text |

**Counter-instruments** — events that *remove or defer* confirmation and must be
representable, not deleted (rule 26 analogue: auditability): RMR/must-run
agreements (PJM Brandon Shores/Wagner through ~2029; ERCOT Braunig), DOE §202(c)
emergency orders (Eddystone 3–4, May 2025), deactivation-request withdrawals,
statute amendments (SB 846 superseding Diablo Canyon's earlier confirmed 2024/25
exit). A registry row hit by a counter-instrument is marked `superseded` with the
citation, keeping the audit trail while the loader ignores it.

### 2.3 Rule-13 admissibility

The test: *could this same quantity be produced for a forward year from forward
drivers, and would it respond to changed conditions?* Yes on both counts:

* **Regenerates forward:** the registry is rebuilt at every intake vintage by
  re-querying the same public lists/dockets — exactly how the additions pipeline
  re-reads U/V/TS from each EIA-860 vintage. Nothing in it is fitted to a residual
  or copied from an outcome; it is market/legal structure, like an outage window or
  a TTC limit.
* **Responds to changed conditions:** the instrument set itself responds — RMR
  agreements, 202(c) orders and statute amendments move units *out* of the
  confirmed set (the 2026–2028 planned population already contains both directions:
  Rockport 1–2 bound by the AEP NSR consent-decree modification vs Eddystone 3–4
  announced for 2026 but compelled to run by a federal 202(c) order). Everything
  not confirmed stays with the economic screen, which is fully
  condition-responsive.

What stays **inadmissible** (rule 13's forbidden side): treating EIA-860 announced
dates as exogenous (an intention, not an instrument — the very failure the owner
flagged), auto-confirming from `OS`/`SB` status, or tuning the confirmed set to
close a capacity/price residual. The registry is also **not** a backcast device:
historical exits are already carried by the vintage snapshot + within-window
retirees; the registry's purpose is forward.

## 3. Empirical check — does the economic screen retire the near-term confirmed subset on schedule?

Probe: default-config **forecast** runs (`ScenarioConfig()` defaults,
`mode="forecast"`), ERCOT and PJM, horizon shortened to 2026–2029 by overriding
`runner.END_YEAR` in a scratch harness that wraps `apply_known_retirements` /
`apply_economic_retirements` / `evolve_fleet` to record every retirement decision,
per-unit loss counters, and the survival of the 2026–2028 planned-retirement plants.
Diagnostic only (not registered anywhere); harness preserved in the W2-P2 prompt's
verification step.

**Result: the economic screen retired ZERO units in either ISO through 2029 —
the near-term confirmed subset does not exit on schedule, and it fails for two
different reasons.** (ERCOT solved 2026–2029 in ~6 min, PJM in ~13 min; harness:
scratch `retire_probe.py`, reproduced in the W2-P2 verification step.)

* **ERCOT — floor-inert.** J K Spruce's coal tranches hit the coal loss threshold
  (counter 1 ≥ `retirement_years_coal=1`) at the very first screen (entering 2027)
  and O W Sommers' gas-steam tranches reached counter 3 by 2029 — both *eligible*,
  neither retired, no unit of any kind retired. Cause: the reliability floor is in
  permanent deficit — `(peak − firm_clean) × 1.15` ≈ 1.15 × (~90 GW − 0.5 GW hydro)
  ≈ **103 GW floor vs ~79–81 GW total thermal** (wind/solar/storage count zero, the
  audit's CX-3), so the floor unconditionally rescues every eligible unit and the
  economic-retirement mechanism is completely inert in ERCOT forecasts. 469 of 633
  units carried nonzero loss counters with zero exits.
* **PJM — profitability-inert.** Only **2 of 1,387** units ever record a loss year
  (2027–2029): with the capacity-market revenue stream and going-forward FOM bars
  1.5–2.5× below ATB (CX-1), essentially the whole thermal fleet covers its fixed
  cost. Kincaid (announced 2027), Cardinal 3 / Rockport 1–2 (2028, Rockport
  consent-decree-bound) and Eddystone's tranches sit at counter 0 every year —
  ~5.5 GW of announced-or-confirmed 2026–2028 exits runs to the horizon. PJM
  thermal *grows* 169.8 → 177.8 GW over the window (planned additions + entry,
  zero exits).
* **New finding (beyond RC-1…5): `bins_to_fleet` drops announced dates for every
  binned thermal plant.** The tranche `Generator`s carry `retirement_year=None`
  (verified in both probes' base fleets: Spruce/Sommers/Kincaid/Rockport/Eddystone
  all `None`; zero mentions of retirement in `fleet.py:5706+`). Only raw non-binned
  units keep dates (in PJM: six small oil/biomass units). So even
  `forecast_fossil_retirement_economic=False` (the "legacy honor-everything"
  toggle) is a no-op for the binned fossil fleet, and the fossil-exemption logging
  in step 1 sees almost nothing. Design consequence: the confirmed-exit injector
  must join the registry to the fleet by **`plant_code`** (robust to binning), not
  rely on `Generator.retirement_year` plumbing — §5.1 does exactly that.

Structural observations independent of the numbers:

* **A 2026 exit can never happen in 2026:** economic retirement needs
  `prior_results`, so the screen first fires entering 2027; `build_base_fleet`
  applies no dates in the first year. Any unit already confirmed to close in the
  first simulated year is mis-carried for a full year without the injector.
* **Granularity:** confirmed exits are unit-level; the fleet is plant-binned (e.g.
  J K Spruce is one 1,488.5 MW COAL bin, but only unit 1 — 566 MW — carries the
  2028 date). The economic screen can only retire the whole bin; a correct
  confirmed channel must **derate** a bin by the exiting unit's MW.
* **Known bias context (audit CX-1):** going-forward FOM bars sit 1.5–2.5× below
  ATB, so the screen systematically under-retires — near-term confirmed coal exits
  are precisely where that bias does the most emissions damage (audit's stated
  ±10% asset-level emissions objective).

## 4. Data intake design (`confirmed-retirements` datatype)

Per the data-intake skill: schema first, per-ISO registry modules, no `if iso ==`
ladders, `write_clean`/`read_clean` seam, tmp-CLEAN_DIR tests. The
`capacity-deliverability` datatype is the pattern to copy — it already solved the
"heterogeneous PDF-published per-ISO sources → hand-curated raw CSV extracts with
full provenance → one tidy canonical frame" problem this datatype shares.

### 4.1 Schema — `data/dictionary/schema/confirmed-retirements.schema.yaml`

```yaml
datatype: confirmed-retirements
schema_version: 1
title: Confirmed generator retirements (binding-instrument registry)
description: >-
  One row per (unit, instrument): generating units whose retirement is bound by an
  enforceable public instrument — RTO deactivation acceptance, consent decree,
  statute, regulatory order — with the instrument's exit date and full provenance.
  Announced/intended retirements (EIA-860 planned dates, IRPs, press releases) do
  NOT belong here; they remain with the economic-retirement screen.
key_columns: [iso, plant_id, generator_id, instrument_id]
allow_additional_columns: false
columns:
  - {name: iso,               dtype: string,  unit: none, nullable: false,
     description: ISO/RTO the unit belongs to (ERCOT/CAISO/PJM/MISO/NYISO/NEISO).}
  - {name: plant_id,          dtype: int64,   unit: none, nullable: false,
     description: EIA plant code (joins the EIA-860 fleet spine).}
  - {name: generator_id,      dtype: string,  unit: none, nullable: false,
     description: EIA-860 generator ID within the plant.}
  - {name: unit_name,         dtype: string,  unit: none, nullable: true,
     description: Human-readable plant/unit label for review.}
  - {name: capacity_mw,       dtype: float64, unit: mw,   nullable: true,
     description: Nameplate MW cross-check against EIA-860 (mismatch >5% fails curation).}
  - {name: exit_year,         dtype: int64,   unit: year, nullable: false,
     description: Calendar year the instrument requires the unit offline.}
  - {name: exit_month,        dtype: int64,   unit: month, nullable: true,
     description: Month (1-12) within exit_year where the instrument specifies one.}
  - {name: confirmation_class, dtype: string, unit: none, nullable: false,
     description: One of rto_deactivation | consent_decree | statute |
       regulatory_order | rmr_end. Vocabulary is closed; announced/intended is
       deliberately NOT a member.}
  - {name: instrument_id,     dtype: string,  unit: none, nullable: false,
     description: Short stable slug for the instrument (e.g. pjm-deact-2027-xyz,
       ilcs-ceja-2030), unique per (unit, instrument).}
  - {name: instrument,        dtype: string,  unit: none, nullable: false,
     description: Full citation — docket/case number, order name, date signed.}
  - {name: instrument_date,   dtype: datetime64[ns], unit: none, nullable: true,
     description: Date the instrument became binding.}
  - {name: superseded,        dtype: bool,    unit: none, nullable: false,
     description: True when a counter-instrument (RMR, DOE 202(c), amendment,
       withdrawal) suspends this row. Kept for audit; loader ignores.}
  - {name: superseding_instrument, dtype: string, unit: none, nullable: true,
     description: Citation of the counter-instrument when superseded.}
  - {name: source_url,        dtype: string,  unit: none, nullable: false,
     description: Authoritative URL of the instrument or the RTO posting row.}
  - {name: source_doc,        dtype: string,  unit: none, nullable: true,
     description: Document title / page reference within source_url.}
  - {name: accessed,          dtype: datetime64[ns], unit: none, nullable: false,
     description: Date the source was last re-queried (the intake vintage stamp).}
  - {name: notes,             dtype: string,  unit: none, nullable: true,
     description: Free-text context (e.g. partial-plant scope, fuel-conversion vs closure).}
```

Tidy long frame, one row per (unit, instrument): a unit can legitimately carry a
consent-decree row *and* a superseded earlier row; `read` takes the earliest
non-superseded exit per unit. A **fuel conversion** (coal→gas) is *not* a
retirement row for the plant — only the coal-unit identity exits; note it in
`notes` and let the conversion itself be handled as it is today (out of scope here).

### 4.2 Raw home and per-ISO registry

* `data/raw/confirmed-retirements/README.md` — sources table (§2.2), the exact
  expected layout, and `DATA NEEDED:` lines for each ISO's un-pulled list.
* `data/raw/confirmed-retirements/<iso>.csv` — hand-curated extract per ISO in the
  schema's column vocabulary (like capacity-deliverability's retrieval CSVs; these
  sources are PDFs/web postings, so curation is human-in-the-loop by design —
  provenance columns are what keep it reproducible).
* `scripts/lib/confirmed_retirements/__init__.py` — `IsoSpec` dataclass +
  `register()` + generic CSV parser (copy the capacity_deliverability pattern);
  `scripts/lib/confirmed_retirements/<iso>.py` — one module per ISO registering its
  spec (source URLs, any native→canonical column aliases, expected
  confirmation-class vocabulary). No shared-code ISO branching; a new ISO is a new
  module.
* `scripts/curate_confirmed_retirements.py` — reads only `data/raw`, validates each
  row against the EIA-860 spine (plant/generator exists; MW within 5%;
  `exit_year >= RETIREMENT_WINDOW_START`), writes via
  `clean_io.write_clean(df, "confirmed-retirements", iso=…, source=…)` +
  `validate_clean`; `curate(raw_root=None, isos=None) -> list[Path]`; registered in
  `regenerate_clean.py` `DATATYPES`. `year=None` (spanning registry; exit_year is a
  column, not a partition).

### 4.3 Seed registry (initial intake targets — verify instruments at intake time)

Candidates identified this session; each needs its instrument confirmed and cited
before the row is committed (post-Jan-2026 developments must be re-checked):

* **PJM:** Rockport 1–2 (AEP NSR consent-decree modification; 2028); Kincaid 1–2
  (announced 2027 — statute backstop is IL CEJA's 2030 private-coal deadline: the
  *2030* date is the confirmable one unless a binding 2027 instrument exists);
  Brandon Shores / H.A. Wagner — **superseded examples** (RMR through ~2029; enter
  with `superseded=false` rows keyed to the RMR **end** date, class `rmr_end`).
  Eddystone 3–4 — **counter-instrument example** (DOE 202(c), May 2025): announced
  2026 date must NOT enter as confirmed.
* **ERCOT:** Braunig 1–3 (NSO filed; unit 3 under an RMR-type agreement —
  `rmr_end` class for the agreement's end, others verify); J K Spruce 1 /
  O W Sommers 1 (CPS announcements — **announced-grade unless** a binding
  settlement emerges; expected to stay OUT of the registry).
* **CAISO:** SWRCB OTC compliance-date table (Alamitos/Huntington Beach/Ormond
  Beach extensions — statute/regulatory_order class, amendment history is the
  worked superseded example); Diablo Canyon per SB 846 (2029/2030).
* **MISO:** Attachment Y **approved** retirements in the 13.5 GW 2026–2028 coal
  cluster (largest single block of confirmed-candidate capacity; itemize from the
  public Attachment Y posting).
* **NYISO/NEISO:** deactivation notices / cleared permanent de-list bids
  (Mystic-class exits are already historical; forward list is short).

#### 4.3.1 Second intake pass — status update (2026-07-05)

The five ISOs left `DATA NEEDED` after W2-P2 (ERCOT, MISO, NYISO, NEISO,
CAISO) were researched and, where an enforceable instrument actually cleared
the admissibility bar, seeded. PJM's original rows were also re-verified
against current postings/dockets and corrected. All rows below pass
`curate_confirmed_retirements.py`'s EIA-860 spine cross-check.

* **PJM** (corrected, not re-seeded): Rockport's two units turned out to be
  governed by two separate instruments — Unit 1 by the federal NSR consent
  decree, Unit 2 by a distinct Indiana IURC Cause No. 45546 settlement order —
  split from the single citation the first pass used for both. Eddystone's
  `exit_year` was corrected 2026→2025 (the PJM-approved date the DOE 202(c)
  order actually supersedes was 2025-05-31). Brandon Shores/Wagner's
  `instrument_date` was corrected to the actual FERC RMR-settlement approval
  date (2025-05-01); a further extension to 2031-05 is pending FERC approval,
  not yet applied.
* **ERCOT** — seeded: V H Braunig 1–2 (binding NSO, effective 2025-03-31).
  Independently cross-validated against `fleet.py`'s existing
  `BIN_FORCED_DERATE_BY_YEAR["SC_STGAS3"]` hardcoded 2025-only derate comment,
  which cites the identical 225 MW/252 MW split — these registry rows are the
  general, forward-projecting data that hardcoded derate is a placeholder for
  (rule 24); wiring the injector to consume it in place of the hardcode is a
  follow-up, not done here. Unit 3 stays out (RMR-bound, i.e. being kept
  *in* service, through 2027-03). Spruce/Sommers remain announced-grade.
* **MISO** — seeded: DTE Monroe 1–4 (Michigan PSC Case No. U-21193 — Units
  3–4 by 2028, Units 1–2 by 2032). This is the only candidate in the ~13.5 GW
  EIA-860-flagged 2026–2028 coal cluster that cleared the admissibility bar;
  MISO's own Attachment Y posting could not be fetched directly (TLS/access
  failures) — a follow-up direct pull is still needed to confirm no other
  approved retirements exist in that posting.
* **NYISO** — still `DATA NEEDED`, honestly: every forward-looking completed
  deactivation notice found (Far Rockaway, Gowanus/Narrows, Pinelawn) has
  since been reversed by a NYISO reliability determination (returned to
  service or withdrawn). Zero qualifying rows is the correct, researched
  outcome, not an unresearched gap.
* **NEISO** — seeded: Merrimack Station 1–2 (2024 Clean Water Act consent
  decree, 2028-06 — the plant fully ceased operating 2025-09-12, ahead of the
  decree deadline). The ISO-NE de-list-bid tracker's other candidates could
  not be matched to a current EIA-860 identity and were excluded rather than
  seeded on an unverified match (the tracker file itself is flagged stale,
  last updated 2024-02-28).
* **CAISO** — seeded: AES Alamitos 3–5 / AES Huntington Beach 2 / Ormond
  Beach 1–2 (SWRCB Resolution 2023-0025, 2026-12-31) and Diablo Canyon 1–2
  (SB 846 + CPUC D.23-12-036, 2029/2030) with two `superseded` rows carrying
  the plant's earlier 2016-settlement dates — the worked `superseded`
  audit-trail example the schema was designed around.

**Net effect: the default-flip decision (§7) is now unblocked on data
grounds for all six ISOs** (five seeded, NYISO's zero is itself a completed,
researched result) — flipping `confirmed_exits_enabled`'s default remains an
explicit owner decision, not taken in this pass. A few rows carry an
in-CSV caveat where a specific docket/decision number could not be
independently confirmed (Rockport 1's civil action number; Diablo Canyon's
CPUC decision number) — worth a primary-document confirmation pass before
the flip.

### 4.4 EIA-860 intake extension (RC-2 fix, same commit)

`scripts/process_eia860.py`: add `"Planned Retirement Month"` to
`_GENERATOR_COLUMN_MAP` and `planned_retirement_month` to `EIA_860_CSV_COLUMNS`
(the loader already consumes it when present — `fleet.py:3127` — and `Generator`
already has `retirement_month`). `status` already flows; **do not** widen the
loader's OP filter in this work item (mothball/return-to-service modeling is a
separate question — flagged as an open item in §7). Regenerate the parquet and
document the new column in the data dictionary.

## 5. Mechanism design

### 5.1 Confirmed-exit injector (forecast mode)

**Consumption seam:** `src/market_sim/data/confirmed_retirements.py` —
`load_confirmed_exits(iso) -> list[ConfirmedExit]` (pydantic:
plant_id, generator_id, exit_year, exit_month, mw), reading
`clean_io.read_clean("confirmed-retirements", iso=…)`, filtering
`superseded == False`, earliest instrument per unit. Returns `[]` when the clean
file is absent (empty no-op, like capacity-deliverability).

**Gate:** new `ScenarioConfig.confirmed_exits_enabled: bool = False` (GATED
default-off per the data-intake skill; flipping the default is an explicit
follow-up decision once the seeded registry is reviewed — see §7). No other knob:
the registry is data, not tuning (rule 24: the flag and the clean path are the
whole surface).

**Application:** new `capacity.apply_confirmed_exits(fleet, year, exits)` running
as **step 0** of `evolve_fleet`, before the announced-date step and the economic
screen, plus a first-year call inside `build_base_fleet` (closing the "2026 exit
can never happen in 2026" hole — §3). Semantics:

* Match `Generator`s by `plant_code` (+ `generator_id` where the fleet is
  unit-grain). For **plant-binned** generators (ERCOT CAMPD bins, synthesized
  tranche plants), a unit-level exit **derates**: `pmax_mw -= exit_mw` (tranche
  fractions/`pmin_mw`/must-run MW scale proportionally), dropping the Generator
  when remaining MW ≤ ε. The residual heat-rate composition shift (the retiring
  unit is usually the worst) is accepted second-order error, noted in the
  docstring.
* Annual convention v1: a unit is out from the first simulation year **≥**
  `exit_year` when `exit_month <= 6`, else from `exit_year + 1` (majority-of-year
  rule, mirroring the additions convention's annual grain). Month-precise exits
  via extending the COD ramp to forecast mode are the natural v2 (the ramp already
  takes an explicit calendar year; it is only mode-gated at `fleet.py:1987-1992`)
  — out of scope for W2-P2.
* Confirmed exits **bypass the reliability floor**: a consent decree does not care
  about the model's reserve margin. The post-exit fleet is what the floor and the
  new-entry screen see, so scarcity created by a confirmed exit correctly feeds
  next year's entry signal (the CX-2 myopia lag applies and is noted, not fixed,
  here).
* The economic screen **still sees** confirmed-exit units in the years before
  their date — a unit bound for 2029 can still exit earlier on sustained losses
  (real-world analogue: bankruptcy precedes the decree date). The confirmed date
  is a *latest-exit ceiling*, the screen a possible accelerant. One phenomenon per
  mechanism (rule 19): exogenous legal exit vs endogenous economic exit are
  different phenomena; they compose as `min(economic_exit, confirmed_date)`.

**Forward story (rule 17 form):** (a) *driver* — the binding public instrument,
external to the model; (b) *window* — exactly the instrument's exit date, any
fuel; (c) *regeneration* — re-run intake per vintage against the same public
postings; counter-instruments flip `superseded` and the exit reverts to the
economic screen. Responds to changed conditions by construction (§2.3).

### 5.2 Confirmation gate for non-fossil announced dates (RC-5)

Non-fossil announced dates stay deterministic **only within the EIA-860 data
horizon**: `retirement_year <= EIA860_OPERABLE_VINTAGE +
NONFOSSIL_ANNOUNCED_HORIZON_YEARS` (new `constants.py` value, **5** — citing the
spec's "after the data horizon (~2030) the model is fully economics-driven" line,
symmetric with the additions pipeline whose U/V/TS statuses only exist near-term).
Beyond the horizon an announced non-fossil date is honored **only if the unit is in
the confirmed registry** (e.g. a statute-dated closure); otherwise it is ignored —
the 2040–2072 hydro-relicense/solar-EOL placeholders stop force-retiring, and
far-dated nuclear announcements fall to the economic screen
(`retirement_years_nuclear`/`fixed_om_nuclear` already exist) plus the registry.
Behaviour change to call out in the changelog: the 3 announced nuclear units
(1,871 MW, 2030–2034) — 2030 stays deterministic (within horizon), 2033/2034
become economic unless confirmed.

**Forward story:** driver — EIA-860 self-reported plan, credible only at the same
near-term grain the additions pipeline trusts; window — announced year within
horizon; regeneration — each EIA-860 vintage moves the horizon forward, so the
gate re-derives with no residual coupling.

### 5.3 RC-3 rename

`apply_known_retirements` → **`apply_announced_retirements`** (no alias — deleted
means deleted, rule 26; update `evolve_fleet`, tests, and every docstring in the
same commit). Step list becomes: "0. confirmed exits (exogenous, any fuel,
instrument-bound) → 1. announced retirements (non-fossil within data horizon
only)". CLAUDE.md capacity-evolution step 1, `capacity.py:1-38` module docstring,
and methodology-spec §5 wording (`model-methodology-spec.md:629,641`) all say
explicitly: *announced fossil dates are a default no-op; the exogenous channel is
the confirmed registry.* Doc sync via `/sync-docs` at the end of W2-P2.

### 5.4 Explicit non-goals

* No mothball (SB) / return-to-service modeling; no widening of the loader's OP
  filter (open question flagged in §7).
* No backcast wiring: historical exits stay with vintage snapshots + within-window
  retirees.
* No fuel-conversion mechanism; conversions are notes, not exits.
* No auto-confirmation from EIA-860 `OS` status.
* No change to `forecast_fossil_retirement_economic` semantics.

## 6. Test plan (W2-P2 ships these)

Trivial cases first (1 gen / 1 zone / 24 h per CLAUDE.md):

1. `tests/test_curate_confirmed_retirements.py` — tmp `CLEAN_DIR`, 2-row fixture
   (one live, one superseded), `validate_clean` passes; spine-mismatch row
   (unknown plant, MW off >5%) fails curation with a clear error.
2. `tests/test_capacity.py::apply_confirmed_exits` — unit-grain drop at exit year;
   plant-bin derate math (pmax/pmin/tranche shares scale, drop at ≤ε); fossil unit
   forced out on confirmed date while an identical announced-only fossil twin
   survives (RC-1's exact scenario); exit_month ≤6 vs >6 year assignment;
   reliability floor cannot rescue a confirmed exit; economic screen can still
   retire a confirmed unit early.
3. Horizon gate — non-fossil at vintage+5 honored, vintage+6 ignored,
   vintage+6-but-confirmed honored.
4. First-year — `build_base_fleet` excludes a unit confirmed for START_YEAR.
5. Rename — no reference to `apply_known_retirements` remains (grep-test in CI or
   plain test asserting the attribute is gone).
6. Default-off — `confirmed_exits_enabled=False` byte-identical fleet evolution to
   today (golden comparison on a small synthetic fleet).

### 4.3.2 Reversal supersession honored by the announced channel (2026-07-05, W2-P3 Stage 2)

The PJM capacity hindcast (docs/hindcast-reports/pjm-2021-2025-realized-2026-07-05.md)
exposed the missing half of the §2.2 counter-instrument design: `superseded`
rows kept the *confirmed* channel from firing, but the *announced* channel
still executed the stale EIA-860 planned date — the 2020 vintage carries
Byron/Dresden's 2021 dates (Exelon's reversed 2020 deactivations), so the
hindcast false-retired 4.1 GW of running nuclear, 100 % of its modelled
retirement GW. Landed: `apply_announced_retirements` now ignores announced
dates for plants whose registry rows are **all** superseded (reversed
outright; a plant with any live row — Diablo Canyon's SB 846 schedule — is
excluded, since its exit was *replaced*, not reversed), via
`data.confirmed_retirements.load_announced_reversal_plants`, loaded in every
forecast run **independently of `confirmed_exits_enabled`** (honoring a
documented reversal is a data correction on the announced channel, not an
exit injection; the injector gate is unchanged and stays default-off).
Byron 1–2 / Dresden 2–3 reversal rows seeded (Exelon deactivations announced
2020-08-27, reversed by IL CEJA P.A. 102-0662 signed 2021-09-15, CMC award);
the curation window check (`exit_year >= RETIREMENT_WINDOW_START`) now
applies to live rows only — a reversal row's original date is historical by
construction. Known limitation: the schema carries no superseding-instrument
date column, so the suppression is not date-gated within a hindcast window;
every seeded reversal predates the earliest evolution step that could consume
it (CEJA 2021-09 vs the 2022 bridge). Adding
`superseding_instrument_date` is the schema-v2 follow-up if a
mid-window reversal ever lands.

## 7. Open items / follow-ups (not W2-P2)

* **Flip `confirmed_exits_enabled` default to on** — DONE 2026-07-05. As of the
  2026-07-05 second intake pass (§4.3.1), all six ISOs had been researched
  and either seeded (PJM, ERCOT, MISO, NEISO, CAISO) or returned an honest,
  researched zero (NYISO), unblocking the flip on data-completeness grounds.
  A primary-document confirmation pass the same day resolved the two
  remaining in-CSV caveats (Rockport 1's S.D. Ohio civil action number —
  confirmed as Consolidated Cases C2-99-1182/C2-99-1250 against the filed
  Fifth Joint Modification, Case 2:99-cv-01250-EAS-KAJ Doc #438; Diablo
  Canyon's CPUC decision number — confirmed as D.23-12-036 against a CPUC
  decision in R.23-01-007 that quotes it verbatim). With both caveats
  cleared, the owner sign-off was given and `ScenarioConfig.confirmed_exits_enabled`
  now defaults to `True` (`src/market_sim/config/scenarios.py`). This also
  activates the non-fossil announced-horizon gate (§5.2), coupled to the same
  flag in `capacity.evolve_fleet`. Backcast mode is unaffected (the channel is
  forecast-mode only, verified byte-identical).
* Month-precise forecast exits by un-gating the COD ramp for forecast years (also
  fixes the comment/code drift at `fleet.py:1983-1992`, whose comment already
  claims forecast support the gate denies).
* Mothball/SB representation (1,501 units invisible today) — separate design.
* MISO Attachment Y confidentiality lag — some approved retirements publish late;
  the registry's `accessed` stamp makes the staleness measurable.
* CX-1 (FOM bars below ATB) is the root cause of PJM's profitability-inertness and
  is owned by W0-P5/W2-P3 — the confirmed channel must not be used to paper over it
  (rule 19: enumerate what already floors the phenomenon).
* **CX-3 escalation (from §3):** the ERCOT reliability floor is in permanent
  ~20 GW deficit (thermal-only vs 1.15×peak), making economic retirement fully
  inert there — the floor needs ELCC/UCAP accreditation of non-thermal firm
  capacity. Owned by W2-P3's reliability-floor item; the probe evidence here is
  its motivating exhibit.
* `bins_to_fleet` dropping announced dates (§3 new finding) also means the
  non-fossil honor path silently skips any binned non-fossil plant; today none
  are binned (bins are gas/coal), so this is latent, but the invariant "announced
  dates ride plant-level joins, not bin plumbing" should be asserted in a test.

## 8. W2-P2 implementation prompt

```
W2-P2 [OPUS] — Implement the confirmed-retirement channel

Prerequisite: read docs/handoffs/confirmed-retirement-plan-2026-07.md (THE PLAN),
then CLAUDE.md rules 13/14/17/19/24/26 and docs/fable-repo-audit-2026-07.md §B.
Implement exactly per the plan; where this prompt and the plan disagree, the plan
wins. Design decisions are settled — do not relitigate them.

1. Data intake (plan §4, data-intake skill end to end):
   a. data/dictionary/schema/confirmed-retirements.schema.yaml — copy the plan
      §4.1 schema verbatim (closed confirmation_class vocabulary: rto_deactivation
      | consent_decree | statute | regulatory_order | rmr_end).
   b. data/raw/confirmed-retirements/README.md with the plan §2.2 source table and
      per-ISO DATA NEEDED lines; per-ISO hand-curated <iso>.csv extracts seeded
      from plan §4.3 — every row carries instrument, instrument_date, source_url,
      accessed; instruments MUST be re-verified against current postings before
      committing (the plan's candidates predate this session's knowledge cutoff;
      Eddystone 3-4 and Brandon Shores/Wagner enter only as superseded/rmr_end
      rows per §4.3). Seed at minimum ERCOT + PJM; other ISOs may land as
      DATA NEEDED with empty CSVs.
   c. scripts/lib/confirmed_retirements/ registry package (IsoSpec + register +
      generic parser, one module per ISO — copy the capacity_deliverability
      pattern; no if-iso ladders) and scripts/curate_confirmed_retirements.py
      (EIA-860 spine validation: plant/generator exists, MW within 5%; writes via
      clean_io.write_clean/validate_clean; curate() + argparse main). Register in
      regenerate_clean.py DATATYPES.
   d. Extend scripts/process_eia860.py per plan §4.4: carry Planned Retirement
      Month into eia860_generators.parquet (_GENERATOR_COLUMN_MAP +
      EIA_860_CSV_COLUMNS); regenerate the parquet; do NOT touch the loader's OP
      status filter.
2. Consumption seam (plan §5.1): src/market_sim/data/confirmed_retirements.py with
   load_confirmed_exits(iso) -> list[ConfirmedExit] (pydantic; filters superseded,
   earliest instrument per unit; [] when clean data absent). New ScenarioConfig
   field confirmed_exits_enabled: bool = False (GATED) — the only new knob.
3. Mechanism (plan §5.1): capacity.apply_confirmed_exits(fleet, year, exits) as
   step 0 of evolve_fleet + first-year application in build_base_fleet. Unit-grain
   drop; plant-bin derate (pmax/pmin/tranche shares proportional, drop at <= ε);
   exit_month <= 6 -> exit_year else exit_year+1; bypasses the reliability floor;
   economic screen still sees the unit before its date (min(economic, confirmed)
   composition per plan §5.1).
4. Confirmation gate (plan §5.2): constants.NONFOSSIL_ANNOUNCED_HORIZON_YEARS = 5
   with the spec-cited comment; announced non-fossil dates beyond
   EIA860_OPERABLE_VINTAGE + horizon are ignored unless the unit is in the
   confirmed registry. Call out the nuclear behaviour change in CHANGELOG.
5. Rename (plan §5.3): apply_known_retirements -> apply_announced_retirements, no
   alias; update evolve_fleet, tests, module docstring, CLAUDE.md capacity-
   evolution step line, model-methodology-spec.md §5 wording — same commit.
6. Tests: the full plan §6 list, trivial cases first. Run the capacity/fleet/
   curation test files green.
7. Verification probe (not a keeper, nothing on the dashboard): re-run the plan
   §3 scratch harness (forecast ERCOT + PJM, END_YEAR 2029, injector ON with the
   seeded registry) and record in the PR/commit message: which confirmed units now
   exit on schedule (expect plant-bin derates at Rockport-class plants), and
   confirm announced-only twins still ride the economic screen. Baseline
   expectation from the plan §3: zero economic retirements in both ISOs — the
   injector is the only working exit channel until CX-1/CX-3 land (W2-P3). Do not
   tune anything to move these results (rule 1).
8. /sync-docs, CHANGELOG entry, commit and push. Use mcp github push_files for
   any large payloads per CLAUDE.md's 413 guidance.
```
