#!/usr/bin/env python3
import asyncio
import sys
import argparse
import logging
import coloredlogs
from p2p.code.peer import Peer
from p2p.code.tracker import Tracker
from p2p.ui.terminal import TrackerTerminal, PeerTerminal

coloredlogs.install(level='ERROR', fmt='%(levelname)s:%(module)s: %(message)s')

if sys.platform != 'win32':
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

async def main_async(option):
    obj = None
    terminal = None
    if option == 'tracker':
        obj = Tracker()
        terminal = TrackerTerminal(obj)
    elif option == 'peer':
        obj = Peer()
        await obj.start(('localhost', 0))
        terminal = PeerTerminal(obj)
    else:
        logging.error('Option must either be \'tracker\' or \'peer\'')
        exit(0)

    try:
        await terminal.cmdloop()
    except (KeyboardInterrupt, EOFError):
        pass
    except Exception as e:
        logging.error('{}:{}'.format(type(e).__name__, e))
    finally:
        await obj.stop()

def main():
    arg_parser = argparse.ArgumentParser(description=__doc__)
    arg_parser.add_argument('option', metavar='OPTION', type=str, nargs='?', default='tracker')
    results = arg_parser.parse_args()

    asyncio.run(main_async(results.option))

if __name__ == "__main__":
    main()
