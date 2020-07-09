import sys
import asyncio
import json
from telethon import TelegramClient
from sonarclient import SonarClient
from telegram_api_credentials import api_id, api_hash
from json_encoder import teleJSONEncoder
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
import pprint

pp = pprint.PrettyPrinter(indent=4)


class SonarTelegram():

    def __init__(self, loop, api_id, api_hash, collection, session_name, endpoint):
        self.loop = loop or asyncio.get_event_loop()
        self.sonar = SonarClient()
        self.api_id = api_id
        self.api_hash = api_hash
        self.telegram = TelegramClient(session_name,
                                       self.api_id,
                                       self.api_hash,
                                       loop=self.loop)
        self.data = {}

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
            "entity_id": dialog.id,
        })

    async def import_message(self, entity):
        if not (isinstance(entity.to_id, PeerChat) or isinstance(entity.to_id, PeerChannel)):
            user_id = entity.from_id
            full = await self.telegram(GetFullUserRequest(user_id))
            entity.username = full.user.username
            entity.first_name = full.user.first_name
            print(entity.username, entity.first_name, entity.message)
        entity_json = json.dumps(entity, cls=teleJSONEncoder)
        id = await self.put_message(entity_json)
        return id

    async def import_entity(self, entity_id, collection_name="telegram"):
        ids = []
        await self.ensure_collection(collection_name)
        await self.ensure_types()
        entities = self.telegram.iter_messages(entity_id)
        async for entity in entities:
            if not (isinstance(entity.to_id, PeerChat) or isinstance(entity.to_id, PeerChannel)):
                user_id = entity.from_id
                full = await self.telegram(GetFullUserRequest(user_id))
                entity.username = full.user.username
                entity.first_name = full.user.first_name
                print(entity.username, entity.first_name, entity.message)
            entity_json = json.dumps(entity, cls=teleJSONEncoder)
            id = await self.put_message(entity_json)
            ids.append(id)

    async def get_info(self):
        return await self.sonar.info()

    async def ensure_collection(self, name):
        self.collection = await self.sonar.create_collection(name)

    async def ensure_types(self):
        types = self.collection.schema.list_types()
        if 'telegram.plainMessage' not in types:
            pp.pprint("putting telegram types")
            await self.load_schemata()

    async def load_schemata(self):
        with open('./schemas/telSchema_MessageMediaPhoto.json') as json_file:
            data = json.load(json_file)
            print(data)
            self.collection.schema.add({'telegram.photoMessage': data})
        with open('./schemas/telSchema_MessageMediaVideo.json') as json_file:
            data = json.load(json_file)
            self.collection.schema.add({'telegram.videoMessage': data})
        with open('./schemas/telSchema_MessageMediaAudio.json') as json_file:
            data = json.load(json_file)
            self.collection.schema.add({'telegram.audioMessage': data})
        with open('./schemas/telSchema_MessageMediaPlain.json') as json_file:
            data = json.load(json_file)
            print(data)
            self.collection.schema.add({'telegram.plainMessage':  data})
        with open('./schemas/telSchema_MessageMediaDocument.json') as json_file:
            data = json.load(json_file)
            self.collection.schema.add({'telegram.documentMessage': data})
        return True

    async def put_message(self, message):
        ''' TODO: Save the remaining types
        (for example the Schema for channels without user_id) in
        ../types and adjust the if-queries here
        '''
        # TODO: get file and push it to fs
        msg = json.loads(message)
        if msg['media'] is None:
            schema = "telegram.plainMessage"
        else:
            if 'MessageMediaAudio' in msg['media']:
                media_id = msg.get('media').get('MessageMediaAudio').get('id')
                schema = "telegram.audioMessage"
            elif 'MessageMediaVideo' in msg['media']:
                media_id = msg.get('media').get('MessageMediaVideo').get('id')
                schema = "telegram.videoMessage"
            elif 'MessageMediaPhoto' in msg['media']:
                media_id = msg.get('media').get('MessageMediaPhoto').get('id')
                schema = "telegram.audioPhoto"
            elif 'MessageMediaDocument' in msg['media']:
                media_id = msg.get('id')
                schema = "telegram.documentMessage"
            else:
                print(json.dumps(msg['media'], cls=teleJSONEncoder))
                return None
            file_bytes = self.telegram.download_media(msg, "./file")
            # TODO: how to handle the file bytes coroutine object?
            print(media_id, str(file_bytes))
        id = await self.collection.put({
            "schema": schema,
            "value": msg,
            "id": "telegram." + str(msg["id"])
        })
        print(id)
        return id


async def init(loop, callback=None, opts=None):
    client = SonarTelegram(
        loop=loop,
        api_id=api_id,
        api_hash=api_hash,
        session_name='anon',
        collection=opts['collection'],
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
