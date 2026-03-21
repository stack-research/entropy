"""Tests for Self-Entropy portability helpers."""

from modules.selfentropy import normalize_rss_bytes


class TestSelfEntropyHelpers:

    def test_normalize_rss_bytes_on_macos(self):
        assert normalize_rss_bytes(4096, 'darwin') == 4096

    def test_normalize_rss_bytes_on_linux(self):
        assert normalize_rss_bytes(4096, 'linux') == 4096 * 1024

    def test_normalize_rss_bytes_handles_zero(self):
        assert normalize_rss_bytes(0, 'linux') == 0
