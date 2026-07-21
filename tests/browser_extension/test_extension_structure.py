"""Structure tests for the HYDRA Coupang browser extension (Manifest V3)."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXT = REPO_ROOT / "browser_extension"

REQUIRED_FILES = ["manifest.json", "popup.html", "popup.js", "content.js", "styles.css"]
ALLOWED_PERMISSIONS = {"activeTab", "scripting", "downloads"}
ALLOWED_HOSTS = {"https://www.coupang.com/*", "https://coupang.com/*"}


def _manifest():
    return json.loads((EXT / "manifest.json").read_text(encoding="utf-8"))


def test_required_files_exist():
    for name in REQUIRED_FILES:
        assert (EXT / name).is_file(), name


def test_manifest_is_valid_mv3():
    manifest = _manifest()
    assert manifest["manifest_version"] == 3
    assert manifest["action"]["default_popup"] == "popup.html"
    assert manifest.get("name")
    assert manifest.get("version")


def test_permissions_are_minimal():
    manifest = _manifest()
    permissions = set(manifest.get("permissions", []))
    assert permissions  # not empty
    assert permissions <= ALLOWED_PERMISSIONS  # nothing beyond the minimal set
    assert "tabs" not in permissions  # broad tab access not requested


def test_host_permissions_restricted_to_coupang():
    manifest = _manifest()
    assert set(manifest.get("host_permissions", [])) == ALLOWED_HOSTS
    assert "<all_urls>" not in json.dumps(manifest)


def test_popup_html_references_assets():
    html = (EXT / "popup.html").read_text(encoding="utf-8")
    assert "popup.js" in html
    assert "styles.css" in html
