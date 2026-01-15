import os
from flask import Flask, request, jsonify, send_from_directory
import yt_dlp

app = Flask(__name__)

# Carpeta temporal para guardar las descargas
DOWNLOAD_FOLDER = '/tmp' # En Render usamos /tmp
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def home():
    return "🚀 Servidor Musical Activo - v4.0 Clean"

# --- 1. BUSCAR (Rápido) ---
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query: return jsonify({'error': 'Falta q'}), 400
    try:
        # Buscamos 15 resultados
        with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
            result = ydl.extract_info(f"ytsearch15:{query}", download=False)
            videos = []
            if 'entries' in result:
                for entry in result['entries']:
                    videos.append({
                        'id': entry['id'],
                        'title': entry.get('title', 'Sin título'),
                        'artist': entry.get('uploader', 'Desconocido'),
                        'thumbnail': f"https://i.ytimg.com/vi/{entry['id']}/mqdefault.jpg",
                    })
            return jsonify(videos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- 2. DESCARGAR Y SERVIR (La Clave) ---
@app.route('/play', methods=['GET'])
def play():
    video_id = request.args.get('id')
    if not video_id: return jsonify({'error': 'Falta id'}), 400

    filename = f"{video_id}.m4a"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    # Si el archivo NO existe, lo descargamos
    if not os.path.exists(filepath):
        try:
            print(f"📥 Descargando: {video_id}...")
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best', # Mejor audio m4a
                'outtmpl': filepath,
                'quiet': True,
                'noplaylist': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
            print("✅ Descarga completada.")
        except Exception as e:
            return jsonify({'error': f"Error descargando: {str(e)}"}), 500

    # Devolvemos la URL directa a NUESTRO archivo (no a YouTube)
    # El celular reproducirá este link
    file_url = f"{request.host_url}file/{filename}"
    return jsonify({'url': file_url})

# --- 3. ENTREGAR EL ARCHIVO ---
@app.route('/file/<filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
