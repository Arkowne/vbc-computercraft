import http.server
import socketserver
import os
import uuid

from convert import convert_video  # ta fonction qui convertit la vidéo et retourne (video_id, output_dir)

PORT = 4334
VIDEO_ROOT = 'videos'
os.makedirs(VIDEO_ROOT, exist_ok=True)


class Handler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.serve_index()
        elif self.path.startswith('/videos/'):
            super().do_GET()
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == '/upload':
            self.handle_upload()
        else:
            self.send_error(404, "Not Found")

    def serve_index(self):
        videos = []
        for vid in sorted(os.listdir(VIDEO_ROOT)):
            video_path = os.path.join(VIDEO_ROOT, vid)
            preview = os.path.join(video_path, 'preview.jpg')
            if os.path.isdir(video_path) and os.path.isfile(preview):
                videos.append((vid, f"/videos/{vid}/preview.jpg"))

        html = '''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>VBC</title>
<link rel="icon" type="image/x-icon" href="https://i.postimg.cc/qMDp0t0p/logo.png" >
<style>
  body { font-family: Arial, sans-serif; margin:0; padding:0; background:#f4f4f4;}
  header { background:#222; color:#fff; display:flex; align-items:center; justify-content:space-between; padding:10px 20px; }
  header .logo { display:flex; align-items:center; font-weight:bold; font-size:1.5em; }
  header .logo img { height:30px; margin-right:10px; }
  header button { background:orange; border:none; padding:10px 20px; color:#fff; cursor:pointer; border-radius:4px; font-weight:bold; }
  main { padding:20px; display:flex; flex-wrap: wrap; gap:20px; justify-content:center; }
  .video-card { background:#fff; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.15); width:160px; text-align:center; padding:10px; }
  .video-card img { width:100%; height:auto; border-radius:4px; }
  .video-id { margin-top:8px; font-family: monospace; font-size: 0.9em; word-break: break-all; }
  form { display:none; }
  img {image-rendering: pixelated;}
</style>
</head>
<body>
<header>
  <div class="logo">
    <img src="https://i.postimg.cc/qMDp0t0p/logo.png" alt="Logo" />
    VBC
  </div>
  <button onclick="document.getElementById('uploadForm').style.display='block'">Upload</button>
</header>

<main>
'''
        for vid, preview_url in videos:
            html += f'''
  <div class="video-card">
    <img src="{preview_url}" alt="Preview {vid}" />
    <div class="video-id">{vid}</div>
  </div>
'''
        html += '''
</main>

<form id="uploadForm" enctype="multipart/form-data" method="POST" action="/upload" style="display:none; padding:20px; background:#fff; position:fixed; top:20%; left:50%; transform:translateX(-50%); border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.3);">
  <h2>Uploader une vidéo</h2>
  <input type="file" name="file" accept="video/*" required />
  <br/><br/>
  <button type="submit" style="background:orange; color:#fff; border:none; padding:10px 20px; border-radius:4px; cursor:pointer;">Envoyer</button>
  <button type="button" onclick="document.getElementById('uploadForm').style.display='none'">Annuler</button>
</form>

</body>
</html>
'''
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def handle_upload(self):
        content_length = int(self.headers.get('Content-Length', 0))
        content_type = self.headers.get('Content-Type', '')
        if 'multipart/form-data' not in content_type:
            self.send_error(400, "Content-Type doit être multipart/form-data")
            return

        boundary = content_type.split("boundary=")[1].encode()
        remainbytes = content_length
        line = self.rfile.readline()
        remainbytes -= len(line)
        if boundary not in line:
            self.send_error(400, "Content does not start with boundary")
            return

        # Lire jusqu'à la ligne avec le filename
        filename = None
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if line.startswith(b'Content-Disposition'):
                disposition = line.decode()
                if 'filename="' in disposition:
                    filename = disposition.split('filename="')[1].split('"')[0]
                    filename = os.path.basename(filename)
                else:
                    filename = f"upload_{uuid.uuid4().hex}.tmp"
            if line == b'\r\n':
                break

        if not filename:
            self.send_error(400, "Pas de fichier dans la requête")
            return

        # Stockage temporaire
        filepath = os.path.join('/tmp', f'upload_{uuid.uuid4().hex}')
        with open(filepath, 'wb') as out_file:
            preline = self.rfile.readline()
            remainbytes -= len(preline)
            while remainbytes > 0:
                line = self.rfile.readline()
                remainbytes -= len(line)
                if boundary in line:
                    preline = preline.rstrip(b'\r\n')
                    out_file.write(preline)
                    break
                else:
                    out_file.write(preline)
                    preline = line

        try:
            video_id, output_dir = convert_video(filepath)
        except Exception as e:
            self.send_error(500, f"Erreur lors de la conversion: {e}")
            os.remove(filepath)
            return

        os.remove(filepath)

        # Rediriger vers la page d'accueil
        self.send_response(303)
        self.send_header('Location', '/')
        self.end_headers()


if __name__ == '__main__':
    os.chdir(os.getcwd())
    with socketserver.TCPServer(('', PORT), Handler) as httpd:
        print(f"Serving HTTP on port {PORT}")
        httpd.serve_forever()
