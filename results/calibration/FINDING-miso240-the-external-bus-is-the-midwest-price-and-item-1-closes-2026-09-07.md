# FINDING miso-240 — `p(MISO_external)` **IS the MISO Midwest energy price**: it ties a border zone in **99.93 / 99.99 / 100.00 %** of hours and ties **ALL FOUR** border zones in **99.91 / 99.99 / 100.00 %**. So `s`'s own-net-load response is a **REAL property of a MISO price, not a modelling artefact**; the one DOF-free candidate at the `s` side measures **exactly ZERO** footprint; and **QUEUE ITEM 1 CLOSES with no DOF-free form to charter**

**Zero LP. No arm, no screen, no bundle, no registration, no cell verdict.**
**Keeper UNCHANGED at `2026-09-07-miso-233-spp-hourly`** (bundle `miso233_sppseam_K`),
DETERMINATION **CALIBRATED**, C3c the single ledgered caveat, DOF ledger **41/2**. Rule 22
`[R-HOLDOUT]`: 2023–2025 only; MISO holds no `complete` marker and **no out-of-training year was
solved, scored or registered**. MISO still carries exactly **one** registered run (rule 15).

**Pre-registration:
`PREREG-miso240-charter-or-refuse-the-external-bus-price-2026-09-07.md`, pushed at `5c503155`
before any adjudicating quantity.** Two addenda, each pushed before the numbers it governs:
`ADDENDUM-miso240-two-decision-rules-fixed-before-the-numbers-2026-09-07.md` (`9316432b`) and
`ADDENDUM-miso240-gate-repair-the-support-predicate-2026-09-07.md` (`c62ad456`). Every decision
rule applied below was fixed in one of those three documents; none was written after seeing a
number. The probe itself was **pushed before it was run** (`9316432b`).

Probe: `scripts/probes/_miso240_external_bus_price_charter_phase0.py` →
`results/calibration/_miso240_external_bus_price_charter_phase0.json`
(+ `_miso240_external_bus_price_charter_phase0_PREREPAIR.json`, §0a).

**Evidence class, stated up front.** §2, §5 and §6 read the keeper's **OWN committed P1 zonal
duals** from `hourly/system_<year>.parquet` — not a reconstruction. §3 rides miso-235's
four-seam **RECONSTRUCTION** (harness `corr(recon, committed)` +0.9845 / +0.9745 / +0.9839) and
is labelled as one throughout. §4 reads committed measured parquets only.

**Basis (PREREG §0b).** Indiana-hub **RT** builds the finite-hour `ok` mask byte-identically to
miso-236/237/238/239. The lane's `da` is the basis of `p1 = da − p_border` and of every merit
signal — and §4b **verifies for the first time** that it really is the Indiana hub. miso-232's
measured decile column (+1,303 / +1,384 / +948) is **not** restated as reproduced by anything
here, and miso-233's own measured South column is not restated as miso-232's.

---

## 0. STATED FIRST, AGAINST INTEREST — four disclosures, three of them costly

### 0a. The provenance gate REJECTED this session's own instrument, at 869.6 MW against a 1e-9 bar

PREREG §1 fixed seven legs and said *"If any leg fails, the instrument is declared BROKEN, the
failure is published, and NOTHING in §3 is read."* **On the first run leg G-ID2 FAILED at
869.6 MW**, in **one cell of six** (2024, the `s`-ladder); the other five cells read
1.91e-11 / 9.44e-11 MW (`s`-ladder, 2023 / 2025) and 1.52e-11 / 1.48e-11 / 7.96e-12 MW
(`p1`-mirror) — **so the bar was not too tight; it caught a real defect.**

The cause was a defect in **this session's own bookkeeping**, not in the object or in any
predecessor: the bin-impurity predicate assigned thresholds to ventile bins with `lo < δ ≤ hi`
against bins that `np.searchsorted(..., side="right")` actually builds as `[lo, hi)`, which
displaces by one position any `δ_k` landing exactly on a ventile edge. The second ADDENDUM
declared the repair **before the repaired numbers existed** and **moved no bar**: impurity
becomes empirical and convention-free, and the falsifiable content is restored as a **new gating
leg `G-ID2b`** (`n_impure ≤ n_crossed_thresholds`, both ladders, all three years) that is
**stricter** than what the PREREG had. After the repair **all eight legs pass** (§1).

### 0b. The §3 values were produced by the failing run and had been SEEN — and the repair is PROVEN not to move them

