import os
import sys
import asyncio
import json
import datetime
from telethon import TelegramClient, events
from telethon.tl.patched import Message
from telethon.tl.types import DocumentAttributeFilename, MessageMediaDocument, MessageMediaPhoto, PeerUser, Document, DocumentAttributeVideo, DocumentAttributeFilename, PhotoStrippedSize, PhotoSize, InputPeerSelf, InputPeerUser, User, UserStatusOffline, UserProfilePhoto, Photo, MessageService, MessageActionPhoneCall, MessageService, PhoneCallDiscardReasonMissed, PhoneCallDiscardReasonHangup, FileLocationToBeDeprecated, DocumentAttributeAudio
from tika import parser
from sonarclient import SonarClient
from telegram_api_credentials import *

class SonarTelegram():

    def __init__(self, loop, api_id, api_hash, island, session_name, endpoint):
        print(loop, api_id, api_hash, session_name, endpoint)
        self.loop = loop or asyncio.get_event_loop()
        self.sonar = SonarClient(endpoint, island)
        self.api_id = api_id
        self.api_hash = api_hash
        self.telegram = TelegramClient(session_name,
                                       self.api_id,
                                       self.api_hash,
                                       loop=self.loop)

        self.data = {}

        # @self.telegram.on(events.NewMessage)
        # async def my_event_handler(event):
            # print("EVENT")
            # print(event.original_update)

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

def date_format(message):
    if type(message) == datetime:
        return message.isoformat()

class teleJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (str, int, float)):
            return json.JSONEncoder.default(self, o)
        elif o is None:
            return 'Python_None'
        elif isinstance(o, Message):
            return filter_telMessage(o)
        elif isinstance(o, MessageService):
            return o.__dict__
        elif isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, MessageMediaDocument):
            return {
                o.__class__.__name__: o.document.__dict__,
                'ttl_seconds': o.ttl_seconds
            }
        elif isinstance(o, MessageMediaPhoto):
            return {
                o.__class__.__name__: o.photo.__dict__,
                'ttl_seconds': o.ttl_seconds
            }
        elif isinstance(o, (Document, PeerUser, DocumentAttributeVideo, DocumentAttributeFilename, PhotoStrippedSize, PhotoSize, InputPeerSelf, InputPeerUser, User, UserStatusOffline, UserProfilePhoto, Photo, MessageActionPhoneCall, MessageService, PhoneCallDiscardReasonMissed, PhoneCallDiscardReasonHangup, FileLocationToBeDeprecated, DocumentAttributeAudio)):
            return {
                o.__class__.__name__: o.__dict__
            }
        pass

def filter_telMessage(message):
    message = message.__dict__.items()
    retMessage = {}
    wanted = ['id', 'to_id', 'date', 'out', 'mentioned', 'media']
    for (key, val) in message:
        if (key[0] != '_'):
            retMessage[key]=val
    return retMessage

async def init(loop):
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

    async with client.telegram:
        await demo(client)
        await client.telegram.run_until_disconnected()

    return loop
    # while True:
    #    await asyncio.sleep(0)

if __name__ == "__main__":
    aio_loop = asyncio.get_event_loop()
    try:
        aio_loop.run_until_complete(init(aio_loop))
    finally:
        if not aio_loop.is_closed():
            aio_loop.close()