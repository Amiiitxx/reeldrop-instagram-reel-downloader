from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import re
import shutil
import subprocess
import sys
from pathlib import Path


app = Flask(__name__)


# =========================================
# DOWNLOAD DIRECTORY
# =========================================

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


# =========================================
# ALLOWED INSTAGRAM URLS
# =========================================

def is_instagram_url(url):
    pattern = (
        r"^https?://(?:www\.)?instagram\.com/"
        r"(?:reel|reels|p|tv)/"
        r"[^/?#]+/?(?:\?.*)?$"
    )

    return bool(
        re.match(
            pattern,
            url.strip(),
            re.IGNORECASE
        )
    )


# =========================================
# MEDIA EXTENSIONS
# =========================================

VIDEO_EXTENSIONS = {
    ".mp4",
    ".webm",
    ".mkv",
    ".mov"
}

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}

ALLOWED_EXTENSIONS = (
    VIDEO_EXTENSIONS |
    IMAGE_EXTENSIONS
)


# =========================================
# CLEAN DOWNLOAD DIRECTORY
# =========================================

def clean_download_directory():

    DOWNLOAD_DIR.mkdir(exist_ok=True)

    for file in DOWNLOAD_DIR.iterdir():

        if file.is_file():

            try:
                file.unlink()

            except OSError:
                pass

        elif file.is_dir():

            try:
                shutil.rmtree(file)

            except OSError:
                pass


# =========================================
# FIND DOWNLOADED MEDIA
# =========================================

def get_downloaded_files():

    files = []

    for file in DOWNLOAD_DIR.rglob("*"):

        if (
            file.is_file()
            and file.suffix.lower() in ALLOWED_EXTENSIONS
        ):
            files.append(file)

    return files


# =========================================
# MEDIA TYPE
# =========================================

def get_media_type(file):

    extension = file.suffix.lower()

    if extension in VIDEO_EXTENSIONS:
        return "video"

    if extension in IMAGE_EXTENSIONS:
        return "image"

    return None


# =========================================
# HOME
# =========================================

@app.route("/")
def index():

    return render_template("index.html")


# =========================================
# DOWNLOAD
# =========================================

