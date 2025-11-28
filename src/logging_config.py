import logging
import sys


# Configure the `discord` logger and a `music_bot` logger for the project.
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')

handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)

discordLogger = logging.getLogger('discord')
discordLogger.setLevel(logging.INFO)
discordLogger.addHandler(handler)

logger = logging.getLogger('music_bot')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Expose both so modules can import `logger` for the bot and tweak levels
# or handlers if needed.
__all__ = ['logger', 'discordLogger', 'handler']
