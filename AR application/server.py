import http.server
import socketserver
import mimetypes
import os
import sys
import socket

# Force UTF-8 encoding for stdout on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

def get_local_ips():
    ips = []
    try:
        hostname = socket.gethostname()
        for item in socket.getaddrinfo(hostname, None):
            ip = item[4][0]
            if ':' not in ip and not ip.startswith('127.'):
                if ip not in ips:
                    ips.append(ip)
    except Exception:
        pass
    return ips

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
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print("==================================================")
        print(f" [AR Web App Server] Dang chay tai:")
        print(f" -> Tren may tinh:  http://localhost:{PORT}")
        
        ips = get_local_ips()
        for ip in ips:
            print(f" -> Tren dien thoai: http://{ip}:{PORT}")
        print("==================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
