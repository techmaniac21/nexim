import io
import os
import schedule
from time import sleep
import yt_dlp
from contextlib import redirect_stdout
import signal
import sys
import threading
import discord
from discord.ext import commands, tasks
import re

# Centralized logging configuration (consistent formatting + handlers)
from logging_config import logger, discordLogger

# Shared runtime objects and helpers
from state import (
    PLAYBACK_STATUS,
    append_playlist,
    get_playlist_snapshot,
    remove_playlist,
)

# Domain models (kept in a separate module to avoid cluttering main)
from models import youtubeObject, joinedChannel

stop = False

def download_audio(item):
    path = "tmp/" + item.ytVideoID

    if os.path.exists(path + ".mp3"):
        logger.info("file already exists, skipping download")
        item.status = PLAYBACK_STATUS.QUEUED
        return

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': path,
        'logger': logger,

    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([item.url])
        except Exception as e:
            logger.info("download failed")
            item.status = PLAYBACK_STATUS.DOWNLOAD_FAILED
            return
    
    item.status = PLAYBACK_STATUS.QUEUED

url = 'https://music.youtube.com/watch?v=17JZKJlx5uI'
# download_audio(url)
 
# Create a bot instance

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def join_voice_channel(ctx: commands.Context, channel_id: int):
    """
    Command to make the bot join a voice channel based on the provided channel ID.

    Parameters:
    - ctx: commands.Context
        The context of the command.
    - channel_id: int
        The ID of the voice channel to join.
    """
    # Getting the voice channel based on the provided ID
    voice_channel = discord.utils.get(ctx.guild.voice_channels, id=channel_id)

    if voice_channel is None:
        await ctx.send("Voice channel not found.")
        return

    # Joining the voice channel
    voice_client = await voice_channel.connect()

    # voice_client.play(discord.FFmpegOpusAudio("audio.mp3"))

    await ctx.send(f"Joined voice channel: {voice_channel.name}")

@bot.command()
async def leave_voice_channel(ctx: commands.Context):
    """
    Command to make the bot leave the current voice channel.

    Parameters:
    - ctx: commands.Context
        The context of the command.
    """
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice_client is None:
        await ctx.send("Not currently in a voice channel.")
        return

    await voice_client.disconnect()
    await ctx.send("Left the voice channel.")

async def join_voice_channel(ctx: commands.Context):
    voice_channel = discord.utils.get(ctx.guild.voice_channels)
    await voice_channel.connect()
    return voice_channel

@bot.command(name="ping")
async def ping(ctx: commands.Context):
    logger.info("Ping command invoked")
    await ctx.send("Pong!")

@bot.command(name="loopCheck")
async def loopCheck(ctx: commands.Context):
    string = "Current Loop: " + str(checkPlaylist.current_loop) + "\nNext Iteration" + str(checkPlaylist.next_iteration) + "\nIs Running: " + str(checkPlaylist.is_running())
    await ctx.send(string)

@bot.command(name="startLoop") # TODO: Why is this required to start the loop? Should start with checkPlaylist.start()?
async def startLoop(ctx: commands.Context):
    if not checkPlaylist.is_running():
        checkPlaylist.start()
        await ctx.send("Started Playlist Loop")
    else:
        await ctx.send("Playlist Loop is already running")

@bot.command(name="setVolume") #TODO: Broken, needs testing and fixing
async def setVolume(ctx: commands.Context, volume: int):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client is None:
        await ctx.send("Not currently in a voice channel.")
        return
    if volume < 0 or volume > 100:
        await ctx.send("Volume must be between 0 and 100.")
        return
    voice_client.source.volume = volume / 100.0
    await ctx.send(f"Volume set to {volume}%")

@bot.command()
async def play(ctx: commands.Context, url: str):
    # Check to see if checkPlaylist is actually running before we start trying to play
    if not checkPlaylist.is_running():
        checkPlaylist.start()

    # Determine current voice client for this guild
    voice_client = ctx.voice_client

    # Find the invoking user's voice channel
    user = ctx.author
    user_voice_channel = None
    if isinstance(user, discord.Member) and user.voice and user.voice.channel:
        user_voice_channel = user.voice.channel

    if user_voice_channel is None:
        await ctx.send("You must be in a voice channel for me to join.")
        return

    # If bot is not connected, connect to the user's channel
    if voice_client is None:
        try:
            voice_client = await user_voice_channel.connect()
        except Exception as e:
            await ctx.send("Failed to connect to your voice channel.")
            return
    else:
        # If bot is connected but in a different channel, move to the user's channel
        if voice_client.channel != user_voice_channel:
            try:
                await voice_client.move_to(user_voice_channel)
            except Exception as e:
                await ctx.send("Failed to move to your voice channel.")
                return

    channel_to_join = user_voice_channel

    # Fix URL to a standard YouTube link format (by taking video ID and implementing it into standard URL)
    youtubeId = re.search(r'(.*watch\?v=|.*youtu.be\/)([a-zA-Z0-9_-]*)(&|\?)?', url)
    if youtubeId is None:
        await ctx.send("I can't find a valid video ID in that URL, ensure that the Youtube link includes a video ID (e.g. watch?v=XXXXXX or youtu.be/XXXXXX).")
        return
    
    logger.info("extracted youtube id: " + youtubeId[2] + " from url " + url)

    url = "https://www.youtube.com/watch?v=" + youtubeId[2]

    yt_obj = youtubeObject(url=url, channel=channel_to_join, client=voice_client)  # TODO: Should voice_client be in object?
    await ctx.send("Item added to playlist!")
    append_playlist(yt_obj)

