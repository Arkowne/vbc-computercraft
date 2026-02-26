import http.server
import socketserver
import os
import json
import urllib.request
import sys
import random
from lib.convert_bmi import convert_main
import string
import yt_dlp
import shutil
import subprocess

PORT = 4334
VIDEO_ROOT = 'videos'
os.makedirs(VIDEO_ROOT, exist_ok=True)

class Handler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.serve_index()
        elif self.path == '/api/videos':
            self.serve_api_videos()
        elif self.path.startswith('/videos/'):
            super().do_GET()
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == '/upload':
            self.handle_upload()
        elif self.path == '/download':
            self.handle_download()
        else:
            self.send_error(404, "Not Found")

    def serve_index(self):
        try:
            with open('index.html', 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading index.html: {e}")

    def serve_api_videos(self):
        videos = []
        for vid in sorted(os.listdir(VIDEO_ROOT)):
            video_path = os.path.join(VIDEO_ROOT, vid)
            preview = os.path.join(video_path, 'preview.jpg')
            if os.path.isdir(video_path) and os.path.isfile(preview):
                videos.append({'id': vid, 'preview': f"/videos/{vid}/preview.jpg"})
        data = json.dumps(videos).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


    def handle_download(self):
        try:
            content_type = self.headers.get('Content-Type')
            if not content_type or 'application/json' not in content_type:
                self.send_error(400, "Content-Type must be application/json")
                return

            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))

            url = data.get('url')
            width = data.get('width')
            height = data.get('height')

            if not url:
                self.send_error(400, "Parameter 'url' missing.")
                return

            video_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'id': video_id}).encode('utf-8'))

            def background_conversion(vid):
                try:
                    downloaded_file = None
                    
                    # YouTube ou autres plateformes
                    if any(x in url.lower() for x in ['youtube.com', 'youtu.be', 'youtube-nocookie.com']):
                        ydl_opts = {
                            'format': 'best[ext=mp4]/best',
                            'outtmpl': f'download_{video_id}.%(ext)s',
                        }
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.download([url])
                    
                    # Trouver fichier téléchargé
                    for ext in ['mp4', 'mkv', 'webm']:
                        test_file = f"download_{video_id}.{ext}"
                        if os.path.exists(test_file):
                            downloaded_file = test_file
                            break
                    
                    if not downloaded_file:
                        # Fallback URL directe
                        urllib.request.urlretrieve(url, f"download_{video_id}.mp4")
                        downloaded_file = f"download_{video_id}.mp4"

                    # Conversion
                    sys_argv_backup = sys.argv
                    try:
                        convert_main(downloaded_file, vid, width=width, height=height)
                    finally:
                        sys.argv = sys_argv_backup

                except Exception as e:
                    print(f"Error processing video {video_id}: {e}")
                    return

                finally:
                    # Nettoyage
                    for ext in ['mp4', 'mkv', 'webm']:
                        if os.path.exists(f"download_{video_id}.{ext}"):
                            os.remove(f"download_{video_id}.{ext}")
                    if os.path.exists(f"temp_{video_id}.mp4"):
                        os.remove(f"temp_{video_id}.mp4")
                    
                    os.makedirs(f"videos/{vid}", exist_ok=True)
                    with open(f"videos/{vid}/lock.txt", 'w') as f:
                        f.write("")

            import threading
            threading.Thread(target=background_conversion, daemon=True, args=(video_id,)).start()

        except Exception as e:
            self.send_error(500, f"Error during download request: {e}")


if __name__ == '__main__':
    os.chdir(os.getcwd())
    with socketserver.TCPServer(('', PORT), Handler) as httpd:
        print(f"Serving HTTP on port {PORT}")
        httpd.serve_forever()
