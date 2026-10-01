# FINDING — caiso-184: the chartered object is **REFUTED** — caiso-181's `f_CEMS > 1` BASIS term is **96–97 % a DIAGNOSTIC-basis artifact**, not a model defect. The defect the census *did* find is the outage-derate **DENOMINATOR**, at **4.50 / 5.63 / 7.02 % of envelope depth**. The repair is built, measured and **PROMOTED with EVERY pre-registered gate PASSING**

**Outcome: the charter's headline hypothesis is FALSIFIED and reported as such; a
different, larger, same-lane defect is identified, repaired at ZERO DOF, and promoted.**
C3a moves **+3.9 → +3.7 %**, **+10.9 → +10.5 %**, **+13.9 → +13.1 %** against a
same-head control noise floor of **EXACTLY ZERO** — but **2024 and 2025 remain FAIL, the
determination stays NOT-YET, and the residual does NOT close.** Unlike caiso-183, **no
gate fired and no bar was moved**, so this promotion needs no gate-regression latitude.

Keeper **`2026-08-09-caiso-184-c1-lpbasis`** (was `2026-08-08-caiso-183-b1-hour`).
DOF ledger **UNCHANGED at 11 / 8** on both arms. **ONE** new `ScenarioConfig` field
(`unit_outage_lp_capacity_basis`, default **off**), its matrix row landed in the same PR.
No frozen identification constant touched. **NO data file was re-derived or rewritten** —
both arms read caiso-183's adopted hour-grain extract `25360e90…`.
`calibration-complete.json` and `holdout-freeze.json` **UNTOUCHED** (owner acts).
**2023 + 2024 + 2025 only**, one bundle per arm.

**Pre-registration:** `PRECHECK-caiso184-capacity-basis-2026-08-08.md`, 313 lines,
sha256 `33fa2093…`, pushed and blob-verified (remote SHA identical to local) **before any
measurement of this session's object was taken**.

Instruments: `scripts/probes/_caiso184_capacity_basis_census.py`, `_caiso184_be_proof.py`,
`_caiso184_gbasis.py`, `_caiso184_arm_identity.py`, `_caiso184_solve_arm.py`. Records:
`_caiso184_capacity_basis_census.json`, `_caiso184_be_proof.json`, `_caiso184_gbasis.json`,
`_caiso184_arm_identity.json`.

---

## 1. P0-1 — DO-NOT-REDO, discharged

The CAISO in-model lever queue is **EMPTY**; all nine §5.2 items are struck, so this
charter had to prove a different object or stop.

* **NOT the settled envelope DEPTH question (caiso-181, SETTLED).** That asked *which
  hours* are asserted unavailable and answered **exactly zero** interior contradiction
  across 599,736 hours. This session touches **no window, no hour, no detector constant,
  no threshold**.
* **NOT the grain seam (caiso-183, CLOSED and PROMOTED).** That repaired the day↔hour
  round-trip. The `f_CEMS > 1` term lives **above** the `f_CEMS = 1` line, where no
  availability multiplier at any grain can reach; post-repair it is what **dominates** the
  remaining 2.00 / 2.22 / 1.38 % of depth.
* **NOT any struck lever.** `battery_dispatch_adder`, the offer-surface coverage
  extension, the AS-power-reservation family, every N–S topology lever (FORBIDDEN), the
  seam/intertie family, `caiso_ps_charge_shape_anchor`, `unit_outage_short_windows` /
  `unit_partial_outage_windows` — none re-opened, re-derived or re-tested.
  `caiso_dam_outages` stays `U` and was **not armed**.

---

## 2. P0-2 — THE CENSUS. **The chartered object is REFUTED.**

caiso-181 §2a's BASIS term is `Σ_t (f_CEMS − 1)⁺ × pcap`. Three capacity quantities are in
play, and **caiso-181 measured against the one the LP does not hold**:

| id | quantity | basis | source |
|---|---|---|---|
| **D1** | `_iso_plant_capacity` — the derate denominator AND caiso-181's `f_CEMS` denominator | **net summer** | `outages.py:436`, `eia860.py:1007` |
| **D2** | the binned fleet's actual **LP** `pmax` sum | **nameplate** for CC (keeper config) | `campd_bins.py:1691` |
| **D3** | `Σ pmax × availability(t)` | as D2, seasonally derated | `arrays.py` |

