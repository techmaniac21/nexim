from flask import Flask, jsonify, request, render_template

# Import shared helpers from `state` so the Flask app and the running bot
# share the same playlist object and access it in a thread-safe way.
from state import PLAYBACK_STATUS, get_playlist_snapshot

app = Flask(__name__)

@app.route('/playlist', methods=['GET'])
def get_playlist():
    snapshot = get_playlist_snapshot()
    playlist_to_display = [
        {
            'url': item.url,
            'status': item.status.name
        }
        for item in snapshot
    ]
    
    return jsonify(playlist_to_display)

@app.route('/')
def admin_panel():
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)