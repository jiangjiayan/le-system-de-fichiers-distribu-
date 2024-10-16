#!/usr/bin/env python3
import pytest
import os
import asyncio
import hashlib
import sys
from ..code import Tracker, Peer

TEST_SMALL_FILE = 'test_small_file'
TEST_SMALL_FILE_1 = 'test_small_file_1'
TEST_LARGE_FILE = 'test_large_file'
TEST_SMALL_FILE_SIZE = 1000
TEST_LARGE_FILE_SIZE = 500 * 1000 * 1000


def fmd5(fname):
    """ calculate the md5 value of a file
    :param fname: file name
    :return: md5 value.
    """
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


async def setup_tracker_and_peers(peer_num, tracker_port):
    tracker = Tracker()
    peers = tuple(Peer() for _ in range(peer_num))
    await tracker.start(('localhost', tracker_port))
    # spawn peers concurrently
    await asyncio.gather(*[peer.start(('localhost', 0)) for peer in peers])
    await asyncio.gather(*[peer.connect(('localhost', tracker_port)) for peer in peers])
    return tracker, peers


@pytest.fixture(scope='session', autouse=True)
def create_test_files(request):
    # only use uvloop on non-windows platform
    if sys.platform != 'win32':
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    with open(TEST_SMALL_FILE, 'wb') as fout:
        fout.write(os.urandom(1000))

    with open(TEST_SMALL_FILE_1, 'wb') as fout:
        fout.write(os.urandom(1000))

    with open(TEST_LARGE_FILE, 'wb') as fout:
        # write 500MB random data into the file
        for _ in range(500):
            fout.write(os.urandom(1000 * 1000))

    def delete_files():
        os.remove(TEST_SMALL_FILE)
        os.remove(TEST_SMALL_FILE_1)
        os.remove(TEST_LARGE_FILE)

    request.addfinalizer(delete_files)