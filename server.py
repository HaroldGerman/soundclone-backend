from flask import Flask, request, jsonify, Response, stream_with_context
import yt_dlp
import requests

app = Flask(__name__)

# --- CONFIGURACIÓN ---
mobile_opts = {
    'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
    'force_ipv4': True,
    'quiet': True,
    'no_warnings': True,
}

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query: return jsonify({'error': 'Falta q'}), 400

    try:
        search_opts = {
            **mobile_opts, 
            'extract_flat': True,
            'format': 'bestaudio/best',
        }
        with yt_dlp.YoutubeDL(search_opts) as ydl:
            result = ydl.extract_info(f"ytsearch40:{query}", download=False)
            
        videos = []
        if 'entries' in result:
            for entry in result['entries']:
                if entry.get('id') and entry.get('title'): 
                    videos.append({
                        'id': entry['id'],
                        'title': entry['title'],
                        'artist': entry.get('uploader', 'Desconocido'),
                        'thumbnail': entry.get('thumbnails', [{}])[-1].get('url', ''),
                    })
        return jsonify(videos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- STREAM MEJORADO (FIX PARA 403) ---
@app.route('/stream', methods=['GET'])
def stream():
    video_id = request.args.get('id')
    if not video_id: return "Falta id", 400

    try:
        print(f"🎵 Streaming: {video_id}")
        
        # 1. Obtener URL real con headers de Android
        audio_opts = {
            **mobile_opts,
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
        }
        url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            real_audio_url = info['url']
            
        print(f"✅ URL obtenida: {real_audio_url[:50]}...")

        # 2. HEADERS CLAVE PARA EVITAR 403
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'identity',
            'Range': request.headers.get('Range', 'bytes=0-'),  # Importante para seeking
        }

        # 3. Conectar con YouTube usando los headers correctos
        req = requests.get(real_audio_url, headers=headers, stream=True)
        
        # 4. Si YouTube requiere Range, enviarlo al cliente
        response_headers = {
            'Content-Type': req.headers.get('Content-Type', 'audio/mp4'),
            'Accept-Ranges': 'bytes',
        }
        
        if 'Content-Length' in req.headers:
            response_headers['Content-Length'] = req.headers['Content-Length']
            
        if 'Content-Range' in req.headers:
            response_headers['Content-Range'] = req.headers['Content-Range']

        # 5. Stream con headers apropiados
        return Response(
            stream_with_context(req.iter_content(chunk_size=1024*16)),
            status=req.status_code,
            headers=response_headers
        )

    except Exception as e:
        print(f"❌ Error Stream: {e}")
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)