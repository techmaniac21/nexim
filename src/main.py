from enum import Enum
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
from apscheduler.schedulers.asyncio import AsyncIOScheduler

stop = False

class PLAYBACK_STATUS(Enum):
    NEW = 0
    DOWNLOADING = 1
    QUEUED = 2
    PLAYING = 3
    FINISHED = 4
    CANCELLED = 5
    # Fail Codes
    DOWNLOAD_FAILED=100

class youtubeObject:
    status = PLAYBACK_STATUS.NEW
    url = None
    ytVideoID = None
    audioData = io.BytesIO()
    channel = None
    client = None

    def __init__(self, url, channel, client, status=None):
        if status != None:
            self.status = status
        self.ytVideoID = url.split("watch?v=")[-1]
        self.url = url
        self.channel = channel
        self.client = client

class joinedChannel:
    channelId = -1
    playlist = []

playlist = []

allJoinedChannels = []

def download_audio(item):
    path = "tmp/" + item.ytVideoID
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': path,
        'logtostderr': True,
        'no-playlist': True #TODO: This isn't working yet
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([item.url])
        except Exception as e:
            print("download failed")
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
    channel_to_join = ctx.voice_client.channel
    voice_client = ctx.voice_client
    if voice_client is None:

        voice_channel = discord.utils.get(ctx.guild.voice_channels)
        user_invoked = ctx.message.author

        channel_to_join = discord.utils.get(ctx.guild.voice_channels, members=[user_invoked])

        voice_client = await voice_channel.connect()

        # if first_voice_channel is None:
        #     voice_client = await join_voice_channel(ctx)
        #     voice_channel = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    object = youtubeObject(url=url, channel=channel_to_join, client=voice_client) # TODO: Should voice_client be in object?
    
    await ctx.send("url added to playlist array")

    playlist.append(object)

@tasks.loop(seconds=1)
async def checkPlaylist():
    for item in playlist:
        match item.status:
            case PLAYBACK_STATUS.NEW:
                item.status = PLAYBACK_STATUS.DOWNLOADING
                thread = threading.Thread(target=download_audio, args=[item])
                thread.start()
                print("started download thread")
            case PLAYBACK_STATUS.DOWNLOADING:
                pass
            case PLAYBACK_STATUS.DOWNLOAD_FAILED:
                print("err download failed everything is died")

                #TODO: Handle failed download (is anything throwing it yet?)
            case PLAYBACK_STATUS.QUEUED:
                channelToPlayTo = item.channel.id
                shouldPlayNow = True
                for item2 in playlist:
                    if item2.channel.id == channelToPlayTo and item2.status == PLAYBACK_STATUS.PLAYING:
                        shouldPlayNow = False
                if shouldPlayNow:
                    print("need to play next track")
                    voice_client = item.client
                    path = "tmp/" + item.ytVideoID + ".mp3"
                    try:
                        playedObject = discord.FFmpegPCMAudio(path)
                        voice_client.play(playedObject, signal_type="music", fec=False)
                    except Exception as e:
                        print("error loading audio into discord")
                        item.status = PLAYBACK_STATUS.FINISHED
                        continue
                    item.status = PLAYBACK_STATUS.PLAYING
                    print("started playing track")
            case PLAYBACK_STATUS.PLAYING:
                if not item.client.is_playing():
                    item.status = PLAYBACK_STATUS.FINISHED
                    print("track finished playing")
                # TODO: Figure out how to determine track is done playing
            case PLAYBACK_STATUS.FINISHED:
                playlist.remove(item)
                print("finished playing track, removed from playlist")
                # TODO: Remove already played track from queue

#TODO: Allow users to skip songs in the playlist

# schedule.every().seconds.do(checkPlaylist)

# def scheduleThread():
#     while(stop == False):
#         schedule.run_pending() #TODO: Should we do hooks instead?
#         sleep(5)

# scheduleThreadRuntime = threading.Thread(target=scheduleThread)
# scheduleThreadRuntime.start()

def signal_handler(sig, frame):
    global stop
    print('You pressed Ctrl+C!')
    stop = True
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
 
# Run the bot
bot.run(os.getenv('DISCORD_BOT_TOKEN', 'null'))
checkPlaylist.start()