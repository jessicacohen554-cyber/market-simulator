# PRE-REGISTRATION — caiso-139 `dump_cost_full_offer_domain` (single delta)

**Written and committed BEFORE either arm was solved.** No arm result existed
when this document was frozen. Gates below are final — a gate this document
does not contain cannot be quoted as a pass. Format follows
`PREREG-caiso138-firm-envelope-clip-2026-07-29.md`.

Charter: the caiso-139 session brief (the caiso-138 §B β defect, filed there
and explicitly handed to its own charter). D1–D4 were passed on committed bytes
before any solve; the instrument is
`scripts/probes/_caiso139_dump_cost_blindspot.py` (§A–§E), run against the
keeper `results/calibration/caiso138_envclip_B`
(`2026-07-29-caiso138-envelope-clip`, NOT-YET, fail {C3a-2025, C3c}).

---

## §0 — what the D-gates established (no solve)

**D1 — the β dump, quantified on the NEW keeper** (probe §A; the caiso-138 clip
has already removed the α component, so what remains is β and nothing else):

| year | WECC_PNW dump | WECC_DSW dump | dominant tranche inside those hours |
|---|---|---|---|
| 2023 | 0.0000 TWh / 0 h | 0.0000 TWh / 0 h | — (no dump at all) |
| 2024 | 0.0088 TWh / 5 h | **0.5218 TWh / 175 h** | `DSW_surplus_clean` 0.8157 TWh (+ CCGT/CT/scarcity) |
| 2025 | 0.0141 TWh / 8 h | 0.0208 TWh / 24 h | `DSW_surplus_clean` 0.1214 TWh; PNW `PNW_midC` |

Node λ is **−26.001 (the dump optimum) in the median of every dump-hour set**.

**D2 — attribution is exact and complete** (probe §B). The objective's guard was
`dump_cost = 26.001` in all three years (wind −26.000 / solar −20.000 /
−storage_eac −0.000). Against the LP's own reconstructed offer array:

| year | rows below −dump_cost | PNW dump hrs WITH a gamed offer | DSW dump hrs WITH one | dump hrs WITHOUT one |
|---|---|---|---|---|
| 2023 | **0** | — (0 dump hrs) | — (0 dump hrs) | **0** |
| 2024 | 7 (`PNW_midC`, `DSW_CCGT`, `DSW_CT`, `WECC_scarcity`, `DSW_surplus_clean`, `DSW_overnight_clean`, `DSW_daytime_clean`) | **5/5** | **175/175** | **0** |
| 2025 | 4 (`PNW_midC`, `DSW_surplus_clean`, `DSW_overnight_clean`, `DSW_daytime_clean`) | **8/8** | **24/24** | **0** |

Both directions hold: every dump hour carries a producible offer below
−dump_cost, no dump hour lacks one, and 2023 — the year with *no* row below the
guard — has *no* dump. Deepest offers: −29.693 (PNW 2024), −58.239 (DSW 2024),
−31.437 (PNW 2025), −36.261 (DSW 2025), i.e. **$3.69–32.24/MWh of pure
generate-to-dump profit**. The converse census (DSW 2024: 241 gamed-offer hours,
of which 175 dump) shows a gamed offer forces a dump only when the corridor is
already cap-bound — consistent with the mechanism, not with a coincidence.

**D3 — the CA-side invariance facts** (probe §C, committed bytes):

* **CA zones never dump.** Total CA dump = 0.000000 MWh, 0 zone-hours > 0, all
  three years. The Dump column is at its lower bound in every CA zone-hour.
* **CA λ never reaches the guard.** min CA λ = **−20.0000** vs −dump_cost
  −26.0010 (repaired: −58.2397 in 2024, −36.2618 in 2025); zone-hours at
  λ ≤ −dump_cost + 0.01: **0**.
* **The corridor is cap-bound in 100 % of the affected hours** — WECC_PNW 5/5
  and 8/8, WECC_DSW 175/175 and 24/24, flow ≡ group cap to 1e-3.

The Dump column's reduced cost is `dump_cost + λ_z`. **Raising** dump_cost can
only *raise* it, so a column already at its lower bound stays there: the CA
primal and every CA dual are unchanged, and the delivered corridor flow in the
affected hours is the cap before and after. The E1/E2 prediction below is
therefore analytic, not a guess, and the caiso-134 SSB replacement-ladder is not
invoked — its trigger (corridor flow changing in ANY hour) cannot fire when the
flow is at cap in every hour the delta touches.