caiso-181 called D1 *"the bin's ENTIRE EIA-860 nameplate"*. **It is net summer**, and for
a CC bin under `cc_nameplate_summer_derate` (armed on the CAISO keeper) it is not the LP's
capacity at all. **That is the correction this section makes.**

### 2a. The decomposition — pre-registered attribution rule, applied verbatim

| MW-h | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `X(N1,D1)` — **caiso-181's BASIS term, reproduced** | 461,441 | 694,328 | 414,254 |
| `X(N2,D1)` — after gross→net | 247,715 | 436,788 | 249,723 |
| `X(N2,D2)` — **after gross→net AND the LP's own basis** | **17,463** | **24,234** | **10,567** |

(caiso-181 measured 461,441 / 694,252 / 414,254; the 2024 difference is that this census
covers **all** bins, not only bins carrying an outage window. A clean positive control.)

| attribution (share of `X(N1,D1)`) | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **H-GROSS** — CAMPD reports GROSS; every model capacity is NET | **46.3 %** | **37.1 %** | **39.7 %** |
| **H-NPBASIS** — denominator net-summer while the LP holds nameplate | **49.9 %** | **59.4 %** | **57.7 %** |
| **RESIDUAL** — the only part that could be a model defect | **3.8 %** | **3.5 %** | **2.6 %** |
| H-REMAP (62115 / 62116 share of base) | 0.000 | 0.000 | 0.000 |

**B-ATTRIB PASSES decisively** — 96.2 / 96.5 / 97.4 % attributed against a 50 % bar.

**B-ARTIFACT FIRES.** The residual is **0.050 / 0.059 / 0.020 % of committed envelope
depth** and **0.00012 / 0.00017 / 0.00008 of thermal capacity-year** — both far inside the
pre-registered 0.5 % / 0.2 % bars. **The LP's capacity basis is NOT contradicted by its
own CEMS record.** Per the pre-registration this branch **licenses no capacity-basis
lever**, and none was taken: `cc_capacity_reconcile` was not armed, its table was not
re-derived, the summer guard was not touched, and no seasonal winter-capacity basis was
introduced.

**H-REMAP is falsified.** caiso-181 named plants 62115 / 62116 (AES Alamitos / Huntington
Beach) as concentrating the excess. They do carry the highest raw `f_CEMS` (1.146 / 1.098),
but once both bases are corrected they fall to **0.994 / 0.965** — *below* 1 — and
contribute **0.000** of the residual. Reported as a falsification of a hypothesis I
pre-registered, not smoothed over.

**What remains above `f_CEMS = 1` after both corrections** is four bins, and it is
concentrated at **plant 358 Mountainview** (1.069 / 1.081 / 1.070) — which is precisely
the **one `raise` row** in the committed `cc_capacity_reconcile_CAISO.csv` (`campd_p999`
1107.6 > current 1036.8). The residual therefore sits at a plant the repo's own
demonstrated-peak table already flags as under-rated. That is `cc_capacity_reconcile`'s
object (CAISO cell `U`), **explicitly out of this charter's scope**, and it is filed, not
acted on.

### 2b. Honesty note on H-GROSS — the measured artifact does not cover CAISO

`parasitic_load_factors.parquet` carries **463 plants and NOT ONE CAISO bin**, so the
gross→net leg fell back to `campd.DEFAULT_PARASITIC_LOAD_PCT` class defaults (CC 2.5 %,
ST_GAS 5.0 %, CT 1.0 %) on **every** bin. **H-GROSS is therefore a class-default estimate,
not a per-plant measurement**, and its 46 / 37 / 40 % split should be read as indicative.
This bounds the precision of the *gross-vs-net* term only: the RESIDUAL — the number
B-ARTIFACT turns on — is measured against the LP's own capacity directly and is unaffected
by the split between the two diagnostic terms.

---

## 3. THE DEFECT THE CENSUS DID FIND — H-DENOM

