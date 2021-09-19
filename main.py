import discord
import json
from discord.ext import commands
import music

client = commands.Bot(command_prefix='-', intents=discord.Intents.all())

cogs = [music]
for i in cogs:
    i.setup(client)

with open('config.json', 'r') as conf_file:
    token = json.load(conf_file)['token']

client.run(token)
