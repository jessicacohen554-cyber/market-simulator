# PREREG nyiso-130 — the Long Island in-window transfer cap is a *capacity* quantity doing an *energy* job; reconcile it to NYISO's published transfer limit

**Registered BEFORE any solve.** Session nyiso-130, 2026-08-06. Keeper under
test: `2026-08-06-nyiso-128-solar-basis` (bundle
`results/calibration/nyiso128_treatment`), determination **NOT-YET**, sole FAIL
**C3c-2023**. Lever-queue item 1 (`docs/mechanism-testing-matrix.md` §5.5), named
by nyiso-129 §3a. **Rule 22: 2023–2025 only**; the holdout spend freeze is active
and untouched.

Everything in §1–§3 is measured, from committed artifacts and NYISO's own
postings, with **no solve spent**:
`scripts/probes/_nyiso130_li_tsl_identification.py` →
`results/calibration/_nyiso130_li_tsl_identification.json`.

---

## 1. The defect, stated as a category error (not as a residual)

`nyiso_li_lcr_tsl` (armed on every NYISO keeper since nyiso-61) caps the model's
**only** mainland→Zone-K AC link, `NYC>Long_Island`, at the published NYISO
**Zone-K "Locality Limit"** — 325 MW (2023) / 275 MW (2024, 2025) — inside the
HB14-21 design-cooling window, and `model/interchange/nyiso.py` already flags the
boundary mismatch in its own docstring.

NYISO's own report says what that number is. From **TABLE 1** of the Locality
Bulk Power Transmission Capability Reports, note 2, verbatim and **identical in
the 2024-25, 2025-26 and 2026-27 editions**:

> *"The true N-1-1 Transmission Security Limit is 940 in this scenario, the Bulk
> Transfer Limit accounts for the loss-of-source of 660 MW."*

So the quantity the model uses as an **hourly energy transfer bound** is:

```
published Locality Limit  =  transfer limit (940 MW)  −  generation loss-of-source (660 MW, Neptune HVDC)
```

That is a *capacity-market deliverability* construction — it is consumed by the
LCR **TSL Floor Calculation**, where the 2023 LCR Report enters it as
`Transmission Security Limit (MW) [B] = Studied 325` and computes
`UCAP Requirement [C] = [A] − [B]` against a **load forecast**. A term that is
subtracted from a load forecast to size an ICAP requirement is not a transfer
limit on an hour.

**The same interface, in every edition, has the same physical basis** — limiting
element Dunwoodie–Shore Road (Y50) 345 kV @ **LTE 964 MVA**, limiting contingency
loss of Sprain Brook–East Garden City (Y49) — and the model's single link
represents exactly the interface Appendix A defines (Y49 + Y50 from Zone I, plus
the two PAR-controlled 138 kV J–K ties).

### 1a. Why the 660 MW deduction is a DOUBLE COUNT in this model specifically

The deduction exists so the ICAP requirement survives Long Island losing its
largest source, the 660 MW Neptune HVDC. The model already represents that
phenomenon **twice over**, explicitly:

1. **Neptune's energy is delivered on a separate link.** `NYISO_external>Long_Island`
   (Neptune 660 + Cross Sound 330 + Northport-Norwalk 1385 200) carries a measured
   seam envelope of 1,012 / 986 / 990 MW and sits **at its bound in 99.9 / 99.9 /
   98.9 %** of all hours. The model therefore *delivers* the 660 MW and *also*
   deducts 660 MW from the AC link for the possibility of losing it.
2. **The contingency reserve against losing it is already carried**, by the armed
   `nyiso_li_locational_reserve` — NYISO's own published Zone-K locational reserve
   ladder (`li_30min_total`), a keeper `K` cell since nyiso-113.

Rule 19 `[R-ONE-MECH]`: one mechanism per phenomenon. A generation-contingency
reserve embedded inside a *transmission* bound, on top of an explicit reserve
requirement for the same contingency, is the duplicate — and it is the implicit
one, so it is the one that goes.

### 1b. D-2 enumeration — what already owns Zone K (rule 19, done before proposing)

Read off the keeper's committed `legitimacy_diagnostics.json`:

| mechanism | what it owns in Zone K | status |
|---|---|---|
| `nyiso_li_lcr_tsl` | in-window bound on `NYC>Long_Island` | **the mechanism under reconciliation** — no forced energy, correctly absent from D-2 |
| `nyiso_li_locational_reserve` | published Zone-K locational reserve ladder | armed, keeper `K` — **the correct home of the loss-of-source phenomenon** |
| `nyiso_seam_deliverability_envelope` | measured P-32 envelope on `NYISO_external>Long_Island` | armed, keeper `K` — untouched here |
| `nyiso_local_selfsupply` | LI 0.45 energy floor | **skips Long_Island** whenever `nyiso_li_lcr_tsl` is on — confirmed absent from D-2 |
| `reliability_floor × ST_GAS` | LI persistent 24 h ST_GAS base (0.262) | live; the LI_ST_ev / LI_CT_ev **peak-window ramps are OFF** (`NYISO_PEAK_WINDOW_FLOORS_OFF`) |

