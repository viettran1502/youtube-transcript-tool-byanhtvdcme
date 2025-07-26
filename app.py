# app.py - Multi-Platform Video Transcript Tool (Complete Version)
from flask import Flask, request, jsonify, send_from_directory
import requests
import re
import os
import time
import json
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)

# Supadata Configuration
SUPADATA_CONFIG = {
    'API_KEY': 'sd_e9a4b528d641fd89efd1f41540741a9a',
    'BASE_URL': 'https://api.supadata.ai/v1/transcript',  # Universal endpoint
    'TIMEOUT': 30
}

def get_supadata_headers():
    """Get headers for Supadata API requests"""
    return {
        'x-api-key': SUPADATA_CONFIG["API_KEY"],
        'Content-Type': 'application/json'
    }

def extract_video_info(url_or_id):
    """Extract video info from YouTube, TikTok, X URLs or return if already ID"""
    if not url_or_id:
        return None, None
    
    url = url_or_id.strip()
    
    # TikTok URL detection
    if 'tiktok.com' in url.lower():
        return url, 'tiktok'
    
    # Twitter/X URL detection  
    if 'twitter.com' in url.lower() or 'x.com' in url.lower():
        return url, 'twitter'
    
    # YouTube URL/ID detection
    if len(url) == 11 and not url.startswith('http'):
        # YouTube video ID
        return f"https://www.youtube.com/watch?v={url}", 'youtube'
    
    # Extract YouTube video ID from various URL formats
    youtube_patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
    ]
    
    for pattern in youtube_patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}", 'youtube'
    
    # If contains youtube.com but no ID found
    if 'youtube.com' in url.lower() or 'youtu.be' in url.lower():
        return url, 'youtube'
    
    # Default: assume it's a valid URL
    return url, 'unknown'

