#!/usr/bin/env python3
import logging
import json
import asyncio
from .server import MessageServer
from .message import MessageType, read_message, write_message
from ..utils.key_manager import KeyManager 

logger = logging.getLogger(__name__)


class Tracker(MessageServer):
    def __init__(self):
        super().__init__()
        # {writer -> address}
        self._peers = {}
        # {filename -> fileinfo(size, total_chunknum)}
        self._file_list = {}
        # {filename -> {(address) -> chunknum}}
        self._chunkinfo = {}

        self.key_manager = KeyManager()

    def file_list(self):
        return self._file_list

    def chunkinfo(self):
        return self._chunkinfo

    def peers(self):
        return tuple(self._peers.values())

    def address(self):
        return self._server_address

    def _reset(self):
        self._peers = {}
        self._file_list = {}
        self._chunkinfo = {}

    async def stop(self):
        await super().stop()
        if len(self._peers) != 0:
            logger.warning('Peers dict not fully cleared {}'.format(self._peers))

        self._reset()

async def process_connection(self, reader, writer):
    assert isinstance(reader, asyncio.StreamReader) and isinstance(writer, asyncio.StreamWriter)
    logger.info('New connection from {}'.format(writer.get_extra_info('peername')))
    self._peers[writer] = None
    try:
        while not reader.at_eof():
            message = await self.receive_and_verify_message(reader)
            message_type = MessageType(message['type'])
            if message_type == MessageType.REQUEST_REGISTER:
                self._peers[writer] = json.dumps(message['address'])
                await self.send_signed_message(writer, {'type': MessageType.REPLY_REGISTER})
            elif message_type == MessageType.REQUEST_PUBLISH:
                # handle publish request
                if message['filename'] in self._file_list:
                    await self.send_signed_message(writer, {
                        'type': MessageType.REPLY_PUBLISH,
                        'filename': message['filename'],
                        'result': False
                    })
                else:
                    self._file_list[message['filename']] = message['fileinfo']
                    self._chunkinfo[message['filename']] = {
                        self._peers[writer]: list(range(0, message['fileinfo']['total_chunknum']))
                    }
                    await self.send_signed_message(writer, {
                        'type': MessageType.REPLY_PUBLISH,
                        'filename': message['filename'],
                        'result': True,
                    })
                    logger.info('{} published file {} of {} chunks'
                                .format(self._peers[writer], message['filename'], message['fileinfo']['total_chunknum']))
            elif message_type == MessageType.REQUEST_FILE_LIST:
                await self.send_signed_message(writer, {
                    'type': MessageType.REPLY_FILE_LIST,
                    'file_list': self._file_list
                })
            elif message_type == MessageType.REQUEST_FILE_LOCATION:
                await self.send_signed_message(writer, {
                    'type': MessageType.REPLY_FILE_LOCATION,
                    'fileinfo': self._file_list[message['filename']],
                    'chunkinfo': self._chunkinfo[message['filename']]
                })
            elif message_type == MessageType.REQUEST_CHUNK_REGISTER:
                peer_address = self._peers[writer]
                if message['filename'] not in self._chunkinfo:
                    logger.warning('REQUEST_CHUNK_REGISTER with non-existing file.')
                    continue
                if peer_address in self._chunkinfo[message['filename']]:
                    if message['chunknum'] not in self._chunkinfo[message['filename']][peer_address]:
                        self._chunkinfo[message['filename']][peer_address].append(message['chunknum'])
                else:
                    self._chunkinfo[message['filename']][peer_address] = [message['chunknum']]
            else:
                logger.error('Undefined message: {}'.format(message))
    except (asyncio.IncompleteReadError, ConnectionError, RuntimeError):
        logger.warning('{} disconnected.'.format(self._peers[writer]))
    finally:
        peer_address = self._peers[writer]
        files_to_remove = []
        for filename, peer_possession_dict in self._chunkinfo.items():
            if peer_address in peer_possession_dict:
                del self._chunkinfo[filename][peer_address]
                if len(self._chunkinfo[filename]) == 0:
                    files_to_remove.append(filename)
        for key in files_to_remove:
            del self._chunkinfo[key]
            del self._file_list[key]
        del self._peers[writer]


    async def send_signed_message(self, writer, message):
        # 将 MessageType 转换为其整数值
        if isinstance(message['type'], MessageType):
            message['type'] = message['type'].value
        
        signature = self.key_manager.sign_message(json.dumps(message).encode())
        signed_message = {
            "message": message,
            "signature": signature.hex()
        }
        await write_message(writer, signed_message)

    async def receive_and_verify_message(self, reader):
        signed_message = await read_message(reader)
        message = signed_message["message"]
        signature = bytes.fromhex(signed_message["signature"])
        if self.key_manager.verify_signature(json.dumps(message).encode(), signature):
            # 检查并转换消息类型
            if 'type' in message:
                message['type'] = MessageType(message['type'])
            return message
        else:
            raise Exception("Message verification failed")