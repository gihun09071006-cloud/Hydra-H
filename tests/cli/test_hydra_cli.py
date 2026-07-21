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

AFFILIATE_URL = "https://link.coupang.com/a/example"
DIRECT_URL = "https://www.coupang.com/vp/products/123456789"


class _FailingPipeline:
    def run(self, url):
        raise RuntimeError("pipeline boom")


def test_affiliate_url_accepted(capsys):
    assert hydra.main([AFFILIATE_URL]) == 0
    out = capsys.readouterr().out
    assert json.loads(out)  # valid JSON


def test_direct_coupang_url_accepted(capsys):
    assert hydra.main([DIRECT_URL]) == 0
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
    hydra.main([DIRECT_URL])
    parsed = json.loads(capsys.readouterr().out)
    assert isinstance(parsed, dict)


def test_output_matches_render_prompt_contract(capsys):
    hydra.main([DIRECT_URL])
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
    assert hydra.main([AFFILIATE_URL]) == 0
