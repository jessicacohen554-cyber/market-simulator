# FFR-4E — CAISO's published storage accreditation, reconciled; and FC-2 row 4 re-read

**Lane.** FFR-4D's routed top successor (§7 D-1 + D-4), chartered against the
ACCREDITATION-RATE cause. Branch `claude/ffr-4e-caiso-storage-elcc-1gznik`, based on
`origin/main` **`2ce94eb`** (rebased fresh at session start; re-verified below).

**The capacity-price ANCHOR route is REFUSED, as chartered.** No CAISO capacity-price
anchor, net-CONE, CPM soft-offer cap or entry-screen price term is read, changed, or
quoted anywhere in this work, and **no row-4 improvement via that route is claimed**.
§8 states this formally.

---

## PRE-REGISTRATION (written and committed BEFORE the treated arm was solved)

Committed in `ffr-4e: pre-register` so the decision rules below cannot be read as
post-hoc. Results sections are appended after.

### P-1. The construction, chosen before measurement

CAISO's published battery accreditation enters as a **whole-class ratio on a NAMEPLATE
basis**, NOT as a by-duration table:

```
STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO["CAISO"] = 13,365 / 15,448.4 = 0.865138
```

gated behind a new **default-OFF** `ScenarioConfig.caiso_storage_nqc_accreditation`.
Rationale pre-registered in §3; the three reasons, stated before the row-4 read:

