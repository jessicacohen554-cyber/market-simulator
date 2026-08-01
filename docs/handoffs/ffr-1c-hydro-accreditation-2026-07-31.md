# FFR-1C — Conventional hydro in the accredited-supply ledger (I7/A2) — 2026-07-31

**Lane.** FFR-1C of `docs/forecast-readiness-prompt-pack-2026-07.md` §Wave 1,
executing audit row **P1-e** and closing finding **FR-3**
(`docs/forecast-readiness-audit-2026-07.md` §3.1) / gap-register **R5c**
(`docs/gap-register-2026-07.md`). Implements the spec FF-2B routed here
(`docs/handoffs/ff-2b-adequacy-basis-2026-07.md` §4).

**Every credit is an ISO-published accreditation factor with a primary-source
citation. Nothing here is tuned to clear I7, and the residual gaps are written
up as findings rather than closed (rules 1/5/13/21).**

---

## 1. Headline

T0 base-year probe, `run_full_horizon.py --start-year 2026 --end-year 2026`
(1 solve-year per invocation, §2.1b cap respected), HEAD defaults, before vs
after the change. All six runs registered on the **forecast** namespace.

| ISO | I7 before | I7 after | Δ accredited firm | Gap closed | Verdict |
|---|---|---|---|---|---|
| **NYISO** | FAIL 30,322 < 32,121 (−1,799 MW) | FAIL 32,085 < 32,121 (**−36 MW**) | **+1,763.3** | **98.0 %** | FF-2B's diagnosis CONFIRMED — the hydro exclusion *was* essentially the whole NYISO gap |
| **CAISO** | FAIL 46,105 < 57,306 (−11,201 MW) | FAIL 50,729 < 57,306 (**−6,577 MW**) | **+4,624.8** | 41.3 % | residual is the FF-2B-routed peak-currency + VRE/storage-ELCC stack, NOT closed here |
| **MISO** | FAIL 133,834 < 141,341 (−7,507 MW) | FAIL 135,304 < 141,341 (**−6,037 MW**) | **+1,470.4** | 19.6 % | residual open, see §5 |

**Attribution is exact.** Each ISO's movement equals its cited credit times the
model's own dispatched hydro nameplate, to the MW:

| ISO | modelled hydro nameplate | × published credit | = expected Δ | measured Δ |
|---|---|---|---|---|
| CAISO | 6,568.4 MW | 0.7041 | 4,624.8 | **4,624.8** |
| MISO | 2,371.5 MW | 0.62 | 1,470.3 | **1,470.4** |
| NYISO | 4,587.1 MW | 0.3844 | 1,763.3 | **1,763.3** |

Nothing else moved: peak, requirement, and the entering fleet are identical in
both arms of every pair (the adequacy backstop built 0 MW in all six runs at
2026), so there is no secondary fleet response to disentangle. Movement is
attributable to the cited credits **alone**, as the prompt required.

---

## 2. What was wrong

`accredited_firm_capacity_mw` (`model/capacity_evolution/adequacy.py`) is
assembled from the **persistent `fleet`** plus the wind/solar pools, storage
ELCC and firm imports. Conventional hydro is an **energy-budget** resource: it
is built by `data/hydro.py::build_hydro_fleet` into the *transient dispatch*
fleet only, and `runner.py` carries the un-split, hydro-less fleet to the next
year. So hydro was **fully dispatched and accredited 0 MW in every ISO** — the
ledger had no hydro term at all, and `firm_clean_mw` (summed over
`_FIRM_CLEAN_FUELS=("hydro",)` on the persistent fleet) is structurally 0.

That is a **ledger-structure exclusion**, not an accreditation-basis mismatch,
which is why FF-2B could not close CAISO/NYISO by fixing their requirement
bases and routed it here.

## 3. What was built

One new registry and one new resolver; **no gate, no `ScenarioConfig` field, no
free parameter** — the same shape as FF-2B's `_firm_import_mw`, which is also
an ungated ledger-composition fix.

- `config/capacity_market.py::HYDRO_ACCREDITATION_CREDIT_BY_ISO` — one published
  accreditation factor per ISO, each with its primary source (§4).