**D4 — no fitted parameter** (probe §D). The repaired guard per year, read off
the model's own offer arrays:

| year | current | repaired | driver row | row min mc | sink rows | sink mc min |
|---|---|---|---|---|---|---|
| 2023 | 26.0010 | **26.0010** | `WECC_DSW_DSW_overnight_clean` | −18.4721 | 2 | −18.5587 |
| 2024 | 26.0010 | **58.2397** | `WECC_DSW_DSW_overnight_clean` | −58.2387 | 2 | −58.2407 |
| 2025 | 26.0010 | **36.2618** | `WECC_DSW_DSW_overnight_clean` | −36.2608 | 2 | −36.4392 |

No threshold, percentile, margin or residual-derived value enters. The
producible mask (`pmax > 0`) is a structural row property, not a parameter —
and it is load-bearing: the `sink mc min` column shows the export sinks sit
*below* the producible minimum (2024: −58.2407 vs −58.2387), so dropping the
mask would inflate the guard off a **withdrawal** price that is a
willingness-to-pay, not a production credit.

**Cross-ISO reach (rule 25 [R-ISO-SCOPE], charter's explicit ask)** — probe §E,
every ISO keeper's own fleet reconstructed, all three years:

| ISO | keeper bundle | min producible mc | verdict |
|---|---|---|---|
| CAISO | `caiso138_envclip_B` | −18.47 / **−58.24** / **−36.26** | guard widens in 2024–2025 |
| ERCOT | `ercot137_margin_arm` | −2.84 / +1.40 / +1.40 | **UNCHANGED (byte-identical)** |
| MISO | `miso101_tempgrain_B` | +1.40 / +1.40 / +1.40 | **UNCHANGED** |
| NEISO | `neiso61_netrev_margin` | +1.40 / +1.40 / +1.40 | **UNCHANGED** |
| NYISO | `nyiso96_ctamort` | +1.40 / +1.40 / +1.40 | **UNCHANGED** |
| PJM | `pjm137_ctheatrate_B` | +1.40 / +1.40 / +1.40 | **UNCHANGED** |

PJM's row is measured with `pjm_da_virtual_bids` disabled (its raw source is not
in this container); the virtual layer is settled **analytically and more
strongly than by measurement**: DEC rows are built `pmax 0 / pmin −peak`
(outside the injectable mask by construction) and INC rungs are floored at
`virtual_bids._inc_offer_floor` = `min_credit + ε`, i.e. `≥ −dump_cost + ε` in
every hour by construction — the same invariant this session is repairing,
already enforced there on the offer side.

No non-CAISO keeper carries an injectable offer within $24/MWh of the guard, so
the repair is **CAISO-only in effect**. It nevertheless ships **flag-gated,
default off**, because `dump_cost` is ISO-agnostic LP infrastructure: each ISO's
lane arms it on its own evidence (rule 25), and the gate keeps every existing
cache key byte-stable (the flag is registered in the `scenarios.py` cache-key
drop list — the caiso-138 field was the sixth miss of that one line).

## §1 — the delta (ONE switch, one widened guard, zero new free parameters)

**Arm B** = the keeper recipe replayed at this session's HEAD **plus the single
flag**:

```
PYTHONPATH=.:src .venv/bin/python scripts/replay_keeper.py \
    results/calibration/caiso138_envclip_B \
    --out-dir results/calibration/caiso139_dumpguard_B \
    --set dump_cost_full_offer_domain=true \
    --note "caiso-139 dump-cost full offer domain (single delta)"
```

* **Arm A** `results/calibration/caiso139_control_A` — keeper recipe, no delta,
  same HEAD, same container, same regenerated `capacity-deliverability` /
  `hydro-plant-modes` partitions (both curated before either solve). Expected to
  reproduce the committed keeper sidecars exactly; that reproduction is also the
  proof that the flag-**off** code path is byte-identical on the full solve
  path. Registered as the run explorer's control arm per rule 15.
* Both arms `--year 2023 2024 2025` in ONE invocation (rule 16), years
  sequential within each run, arms sequential to each other (rule 12 — CAISO is
  single-solve-only on this 15 GB box).