The probe emits the whole report in one pass, so the failing run also printed every §3 quantity.
That is disclosed rather than papered over, and the second ADDENDUM §3 declared **in advance**
the reason it cannot rescue anything and the check that would prove it: the repair touches only
a REPORTED predicate that feeds no verdict, so every other value must be identical. **Verified
and published**: `s3_values_unchanged_after_repair` = `{verified: true, verdicts_identical:
true}`, a whole-report exact equality against the committed pre-repair artifact after removing
only the repaired predicate's own reported columns, the G-ID2 legs, and the post-hoc census
block (§2a) that postdates both runs. **Not one verdict, share, correlation or MW value below
differs between the two runs.**

### 0c. This session's OWN sharpest intended leg was killed by its OWN pre-registered floor

Q-B (§3) was written to test whether miso-239's `γ_np(s)` column is evidence at all. The first
ADDENDUM §A made the leg **stricter** by requiring the verdict to hold on **both** candidate
denominators, with the PREREG's `100 MW/z` absolute floor applying to each. It fired: the mirror
denominator is **216.48 / 14.18 / 327.89** MW/z and the raw one **−17.62 / −77.83 / +122.31**
MW/z, so **both fall below the floor in at least one year** and **Q-B reads NOT MEANINGFUL and
attaches nothing.** The placebo ratios that would have supported an ARTEFACT reading
(0.0332 / 0.0362 / 0.0039 against the mirror) are reported in §3 and are **not** converted into
a verdict, and the handoff's *"this EVIDENCE points at `s` itself"* reading is therefore
**neither confirmed nor withdrawn here**. It stays exactly what miso-239 made it:
reported-not-gated, chartering nothing.

### 0d. A suspicion this session raised BEFORE the numbers was WRONG, and the gate says so

The first ADDENDUM §B split off Q-C2 because the lane's `da` is read from
`actual_lmp_hourly_MISO.parquet`, whose own builder docstring calls it *"the measured hourly
**system** series"* while the lane calls it the **Indiana hub**. The gate settles it: the zonal
parquet's `INDIANA.HUB` DA equals the lane's `da` to `$0.01/MWh` in **1.0000 / 1.0000 / 1.0000**
of `ok` hours, while every other candidate — the other seven named hubs and the eight-hub mean —
matches in at most **0.0092**. **BASIS CONFIRMED.** The lane's standing label is correct as
written, and this session's suspicion is recorded as refuted.

## 1. The provenance gate — ALL EIGHT LEGS PASS after the declared repair

| leg | what it reproduces | bar | first run | **after repair** |
|---|---|---:|---:|---:|
| **G-P1** | miso-239's `γ_MERIT` (PJM, partial OLS) | ≤ 0.5 MW/z | 0.004 | **0.004 MW/z** |
| **G-P2** | miso-239's `σ_LIN`/`σ_CURVE`/`σ_STEP` | ≤ 0.005 | 4e-05 | **4e-05** |
| **G-P3** | miso-239's BOTH ventile columns | ≤ 0.5 MW/z | 0.003 | **0.003 MW/z** |
| **G-P4** | miso-238's `γ_model` (PJM) | ≤ 0.5 MW/z | 0.004 | **0.004 MW/z** |
| **G-X0** | the PJM export leg identically zero | exact 0 | 0.0 | **0.000000 MW** |
| **G-ID1** | the band-count identity `g(s) ≡ G_{n−1}` | ≤ 1e-6 MW | 0.0 | **0.000e+00 MW** |
| **G-ID2** | pure-bin support identity | ≤ 1e-9 MW | **869.6 FAIL** | **9.87e-11 MW** |
| **G-ID2b** | `n_impure ≤ n_crossed` (both ladders × 3 yr) | inequality | *(new)* | **PASS, 6/6** |

Recomputed from scratch: `γ_MERIT` **−870.18 / −930.93 / −791.43** MW/z; shares
0.6679/0.3063/0.0259 · 0.2839/0.6816/0.0345 · 0.7312/0.2210/0.0479; `γ_np(p1)`
**−677.62 / −662.69 / −590.15**; `γ_np(s)` **−15.70 / +2.00 / −4.41**; `γ_model`
**−866.18 / −1043.37 / −843.45**. **Every one reproduces miso-238's and miso-239's published
column to ≤ 0.004 of its bar**, on an independent code path. `G-ID2b` reads `n_impure` 6/7/4
(`s`-ladder) and 7/8/8 (`p1`-mirror) against `n_crossed` 8/8/7 and 8/8/8 — the arithmetic claim
that a monotone `K`-step function makes at most one bin impure per threshold **holds in all six
cells.**

