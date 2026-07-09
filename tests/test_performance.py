"""
Performance tests
==================
These are not micro-benchmarks; thresholds are deliberately generous so
they don't flake on slower/shared CI runners. Their job is to catch
gross regressions (e.g. an accidental O(n^2) loop, a hung retry) rather
than to track fine-grained performance.
All tests made by DevX-Dragon and some helpers!
"""
from __future__ import annotations

import time

import pytest

import betterqr


class TestGenerationSpeed:
    def test_single_standard_qr_is_fast(self):
        start = time.perf_counter()
        betterqr.QR("https://example.com").to_buffer("PNG")
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"single QR generation took {elapsed:.3f}s"

    def test_large_payload_is_reasonably_fast(self):
        data = "A" * 2000  # forces a high-version symbol
        start = time.perf_counter()
        betterqr.QR(data, ecc="L").to_buffer("PNG")
        elapsed = time.perf_counter() - start
        assert elapsed < 3.0, f"large-payload QR generation took {elapsed:.3f}s"

    def test_micro_qr_is_fast(self):
        start = time.perf_counter()
        betterqr.QR("HI", qr_type="micro", ecc="L").to_buffer("PNG")
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"Micro QR generation took {elapsed:.3f}s"

    def test_svg_generation_is_fast(self):
        start = time.perf_counter()
        betterqr.QR("svg speed test").to_buffer("SVG")
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"SVG generation took {elapsed:.3f}s"


class TestBatchThroughput:
    def test_batch_of_50_completes_quickly(self, tmp_path):
        items = [f"item-{i}" for i in range(50)]
        start = time.perf_counter()
        betterqr.batch(items, output_dir=str(tmp_path))
        elapsed = time.perf_counter() - start
        avg = elapsed / len(items)
        assert elapsed < 15.0, f"batch of 50 took {elapsed:.3f}s ({avg:.3f}s/code)"

    def test_repeated_generation_has_no_major_slowdown(self):
        # Generate in two equal-size batches and make sure the second
        # isn't dramatically slower than the first (would flag leaks or
        # unbounded caches growing with each call).
        def batch_time(n):
            start = time.perf_counter()
            for i in range(n):
                betterqr.QR(f"repeat-{i}").to_buffer("PNG")
            return time.perf_counter() - start

        first = batch_time(20)
        second = batch_time(20)
        assert second < first * 3 + 0.5, (
            f"second batch ({second:.3f}s) much slower than first ({first:.3f}s)"
        )


class TestAnimationPerformance:
    def test_gif_animation_completes(self, tmp_path):
        f = str(tmp_path / "perf.gif")
        start = time.perf_counter()
        qr = betterqr.QR("animation speed test")
        qr.animate(effect="shimmer", frames=10, fps=10).save(f)
        elapsed = time.perf_counter() - start
        assert elapsed < 10.0, f"10-frame GIF animation took {elapsed:.3f}s"
