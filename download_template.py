import urllib.request

url = "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF4gDS2U7nZHRN9R0GGG1RL11pBIGdNkYyhxhJ0OEoxkFN0fc-Sw1yThZPm63Lm5aIFkawTwgoF9H3mbrkeDfAsPSVJZRRBzSrRCXQR-AKWn7oZQfEYpsaP6x4uICPvt7eYT7KbXz5Enhd-qk-oCBrKVi6v1Rw3iIGv9lBGhBtEA8nL9VxGJyUQn89TaGILCmu-bqu74hLub_k6u4xz0PFdwYA7SZSK"
final_filename = r"e:\G-AI-1\高雄市稅捐稽徵處115年度公教員工生活津貼申請表暨收據_網路下載版.doc"

try:
    print("Downloading...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req) as response, open(final_filename, 'wb') as out_file:
        data = response.read()
        out_file.write(data)
    print("Download complete.")
except Exception as e:
    print(f"Error downloading: {e}")
