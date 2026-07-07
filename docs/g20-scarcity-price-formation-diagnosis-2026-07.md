# G-20 — scarcity price formation: why it is inert in PJM/MISO/CAISO/NYISO

**Date:** 2026-07-07. **Branch:** `claude/scarcity-price-formation-isos-10us34`.
**Scope:** diagnosis only — no re-solve, no keeper change (owner decision, this
session). **Question answered:** *why is scarcity pricing inert in PJM, and is
the same true for CAISO and NYISO?*

**Headline.** G-20 is **not** a "missing or mis-wired scarcity overlay" gap. Every
ISO already has a published, structurally-faithful post-solve scarcity overlay
(ERCOT ORDC, PJM two-step ORDC, NYISO/NEISO RCPF, CAISO LOLP). C3c stays ≈ 0 for
the four capacity-market ISOs because of **two independent layers**, and fixing
the overlay curve fixes neither:

1. **Plumbing (all six ISOs):** C3c scores the *raw energy-only LP dual*, not the
   settlement price the overlay produces — so no overlay, however correct, can
   move the metric today.
2. **Inertness (the four keepers):** even enabled and scored, the overlays sit at
   ~$0 because the perfect-foresight LP is **not tight where the real market is
   short**. The blocker differs by ISO — over-commitment (PJM), missing downstate
   transmission tightness (NYISO), or a non-reserve pricing gap (CAISO).