- `adequacy.py::resolve_hydro_capacity_credit(iso)` — the single resolver
  (rule 19); ISOs absent from the registry fall back to the generic published
  class derate `RENEWABLE_CAPACITY_CREDIT["hydro"] = 0.50`, the same neutral
  fallback every unpublished class already takes (rule 25 — never another ISO's
  factor).
- `adequacy.py::modelled_hydro_nameplate_mw(iso, year)` — the accreditation
  **basis** is the model's OWN dispatched hydro fleet: it reproduces exactly the
  plant population `build_hydro_fleet` puts in the LP (EIA-923-reporting
  conventional-hydro plants, prime mover `HY`, resolving to a model zone, with
  positive MW envelope and positive energy) and sums their MW envelope. `year`
  is clamped to `EIA923_LATEST_FINAL_VINTAGE`, exactly as the forecast hydro
  path clamps its budget shape year, so a forecast year can never accredit a
  partial early-release census. Cached per `(iso, year)`; a missing budget
  credits **0.0** and logs — a missing input can never fabricate accredited MW.
- `adequacy.py::_hydro_firm_mw(fleet, iso, year)` — nameplate × credit, with the
  `_firm_import_mw` no-double-count discipline: any hydro nameplate that *is*
  in the persistent fleet (structurally none today) is netted off the pool so
  the existing fleet loop and the pool can never both credit it. `iso=None` is
  byte-identical legacy behaviour.
- `capacity_reserve_position` threads its solve year into the ledger.

**Tests.** `tests/unit/model/test_hydro_accreditation.py` is the FR-26 test the
audit named as exactly-missing ("none asserts which fuels enter the accredited
ledger"): hermetic fixtures assert the ledger's full composition (thermal UCAP +
wind/solar credits + storage + firm imports + hydro), the loader's three plant
filters, the no-double-count path, the `iso=None` byte-identity, the published
credits, the generic fallback for unpublished ISOs, and the FF-2B gap magnitudes
entering at their published credits. `tests/helpers.no_hydro_accreditation()`
keeps the pre-existing hand-computed ledger-arithmetic tests hermetic.

**Full suite:** 85 failures on `origin/main`, the **same 85** after the change —
byte-identical failure sets, no regressions. (Those 85 are pre-existing and out
of this lane's scope.)

## 4. Citations table

Every ISO's published RA construction splits hydro into a **controllable /
reservoir** class and a **limited-control / run-of-river / non-dispatchable**
class, at materially different factors. The model carries **no per-plant RA
class assignment** for its hydro fleet (the ORNL-EHA `hydro-plant-modes`
classifier behind `hydro_ror_split` is a curated CLEAN partition, absent from a
default raw-path run and reviewed only for some ISOs), so the registry takes the
**LOWER published class factor**. That is deliberate and conservative in the
only direction that matters for an adequacy ledger: it can never manufacture
firm MW the ISO would not count, so every number above is a **floor** on the
published credit, not a fit.

| ISO | credit | published class used | same-table controllable class | source |
|---|---|---|---|---|
| **CAISO** | **0.7041** | "Non-dispatchable Hydro" NQC technology factor, **September** = the minimum over CAISO's Jul/Aug/Sep peak-risk months (Jul 0.7252 / Aug 0.7084 / Sep 0.7041), so the credit holds whichever month the annual peak lands in (the model's own CAISO peak is Aug in 2023/2025, Sep in 2024) | dispatchable hydro QC = the most recent maximum-capability (Pmax) test = **1.00** | CPUC/CAISO *Final Net Qualifying Capacity Report for Compliance Year 2025*, "2025 Tech Factors" tab (3-year 2021–2023 average, as published). Methodology: CPUC *2023 Resource Adequacy Report* §5; adopted QC Methodology Manual, D.10-06-036 App. B §§7,10 |
| **NYISO** | **0.3844** | CARC "Limited Control Run of River", Rest-of-State (G-J/GHI 41.44 %; class absent in NYC/LI) | "Large Hydro" **100.00 %**, "Large Hydro with partial Pump Storage" **100.00 %** | NYISO *2025-2026 Final Capacity Accreditation Factors and Peak Load Window*, ICAPWG/MIWG 2025-02-04 (slide 5 table; confirmed on the slide-7 Set-2 comparison) |
| **MISO** | **0.62** | "Run-of-River Hydro", **Summer** column, % of ICAP (Fall 52 %, Winter 58 %, Spring 63 %) | "Reservoir Hydro" **89 %** Summer | MISO *Planning Year 2025-2026 Indicative Direct Loss of Load (DLOL) Results*, "Indicative Resource Class-level UCAP (DLOL)" table |
| **PJM** | **0.38** | ELCC class "Hydro Intermittent", 38 % at 519 MW installed (2026/27 BRA official/final) | "Hydro with Non-Pumped Storage" 96 % (predecessor Dec-2021 ELCC report) | `data/raw/capacity-market/elcc/pjm/pjm.csv` — the committed P-0B/N6 intake row; PJM 2026/27 BRA final ELCC class ratings (2025 PJM ELCC/RRS Table 24 p.42, Table 5 p.16-17) |
| **NEISO** | *(absent)* → 0.50 | — | — | **No ISO-published hydro class factor located this session.** ISO-NE's FCM qualifies hydro at Seasonal Claimed Capability with intermittent hydro on a per-resource median-output construction; no published class rating exists to digitize. Falls back to the generic `RENEWABLE_CAPACITY_CREDIT["hydro"] = 0.50`. **Open item.** |
| **ERCOT** | *(absent)* → 0.50 | — | — | **No published accreditation product** — ERCOT is energy-only. Falls back to the generic 0.50. Effect is confined to the ledger's reported reserve margin (ERCOT's reliability floor is skipped by market design and its backstop is off). **Open item.** |

