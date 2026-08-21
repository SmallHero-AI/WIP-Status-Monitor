# 專門幼兒觀看 - 低剪輯頻率與真實人眼視角影片自動化生成工具 (Toddler Video Generator)

本工具專為 0-3 歲幼兒視覺與認知發展設計。傳統動畫通常具備快速鏡頭切換（High Frequency Cuts）、亮色衝擊與劇烈晃動，容易造成幼兒眼神疲勞與大腦過度刺激（Over-stimulation）。
本工具透過 Python 自動化引擎，精確控制運镜頻率、運鏡曲線與畫面色彩，導出符合自然人眼視角的柔和影片。

---

## 🌟 核心設計規範

1. **極低剪輯頻率 (Low Shot Frequency)**：
   - 單一鏡頭停留時間強制限制在 **10 至 15 秒以上**。
   - 嚴禁硬切（Hard Cut），場景之間統一使用 **2.5 秒漸變融鏡 (Cross-Dissolve)**。
2. **模擬真實人眼視角 (Human-Eye Motion Curves)**：
   - 採用 **S 型 Ease-In-Out 貝茲曲線** 進行慢速 Pan & Zoom，符合人類眼神跟隨物體的自然起伏。
3. **視覺防過度刺激過濾 (Anti-Overstimulation Filter)**：
   - 彩度自動軟化（Saturation Scale 85%），避免強烈原色刺激幼兒視覺感官。
   - 柔化畫面對比度，去除閃爍高光。

---

## 📁 目錄結構

```
Toddler_Video_Generator/
├── config/
│   └── sample_story.json           # 幼兒故事 JSON 腳本
├── sample_assets/                  # 示範用柔和圖像與聲波音效素材
├── src/
│   ├── script_validator.py         # 幼兒視覺安全校驗器
│   ├── motion_engine.py            # 人眼運鏡與圖像處理引擎
│   └── video_renderer.py           # 高畫質 1080p/60fps 影片合成器
├── generate_sample_assets.py       # 預設素材生成腳本
├── preview_dashboard.html          # HTML5 Canvas 即時運鏡預覽儀表板
├── preview_server.py               # 本地預覽 HTTP 伺服器
├── main.py                         # 主程式入口 CLI
└── README.md
```

---

## 🚀 快速開始 (Quick Start)

### 1. 生成示範素材並合成 1080p 幼兒影片
直接執行 `main.py`：
```bash
python main.py
```
執行後將自動生成示範圖片、校驗故事腳本，並在專案根目錄導出 `toddler_sample_video.mp4`！

### 2. 開啟網頁即時運鏡預覽器
在瀏覽器中開啟 `preview_dashboard.html` 或執行：
```bash
python preview_server.py
```
連線至 `http://localhost:8088/preview_dashboard.html` 即可在網頁上播放動畫預覽與運鏡向量。

### 3. 腳本安全校驗 (Script Validator)
僅檢查 JSON 腳本是否符合幼兒視覺安全規範：
```bash
python main.py --validate-only --script config/sample_story.json
```

---

## 📄 JSON 腳本自訂格式說明

您可以自由編寫 JSON 腳本生成專屬幼兒動畫：

```json
{
  "title": "我的幼兒繪本故事",
  "visual_safety": {
    "min_scene_duration_sec": 12.0,
    "transition_duration_sec": 2.5,
    "saturation_scale": 0.85
  },
  "scenes": [
    {
      "id": "scene_1",
      "title": "藍天與白雲",
      "image": "path/to/image.png",
      "duration": 12.0,
      "motion": {
        "type": "pan_zoom",
        "start": { "x": 0.0, "y": 0.0, "zoom": 1.0 },
        "end": { "x": 0.2, "y": 0.2, "zoom": 1.15 },
        "easing": "ease_in_out"
      }
    }
  ],
  "bgm": {
    "file": "path/to/soft_music.mp3",
    "volume": 0.25
  }
}
```