## 2. Q-A — **INTERNAL-PRICE FORMATION**, and far more strongly than the bar asked. Deliverable (a)

Per hour, `p_ext` classified over the shared node's four border zones (`MISO-Illinois`,
`MISO-Indiana`, `MISO-East`, `MISO-West`) and the offer levels of every seam hosted in it.
`τ = $0.01/MWh`, with the pre-registered sensitivity beside it.

| PJM · `MISO_external` | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **`share(ZONE)`** — ties a border zone | **0.9993** | **0.9999** | **1.0000** |
| `share(BAND)` — ties a seam offer, no zone | 0.0007 | 0.0000 | 0.0000 |
| `share(NEITHER)` | 0.0000 | 0.0001 | 0.0000 |
| **`share(all four border zones tied)`** | **0.9991** | **0.9999** | **1.0000** |
| mean number of border zones tied (of 4) | 3.997 | 4.000 | 4.000 |
| `p_ext = min` of the four / `= max` of the four | 0.9993 / 0.9991 | 0.9999 / 0.9999 | 1.0000 / 1.0000 |
| `p_ext` strictly below all four / above all four | 0.0007 / 0.0000 | 0.0001 / 0.0000 | 0.0000 / 0.0000 |

**VERDICT: INTERNAL-PRICE FORMATION**, on the pre-registered `≥ 0.50` bar, cleared by
99.93–100.00 %. **NOT FRAGILE**: the verdict is identical at `τ = $0.001`, `$0.01` and `$0.10`,
and so is every share to four decimals.

**THE PRE-REGISTERED READING, fixed before the numbers, therefore applies:** `p_ext` is a
**Midwest zonal dual — the MISO Midwest energy price** — so **`s`'s own-net-load response is a
REAL property of a MISO price, not a modelling artefact.** A price that responds to MISO net
load is what MISO's price *is*. **Item 1's own question is answered, and the answer is that
there is no artefact at the `s` side to charter.**

The answer is stronger than "ties *a* zone": the four border zones tie **each other** in
99.91–100.00 % of hours, so the classification cannot distinguish *which* zone sets `p_ext` —
because they are **one price**. `MISO_external_South` behaves the same way against `MISO-South`
(0.9993 / 0.9999 / 1.0000, reported, never gating).

### 2a. POST-HOC, LABELLED, AND IT MOVES NOTHING — where the model's price DOES separate

Not named in the PREREG or either addendum, and it reads **no** gated quantity: every verdict is
computed from `share_ZONE`/`share_BAND`, Q-B's ratios and floor, Q-C's coverage, Q-C2's match
shares and Q-D's shares, none of which touches a value here. It is reported because the reader
should see the context §2's answer sits in.

Hourly `max − min` across zones, on the keeper's own committed P1 duals and on the committed
measured hub DA:

| `max − min`, share of hours > $0.01 · mean · p99 | 2023 | 2024 | 2025 |
|---|---|---|---|
| **model, the 4 border zones** | **0.0002** · $0.0001 · $0.00 | **0.0000** · $0.00 · $0.00 | **0.0000** · $0.00 · $0.00 |
| model, all 6 MISO zones (adds Plains, South) | 0.2830 · $0.91 · $9.41 | 0.2732 · $1.49 · $14.57 | 0.4252 · $2.86 · $23.63 |
| **MEASURED, the same 4 border zones (DA hubs)** | **1.0000** · **$8.75** · $35.25 | **1.0000** · **$8.75** · $51.80 | **1.0000** · **$11.25** · $54.14 |

**The model's Midwest border zones are literally one price; the real ones never are.** The
model's six-zone separation that does exist is the RDT/South and Plains boundary, not the
Midwest. **Rule 28(a): this CORROBORATES `internal_congestion_split` **G** — miso-79's NO-BUILD
and miso-204's "the model reproduces ~2 % of the actual dispersion" — on a new instrument, and
it neither re-tests nor re-opens that verdict.** Nothing here proposes a zonal split.

## 3. Q-B — **NOT MEANINGFUL**, killed by this session's own floor. Reported, and NOT converted into a verdict

