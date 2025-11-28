"""Shared runtime state for the bot and web admin UI.

This module centralizes objects that must be identical across different
parts of the program (notably `playlist` and `PLAYBACK_STATUS`). Importing
these from a single module prevents the classic Python gotcha where the
main script (loaded as `__main__`) and an import of the same file under a
different module name (e.g. `import main`) create two separate module
objects and therefore two distinct copies of what the author intended to
be a single global.

When the application is run as `python src/main.py`, Python binds that file
to the module name `__main__`. If another module does `from main import ...`
Python will load the same file a second time as module `main`. Each module
object gets its own globals, so two different `playlist` lists would exist.

To avoid that, other modules import from `state` which is loaded once and
shared across the interpreter.
"""

from enum import Enum
import threading
from typing import List


class PLAYBACK_STATUS(Enum):
    NEW = 0
    DOWNLOADING = 1
    QUEUED = 2
    PLAYING = 3
    FINISHED = 4
    CANCELLED = 5
    DOWNLOAD_FAILED = 100


# Shared playlist used by both the bot and the web admin UI. Import this
# module from other modules to ensure a single shared object instance.
# Keep a re-entrant lock and small helper functions so concurrent access
# from the bot loop and Flask request threads is safe.
playlist: List[object] = []
playlist_lock = threading.RLock()


def get_playlist_snapshot():
    """Return a shallow copy of the playlist under lock for safe iteration."""
    with playlist_lock:
        return list(playlist)


def append_playlist(item: object) -> None:
    """Append an item to the shared playlist under lock."""
    with playlist_lock:
        playlist.append(item)


def remove_playlist(item: object) -> None:
    """Remove an item from the shared playlist under lock, if present."""
    with playlist_lock:
        try:
            playlist.remove(item)
        except ValueError:
            # already removed by another thread; safe to ignore
            pass


def playlist_length() -> int:
    with playlist_lock:
        return len(playlist)

