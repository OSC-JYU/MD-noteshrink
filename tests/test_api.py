"""clean in HTTP and disk mode, its settings, and /config, /help, /health."""

import importlib
import io
import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "test" / "notesA1.jpg"
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def md(tmp_path, monkeypatch):
    """A MessyDesk root with the sample image, and the service reloaded in disk mode."""
    (tmp_path / "data/messydesk/projects/p1").mkdir(parents=True)
    (tmp_path / "data/messydesk/projects/p1/notes.jpg").write_bytes(SAMPLE.read_bytes())
    monkeypatch.setenv("MD_PATH", str(tmp_path))
    monkeypatch.delenv("STORAGE_MODE", raising=False)
    import md_storage

    importlib.reload(md_storage)
    yield tmp_path
    monkeypatch.delenv("MD_PATH")
    importlib.reload(md_storage)


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    from fastapi.testclient import TestClient

    os.chdir(tmp_path_factory.mktemp("work"))  # uploads/ and output/
    import api

    return TestClient(api.app)


FILE = {"@rid": "#80:1", "label": "notes.jpg", "path": "data/messydesk/projects/p1/notes.jpg"}


def message(params=None, task="clean"):
    return ("message.json", json.dumps({"task": {"id": task, "params": params or {}}, "file": FILE}), "application/json")


def colours(png: bytes) -> int:
    image = Image.open(io.BytesIO(png))
    assert image.format == "PNG" and image.mode == "P"
    return len(np.unique(np.asarray(image)))


def test_clean_over_http(client):
    response = client.post("/process", files={"message": message(), "content": ("notes.jpg", SAMPLE.read_bytes(), "image/jpeg")})
    assert response.status_code == 200, response.text
    uri = response.json()["response"]["uri"]
    assert response.json()["response"]["type"] == "stored" and uri.endswith(".png")
    png = client.get(uri)
    assert png.status_code == 200
    assert colours(png.content) <= 8
    assert client.get(uri).status_code == 404  # removed once fetched


def test_clean_on_disk(client, md):
    response = client.post("/process", files={"message": message({"num_colors": "2", "white_bg": True})})
    assert response.status_code == 200, response.text
    entry = response.json()["response"]["files"][0]
    assert response.json()["response"]["type"] == "disk"
    assert (entry["label"], entry["type"], entry["extension"]) == ("notes.jpg.png", "image", "png")
    png = (md / "data/messydesk/tmp" / entry["path"]).read_bytes()
    image = Image.open(io.BytesIO(png))
    assert colours(png) == 2
    assert image.getpalette()[:3] == [255, 255, 255]  # the background is white
    assert image.size == Image.open(SAMPLE).size


def test_settings_are_checked(client):
    upload = ("notes.jpg", SAMPLE.read_bytes(), "image/jpeg")
    assert client.post("/process", files={"message": message({"num_colors": "500"}), "content": upload}).status_code == 400
    assert client.post("/process", files={"message": message({"value_threshold": "lots"}), "content": upload}).status_code == 400
    assert client.post("/process", files={"message": message(task="shrink"), "content": upload}).status_code == 400
    bad = client.post("/process", files={"message": message(), "content": ("x.jpg", b"not an image", "image/jpeg")})
    assert bad.status_code == 400


def test_disk_mode_refuses_paths_outside_md_path(client, md):
    outside = {"task": {"id": "clean"}, "file": {**FILE, "path": "../etc/passwd"}}
    response = client.post("/process", files={"message": ("m.json", json.dumps(outside), "application/json")})
    assert response.status_code == 400


def test_config_help_health(client, md):
    config = client.get("/config").json()
    assert config["id"] == "md-noteshrink" and config["adapter"] == "elg_fs"
    assert set(config["tasks"]["clean"]["params_help"]) == {"num_colors", "value_threshold", "sat_threshold", "white_bg", "saturate"}
    assert client.get("/help").text.startswith("# Noteshrink")
    assert client.get("/health").json()["status"] == "ok"
