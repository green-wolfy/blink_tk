import asyncio
from aiohttp import ClientSession
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth
from blinkpy.helpers.util import json_load

import os

cred_file = "./cred.json"

async def start():
    if os.path.isfile(cred_file):
        blink = Blink()
        auth = Auth(await json_load(cred_file))
        blink.auth = auth
        await blink.start()
    else:
        blink = Blink(session=ClientSession())
        await blink.start()
        if blink: await blink.save(cred_file)
    return blink

blink = asyncio.run(start())
for name, camera in blink.cameras.items():
  print(name)                   # Name of the camera
  print(camera.attributes)      # Print available attributes of camera