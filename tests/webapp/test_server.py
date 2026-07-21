"""Tests for the local web server (TASK-028).

The integration test binds a loopback server on an ephemeral port and drives it
with urllib. This is local (127.0.0.1) only — no external network access.
"""

import json
import sys
import threading
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from webapp.server import facts_from_product_json, run_server  # noqa: E402
from webapp.shortform_editor import PlanError  # noqa: E402

EXTENSION_JSON = {
    "marketplace": "coupang",
    "product_name": "무선 목 어깨 마사지기",
    "product_url": "https://www.coupang.com/vp/products/1",
    "affiliate_url": "https://link.coupang.com/a/abc",
    "price": 39900,
    "currency": "KRW",
    "image_urls": ["https://image.coupang.com/a.jpg"],
    "features": ["무선", "온열"],
    "rating": 4.7,
    "review_count": 1234,
}

BOUNDARY = "----hydraTest"


def test_facts_from_extension_json():
    facts = facts_from_product_json(json.dumps(EXTENSION_JSON).encode("utf-8"))
    assert facts.product_name == "무선 목 어깨 마사지기"
    assert facts.source_url == "https://www.coupang.com/vp/products/1"
    assert facts.affiliate_url == "https://link.coupang.com/a/abc"


def test_facts_from_plain_productfacts_json():
    plain = {"product_name": "샘플", "price": 1000, "currency": "KRW"}
    facts = facts_from_product_json(json.dumps(plain).encode("utf-8"))
    assert facts.product_name == "샘플"


def test_facts_rejects_invalid_json():
    with pytest.raises(PlanError):
        facts_from_product_json(b"not json")


def test_facts_rejects_missing_name():
    with pytest.raises(PlanError):
        facts_from_product_json(json.dumps({"price": 1}).encode("utf-8"))


def _multipart(product_json, n_videos):
    delim = ("--" + BOUNDARY).encode()
    out = b""
    out += delim + b"\r\n"
    out += (
        b'Content-Disposition: form-data; name="product_json"; filename="p.json"\r\n'
        b"Content-Type: application/json\r\n\r\n"
    )
    out += json.dumps(product_json).encode("utf-8") + b"\r\n"
    for i in range(n_videos):
        out += delim + b"\r\n"
        out += (
            f'Content-Disposition: form-data; name="videos"; filename="v{i}.mp4"\r\n'
            "Content-Type: video/mp4\r\n\r\n"
        ).encode()
        out += f"fake-video-bytes-{i}".encode() + b"\r\n"
    out += delim + b"--\r\n"
    return out


@pytest.fixture()
def live_server(tmp_path):
    server = run_server(
        host="127.0.0.1", port=0, output_dir=str(tmp_path), enable_preview=False
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()


def _post(base_url, body):
    req = urllib.request.Request(
        base_url + "/generate",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={BOUNDARY}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:  # noqa: S310 (loopback only)
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def test_health(live_server):
    with urllib.request.urlopen(live_server + "/health") as resp:  # noqa: S310
        assert resp.read() == b"ok"


def test_upload_page_served(live_server):
    with urllib.request.urlopen(live_server + "/") as resp:  # noqa: S310
        body = resp.read().decode("utf-8")
    assert "HYDRA" in body
    assert "소스 영상" in body


def test_generate_happy_path(live_server, tmp_path):
    status, body = _post(live_server, _multipart(EXTENSION_JSON, 5))
    assert status == 200
    assert "편집 계획 생성 완료" in body
    # A plan.json was written under the output dir.
    runs = list(Path(tmp_path).glob("run_*/plan.json"))
    assert len(runs) == 1
    plan = json.loads(runs[0].read_text(encoding="utf-8"))
    assert len(plan["clip_timeline"]) == 5
    assert plan["publishing_copy"]["affiliate_disclosure"]


def test_generate_wrong_video_count(live_server):
    status, body = _post(live_server, _multipart(EXTENSION_JSON, 4))
    assert status == 400
    assert "정확히" in body


def test_generate_missing_product_json(live_server):
    delim = ("--" + BOUNDARY).encode()
    body = delim + b"\r\n"
    body += (
        b'Content-Disposition: form-data; name="videos"; filename="v.mp4"\r\n'
        b"Content-Type: video/mp4\r\n\r\nbytes\r\n"
    )
    body += delim + b"--\r\n"
    status, _ = _post(live_server, body)
    assert status == 400
