"""Unit tests for the HYDRA CLI runner (hydra.py)."""

import json
import socket
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import hydra  # noqa: E402
from adapters.coupang.coupang_adapter import CoupangAdapter  # noqa: E402
from runtime.hydra_pipeline import HydraPipeline  # noqa: E402

AFFILIATE_URL = "https://link.coupang.com/a/example"
DIRECT_URL = "https://www.coupang.com/vp/products/123456789"
PRODUCT_HTML = (REPO_ROOT / "tests" / "fixtures" / "coupang_product_sample.html").read_text(
    encoding="utf-8"
)


class _FakeResponse:
    def __init__(self):
        self.status_code = 200
        self.url = DIRECT_URL
        self.text = PRODUCT_HTML
        self.headers = {"Content-Type": "text/html; charset=utf-8"}


class _FakeSession:
    def get(self, url, headers=None, timeout=None, allow_redirects=None):
        return _FakeResponse()


def _fake_pipeline():
    """A real HydraPipeline whose adapter HTTP is mocked — no real network."""
    return HydraPipeline(adapter=CoupangAdapter(http_client=_FakeSession()))


class _FailingPipeline:
    def run(self, url):
        raise RuntimeError("pipeline boom")


def test_affiliate_url_accepted(capsys):
    assert hydra.main([AFFILIATE_URL], pipeline=_fake_pipeline()) == 0
    out = capsys.readouterr().out
    assert json.loads(out)  # valid JSON


def test_direct_coupang_url_accepted(capsys):
    assert hydra.main([DIRECT_URL], pipeline=_fake_pipeline()) == 0
    assert json.loads(capsys.readouterr().out)


def test_missing_url_rejected(capsys):
    code = hydra.main([])
    assert code != 0
    assert capsys.readouterr().err  # argparse message on stderr


def test_extra_positional_argument_rejected(capsys):
    code = hydra.main([AFFILIATE_URL, DIRECT_URL])
    assert code != 0
    assert capsys.readouterr().err


def test_invalid_marketplace_url_rejected(capsys):
    code = hydra.main(["https://www.amazon.com/dp/B000000000"])
    assert code != 0
    captured = capsys.readouterr()
    assert captured.out == ""  # nothing printed to stdout on failure
    assert "error" in captured.err.lower()


def test_successful_output_is_valid_json(capsys):
    hydra.main([DIRECT_URL], pipeline=_fake_pipeline())
    parsed = json.loads(capsys.readouterr().out)
    assert isinstance(parsed, dict)


def test_output_matches_render_prompt_contract(capsys):
    hydra.main([DIRECT_URL], pipeline=_fake_pipeline())
    parsed = json.loads(capsys.readouterr().out)
    assert set(parsed) == {"target_backend", "prompt", "negative_prompt", "metadata"}
    assert set(parsed["metadata"]) == {"duration", "aspect_ratio", "language", "version"}


def test_pipeline_failure_returns_nonzero(capsys):
    code = hydra.main([DIRECT_URL], pipeline=_FailingPipeline())
    assert code != 0


def test_errors_written_to_stderr(capsys):
    hydra.main([DIRECT_URL], pipeline=_FailingPipeline())
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "pipeline boom" in captured.err
    # A concise message, not a multi-line traceback.
    assert "Traceback" not in captured.err


def test_cli_makes_no_network_calls(capsys, monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", _boom)
    assert hydra.main([AFFILIATE_URL], pipeline=_fake_pipeline()) == 0


# -- local HTML mode --------------------------------------------------------

def _html_file(tmp_path, content=PRODUCT_HTML):
    path = tmp_path / "product.html"
    path.write_text(content, encoding="utf-8")
    return str(path)


def test_local_html_mode_succeeds(capsys, tmp_path):
    code = hydra.main(["--html-file", _html_file(tmp_path), "--source-url", AFFILIATE_URL])
    assert code == 0
    parsed = json.loads(capsys.readouterr().out)
    assert set(parsed) == {"target_backend", "prompt", "negative_prompt", "metadata"}


def test_local_html_mode_accepts_direct_source(capsys, tmp_path):
    code = hydra.main(["--html-file", _html_file(tmp_path), "--source-url", DIRECT_URL])
    assert code == 0
    assert json.loads(capsys.readouterr().out)


def test_local_html_mode_requires_source_url(capsys, tmp_path):
    code = hydra.main(["--html-file", _html_file(tmp_path)])
    assert code != 0
    assert "source-url" in capsys.readouterr().err


def test_url_and_html_together_rejected(capsys, tmp_path):
    code = hydra.main([AFFILIATE_URL, "--html-file", _html_file(tmp_path), "--source-url", AFFILIATE_URL])
    assert code != 0
    assert capsys.readouterr().err


def test_missing_html_file_rejected(capsys):
    code = hydra.main(["--html-file", "does_not_exist.html", "--source-url", AFFILIATE_URL])
    assert code != 0
    assert "not found" in capsys.readouterr().err.lower()


def test_empty_html_file_rejected(capsys, tmp_path):
    code = hydra.main(["--html-file", _html_file(tmp_path, "   "), "--source-url", AFFILIATE_URL])
    assert code != 0
    assert capsys.readouterr().err


def test_invalid_source_domain_rejected(capsys, tmp_path):
    code = hydra.main(["--html-file", _html_file(tmp_path), "--source-url", "https://evil.example.com/x"])
    assert code != 0
    assert capsys.readouterr().err


def test_local_html_mode_makes_no_network(capsys, tmp_path, monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", _boom)
    code = hydra.main(["--html-file", _html_file(tmp_path), "--source-url", AFFILIATE_URL])
    assert code == 0
