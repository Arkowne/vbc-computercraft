import http.server
import socket
from pathlib import Path
import json
import secrets
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer
import yt_dlp
import shutil
import urllib.request
import traceback

from lib.convert_bmi import convert_main


PORT = 4334
VIDEO_ROOT = Path("videos")
JOBS_ROOT = Path("jobs")

VIDEO_ROOT.mkdir(exist_ok=True)
JOBS_ROOT.mkdir(exist_ok=True)

executor = ThreadPoolExecutor(max_workers=4)


def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https")
    except:
        return False


def write_json(path, data):
    path.write_text(json.dumps(data))


def download_video(url, filename, cookies=None):
    filename = Path(filename)

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': str(filename.with_suffix('')) + '.%(ext)s',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'ignoreerrors': True,
        'age_limit': None,
        'quiet': False,
        'no_warnings': True
    }

    if cookies:
        ydl_opts['cookiefile'] = cookies

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("Download completed successfully!")
    except Exception as e:
        print("Error:", e)


def background_conversion(video_id, url, width, height):
    job_dir = JOBS_ROOT / video_id
    job_dir.mkdir(parents=True, exist_ok=True)

    status_file = job_dir / "status.json"
    write_json(status_file, {"status": "processing"})

    downloaded_file = None

    try:
        if any(x in url.lower() for x in ['youtube.com', 'youtu.be', 'youtube-nocookie.com']):
            downloaded_file = job_dir / "input.mp4"
            download_video(url, downloaded_file)
        else:
            downloaded_file = job_dir / "input.mp4"
            urllib.request.urlretrieve(url, downloaded_file)

        convert_main(
            str(downloaded_file),
            video_id=video_id,
            width=width,
            height=height
        )

        write_json(status_file, {"status": "done"})

    except Exception as e:
        print(f"Error processing {video_id}: {e}")
        traceback.print_exc()
        write_json(status_file, {"status": "error", "error": str(e)})

    finally:
        temp_files = ['video.mp4', 'audio.mp4']
        for f in temp_files:
            f_path = job_dir / f
            if f_path.exists():
                f_path.unlink()


def search_youtube_videos(query, max_results=6):
    videos_search = VideosSearch(query, limit=max_results)
    results = videos_search.result()["result"]

    videos = []

    for video in results:
        videos.append({
            "title": video["title"],
            "url": video["link"]
        })

    return videos


class Handler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path in ("/", "/index.html"):
            self.serve_index()
        elif parsed_path.path == "/api/videos":
            self.serve_api_videos()
        elif parsed_path.path == "/search":
            self.serve_search(parsed_path)
        elif parsed_path.path.startswith("/videos/"):
            super().do_GET()
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/download":
            self.handle_download()
        else:
            self.send_error(404, "Not Found")

    def serve_search(self, parsed_path):
        try:
            query_params = parse_qs(parsed_path.query)
            q = query_params.get("q", [""])[0]

            if not q:
                self.send_error(400, "Missing 'q' query parameter")
                return

            videos = search_youtube_videos(q, max_results=6)

            data = json.dumps(videos).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        except Exception as e:
            self.send_error(500, str(e))

    def serve_index(self):
        try:
            content = Path("index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))

    def serve_api_videos(self):
        videos = []
        for vid in sorted(VIDEO_ROOT.iterdir()):
            preview = vid / "preview.jpg"
            if vid.is_dir() and preview.exists():
                videos.append({
                    "id": vid.name,
                    "preview": f"/videos/{vid.name}/preview.jpg"
                })

        data = json.dumps(videos).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def handle_download(self):
        try:
            if "application/json" not in self.headers.get("Content-Type", ""):
                self.send_error(400, "Content-Type must be application/json")
                return

            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body.decode("utf-8"))

            url = data.get("url")
            width = data.get("width")
            height = data.get("height")

            if not url or not is_valid_url(url):
                self.send_error(400, "Invalid or missing URL")
                return

            video_id = secrets.token_hex(5)

            response = {"status": "ok", "id": video_id}
            response_bytes = json.dumps(response).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response_bytes)))
            self.end_headers()
            self.wfile.write(response_bytes)

            executor.submit(
                background_conversion,
                video_id,
                url,
                width,
                height
            )

        except Exception as e:
            self.send_error(500, str(e))


class IPv6ThreadingServer(ThreadingHTTPServer):
    address_family = socket.AF_INET6


if __name__ == "__main__":
    with IPv6ThreadingServer(('::', PORT), Handler) as httpd:
        print(f"IPv6 server running on [::]:{PORT}")
        print(f"Local: http://[::1]:{PORT}")
        print(f"Public: http://[your-ipv6]:{PORT}")
        httpd.serve_forever()