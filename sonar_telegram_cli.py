from sonar_telegram import init
import asyncio
import click
from telethon import events
import logging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)


@click.group()
def cli():
    pass


@cli.command()
def dialogs():
    loop(dialogs_cb)


@cli.command()
@click.option('-d', '--dialog_id', default='all')
def listen(dialog_id):
    if dialog_id == 'all':
        opts = {}
    else:
        opts = {"dialog_id": int(dialog_id)}
    loop(listen_cb, opts)


@cli.command()
@click.argument('message')
@click.argument('entity')
def send(message, entity):
    opts = {"message": message, 'entity': entity}
    loop(send_message, opts)


@cli.command()
@click.argument('dialog_id')
def dialog(dialog_id):
    opts = {"dialog_id": int(dialog_id)}
    loop(get_dialog_cb, opts)


async def send_message(client, opts={}):
    msg = opts.get('message')
    entity = opts.get('entity')
    if msg is not None:
        await client.telegram.send_message(entity, msg)


async def listen_cb(client, opts={}):
    @client.telegram.on(events.NewMessage(chats=(opts.get('dialog_id'))))
    async def listen(event):
        print('{}'.format(event.message))

    # listen for events until the connection is closed (ie forever)
    async with client.telegram:
        await client.telegram.run_until_disconnected()


async def get_dialog_cb(client, opts={}):
    dialog_id = opts.get("dialog_id")
    dialog = await client.get_messages(dialog_id)
    print(dialog)
    # print("Name: {}, User_ID: {}, Dialog_ID: {}  ".format(dialog.name, dialog))
    return dialog


async def dialogs_cb(client, opts={}):
    dialogs = await client.get_jsondialogs()
    print(dialogs)
    return dialogs


def loop(callback, opts={}):
    aio_loop = asyncio.get_event_loop()
    try:
        aio_loop.run_until_complete(init(aio_loop, callback, opts))
    finally:
        if not aio_loop.is_closed():
            aio_loop.close()