The declared placebo: `MERIT_p1 = g(p1) − mean`, the **same frozen ladder `g`** (same `b̄_k`,
same `δ_k`) evaluated on the **measured** spread, containing no model bus price anywhere.

| PJM (RECONSTRUCTION) | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `γ_MERIT` (`s`-ladder) | −870.18 | −930.93 | −791.43 |
| `γ_np(s)` on `MERIT` — miso-239's column | −15.70 | +2.00 | −4.41 |
| ratio | 0.0180 | 0.0021 | 0.0056 |
| `γ_np(p1)` on `MERIT` — miso-239's column | −677.62 | −662.69 | −590.15 |
| ratio | 0.7787 | 0.7119 | 0.7457 |
| **`γ_mirror` denominator** | **216.48** | **14.18** | **327.89** |
| **`γ_raw` denominator** | **−17.62** | **−77.83** | **+122.31** |
| `γ_np(p1)` on `MERIT_p1` — the placebo | −7.19 | +0.51 | −1.29 |
| ratio vs mirror / vs raw | 0.0332 / 0.4079 | 0.0362 / 0.0066 | 0.0039 / 0.0106 |
| `γ_np(s)` on `MERIT_p1` — the cross leg | +275.69 | +238.20 | +378.56 |

**VERDICT: NOT MEANINGFUL.** The PREREG's `100 MW/z` absolute floor, applied by the first
ADDENDUM §A to **both** denominators, is breached by the mirror in 2024 (14.18) and by the raw
in 2023 and 2024 (17.62, 77.83). **The leg attaches nothing, in either direction**, and the
`0.0332 / 0.0362 / 0.0039` column above is reported precisely so that a reader can see the
number this session is declining to read as a verdict. That is what the floor was fixed for, and
it is the same discipline miso-238 applied to three of its four seams.

**Consequences, stated exactly:**
* **Nothing miso-239 published moves.** Its `γ_np(s)` column was REPORTED-NOT-GATED, its PREREG
  §4 said in advance it *"cannot move a verdict"*, and it chartered nothing. Reproduced here to
  ≤ 0.003 MW/z (G-P3).
* **The handoff's "points at `s`" reading is NEITHER confirmed NOR withdrawn.** This session had
  a pre-registered instrument for it and that instrument returned NOT MEANINGFUL. A successor
  wanting to settle it needs a placebo whose denominator clears a meaningful floor — and should
  note that the *reason* the denominators are small is itself informative and un-adjudicated
  here: applying the PJM ladder to the measured spread produces an object with almost no
  own-net-load response at all.
* **The support census, REPORTED:** `n_impure` 6/7/4 (`s`) and 7/8/8 (`p1`) bins of 20, covering
  0.300/0.351/0.200 and 0.350/0.400/0.400 of hours, with the residual **exactly zero** (≤ 9.9e-11
  MW) on every pure bin. It is the *mechanism* by which any such column is bounded; it is **not**
  a verdict and §5 forbids acting on it.

## 4. Q-C and Q-C2 — the measured analogue **EXISTS** and the lane's basis label is **CONFIRMED**. Deliverable (b)

### 4a. Q-C: **EXISTS**

`data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet` carries all four border zones
in all three years (`MISO-East`, `MISO-Illinois`, `MISO-Indiana`, `MISO-West`, plus
`MISO-South`), with DA hourly coverage on the fixed 8,760 grid of **1.0000 / 1.0000 / 0.9999**
per border zone-year, against a `0.95` bar. Hub → model zone is the committed mapping
(`MINN→West`, `ILLINOIS→Illinois`, `INDIANA→Indiana`, `MICHIGAN→East`; **`MISO-Plains` has no
hub**).

### 4b. Q-C2: **BASIS CONFIRMED** — `INDIANA.HUB`

Share of `ok` hours where a candidate's DA equals the lane's `da` to `$0.01/MWh`:

| candidate | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **`INDIANA.HUB`** | **1.0000** | **1.0000** | **1.0000** |
| `MICHIGAN.HUB` | 0.0088 | 0.0092 | 0.0079 |
| `HUB8_MEAN` | 0.0025 | 0.0019 | 0.0017 |
| the other six named hubs | ≤ 0.0014 | ≤ 0.0021 | ≤ 0.0019 |

**The lane's "Indiana-hub DA" label is exactly right**, verified for the first time against an
independent committed source. As the first ADDENDUM §B fixed in advance, this **changes no
predecessor number and moves no verdict** either way.

