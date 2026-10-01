# FINDING nyiso-160 — Leg 2 (the MyNYISO AORR intake) STOPPED WITH CAUSE at access; the winter face is now identification-blocked on both legs; the keeper's HEAD-replay touchpoint-prep audit run in its place

**Session:** nyiso-160, 2026-08-30. **Keeper under audit:**
`2026-08-30-nyiso-159-loss-surface` (bundle
`results/calibration/nyiso159_lossarm_B`; determination NOT-YET on
{C3a-2025 −11.5 %, C3c}). Freeze ACTIVE; every solve year ∈ {2023, 2024,
2025}; no `--holdout-authorized` (NYISO holds no `complete` marker — Q5-W).
Machine-readable audit record: `results/calibration/_nyiso160_tpaudit.json`.

---

## §1 — Leg 2 stops with cause: the owner cannot produce the AORR files

The handoff's Step 1 executed as written. The MyNYISO artifacts the Leg-2
charter requires (`docs/INTAKE-SPEC-nyiso156-winter-locational-2026-08-30.md`
§2: the current-vintage AORR table — all Con Edison and LIPA rows, esp. the
successors of Table B.4 LRR 1–3, ARR 37, ARR 66, ARR 28 — any
Manual-12-linked replacement tables for the former Appendix B, and the
effective-date/versioning page covering 2023–2025) had **not landed in
`data/raw`** (verified: no AORR/MyNYISO artifact anywhere in the tree or the
history; the only "AORR" hit is the nyiso-156b spec-filing commit itself).
Asked in-session, the owner answered: **"Cannot produce them"** (no MyNYISO
access).

**Consequence, per the spec and the handoff, applied without improvisation:**

* **The leg closes with cause at ACCESS — the same wall at which nyiso-97's
  authorization variant stopped** (stop-if-walled). The nyiso-97 §4
  identifiability gate never ran, because its input never existed: the gate
  is an on-receipt content test, and nothing was received. There is no gate
  verdict to file; this stop record is what stands in its place.
* **No substitute winter mechanism is invented.** nyiso-158 §1.4 measured
  that NO admissible driver reaches the winter face (the sharpened iroquois
  re-open bar is unreachable by any measured driver — it describes a
  model-overshoot regime, not a real one), and the spec's §2 re-open bar
  (nyiso-97 §5, restated verbatim as binding) forbids inferring the
  requirement from conduct, BPCG uplift, LBMP, or the residual. Both stand
  untouched.
* **The winter face of C3a-2025 is now identification-blocked on both legs:**
  Leg 1 executed and promoted at nyiso-157 (P3 stood — the seam alone was
  never predicted to close 2025), its companion chain closed on measurement
  at nyiso-158, and Leg 2 is closed at access by this record. The face stays
  OPEN as a diagnosed, unclosed identification gap; the summer face stays the
  ledgered model-class C3c. The determination consequence is nothing new: the
  keeper already reads NOT-YET on exactly {C3a-2025, C3c}.
* **Re-open conditions are the nyiso-97 set, unchanged and satisfiable:**
  NYISO/NYSRC restores a public AORR posting at current vintage carrying
  actual pocket parameters; a FERC/PSC docket publishes the as-enforced
  pocket MW requirements and eligible unit sets; or the owner supplies
  authorized access to the walled table AND its rows carry derivable
  parameters (the §2 gate then runs first, fail-closed, before any
  mechanism prereg). Nothing short of one of these re-opens the lane.

**Matrix consequence:** no mechanism was tested — no cell verdict moves. The
§5.5 queue prose carries a dated annotation recording the Leg-2 stop (this
finding is its citation), so no future session re-opens the lane against a
wall the record already names.

## §2 — What ran instead: the touchpoint-prep audit (the handoff's designated fallback)

With Leg 2 stopped, the session's fallback duty is to verify the keeper
recipe replays at HEAD and close any drift — the preparation half of the
touchpoint discipline (rule 22: a future validation-year spend must find the
keeper config frozen, reproducible, and with nothing left to prepare;
NYISO's validation authorization lapsed with the Q5-W marker withdrawal, so
this is preparation only, spending nothing).

