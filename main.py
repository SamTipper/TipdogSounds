import os
import discord
import asyncio
from fuzzywuzzy import fuzz
from datetime import datetime, timedelta
import json
from random import choice
import itertools
from dotenv import load_dotenv
import shutil
from mutagen.mp3 import MP3
import random

intents = discord.Intents.default()
intents.messages = True
intents.members = True
env = load_dotenv()
client = discord.Bot(intents=intents)
queue = []

def add_to_queue(sound: str):
    queue.append(sound)

@client.event
async def on_voice_state_update(member, before, after):
    if after.channel and before.channel == None:
        found = False
        for user in after.channel.members:
            if user.id == member.id:
                found = True
                break
        if found == True:
            voice = discord.utils.get(member.guild.voice_channels, name=after.channel.name)
            await play_on_join(voice, str(member.id))

async def play_on_join(channel, user_id):
    data = read_json('ringtones')
    if user_id in data:
        add_to_queue(data[user_id])
        if not discord.utils.get(client.voice_clients, guild=channel.guild):
            await play_sound(channel, False)

def read_json(file):
    if file == 'leaderboard':
        with open("./leaderboard.json", "r") as db:
            data = json.load(db)
            db.close()
    elif file == 'ringtones':
        with open("./ringtones.json", "r") as db:
            data = json.load(db)
            db.close()
    return data

def leaderboard(state, sound=None):
    data = read_json('leaderboard')
    if state == "add":
        if sound not in data:
            data.update({sound.lower(): 1})
        else:
            data[sound.lower()] += 1
        with open("./leaderboard.json", "w") as db:
            json.dump(data, db)

    elif state == "leaderboard":
        data_str = ""
        for sound, counter in sorted(itertools.islice(data.items(), 10), key=lambda item: item[1], reverse=True):
            data_str += f"**{sound.title()}:** x{counter}\n"

        embed = discord.Embed(
            title = 'Sound Leaderboard',
            description=data_str,
            colour = discord.Colour.dark_green()
        )  
        return embed

async def search_for_sound(args, state=None):
    sound_found = False
    sounds = {}
    for file in os.listdir("./sounds"):
        likeness = fuzz.ratio(args.lower(), file.replace(".mp3", "").lower())
        if likeness >= 80:
            if likeness == 100:
                sound_found = True
                break
            else:
                sounds.update({file.replace(".mp3", "").lower(): likeness})

    if sound_found == True:
        if state != None:
            leaderboard(state="add", sound=file.replace(".mp3", ""))
        return file.replace(".mp3", ""), sound_found
    elif sounds:
        sound_found = True
        if state != None:
            leaderboard(state="add", sound=max(sounds, key=sounds.get).replace(".mp3", ""))
        return max(sounds, key=sounds.get), sound_found
    
    else:
        return "Sound file not found, check your spelling and try again.", sound_found

@client.slash_command()
async def sound(ctx, arg1, arg2=None):
    """Play a sound, find sounds, or set your theme tune as you enter the voice chat!"""
    if arg1.lower() == "list":
        await sound_list(ctx)

    elif arg1.lower() == "play":
        if arg2 != None:
            result = await search_for_sound(arg2, 'normal') 
            if result[1] == True:
                add_to_queue(result[0])
                if not discord.utils.get(client.voice_clients, guild=ctx.guild):
                    await play_sound(ctx, True)
                else:
                    await ctx.respond(f'{result[0].title()} added to the queue!')
            else:
                await ctx.respond(result[0])
        else:
            await ctx.respond(f"Sound name not entered, try: ``/sound play [sound name]``")

    elif arg1.lower() == "random":
        choice = choice(os.listdir("./sounds")).replace(".mp3", "").title()
        add_to_queue(choice)
        if not discord.utils.get(client.voice_clients, guild=ctx.guild):
            await play_sound(ctx, True)
        else:
            await ctx.respond(f'{choice} added to the queue!')

    elif arg1.lower() == "leaderboard":
        embed = leaderboard(state="leaderboard")
        await ctx.respond(embed=embed)
    else:
        await ctx.respond("Command used incorrectly, ``/sound list``\n``/sound play [sound name]``\n``/sound random``\n``/sound leaderboard``")