Lowering a breakpoint, inflating a penalty, or subtracting a headroom offset to
force a fire is forbidden (CLAUDE.md #11) and the PJM prior art already refused
to. None of the four is closable by tuning the overlay.

---

## Layer 1 — the scored series is the raw dual, not the settlement price

C3c ("price tail / scarcity", `scripts/calibration_verdict.py::score_price_tail`,
line 1010) reads the model tail from `ypay["ordc"]["hoursGt200"]["model"]`:

```python
# scripts/render_calibration_html.py:1245
"hoursGt200": {
    "actual":  int(np.nansum(rt  > thr)),
    "model":   int(np.nansum(lam > thr)),    # lam   = raw energy-only dual
    "overlay": int(np.nansum(lam_s > thr)),  # lam_s = lam + scarcity_adder
},
# scripts/calibration_verdict.py:1010
model = float(h.get("model", 0))             # reads .model, never .overlay
```

The overlay-adjusted series (`.overlay`) is computed **for ERCOT display only**
(`render_calibration_html.py:1070`, gated `iso == "ERCOT"`) and the verdict never
reads it. For every other ISO the fallback (`render_calibration_html.py:1271`)
sets `model` from the raw persisted `price` column. And the backcast orchestrator
(`scripts/run_calibration.py`) never calls `scarcity_prices` /
`caiso_scarcity_overlay` / `rcpf_adder` at all — those run only in the *forecast*
capacity-economics path (`runner.py:1394-1511`) or in standalone derivation
scripts that write a side-car `scarcity.parquet` (`derive_*_overlay.py`).

**Consequence:** the scored `model` value is always the raw perfect-foresight dual,
which carries ~no scarcity rent by construction. The overlays are decorative for
C3c. Threshold per ISO (`TAIL_THRESHOLD`): $200 ERCOT/PJM/MISO/CAISO, $300
NYISO/NEISO. The scored basis is the **energy-only LMP**; the real actual it is
compared against is the **settlement price** (LMP + reserve/scarcity adder) — an
apples-to-oranges comparison that structurally guarantees a collapsed tail for
capacity-market ISOs regardless of model quality.

**Owner decision (2026-07-07):** the correct basis is the **settlement price**
(score `lam_s` = LMP + published overlay). The adder is published, structural,
and forward-reproducible (rule-13 admissible), not fitted to residuals — real RT
settlement *is* energy LMP + reserve price (ERCOT RTSPP, PJM SRMCP-into-LMP,
NYISO RCPF-into-LBMP). This plumbing is **necessary but not sufficient**: it lets
the overlays score, but on the four keepers C3c stays ≈ 0 because of Layer 2. The
plumbing build is deferred to a follow-up (not done this session).

---

## Layer 2 — the overlays are inert on these keepers (measured)

The overlays are correct; they stay at ~$0 because the LP's system-wide reserve
never reaches the requirement. The *reason* it never reaches the requirement is
different in each ISO.

| ISO | Overlay shape | Fires? | Measured evidence | Root blocker |
|---|---|---|---|---|
| **PJM** | vertical two-step ($850 < REQ, $300 < REQ+190 ≈ 3.3 GW) | **~0 h** | `pjm-81` per-gen co-opt fired **1 h / 3 yr** (2025-06-23 h19, $46.47 dual). Online reserve ~14 GW vs ~3 GW req even in real-short hours. | **Perfect-foresight over-commitment** keeps ~14 GW synchronized-and-idle. Vertical curve → strictly $0 above REQ. |
| **NYISO** | piecewise-linear RCPF + **locational** stack (NYCA ⊃ East ⊃ SENY ⊃ NYC) | system-wide **0 h**; locational **gated** | NYCA headroom ~4–6 GW (3–4 GW too loose to bind). But in actual >$300 h, **NYC-zone headroom collapses to ~1,000 MW ≈ the NYC 1,000 MW req** while NYCA-wide is still ~5 GW. | Tail is **genuinely locational** (import-constrained NYC/SENY pocket). Directionally correct — blocked on **downstate transmission binding** (interface TTC + Gold-Book load shares) + the #1344 condition-varying-requirement intake. |
| **CAISO** | smooth LOLP (σ=2,500 MW, $2,000 cap) | reserve co-opt **inert** (+$0.47 mean, tail unchanged) | `caiso-59` probe: 2023 **over**-tails 483 h vs 21 h RT; 2024 0 h; 2025 0 h. Adding co-opt leaves the tail at 483 h. | The C3c miss is **not a reserve-scarcity gap** — it's the **evening-merit / RA-commitment-uplift** gap (`FINDING-caiso-evening-merit-2026-07-04`). The smooth overlay is inert on that residual. (G-15 territory.) |
| **MISO** | — (raw dual / co-opt only) | **~0 h** | DA tail is **year-dependent, not uniformly tiny**: 2023 = 1 h (RT's 30-h tail is single-hour 5-minute transients, `miso-scarcity-tail-diagnosis.md` §1), but **2024 = 24 h (Winter Storm Heather) and 2025 = 38 h** — both real C3c FAILs under the rubric's ratio-band gate (actual ≥ 10 h ⇒ model must land in [0.5×,2.0×]; model is 0 h both years). The current keeper (`miso-45-cc-capacity`) registry entry itself records this as an open FAIL. | Same over-commitment family as PJM for the material years; **both admissible remedies already exhausted** — commitment posture built + honesty-gate REJECTED under G-25 (`miso-43`); Midwest locational reserve zone still DATA-BLOCKED (no published requirement series). See G-20e correction below. |

**Evidence sources:** `docs/multi-iso/pjm-reserve-ordc.md` (honesty gate +
Phase-2 re-gates, `pjm-81`); `docs/nyiso-rcpf-overlay.md` §"Finding: the
2023–2025 tail is *locational*"; `docs/calibration-log.md:522-542`
(`caiso-59-reserve-coopt`, "~455h-vs-21h driver → NEGATIVE"); the current
`frontend/data/backcast/status.js` C3c rows (PJM/MISO/NYISO 0 h; CAISO 2023
483 h over-tail on raw duals).

### The unifying root cause

A perfect-foresight energy LP with zero unserved energy holds **far more
system-wide reserve headroom than the real market**. Any reserve-shortage-
triggered mechanism — vertical (PJM), smooth (CAISO), or piecewise-linear
(NYISO) — therefore rarely reaches its requirement at the *system* level. This is
the same wedge as G-22 (ERCOT ~3.2 GW online-capability) and G-25 (P1 carries
+34% committed CC energy vs MIP). Scarcity pricing is inert because the LP is not
tight, **not** because the curve is missing or mis-wired.

### What is *not* the fix

- Not lowering the PJM breakpoint, inflating a penalty, or netting a multi-GW
  headroom offset to manufacture a fire (CLAUDE.md #11; PJM prior art refused).
- Not a fitted price adder tuned to the C3c residual (rule 11/13).
- Not "turning the overlays on in the keepers" — they are inert; the count moves
  0 → 0 (PJM/NYISO-system/CAISO-on-residual) or 0 → over-tail from an unrelated
  gap (CAISO 2023).

---

## Sharpened sub-gaps (supersedes the single G-20 line)

| Sub-gap | ISO | The real blocker | Owning gap / next build |
|---|---|---|---|
| **G-20a** | all six | C3c scores the raw dual, not the settlement price; overlays never reach the scored series | Layer-1 plumbing: score `LMP + published overlay`, wire each ISO's overlay into the scored payload behind its existing flag. Necessary, ISO-agnostic, low-risk. Approved basis; deferred build. |
| **G-20b** | PJM | perfect-foresight over-commitment (online reserve ~14 GW vs ~3 GW) | ~~commitment posture~~ struck (wrong direction). **UNBLOCKED 2026-07-07** (`pjm-87`, `pjm_reserve_pergen_sync`): per-gen ramp limit + online/offline product scoping fires the co-opt (133/44/50 h/yr) in the correct opportunity-cost regime (never crosses $300), but at small magnitude — criterion-identical to the flag-off baseline, not a promotion case. See `docs/gap-register-2026-07.md` G-20/PJM rows. |
| **G-20c** | NYISO | downstate transmission not binding; tail is locational (NYC pocket) | interface-TTC/Gold-Book-load-share audit so downstate peaks, + locational RCPF (`nyiso_rcpf_locational`) + #1344 condition-varying requirement intake. |
| **G-20d** | CAISO | C3c miss is evening-merit / RA-commitment, not reserve scarcity | folded into **G-15** (evening-CT merit / LCR commitment credit). The scarcity overlay is inert here by design. |
| **G-20e** | MISO | over-commitment (2024/25 material FAILs) + Midwest reserve zone unbuilt | **Corrected 2026-07-07** (was: "narrow gap given DA tail ≈ 1 h" — true for 2023 only; 2024=24 h/2025=38 h are real, non-trivial C3c FAILs, confirmed against the current `miso-45` keeper). Both admissible remedies are already exhausted, not open: commitment posture is G-25's lever, built and honesty-gate REJECTED (`miso-43`, postured headroom 3.7–4.2× measured); Midwest locational zone is DATA-BLOCKED (no published zonal requirement series — a hand-sized one is forbidden, rule 11). No new mechanism is admissible under G-20e without duplicating G-25 (rule 18) or fitting an ungrounded requirement (rule 11). Downgraded to **tracked/blocked**, inherits G-25 (posture refinement: deferred min-run/min-down rows on the existing lever) and the open Midwest-requirement-series data ask — not a G-20e-specific build. |

**Disposition:** G-20 stays **open** as a diagnosed cluster. No keeper changed; no
overlay tuned. The honest conclusion is that scarcity price formation is gated on
LP tightness (commitment/topology), not on the scarcity curves — which are built,
cited, and correct.

---

## Addendum 2026-07-07 — G-20e re-verification (no re-solve, no keeper change)

Re-checked G-20e's "narrow gap" framing against the current MISO keeper
(`miso-45-cc-capacity`) and the live dashboard tail data
(`frontend/data/backcast/tail/actual_tail.json`), per the calibration
determination rubric's C3c small-count rule (`docs/calibration-determination-
rubric.md`: actual < 10 h ⇒ `|model − actual| ≤ 10 h`; actual ≥ 10 h ⇒ model
must land in `[0.5×, 2.0×]` of actual):

| year | DA actual (h > $200) | model (h) | rubric gate | result |
|---|---|---|---|---|
| 2023 | 1 | 0 | small-count, \|0−1\|≤10 | **PASS** |
| 2024 | 24 | 0 | ratio band [12, 48] | **FAIL** |
| 2025 | 38 | 0 | ratio band [19, 76] | **FAIL** |

So the original claim ("narrow gap given DA tail ≈ 1 h") only holds for 2023;
2024 and 2025 are genuine, material C3c FAILs — matching what the `miso-45`
registry entry (`frontend/data/backcast/registry/2026-07-07-miso-45-cc-
capacity.json`) already discloses as an open FAIL, and what `docs/gap-
register-2026-07.md`'s MISO row (line 351) already tracks under "scarcity
posture (G-20/G-25)".

**No new structural work follows from this correction.** Both routes the
task brief asked to evaluate are already closed out, not open:

1. **Midwest locational reserve zone** (would let the zonal co-opt bind
   where 2024's Winter Storm Heather event was Midwest-wide, not
   MISO-South): still **DATA-BLOCKED** — `docs/multi-iso/miso-scarcity-
   posture-design-2026-07.md` §B and `docs/calibration-log.md:7059` record
   the open ask (a published/measured Midwest zonal *requirement* series;
   the intaken `data/raw/MISO-AS` series has cleared MW/MCPs but not the
   requirement basis). No such series has landed since. A hand-sized
   requirement would be a rule-11 fitted input, not admissible.
2. **Commitment posture** (the LP holding too much reserve online): this is
   **G-25's** lever (`miso_commitment_posture`, `config/reserve_config.py`),
   already built with zero fitted parameters and already probed full-span
   (`miso-43-commitment-posture`, 2026-07-06) — its own pre-committed
   honesty gate **rejected** it (postured online headroom 9.9–11.1 GW vs
   measured cleared reserve 2.5–2.7 GW, 3.7–4.2× too loose; C3c tail stayed
   0 h ×3). Building a second posture mechanism under G-20e would violate
   rule 18 (one mechanism per phenomenon); G-25 already owns the honest
   rejection and its own named follow-up (deferred min-run/min-down
   rolling-window rows on the same lever, blocked on G-40 memory headroom).

**Conclusion:** G-20e is downgraded from an open build item to
**tracked/blocked** — a real (if narrow-scope) 2-of-3-year gap whose only
admissible next moves are outside this gap's ownership (G-25's posture
refinement) or outside this session's control (the Midwest requirement-series
data ask). No code change, no re-solve, no keeper touched this session.
