# Changelog

All notable changes to BetterQR will be documented in this file.

## [2.0.0] - To be officialy released

### Breaking changes
- `WiFi`/`VCard`/`MeCard`/`SMS`/etc. now use the correctly-validated, correctly-escaped implementation instead of the (buggy, silently-shadowed) duplicate. In practice this means: WEP passwords are now validated against real key-length rules and will raise `ValueError` if invalid where they previously wouldn't; SSIDs/passwords containing `;`, `,`, or `\` now escape those characters in the output string rather than emitting a malformed `WIFI:` string. No public class or function names changed.
- `QR(data, qr_type=...)` now validates `qr_type` against `("standard", "micro")` and raises `ValueError` for anything else. `qr_type="rmqr"` previously crashed with an unrelated `TypeError` deep in the encoder rather than failing cleanly, so no code that worked before should be affected — but code that was catching the old crash specifically will need to catch `ValueError` instead.

### Fixed — critical
- **Every standard QR code at versions 30-40 and ECC level M could silently corrupt or fail to decode** once the payload was large enough to use the block sizes affected. The internal Reed-Solomon block table had 11 incorrect entries (per-block data codeword counts were 2 short in each of the two block groups, e.g. version 30-M listed `(19,45),(10,46)` instead of the correct `(19,47),(10,48)`). Small payloads at these versions never hit the bug, which is why it went undetected until an exhaustive near-max-capacity sweep was run and cross-checked against `segno`'s tables. All 160 version/ECC-level combinations are now verified to match the ISO/IEC 18004:2015 reference tables exactly, and a table-consistency test now runs on every CI build so a bug like this can never land silently again.
- Micro QR versions M1 and M3 could silently truncate data near their capacity limit — the final data codeword in those symbols is a 4-bit nibble, not a full byte, and the capacity check didn't account for that.
- `.logo()` raised `KeyError` on every call (an internal dict key mismatch between the styling layer and the matrix renderer).
- Duplicate `WiFi`/`VCard`/`MeCard`/`SMS`/etc. class definitions meant the *less* correct implementation silently shadowed the properly-escaped one — special characters (`;`, `,`, `\`) in a WiFi SSID or password produced malformed, unscannable strings.
- The WEP password validator itself was wrong (required hexadecimal characters at ASCII-length values, rejecting virtually every real-world WEP key).
- Styled Micro QR codes (custom module shape / finder color) incorrectly painted phantom "finder" styling near the top-right and bottom-left corners, which don't exist in Micro QR's single-finder layout.
- Terminal `compact` render style had asymmetric padding and a stray extra row.
- `qr_type="rmqr"` was reachable from the public API but the implementation was incomplete and crashed; it's now explicitly rejected with a clear error instead.

### Added
- PDF and EPS output formats.
- Kanji mode (standard QR only) — Shift-JIS-encodable text now uses 13 bits/character instead of being encoded as UTF-8 bytes.
- ECI (UTF-8) declaration for non-ASCII byte-mode payloads (standard QR only), for stricter spec compliance with non-Latin text.
- Structured Append (`betterqr.structured_append()`) — split a message across up to 16 linked QR symbols, standard QR only.
- `betterqr.save(data, path, **style)` one-liner convenience function.
- `py.typed` marker for type-checker support.
- `LogoECCWarning` — adding a logo now visibly warns when it silently raises the ECC level to H, instead of doing so quietly.

### Changed — performance
- PNG generation for the common case (plain square modules, solid fill color) now builds the image directly in indexed/palette mode instead of full RGBA with per-module `ImageDraw` calls — roughly 40% faster end to end for typical QR codes, with a much bigger win on the encode step specifically.
- Removed PNG `optimize=True` from the default render path — it roughly doubled encode time for a ~10% file-size reduction on these simple, highly-repetitive images.
- Mask-pattern grids are now cached (they only depend on symbol size and mask index, never on the actual data), so generating many QR codes at the same version — a common batch/server workload — no longer re-derives the same mask arithmetic every time.
- Rewrote the mask-penalty "Rule 3" pattern check to use an integer rolling window instead of slicing a fresh list at every position.
- SVG output for plain square modules now uses integer path coordinates instead of floating-point formatting where the geometry is always whole-pixel.
- See `benchmark.py` for a reproducible comparison against `segno` and `qrcode`; BetterQR was ~1.6-2x slower than both before this pass and is now roughly on par for small-to-medium payloads, within ~10% for large ones. `segno`'s SVG path is still consistently faster — see README for the honest breakdown.

### Test infrastructure
- Replaced `pyzbar` with `zxing-cpp` for decode verification — `pyzbar`/zbar cannot decode Micro QR at all (confirmed: it returns zero results for *any* valid Micro QR image), so Micro QR had no real regression coverage before this release.
- Split the test suite into focused files: unit tests, generation smoke tests, decode round-trip tests, and performance sanity tests — 172 tests total, up from ~56.
- CI now installs Ghostscript and cairosvg to decode-verify PDF/EPS/SVG output, not just PNG.

## [1.0.0] - 2026-06-11


### Added
- First public release of BetterQR.
- Python API for generating QR codes from text, URLs, and helper payloads.
- CLI entry point for terminal-based QR generation.
- QR payload helpers for Wi-Fi, vCard, MeCard, geo locations, SMS, email, phone, and crypto addresses.
- Styling support for multiple module shapes, custom colors, gradients, finder colors, and quiet zones.
- Logo embedding, decorative frames, and optional text labels.
- Animated QR output with multiple visual effects.
- Support for PNG, JPG/JPEG, SVG, and GIF output formats.
- Batch generation helper for writing multiple QR codes to disk.

### Changed
- Packaging metadata updated for PyPI release.
- Python requirement set to 3.10+.
- Release workflow configured to publish from GitHub Release assets.

### Fixed
- Cleaned up packaging and documentation artifacts before the public release.