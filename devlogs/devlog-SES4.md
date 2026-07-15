# Benchmarking 
This session focuses on benchmarking `BetterQR` with other popular libraries like `segno` and `qrcode`. 

## How it Compares
This is a rough comparison between `BetterQR`, `qrcode`, and `segno`.

| Feature | BetterQR | `qrcode` | `segno` |
| :--- | :---: | :---: | :---: |
| **Micro QR** | ✅ M1–M4 | ❌ | ✅ |
| **Kanji Mode** | ✅ | ❌ | ✅ |
| **Structured Append** | ✅ | ❌ | ✅ |
| **Logo Embedding** | ✅ Built-in | ❌ (Manual PIL) | ❌ (Manual) |
| **Module Shapes** | ✅ 8 Shapes | ⚠️ Limited | ❌ |
| **Gradients** | ✅ | ❌ | ❌ |
| **Animated GIF** | ✅ 10 Effects | ❌ | ❌ |
| **Frames & Labels** | ✅ Built-in | ❌ | ❌ |
| **Structured Data Helpers** *(WiFi, vCard, ...)* | ✅ | ❌ | ⚠️ Via plugin |

`BetterQR`'s primary aim is not to aggressively beat other libraries, but to provide a highly capable, reliable, and user-friendly alternative packed with creative options out of the box. 

---

## Performance Metrics

### Payload Performance Benchmarks (2.0.0-rc)
*All times are in milliseconds (ms). Lower is better.*

| Payload Category | Size / Type | BetterQR | Segno | Standard `qrcode` | BetterQR Status |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **URL** | Tiny / Short | **6.88** | 7.19 | 5.90 | 🟢 **Beats Segno** / Competitive |
| **Medium** | Standard | 22.44 | **21.89** | 20.03 | 🟡 **Ties Segno** (~2.5% diff) |
| **Large** | V40 / Dense | 106.63 | **98.94** | 98.96 | 🔴 Behind by ~8% |
| **Very Large** | Max Capacity | 209.00 | **197.00** | 204.00 | 🟡 Highly Competitive (~6% diff) |
| **SVG (Large)** | Vector | 86.63 | **~0.56** | — | 🟡 Meaningful fix (was 104.66) |
| **SVG (Very Large)**| Vector | 174.19 | **~1.50** | — | 🟡 Meaningful fix (was 211.84) |


## Known Limitations / Project Honesty

To build clear engineering trust, here are the current structural limitations of `BetterQR` compared to older ecosystem veterans:

* **Dependency Overhead:** Depends heavily on `Pillow` for its extensive visual layouts and shapes, unlike `segno`, which is zero-dependency.
* **Large Matrix Vectorization:** Pure PNG generation lags behind by ~6-8% on maximum matrix dimensions (like V40) due to mask scoring loops running entirely in pure Python.
* **Vector Vectorization Limits:** While our SVG generation times dropped significantly in the latest release, pure string-building layout engines like `segno` still massively outperform us on massive vector layouts.
* **Format Boundaries:** The legacy `EPS` writer does not support logo embedding. 
* **Spec Edge Cases:** Kanji mode and Structured Append are fully validated for standard QR codes, but are not yet implemented for Micro QR variants. `rMQR` (Rectangular Micro QR) is currently unsupported.

---
