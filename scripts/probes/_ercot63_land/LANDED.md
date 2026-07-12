# ERCOT-63 landing record

- Session patch (code + docs + probes + tests + attestation): sha256
  8ab23ec3063cf60cbaa3b4b4415e3d68d97535fe8ac685b3fadf85feccf14b87,
  applied + solved + registered by `.github/workflows/ercot63-bridge-solve-register.yml`
  (run 29205996200), merged to main via PR #2152.
- Docs-sync patch (CLAUDE.md / model-methodology-spec.md / CHANGELOG.md): sha256
  e0297fc838f89676e172413142afd74b664ebeab27370a3c1638241e2485c5b8,
  applied by `.github/workflows/ercot63-docs-sync.yml` (run 29208412639).
- Registered runs: `2026-07-12-ercot63-gas-bridge` (CALIBRATED-WITH-CAVEATS,
  one ledgered caveat — C3c-2024 inherited byte-identical; C5c-2024
  storage-shape FAIL flips to PASS) + `2026-07-12-ercot63-gas-bridge-ablation`
  (zero-forcing twin, linked). Keeper stays `2026-07-12-ercot59-storage-deploy`
  pending the owner promotion decision (case: calibration-log ERCOT-63 entry).