def get_transcript_supadata_universal(video_url, platform, languages=['vi', 'en']):
    """Get transcript using Supadata Universal API for any supported platform"""
    print(f"📡 Calling Supadata Universal API for {platform.upper()} video: {video_url}")
    
    # Supadata universal transcript endpoint
    api_url = SUPADATA_CONFIG['BASE_URL']
    headers = get_supadata_headers()
    
    # Prepare URL parameters
    params = {
        'url': video_url,
        'text': 'false'  # Get structured data with timestamps
    }
    
    # Add language preference if specified
    if languages and languages[0]:
        params['lang'] = languages[0]
    
    try:
        print(f"🔄 Making GET request to: {api_url}")
        print(f"📝 Parameters: {params}")
        print(f"🎬 Platform: {platform.upper()}")
        
        response = requests.get(
            api_url,
            params=params,
            headers=headers,
            timeout=SUPADATA_CONFIG['TIMEOUT']
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📏 Response length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ API call successful for {platform.upper()}")
                print(f"📋 Response type: {type(data)}")
                
                # Debug: Show response structure
                if isinstance(data, dict):
                    print(f"📄 Response keys: {list(data.keys())}")
                
                # Check if it's a job ID (for large files)
                if isinstance(data, dict) and 'jobId' in data:
                    print(f"⏳ Async job created: {data['jobId']}")
                    return None, f"Processing {platform} video - Job ID: {data['jobId']} (use job status endpoint)"
                
                return process_supadata_response(data, languages[0] if languages else "auto", platform)
                
            except json.JSONDecodeError:
                print(f"❌ JSON decode error for {platform}")
                print(f"📄 Raw response: {response.text[:500]}")
                return None, f"Invalid JSON response from Supadata API for {platform}"
                
        elif response.status_code == 401:
            return None, "Invalid API key - kiểm tra lại API key Supadata"
        elif response.status_code == 429:
            return None, "Rate limit exceeded - đã vượt quota API"
        elif response.status_code == 404:
            return None, f"{platform.title()} video not found hoặc không có transcript"
        elif response.status_code == 405:
            return None, f"Method not allowed for {platform} - API endpoint có thể đã thay đổi"
        else:
            print(f"❌ API error for {platform}: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return None, f"Supadata API error for {platform}: {response.status_code} - {response.text}"
            
    except requests.exceptions.Timeout:
        return None, f"Request timeout for {platform} - thử lại sau"
    except requests.exceptions.RequestException as e:
        return None, f"Network error for {platform}: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error for {platform}: {str(e)}"

def process_supadata_response(data, language, platform="youtube"):
    """Process the response from Supadata API for any platform"""
    try:
        print(f"🔍 Processing {platform.upper()} response...")
        print(f"📋 Response type: {type(data)}")
        
        # Debug: Print response structure
        if isinstance(data, dict):
            preview = str(data)[:300] + "..." if len(str(data)) > 300 else str(data)
            print(f"📄 Response preview: {preview}")
        
        transcript = []
        full_text = ""
        
        # Handle Supadata response format according to their docs
        if isinstance(data, dict):
            print(f"📝 Processing object response for {platform.upper()}...")
            
            # Check for error in response
            if 'error' in data:
                return None, f"API Error: {data['error']}"
            
            # Supadata returns 'content' field with transcript data
            transcript_data = data.get('content')
            detected_language = data.get('lang', language)
            available_languages = data.get('availableLangs', [])
            
            print(f"🗣️ Detected language: {detected_language}")
            print(f"🌍 Available languages: {available_languages}")
            print(f"🎬 Platform: {platform.upper()}")
            
            if not transcript_data:
                return None, f"No content field found in {platform} video response"
            
            # Process transcript data
            if isinstance(transcript_data, str):
                # Simple text format (when text=true)
                full_text = transcript_data.strip()
                transcript = [{'text': full_text, 'start': 0, 'duration': 0}]
                
            elif isinstance(transcript_data, list):
                # Array of transcript segments (when text=false)
                for item in transcript_data:
                    if isinstance(item, dict):
                        # Extract text and timing info
                        text = item.get('text', '').strip()
                        start = float(item.get('offset', 0)) / 1000.0  # Convert ms to seconds
                        duration = float(item.get('duration', 3000)) / 1000.0  # Convert ms to seconds
                        
                        if text:
                            transcript.append({
                                'text': text,
                                'start': start,
                                'duration': duration
                            })
                            full_text += " " + text
                    
                    elif isinstance(item, str) and item.strip():
                        # Direct string items
                        transcript.append({
                            'text': item.strip(),
                            'start': len(transcript) * 3,
                            'duration': 3.0
                        })
                        full_text += " " + item.strip()
            
            else:
                return None, f"Unknown content format for {platform}: {type(transcript_data)}"
        
        else:
            return None, f"Unknown response format from {platform}: {type(data)}"
        
        # Clean up full_text
        full_text = full_text.strip()
        
        if not full_text:
            return None, f"No text content found in {platform} video"
        
        # Validate we have meaningful content
        words = full_text.split()
        if len(words) < 3:
            print(f"⚠️ Short response from {platform}: '{full_text}'")
            return None, f"Response too short from {platform}: '{full_text}'"
        
        result = {
            'transcript': transcript,
            'text': full_text,
            'language': f"{detected_language} (Supadata)",
            'platform': platform.title(),
            'total_entries': len(transcript),
            'word_count': len(words),
            'char_count': len(full_text),
            'available_languages': available_languages
        }
        
        print(f"✅ Processed {platform.upper()} successfully!")
        print(f"📊 Entries: {len(transcript)}, Words: {len(words)}")
        print(f"📝 First 100 chars: {full_text[:100]}...")
        
        return result, None
        
    except Exception as e:
        print(f"❌ Processing error for {platform}: {e}")
        import traceback
        traceback.print_exc()
        return None, f"Response processing error for {platform}: {str(e)}"

def check_video_availability_oembed(video_id):
    """Check video availability using oEmbed API (YouTube only)"""
    try:
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(oembed_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"📺 Video title: {data.get('title', 'N/A')}")
            print(f"👤 Author: {data.get('author_name', 'N/A')}")
            return True, data
        else:
            print(f"❌ Video không khả dụng (status: {response.status_code})")
            return False, None
            
    except Exception as e:
        print(f"⚠️ Không thể kiểm tra video: {e}")
        return None, None

def extract_video_id_youtube_only(url):
    """Extract video ID only for YouTube URLs"""
    if len(url) == 11 and not url.startswith('http'):
        return url
    
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript_with_supadata_universal(video_url, platform, languages):
    """Get transcript using Supadata Universal API for any platform"""
    print(f"📥 Processing {platform.upper()} video with Supadata Universal API")
    print(f"🔗 URL: {video_url}")
    
    # For YouTube platforms, check availability using oEmbed
    if platform == 'youtube':
        # Extract video ID for YouTube oEmbed check
        video_id = extract_video_id_youtube_only(video_url)
        if video_id:
            available, video_info = check_video_availability_oembed(video_id)
            if available is False:
                return None, "YouTube video không khả dụng hoặc bị private/restricted"
    
    # Try Supadata Universal API
    print(f"\n🔄 Trying: Supadata Universal API for {platform.upper()}")
    
    try:
        result, error = get_transcript_supadata_universal(video_url, platform, languages)
        if result:
            return result, None
        elif error:
            print(f"❌ Supadata API error for {platform}: {error}")
            return None, error
    
    except Exception as e:
        print(f"❌ Supadata API exception for {platform}: {e}")
        return None, f"Supadata API failed for {platform}: {str(e)}"
    
    return None, f"Supadata API method failed for {platform}"

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/transcript', methods=['POST'])
def get_transcript():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        languages = data.get('languages', ['vi', 'en'])
        include_timestamps = data.get('include_timestamps', False)
        
        if not url:
            return jsonify({'success': False, 'error': 'URL không được để trống'})
        
        # Extract video info and detect platform
        video_url, platform = extract_video_info(url)
        if not video_url:
            return jsonify({'success': False, 'error': 'URL không hợp lệ'})
        
        print(f"\n{'='*60}")
        print(f"🎯 Processing {platform.upper()} URL: {video_url}")
        print(f"🗣️ Requested languages: {languages}")
        print(f"⏰ Include timestamps: {include_timestamps}")
        print(f"🚀 Using Supadata Universal API")
        print(f"{'='*60}")
        
        # Get transcript using Supadata Universal API
        result, error = get_transcript_with_supadata_universal(video_url, platform, languages)
        
        if error:
            print(f"\n❌ Final error: {error}")
            return jsonify({
                'success': False, 
                'error': error,
                'platform': platform.title(),
                'video_url': video_url,
                'api_used': 'Supadata Universal',
                'suggestions': [
                    f"Xác nhận {platform} video có subtitle/captions",
                    "Kiểm tra API key Supadata",
                    "Thử URL khác để test",
                    f"Một số {platform} video có thể không có transcript",
                    f"Kiểm tra xem {platform} video có public không"
                ]
            })
        
        if not result:
            return jsonify({
                'success': False, 
                'error': f'Không thể lấy transcript từ {platform} video',
                'platform': platform.title()
            })
        
        # Format response
        response_data = {
            'success': True,
            'platform': result['platform'],
            'video_url': video_url,
            'language': result['language'],
            'word_count': result['word_count'],
            'char_count': result['char_count'],
            'total_entries': result['total_entries'],
            'method': 'Supadata Universal API',
            'api_used': 'Supadata',
            'available_languages': result.get('available_languages', [])
        }
        
        if include_timestamps and result['transcript']:
            formatted_lines = []
            for entry in result['transcript']:
                start_time = int(entry.get('start', 0))
                minutes = start_time // 60
                seconds = start_time % 60
                timestamp = f"[{minutes:02d}:{seconds:02d}]"
                formatted_lines.append(f"{timestamp} {entry.get('text', '')}")
            
            response_data['text'] = '\n'.join(formatted_lines)
        else:
            response_data['text'] = result['text']
        
        print(f"\n✅ SUCCESS! Platform: {result['platform']}, Words: {result['word_count']}")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False, 
            'error': f'Lỗi hệ thống: {str(e)}',
            'api_used': 'Supadata Universal'
        })

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'OK', 
        'service': 'Multi-Platform Video Transcript Tool',
        'api_provider': 'Supadata.ai',
        'api_host': 'api.supadata.ai',
        'supported_platforms': ['YouTube', 'TikTok', 'X (Twitter)', 'Video Files'],
        'version': '7.0'
    })

