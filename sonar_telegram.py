import sys
import asyncio
import json
from telethon import TelegramClient
from telethon.tl.types import PeerChat, PeerChannel, DocumentAttributeFilename
from sonarclient import SonarClient
from telegram_api_credentials import api_id, api_hash
from json_encoder import teleJSONEncoder
from telethon.tl.functions.users import GetFullUserRequest


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

    async def import_entity(self, entity_id):
        ids = []
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
        return ids

    async def init_schemata(self):
        with open('./schemas/telSchema_MessageMediaPhoto.json') as json_file:
            data = json.load(json_file)
            await self.sonar.put_schema('telegram.photoMessage', data)
        with open('./schemas/telSchema_MessageMediaVideo.json') as json_file:
            data = json.load(json_file)
            await self.sonar.put_schema('telegram.videoMessage', data)
        with open('./schemas/telSchema_MessageMediaAudio.json') as json_file:
            data = json.load(json_file)
            await self.sonar.put_schema('telegram.audioMessage', data)
        with open('./schemas/telSchema_MessageMediaPlain.json') as json_file:
            data = json.load(json_file)
            await self.sonar.put_schema('telegram.plainMessage', data)
        with open('./schemas/telSchema_MessageMediaDocument.json') as json_file:
            data = json.load(json_file)
            await self.sonar.put_schema('telegram.documentMessage', data)
        return True

    async def put_message(self, message):
        ''' TODO: Save the remaining schemas
        (for example the Schema for channels without user_id) in
        ../schemas and adjust the if-queries here
        '''
        msg = json.loads(message)
        if msg['media'] is None:
            schema = "telegram.plainMessage"
        elif 'MessageMediaAudio' in msg['media']:
            schema = "telegram.audioMessage"
        elif 'MessageMediaVideo' in msg['media']:
            schema = "telegram.videoMessage"
        elif 'MessageMediaPhoto' in msg['media']:
            schema = "telegram.audioPhoto"
        elif 'MessageMediaDocument' in msg['media']:
            schema = "telegram.documentMessage"
        else:
            print(json.dumps(msg['media'], cls=teleJSONEncoder))
            return None
        id = await self.sonar.put({
            "schema": schema,
            "value": msg,
            "id": "telegram." + str(msg["id"])
        })
        return id


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
