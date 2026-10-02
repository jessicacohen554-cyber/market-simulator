# FINDING soco-101 — forward heat rate for the SOCO seams (2026-10-02)

Lane soco-101, zero LP, no solve. Implements the owner ruling recorded in
`FINDING-soco-100-fpl-tal-lambda-basis-2026-10-02.md` §7: the forward heat rate
for the SOCO seams is the **seam-own flat mean of the registered `hr_by_year`
cells** — not the FINDING-soco-98 §3 elasticity fits, not the 11.6 flat.

## 1. Owner card (answered in session)

*Where should the forward value live?* — **Separate field** (recommended option):
a new `NeighborInterface.forward_heat_rate`; `marginal_heat_rate` (11.6 / 9.63)
is untouched and stays the structural fallback. No open question remains.

## 2. What changed

| Piece | Change |
|---|---|
| `model/interchange/spec.py` | `NeighborInterface.forward_heat_rate: float \| None = None` (compare=False, like `hr_by_year`); set on the seven SOCO seams with cells |
| `data/neighbor_price.py::neighbor_heat_rate` | step 3 (no elastic fit): `forward_heat_rate` when registered, else `marginal_heat_rate`. Backcast-tabulated years still return their cell (step 1 untouched) |
| `scripts/data/derive_neighbor_forward_hr.py` | the producer: equal-weight mean of each seam's cells at the cells' 2-dp precision, scoped to `FORWARD_HR_ISOS = {"SOCO"}` (an ISO without a ruling raises) |
| `tests/iso/soco/test_soco_lambda_anchors.py` | registry == producer output; backcast years resolve to their cells; forward years and the `"flat"` forward-skill path resolve to `forward_heat_rate`; SCEG falls to 11.6; no other ISO sets the field |

Produced values (`uv run python scripts/data/derive_neighbor_forward_hr.py --iso SOCO`):

| Seam | Cells | forward_heat_rate | was (flat) |
|---|---|---|---|
| SOCO_TVA | 2019–25 (7) | 9.15 | 11.6 |
| SOCO_MISO | 2019–25 (7) | 9.24 | 9.63 |
| SOCO_DUK | 2019–25 (7) | 10.15 | 11.6 |
| SOCO_SCEG | none | — (keeps 11.6) | 11.6 |
| SOCO_SC | 2019–25 (7) | 12.32 | 11.6 |
| SOCO_FPL | 2019, 2020, 2022–25 (6) | 6.34 | 11.6 |
| SOCO_FPC | 2019–25 (7) | 8.71 | 11.6 |
| SOCO_TAL | 2019–25 (7) | 6.70 | 11.6 |

FPL 6.34 / TAL 6.70 / FPC 8.71 match FINDING-soco-100 §7 exactly.

## 3. Rules

- **Rule 23** — produced, not typed; it moves only when the cells move (i.e. when
  their FERC-714 / MISO-South LMP source data updates and
  `derive_neighbor_hr_by_year.py` re-derives them).
- **Rule 24** — no new `ScenarioConfig` field and no knob: the value is registry
  data in the same `INTERFACE_NEIGHBORS` block as `hr_by_year`, and it acts only
  where the existing `reference_price_interface` / `priced_interchange` switches
  arm the seam. Hence no new mechanism-matrix row; the SOCO
  `reference_price_interface` cell stays **U** with a soco-101 evidence note,
  `priced_interchange` stays **U** untouched.
- **Rule 25** — the field is set on SOCO blocks only (test-asserted); every other
  ISO's seams keep their resolution byte-identical.
- **Rule 13** — the mean of annual-mean anchors is a forward-driver input
  (`(HH + basis) x HR x shape` still moves with the gas trajectory); no hourly
  lambda is ever a seam price.

## 4. G-DRIFT (backcast path)

| Hunk | Class | Reason |
|---|---|---|
| `neighbor_price.py` comment (forward-skill) + docstring | INERT | text |
| `neighbor_heat_rate` new `forward_heat_rate` branch | INERT | reached only for a block with the field set (SOCO only), in a year absent from `hr_by_year` with no elastic fit. SOCO blocks are reached only when `reference_price_interface` / `priced_interchange` is armed for SOCO: neither default ISO set holds SOCO, SOCO has no `IMPORT_ZONE`, and no keeper arms it |
| `NeighborInterface.forward_heat_rate` field | INERT | default `None` reproduces the old resolution for every other block |
| SOCO `forward_heat_rate=` values | INERT | same arming gate as above |

One note for whoever arms the SOCO blocks: **SOCO_FPL 2021** is the one backcast
year with no cell (refused re-filing), so once armed it prices at 6.34 instead of
11.6. That is the ruled behaviour, not drift (the blocks are off today).

Cache keys: `model/interchange/spec.py` is outside the solve-surface fingerprint
(`config/solve_surface.py` scope boundary), and no SOCO run arms the seams, so no
key or bundle moves. No control solve is warranted.

## 5. Tests

`tests/iso/soco/test_soco_lambda_anchors.py` + neighbor-price / SPP / NWPP seam
suites: green. Fast lane: see the PR body.
