"""Model classes used by the bot.

Keeping these here avoids cluttering `main.py` and makes it easy for other
modules to import the domain objects without importing the whole bot
runtime.
"""
import io
from state import PLAYBACK_STATUS


class youtubeObject:
    """Represents a requested YouTube audio item.

    Note: instances are mutable and shared between the bot and the web UI.
    """
    status = PLAYBACK_STATUS.NEW
    url = None
    ytVideoID = None
    audioData = io.BytesIO()
    channel = None
    client = None

    def __init__(self, url, channel, client, status=None):
        if status is not None:
            self.status = status
        # store video id by splitting on watch?v= or using full id
        self.ytVideoID = url.split("watch?v=")[-1]
        self.url = url
        self.channel = channel
        self.client = client


class joinedChannel:
    channelId = -1
    playlist = []