**Nothing is stacked.** This is a change of one published number inside one
already-armed mechanism. No floor is added, no window is changed, no other link
is touched.

## 2. The identification — published, zero free parameters

`transfer_security_limit` (Long Island) = **940 MW**, all three years.

| capability year | published Locality Limit | stated true N-1-1 TSL | loss-of-source | limiting element |
|---|---:|---:|---:|---|
| 2023/24 | 325 MW | *(not stated)* | 660 MW (as the limiting contingency) | Y50 @ LTE 964 MVA |
| 2024/25 | 275 MW | **940 MW** | 660 MW | Y50 @ LTE 964 MVA |
| 2025/26 | 275 MW | **940 MW** | 660 MW | Y50 @ LTE 964 MVA |
| 2026/27 | 275 MW | **940 MW** | 660 MW | Y50 @ LTE 964 MVA |

**Declared, against interest:** the 2023-24 edition does not print a true-N-1-1
figure. Its Zone-K table carries the *same* limiting element at the *same*
LTE 964 MVA rating with the *same* 660 MW Neptune loss-of-source, and NYISO's own
Table 4 records the Zone-K limit **unchanged 2022 → 2023**, attributing the later
325 → 275 move purely to *"a change in methodology of this study"* — not to any
physical change. The arithmetically implied 2023-24 figure is 325 + 660 ≈ **985 MW**.
**We use the published 940 MW for 2023 as well**, i.e. the *tighter* of the two
in the year whose gate this lever is expected to help. One published constant,
carried across three years; **no per-year value is fitted and `n_residual` is
unchanged at 6.**

Forward-reproducible (rule 13 `[R-MEASURED]`): NYISO publishes this table every
capability year, and it responds to changed conditions (the G-J row moves
3,425 → 4,350 → 4,500 → 4,525 MW across the same four editions as new circuits
enter service).

## 3. Where the model stands (measured, keeper artifacts)

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| in-window bound on `NYC>Long_Island` | 325 | 275 | 275 MW |
| flow at that bound, in-window p50 / p95 | 325 / 325 | 275 / 275 | 275 / 275 MW |
| share of in-window hours at bound | 80.1 % | 85.5 % | 66.3 % |
| off-window bound (untouched) | 1,650 | 1,650 | 1,650 MW |
| **C3c model tail hours** | **22** | **3** | **24** |
| RT actual tail hours | 10 | 12 | 42 |
| gate band [0.5×, 2×] | [5, 20] | [6, 24] | [21, 84] |
| gate status | **FAIL (2.20×)** | CAVEAT (0.25×) | PASS — **3 h above the lower edge** |
| **share of tail hours that are Long Island** | **100 %** | **100 %** | **100 %** |
| **share of tail hours inside HB14-21** | **100 %** | **100 %** | **100 %** |
| both Zone-K links at bound, in tail hours | **100 %** | **100 %** | **100 %** |

**The whole of NYISO's modelled scarcity tail, in every year, is Long Island in
the window this bound is applied, with the bound saturated.** That is the finding
the A/B is designed around, and it is why the adverse case below is stated so
sharply.

## 4. The arm

New `ScenarioConfig` field `nyiso_li_tsl_n11_security: bool = False`
(default off ⇒ byte-identical; NYISO-only; effective only when
`nyiso_li_lcr_tsl` is on). When armed, `apply_nyiso_li_tsl_import_cap` reads the
`transfer_security_limit` metric instead of `import_limit`.

* **control** — `python scripts/probes/_nyiso128_solve_ab.py --arm control`
  (reproduces the designated keeper; recipe fidelity verified at nyiso-129).
* **treatment** — the same, `--override nyiso_li_tsl_n11_security=true`.
* Both arms: `--years 2023 2024 2025`, 8760 h, run concurrently (rule 12).
* `--verify-only` is run on **both** arms before either full arm is spent.

## 5. Ex-ante predictions

* **P1 (live)** the arm's `hourly/network_<year>.parquet` shows in-window
  `limit_up` on `NYC>Long_Island` = **940.0** in all three years; the control
  shows 325 / 275 / 275. Off-window stays 1,650 in both.
* **P2 (direction)** in-window LI import rises and the link's in-window at-bound
  share **falls** from 80.1 / 85.5 / 66.3 %.
* **P3 (substitution)** the relieved LI energy is displaced from the **in-zone**
  fleet, not from the seam: LI in-window CT_PEAKER + ST_GAS generation falls
  while `NYISO_external>Long_Island` is unchanged (it is already bound).
