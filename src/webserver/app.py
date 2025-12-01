from flask import Flask, jsonify, request, render_template

# Import shared helpers from `state` so the Flask app and the running bot
# share the same playlist object and access it in a thread-safe way.
from state import PLAYBACK_STATUS, get_playlist_snapshot
from state import bot as state_bot

app = Flask(__name__)

@app.route('/playlist', methods=['GET'])
def get_playlist():
    snapshot = get_playlist_snapshot()
    playlist_to_display = [
        {
            'url': item.url,
            'status': item.status.name,
            'title': item.title
        }
        for item in snapshot
    ]
    
    return jsonify(playlist_to_display)

@app.route('/guilds', methods=['GET'])
def get_guild_count():
    """Return the number of guilds the bot is connected to.

    The Discord bot instance is stored in :mod:`state` under the name
    ``bot``.  If the bot has not yet connected, ``state_bot.guilds`` will
    be an empty list.
    """
    if state_bot is None: #TODO: Pretty sure this is never true, needs to be fixed
        return jsonify({'guilds': 0})
    return jsonify({'guilds': len(state_bot.guilds)})

@app.route('/')
def admin_panel():
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)