`docs/parameter-citations.md` / `frontend/data/parameters.json` carry the four
published credits with full source, page/table and URL, in this PR.

MISO single-document arithmetic, recorded for the routed refinement and **not
adopted**: the companion *Indicative PRMR (DLOL)* table publishes Summer class
UCAP of 1,846 MW reservoir / 721 MW run-of-river, implying ICAP 2,074 / 1,163 MW
and an MW-weighted fleet credit of **0.793**. It is not used because the model
cannot assign its own plants to the two classes.

## 5. Findings (residuals are findings, not things to fix)

**F-1 — The FF-2B gap magnitudes are stale, and by a factor of ~2 (CAISO/NYISO)
to ~63 (NEISO).** FF-2B measured the dispatched-but-unaccredited hydro at
CAISO 3,601 / NYISO 3,343 / NEISO 30 MW. Those were taken when the hydro budget
resolved to the **2025 EIA-923 early release** — a monthly-survey-only partial
census (NYISO 3 of 147 plants, NEISO 5 of 166, CAISO 26 of 160). At HEAD the
forecast path clamps its shape year to `EIA923_LATEST_FINAL_VINTAGE = 2024`, a
complete final-release census, so the real modelled hydro nameplate is:

| ISO | CAISO | NYISO | MISO | PJM | NEISO | ERCOT |
|---|---|---|---|---|---|---|
| modelled hydro nameplate (2024 final census) | 6,568.4 | 4,587.1 | 2,371.5 | 3,300.7 | 1,899.5 | 546.3 MW |
| the FF-2B figure (2025 early release) | 3,916 | 3,343 | — | — | 30 | — |

Reproducing NYISO 3,343 and NEISO 30 exactly off the 2025 partial census is what
identifies the cause. **Any future citation of the FF-2B magnitudes should use
the table above instead.** (The energy-budget *level* channel — miso-110's
`forecast_monthly_hydro` mode B→BF fix, PJM forward level 15.875→9.254 TWh — is
orthogonal to this accreditation term and was neither re-diagnosed nor touched.)

**F-2 — NYISO I7 is 36 MW from PASS and that residual is NOT worth a
parameter.** −1,799 → −36 MW is 98.0 % of the gap, and the remaining 36 MW is
0.11 % of the requirement. FF-2B's other NYISO candidate — ICAP Special Case
Resources / demand response — remains a real uncounted-supply item with no
located primary NYCA UCAP figure, and is the honest next step if NYISO is to
clear; it is **not** taken here (rules 5/24). Note also that the conservative
class choice (§4) means NYISO's own published ledger would credit its Large
Hydro at 100 %, so the true published credit is *above* 0.3844 — the class-split
refinement (F-4) would close this residual on published values alone.