**Method.** Zero-delta replay of the keeper bundle's recorded recipe at HEAD
(`scripts/replay_keeper.py results/calibration/nyiso159_lossarm_B --out-dir
results/calibration/nyiso160_tpaudit_replay`, years 2023 2024 2025,
sequential within the single invocation per rule 12; no `--set`). The audit
probe (`scripts/probes/_nyiso160_tpaudit.py`, the nyiso-155/157/159
committed-bytes readers) then compares the replay against the committed
keeper bundle on three legs:

* **A1 replay identity** — max abs divergence per year on every hourly
  sidecar value column the slim bundle carries (`system` price / slack /
  dump / demand / reserve_price; `class_hourly` MW; `reserve_family` dual /
  requirement / held / shortfall; `storage` charge / discharge).
* **A2 scorecard reproduction** — replay C3a per year on the committed-anchor
  basis vs the keeper's committed C3a (±0.2 pp, the K6 class).
* **A3 recipe identity** — the recorded config surface diffed key-by-key
  (volatile provenance keys excluded); a zero-delta replay must show zero
  differing levers.

**Environment note (part of the audit's point):** the replay required the
disposable `data/clean` tree to be regenerated from raw
(`scripts/regenerate_clean.py`) before the recipe would run at all — the
capacity-deliverability and nyiso-interface-flows partitions fail loudly
when absent (both mechanisms correctly refuse to silently no-op). That is
the clean-tree contract working as designed, not drift.

## §3 — Audit verdict: THE KEEPER REPLAYS IDENTICALLY AT HEAD — no drift to close

Record: `results/calibration/_nyiso160_tpaudit.json`. The replay solved at
the branch head `cda9b18` (= main `74775c4` + this session's records commit;
no solve-affecting file differs from main).

* **A1 — bit-identical in every scored object, all three years.** Max abs
  divergence replay-vs-keeper is **0.0** on every value column of every
  hourly sidecar: zonal `price` / `slack` / `dump` / `demand` /
  `reserve_price` (52,560 rows/yr), per-class `mw`, reserve-family `dual` /
  `requirement_mw` / `held_mw` / `shortfall_mw`, and storage `charge_mw` /
  `discharge_mw`. Max zonal |Δprice| = 0.0 in 2023, 2024 and 2025 — the
  same zero distance the nyiso-159 K5/K6 legs measured, now re-established
  at the current head.
* **A2 — the scorecard reproduces to the recorded digit.** Replay C3a on the
  committed-anchor basis: **+2.35 / −1.21 / −11.48 %** vs the keeper's
  committed +2.35 / −1.21 / −11.48 (Δ = 0.00 pp everywhere; identical
  load-weighted λ to 4 dp: 33.0071 / 37.6598 / 58.8071).
* **A3 — zero differing levers.** The recorded config surfaces diff empty
  after the fail-closed schema-growth adjudication: the only two differing
  keys (`entry_forward_reserve_leg`, `ercot_offer_surface_cleared_share_rt_room`)
  are ScenarioConfig fields REGISTERED AFTER the keeper's recipe was
  recorded (the latter by ercot-242, merged at the same head), absent from
  the keeper's surface and recorded in the replay at their registered
  default `False` — rule-24 surface widening, with the A1 bit-identity
  independently proving both inert on this recipe. No lever moved.
* **Legitimacy diagnostics** regenerate gate-identical to the keeper's
  committed artifact (every D-gate equal; the only content difference is
  the bundle-name string inside D9 row labels). The generation-time
  module warning on the replayed bundle is the identical state the
  keeper's own committed diagnostics carry — C8 scores PASS from contents,
  as the keeper's determination records.

**Verdict: no G1-class drift exists at this head** (contrast nyiso-155 §4,
where the then-keeper did not reproduce bit-identically and 2023/2024
reshuffled). The touchpoint-prep condition — the keeper recipe frozen,
reproducible at HEAD, nothing left to prepare — is SATISFIED as of this
audit. Should NYISO's validation authorization be re-granted (a new owner
`complete` declaration once the keeper scores CALIBRATED — Q5-W's stated
re-entry route), the recipe replays as-committed with no repair step.

## §4 — What this session did NOT do

No mechanism armed, disarmed, re-scoped or re-tuned (the loss-surface derive
stays frozen, rule 23); no C3c lever (the ledgered queue stays closed); no
holdout year touched; no re-open of the refuted routes (Tier-3 TTC
re-grounding, the F/G split, the bare Zone-K swap, the fuel-side iroquois
flag alone); keeper and determination unchanged. The replay run is
registered on the dashboard (rule 15) as an audit probe, never a keeper
candidate.
