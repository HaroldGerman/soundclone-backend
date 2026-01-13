from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

# Opciones para OBTENER el link directo (sin descargar)
# Usamos un cliente 'ios' o 'web' que suelen ser más permisivos con ExoPlayer
ydl_opts_stream = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'force_ipv4': True,
    'extractor_args': {'youtube': {'player_client': ['ios', 'web']}}, # Truco para evitar bloqueo Android
}

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'online', 'version': '3.0 (Hybrid Link Gen)'})

# --- BÚSQUEDA ---
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query: return jsonify({'error': 'Falta q'}), 400

    try:
        search_opts = {
            'extract_flat': True,
            'quiet': True,
            'force_ipv4': True,
        }
        with yt_dlp.YoutubeDL(search_opts) as ydl:
            result = ydl.extract_info(f"ytsearch20:{query}", download=False)
            
        videos = []
        if 'entries' in result:
            for entry in result['entries']:
                if not entry.get('id'): continue
                videos.append({
                    'id': entry['id'],
                    'title': entry.get('title', 'Sin título'),
                    'artist': entry.get('uploader', 'Desconocido'),
                    'thumbnail': entry.get('thumbnails', [{}])[-1].get('url', ''),
                })
        return jsonify(videos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- NUEVO: GENERADOR DE LINKS ---
@app.route('/stream', methods=['GET'])
def stream():
    video_id = request.args.get('id')
    if not video_id: return jsonify({'error': 'Falta id'}), 400

    try:
        print(f"🎧 Generando link para: {video_id}")
        with yt_dlp.YoutubeDL(ydl_opts_stream) as ydl:
            info = ydl.extract_info(video_id, download=False)
            
            # Buscamos la URL directa del audio
            audio_url = info.get('url')
            
            print(f"✅ Link generado exitosamente")
            return jsonify({'url': audio_url})
            
    except Exception as e:
        print(f"❌ Error generando link: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)