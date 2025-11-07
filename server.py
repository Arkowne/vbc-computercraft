import http.server
import socketserver
import os
import json
import urllib.request
import sys
import random
from lib.convert_bmi import convert_main
import string

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
            self.send_error(500, f"Erreur lecture index.html : {e}")

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

    def handle_upload(self):
        content_type = self.headers.get('Content-Type')
        if not content_type or 'multipart/form-data' not in content_type:
            self.send_error(400, "Content-Type must be multipart/form-data")
            return

        boundary = content_type.split("boundary=")[-1].encode()
        remain_bytes = int(self.headers['Content-Length'])

        line = self.rfile.readline()
        remain_bytes -= len(line)
        if boundary not in line:
            self.send_error(400, "Content does not start with boundary")
            return

        # Parse headers for file part
        line = self.rfile.readline()
        remain_bytes -= len(line)
        disposition = line.decode()
        if 'filename="' not in disposition:
            self.send_error(400, "Can't find filename in disposition")
            return
        filename = disposition.split('filename="')[1].split('"')[0]

        # Skip Content-Type line and empty line
        line = self.rfile.readline()
        remain_bytes -= len(line)
        line = self.rfile.readline()
        remain_bytes -= len(line)

        tmp_filename = f"upload_{os.getpid()}.tmp"

        with open(tmp_filename, 'wb') as out:
            prev_line = None
            while remain_bytes > 0:
                line = self.rfile.readline()
                remain_bytes -= len(line)
                if boundary in line:
                    if prev_line:
                        if prev_line.endswith(b'\r\n'):
                            prev_line = prev_line[:-2]
                        out.write(prev_line)
                    break
                if prev_line:
                    out.write(prev_line)
                prev_line = line
            else:
                if prev_line:
                    out.write(prev_line)

        import sys
        sys_argv_backup = sys.argv
        try:
            convert_main(tmp_filename)
        except Exception as e:
            self.send_error(500, f"Erreur lors de la conversion : {e}")
            os.remove(tmp_filename)
            sys.argv = sys_argv_backup
            return
        sys.argv = sys_argv_backup

        os.remove(tmp_filename)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))


    def handle_download(self):
        try:
            # Vérifier le Content-Type
            content_type = self.headers.get('Content-Type')
            if not content_type or 'application/json' not in content_type:
                self.send_error(400, "Content-Type must be application/json")
                return

            # Lire le corps de la requête
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))

            url = data.get('url')
            width = data.get('width')
            height = data.get('height')

            if not url:
                self.send_error(400, "Paramètre 'url' manquant")
                return

            # Générer un ID unique et nom temporaire
            video_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            tmp_filename = f"download_{video_id}.mp4"

            # Répondre immédiatement au client avec l'ID
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'id': video_id}).encode('utf-8'))

            # Lancer la conversion en arrière-plan
            def background_conversion(vid):
                try:
                    # Télécharger la vidéo
                    try:
                        urllib.request.urlretrieve(url, tmp_filename)
                    except Exception as e:
                        print(f"Erreur téléchargement vidéo {video_id}: {e}")
                        return

                    # Préparer sys.argv pour convert_main
                    sys_argv_backup = sys.argv
                    try:
                        convert_main(tmp_filename, vid, width=width, height=height)
                    except Exception as e:
                        print(f"Erreur conversion vidéo {video_id}: {e}")
                    finally:
                        sys.argv = sys_argv_backup

                finally:
                    if os.path.exists(tmp_filename):
                        os.remove(tmp_filename)
                        os.remove(f"temp_{video_id}.mp4")
                        with open("videos/" + vid + "/lock.txt", 'w') as f:
                            f.write("")  # ou tu peux écrire "locked" ou autre

            import threading
            threading.Thread(target=background_conversion, daemon=True, args=(video_id,)).start()

        except Exception as e:
            self.send_error(500, f"Erreur lors du téléchargement : {e}")



if __name__ == '__main__':
    os.chdir(os.getcwd())
    with socketserver.TCPServer(('', PORT), Handler) as httpd:
        print(f"Serving HTTP on port {PORT}")
        httpd.serve_forever()