### 4c. REPORTED, NEVER GATING, AND NEVER A TUNING TARGET (rules 1 / 13)

`corr` of each border zone's measured DA-minus-border spread with the model's `s` and with `p1`:

| zone | `corr(·, s)` 2023/24/25 | `corr(·, p1)` 2023/24/25 |
|---|---|---|
| MISO-Illinois | 0.5549 / 0.4319 / 0.4805 | 0.7678 / 0.7792 / 0.8858 |
| **MISO-Indiana** | **0.4327 / 0.2559 / 0.3790** | **1.0000 / 1.0000 / 1.0000** |
| MISO-East | 0.5821 / 0.4203 / 0.4446 | 0.8409 / 0.8598 / 0.9335 |
| MISO-West | 0.4695 / 0.3971 / 0.5026 | 0.5839 / 0.4573 / 0.7099 |

**Two consistency facts fall out and neither is a verdict.** (i) The `MISO-Indiana` row's
`corr(·, p1) = 1.0000` is the arithmetic consequence of §4b — with the basis confirmed,
`p_meas,Indiana^DA − p_border` **is** `p1` — so the row is an identity check and it passes.
(ii) Its `corr(·, s)` = **0.4327 / 0.2559 / 0.3790** reproduces miso-239's published
`corr(s, p1)` **to the digit**, on a code path that never reads miso-239's value — an unplanned
sixth reproduction of a predecessor's column.

**A construction defect in this session's own reported column, disclosed:** the "zone-matched"
analogue (0.5984 / 0.4320 / 0.4805) was meant to price `s`'s measured twin at *the zone `p_ext`
ties*. Because §2 finds all four zones tie in ~100 % of hours, the first-tie-wins rule
degenerates to *the first zone in a fixed tuple order* (`MISO-Illinois`) — 2024 and 2025 match
the Illinois row to ≤ 0.0001. **It is NOT a location selection and must not be read as one.**

## 5. Q-D — **STAR-COUPLING INERT**, at exactly zero. Deliverable (d)'s live alternative is CLOSED at zero LP