@app.route('/api/test', methods=['GET'])
def test_api():
    """Test endpoint for multiple platforms"""
    try:
        test_urls = {
            'youtube': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            # Add more test URLs when available
            # 'tiktok': 'https://www.tiktok.com/@username/video/1234567890'
        }
        
        results = {}
        
        for platform, test_url in test_urls.items():
            print(f"🧪 Testing {platform.upper()}: {test_url}")
            video_url, detected_platform = extract_video_info(test_url)
            result, error = get_transcript_with_supadata_universal(video_url, detected_platform, ['en'])
            
            results[platform] = {
                'test_status': 'success' if result else 'failed',
                'platform': detected_platform,
                'error': error,
                'word_count': result['word_count'] if result else 0,
                'preview': result['text'][:100] + '...' if result and result.get('text') else None
            }
        
        return jsonify({
            'overall_status': 'success',
            'api_key_status': 'configured' if SUPADATA_CONFIG['API_KEY'] else 'missing',
            'api_endpoint': SUPADATA_CONFIG['BASE_URL'],
            'supported_platforms': ['YouTube', 'TikTok', 'X (Twitter)', 'Video Files'],
            'test_results': results,
            'api_host': 'api.supadata.ai',
            'quota_info': 'Free tier: 100 requests/month'
        })
        
    except Exception as e:
        return jsonify({
            'overall_status': 'error',
            'error': str(e),
            'supported_platforms': ['YouTube', 'TikTok', 'X (Twitter)', 'Video Files'],
            'api_host': 'api.supadata.ai'
        })

if __name__ == '__main__':
    print("🚀 Starting Multi-Platform Video Transcript Service...")
    print("✅ Supadata Universal API integration ready!")
    print("🎤 Multi-Platform Video Transcript Tool v7.0")
    print("📱 Access: http://localhost:5000")
    print("🔑 API: Supadata.ai Universal")
    print("🌐 Platforms: YouTube, TikTok, X (Twitter), Video Files")
    print("🔧 Test endpoint: http://localhost:5000/api/test")
    print("💰 Free tier: 100 requests/month")
    print("📋 Method: GET request with URL parameters")
    print("🔑 Auth: x-api-key header")
    
    app.run(host='0.0.0.0', port=5000, debug=True)