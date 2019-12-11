import json
import datetime
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto, PeerUser, Document, DocumentAttributeVideo, DocumentAttributeFilename, PhotoStrippedSize, PhotoSize, InputPeerSelf, InputPeerUser, User, UserStatusOffline, UserProfilePhoto, Photo, MessageActionPhoneCall, MessageService, PhoneCallDiscardReasonMissed, PhoneCallDiscardReasonHangup, FileLocationToBeDeprecated, DocumentAttributeAudio
from telethon.tl.patched import Message


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
    for (key, val) in message:
        if (key[0] != '_'):
            retMessage[key] = val
    return retMessage
