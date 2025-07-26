# 🎥 Multi-Platform Video Transcript Tool

Tool chuyển đổi video từ YouTube, TikTok, X (Twitter) sang text với giao diện web đẹp, hỗ trợ timestamps và multiple platforms.

## ✨ Tính năng

- ✅ Trích xuất transcript từ **YouTube, TikTok, X (Twitter)**
- ✅ Hỗ trợ nhiều ngôn ngữ (Tiếng Việt, English, 日本語, 한국어, 中文, Español, Deutsch)
- ✅ **Auto-detect platform** từ URL 
- ✅ 2 chế độ hiển thị: Text thuần và Text có timestamps
- ✅ Copy transcript và download file (.txt hoặc .srt)
- ✅ Giao diện responsive với **platform selector**
- ✅ Thống kê số từ, ký tự, platform

## 🌟 Platforms được hỗ trợ

| Platform | Support | Status |
|----------|---------|--------|
| **🎬 YouTube** | Videos, Shorts, Live | ✅ Full Support |
| **📱 TikTok** | Public videos | 🟡 Partial (không age-restricted) |
| **🐦 X (Twitter)** | Video posts | ✅ Support |
| **🔗 Direct Video Files** | .mp4, .mov, .avi URLs | ✅ Support |

## 🖼️ Screenshots

### Giao diện chính với Platform Selector
![Main Interface](screenshot-main.png)

### Kết quả với timestamps
![With Timestamps](screenshot-timestamps.png)

## 🛠️ Cài đặt

### Requirements
- Python 3.7+
- Flask
- requests
- Supadata API key

### Local Development
```bash
# Clone project
git clone https://github.com/viettran1502/youtube-transcript-tool-byanhtvdcme.git
cd youtube-transcript-tool-byanhtvdcme

# Tạo virtual environment
python -m venv venv

# Kích hoạt virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy ứng dụng
python app.py

# Truy cập: http://localhost:5000
```

## 🔧 Cấu hình API Key

### Supadata API
1. Đăng ký tại [dash.supadata.ai](https://dash.supadata.ai)
2. Lấy API key miễn phí (100 requests/month)
3. Thay trong `app.py`:
```python
SUPADATA_CONFIG = {
    'API_KEY': 'your_api_key_here',
    # ...
}
```

## 📁 Cấu trúc Project

```
multi-platform-transcript-tool/
├── app.py                 # Flask backend với multi-platform support
├── index.html            # Frontend với platform selector
├── requirements.txt      # Python dependencies
├── vercel.json          # Vercel deployment config
└── README.md            # Documentation
```

## 🎯 Cách sử dụng

### 1. **Chọn Platform**
- 🎯 **Tự động**: Auto-detect từ URL
- 🎬 **YouTube**: Videos & Shorts
- 📱 **TikTok**: TikTok videos  
- 🐦 **X (Twitter)**: Video posts

### 2. **Nhập URL**
```
# YouTube
https://www.youtube.com/watch?v=dQw4w9WgXcQ
dQw4w9WgXcQ

# TikTok  
https://www.tiktok.com/@username/video/1234567890

# X (Twitter)
https://twitter.com/username/status/1234567890
https://x.com/username/status/1234567890

# Direct Video Files
https://example.com/video.mp4
```

### 3. **Tùy chọn**
- **Ngôn ngữ**: vi, en, ja, ko, zh, es, de
- **Timestamps**: Bao gồm thời gian trong transcript

### 4. **Kết quả**
- Copy text transcript
- Download file .txt hoặc .srt
- Xem thống kê: số từ, ký tự, platform

## 📋 API Endpoints

### POST /api/transcript
Lấy transcript từ video URL

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "languages": ["vi", "en"],
  "include_timestamps": false
}
```

**Response:**
```json
{
  "success": true,
  "platform": "YouTube",
  "text": "Transcript content...",
  "word_count": 1234,
  "char_count": 5678,
  "language": "vi (Supadata)",
  "available_languages": ["vi", "en", "ja"],
  "method": "Supadata Universal API"
}
```

### GET /api/health
Health check và platform info

### GET /api/test  
Test endpoint để verify API connection

## 🚀 Deployment

### Vercel (Recommended)
```bash
# Deploy với Vercel CLI
vercel --prod
```

### Railway/Heroku
```bash
# Deploy với Git
git add .
git commit -m "Deploy multi-platform transcript tool"
git push railway main  # hoặc heroku main
```

### VPS với CyberPanel
1. Upload files qua File Manager
2. Cài đặt Python dependencies
3. Configure web server
4. Set environment variables

## ⚠️ Limitations

### Platform-specific
- **YouTube**: Chỉ video có subtitle/closed captions
- **TikTok**: Không hỗ trợ age-restricted videos
- **X (Twitter)**: Chỉ video posts có audio
- **Video Files**: Phải là public URLs

### API Limitations  
- **Free tier**: 100 requests/month (Supadata)
- **Rate limits**: Tự động handle với exponential backoff
- **File size**: Có giới hạn cho video files lớn

## 🐛 Troubleshooting

### "Không tìm thấy transcript"
- Video không có subtitle/captions
- Video bị private/restricted  
- Thử platform khác hoặc video khác

### "API Error 500"
- TikTok video có thể bị age-restricted
- Thử video public khác
- Check API quota

### Local development issues
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Check Python version  
python --version  # Cần >= 3.7
```

## 📊 Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, TailwindCSS, JavaScript
- **API**: Supadata Universal API
- **Deployment**: Vercel, Railway, Heroku compatible

## 📞 Support

- **GitHub Issues**: [Report bugs](https://github.com/viettran1502/youtube-transcript-tool-byanhtvdcme/issues)
- **Facebook**: [duymuoi.team](https://www.facebook.com/duymuoi.team)

## 📄 License

MIT License - Sử dụng tự do cho mục đích cá nhân và thương mại.

## 🙏 Credits

- **Supadata API** - Universal video transcript extraction
- **Flask** - Web framework
- **TailwindCSS** - UI styling  
- **Font Awesome** - Icons

## 📈 Changelog

### v7.0 (2025-07-26) - Multi-Platform Release
- ✅ **Multi-platform support**: YouTube, TikTok, X (Twitter)
- ✅ **Platform selector UI**: Auto-detect và manual selection
- ✅ **Universal API integration**: Supadata Universal endpoint
- ✅ **Enhanced error handling**: Platform-specific error messages
- ✅ **Better UX**: Platform examples và auto-detection
- ✅ **Improved statistics**: Platform info display

### v6.1 (2025-07-24) - Supadata Integration  
- ✅ Migrated to Supadata API
- ✅ Fixed authentication (x-api-key header)
- ✅ Improved error handling
- ✅ Better response processing

### v1.0.0 (2025-07-24) - Initial Release
- ✅ Basic YouTube transcript extraction
- ✅ Web interface
- ✅ Multiple language support
- ✅ Timestamps feature
- ✅ Download functionality

---

**Made with ❤️ by anhtv@dcme**