1. **CAISO publishes no storage duration table.** The CY2026 NQC report's `2026 Tech
   Factors` tab has **no battery row** — batteries are *dispatchable* and are accredited
   at demonstrated capability, not by a technology factor. Minting a CAISO
   `STORAGE_ELCC_BY_DURATION_BY_ISO` entry would be inventing an object CAISO does not
   publish.
2. **The published ratio is NQC/NDC; the model's multiplicand is nameplate.** Dropping
   0.9458 onto `power_cap_mw` is the substitution FFR-4D §6.1 warned against, and it is
   quantified in §3.3.
3. The registry gains a whole-class path that is **one mechanism, not a stack** (rule 19):
   where a whole-class ratio exists it **replaces** `_elcc_for_duration`, never multiplies
   it.

### P-2. Keeper guard — the gate is default-OFF, and that is the pre-registered posture

The CAISO **backcast** keeper `2026-08-09-caiso-184-c1-lpbasis` **does** consume the
storage accreditation entries (§4 enumerates the four consumers; `run_config.json` shows
`capacity_deliverability_limits: true`, `storage_capacity_value: true`,
`renewable_elcc_curves: true`). Byte-inertness is therefore **not** available by
inspection, and the keeper's evolution ledger is not committed (bundles are slim), so it
cannot be re-read without a re-solve. The charter's second branch is taken: **gate the
intake default-off**, which makes byte-inertness hold *by construction* rather than by
measurement. Pre-registered check **G-INERT**: with the gate absent, the CAISO
accreditation chain is numerically identical to HEAD, and the pinned default cache key is
unmoved.

### P-3. FC-2 row 4 arms

Both arms at this head, cold, `scripts/run_full_horizon.py --iso CAISO --start-year 2026
--end-year 2030` (5 years, sequential — rule 12), separate `--out-dir`s:

| arm | config |
|---|---|
| **control** | HEAD default (gate off) |
| **treated** | `caiso_storage_nqc_accreditation` ON, nothing else changed |

**The control is a NEW control, not FFR-4D's.** FFR-4D's D-8 control (14,043.6 / 21,448.0
/ 65.48 %) was measured *before* its own fleet fix; that fix is merged at this head, so
the expected control here is FFR-4D's **treated** arm (≈ 8,186.3 MW / 52.51 %). Predicted
before solving; §5 reports what actually came back.

### P-4. Decision rule, pre-registered

Row 4 scores `cumulative reserve_backstop thermal additions ÷ total additions`
(`scripts/forecast_verdict.py`): **PASS ≤ 10 %, CAVEAT 10–30 %, FAIL > 30 %**.

* If the treated arm clears to PASS or CAVEAT — report it as the accreditation cause
  closing, with the fleet fix (FFR-4D) as the other half.
* **If row 4 still FAILs with the fleet AND the accreditation right — THAT IS THE
  FINDING** (rule 11). It is written as such; **no further lever is pulled in this
  session**, and in particular the capacity-price anchor is not touched. The residual then
  points at the anchor object, which is **NOT this lane's** — it may be chartered later,
  by someone else, on its own rule-14 merits.

### P-5. D-4 (dilution) decision rule

Intake a published CAISO/CPUC **portfolio** dilution source if one exists at citation
quality; otherwise **HOLD the hard 1.0** and document the assumption in the registry
comment. Pre-registered: the committed E3/Astrapé incremental study is examined for this
purpose, and it qualifies only if it is a *portfolio/fleet-average* object on a
*compatible penetration axis*. §6 records the adjudication.

---

## 1. State verified at this head

| item | verified |
|---|---|
| `origin/main` | **`2ce94eb`** |
| CAISO keeper | **`2026-08-09-caiso-184-c1-lpbasis`** — re-read from `frontend/data/backcast/keepers/CAISO.json` at this head, as the packet instructed |
| `complete` markers | CAISO **absent** (withdrawn by the owner 2026-08-06 at caiso-178) |
| `final` markers | EMPTY — CAISO's locked test never granted, never spent |
| years touched | **2023–2025 in-sample (none solved) and 2026–2030 forecast ONLY.** No out-of-training year was solved, scored, read or approached. |

Prerequisites ran in the briefed order: `uv sync` first, then
`scripts/regenerate_clean.py`.

---

## 2. The intake — first-party, and it CLOSES D-7

FFR-4D §7 D-7 flagged that Table 1.1's cells were carried from FFR-3P's
transcription with the source PDF uncommitted. That is now closed for **every
class, not just battery**.

Committed under `data/raw/capacity-market/loads-resources/caiso/` on the sibling
`nqc/caiso/` intake's contract (immutable source + reviewable derived CSV +
README; raw-only, no `data/clean/` schema, because these enter as cited registry
constants rather than a solve-time series):

| file | |
|---|---|
| `2026-summer-loads-and-resources-assessment-technical-appendix.pdf` | CAISO, May 2026. sha256 `609e77b53dcbb65901dc93c6adbe0be16ebe57f7bebf916476e1b909a5654be3` |
| `caiso_slra_class_accreditation.csv` | Table 1.1 digitized by `scripts/data/derive_caiso_slra_class_accreditation.py` |

**FFR-3P's transcription is CONFIRMED, not merely re-quoted.** The battery row
reads NDC **14,131** / NQC **13,365** first-party, and 13,365/14,131 = 0.945793.

Two closure checks the deriver runs on every re-derivation:

* the NQC column's fuel rows foot **exactly** to the published Total, 59,069 MW
  — which is the parse's own proof, and independently re-confirms the 59,069
  figure FFR-3P's §1.1 ledger is built on;
* the NDC column's rows sum to 83,923 against a published 83,922 — a **1 MW
  per-row rounding artifact in CAISO's own table**, tolerated at ±2 MW and
  logged, never silently absorbed.

Provenance the table's own footnotes carry, and which the registry comment now
records: **September** NQC values; **NDC as of April 1, 2026** from the CAISO
Master File; source is the **March 2026** NQC list; the table **excludes**
tie-generators, pseudo-tie/dynamic imports outside the BAA (~9,200 MW), SRR gas
units, participating loads and demand response.

---

## 3. The reconciliation — three misalignments, not one

FFR-4D §6.1 routed this with one warning (the synthetic duration mix). Measuring
it surfaced **three** distinct misalignments, and the largest is not the one that
was flagged.

### 3.1 CAISO publishes NO storage duration table — so no by-duration row is minted

The CY2026 NQC report's `2026 Tech Factors` tab carries factors for Solar Fixed /
Tracking / Thermal, Wind (Norcal/Socal/AZ/NM/WA-OR), non-dispatchable Hydro,
Geothermal, Cogeneration and Biomass — and **no battery row at all**. Batteries
are *dispatchable* and are accredited at demonstrated capability. The assessment
says so in terms (§1.1.1):

> *"For dispatchable resources like battery and natural gas plants, the NQC value
> is typically near its NDC or installed capacity."*

So a CAISO entry in `STORAGE_ELCC_BY_DURATION_BY_ISO` would be an **invented
object**. The publishable object is a whole-class ratio, and the registry gains a
whole-class rung (`STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO`) that **replaces**
the by-duration lookup rather than overriding a row inside it — the charter's
option (b), taken because the registry structure genuinely supports it more
honestly than a by-duration fudge.

### 3.2 The duration-mix question, MEASURED — and it resolves against the mix route

The charter asked for the real CAISO duration mix from the measured EIA-860
fleet. Derived (BA `CISO`, `Status = "OP"`, MW-weighted on nameplate; 273 units,
15,448.4 MW, zero units missing energy capacity):

| duration band | MW | share |
|---|--:|--:|
| < 1.5 h | 2,335.5 | 15.1 % |
| ~2 h | 963.9 | 6.2 % |
| ~3 h | 308.5 | 2.0 % |
| **~4 h** | **11,267.1** | **72.9 %** |
| ~5 h | 381.4 | 2.5 % |
| ~6 h | 146.1 | 0.9 % |
| 7–8 h | 45.9 | 0.3 % |
| **fleet energy-weighted mean** | | **3.428 h** |

Now the measurement that settles the route:

```
generic NREL/E3 table on the REAL measured mix   = 0.5589
generic NREL/E3 table on the SYNTHETIC 70/25/5   = 0.6875   (what the model does today)
CAISO's own realized whole-class accreditation   = 0.8651   (nameplate basis, §3.3)
```

**Using the real mix makes the by-duration path WORSE, not better.** The real
CAISO fleet is *shorter*-duration than the synthetic mix (which carries 25 % at
8 h and 5 % iron-air at 100 h), so re-weighting the generic curve onto it moves
the credit *away* from CAISO's realized value, by a further 12.9 pp. The gap to
0.8651 is therefore **not a duration-mix artifact at all** — it is CAISO's
accreditation *methodology*, which derates a dispatchable resource by
demonstrated capability and not by duration in any degree. A 1-hour CAISO battery
earns near-full NQC; the NREL/E3 curve gives it 0.40.

That is the substantive answer to §6.1's warning: the mix is the *evidence that
the by-duration object is the wrong shape*, not a weighting to apply.

### 3.3 The basis correction — the largest term, and the one FFR-4D's number missed

The published ratio is NQC/**NDC**. The model multiplies a storage unit's
**EIA-860 nameplate** `power_cap_mw`. CAISO's NDC is materially below nameplate:

```
NDC / nameplate = 14,131   / 15,448.4 = 0.914723
NQC / NDC       = 13,365   / 14,131   = 0.945793   <- the published ratio
NQC / nameplate = 13,365   / 15,448.4 = 0.865138   <- THE REGISTRY VALUE
```

Both terms of the adopted ratio are measured, and they describe **one fleet**:
the denominator is the same EIA-860 2025 Early Release object
`STORAGE_BASE_FLEET_MW["CAISO"]` was re-vintaged from at FFR-4D (15,448.4 →
15,450).

**Consequence for the routed number.** FFR-4D D-1 quoted **+3,990.6 MW** by
applying 0.9458 to a nameplate quantity. On the corrected basis the forecast
effect is **+2,744.5 MW** — the routed figure was **overstated by 1,246.1 MW**.
This is precisely the substitution §6.1 refused to perform blind, now quantified.

### 3.4 Deliverability — kept, and why

The published whole-class ratio embeds a deliverability haircut:

| tranche | NDC | NQC | ratio |
|---|--:|--:|--:|
| Full Capacity Deliverable | 8,864 | 8,764 | 0.98872 |
| Interim Deliverability | 4,131 | 3,977 | 0.96272 |
| Partial Deliverability | 1,059 | 624 | 0.58924 |
| Energy Only | 78 | 0 | 0.00000 |
| **Total** | **14,131** | **13,365** | **0.94579** |

The haircut is **kept**, on two grounds. First, the model has **no per-resource
deliverability status for storage** — `capacity_deliverability_limits` prices a
zonal/seam quantity, not a queue outcome — so excluding it would credit MW
CAISO's own ledger does not count, and there is no second mechanism removing
them. Second, and decisively, **the deliverability-clean alternative is not
constructible on this basis**: its numerator is published per tranche but its
nameplate denominator is not, and no CAISO-resource-ID → EIA-860 crosswalk
exists in this repo. The whole-class ratio is the only construction *both* of
whose terms are measured.

Stated as the residual assumption: forward builds inherit the 2026 fleet's
deliverability mix. That runs slightly **against** accredited capacity (it is a
haircut), so it is the conservative direction.

### 3.5 The class boundary — pumped storage excluded

The ratio is Table 1.1's **Battery** row. CAISO books pumped storage on its
**Hydro** row — FFR-4D §2 proved that two independent ways and this session takes
it as settled — so `storage_accreditation_credit` excludes `pumped_storage` from
rung 1 by `tech_name` and leaves it on the by-duration table, where its long
duration is already credited correctly. Measured: PS firm capacity is **1,932.2
MW armed and unarmed alike**, in every year.

---

## 4. The keeper guard — a live consumer chain, so the gate ships default-OFF

### 4.1 What consumes the CAISO accreditation entries (enumerated BEFORE landing)

`storage_firm_mw` is computed in `runner.py` for **every solve year in both
modes**, flows into `prior_results`, and from there into **four** consumers —
all of them reachable on a CAISO *backcast*, because `evolve_fleet` runs for
every year after the first regardless of mode:

| # | consumer | armed on the keeper? |
|---|---|---|
| 1 | `accredited_firm_capacity_mw` → the evolution ledger's `firm_mw` | always |
| 2 | economic-retirement **reliability floor** (`evolve.py` step 3) | always |
| 3 | **reserve-margin backstop** (`resolve_reserve_margin_build_enabled`; capacity-market ISOs default-on) | resolves per market design |
| 4 | **locational-deliverability headroom** (`deliverability_headroom_by_zone`) | **YES** — `capacity_deliverability_limits: true` |

The keeper's own `run_config.json` (`2026-08-09-caiso-184-c1-lpbasis`) shows
`capacity_deliverability_limits: true`, `storage_capacity_value: true`,
`renewable_elcc_curves: true`, `storage_measured_base_fleet: true`. So
byte-inertness was **not** available by inspection, and the keeper's evolution
ledger is not committed (bundles are slim; `<out-dir>/<ISO>/<runtime-key>/` died
with FFR-4D's container), so it could not be re-read without a re-solve.

### 4.2 The charter's second branch, taken — and it is load-bearing

The gate ships **default-OFF**, which makes the keeper inert **by construction**.
This is not precautionary: had the entry landed unconditionally it **would** have
moved the keeper. Measured on the keeper's own recipe and its own measured fleet:

| year | fleet MW | `storage_firm_mw` HEAD | gate-off | **Δ** | gate-ON (what was avoided) |
|---|--:|--:|--:|--:|--:|
| 2023 | 9,570.0 | 5,963.6680 | 5,963.6680 | **0.0e+00** | 8,414.1 (+2,450.5) |
| 2024 | 13,208.9 | 8,003.6980 | 8,003.6980 | **0.0e+00** | 11,562.3 (+3,558.6) |
| 2025 | 17,526.0 | 10,318.1680 | 10,318.1680 | **0.0e+00** | 15,297.2 (+4,979.0) |

**G-INERT PASSES**: gate-off is exactly equal to the pre-FFR-4E value in all
three keeper years — not "within tolerance", equal. Pinned by
`tests/unit/model/test_storage_whole_class_accreditation.py::KeeperInertnessTest`
so it cannot regress silently.

**Cache.** Registered in `_CACHE_KEY_OPTIONAL_FIELDS` at `False`. The pinned
default key **`603c2498bf71d21d` is UNMOVED** (measured), and the armed config
keys distinctly. Unlike its FFR-4D sibling this is byte-identical at its default,
so it is **not** a same-key invalidation and carries **no cache epoch** — no
cached bundle in any ISO is orphaned.

### 4.3 Solve-free projection, recorded BEFORE the arms were solved

On FFR-4D §4.3's post-fleet-fix ledger at this head:

```
battery firm     10,621.9 -> 13,366.4   (+2,744.5)
pumped storage    1,932.2 ->  1,932.2   (unchanged -- Hydro row)
accredited firm  56,269.6 -> 59,014.1
requirement      57,306.0
reserve position   0.9819 ->   1.0298   (1.8 % SHORT -> 3.0 % LONG)
base-year gap    +1,036.4 MW -> -1,708.1 MW
```

So the arithmetic predicts the base-year adequacy deficit **closes**. Whether
that collapses row 4's numerator is what the solve answers.

---

## 5. FC-2 row 4, re-read at this head — **STILL FAIL. That is the finding.**

Both arms solved cold at this head, 2026–2030, five years sequential in each
invocation, separate `--out-dir`s, concurrent invocations (rule 12).

```
control  scripts/run_full_horizon.py --iso CAISO --start-year 2026 --end-year 2030 \
           --out-dir results/ffr4e/caiso-control
