import http.server
import socketserver
import socket
import qrcode
import os
import sys

# Get local IP
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

PORT = 8000
IP = get_ip()
URL = f"http://{IP}:{PORT}/Stock%20analysis%20Web.html"

# Generate QR Code
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=1,
    border=2,
)
qr.add_data(URL)
qr.make(fit=True)

print("="*60)
print(f"啟動 PWA 本地伺服器...")
print(f"請確保您的手機與電腦連線至【同一個 Wi-Fi】網路。")
print(f"請用手機相機掃描下方的 QR Code，或直接在手機瀏覽器輸入：")
print(f"網址: {URL}")
print("="*60)
print("\n")
qr.print_ascii(tty=False)
print("\n")
print("="*60)
print("伺服器運行中... (按 Ctrl+C 即可停止)")

Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n伺服器已關閉。")
        sys.exit(0)