async def sound_list(ctx):
    file_str = ""
    for file in sorted(os.listdir("./sounds")):
        length = MP3(f"./sounds/{file}").info.length
        file_str += f"{file}".replace(".mp3", "").title() + f" *| {round(length, 1)} s*\n"
        
    embed = discord.Embed(
        title = 'All Sounds',
        description=f"**/sound play [sound name]**\n{file_str}",
        colour = discord.Colour.dark_green()
    )
    embed.set_footer(text=f"{len(os.listdir('./sounds'))} unique sound files | {len(file_str)}/4096 chars")
    await ctx.respond(embed=embed)

async def play_sound(ctx, in_channel):
    """Handles playing of sound"""
    # Connect to VC and play audio
    try:
        vc = False
        if isinstance(ctx, discord.channel.VoiceChannel):
            voice_channel = ctx
            vc = True
        elif ctx.author.voice is not None:
            voice_channel = ctx.author.voice.channel
            vc = True
        else:
            await ctx.respond('You\'re not in a channel!')

        if vc == True:
            active_voice = await voice_channel.connect()

            while True:
                if in_channel:
                    await ctx.respond(f"Playing: {queue[0].title()}")
                await ctx.guild.get_member(int(os.environ.get("BOT_ID"))).edit(nick=queue[0].title())
                await asyncio.sleep(0.5)
                active_voice.play(discord.FFmpegPCMAudio(executable='ffmpeg',source=f"./sounds/{queue[0]}.mp3"))
                # Wait until audio is finished and then leave the VC
                await asyncio.sleep(2)
                while active_voice.is_playing():
                    await asyncio.sleep(0.5)
                await asyncio.sleep(2)
                queue.pop(0)

                if not queue:
                    break

            await active_voice.disconnect()
            await ctx.guild.get_member(int(os.environ.get("BOT_ID"))).edit(nick="Tipdog Soundboard")

    except Exception as e:
        print(e)
        await ctx.guild.get_member(int(os.environ.get("BOT_ID"))).edit(nick="Tipdog Soundboard")
        await ctx.respond('An error has occured, please try again later.')

@client.slash_command()
async def set(ctx, arg):
    """Play a sound upon joining the server"""
    if arg.lower() != 'none':
        result = await search_for_sound(arg)
        if result[1] == True:
            if MP3(f"./sounds/{result[0]}.mp3").info.length <= 10:
                data = read_json('ringtones')
                if str(ctx.author.id) not in data:
                    data.update({str(ctx.author.id): result[0]})
                else:
                    data[str(ctx.author.id)] = result[0]
                with open("./ringtones.json", "w") as db:
                    json.dump(data, db)
                    db.close()
                await ctx.respond(f"Your ringtone has been updated to {result[0].title()}!")
            else:
                await ctx.respond("Audio clip must be shorter than 10 seconds.")
    else:
        data = read_json('ringtones')
        if str(ctx.author.id) in data:
            del data[str(ctx.author.id)]
            with open("./ringtones.json", "w") as db:
                json.dump(data, db)
                db.close()
            await ctx.respond("Ringtone unset")
        else:
            await ctx.respond("You don't have a ringtone set.")

@client.slash_command()
async def meme(ctx):
    """Get hurled around"""
    if ctx.author.voice:
        await ctx.respond("Have a good trip!")
        og_channel = ctx.author.voice.channel
        for i in range(random.randint(1, 5)):
            channel = client.get_channel(random.choice(ctx.guild.voice_channels).id)
            await asyncio.sleep(0.5)
            await ctx.author.move_to(channel)
        await ctx.author.move_to(og_channel)
    else:
        await ctx.respond("Join a VC!")
        
# On ready
@client.event
async def on_ready():
  await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="/"))
  print('You have logged in as {0.user}'.format(client))


client.run(os.environ.get("TOKEN"))
