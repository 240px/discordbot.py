import discord
from discord.utils import get
from discord import FFmpegPCMAudio
import youtube_dl
import asyncio
from async_timeout import timeout
from functools import partial
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import itertools
from random import choice
import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('TOKEN')

suisei = commands.Bot(command_prefix=".",help_command=None)  #ตัวแปรนี้คือ = ตัวบอทของเรา

# wrapper / decorator

message_lastseen = datetime.now()
message2_lastseen = datetime.now()

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn',
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5" ## song will end if no this line
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester

        self.title = data.get('title')
        self.web_url = data.get('webpage_url')

        # YTDL info dicts (data) have other useful information you might want
        # https://github.com/rg3/youtube-dl/blob/master/README.md

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading.
        """
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop, download=False):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        await ctx.send(f'```ini\n[Added {data["title"]} ได้เพิ่มลงในคิวแล้ว.]\n```') #delete after can be added

        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title']}

        return cls(discord.FFmpegPCMAudio(source, **ffmpeg_options), data=data, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(data['url'], **ffmpeg_options), data=data, requester=requester)

class MusicPlayer:
    """A class which is assigned to each guild using the bot for Music.
    This class implements a queue and loop, which allows for different guilds to listen to different playlists
    simultaneously.
    When the bot disconnects from the Voice it's instance will be destroyed.
    """

    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  # Now playing message
        self.volume = .5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(300):  # 5 minutes...
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return await self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                # So we should regather to prevent stream expiration
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f'เกิดข้อผิดพลาดในการประมวลผลเพลง.\n'
                                             f'```css\n[{e}]\n```')
                    continue

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            self.np = await self._channel.send(f'**กำลังเล่น :** `{source.title}`')
            await self.next.wait()

            # Make sure the FFmpeg process is cleaned up.
            source.cleanup()
            self.current = None

            try:
                # We are no longer playing this song...
                await self.np.delete()
            except discord.HTTPException:
                pass

    async def destroy(self, guild):
        """Disconnect and cleanup the player."""
        del players[self._guild]
        await self._guild.voice_client.disconnect()
        return self.bot.loop.create_task(self._cog.cleanup(guild))

############


game = discord.Game("Type .help")
# wrapper / decorator ฟังก์ชั่นที่อยู่ในฟังก์ชั่น   
@suisei.event
# aysnc คือ asynchronous // แปลว่าการทำงานที่ไม่พร้อมกัน เป็นคำตรงข้ามของ synchronous
async def on_ready():
    await suisei.change_presence(status=discord.Status.do_not_disturb, activity=game)
    print(f"Starting {suisei.user}")

@suisei.command()
async def test(ctx, *, par):
    await ctx.channel.send("You typed {0}".format(par))

@suisei.command() 
async def help(ctx):
    # help
    # test
    # send
    emBed = discord.Embed(title="Suisei", description="คำสั่งบอทที่ใช้งานได้ตอนนี้", color=0x17c1ff)
    emBed.add_field(name=".help", value="ดูคำสั่งต่างๆ ของบอท", inline=False)
    emBed.add_field(name=".leave", value="คำสั่งเอาบอทออกจากห้อง", inline=False)
    emBed.add_field(name="คำสั่งเกี่ยวกับเพลง", value="ทุกอย่างที่เกี่ยวกับเพลง")
    emBed.add_field(name=".p", value="คำสั่งเล่นเพลง", inline=False)
    emBed.add_field(name=".skip", value="คำสั่งข้ามเพลง", inline=False)
    emBed.add_field(name=".pause", value="คำสั่งหยุดเพลง", inline=False)
    emBed.add_field(name=".resume", value="คำสั่งเล่นเพลงต่อ", inline=False)
    emBed.add_field(name=".stop", value="คำสั่งหยุดเพลง (เล่นต่อไม่ได้)", inline=False)
    emBed.add_field(name=".queue", value="คำสั่งดูคิวเพลง", inline=False)
    emBed.set_thumbnail(url='https://i.imgur.com/baFb9X2.jpeg')
    emBed.set_footer(text='Hoshimachi Suisei', icon_url='https://i.imgur.com/baFb9X2.jpeg')
    await ctx.channel.send(embed=emBed)

@suisei.command()
async def send(ctx):
    print(ctx.channel)
    await ctx.channel.send('โชหล่อมาก')

# รับค่ามาแล้วส่งข้อความหา author
@suisei.event #async/await 
async def on_message(message):
    if message.content == 'suichan':
        await suisei.logout()
    await suisei.process_commands(message)

# ฟังก์ชั่นเล่นเพลง .p
@suisei.command()
async def p(ctx,* ,search: str):
    channel = ctx.author.voice.channel
    # ตัวแปรนี้มันจะหาบอทที่อยู่ใน Voice client เรามา
    voice_client = get(suisei.voice_clients, guild=ctx.guild) 

    # if นี้จะให้มันเช็คว่า ถ้า client นี้เป็น None แล้วก็จะให้บอทเข้ามา จะทำให้บอทเชื่อมต่อเข้ามา
    if voice_client == None:
        await ctx.channel.send("บอทมาแล้ววว")
        await channel.connect()
        voice_client = get(suisei.voice_clients, guild=ctx.guild)
    
    await ctx.trigger_typing()

    _player = get_player(ctx)
    source = await YTDLSource.create_source(ctx, search, loop=suisei.loop, download=False)

    await _player.queue.put(source)


players = {}
def get_player(ctx):
    try:
        player = players[ctx.guild.id]
    except:
        player = MusicPlayer(ctx)
        players[ctx.guild.id] = player
    
    return player

# คำสั่งหยุดเพลง
@suisei.command()
async def stop(ctx):
    voice_client = get(suisei.voice_clients, guild=ctx.guild)
    if voice_client == None:
        await ctx.channel.send("บอทไม่ได้อยู่ในห้อง")
        return

    if voice_client.channel != ctx.author.voice.channel:
        await ctx.channel.send("คุณไม่สามารถหยุดเพลงจากห้องอื่นได้".format(voice_client.channel))
        return
    voice_client.stop()

# คำสั่งหยุดที่เล่นในขณะนี้
@suisei.command()
async def pause(ctx):
    voice_client = get(suisei.voice_clients, guild=ctx.guild)
    if voice_client == None:
        await ctx.channel.send("บอทไม่ได้อยู่ในห้อง")
        return

    if voice_client.channel != ctx.author.voice.channel:
        await ctx.channel.send("คุณไม่สามารถใช้คำสั่งนี้ได้".format(voice_client.channel))
        return
    voice_client.pause()    


@suisei.command()
async def resume(ctx):
    voice_client = get(suisei.voice_clients, guild=ctx.guild)
    if voice_client == None:
        await ctx.channel.send("บอทไม่ได้อยู่ในห้อง")
        return

    if voice_client.channel != ctx.author.voice.channel:
        await ctx.channel.send("คุณไม่สามารถใช้คำสั่งนี้ได้".format(voice_client.channel))
        return
    voice_client.resume()   


@suisei.command()
async def leave(ctx):
    await ctx.voice_client.disconnect()


@suisei.command()
async def queue(ctx):
    voice_client = get(suisei.voice_clients, guild=ctx.guild)
    if voice_client == None or not voice_client.is_connected():
        await ctx.channel.send("บอทไม่ได้อยู่ในห้อง",delete_after=10)
        return

    player = get_player(ctx)
    if player.queue.empty():
        return await ctx.send("ขณะนี้ไม่มีเพลงอยู่ในคิว")

    upcoming = list(itertools.islice(player.queue._queue,0,player.queue.qsize()))
    fmt = '\n'.join(f'**`{_["title"]}`**' for _ in upcoming)
    embed = discord.Embed(title=f'เพลงต่อไป {len(upcoming)}', description=fmt)
    await ctx.send(embed=embed)


@suisei.command()
async def skip(ctx):
    voice_client = get(suisei.voice_clients, guild=ctx.guild)

    if voice_client == None or not voice_client.is_connected():
        await ctx.channel.send("บอทไม่ได้อยู่ในห้อง", delete_after=10)
        return

    if voice_client.is_paused():
        pass
    elif not voice_client.is_playing():
        return

    voice_client.stop()
    await ctx.send(f'**`{ctx.author.name}`**: ได้ทำการ skip เพลง')
    

suisei.run(token)