* **P4 (tail)** C3c tail hours **fall in all three years** — necessarily, since
  100 % of them are Long Island at this bound.
* **P5 (C3a)** mean LMP **falls** in all three years, most in 2025 (LI in-window
  price p95 $167.3 vs $73.6 in 2023).

## 6. Kill gates — these, and only these, refute the arm as BUILT

| # | gate | fails if |
|---|---|---|
| **K1** | config isolation | more than ONE `scenario_config` field differs between arms |
| **K2** | feasibility | any new unserved energy (slack) or dump in any year, either arm — a *loosening* must never create shortage |
| **K3** | liveness | in-window `limit_up` ≠ 940.0 in any year (the mechanism must never silently no-op — it already raises rather than no-ops) |
| **K4** | scope | any other link's `limit_up` changes, including `NYISO_external>Long_Island` |
| **K5** | seam | the priced import-node ±2 % monthly reconciliation band breaks in any month of any year — the arm must not import its way out through the seam |
| **K6** | forcing | any D-2 mechanism's forced share **rises**, or `nyiso_local_selfsupply` reappears for Long_Island (rule 19), or C8 flips |

## 7. THE ADVERSE CASE, stated before the solve

Because **100 % of the tail is this bound in every year**, the arm removes tail
hours in the two years that do not want them removed:

* **2024** is already 3 h against 12 h. It goes lower. It already rides the
  ledgered caveat.
* **2025** is 24 h against a band whose **lower edge is 21 h**. A loosening of
  665 MW into a zone whose in-window p50 demand is 2,437 MW (**27 %**) is very
  likely to take it below 21 and turn a PASS into a **new FAIL**.

**So the single most likely outcome is that C3c stops failing HIGH in 2023 and
starts failing LOW in 2025 — the fail moves years and the determination does not
improve on its own.**

**That is pre-registered as NOT a refutation** (rule 1 `[R-STRUCT]`). The arm
replaces a demonstrably mis-typed quantity with the published one and removes a
double count the model carries twice elsewhere; the fit is not what licenses it.
If the tail does collapse, the finding is that **NYISO's modelled scarcity tail
was manufactured by a mis-typed transfer bound** — a discovery about where the
real tail must come from, not a reason to keep the wrong number. The magnitudes
will be reported at full size in every year, whichever way they go.

Also watched, and named as the thing that could genuinely go wrong:
**C3a regression in the two years that pass most comfortably.** C3a is
+8.8 / +0.8 / −3.2 % against a ±10 % band; the arm pushes all three **down**, so
2023 moves *away* from its edge while **2024 and 2025 move toward the −10 %
edge**. A C3a breach is a real refutation (§8).

## 8. Disposition, fixed in advance

* **PROMOTE** if every kill gate K1–K6 is silent and C1 / C2 / C3a / C3b / C4 /
  C6 / C8 all still PASS — **whatever C3c does** (rule 1). The mechanism's
  licence is the published number and the removed double count.
* **REJECT** on any kill gate, or on any load-bearing criterion (C1 / C2 / C3a /
  C3b) or protective criterion (C6 / C8) failing.
* **OWNER DIRECTIVE, given in session 2026-08-06, verbatim:** *"After this run if
  the only outstanding issue is c3c scarcity tail of +12 hours in 2023 I want
  NYISO registered as calibrated with caveats. C3c is an acceptable gate failure
  as a ledgered caveat."* Applied as written: **if C3c is the sole failing
  criterion on the run that ends up designated, it is carried as a LEDGERED
  CAVEAT and the determination reads CALIBRATED-WITH-CAVEATS.** This supplies the
  in-training authorization rule 22's C3c standing rule does not reach (that rule
  is out-of-training only), and it resolves nyiso-129's withheld 2023 exception.
  Two disciplines are kept, not waived:
  1. **The 2023 entry gets its OWN, correctly-signed classification.** It is an
     *over*-production; the inherited 2024 exception's classification licenses
     only an *under*-production. It will **not** ride under that entry — a new
     entry is written, citing this directive. The withheld-exception guard in the
     attestation generator stays in place for any future wrong-sign miss.
  2. **The miss is reported at full magnitude**, never softened, and the
     directive reaches **C3c alone** — if anything else fails, the determination
     is not CALIBRATED-WITH-CAVEATS.
* **ESCALATE** rather than silently promote if the re-verified determination is
  *worse* than the incumbent's (rule 22 D-5(b)); NYISO holds a `complete` marker,
  so a promotion also re-keys and re-verifies it in the same commit.

## 9. Duties this session owes regardless of outcome

Rule 15 (register both arms on the dashboard, all three years, same session),
rule 28 (update the matrix cell + citation, rejection included; a new
`ScenarioConfig` field needs its own row in the same PR), rule 27 (verify pushed
blobs ≥300 lines), rule 20 (DOF ledger — this arm adds **zero** free parameters).
