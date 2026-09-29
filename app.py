from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import re
from pathlib import Path

app = Flask(__name__)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


def is_instagram_url(url):
    return bool(re.match(
        r"^https?://(www\.)?instagram\.com/(reel|p|tv)/[^/?#]+/?",
        url.strip()
    ))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url", "").strip()

    if not url:
        return jsonify({"success": False, "message": "Please enter an Instagram URL."}), 400

    if not is_instagram_url(url):
        return jsonify({
            "success": False,
            "message": "Please enter a valid public Instagram Reel or Post URL."
        }), 400

    # Remove old files so the page returns only the newly downloaded file.
    for file in DOWNLOAD_DIR.iterdir():
        if file.is_file():
            try:
                file.unlink()
            except OSError:
                pass

    options = {
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": str(DOWNLOAD_DIR / "%(title).80s-%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        files = [
            f for f in DOWNLOAD_DIR.iterdir()
            if f.is_file() and f.suffix.lower() == ".mp4"
        ]

        if not files:
            return jsonify({
                "success": False,
                "message": "No downloadable MP4 was returned."
            }), 500

        latest = max(files, key=lambda f: f.stat().st_mtime)

        return jsonify({
            "success": True,
            "filename": latest.name,
            "download_url": f"/file/{latest.name}"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Download failed. Make sure the URL is public and try again."
        }), 500


@app.route("/file/<path:filename>")
def get_file(filename):
    file_path = DOWNLOAD_DIR / filename

    if not file_path.exists() or not file_path.is_file():
        return "File not found", 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name=file_path.name
    )


if __name__ == "__main__":
    app.run(debug=True)