@app.route("/download", methods=["POST"])
def download():

    # -----------------------------------------
    # GET URL
    # -----------------------------------------

    url = request.form.get(
        "url",
        ""
    ).strip()


    # -----------------------------------------
    # EMPTY URL
    # -----------------------------------------

    if not url:

        return jsonify({

            "success": False,

            "message":
                "Please enter an Instagram URL."

        }), 400


    # -----------------------------------------
    # URL VALIDATION
    # -----------------------------------------

    if not is_instagram_url(url):

        return jsonify({

            "success": False,

            "message": (
                "Please enter a valid Instagram "
                "Reel or Post URL."
            )

        }), 400


    # -----------------------------------------
    # CLEAN OLD FILES
    # -----------------------------------------

    clean_download_directory()


    # =========================================
    # YT-DLP
    # =========================================

    ytdlp_error = ""

    ytdlp_options = {

        # Best available video/audio
        "format":
            "bestvideo+bestaudio/best",

        # Output
        "outtmpl":
            str(
                DOWNLOAD_DIR /
                "%(title).80s-%(id)s.%(ext)s"
            ),

        # One URL only
        "noplaylist":
            True,

        # Merge video + audio
        "merge_output_format":
            "mp4",

        # Browser headers
        "http_headers": {

            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/154.0.0.0 "
                "Safari/537.36"
            ),

            "Accept-Language":
                "en-US,en;q=0.9"
        },

        "quiet":
            False,

        "no_warnings":
            False,

        "ignoreerrors":
            False,

        "extract_flat":
            False
    }


    try:

        print("\n")
        print("=" * 70)
        print("TRYING VIDEO DOWNLOADER")
        print("=" * 70)
        print(url)
        print("=" * 70)
        print("\n")


        with yt_dlp.YoutubeDL(
            ytdlp_options
        ) as ydl:

            ydl.extract_info(
                url,
                download=True
            )


        # -------------------------------------
        # CHECK DOWNLOADED FILE
        # -------------------------------------

        files = get_downloaded_files()


        if files:

            latest = max(
                files,
                key=lambda f:
                    f.stat().st_mtime
            )

            media_type = get_media_type(
                latest
            )


            if media_type:

                return jsonify({

                    "success":
                        True,

                    "filename":
                        latest.name,

                    "download_url":
                        f"/file/{latest.name}",

                    "media_type":
                        media_type,

                    "extension":
                        latest.suffix.lower()

                })


    except yt_dlp.utils.DownloadError as e:

        ytdlp_error = str(e)

        print("\n")
        print("=" * 70)
        print("YT-DLP ERROR")
        print("=" * 70)
        print(ytdlp_error)
        print("=" * 70)
        print("\n")


    except Exception as e:

        ytdlp_error = str(e)

        print("\n")
        print("=" * 70)
        print("YT-DLP GENERAL ERROR")
        print("=" * 70)
        print(ytdlp_error)
        print("=" * 70)
        print("\n")


    # =========================================
    # GALLERY-DL
    # =========================================

    # Remove files created by yt-dlp
    clean_download_directory()

    gallery_error = ""


    try:

        print("\n")
        print("=" * 70)
        print("TRYING IMAGE DOWNLOADER")
        print("=" * 70)
        print(url)
        print("=" * 70)
        print("\n")


        # -------------------------------------
        # RUN GALLERY-DL
        # -------------------------------------

        result = subprocess.run(

            [
                sys.executable,
                "-m",
                "gallery_dl",

                "-D",
                str(DOWNLOAD_DIR),

                url
            ],

            capture_output=True,

            text=True,

            timeout=120
        )


        stdout = (
            result.stdout.strip()
        )

        stderr = (
            result.stderr.strip()
        )


        # -------------------------------------
        # PRINT OUTPUT
        # -------------------------------------

        if stdout:

            print(stdout)


        if stderr:

            print(stderr)


        # -------------------------------------
        # ERROR
        # -------------------------------------

        if result.returncode != 0:

            gallery_error = (
                stderr
                or stdout
                or "gallery-dl failed"
            )

            raise RuntimeError(
                gallery_error
            )


        # -------------------------------------
        # FIND MEDIA
        # -------------------------------------

        files = get_downloaded_files()


        if files:

            latest = max(

                files,

                key=lambda f:
                    f.stat().st_mtime

            )


            media_type = get_media_type(
                latest
            )


            if media_type:

                return jsonify({

                    "success":
                        True,

                    "filename":
                        latest.name,

                    "download_url":
                        f"/file/{latest.name}",

                    "media_type":
                        media_type,

                    "extension":
                        latest.suffix.lower()

                })


        gallery_error = (
            "gallery-dl completed, "
            "but no supported media file "
            "was found."
        )


    except subprocess.TimeoutExpired:

        gallery_error = (
            "gallery-dl timed out after "
            "120 seconds."
        )


        print("\n")
        print("=" * 70)
        print("GALLERY-DL TIMEOUT")
        print("=" * 70)
        print(gallery_error)
        print("=" * 70)
        print("\n")


    except Exception as e:

        gallery_error = str(e)


        print("\n")
        print("=" * 70)
        print("GALLERY-DL ERROR")
        print("=" * 70)
        print(gallery_error)
        print("=" * 70)
        print("\n")


    # =========================================
    # ERROR HANDLING
    # =========================================

    combined_error = (
        ytdlp_error
        + " "
        + gallery_error
    )

    error_lower = (
        combined_error.lower()
    )


    # -----------------------------------------
    # LOGIN / AUTHENTICATION
    # -----------------------------------------

    if (
        "login" in error_lower
        or
        "authentication" in error_lower
        or
        "redirect to login" in error_lower
        or
        "requires login" in error_lower
    ):

        return jsonify({

            "success":
                False,

            "message": (
                "Instagram requires login access "
                "for this post. Please try another "
                "publicly accessible post."
            ),

            "debug": {

                "yt_dlp":
                    ytdlp_error,

                "gallery_dl":
                    gallery_error

            }

        }), 403


    # -----------------------------------------
    # PRIVATE
    # -----------------------------------------

    if "private" in error_lower:

        return jsonify({

            "success":
                False,

            "message": (
                "This Instagram account or post "
                "is private."
            ),

            "debug": {

                "yt_dlp":
                    ytdlp_error,

                "gallery_dl":
                    gallery_error

            }

        }), 403


    # -----------------------------------------
    # NO VIDEO
    # -----------------------------------------

    if (
        "there is no video" in error_lower
        and
        gallery_error
    ):

        return jsonify({

            "success":
                False,

            "message": (
                "This post could not be accessed "
                "as downloadable media by Instagram."
            ),

            "debug": {

                "yt_dlp":
                    ytdlp_error,

                "gallery_dl":
                    gallery_error

            }

        }), 500


    # -----------------------------------------
    # FINAL ERROR
    # -----------------------------------------

    return jsonify({

        "success":
            False,

        "message": (
            "Instagram could not provide "
            "downloadable media from this URL."
        ),

        "debug": {

            "yt_dlp":
                ytdlp_error,

            "gallery_dl":
                gallery_error

        }

    }), 500


# =========================================
# SERVE FILE
# =========================================

@app.route("/file/<path:filename>")
def get_file(filename):

    file_path = (
        DOWNLOAD_DIR /
        filename
    )


    # -----------------------------------------
    # RESOLVE PATH
    # -----------------------------------------

    try:

        file_path = (
            file_path.resolve()
        )

        download_root = (
            DOWNLOAD_DIR.resolve()
        )


        # Prevent path traversal
        if (
            download_root
            not in file_path.parents
        ):

            return (
                "Invalid file path",
                403
            )


    except Exception:

        return (
            "Invalid file path",
            403
        )


    # -----------------------------------------
    # FILE NOT FOUND
    # -----------------------------------------

    if (
        not file_path.exists()
        or
        not file_path.is_file()
    ):

        return (
            "File not found",
            404
        )


    # -----------------------------------------
    # EXTENSION CHECK
    # -----------------------------------------

    if (
        file_path.suffix.lower()
        not in ALLOWED_EXTENSIONS
    ):

        return (
            "File type not allowed",
            403
        )


    # -----------------------------------------
    # SEND FILE
    # -----------------------------------------

    return send_file(

        file_path,

        as_attachment=True,

        download_name=
            file_path.name

    )


# =========================================
# RUN APPLICATION
# =========================================

if __name__ == "__main__":

    app.run(

        debug=True,

        host="127.0.0.1",

        port=5000

    )