The shared `MISO_external` node hosts PJM, SPP and Manitoba against **one** `p_ext` and links to
four Midwest border zones, so it could in principle price one seam's merit test at a zone on the
other side of the footprint — the defect class `split_miso_south_external_node`'s own docstring
names for South ("a free 3,000 MW bypass around the RDT"), and which
`build_miso_deliverability_groups` leaves open by construction ("External-node border links are
NOT members" of the CIL/CEL groups).

| PJM · shared node | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `share_west_sets` — `p_ext` ties West and is below all three eastern zones | **0.0000** (0 h) | **0.0000** (0 h) | **0.0000** (0 h) |
| `share_east_sets` — the mirror | **0.0000** (0 h) | **0.0000** (0 h) | **0.0000** (0 h) |
| **`share_total`** | **0.0000** | **0.0000** | **0.0000** |

**VERDICT: STAR-COUPLING INERT** (bar: `< 0.02` in all three years), at **exactly zero hours out
of 26,280**, and identical at all three `τ`. **NOT FRAGILE.**

**The pre-registered reading applies: the candidate is CLOSED at zero LP and no solve is ever
spent on it.** The reason is arithmetic and follows from §2: a node that is price-**identical**
to every zone it touches cannot be mispricing any seam against any of them, so **splitting it
per seam cannot move the merit signal by construction.** The per-seam external-node split — the
transform the code already performs for South, over the tie geography already committed in
`IMPORT_NODE_LINKS["MISO"]`'s own comment — is therefore **REFUSED as a lever before it cost a
single LP minute**, which is exactly what rule 29 `[R-SCREEN]`'s clause 0 exists to produce.

**Rule 28(a), as the PREREG fixed in advance:** this is **not** `internal_congestion_split`
(**G** at MISO on miso-79's NO-BUILD), which is about congestion the six-zone topology does not
carry. §5 asked whether the appended external node **bypasses the CIL/CEL groups the topology
already carries**, and the answer is that on the keeper it does not, because there is nothing to
bypass — the Midwest is one price either way. Neither cell moves.

## 6. THE CHARTER — all four legs, and the DOF-free verdict

### (a) How `p(MISO_external)` is FORMED in the LP — ANSWERED

`MISO_external` is a **zero-load transshipment node** appended by
`import_nodes.extend_with_import_node` (`Zone(load_share=0.0)`), carrying the keeper's four
Midwest border links (`MISO-Illinois` 3,300 · `MISO-Indiana` 2,000 · `MISO-East` 2,000 ·
`MISO-West` 4,000 MW; South is re-homed onto `MISO_external_South` by
`split_miso_south_external_node` under the armed `miso_south_seam_split`). The PJM, SPP and
Manitoba seams' 8 import + 8 export pseudo-generators are hosted **inside** it
(`build_reference_price_node`), priced hourly by `inject_reference_price_mc`. The links are
lossless with `flow_cost = 0.0` (`miso_zonal_loss_surface` is off on the keeper, and the loss
split applies to Midwest-**internal** links only), so an interior flow forces the two duals
equal; the Midwest-internal links carry a 40,000 MW placeholder TTC, so what could separate the
Midwest is the published CIL/CEL `InterfaceLimit` groups.

**Measured (§2): it essentially never does.** `p_ext` ties a border zone in
**99.93 / 99.99 / 100.00 %** of hours and ties **all four** in **99.91 / 99.99 / 100.00 %**; a
seam band sets it in **0.07 / 0.00 / 0.00 %**. **`p(MISO_external)` IS the MISO Midwest energy
price.**

**And therefore: `s`'s own-net-load response is a REAL seam property, NOT a modelling
artefact.** `s = p_MISO-Midwest(model) − p_PJM-border(measured)` is a real market's import
economics written down correctly: a footprint imports when its own energy price exceeds its
neighbour's by more than the hurdle. That the model's `s` responds to MISO net load is what
MISO's price *does*. **The premise item 1 was opened on does not hold.**

### (b) The MEASURED analogue of `s`, NAMED, with its basis — ANSWERED

**`p_meas,z^DA(t) − p_PJM-border(t)`** over
`data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet`, on the **DA** basis (the
basis `δ_k` was Q-Q derived against), coverage 1.0000/1.0000/0.9999 (§4a); the RT basis exists
in the same file and is never interchanged with it. At `z = MISO-Indiana` this **is** `p1`, and
§4b confirms the identity to `$0.01` in 100.00 % of hours in all three years.

**What §2 does to this deliverable, and it is the honest half:** because the model prices the
whole Midwest at one dual, **there is no locational choice to make on the model side** — every
`z` is the same `p_ext`. The measured side is not one price (§2a: the four measured hubs
separate in **100 %** of hours, mean **$8.75 / $8.75 / $11.25**), so a measured analogue can be
located and the model's cannot. **That asymmetry is a REPORTED observation and it corroborates
`internal_congestion_split` G rather than re-opening it** (§2a). No basis change is proposed:
`p1` on the Indiana hub is the lane's regressor, it is correctly labelled, and it stays.

### (c) Rule 17 `[R-FLOOR-WINDOW]` — **NOT OWED, because no candidate stands**

The PREREG fixed that this leg is written *"for whatever candidate §3d leaves standing, or
recorded as **not owed** because no candidate stands."* §5 leaves none standing: the only
DOF-free construction this session could name measures a footprint of **exactly zero hours in
26,280**. No floor, no window, no driver and no forecast-regeneration story is owed, because
there is no mechanism to owe them for. **Nothing is proposed here, so rule 17 attaches to
nothing.**

### (d) Rule 19 `[R-ONE-MECH]` — the enumeration, written whatever the verdict

What already sets the PJM seam on the keeper: the armed **hourly PJM neighbour anchor**
(`miso_seam_neighbour_hourly_ladder`, band `k` offered at `p_border(t) + δ_k`); the **frozen
Q-Q `δ_k` ladder** (`MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR`, derived, frozen and pinned to
its derive by test, rule 23); the **export ladder** on the `p_bus` LEVEL
(`MISO_SEAM_LADDER_BY_YEAR[...]["export"]`, structurally inert on PJM — G-X0, 0.000000 MW); the
**measured `(month × hod)` deliverability envelope** (`miso_seam_flow_limit`,
`miso_seam_export_limit`, `miso_seam_envelope_merit_cap`,
`miso_seam_envelope_hour_ending_key`), which sets every `b̄_k`; the four **border-link TTCs**;
the **8,700 MW `MISO_simultaneous_import` SIL**; and the published **CIL/CEL** deliverability
groups. **Nothing is added, so nothing replaces and nothing reconciles** — and the candidate
that would have had to answer this question (the per-seam node split, which would have
**REPLACED** the shared node for PJM/SPP exactly as the South split did, never stacked on it) is
refused at §5 before reaching it.

### THE VERDICT: **NO DOF-FREE FORM EXISTS AT THE `s` SIDE, AND QUEUE ITEM 1 CLOSES**

The handoff fixed the standard — *"A DOF-free construction is the bar… IF NO DOF-FREE FORM
EXISTS, SAY SO AND STOP — that is a complete session result."* It does not exist, on three
independent grounds, each established above rather than argued:

1. **There is no artefact to fix.** `p_ext` is the MISO Midwest energy price in ~100 % of hours
   (§2), so the own-net-load response item 1 was opened on is real.
2. **`p_ext` is not a tunable at all.** It is the LP dual on a zero-load energy balance. Nothing
   can be armed, sized or offset there; the only structural way to change it is to change the
   topology or the constraints that set it — and the one such candidate measures **exactly
   zero** footprint (§5).
3. **The one substitution that would change `s` is FORBIDDEN.** Replacing `p_ext` with a
   measured MISO price in the seam's merit test would feed the model's own **outcome** back into
   its own clearing decision — rule 13 `[R-MEASURED]`'s core prohibition ("pinning an output"),
   and no reformulation of it survives. The *neighbour* price is exogenous and is already
   measured and armed; MISO's own price cannot be.

**SAID, AND STOPPED.**

## 7. What is handed forward — and item 1 closes INTO the existing queue, opening nothing new

1. **QUEUE ITEM 1 IS CLOSED**, on this session's own pre-registered rules. `p(MISO_external)`'s
   formation is answered (a), its measured analogue is named (b), rule 17 is not owed (c), the
   rule-19 enumeration is written (d), and no DOF-free form exists. **A successor should not
   re-open it without new evidence** (rule 28(a)) — and specifically should not re-run §2 or §5,
   whose answers are 99.9–100 % and exactly 0.
2. **THE PER-SEAM EXTERNAL-NODE SPLIT IS REFUSED AT ZERO LP** (§5) and is not to be re-proposed
   on the keeper's topology without new evidence that the Midwest separates.
3. **WHAT THE CLOSURE POINTS AT IS ALREADY ON THE QUEUE, NOT SOMEWHERE NEW.** If the model's
   price-side seam response is structurally *right*, then what makes it too strong is that it is
   the **only** channel the seam has: miso-235 §4b measured the real PJM tie's own `R²` on its
   own measured spread at **0.0577 / 0.0701 / 0.0375**, i.e. the real seam is 94–96 %
   NON-price-driven, while the model's flow is a function of `s` and a deterministic envelope
   and nothing else. That is **handoff items 2/3's territory and miso-236/237's SPP
   quantity-side charter**, which stay exactly where they are filed. **Nothing here charters,
   sizes or names a field for them.**
4. **Q-B IS UNRESOLVED AND IS HANDED ON AS SUCH** (§0c, §3): a successor wanting to settle
   whether miso-239's `γ_np(s)` column is evidence needs a placebo whose denominator clears a
   meaningful floor. This session's did not, and its ratios are reported, not read.
5. **UNCHANGED AND NOT RE-TESTED:** the saturation hypothesis stays **REFUTED** (miso-238);
   miso-239's Q-A stays **MIXED** and its Q-C stays **SURVIVES**, neither re-run; the SPP
   neighbour-state channel stays **QUANTITY-SIDE**, NAMED and **NOT CHARTERED** (miso-237);
   South's neighbour-state route stays **CLOSED** (miso-236 D-4); `miso_manitoba_seam` stays
   **CLOSED as already-armed**; the `(month × hod)` template hypothesis stays **REMOVED**; the
   PJM import/export asymmetry stays **CLOSED FOR PJM** (G-X0 *uses* that closure);
   `internal_congestion_split` **G** (corroborated §2a, never re-tested);
   `vre_reference_rate_curtailment_grossup` **K**; `measured_interface_limits` **R**;
   `miso_rdt_measured_limit` **R**; `miso_south_firm_export_block` **G**;
   `miso_south_export_ladder_rt_tail` **R**; `miso_south_gas_delivered_cost_basis` **R**.
6. **Manitoba determinism** (miso-236 §5.3), **CC_REGULAR 2024→2025 shape emergence** (miso-234)
   and **C3c**, the designated frontier since 2026-07-20, are **untouched** and stay where they
   are filed. C3c still needs a new admissible measured identification **and** an owner ruling;
   no LP is authorized there and none was sought.
7. **NOTHING LICENSES A RE-DERIVE OR A DAMPING FACTOR** on the PJM or SPP `δ_k` ladders, which
   are derived, frozen and pinned to their derives by test (rule 23 `[R-FROZEN-DERIVE]`), or any
   change to the measured `(month × hod)` envelope (rule 14 `[R-ACCURATE]`). PREREG §5.2 fixed
   this in advance for **every** outcome and it binds. **Every number in this document is
   declared UN-TARGETABLE** (PREREG §5.3); miso-236's 328.6 / 341.7 / 207.5 MW sizing stays
   un-targetable and is not re-quoted as a target.

## 8. Non-claims

1. **This session solved nothing.** No screen was run, so nothing here has been through a
   structural gate, and no number is a solve result.
2. **"INTERNAL-PRICE FORMATION" is an attribution, not an endorsement.** That `p_ext` is a real
   MISO price does not make the seam's *gain* right — §7.3 says exactly what it leaves open.
3. **§3 rides a RECONSTRUCTION** (miso-235's four-seam form, +0.9845 / +0.9745 / +0.9839) and is
   labelled as one; **§2, §5 and §6 do not** — they read the keeper's committed P1 duals.
   2024 remains the loosest reconstruction year and is also the year whose Q-B mirror denominator
   (14.18 MW/z) breaches the floor; the two are reported together and neither explains the other.
4. **Q-B attaches nothing in either direction** and its placebo ratios are not quoted as a
   verdict (§0c, §3).
5. **The "zone-matched" measured analogue is NOT a location selection** and degenerates to a
   fixed tuple order because §2's zones all tie (§4c, disclosed).
6. **§2a and the §4c consistency facts are POST-HOC or unplanned** and are labelled; neither
   feeds any verdict, and §0b's exact-equality check proves the whole report is unmoved by the
   only repair this session made.
7. **No verdict moves anywhere in the matrix**, in either direction. Evidence only.
8. **MISO has no failing gate**, and nothing here proposes trading a passing one. There is no
   rubric failure anywhere in the program and this session did not invent one.

## 9. Governance

Rule 1 `[R-STRUCT]`: no mechanism was judged by a residual; the one candidate this session could
name was refused on a **structural** footprint measurement, never on a residual, and every number
was declared un-targetable before it was computed (PREREG §5.3). Rule 12 `[R-PARALLEL]`: no LP;
nothing ran on CI. Rule 13 `[R-MEASURED]`: measurement only; no input changed, no measured
outcome entered any solve, and §6's verdict leg 3 states the prohibition that closes the one
substitution which would have changed `s`. Rule 14 `[R-ACCURATE]`: no input changed; the measured
envelope untouched. Rule 15 `[R-DASHBOARD]`: no run produced, so nothing registered or pruned;
MISO keeps exactly one registered run and the keeper's `hourly/` sidecars stay committed.
Rule 17 `[R-FLOOR-WINDOW]`: no floor added — §6(c) records why none is owed. Rule 19
`[R-ONE-MECH]`: no mechanism added; §6(d) writes the enumeration anyway, as the PREREG required.
Rule 21 `[R-DOF]`: **41/2, unchanged**; every instrument here carries **zero** free parameters,
and `τ`'s declared sensitivity shows both verdicts invariant across two orders of magnitude.
Rule 22 `[R-HOLDOUT]`: 2023–2025 only; MISO holds no `complete` marker and no out-of-training
year was solved, scored or registered. Rule 23 `[R-FROZEN-DERIVE]`: no derive re-run, and §7.7
restates the freeze. Rule 24 `[R-REGISTRY]`: no field created. Rule 25 `[R-ISO-SCOPE]`: MISO's
shard, section and lane only. Rule 26 `[R-DELETE]`: the defective impurity predicate was
**replaced**, not left behind a flag. Rule 27 `[R-PUSH]`: on-disk edits only, every pushed blob
≥300 lines verified against local after push. Rule 28(a): queue item 1 taken and CLOSED; every
standing adjudication touched is corroborated or untouched, never re-tested. Rule 28(b): no
verdict moves; evidence appended in MISO's shard in-session. Rule 29 `[R-SCREEN]`: clause 0 in
full — zero-LP phase 0, and it **answered the successor's question, closed a queue item and
REFUSED the only DOF-free candidate it could name before a single LP minute was spent**, which
is the outcome the clause exists to produce.