`arrays.py:929` calls `unit_outage_derate_factors`, whose per-row share is
`removed_mw / plant_capacity_mw` with the denominator **D1 = net summer**. The extract's
`unit_capacity_mw` is written by
`scripts/data/derive_campd_unit_outages.py::build_capacity_index`, whose `derate_mw` is
**EIA-860 NAMEPLATE** — and whose own docstring states the invariant it believes it
satisfies:

> *"so the plant's CT shares sum back to the full block (CT + steam) — **the same basis as
> the model bin denominator the derate divides into**"*

**That invariant is violated.** Numerator nameplate ÷ denominator net summer inflates the
removed **fraction** by `nameplate / net_summer`, so **the model removes more MW than went
out**. It is the identical arithmetic `_iso_plant_capacity` **already forwards
`cc_steam_part_reclass` to prevent** (NEISO 6081 Stony Brook, *"46 % more than actually
went out"*, `outages.py:445-455`) — never forwarded for this flag.

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| over-removal (MW-h) | 1,536,735 | 2,374,969 | 3,688,810 |
| **share of committed envelope depth** | **4.50 %** | **5.63 %** | **7.02 %** |
| rows whose removal would *increase* (G-MONO) | **0** | **0** | **0** |

Computed **EXACTLY, not as a bound**: both availability arrays are rebuilt with the
shipped accumulator, including concurrent-row summation and the `clip(1−v, 0, 1)`.
**B-DENOM clears its 2 % bar in all three years**, so the pre-registered **branch C**
fires and licenses one arm.

**The leg the repair does NOT cover, measured rather than assumed.** The repair moves only
the groups `fleet_to_bins` raises (CC_REGULAR / CC_CHP); at a non-CC bin the same
nameplate÷net-summer mix survives. In CAISO that leg is **nil**: exactly **one** non-CC
bin (ST_GAS) carries outage windows, its extract-capacity/D1 ratio is **0.9434** (below 1,
so no over-removal), and the total unrepaired share of depth is **0.0000**. In another ISO
it need not be — filed as an open item (§8).

---

## 4. THE REPAIR — zero DOF, and byte-inert for every ISO that does not opt in

`ScenarioConfig.unit_outage_lp_capacity_basis` (**default off**) raises the derate
denominator's CC bins by the **same published `cc_summer_derate_ratio`** `fleet_to_bins`
uses, with the same clamp and the same absent-plant fallback — so the two can never
disagree. Threaded `_iso_plant_capacity` → all four factor loaders → `arrays.py` → CLI.

* **ZERO DOF, ZERO fitted scalars.** EIA-860 published nameplate and net summer only.
* **MONOTONE by construction** — nameplate ≥ net summer, so a removed fraction can only
  fall. A falling denominator is a stop-the-line event; **measured 0 across all six ISOs**.
* **Scoped** — zero non-CC bins move in **any** ISO.

**Independent corroboration, and the strongest single number in this finding:** the raised
denominator reproduces the extract's **own** `plant_capacity_mw` — which the deriver builds
from the **same `derate_mw` capacities as the numerator** — **EXACTLY on 11 of 12
EIA-sourced CAISO CC bins** (median ratio **1.000**, against **1.072** unraised). The two
sides of the invariant meet at 1.000 without anything being fitted to make them.

---

## 5. P0-3 — BYTE-EQUIVALENCE

| leg | bar | result |
|---|---|---|
| **BE-1** | gate absent ⇒ `_iso_plant_capacity` identical to the incumbent, all six ISOs | **PASS** — digests measured on the **ACTUAL pre-change tree** (`git stash` of the touched sources), not reconstructed |
| **BE-2 / G-SIXISO** | the repair's reach is exactly the raised groups | **PASS** — 0 non-CC bins move in any ISO; cache-key extension cannot leak an armed map to an unarmed caller |
| **BE-3** | no data file re-derived or rewritten | **PASS** — sha256 ledger; the extract stays at caiso-183's `25360e90…` |
| **G-MONO** | no denominator may fall | **PASS** — 0, all six ISOs |
| **G-CONSIST** | asserted in code **and** in a test | **PASS** — `tests/unit/data/test_outages.py::UnitOutageLpCapacityBasisTest`, 5 tests / 18 subtests |

**BE-2 was restated, not re-scored.** My first form of it compared the *armed* map to the
*unarmed* one for the non-CAISO ISOs — which is not a byte-equivalence statement at all
(it could only pass if the repair did nothing). The defective form is recorded in the
probe's docstring rather than quietly deleted.

---

## 6. A DEFECT THIS SESSION INTRODUCED AND CAUGHT BEFORE ANY ARM WAS SCORED

Adding the field to `ScenarioConfig` moved the **pinned default cache key** off
`603c2498bf71d21d`, which would have **orphaned every on-disk cached run in all six ISOs**
and reddened a blocking guard. Registered in `_CACHE_KEY_OPTIONAL_FIELDS` +
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` (the nyiso-119 discipline, same commit as the field):
the default key returns to `603c2498bf71d21d` and an armed run hashes distinctly
(`224144fce8484fc7`). **Both arms were then killed and re-solved at the final head** rather
than scored on superseded code. Reported because a session that only reports the defects it
found in *other* people's code is not reporting honestly.

---

## 7. THE ARMS — control **BIT-ZERO**, treated narrows C3a in all three years, residual does **NOT** close

Two arms, **one delta**, solved sequentially at one head (rule 12), each 2023 + 2024 + 2025
in **one** bundle (rule 16), both registered (rule 15) with `legitimacy_diagnostics.json`
so **C8 stays SCORED**: `2026-08-09-caiso-184-c0-control` and
`2026-08-09-caiso-184-c1-lpbasis`.

### 7a. CONTROL — bit-zero, and *stronger* than caiso-183's

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| zone-hours differing from the keeper (full precision) | **0** | **0** | **0** |
| of 61,320 | | | |
| C3a | +3.9 % | +10.9 % | +13.9 % |

**The noise floor is EXACTLY ZERO in all three years**, so every treated delta below is
signal. This **corrects caiso-183's carried-forward expectation**: that session measured
−0.0027 / −0.0024 $/MWh of same-head drift on the zero-demand WECC import nodes and warned
the control is not bit-zero. Here it is — in every year. It also establishes that the **27
commits merged to main between the two sessions changed nothing on the CAISO backcast
path**.

### 7b. TREATED — C3a narrows in all three years, and does not close

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| C3a control | +3.9 % (PASS) | +10.9 % (FAIL) | +13.9 % (FAIL) |
| **C3a treated** | **+3.7 % (PASS)** | **+10.5 % (FAIL)** | **+13.1 % (FAIL)** |
| model level $/MWh | 56.30 → **56.17** | | |
| zone-hours moved | 25,390 | 31,200 | 37,395 |
| CC_REGULAR | +0.070 TWh | +0.042 TWh | +0.087 TWh |

The direction matches the **pre-registered prediction** (freed CC capability ⇒ lower
price), which was recorded as **UNKNOWN** precisely so a confirming move could not be
presented as corroboration it was not designed to be.

**IT DOES NOT CLOSE.** 2024 and 2025 remain **FAIL**, determination **NOT-YET**. The repair
takes roughly **1/27** and **1/17** of the remaining excess. The first named remaining
contributor is still the **WALLED hourly pumped-storage water state**
(`FINDING-caiso140` §B / caiso-141 A2) — an **owner-funded intake, not a session lever**.
No close was manufactured.

### 7c. Gate tally — **every gate PASSES**

| gate | verdict |
|---|---|
| **G-DOF** | **PASS** — 11 / 8 on both arms |
| **G-NOFIT** | **PASS** — zero new fitted scalars |
| **G-SIXISO** | **PASS** (§5) |
| **G-MONO** | **PASS** — 0 |
| **G-CONSIST** | **PASS** — code assertion + test |
| **G-BASIS** | **PASS** — `f_CEMS > 1` capacity-year down **90.3 / 89.3 / 91.9 %** (bar 50 %); over-correction median **1.000** (bar ≥ 0.95) |
| **G-C1** | **PASS** — C1 12/12, free 8/8, both arms |
| **G-PROT** | **PASS** — C8 PASS and **SCORED** both arms; C6 **PASS** on the attestation |
| **G-LOYO** | **not reached** — no verdict flipped (both arms NOT-YET), so nothing to score |
| **CONTROL** | **PASS** — bit-zero (§7a) |

**No bar was moved and none fired.** Unlike caiso-183, this promotion rests on no
gate-regression latitude.

---

## 8. DISPOSITION

1. **PROMOTED.** `2026-08-09-caiso-184-c1-lpbasis` is the CAISO keeper. Rule 1
   `[R-STRUCT]` and rule 14 `[R-ACCURATE]` both support it: the model stops violating an
   invariant its own extract deriver declares, at zero DOF, with every gate passing — and
   the fit improves rather than regresses.
2. **The charter's own hypothesis is refuted and the refutation is the headline.** No
   capacity-basis lever was taken, because the census said none was licensed.
3. **caiso-181 §2a's language is corrected**: its `f_CEMS` denominator is **net summer**,
   not nameplate, and for a CC bin it is not the LP's capacity.
4. **No existing adjudication is repealed.** caiso-183's two failed gates stay on the
   record at full magnitude, both bars unmoved, both withdrawals still with the owner;
   this session neither reinstates nor repeals them.

## 9. Known-open, carried forward

1. **C3a's residual: 2024 +10.5 %, 2025 +13.1 %.** First named contributor remains the
   **WALLED hourly pumped-storage water state** — an owner-funded intake. **This is the
   binding data blocker on the CAISO lane.**
2. **The non-CC denominator leg** (§3) — nil in CAISO (one ST_GAS bin, ratio 0.9434), but
   **unmeasured elsewhere**. No verdict transfers (rule 25).
3. **PJM / NYISO / NEISO also arm `cc_nameplate_summer_derate`**, so the same divergence is
   **live and UNMEASURED on their keepers**. They enter as `U`; each lane must measure its
   own magnitude on its own extract before arming (rule 28(d)).
4. **Plant 358 Mountainview** carries the entire post-correction `f_CEMS > 1` residual and
   is the one `raise` row in `cc_capacity_reconcile_CAISO.csv`. `cc_capacity_reconcile`
   (CAISO `U`) is its named mechanism — out of scope here.
5. **Two pre-existing test failures at HEAD**, both reproducing identically on the
   unmodified tree: `NuclearUnitAvailabilityTest::test_unknown_iso_degrades_to_empty` and
   its sibling. Not this charter's object; reported so they are not attributed here.
6. `curate_dam_public_bids.py` still cannot process a full CAISO year (caiso-178).

## 10. Governance

Rule 1 `[R-STRUCT]` — no mechanism judged by its effect on the fit; C3a reported only.
Rule 13 `[R-MEASURED]` — every input EIA-860-published or CAMPD-measured; no measured
outcome, price residual or benchmark entered any input. Rule 14 `[R-ACCURATE]` — the
consistent basis stays; it happened also to improve the fit. Rule 15 / 16 — both arms
registered with `legitimacy_diagnostics.json`, all three years in ONE bundle. Rule 19
`[R-ONE-MECH]` — the repair **replaces** a basis; it stacks no second derate. Rule 21
`[R-DOF]` — ledger 11 / 8, unchanged. Rule 22 `[R-HOLDOUT]` — 2023–2025 only; spend freeze
respected; **both markers untouched (owner acts)**; CAISO holds no `complete`, so no
determination re-key was owed. Rule 23 `[R-FROZEN-DERIVE]` — no derive re-run, no
identification constant re-valued, no data byte changed. Rule 24 `[R-REGISTRY]` — the one
new tunable is in `ScenarioConfig`, in `run_config.json`, and in the CLI; no env knob, no
hardcoded per-plant dict. Rule 25 `[R-ISO-SCOPE]` — CAISO-scoped; no other ISO's keeper
shard, sidecar, status part or bench file written; no verdict transfers. Rule 27
`[R-PUSH]` — the pre-registration was pushed and blob-verified before any measurement;
every push blob-verified by commit-SHA round trip; no existing ≥300-line file rewritten
from regenerated content. Rule 28 `[R-MECH-MATRIX]` — the row landed with the field (duty
c), the CAISO cell and §5.2 header are stamped in this session (duty b),
`check_mechanism_matrix.py` exit 0.
