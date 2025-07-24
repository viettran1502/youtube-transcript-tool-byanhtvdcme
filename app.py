from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import re
import os
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

app = Flask(__name__)
CORS(app)

class YouTubeTranscriptService:
    def __init__(self):
        # Khởi tạo API instance (cú pháp mới)
        self.api = YouTubeTranscriptApi()
        print("✅ YouTube Transcript Service đã sẵn sàng!")
        
    def extract_video_id(self, url):
        patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
            return url
            
        return None
    
    def get_available_languages(self, video_id):
        """Lấy danh sách ngôn ngữ transcript có sẵn"""
        try:
            # Dùng static method cho list_transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            languages = []
            
            for transcript in transcript_list:
                languages.append({
                    'language': transcript.language,
                    'language_code': transcript.language_code,
                    'is_generated': transcript.is_generated,
                    'is_translatable': transcript.is_translatable
                })
            
            return languages
        except Exception as e:
            print(f"❌ Lỗi lấy ngôn ngữ: {str(e)}")
            return []
    
    def get_transcript_new_api(self, video_id, languages=['vi', 'en']):
        """Thử lấy transcript với API mới"""
        try:
            print(f"🔄 Thử API mới với ngôn ngữ: {languages}")
            
            # Thử dùng static method trước
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
            return {
                'success': True,
                'transcript': transcript,
                'language_used': languages[0] if languages else 'auto'
            }
            
        except AttributeError:
            # Nếu lỗi AttributeError, thử instance method
            print("🔄 Thử instance method...")
            try:
                transcript = self.api.fetch(video_id, languages=languages)
                return {
                    'success': True,
                    'transcript': transcript,
                    'language_used': languages[0] if languages else 'auto'
                }
            except Exception as e:
                print(f"❌ Instance method failed: {str(e)}")
                return {'success': False, 'error': str(e)}
                
        except Exception as e:
            print(f"❌ Static method failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_transcript_with_fallback(self, video_id, preferred_languages=['vi', 'en']):
        """Thử lấy transcript với nhiều ngôn ngữ khác nhau"""
        language_attempts = [
            preferred_languages,
            ['en'],
            ['vi'], 
            ['auto'],
            [],
        ]
        
        for languages in language_attempts:
            try:
                print(f"🔄 Đang thử với ngôn ngữ: {languages}")
                
                if not languages:
                    # Thử lấy transcript đầu tiên có sẵn
                    try:
                        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                        for transcript_obj in transcript_list:
                            transcript = transcript_obj.fetch()
                            if transcript:
                                return {
                                    'success': True,
                                    'transcript': transcript,
                                    'language_used': transcript_obj.language_code
                                }
                    except Exception as e:
                        print(f"❌ List transcripts failed: {str(e)}")
                        continue
                else:
                    result = self.get_transcript_new_api(video_id, languages)
                    if result['success']:
                        return result
                        
            except Exception as e:
                print(f"❌ Lỗi với ngôn ngữ {languages}: {str(e)}")
                continue
        
        return {
            'success': False,
            'error': 'Không tìm thấy transcript cho video này'
        }
    
    def get_transcript(self, video_url, languages=['vi', 'en'], include_timestamps=False):
        """Lấy transcript từ video YouTube"""
        try:
            video_id = self.extract_video_id(video_url)
            if not video_id:
                return {
                    'success': False,
                    'message': 'URL YouTube không hợp lệ'
                }
            
            print(f"📥 Đang xử lý video: {video_id}")
            
            # Lấy danh sách ngôn ngữ có sẵn
            available_languages = self.get_available_languages(video_id)
            print(f"🌐 Ngôn ngữ có sẵn: {[lang.get('language_code', 'unknown') for lang in available_languages]}")
            
            # Thử lấy transcript
            result = self.get_transcript_with_fallback(video_id, languages)
            
            if not result['success']:
                return {
                    'success': False,
                    'message': result.get('error', 'Không thể lấy transcript')
                }
            
            transcript = result['transcript']
            
            # Xử lý transcript data
            if hasattr(transcript, '__iter__') and not isinstance(transcript, str):
                # Nếu transcript là list hoặc iterable
                if include_timestamps:
                    # Format với timestamps: [mm:ss] text
                    text_parts = []
                    for item in transcript:
                        text_content = ""
                        start_time = 0
                        
                        if isinstance(item, dict):
                            text_content = item.get('text', '')
                            start_time = item.get('start', 0)
                        elif hasattr(item, 'text'):
                            text_content = item.text
                            start_time = getattr(item, 'start', 0)
                        else:
                            text_content = str(item)
                        
                        if text_content.strip():
                            # Chuyển seconds thành mm:ss
                            minutes = int(start_time // 60)
                            seconds = int(start_time % 60)
                            timestamp = f"[{minutes:02d}:{seconds:02d}]"
                            text_parts.append(f"{timestamp} {text_content.strip()}")
                    
                    text = '\n'.join(text_parts)
                else:
                    # Format thông thường: chỉ text
                    text_parts = []
                    for item in transcript:
                        if isinstance(item, dict):
                            text_parts.append(item.get('text', ''))
                        elif hasattr(item, 'text'):
                            text_parts.append(item.text)
                        else:
                            text_parts.append(str(item))
                    
                    text = ' '.join(text_parts)
                
                # Tính duration
                duration = 0
                try:
                    for item in transcript:
                        if isinstance(item, dict):
                            start = item.get('start', 0)
                            dur = item.get('duration', 0)
                            duration = max(duration, start + dur)
                        elif hasattr(item, 'start') and hasattr(item, 'duration'):
                            duration = max(duration, item.start + item.duration)
                except:
                    duration = 0
            else:
                text = str(transcript)
                duration = 0
            
            response = {
                'success': True,
                'video_id': video_id,
                'text': text,
                'word_count': len(text.split()),
                'char_count': len(text),
                'duration': duration,
                'language': result['language_used'],
                'available_languages': available_languages,
                'method': 'YouTube Transcript API (Updated)'
            }
            
            if include_timestamps:
                response['transcript'] = transcript
                
            print(f"✅ Thành công! Text length: {len(text)} ký tự")
            
            return response
                
        except Exception as e:
            print(f"❌ Lỗi tổng thể: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'message': f'Lỗi xử lý: {str(e)}'
            }

# Khởi tạo service
print("🚀 Đang khởi tạo YouTube Transcript Service...")
transcript_service = YouTubeTranscriptService()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/transcript', methods=['POST'])
def get_transcript():
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'success': False, 'message': 'URL là bắt buộc'}), 400
        
        url = data['url'].strip()
        languages = data.get('languages', ['vi', 'en'])
        include_timestamps = data.get('include_timestamps', False)
        
        # Xử lý danh sách ngôn ngữ
        if isinstance(languages, str):
            languages = [lang.strip() for lang in languages.split(',')]
        
        video_id = transcript_service.extract_video_id(url)
        if not video_id:
            return jsonify({'success': False, 'message': 'URL YouTube không hợp lệ'}), 400
        
        result = transcript_service.get_transcript(url, languages, include_timestamps)
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Lỗi API: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy', 
        'message': 'YouTube Transcript API đang hoạt động',
        'method': 'YouTube Transcript API (Compatible với cả API cũ và mới)'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🎤 YouTube Transcript Tool")
    print("📱 Truy cập: http://localhost:5000")
    print("📝 Tương thích với cả API cũ và mới")
    print("⚠️  Chỉ hoạt động với video có subtitle công khai")
    app.run(debug=True, host='0.0.0.0', port=port)