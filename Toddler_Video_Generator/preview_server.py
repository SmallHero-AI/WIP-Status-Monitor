"""
幼兒影片預覽儀表板本地 HTTP 伺服器 (Local Preview Web Server)
"""

import os
import sys
import http.server
import socketserver
import webbrowser

PORT = 8088
DIRECTORY = "e:/G-AI-1/Toddler_Video_Generator"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def start_server():
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("=" * 60)
        print(f"幼兒慢速運鏡預覽儀表板已在本地啟動！")
        print(f"請在瀏覽器開啟: http://localhost:{PORT}/preview_dashboard.html")
        print("=" * 60)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n伺服器已停止。")

if __name__ == "__main__":
    start_server()
