# server.py
# Serveur HTTP minimal qui héberge plusieurs vidéos sous /videos/<id>/

import http.server
import socketserver
import os

PORT = 4334
VIDEO_ROOT = 'videos'

class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # redirige /videos/<id>/... vers le dossier local VIDEO_ROOT/<id>/...
        if path.startswith('/videos/'):
            # retire le slash initial
            rel = path.lstrip('/')
            return os.path.join(os.getcwd(), rel)
        return super().translate_path(path)

    def log_message(self, format, *args):
        # silence
        pass

if __name__ == '__main__':
    os.chdir(os.getcwd())
    with socketserver.TCPServer(('', PORT), Handler) as httpd:
        print(f"Serving HTTP on port {PORT}")
        httpd.serve_forever()