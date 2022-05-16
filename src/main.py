import discord
from discord.ext import commands
import DiscordUtils
from discord.utils import get
from datetime import datetime, timedelta
from random import choice, random

from songs import songAPI

# อันนี้เอาไว้แอบโค้ด เป็น library
import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('TOKEN')
#################################

songsInstance = songAPI()
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
    # emBed สุดยอดเลขฐาน
    emBed = discord.Embed(title="elaina", description="คำสั่งบอทที่ใช้งานได้ตอนนี้", color=0x17c1ff)
    emBed.add_field(name=".help", value="ดูคำสั่งต่างๆ ของบอท", inline=False)
    emBed.add_field(name=".leave", value="คำสั่งเอาบอทออกจากห้อง", inline=False)
    emBed.add_field(name="คำสั่งเกี่ยวกับเพลง", value="ทุกอย่างที่เกี่ยวกับเพลง")
    emBed.add_field(name=".p", value="คำสั่งเล่นเพลง", inline=False)
    emBed.add_field(name=".skip", value="คำสั่งข้ามเพลง", inline=False)
    emBed.add_field(name=".pause", value="คำสั่งหยุดเพลงชั่วคราว", inline=False)
    emBed.add_field(name=".resume", value="คำสั่งเล่นเพลงต่อ", inline=False)
    emBed.add_field(name=".stop", value="คำสั่งหยุดเพลง", inline=False)
    emBed.add_field(name=".queue", value="คำสั่งดูคิวเพลง", inline=False)
    emBed.add_field(name=".search", value="ค้นหารูปภาพใน google", inline=False)
    emBed.set_thumbnail(url='https://i.imgur.com/baFb9X2.jpeg')
    emBed.set_footer(text='Hoshimachi elaina', icon_url='https://i.imgur.com/baFb9X2.jpeg')
    await ctx.channel.send(embed=emBed)

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
    if message.content == 'ซุยจัง':
        await message.channel.send("คะ ?")
        

# ฟังก์ชั่นเล่นเพลง .p
@elaina.command()
async def play(ctx,* ,search: str):
    await songsInstance.play(ctx, search)

# คำสั่งหยุดเพลง
@elaina.command()
async def stop(ctx):
    await songsInstance.stop(ctx)

# คำสั่งหยุดที่เล่นในขณะนี้
@elaina.command()
async def pause(ctx):
    await songsInstance.pause(ctx)

@elaina.command()
async def resume(ctx):
    await songsInstance.resume(ctx)


@elaina.command()
async def leave(ctx):
    await songsInstance.leave(ctx)


@elaina.command()
async def queue(ctx):
    await songsInstance.queue(ctx)


@elaina.command()
async def skip(ctx):
    await songsInstance.skip(ctx)

@elaina.command()
async def avatar(ctx, member: discord.Member = None):
    if member == None:
        member = ctx.author
    
    memberAvatar = member.avatar_url

    avaEmbed = discord.Embed(title = f"{member.name}'s Avatar", color=0x17c1ff)
    avaEmbed.set_image(url = memberAvatar)
    
    await ctx.send(embed = avaEmbed)

elaina.run(token)