treated  ... --caiso-storage-nqc-accreditation --out-dir results/ffr4e/caiso-treated
```

Runtime cache keys **`3d3e836a176ac9cd`** (control) / **`bf9b4d739a6b3ab8`**
(treated) — distinct in the real run, so the two arms could not have shared a
bundle. `caiso_storage_nqc_accreditation` is recorded `False` / `True` in each
arm's own `run_config.json` (rule 24).

### 5.1 The control re-establishes, and P-3's prediction is confirmed

| | backstop MW | total additions MW | **row 4** |
|---|--:|--:|--:|
| **control** | **8,186.3** | 15,590.7 | **52.51 % FAIL** |
| **treated** | **5,292.3** | 12,696.7 | **41.68 % FAIL** |

The control reproduces FFR-4D's **treated** arm to the megawatt and to the digit
(8,186.3 / 52.51 %), exactly as P-3 predicted it would — confirming that FFR-4D's
fleet fix is merged and live at this head, and that this session's control is the
right same-head baseline. Scored by `scripts/forecast_verdict.py --tier t1f`, not
by hand: *"row4: backstop share 52.5 % > 30 % (administrative over-build)"* →
*"row4: backstop share 41.7 % > 30 %"*.

### 5.2 The accreditation chain reproduces the solve-free projection exactly

| | control | treated | Δ |
|---|--:|--:|--:|
| `storage_firm_mw` 2026 (battery + PS) | 12,554.043 | 15,298.552 | **+2,744.509** |
| accredited firm 2026 | 56,270 | **59,014** | +2,744 |
| requirement 2026 | 57,306 | 57,306 | — |
| reserve margin 2026 | 12.92 % | **18.43 %** | +5.5 pp |

§4.3's projection (+2,744.5 MW; 56,269.6 → 59,014.1) is reproduced **to the
megawatt** by the solve, and pumped storage is unmoved in both arms.

### 5.3 What DID clear — real structural gains, reported at full magnitude

| invariant | control | treated |
|---|---|---|
| **I7** (accredited firm ≥ requirement) | **FAIL** — 2026 (56,270 < 57,306), 2027 (54,969 < 58,671), 2028 (57,621 < 60,082) | **FAIL — 2027 only** (57,713 < 58,671, short 958 MW) |
| **I12** (reserve-margin band) | **FAIL** — 2026 12.9 %, 2027 7.7 %, 2028 10.3 % | **WARN** — 2027 13.1 % only |
| I3 (unserved/dump) | PASS | PASS |
| I13 (cobweb) | PASS | PASS |

**The base-year adequacy deficit CLOSES.** Two of three short years disappear and
I12 is downgraded FAIL → WARN. The base-year gap that FFR-4D left at 1,036.4 MW
short is gone.

### 5.4 Why row 4 nonetheless stays FAIL — and it is not the accreditation

The numerator falls **35.4 %** (8,186.3 → 5,292.3 MW) but the share falls only
**10.8 pp**, because *the backstop builds are most of the denominator too*: when
the administrative channel builds less, total additions fall with it.

The decisive observation is what did **not** move:

| channel | control | treated |
|---|--:|--:|
| renewable builds | 5,404.4 MW (4,702.2 in 2029 + 702.2 in 2030) | **5,404.4 MW — identical** |
| **economic** thermal entry | 2,000.0 MW (2029, one block) | **2,000.0 MW — identical** |
| reserve-backstop thermal | 8,186.3 MW | 5,292.3 MW |
| storage builds | 0.0 | 0.0 |

**Every megawatt of the move is backstop; the economic entry screen is completely
unresponsive to a 2.7 GW improvement in the accredited ledger.** Across a
five-year horizon in which the requirement grows ~1.3 GW/yr, economic entry
supplies exactly one 2,000 MW block, in both arms, and storage entry supplies
nothing at all. Adequacy is therefore met administratively no matter how correct
the accreditation ledger becomes — which is precisely the behaviour row 4 exists
to surface.

**So the pre-registered FINDING branch (P-4) fires.** With the fleet right
(FFR-4D) *and* the accreditation right (this session), row 4 is still FAIL. The
two fleet/accreditation causes together took it 65.48 % → 52.51 % → 41.68 %, a
23.8 pp improvement that is real, structurally grounded and still **11.7 pp above
the CAVEAT line and 31.7 pp above PASS**. The residual is not an accreditation
quantity. It is an **entry-economics** object: the screen that decides whether a
merchant unit builds prices new capacity through the capacity-price seam.

**That object is NOT this lane's, and nothing in it was read, changed or quoted.**
No further lever was pulled after this result, per P-4. It may be chartered later,
by someone else, on its own rule-14 merits — and if it is, it must be justified as
a correct market representation, never as the thing that turns row 4 green.

### 5.5 Nothing was tuned to the result

The registry value was fixed in §3 **before** either arm was solved, from two
published/measured megawatt quantities, and was not revisited after the row-4
read. The construction that makes row 4 look *worse* than FFR-4D's routed
estimate — the nameplate basis, which cuts the credit from 0.9458 to 0.8651 and
the effect from +3,990.6 to +2,744.5 MW — is the one adopted (rule 14: the
accurate value is kept even when it is adverse to the residual; rule 1: the
mechanism is judged on faithfulness, not on the fit).

---

## 6. D-4 — CAISO storage ELCC portfolio dilution: **HOLD 1.0, assumption stated**

Per P-5. No published CAISO/CPUC portfolio-dilution object exists at citation
quality:

* the committed **E3/Astrapé Incremental ELCC Study** publishes **marginal**
  tranche ELCCs, not a fleet-average; its 4-hour series is **non-monotone** in
  penetration (96.3 → 90.7 → 75.1 @1,759 MW → 76.6 @4,123 → 74.0 @6,553 → 76.5);
  and its axis is **cumulative MW *added* since a baseline**, a different
  quantity from the `existing_storage_mw` the dilution is indexed on. Fitting a
  portfolio line through that would be inventing a curve (rules 5 and 14). The
  intake's own README already records why the marginal study cannot serve as a
  whole-fleet ledger credit; this is the same finding for the same reason;
* CAISO's SLRA Table 1.1 publishes **one realized point**, not a curve.

So CAISO stays absent from both dilution registries and the factor stays **1.0**,
which is **exactly right at the reference fleet** — 0.8651 *is* CAISO's realized,
already-diluted fleet-average at 15,448 MW installed, so any further dilution
there would double-derate it.

**The stated caveat, written into the registry comment rather than left implicit:**
above ~15.4 GW a forecast credits new CAISO storage at the accreditation its 2026
fleet realized, with no penetration compression. That assumption runs **in favour
of** accredited capacity — i.e. it makes adequacy look better, and it makes row 4
look better — so it is disclosed here as an assumption that flatters the treated
arm, not one that excuses it. A published CAISO/CPUC portfolio-ELCC-vs-penetration
series would close it.

---

## 7. Open items, routed not fixed

| id | item | why not here |
|---|---|---|
| **E-1** | **FC-2 row 4's residual is an ENTRY-ECONOMICS object** — economic thermal entry is a single invariant 2,000 MW block and storage entry is 0.0 MW across the whole horizon, in BOTH arms. Adequacy is met administratively regardless of the accreditation ledger. | §5.4. The capacity-price anchor route is **owner-declined in D-15's charter** and was refused here. Any successor must justify it on its own rule-14 merits, never as the thing that turns row 4 green. |
| **E-2** | **`caiso_storage_nqc_accreditation` arming posture is an OWNER decision.** The mechanism is built, measured, and default-OFF; it is CAISO's own published accreditation and rule 14 favours it over the generic curve, but arming it MOVES THE DESIGNATED BACKCAST KEEPER (§4.2: +2,450.5 / +3,558.6 / +4,979.0 MW). | Arming would require a CAISO keeper re-solve + re-gate under rules 15/16 — its own session in the CAISO lane, exactly like its VRE sibling `caiso_nqc_accreditation` (owner decision D.1). |
| **E-3** | **The forecast lane's synthetic 70/25/5 duration mix is measurably wrong for CAISO** (real mix: mean 3.43 h, 72.9 % at ~4 h, 21.3 % under 2.5 h). This session did NOT fix it, because on the whole-class rung it is inert for CAISO accreditation. | It still drives `STORAGE_TECHS` economics elsewhere (degradation, entry). A separate, CAISO-scoped question; touching it here would have been an unchartered second mechanism. |
| **E-4** | **ERCOT's storage row (FFR-4D D-3) is untouched.** | Rule 25 `[R-ISO-SCOPE]` — ERCOT's lane. |
| **E-5** | **The whole-class rung is CAISO-only.** Other ISOs that accredit dispatchable storage at demonstrated capability may have the same shape defect, unmeasured. | Each needs its own lane and its own published source; a verdict never transfers (rule 28(d)). |

**CLOSED by this session:** FFR-4D **D-1** (the rate is intaken and reconciled),
**D-4** (adjudicated, held at 1.0 with the assumption stated), and **D-7**
(Table 1.1 is digitized first-party for every class, no longer FFR-3P's
transcription).

---

## 8. Governance

* **THE ANCHOR REFUSAL — honoured, formally.** No CAISO capacity-price anchor,
  net-CONE, CPM soft-offer cap or entry-screen price term was read, changed, or
  quoted. `data/raw/capacity-market/demand-curve/caiso/` was not opened. **No
  row-4 improvement via that route is claimed anywhere**, and §5.4 reports row 4
  *not clearing* rather than reaching for the route that might clear it. §7 E-1
  restates that the object belongs to a future, separately-chartered lane.
* **Rule 1 `[R-STRUCT]` / rule 11.** Nothing is tuned to a residual. The registry
  value was fixed before either arm solved. The basis correction is **adverse**
  to the treated arm (it cuts the effect from +3,990.6 to +2,744.5 MW) and is
  adopted anyway; the still-FAIL result is written as the finding rather than
  chased.
* **Rule 5 `[R-NO-MAGIC]`.** Every value is a published MW or a ratio of two of
  them, cited to a committed source. The one place a number could have been
  invented — the dilution curve — is where the session declined to invent it.
* **Rule 13 `[R-MEASURED]`.** Both terms of the ratio regenerate for a forward
  year from annual publications and respond to changed conditions. It is an
  accreditation *rule*, not a measured outcome; nothing is pinned to actuals.
* **Rule 14 `[R-ACCURATE]`.** The published accreditation replaces a generic
  estimate. The three misalignments (§3) are **reconciled and documented**, not
  buried: the duration-mix question is answered with a measurement that resolves
  *against* the by-duration route, the NDC↔nameplate basis is corrected rather
  than substituted, and the deliverability and hybrid boundaries are stated.
* **Rule 19 `[R-ONE-MECH]`.** Rung 1 **replaces** rung 2; it never multiplies it
  (pinned by test). One resolver, `storage_accreditation_credit`, so an ISO's
  basis cannot be applied on one consumer and not another.
* **Rule 20 `[R-DOF]`.** **Zero new free parameters.** The registry value is a
  ratio of two published/measured quantities with no fitted term; no DOF ledger
  entry is added, and no keeper's ledger changes (no keeper moved).
* **Rule 22 `[R-HOLDOUT]`.** Forecast-mode **2026–2030 only**, plus in-sample
  2023–2025 read solve-free for the keeper guard. **No out-of-training year was
  solved, scored, read or approached.** CAISO holds no `complete` and no `final`
  marker; both are respected and neither was written. Data intake is unrestricted
  under the 2026-08-06 clarification (what is held out is the *score*, never the
  *data*) — and this intake is applied consistently, not year-scoped.
* **Rule 23 `[R-FROZEN-DERIVE]`.** The re-derivation licence is the source-data
  vintage (CAISO's CY2026 publication), never a residual, and the deriver says so.
  A committed test reconciles the registry literal against the digitized artifact
  so it cannot drift silently.
* **Rule 24 `[R-REGISTRY]`.** One `ScenarioConfig` field, one CLI flag, recorded
  in both arms' `run_config.json`. No env var, no per-plant dict, no `getattr`
  fallback literal.
* **Rule 25 `[R-ISO-SCOPE]`.** CAISO only — the registry holds one ISO and the
  gate resolves per ISO; **measured**: arming CAISO leaves ERCOT/PJM/MISO/NYISO/
  NEISO byte-identical. ERCOT's parallel question is routed, not fixed. No
  cross-ISO parameter or verdict was imported.
* **Rule 27 `[R-PUSH]`.** Opus. No file ≥300 lines was rewritten from generated
  content; every change is a local `Edit` of on-disk bytes, pushed via `git push`
  on a freshly-rebased base, and **every pushed file ≥300 lines was blob-verified
  against the remote** (line count + object hash) before the next commit.
* **Rule 28 `[R-MECH-MATRIX]`.** Row `caiso_storage_nqc_accreditation` minted in
  the same commit as its field (duty c) and its verdict updated in this session
  from the solve (duty b).
* **Cache.** Registered in `_CACHE_KEY_OPTIONAL_FIELDS` at `False`; the pinned
  default key **`603c2498bf71d21d` is unmoved (measured)**, the armed config keys
  distinctly, and the two solved arms took distinct runtime keys. Byte-identical
  at its default, so — unlike FFR-4D's sibling field — this is **not** a same-key
  invalidation and carries **no cache epoch**. No cached bundle in any ISO is
  orphaned.
* **Rules 15/16.** No *backcast* calibration run was produced, so there is nothing
  for the backcast dashboard and no keeper changed. The two forecast-lane arms ARE
  registered on the **forecast** dashboard via the single
  `scripts/register_forecast_run.py` path (`--kind adequacy`), ids
  `caiso-2026-2030-2026-08-09-ffr4e-caiso-{control,treated}` — the canonical
  `frontend/data/hindcast/<id>.json` sidecars are committed; the
  `frontend/data/forecast/` namespace is generated and gitignored, rebuilt by the
  Pages deploy. *(This is a deliberate step beyond FFR-4D, whose identical two-arm
  A/B was left unregistered.)* The dispatch parquets are **not** committed — the
  slim artifacts (summaries, `run_config.json`, evolution ledgers, floor-retention
  logs) are, per the pack-size rule.

---

## 9. Reproduction

```bash
uv sync                                    # ~2 min
uv run python scripts/regenerate_clean.py  # ~50 min

