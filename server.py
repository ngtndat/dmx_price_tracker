import http.server
import socketserver
import mimetypes
import os
import sys

# Force UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

HOST = "127.0.0.1"
PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class ARHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Enable CORS for WebXR & model-viewer blob loading
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

# Register WebXR MIME types
mimetypes.add_type('model/gltf-binary', '.glb')
mimetypes.add_type('model/gltf+json', '.gltf')
mimetypes.add_type('model/vnd.usdz+zip', '.usdz')
mimetypes.add_type('image/avif', '.avif')
mimetypes.add_type('application/json', '.json')

if __name__ == '__main__':
    handler = ARHTTPRequestHandler
    with socketserver.TCPServer((HOST, PORT), handler) as httpd:
        print(f"[AR Web App Server] running at http://{HOST}:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
