import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
import yt_dlp

app = Flask(__name__)

# Vercel's deployment directory is read-only. Use temporary storage instead.
# Note: Vercel temporary files and in-memory tokens are not persistent across
# serverless invocations. For reliable production use, stream files directly
# or store them in object storage (for example, S3 or compatible storage).
BASE_DOWNLOAD_DIR = Path(
    os.environ.get(
        "DOWNLOAD_DIR",
        str(Path(tempfile.gettempdir()) / "reeldrop"),
    )
)
BASE_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_EXTENSIONS = {".mp4", ".webm", ".mkv", ".mov"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_EXTENSIONS = VIDEO_EXTENSIONS | IMAGE_EXTENSIONS

# Works only while the same runtime instance remains alive; not persistent.
FILE_TOKENS = {}


def is_instagram_url(url: str) -> bool:
    """Allow common Instagram Reel, post, reels, and TV URLs."""
    pattern = (
        r"^https?://(?:www\.)?instagram\.com/"
        r"(?:reel|reels|p|tv)/[^/?#]+/?(?:\?.*)?$"
    )
    return bool(re.match(pattern, url.strip(), re.IGNORECASE))


def get_media_type(file_path: Path):
    extension = file_path.suffix.lower()
    if extension in VIDEO_EXTENSIONS:
        return "video"
    if extension in IMAGE_EXTENSIONS:
        return "image"
    return None


def get_downloaded_files(directory: Path):
    return [
        path
        for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS
    ]


def register_file(file_path: Path) -> str:
    token = uuid.uuid4().hex
    FILE_TOKENS[token] = file_path
    return token


def find_downloaded_file(directory: Path):
    files = get_downloaded_files(directory)
    if not files:
        return None
    return max(files, key=lambda item: item.stat().st_mtime)


def response_for_file(file_path: Path):
    media_type = get_media_type(file_path)
    if not media_type:
        return None
    token = register_file(file_path)
    return jsonify(
        {
            "success": True,
            "filename": file_path.name,
            "download_url": f"/file/{token}",
            "media_type": media_type,
            "extension": file_path.suffix.lower(),
        }
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "ReelDrop"})


@app.route("/download", methods=["POST"])
def download():
    url = (request.form.get("url") or "").strip()

    if not url:
        return jsonify(
            {"success": False, "message": "Please enter an Instagram URL."}
        ), 400

    if not is_instagram_url(url):
        return jsonify(
            {
                "success": False,
                "message": "Please enter a valid Instagram Reel or Post URL.",
            }
        ), 400

    # Each request gets its own folder to avoid filename collisions.
    request_dir = BASE_DOWNLOAD_DIR / uuid.uuid4().hex
    request_dir.mkdir(parents=True, exist_ok=True)

    ytdlp_error = ""
    gallery_error = ""

    ytdlp_options = {
        # Prefer one combined format to avoid requiring FFmpeg to merge streams.
        # Some posts may not provide a combined format; those may still fail.
        "format": "best",
        "outtmpl": str(request_dir / "%(title).80s-%(id)s.%(ext)s"),
        "noplaylist": True,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/154.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
    }

    try:
        with yt_dlp.YoutubeDL(ytdlp_options) as ydl:
            ydl.extract_info(url, download=True)

        downloaded = find_downloaded_file(request_dir)
        if downloaded:
            result = response_for_file(downloaded)
            if result:
                return result

        ytdlp_error = "yt-dlp completed but no supported media file was found."

    except yt_dlp.utils.DownloadError as exc:
        ytdlp_error = str(exc)
        app.logger.warning("yt-dlp failed: %s", ytdlp_error)
    except Exception as exc:
        ytdlp_error = str(exc)
        app.logger.exception("Unexpected yt-dlp error")

    # Fallback for supported image/carousel posts. This may not help with Reels.
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "gallery_dl",
                "-D",
                str(request_dir),
                url,
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

        if result.returncode != 0:
            gallery_error = (
                result.stderr.strip()
                or result.stdout.strip()
                or "gallery-dl failed"
            )
        else:
            downloaded = find_downloaded_file(request_dir)
            if downloaded:
                response = response_for_file(downloaded)
                if response:
                    return response
            gallery_error = (
                "gallery-dl completed, but no supported media file was found."
            )

    except subprocess.TimeoutExpired:
        gallery_error = "gallery-dl timed out after 120 seconds."
    except Exception as exc:
        gallery_error = str(exc)
        app.logger.exception("gallery-dl failed")

    combined_error = f"{ytdlp_error} {gallery_error}".lower()

    # Check technical/server errors before classifying Instagram access errors.
    if "ffmpeg is not installed" in combined_error or "ffmpeg not found" in combined_error:
        status_code = 502
        message = (
            "The server cannot process this video because FFmpeg is unavailable. "
            "Try another post or configure FFmpeg on the server."
        )
    elif any(
        term in combined_error
        for term in (
            "login",
            "authentication",
            "redirect to login",
            "requires login",
            "empty media response",
        )
    ):
        status_code = 403
        message = (
            "Instagram did not provide media access for this post. "
            "It may require login or be temporarily restricted. "
            "Please try another public post."
        )
    elif "private" in combined_error:
        status_code = 403
        message = "This Instagram account or post appears to be private."
    else:
        status_code = 502
        message = (
            "Instagram could not provide downloadable media from this URL. "
            "The post may be unavailable, unsupported, or temporarily restricted."
        )

    # Keep detailed internal errors in server logs, not in the public response.
    app.logger.warning(
        "Download failed. yt-dlp=%s | gallery-dl=%s",
        ytdlp_error[:1000],
        gallery_error[:1000],
    )
    return jsonify({"success": False, "message": message}), status_code


@app.route("/file/<token>")
def get_file(token):
    file_path = FILE_TOKENS.get(token)

    if file_path is None:
        return jsonify(
            {
                "success": False,
                "message": (
                    "This temporary download is no longer available. "
                    "Please download the media again."
                ),
            }
        ), 404

    try:
        resolved_file = file_path.resolve()
        resolved_root = BASE_DOWNLOAD_DIR.resolve()

        # Prevent path traversal outside the configured download directory.
        if resolved_root not in resolved_file.parents:
            return "Invalid file path", 403

        if (
            not resolved_file.exists()
            or not resolved_file.is_file()
            or resolved_file.suffix.lower() not in ALLOWED_EXTENSIONS
        ):
            FILE_TOKENS.pop(token, None)
            return "File not found", 404

        return send_file(
            resolved_file,
            as_attachment=True,
            download_name=resolved_file.name,
        )
    except OSError:
        app.logger.exception("Could not serve temporary download")
        return "Could not serve the file", 500


if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_DEBUG") == "1",
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
    )