# the intake, first-party from the committed PDF
uv run --with pypdf python scripts/data/derive_caiso_slra_class_accreditation.py --report

# the reconciliation + the keeper guard, no solve
uv run python -m pytest \
  tests/unit/data/test_caiso_slra_class_accreditation.py \
  tests/unit/model/test_storage_whole_class_accreditation.py -q

# the real CAISO duration mix (§3.2)
uv run python -c "
import pandas as pd
from market_sim.model.storage import _elcc_for_duration
plant = pd.read_parquet('data/raw/eia-860/eia860_plant.parquet')
ba = plant.set_index('Plant Code')['Balancing Authority Code']
op = pd.read_parquet('data/raw/eia-860/eia860_energy_storage_operable.parquet')
c = op[(op['Plant Code'].map(ba)=='CISO') & (op['Status']=='OP')].copy()
c['pw'] = pd.to_numeric(c['Nameplate Capacity (MW)'], errors='coerce')
c['en'] = pd.to_numeric(c['Nameplate Energy Capacity (MWh)'], errors='coerce')
c = c[c['pw']>0]; tot = c['pw'].sum()
print('nameplate', round(tot,1), 'mean duration', round(c['en'].sum()/tot,3))
print('generic table on the REAL mix',
      round(float((c['pw']*(c['en']/c['pw']).map(lambda d: _elcc_for_duration(d))).sum()/tot), 4))
"

# the two row-4 arms (concurrent invocations, years sequential within each)
uv run python scripts/run_full_horizon.py --iso CAISO --start-year 2026 --end-year 2030 \
  --out-dir results/ffr4e/caiso-control &
uv run python scripts/run_full_horizon.py --iso CAISO --start-year 2026 --end-year 2030 \
  --caiso-storage-nqc-accreditation --out-dir results/ffr4e/caiso-treated &
wait

# the row-4 verdict, from committed artifacts only
for a in control treated; do
  uv run python scripts/forecast_verdict.py --tier t1f \
    --summary results/ffr4e/caiso-$a/full_horizon_summary.json \
    --run-config results/ffr4e/caiso-$a/run_config.json | grep row4
done
```
