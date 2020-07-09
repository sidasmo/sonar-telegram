from sonar_telegram import init
import asyncio
import click
from telethon import events
import pprint
import logging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)


pp = pprint.PrettyPrinter(indent=4)


@click.group()
def cli():
    pass


@cli.command()
@click.option('-c', '--collection', default='telegram')
def dialogs(collection):
    opts = {"collection": collection}
    loop(dialogs_cb, opts)


@cli.command()
@click.option('-d', '--entity_id', default='all')
@click.option('-c', '--collection', default='telegram')
def listen(entity_id, collection):
    if entity_id == 'all':
        opts = {}
    else:
        opts = {"entity_id": int(entity_id)}
    opts["collection"] = collection
    loop(listen_cb, opts)


@cli.command()
@click.argument('message')
@click.argument('entity')
def send(message, entity):
    opts = {"message": message, 'entity': entity}
    loop(send_message, opts)


@cli.command()
@click.argument('entity_id')
@click.option('-c', '--collection', default='telegram')
def entity(entity_id, collection):
    print(collection)
    opts = {"entity_id": int(entity_id),
            "collection": collection}
    loop(get_entity_cb, opts)


async def send_message(client, opts={}):
    msg = opts.get('message')
    entity = opts.get('entity')
    if msg is not None:
        await client.telegram.send_message(entity, msg)


async def listen_cb(client, opts={}):
    await client.ensure_types()
    @client.telegram.on(events.NewMessage(chats=(opts.get('entity_id'))))
    async def listen(event):
        #print(event.message)
        id = await client.import_message(event.message)
        print('ID: {}, Message {}'.format(id, event.message))
    # listen for events until the connection is closed (ie forever)
    async with client.telegram:
        await client.telegram.run_until_disconnected()


async def get_entity_cb(client, opts={}):
    await client.ensure_collection(opts.get("collection"))
    entity_id = opts.get("entity_id")
    ids = await client.import_entity(entity_id)
    print(ids)
    return ids


async def dialogs_cb(client, opts={}):
    dialogs = await client.get_jsondialogs()
    pp.pprint(dialogs)
    return dialogs

def loop(callback, opts={}):
    aio_loop = asyncio.get_event_loop()
    try:
        aio_loop.run_until_complete(init(aio_loop, callback, opts))
    finally:
        if not aio_loop.is_closed():
            aio_loop.close()
