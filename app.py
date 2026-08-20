import os
import secrets
import string
from urllib.parse import urlparse

from flask import Flask, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from models import SessionLocal, Urls

app = Flask(__name__)
# A random fallback keeps local development usable without shipping a shared secret.
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 4096

SHORT_CODE_LENGTH = 6
SHORT_CODE_ALPHABET = string.ascii_letters + string.digits


def is_valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def generate_short_code() -> str:
    return "".join(secrets.choice(SHORT_CODE_ALPHABET) for _ in range(SHORT_CODE_LENGTH))


def save_url(original_url: str) -> str:
    """Save a URL, retrying if a randomly generated code collides."""
    for _ in range(10):
        short_url = generate_short_code()
        with SessionLocal() as session:
            session.add(Urls(short_url=short_url, original_url=original_url))
            try:
                session.commit()
                return short_url
            except IntegrityError:
                session.rollback()
    raise RuntimeError("Could not allocate a unique short URL")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        original_url = (request.form.get("url") or "").strip()
        if not is_valid_url(original_url):
            flash("Enter a valid http:// or https:// URL.", "error")
            return render_template("index.html"), 400

        try:
            short_url = save_url(original_url)
        except Exception:
            app.logger.exception("Failed to save shortened URL")
            flash("The URL could not be saved. Please try again.", "error")
            return render_template("500.html"), 500

        short_link = url_for("redirect_short_url", short_url=short_url, _external=True)
        flash(f"{original_url} was saved successfully!", "success")
        flash(f"Short URL: {short_link}", "success")
        return redirect(url_for("index"))

    return render_template("index.html")


@app.route("/<short_url>")
def redirect_short_url(short_url: str):
    with SessionLocal() as session:
        entry = session.query(Urls).filter_by(short_url=short_url).first()
    if entry:
        return redirect(entry.original_url)
    return render_template("404.html"), 404


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(_error):
    return render_template("500.html"), 500


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
