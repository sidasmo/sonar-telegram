import os
import sys
import asyncio
import json
from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeFilename
from tika import parser
from sonarclient import SonarClient
from telegram_api_credentials import api_id, api_hash
from json_encoder import teleJSONEncoder


class SonarTelegram():

    def __init__(self, loop, api_id, api_hash, island, session_name, endpoint):
        self.loop = loop or asyncio.get_event_loop()
        self.sonar = SonarClient(endpoint, island)
        self.api_id = api_id
        self.api_hash = api_hash
        self.telegram = TelegramClient(session_name,
                                       self.api_id,
                                       self.api_hash,
                                       loop=self.loop)
        self.data = {}

    async def ensure_schema(self, schema_name, schema):
        schema = await self.sonar.get_schema(schema_name)
        if schema:
            return schema
        elif await self.sonar.set_schema():
            return True
        else:
            return False

    async def get_jsondialogs(self):
        dialogs_list = []
        dialogs = self.telegram.iter_dialogs()
        async for dialog in dialogs:
            dialog_json = await self.create_dialog_schema(dialog)
            dialogs_list.append(dialog_json)
        return dialogs_list

    async def create_dialog_schema(self, dialog):
        return json.dumps({
            "name": dialog.name,
            "date": dialog.date.isoformat(),
            "last_message": dialog.message.message,
            "dialog_id": dialog.id,
        })

    async def get_messages(self, dialog_id):
        msg_set = []
        msgs = self.telegram.iter_messages(dialog_id)
        async for msg in msgs:
            msg_json = json.dumps(msg, cls=teleJSONEncoder)
            msg_set.append(msg_json)
        return msg_set

    # async def create_message_schema(self, message):
        # return json.dumps({
        # "id": message.id,
        # "from_id": message.from_id,
        # "date": message.date.isoformat(),
        # "content": message.message,
        # "silent": message.silent,
        # "mentioned": message.mentioned
        # })
        # return json.dumps(message, cls=teleJSONEncoder)

    def create_webpage_schema(self, webpage, msg_id):
        return json.dumps({
            "title": webpage.title,
            "url": webpage.url,
            "sitename": webpage.site_name,
            "description": webpage.description,
            "content_type": "website",
            "telegram_id": msg_id
        })

    async def create_document_json(self, document, datadir, msg_id):
        for attribute in document.attributes:
            if type(attribute) is DocumentAttributeFilename:
                if not os.path.isfile(datadir + "/" + attribute.file_name):
                    path = await self.telegram.download_media(
                        message=document,
                        file=datadir
                    )

                    return {
                        "filename": attribute.file_name,
                        "path": path,
                        "extracted_text": parser.from_file(
                            path
                        )["content"],
                        "telegram_id": msg_id,
                        "content_type": "document",
                        "mime_type": document.mime_type
                    }


async def demo(client):
    with open('./schemas/telSchema_MessageMediaPhoto.json') as json_file:
        data = json.load(json_file)
        await client.sonar.put_schema('telegram.photoMessage', data)
    with open('./schemas/telSchema_MessageMediaVideo.json') as json_file:
        data = json.load(json_file)
        await client.sonar.put_schema('telegram.videoMessage', data)
    with open('./schemas/telSchema_MessageMediaAudio.json') as json_file:
        data = json.load(json_file)
        await client.sonar.put_schema('telegram.audioMessage', data)
    with open('./schemas/telSchema_MessageMediaPlain.json') as json_file:
        data = json.load(json_file)
        await client.sonar.put_schema('telegram.plainMessage', data)

    dialogs = await client.get_jsondialogs()
    last_dialog_id = json.loads(dialogs[0])["dialog_id"]
    messages = await client.get_messages(last_dialog_id)
    for msg in messages:
        msg = json.loads(msg)
        if msg['media'] is None:
            schema = "telegram.plainMessage"
        elif 'MessageMediaAudio' in msg['media']:
            schema = "telegram.audioMessage"
        elif 'MessageMediaVideo' in msg['media']:
            schema = "telegram.videoMessage"
        elif 'MessageMediaPhoto' in msg['media']:
            schema = "telegram.audioPhoto"
        id = await client.sonar.put({
            "schema": schema,
            "value": msg,
            "id": "telegram." + str(msg["id"])
        })

async def init(loop, callback=None, opts=None):
    client = SonarTelegram(
        loop=loop,
        api_id=api_id,
        api_hash=api_hash,
        session_name='anon',
        island='default',
        endpoint='http://localhost:9191/api')

    try:
        await client.telegram.connect()
        await client.telegram.start()
    except Exception as e:
        print('Failed to connect', e, file=sys.stderr)
        return

    if callback:
        async with client.telegram:
            try:
                await callback(client, opts)
                await client.sonar.close()
            except Exception as e:
                print('Failed in command callback', e, file=sys.stderr)
                return

        # async with client.telegram:
            # await client.telegram.run_until_disconnected()

    return loop

if __name__ == "__main__":
    aio_loop = asyncio.get_event_loop()
    try:
        aio_loop.run_until_complete(init(aio_loop))
    finally:
        if not aio_loop.is_closed():
            aio_loop.close()
