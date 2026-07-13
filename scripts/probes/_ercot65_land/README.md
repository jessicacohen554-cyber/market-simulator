# ERCOT-65 session-diff landing blob

`ercot65.patch.xz.b64.part1` is the ERCOT-65 session diff (the
`wind_ptc_vintage_offers` PTC vintage-scoping build: config field +
statutory constants, EIA-860 eligible-share loader, ira dispatch-offer
builder, both orchestrators + forecast runner wiring, unit tests, probe scripts, parameter-registry regen, the wtx recorder-fidelity fix + ercot63 record corrections, and the ERCOT-65 docs (diagnosis §9, calibration-log entry, CLAUDE.md, CHANGELOG, methodology-spec §1.2)) as one `git diff origin/main..HEAD`
patch, xz-9 + base64. The modified files total ~3 MB — past the MCP
relay's single-call ceiling — so the 235 KB patch (49.7 KB b64) rides this blob and the
one-shot `.github/workflows/ercot65-negepoch-land.yml` applies it
sha-gated (sha256
57652cc64a473dd02ee1726f216e7e2142a30c47c6f96a1be980973b98f93864) on the
`claude/ercot-negative-price-epoch-368q8q` branch. Same pattern as
`_ercot64_land/` (the CURRENT template per the ERCOT-65 charter).
