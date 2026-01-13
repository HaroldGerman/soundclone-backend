from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

mobile_opts = {
    'extractor_args': {'youtube': {'player_client': ['android_music']}},
    'force_ipv4': True,
    'quiet': True,
    'no_warnings': True,
}

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'online',
        'version': '2.0',
        'note': 'Solo búsqueda - El streaming lo hace el cliente'
    })

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'Falta parámetro q'}), 400

    try:
        print(f"🔍 Búsqueda: {query}")
        
        search_opts = {
            **mobile_opts, 
            'extract_flat': True,
        }
        
        with yt_dlp.YoutubeDL(search_opts) as ydl:
            result = ydl.extract_info(f"ytsearch40:{query}", download=False)
            
        videos = []
        if 'entries' in result:
            for entry in result['entries']:
                if not entry.get('id') or not entry.get('title'):
                    continue
                    
                # Fix para thumbnails
                thumbnail = ''
                if entry.get('thumbnails'):
                    thumbnail = entry['thumbnails'][-1].get('url', '')
                    if thumbnail.startswith('//'):
                        thumbnail = 'https:' + thumbnail
                
                videos.append({
                    'id': entry['id'],
                    'title': entry['title'],
                    'artist': entry.get('uploader', 'Desconocido'),
                    'thumbnail': thumbnail,
                })
        
        print(f"✅ Encontrados: {len(videos)} resultados")
        return jsonify(videos)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)