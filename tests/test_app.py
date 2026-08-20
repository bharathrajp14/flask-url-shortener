import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _database_url():
    handle = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    handle.close()
    return f"sqlite:///{handle.name}"


os.environ["DATABASE_URL"] = _database_url()

from app import app, save_url  # noqa: E402
from models import SessionLocal, Urls  # noqa: E402


app.config.update(TESTING=True, SECRET_KEY="test-secret")


def test_short_url_redirects_to_original_url():
    short_code = save_url("https://example.com/docs")
    response = app.test_client().get(f"/{short_code}")
    assert response.status_code == 302
    assert response.headers["Location"] == "https://example.com/docs"


def test_unknown_short_url_has_dedicated_404_page():
    response = app.test_client().get("/does-not-exist")
    assert response.status_code == 404
    assert b"Short URL not found" in response.data


def test_invalid_url_is_rejected():
    response = app.test_client().post("/", data={"url": "not-a-url"})
    assert response.status_code == 400
    assert b"valid http" in response.data


def test_duplicate_original_urls_are_allowed_with_unique_codes():
    first = save_url("https://example.com/same")
    second = save_url("https://example.com/same")
    assert first != second
    with SessionLocal() as session:
        rows = session.query(Urls).filter_by(original_url="https://example.com/same").all()
    assert len(rows) == 2
