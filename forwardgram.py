from telethon import TelegramClient, events
from telethon.tl.types import InputChannel
import yaml
import discord
import asyncio
import os
import logging

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.INFO)

messages = None

with open(os.environ['CONFIG_FILE'], 'rb') as f:
    config = yaml.safe_load(f)

channel_mapping = {}

"""
TELEGRAM CLIENT STUFF
"""
client = TelegramClient(os.environ['SESSION_NAME'], config["api_id"], config["api_hash"])

#TELEGRAM NEW MESSAGE
async def read_messages(event):
    global messages
    # If the message contains a URL, parse and send Message + URL
    try:
        parsed_response = (event.message.message + '\n' + event.message.entities[0].url )
        parsed_response = ''.join(parsed_response)
    # Or we only send Message    
    except:
        parsed_response = event.message.message


    messages.put_nowait((event.chat.id, parsed_response))



"""
DISCORD CLIENT STUFF
"""
intents = discord.Intents.none()
intents.guilds = True
discord_client = discord.Client(intents=intents)
DISCORD_MAX_MESSAGE_LENGTH = 1800

async def send_messages():
    global messages
    await discord_client.wait_until_ready()
    while True:
        telegram_channel, message = await messages.get()
        discord_channel = discord_client.get_channel(channel_mapping[telegram_channel])
        batches = [message[i:i+DISCORD_MAX_MESSAGE_LENGTH] for i in range(0, len(message), DISCORD_MAX_MESSAGE_LENGTH)]
        for batch in batches:
            await discord_channel.send(batch)

async def main():
    global messages 
    global channel_mapping

    messages = asyncio.Queue()
    await client.start()
    input_channels_entities = []
    channel_names_to_discord = {}
    for c in config["channels_configuration"]:
        channel_names_to_discord[c["input"]] = c["output"]
    async for d in client.iter_dialogs():
        if d.name in channel_names_to_discord: #or d.entity.id in config["input_channel_id"]:
            logging.info("Listening in " + d.name)
            channel_mapping[d.entity.id] = channel_names_to_discord[d.name]
            del channel_names_to_discord[d.name]
            input_channels_entities.append( InputChannel(d.entity.id, d.entity.access_hash) )
            if not channel_names_to_discord:
                break

    if not input_channels_entities:
        logging.error("No input channels found, exiting")
        exit()

    client.add_event_handler(read_messages, events.NewMessage(chats=input_channels_entities))

    await asyncio.gather(
        client.disconnected,
        asyncio.create_task(discord_client.start(config["discord_bot_token"])),
        asyncio.create_task(send_messages()),
    )


"""
RUN EVERYTHING ASYNCHRONOUSLY
"""

client.loop.run_until_complete(main())