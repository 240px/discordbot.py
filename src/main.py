import discord
from discord.ext import commands
import DiscordUtils
from discord.utils import get
from datetime import datetime, timedelta
from random import choice, random

from commands import commandsAPI

# อันนี้เอาไว้แอบโค้ด เป็น library
import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('TOKEN')
#################################

commandsAPI = commandsAPI()
# wrapper / decorator

message_lastseen = datetime.now()
message2_lastseen = datetime.now()
music = DiscordUtils.Music()
elaina = commands.Bot(command_prefix=".",help_command=None)  #ตัวแปรนี้คือ = ตัวบอทของเรา

game = discord.Game("Type .help")
    # wrapper / decorator ฟังก์ชั่นที่อยู่ในฟังก์ชั่น   
@elaina.event
    # aysnc คือ asynchronous // แปลว่าการทำงานที่ไม่พร้อมกัน เป็นคำตรงข้ามของ synchronous
async def on_ready():
    print(f"Logged in as {elaina.user}")
    await elaina.change_presence(status=discord.Status.do_not_disturb, activity=game)

@elaina.command()
async def test(ctx, *, par):
    await ctx.channel.send("You typed {0}".format(par))

@elaina.command() 
async def help(ctx):
    await commandsAPI.help(ctx)

@elaina.command()
async def send(ctx):
    print(ctx.channel)
    await ctx.channel.send('Hello')

# รับค่ามาแล้วส่งข้อความหา author
@elaina.event #async/await 
async def on_message(message):
    if message.content == 'suichan':
        await elaina.logout()
    await elaina.process_commands(message)
        

# ฟังก์ชั่นเล่นเพลง .p
@elaina.command()
async def play(ctx,* ,search: str):
    await commandsAPI.play(ctx, search)

# คำสั่งหยุดเพลง
@elaina.command()
async def stop(ctx):
    await commandsAPI.stop(ctx)

# คำสั่งหยุดที่เล่นในขณะนี้
@elaina.command()
async def pause(ctx):
    await commandsAPI.pause(ctx)

@elaina.command()
async def resume(ctx):
    await commandsAPI.resume(ctx)


@elaina.command()
async def leave(ctx):
    await commandsAPI.leave(ctx)


@elaina.command()
async def queue(ctx):
    await commandsAPI.queue(ctx)


@elaina.command()
async def skip(ctx):
    await commandsAPI.skip(ctx)

@elaina.command()
async def avatar(ctx, member: discord.Member = None):
    await commandsAPI.avatar(ctx)

elaina.run(token)