**F-3 — CAISO's and MISO's residuals are NOT hydro.** CAISO's −6,577 MW is the
stack FF-2B §4 already routed elsewhere: peak currency (the model's 2026 peak
49,831 MW vs the CEC 1-in-2 ~46 GW, ≈4.4 GW of requirement inflation → FF-1C
demand lane) and published VRE/storage ELCC (CR-3.1). MISO's −6,037 MW is
un-decomposed by this lane; its I12 reserve margin moves 4.1 % → 5.3 % against a
[10 %, 25 %] band, so the shortfall is broad, not a single omitted class. Both
are recorded here and closed by nothing.

**F-4 — The per-plant reservoir/run-of-river class split is the single largest
remaining published headroom, and it is an INTAKE, not a parameter.** Applying
each ISO's controllable-class factor to the plants that qualify would move
CAISO toward 1.00, NYISO toward 1.00 and MISO toward 0.89 on the reservoir share
of their fleets — on published numbers, with no new degrees of freedom. It needs
a published plant→class mapping (NYISO's Final CARC list, MISO's resource-class
registration, CAISO's dispatchable/non-dispatchable NQC classification) crosswalked
to EIA plant ids: a data-intake lane (WP), not something to approximate here.
The ORNL-EHA `hydro-plant-modes` classifier already in the repo is the *shape*
of the answer but is a CLEAN partition (absent by default) and is curated for
CAISO only, so it cannot carry a default-on ledger term today.

**F-5 — `runner.py:2458` `firm_clean_mw` still reports 0.0, and that is now a
display seam only.** It sums `_FIRM_CLEAN_FUELS=("hydro",)` over the persistent
fleet, which never contains hydro. The accredited ledger itself is now correct
(the I7 numbers above are from `reserve_margin`, which reads
`accredited_firm_capacity_mw`), but the reported `firm_clean_mw` remains
structurally zero and will mislead the next reader of an `evolution_*.json`.
**Flagged for FFR-3B**, which owns `runner.py` this wave; deliberately untouched
here per the lane's file ownership.

**F-6 — The four ledger call sites cannot pass a solve year.** `runner.py:2428`,
`evolve.py:633` and `retirements.py:1065` are owned by other Wave-1 lanes, so
they call `accredited_firm_capacity_mw` without `year` and the hydro census
resolves at `EIA923_LATEST_FINAL_VINTAGE`. For the forecast path this is exactly
right (the clamp applies anyway). For a **backcast** of 2023 it means the 2024
census is used rather than 2023's — a ≤2 % nameplate difference (CAISO 6,432.7
vs 6,568.4; NYISO 4,647.5 vs 4,587.1) with no scored consequence today, since
the accredited ledger drives only forecast-mode capacity screens. Threading the
year from the runner rides **FFR-3B** with F-5.

**F-7 — Environment note for the next session.** `data/clean` is gitignored and
absent from a fresh checkout, so a forecast run refuses to start until
`PYTHONPATH=. python scripts/data/curate_confirmed_retirements.py` has been run
(NYISO legitimately writes no partition — zero researched rows — and degrades to
a logged warning). This cost the first two probe invocations.

## 6. Registered runs (forecast namespace, `frontend/data/hindcast/`)

`scripts/register_forecast_run.py --summary … --kind adequacy` — never the
backcast registry (rule 15 / plan §7.5).

| run id | ISO | arm |
|---|---|---|
| `caiso-2026-2026-ffr1c-i7-before` / `-after` | CAISO | pre/post |
| `miso-2026-2026-ffr1c-i7-before` / `-after` | MISO | pre/post |
| `nyiso-2026-2026-ffr1c-i7-before` / `-after` | NYISO | pre/post |

All six carry `meta.lane = "FFR-1C"` and `meta.arm`. I1–I6, I8–I11, I13–I14 PASS
in every run; I7 FAIL and I12 WARN as tabulated in §1.

## 7. Mechanism matrix (rule 28)

New row `hydro_accreditation` (category `capacity`), cells `OKOKKO`: **K** for
the three ISOs probed here (CAISO, MISO, NYISO), **O** for ERCOT/PJM/NEISO —
the term is armed there too but unprobed this session, and verdicts never
transfer across ISOs (rule 25). The stale `elcc_accreditation` note claiming
"I7/A2 hydro excluded from accredited firm capacity" is corrected to point at
the new row. `scripts/check_mechanism_matrix.py`: integrity OK (the two ERCOT /
CAISO keeper-stamp warnings are pre-existing on `origin/main` and belong to
those promoting sessions).