**What the flag does** (`model/lp/costs.py::build_cost_vector` via
`model/lp/model.py::DispatchModel.solve`): the dump price's minimum, today taken
over `(wind_mc, solar_mc, −storage_eac)` alone, additionally spans every `mc`
row that can INJECT (`pmax > 0`):

```
dump_cost = max(ε, −min(0, wind_mc, solar_mc, −storage_eac, min_{pmax>0} mc) + ε)
```

* **DRIVER (rules 13/14/17)**: the bound is the model's own offer set, computed
  per solve. It is an LP soundness invariant — *no row may profit by generating
  purely to dump* — not an overlay, so it regenerates from whatever offer set a
  forecast year assembles. Window = wherever an injectable offer sits below the
  incumbent guard.
* **DOF added: zero** (rule 24).
* **Rule 19 [R-ONE-MECH]**: the SAME guard widened to its own stated domain, not
  a second mechanism stacked on the residual.
* **Rule 14 [R-ACCURATE]**: the alternative repair — flooring the import
  tranches' offers at −dump_cost, the `data/virtual_bids.py::_inc_offer_floor`
  treatment — is **rejected here**, because on this corpus it would actively
  bind on measured hub prices (2024 DSW: −58.24 rewritten to −26.00) rather than
  stay the structural no-op it is for the PJM virtuals. Burying the guard's
  incompleteness inside a measured input is exactly what rule 14 forbids.

## §2 — pre-registered predictions and gates

* **P1 (primary, kill if missed).** Arm B's dump goes to **zero at both WECC
  pseudo-nodes in all three years**: WECC_PNW 0.0000/0.0088/0.0141 → ≤ 0.001 TWh
  and WECC_DSW 0.0000/0.5218/0.0208 → ≤ 0.001 TWh, dump-hour counts 0/5/8 and
  0/175/24 → 0. Any residual dump above 0.001 TWh is a NEW defect and a
  stop-and-report (D2 says every current dump hour is attributable, so a
  residual means an unmodelled channel).
* **P2 (E-envelope, kill if missed).** CA demand-weighted annual LMP move vs
  arm A (`ca_lambda`, WECC seam zones excluded): **2025 ≤ +$0.00** and
  **2024 ≤ +$0.30** (ask memo caiso-131 §2 E1/E2). Point prediction **+$0.0000
  both**, and the stronger form: **max CA per-zone-hour |Δprice| = 0.0000** —
  the CA-side LP is byte-identical by the D3 reduced-cost argument. Tolerance
  for LP degeneracy noise ±$0.02; **a CA move beyond that tolerance falsifies
  the D3 argument and is a stop-and-report, not a re-tune.**
* **P3 (rubric).** Arm B's C-gate rubric is IDENTICAL to arm A's (fail set
  {C3a-2025, C3c}, determination NOT-YET). Any scored-gate flip vs arm A in
  either direction is a stop-and-report.
* **P4 (2023 null control, kill if missed).** The repaired guard equals the
  incumbent guard in 2023 (26.0010 → 26.0010, D4), so **arm B's 2023 must be
  byte-identical to arm A's 2023** on prices and dumps (max |Δ| = 0). A 2023
  difference means the code path does something the D-gates did not describe.
* **P5 (reported, not gated).** The node price at WECC_DSW / WECC_PNW in the
  former dump hours, against the measured PALOVRDE / MALIN hub in the SAME
  hours. The corner is LP-degenerate once the dump stops binding; the print is
  reported as found. Also reported: the tranche energy withdrawn at each node
  (the phantom revenue removed).
* **Control integrity.** Arm A reproduces the committed keeper's scored metrics
  and hourly series; a material arm-A drift vs `caiso138_envclip_B` is
  investigated before any B-arm claim is made.

Promotion is NOT pre-granted: if P1–P4 hold, the flag is a keeper CANDIDATE and
promotion is a separate owner act. Rule-22 LOYO note prepared in advance: the
mechanism carries no fitted parameter and its predicted CA-side effect is
exactly zero in every year, so there is nothing to overfit — the criterion is
satisfied degenerately, exactly as for caiso-138. Whatever the verdict, both
arms are registered on the dashboard (rule 15) and the matrix row is stamped in
this session (rule 28 duties b/c).