@bot.command
async def move(ctx: commands.Context):
    voice_client = ctx.voice_client

    # Find the invoking user's voice channel
    user = ctx.author
    user_voice_channel = None
    if isinstance(user, discord.Member) and user.voice and user.voice.channel:
        user_voice_channel = user.voice.channel

    if user_voice_channel is None:
        await ctx.send("Target voice channel not found. Am I able to see the channel?")
        return

    if voice_client is None:
        await ctx.send("I'm not currently in a voice channel. I have to be in a voice channel to be moved. Play something first!")
        return

    # Moving the bot to the target voice channel
    await voice_client.move_to(user_voice_channel)
    await ctx.send(f"Moved to voice channel: {user_voice_channel.name}")

@tasks.loop(seconds=1)
async def checkPlaylist():
    # Iterate a snapshot of the playlist to avoid holding the lock for long
    # and to allow safe modification via the helper functions.
    for item in get_playlist_snapshot():
        match item.status:
            case PLAYBACK_STATUS.NEW:
                item.status = PLAYBACK_STATUS.DOWNLOADING
                thread = threading.Thread(target=download_audio, args=[item])
                thread.start()
                logger.info("started download thread")
            case PLAYBACK_STATUS.DOWNLOADING:
                pass
            case PLAYBACK_STATUS.DOWNLOAD_FAILED:
                logger.info("err download failed everything is died")

                #TODO: Handle failed download (is anything throwing it yet?)
                logger.info("download failed for item: " + item.url)
                logger.info("removing item from playlist")
                remove_playlist(item)
            case PLAYBACK_STATUS.QUEUED:
                channelToPlayTo = item.channel.id
                shouldPlayNow = True
                # Check the playing state using a snapshot to avoid races
                for item2 in get_playlist_snapshot():
                    if item2.channel.id == channelToPlayTo and item2.status == PLAYBACK_STATUS.PLAYING:
                        shouldPlayNow = False
                if shouldPlayNow:
                    logger.info("need to play next track")
                    voice_client = item.client
                    path = "tmp/" + item.ytVideoID + ".mp3"
                    try:
                        playedObject = discord.FFmpegPCMAudio(path)
                        voice_client.play(playedObject, signal_type="music", fec=False)
                    except Exception as e:
                        logger.info("error loading audio into discord")
                        item.status = PLAYBACK_STATUS.FINISHED
                        continue
                    item.status = PLAYBACK_STATUS.PLAYING
                    logger.info("started playing track")
            case PLAYBACK_STATUS.PLAYING:
                if not item.client.is_playing():
                    item.status = PLAYBACK_STATUS.FINISHED
                    logger.info("track finished playing or was skipped")
            case PLAYBACK_STATUS.FINISHED:
                remove_playlist(item)
                logger.info("finished playing track, removed from playlist")

#TODO: Allow users to skip songs in the playlist

@bot.command()
async def skip(ctx: commands.Context):
    voice_client = ctx.voice_client

    if voice_client is None or not voice_client.is_playing():
        await ctx.send("Not currently playing any audio.")
        return

    voice_client.stop()
    await ctx.send("Skipped the current track.")

@bot.command()
async def showPlaylist(ctx: commands.Context):
    playlistToDisplay = []
    for index, item in enumerate(get_playlist_snapshot(), start=1):
        if item.status != PLAYBACK_STATUS.FINISHED and item.status != PLAYBACK_STATUS.CANCELLED:
            playlistToDisplay.append(item)
    
    if playlistToDisplay == []:
        await ctx.send("The playlist is currently empty.")
        return

    message = "Current Playlist:\n"
    for index, item in enumerate(playlistToDisplay, start=1):
        message += f"{index}. {item.url} - Status: {item.status.name}\n"

    await ctx.send(message, suppress_embeds=True)

def signal_handler(sig, frame):
    global stop
    logger.info('You pressed Ctrl+C!')
    stop = True
    checkPlaylist.stop()
    sys.exit(0)

# signal.signal(signal.SIGINT, signal_handler)

def run_webserver():
    from webserver.app import app
    app.run(host='0.0.0.0', port=8080, use_reloader=False)

if __name__ == "__main__":
    # Start the web server in a separate thread
    web_thread = threading.Thread(target=run_webserver, daemon=True)
    web_thread.start()

    # Run the bot
    bot.run(os.getenv('DISCORD_BOT_TOKEN', 'null'), log_handler=None)
